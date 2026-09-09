/**
 * AuthContext — Global Supabase Auth State for DebugVerse
 *
 * Provides:
 *   - user, session, loading state
 *   - login(), signup(), loginWithGoogle(), logout() actions
 *   - useAuth() hook for any component
 *
 * Dev mode: if SUPABASE_URL is not set, works in bypass mode
 * (treats everyone as a logged-in pro user for local development).
 */

import React, { createContext, useContext, useEffect, useState, useCallback } from "react";

// ── Supabase client (lazy init) ───────────────────────────────────────────────
const SUPABASE_URL = process.env.REACT_APP_SUPABASE_URL || "";
const SUPABASE_ANON_KEY = process.env.REACT_APP_SUPABASE_ANON_KEY || "";

let _supabaseClient = null;

function getSupabase() {
  if (_supabaseClient) return _supabaseClient;
  if (!SUPABASE_URL || !SUPABASE_ANON_KEY) return null;
  try {
    const { createClient } = require("@supabase/supabase-js");
    _supabaseClient = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
    return _supabaseClient;
  } catch {
    return null;
  }
}

// ── Dev mode mock user ────────────────────────────────────────────────────────
const DEV_USER = {
  id: "dev-user-id",
  email: "dev@debugverse.local",
  user_metadata: { full_name: "Dev User", avatar_url: "" },
  tier: "pro",
};

// ── Context ───────────────────────────────────────────────────────────────────
const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const supabase = getSupabase();
  const isDevMode = !supabase;

  const [user, setUser] = useState(isDevMode ? DEV_USER : null);
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(!isDevMode);
  const [tier, setTier] = useState(isDevMode ? "pro" : "free");

  useEffect(() => {
    if (isDevMode) {
      setLoading(false);
      return;
    }

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchTier(session.user.id);
      }
      setLoading(false);
    });

    // Subscribe to auth changes
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      async (_event, session) => {
        setSession(session);
        setUser(session?.user ?? null);
        if (session?.user) {
          await fetchTier(session.user.id);
        } else {
          setTier("free");
        }
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []); // eslint-disable-line

  const fetchTier = useCallback(async (userId) => {
    try {
      const response = await fetch(
        `${process.env.REACT_APP_API_URL || "http://localhost:8000"}/billing/status`,
        {
          headers: {
            Authorization: `Bearer ${(await supabase.auth.getSession()).data.session?.access_token}`,
          },
        }
      );
      if (response.ok) {
        const data = await response.json();
        setTier(data.tier || "free");
      }
    } catch {
      setTier("free");
    }
  }, [supabase]);

  // ── Auth Actions ────────────────────────────────────────────────────────────
  const login = async (email, password) => {
    if (isDevMode) {
      setUser(DEV_USER);
      setTier("pro");
      return { data: { user: DEV_USER }, error: null };
    }
    const result = await supabase.auth.signInWithPassword({ email, password });
    return result;
  };

  const signup = async (email, password, fullName) => {
    if (isDevMode) {
      setUser({ ...DEV_USER, email, user_metadata: { full_name: fullName } });
      return { data: { user: DEV_USER }, error: null };
    }
    const result = await supabase.auth.signUp({
      email,
      password,
      options: { data: { full_name: fullName } },
    });
    return result;
  };

  const loginWithGoogle = async () => {
    if (isDevMode) {
      setUser(DEV_USER);
      setTier("pro");
      return { data: {}, error: null };
    }
    return supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/dashboard` },
    });
  };

  const logout = async () => {
    if (isDevMode) {
      setUser(null);
      setTier("free");
      return;
    }
    await supabase.auth.signOut();
    setUser(null);
    setSession(null);
    setTier("free");
  };

  // ── Auth token getter (for API calls) ──────────────────────────────────────
  const getToken = async () => {
    if (isDevMode) return "dev-token";
    const { data } = await supabase.auth.getSession();
    return data?.session?.access_token || "";
  };

  const value = {
    user,
    session,
    loading,
    tier,
    isDevMode,
    isAuthenticated: !!user,
    isPro: tier === "pro" || tier === "enterprise",
    // Actions
    login,
    signup,
    loginWithGoogle,
    loginWithFirebaseSocial: async (provider) => {
      const { signInWithSocialProvider } = require("../services/firebaseAuth");
      const { user: fbUser, token } = await signInWithSocialProvider(provider);
      setUser(fbUser);
      setSession({ access_token: token, user: fbUser });
      setTier("pro");
      return { user: fbUser, token };
    },
    sendPhoneVerification: async (phone) => {
      const { sendPhoneVerificationCode } = require("../services/firebaseAuth");
      return await sendPhoneVerificationCode(phone);
    },
    confirmPhoneVerification: async (otp) => {
      const { confirmPhoneOtp } = require("../services/firebaseAuth");
      const { user: fbUser, token } = await confirmPhoneOtp(otp);
      setUser(fbUser);
      setSession({ access_token: token, user: fbUser });
      setTier("pro");
      return { user: fbUser, token };
    },
    logout,
    getToken,
    // User display helpers
    displayName: user?.displayName || user?.user_metadata?.full_name || user?.email?.split("@")[0] || user?.phoneNumber || "User",
    avatarUrl: user?.photoURL || user?.user_metadata?.avatar_url || "",
    email: user?.email || user?.phoneNumber || "",
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}

export default AuthContext;
