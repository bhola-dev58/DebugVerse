/**
 * Dashboard Page — DebugVerse
 * User profile, usage stats, billing management, and persistent history.
 */

import React, { useState, useEffect, useCallback } from "react";
import { Link, useNavigate, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Dashboard.css";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const TIER_COLORS = { free: "#64748b", pro: "#10b981", enterprise: "#7c3aed" };
const TIER_LIMITS = { free: 10, pro: 200, enterprise: Infinity };

const Dashboard = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { tier, isPro, displayName, email, getToken, logout, isAuthenticated, loading: authLoading } = useAuth();

  const [stats, setStats] = useState(null);
  const [history, setHistory] = useState([]);
  const [historyLoading, setHistoryLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState("overview");
  const [portalLoading, setPortalLoading] = useState(false);
  const [successMsg, setSuccessMsg] = useState("");

  // Handle post-upgrade redirect
  useEffect(() => {
    if (searchParams.get("upgraded") === "true") {
      setSuccessMsg("🎉 Welcome to Pro! Your account has been upgraded.");
      setTimeout(() => setSuccessMsg(""), 5000);
    }
  }, [searchParams]);

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      navigate("/auth");
    }
  }, [authLoading, isAuthenticated, navigate]);

  const fetchStats = useCallback(async () => {
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/history/stats`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setStats(await res.json());
    } catch {
      setStats({ total_sessions: 0, today_debugs: 0, this_month_debugs: 0, tier });
    } finally {
      setStatsLoading(false);
    }
  }, [getToken, tier]);

  const fetchHistory = useCallback(async () => {
    setHistoryLoading(true);
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/history?limit=20`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) setHistory(await res.json());
    } catch {
      setHistory([]);
    } finally {
      setHistoryLoading(false);
    }
  }, [getToken]);

  useEffect(() => {
    if (isAuthenticated) {
      fetchStats();
      fetchHistory();
    }
  }, [isAuthenticated, fetchStats, fetchHistory]);

  const handleDeleteSession = async (id) => {
    try {
      const token = await getToken();
      await fetch(`${API_BASE}/history/${id}`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
      setHistory((h) => h.filter((s) => s.id !== id));
    } catch {}
  };

  const handleOpenPortal = async () => {
    setPortalLoading(true);
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/billing/portal`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      if (data.url) window.location.href = data.url;
    } catch {
      alert("Failed to open billing portal. Please contact support.");
    } finally {
      setPortalLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  if (authLoading) {
    return (
      <div className="dashboard-loading">
        <div className="dashboard-spinner" />
      </div>
    );
  }

  const tierColor = TIER_COLORS[tier] || TIER_COLORS.free;
  const usagePercent = tier === "enterprise" ? 0 : Math.min(100, ((stats?.today_debugs || 0) / TIER_LIMITS[tier]) * 100);

  return (
    <div className="dashboard-page">
      {/* Sidebar */}
      <aside className="dashboard-sidebar">
        <Link to="/" className="dashboard-logo">DebugVerse.</Link>

        <div className="dashboard-user-card">
          <div className="dashboard-avatar">
            {displayName.charAt(0).toUpperCase()}
          </div>
          <div className="dashboard-user-info">
            <div className="dashboard-user-name">{displayName}</div>
            <div className="dashboard-user-email">{email}</div>
          </div>
          <div className="dashboard-tier-badge" style={{ color: tierColor, borderColor: tierColor }}>
            {tier.toUpperCase()}
          </div>
        </div>

        <nav className="dashboard-nav">
          {[
            { id: "overview", label: "Overview", icon: "◈" },
            { id: "history", label: "Debug History", icon: "⊞" },
            { id: "billing", label: "Billing", icon: "◉" },
          ].map((item) => (
            <button
              key={item.id}
              className={`dashboard-nav-item ${activeTab === item.id ? "active" : ""}`}
              onClick={() => setActiveTab(item.id)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>

        <div className="dashboard-sidebar-bottom">
          <Link to="/debug" className="dashboard-go-editor">
            Open Editor →
          </Link>
          <button className="dashboard-logout" onClick={handleLogout}>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <main className="dashboard-main">
        {successMsg && (
          <div className="dashboard-success-banner">{successMsg}</div>
        )}

        {/* ── OVERVIEW TAB ── */}
        {activeTab === "overview" && (
          <div className="dashboard-section">
            <h1 className="dashboard-page-title">Welcome back, {displayName.split(" ")[0]} 👋</h1>
            <p className="dashboard-page-subtitle">Here's how you've been using DebugVerse.</p>

            {/* Stats Grid */}
            <div className="dashboard-stats-grid">
              {[
                { label: "Debugs Today", value: stats?.today_debugs ?? "—", sub: `Limit: ${tier === "enterprise" ? "∞" : TIER_LIMITS[tier]}/day` },
                { label: "This Month", value: stats?.this_month_debugs ?? "—", sub: "Total debug sessions" },
                { label: "All Time", value: stats?.total_sessions ?? "—", sub: "Saved sessions" },
                { label: "Current Plan", value: tier.charAt(0).toUpperCase() + tier.slice(1), sub: isPro ? "Active subscription" : "Free tier", color: tierColor },
              ].map((s, i) => (
                <div key={i} className="dashboard-stat-card">
                  <div className="stat-value" style={s.color ? { color: s.color } : {}}>
                    {statsLoading ? <span className="stat-skeleton" /> : s.value}
                  </div>
                  <div className="stat-label">{s.label}</div>
                  <div className="stat-sub">{s.sub}</div>
                </div>
              ))}
            </div>

            {/* Usage bar (free tier only) */}
            {tier === "free" && (
              <div className="dashboard-usage-bar-card">
                <div className="usage-bar-header">
                  <span>Daily Debug Usage</span>
                  <span>{stats?.today_debugs ?? 0} / {TIER_LIMITS.free}</span>
                </div>
                <div className="usage-bar-track">
                  <div
                    className="usage-bar-fill"
                    style={{
                      width: `${usagePercent}%`,
                      background: usagePercent > 80 ? "#ef4444" : "#10b981",
                    }}
                  />
                </div>
                {usagePercent > 70 && (
                  <div className="usage-bar-warning">
                    Running low!{" "}
                    <Link to="/pricing">Upgrade to Pro</Link> for unlimited access.
                  </div>
                )}
              </div>
            )}

            {/* Quick actions */}
            <div className="dashboard-quick-actions">
              <Link to="/debug" className="quick-action quick-action--primary">
                Start Debugging →
              </Link>
              {!isPro && (
                <Link to="/pricing" className="quick-action quick-action--upgrade">
                  Upgrade to Pro ↗
                </Link>
              )}
            </div>
          </div>
        )}

        {/* ── HISTORY TAB ── */}
        {activeTab === "history" && (
          <div className="dashboard-section">
            <h1 className="dashboard-page-title">Debug History</h1>
            <p className="dashboard-page-subtitle">Your last 20 debug sessions, synced across devices.</p>

            {historyLoading ? (
              <div className="history-skeletons">
                {[...Array(5)].map((_, i) => <div key={i} className="history-skeleton-row" />)}
              </div>
            ) : history.length === 0 ? (
              <div className="history-empty">
                <span className="history-empty-icon">◈</span>
                <p>No debug sessions yet.</p>
                <Link to="/debug" className="quick-action quick-action--primary" style={{ display: "inline-flex", marginTop: "16px" }}>
                  Start Your First Debug →
                </Link>
              </div>
            ) : (
              <div className="history-list">
                {history.map((session) => (
                  <div key={session.id} className="history-card">
                    <div className="history-card-header">
                      <span className="history-lang-badge">{session.language?.toUpperCase()}</span>
                      {session.model_used && (
                        <span className="history-model-badge">{session.model_used}</span>
                      )}
                      <span className="history-date">
                        {new Date(session.created_at).toLocaleDateString("en-IN", {
                          day: "numeric", month: "short", hour: "2-digit", minute: "2-digit"
                        })}
                      </span>
                      <div className="history-actions">
                        <button
                          className="history-load-btn"
                          onClick={() => navigate("/debug", { state: { code: session.code, language: session.language } })}
                        >
                          Load
                        </button>
                        <button
                          className="history-delete-btn"
                          onClick={() => handleDeleteSession(session.id)}
                          aria-label="Delete session"
                        >
                          ✕
                        </button>
                      </div>
                    </div>
                    <pre className="history-code-preview">
                      {session.code?.slice(0, 120)}{session.code?.length > 120 ? "..." : ""}
                    </pre>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── BILLING TAB ── */}
        {activeTab === "billing" && (
          <div className="dashboard-section">
            <h1 className="dashboard-page-title">Billing & Subscription</h1>
            <p className="dashboard-page-subtitle">Manage your plan and payment details.</p>

            <div className="billing-current-plan">
              <div className="billing-plan-header">
                <div>
                  <span className="billing-plan-name" style={{ color: tierColor }}>
                    {tier.charAt(0).toUpperCase() + tier.slice(1)} Plan
                  </span>
                  <p className="billing-plan-desc">
                    {tier === "free" && "10 AI debugs per day. Upgrade for unlimited access."}
                    {tier === "pro" && "Unlimited debugs, all models, multi-agent pipeline."}
                    {tier === "enterprise" && "Full team access with SSO, audit logs, and SLA."}
                  </p>
                </div>
                <div className="billing-plan-actions">
                  {tier === "free" ? (
                    <Link to="/pricing" className="billing-upgrade-btn">Upgrade to Pro →</Link>
                  ) : (
                    <button
                      className="billing-portal-btn"
                      onClick={handleOpenPortal}
                      disabled={portalLoading}
                    >
                      {portalLoading ? "Opening..." : "Manage Subscription →"}
                    </button>
                  )}
                </div>
              </div>
            </div>

            <div className="billing-info-grid">
              {[
                { label: "Current Tier", value: tier.charAt(0).toUpperCase() + tier.slice(1) },
                { label: "Daily Limit", value: tier === "enterprise" ? "Unlimited" : `${TIER_LIMITS[tier]} debugs` },
                { label: "Models Available", value: isPro ? "Gemini + Claude 3.5" : "Gemini 2.5 Flash" },
                { label: "Multi-Agent Pipeline", value: isPro ? "Enabled" : "Pro only" },
              ].map((item, i) => (
                <div key={i} className="billing-info-item">
                  <span className="billing-info-label">{item.label}</span>
                  <span className="billing-info-value">{item.value}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
};

export default Dashboard;
