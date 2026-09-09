/**
 * Auth Page — Login & Signup for DebugVerse
 * Beautiful glassmorphism design with smooth form transitions.
 */

import React, { useState, useEffect } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Auth.css";

const Auth = () => {
  const navigate = useNavigate();
  const { login, signup, loginWithFirebaseSocial, sendPhoneVerification, confirmPhoneVerification, isAuthenticated, loading } = useAuth();

  const [mode, setMode] = useState("login"); // "login" | "signup"
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  // Redirect if already logged in
  useEffect(() => {
    if (!loading && isAuthenticated) {
      navigate("/debug");
    }
  }, [isAuthenticated, loading, navigate]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);

    try {
      let result;
      if (mode === "login") {
        result = await login(email, password);
      } else {
        if (password.length < 8) {
          setError("Password must be at least 8 characters.");
          setSubmitting(false);
          return;
        }
        result = await signup(email, password, fullName);
      }

      if (result.error) {
        setError(result.error.message || "Authentication failed. Please try again.");
      } else if (mode === "signup") {
        setSuccess("Account created! Check your email to verify, then sign in.");
        setMode("login");
      } else {
        navigate("/debug");
      }
    } catch (err) {
      setError("An unexpected error occurred. Please try again.");
    } finally {
      setSubmitting(false);
    }
  };

  const [authMethod, setAuthMethod] = useState("social"); // "social" | "phone" | "email"
  const [phone, setPhone] = useState("");
  const [otp, setOtp] = useState("");
  const [phoneStep, setPhoneStep] = useState("number"); // "number" | "otp"

  const handleSocialAuth = async (provider) => {
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      await loginWithFirebaseSocial(provider);
      navigate("/app");
    } catch (err) {
      setError(err?.message || `${provider} authentication failed. Please check provider settings in Firebase Console.`);
    } finally {
      setSubmitting(false);
    }
  };

  const handleSendPhoneOtp = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      if (!phone.startsWith("+")) {
        setError("Please enter phone with country code (e.g., +1 555-123-4567 or +91 9876543210)");
        setSubmitting(false);
        return;
      }
      await sendPhoneVerification(phone);
      setPhoneStep("otp");
      setSuccess("SMS code sent! Enter the 6-digit code below.");
    } catch (err) {
      setError(err?.message || "Failed to send SMS code. Please verify the number.");
    } finally {
      setSubmitting(false);
    }
  };

  const handleConfirmPhoneOtp = async (e) => {
    e.preventDefault();
    setError("");
    setSuccess("");
    setSubmitting(true);
    try {
      await confirmPhoneVerification(otp);
      navigate("/app");
    } catch (err) {
      setError(err?.message || "Invalid SMS verification code.");
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="auth-loading">
        <div className="auth-spinner" />
      </div>
    );
  }

  return (
    <div className="auth-page">
      {/* Background ambient orbs */}
      <div className="auth-orb auth-orb--1" />
      <div className="auth-orb auth-orb--2" />

      <div className="auth-container">
        {/* Logo */}
        <Link to="/" className="auth-logo">DebugVerse.</Link>
        <p className="auth-tagline">
          {mode === "login" ? "Welcome back, engineer." : "Start debugging smarter."}
        </p>

        {/* Card */}
        <div className="auth-card">
          {/* Tab switcher */}
          <div className="auth-tabs">
            <button
              className={`auth-tab ${mode === "login" ? "active" : ""}`}
              onClick={() => { setMode("login"); setError(""); setSuccess(""); }}
            >
              Sign In
            </button>
            <button
              className={`auth-tab ${mode === "signup" ? "active" : ""}`}
              onClick={() => { setMode("signup"); setError(""); setSuccess(""); }}
            >
              Create Account
            </button>
          </div>

          {/* Invisible reCAPTCHA container for Phone Auth */}
          <div id="recaptcha-container"></div>

          {/* Authentication Method Selector */}
          <div className="auth-method-pills">
            <button
              type="button"
              className={`auth-pill ${authMethod === "social" ? "active" : ""}`}
              onClick={() => { setAuthMethod("social"); setError(""); }}
            >
              Social Sign-in
            </button>
            <button
              type="button"
              className={`auth-pill ${authMethod === "phone" ? "active" : ""}`}
              onClick={() => { setAuthMethod("phone"); setError(""); setPhoneStep("number"); }}
            >
              Phone SMS
            </button>
            <button
              type="button"
              className={`auth-pill ${authMethod === "email" ? "active" : ""}`}
              onClick={() => { setAuthMethod("email"); setError(""); }}
            >
              Email & Pass
            </button>
          </div>

          {authMethod === "social" && (
            <div className="auth-social-stack">
              {/* Google OAuth */}
              <button
                className="auth-provider-btn auth-google-solid"
                onClick={() => handleSocialAuth("google")}
                disabled={submitting}
                type="button"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="none">
                  <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
                  <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
                  <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
                  <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
                </svg>
                Continue with Google
              </button>

              {/* GitHub OAuth */}
              <button
                className="auth-provider-btn auth-github-solid"
                onClick={() => handleSocialAuth("github")}
                disabled={submitting}
                type="button"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path fillRule="evenodd" clipRule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.53 1.032 1.53 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" />
                </svg>
                Continue with GitHub
              </button>

              {/* Facebook OAuth */}
              <button
                className="auth-provider-btn auth-facebook-solid"
                onClick={() => handleSocialAuth("facebook")}
                disabled={submitting}
                type="button"
              >
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M24 12.073c0-6.627-5.373-12-12-12s-12 5.373-12 12c0 5.99 4.388 10.954 10.125 11.854v-8.385H7.078v-3.47h3.047V9.43c0-3.007 1.792-4.669 4.533-4.669 1.312 0 2.686.235 2.686.235v2.953H15.83c-1.491 0-1.956.925-1.956 1.874v2.25h3.328l-.532 3.47h-2.796v8.385C19.612 23.027 24 18.062 24 12.073z" />
                </svg>
                Continue with Facebook
              </button>
            </div>
          )}

          {authMethod === "phone" && (
            <div className="auth-phone-block">
              {phoneStep === "number" ? (
                <form onSubmit={handleSendPhoneOtp} className="auth-form">
                  <div className="auth-field">
                    <label htmlFor="phoneInput">Mobile Phone Number</label>
                    <input
                      id="phoneInput"
                      type="tel"
                      value={phone}
                      onChange={(e) => setPhone(e.target.value)}
                      placeholder="+91 9876543210 or +1 555-123-4567"
                      required
                    />
                    <span className="auth-field-hint">Include international country code with '+' prefix</span>
                  </div>

                  {error && <div className="auth-error" role="alert">{error}</div>}
                  {success && <div className="auth-success" role="status">{success}</div>}

                  <button type="submit" className="auth-submit-btn" disabled={submitting}>
                    {submitting ? "Sending SMS Code..." : "Send Verification Code →"}
                  </button>
                </form>
              ) : (
                <form onSubmit={handleConfirmPhoneOtp} className="auth-form">
                  <div className="auth-field">
                    <label htmlFor="otpInput">Enter 6-Digit SMS Code</label>
                    <input
                      id="otpInput"
                      type="text"
                      maxLength={6}
                      value={otp}
                      onChange={(e) => setOtp(e.target.value)}
                      placeholder="123456"
                      className="auth-otp-input"
                      required
                    />
                  </div>

                  {error && <div className="auth-error" role="alert">{error}</div>}
                  {success && <div className="auth-success" role="status">{success}</div>}

                  <button type="submit" className="auth-submit-btn" disabled={submitting}>
                    {submitting ? "Verifying Code..." : "Verify & Sign In →"}
                  </button>

                  <button
                    type="button"
                    className="auth-text-btn"
                    onClick={() => { setPhoneStep("number"); setError(""); setSuccess(""); }}
                  >
                    ← Change phone number
                  </button>
                </form>
              )}
            </div>
          )}

          {authMethod === "email" && (
            <>
              <div className="auth-divider"><span>or sign in with password</span></div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="auth-form">
            {mode === "signup" && (
              <div className="auth-field">
                <label htmlFor="fullName">Full Name</label>
                <input
                  id="fullName"
                  type="text"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                  placeholder="Bhola Kumar"
                  required={mode === "signup"}
                  autoComplete="name"
                />
              </div>
            )}

            <div className="auth-field">
              <label htmlFor="email">Email Address</label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@example.com"
                required
                autoComplete="email"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="password">
                Password
                {mode === "login" && (
                  <span className="auth-forgot">Forgot password?</span>
                )}
              </label>
              <div className="auth-password-wrapper">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder={mode === "signup" ? "Min. 8 characters" : "Your password"}
                  required
                  autoComplete={mode === "login" ? "current-password" : "new-password"}
                />
                <button
                  type="button"
                  className="auth-show-password"
                  onClick={() => setShowPassword((s) => !s)}
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  {showPassword ? "👁" : "👁‍🗨"}
                </button>
              </div>
            </div>

            {error && (
              <div className="auth-error" role="alert">
                {error}
              </div>
            )}
            {success && (
              <div className="auth-success" role="status">
                {success}
              </div>
            )}

            <button
              type="submit"
              className="auth-submit-btn"
              disabled={submitting}
            >
              {submitting ? (
                <><span className="auth-btn-spinner" /> {mode === "login" ? "Signing in..." : "Creating account..."}</>
              ) : (
                mode === "login" ? "Sign In →" : "Create Free Account →"
              )}
            </button>
          </form>
          </>
          )}

          {mode === "signup" && (
            <p className="auth-terms">
              By creating an account, you agree to our{" "}
              <a href="/terms" target="_blank" rel="noopener noreferrer">Terms of Service</a>{" "}
              and{" "}
              <a href="/privacy" target="_blank" rel="noopener noreferrer">Privacy Policy</a>.
            </p>
          )}
        </div>

        {/* Free tier callout */}
        <div className="auth-free-note">
          Free tier includes <strong>10 AI debugs/day</strong> — no credit card required.
        </div>
      </div>
    </div>
  );
};

export default Auth;
