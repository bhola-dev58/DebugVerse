import React from "react";
import { Link, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Navbar.css";

export default function Navbar({ theme, toggleTheme }) {
  const { isAuthenticated, displayName, tier, logout } = useAuth();
  const location = useLocation();

  return (
    <nav className="dv-navbar" role="navigation" aria-label="Main Navigation">
      <div className="dv-navbar-left">
        <Link to="/" className="dv-logo">
          <span className="dv-logo-text">DebugVerse</span>
          <span className="dv-logo-dot" />
        </Link>
        <span className="dv-logo-badge">PRO MAX</span>
      </div>

      <div className="dv-navbar-center">
        <Link
          to="/"
          className={`dv-nav-link ${location.pathname === "/" ? "active" : ""}`}
        >
          Home
        </Link>
        <Link
          to="/debug"
          className={`dv-nav-link ${location.pathname === "/debug" ? "active" : ""}`}
        >
          Studio
        </Link>
        <Link
          to="/pricing"
          className={`dv-nav-link ${location.pathname === "/pricing" ? "active" : ""}`}
        >
          Pricing
        </Link>
        {isAuthenticated && (
          <Link
            to="/dashboard"
            className={`dv-nav-link ${location.pathname === "/dashboard" ? "active" : ""}`}
          >
            Dashboard
          </Link>
        )}
      </div>

      <div className="dv-navbar-right">
        {/* Tier badge */}
        <span className={`dv-tier-badge tier-${tier || "free"}`}>
          {tier || "free"}
        </span>

        {/* Auth CTA */}
        {isAuthenticated ? (
          <div className="dv-user-menu">
            <Link to="/dashboard" className="dv-user-avatar-btn" title="View Account">
              <span className="dv-avatar-letter">
                {(displayName || "U")[0].toUpperCase()}
              </span>
              <span className="dv-user-name">
                {(displayName || "Developer").split(" ")[0]}
              </span>
            </Link>
            <button onClick={logout} className="dv-logout-btn" title="Sign Out">
              Sign Out
            </button>
          </div>
        ) : (
          <Link to="/auth" className="dv-signin-btn">
            Sign In
          </Link>
        )}

        {/* Theme Toggle */}
        <button
          className="dv-theme-toggle-btn"
          onClick={toggleTheme}
          title={theme === "dark" ? "Switch to Light Mode" : "Switch to Dark Mode"}
          aria-label="Toggle visual theme"
        >
          {theme === "dark" ? "☀️" : "🌙"}
        </button>
      </div>
    </nav>
  );
}
