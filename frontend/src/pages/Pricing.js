/**
 * Pricing Page — DebugVerse
 * Three-tier pricing with Stripe integration.
 */

import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import "./Pricing.css";

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const PLANS = [
  {
    id: "free",
    name: "Free",
    price: "$0",
    priceNote: "forever",
    tagline: "Perfect for trying DebugVerse",
    color: "#64748b",
    solidBg: "#334155",
    features: [
      "10 AI debugs per day",
      "Gemini 2.5 Flash model",
      "5 programming languages",
      "Docker sandbox execution",
      "7-day debug history",
      "Community support",
    ],
    limitations: ["No Claude 3.5 Sonnet", "No persistent history", "No multi-agent pipeline"],
    cta: "Get Started Free",
    highlighted: false,
  },
  {
    id: "pro",
    name: "Pro",
    price: "$19",
    priceNote: "per month",
    tagline: "For serious developers",
    color: "#10b981",
    solidBg: "#10b981",
    badge: "Most Popular",
    features: [
      "Unlimited AI debugs",
      "Claude 3.5 Sonnet + Gemini 2.5 Flash",
      "Multi-agent pipeline (4 AI agents)",
      "All 10+ programming languages",
      "Unlimited persistent history",
      "Priority inference queue",
      "RAG citations + references",
      "Email support",
    ],
    limitations: [],
    cta: "Upgrade to Pro",
    highlighted: true,
  },
  {
    id: "enterprise",
    name: "Enterprise",
    price: "$49",
    priceNote: "per seat/month",
    tagline: "For engineering teams",
    color: "#7c3aed",
    solidBg: "#7c3aed",
    features: [
      "Everything in Pro",
      "Team shared knowledge base",
      "Private codebase RAG indexing",
      "SSO (SAML/OIDC)",
      "Audit logs & compliance",
      "Custom model fine-tuning",
      "SLA guarantee (99.9%)",
      "Dedicated Slack support",
    ],
    limitations: [],
    cta: "Contact Sales",
    highlighted: false,
  },
];

const Pricing = () => {
  const navigate = useNavigate();
  const { isAuthenticated, tier, getToken } = useAuth();
  const [loading, setLoading] = useState(null);
  const [error, setError] = useState("");

  const handleCTA = async (plan) => {
    setError("");

    if (plan.id === "free") {
      navigate(isAuthenticated ? "/debug" : "/auth");
      return;
    }

    if (plan.id === "enterprise") {
      window.location.href = "mailto:hello@debugverse.dev?subject=Enterprise%20Inquiry";
      return;
    }

    if (!isAuthenticated) {
      navigate("/auth");
      return;
    }

    if (tier === plan.id) {
      navigate("/dashboard");
      return;
    }

    // Stripe checkout
    setLoading(plan.id);
    try {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/billing/checkout`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify({ plan: plan.id }),
      });

      const data = await response.json();
      if (data.url) {
        window.location.href = data.url;
      } else {
        setError(data.message || "Failed to start checkout. Please try again.");
      }
    } catch (err) {
      setError("Connection error. Please check your internet connection.");
    } finally {
      setLoading(null);
    }
  };

  const isCurrentPlan = (planId) => tier === planId;

  return (
    <div className="pricing-page">
      <div className="pricing-orb pricing-orb--1" />
      <div className="pricing-orb pricing-orb--2" />

      <nav className="pricing-nav">
        <Link to="/" className="pricing-logo">DebugVerse.</Link>
        <div className="pricing-nav-links">
          <Link to="/debug">Editor</Link>
          {isAuthenticated
            ? <Link to="/dashboard">Dashboard</Link>
            : <Link to="/auth">Sign In</Link>
          }
        </div>
      </nav>

      <div className="pricing-content">
        {/* Header */}
        <div className="pricing-header">
          <span className="pricing-badge">Simple Pricing</span>
          <h1 className="pricing-title">
            Start Free. <span className="pricing-title-accent">Scale as You Grow.</span>
          </h1>
          <p className="pricing-subtitle">
            No credit card required for Free tier. Cancel Pro anytime — no questions asked.
          </p>
        </div>

        {error && (
          <div className="pricing-error">
            {error}
          </div>
        )}

        {/* Plans Grid */}
        <div className="pricing-grid">
          {PLANS.map((plan) => (
            <div
              key={plan.id}
              className={`plan-card ${plan.highlighted ? "plan-card--highlighted" : ""}`}
            >
              {plan.badge && (
                <div className="plan-badge" style={{ background: plan.solidBg }}>
                  {plan.badge}
                </div>
              )}

              <div className="plan-header">
                <div className="plan-name" style={{ color: plan.color }}>{plan.name}</div>
                <div className="plan-price">
                  <span className="plan-price-amount">{plan.price}</span>
                  <span className="plan-price-note">{plan.priceNote}</span>
                </div>
                <p className="plan-tagline">{plan.tagline}</p>
              </div>

              <button
                className={`plan-cta ${plan.highlighted ? "plan-cta--primary" : "plan-cta--secondary"}`}
                onClick={() => handleCTA(plan)}
                disabled={loading === plan.id || isCurrentPlan(plan.id)}
                style={plan.highlighted ? { background: plan.solidBg } : {}}
              >
                {loading === plan.id ? (
                  <><span className="plan-cta-spinner" /> Processing...</>
                ) : isCurrentPlan(plan.id) ? (
                  "Your Current Plan"
                ) : (
                  plan.cta
                )}
              </button>

              <ul className="plan-features">
                {plan.features.map((f, i) => (
                  <li key={i} className="plan-feature plan-feature--included">
                    <span className="plan-feature-icon">✓</span> {f}
                  </li>
                ))}
                {plan.limitations.map((f, i) => (
                  <li key={i} className="plan-feature plan-feature--excluded">
                    <span className="plan-feature-icon">✗</span> {f}
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* FAQ section */}
        <div className="pricing-faq">
          <h2>Frequently Asked Questions</h2>
          <div className="faq-grid">
            {[
              { q: "Can I change plans?", a: "Yes — upgrade or downgrade anytime. Changes take effect on your next billing cycle." },
              { q: "What payment methods?", a: "All major credit/debit cards via Stripe. UPI and PayPal coming soon." },
              { q: "Is there a student discount?", a: "Yes — 50% off Pro for verified students. Email us with your .edu address." },
              { q: "What happens when I hit the free limit?", a: "You'll see a friendly upgrade prompt. Your code is never lost — you can paste and debug again tomorrow." },
            ].map((item, i) => (
              <div key={i} className="faq-item">
                <div className="faq-q">{item.q}</div>
                <div className="faq-a">{item.a}</div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};

export default Pricing;
