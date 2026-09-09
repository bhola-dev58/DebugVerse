import React, { useState } from "react";
import { Link } from "react-router-dom";
import Navbar from "../components/Navbar";
import "./Landing.css";

const AGENT_SHOWCASE = [
  {
    id: "explain",
    name: "Root Cause Explainer",
    icon: "🔍",
    tag: "Core Diagnostics",
    headline: "Deconstructs the deepest runtime anomalies",
    description:
      "Pinpoints compiler and runtime defects at their origin. Provides step-by-step code diffs and architectural patterns to prevent recurrent regressions.",
    color: "#3b82f6",
  },
  {
    id: "security",
    name: "Security Auditor",
    icon: "🛡️",
    tag: "AppSec & OWASP",
    headline: "Automated vulnerability & credential audit",
    description:
      "Rigorously scans for OWASP Top 10 vulnerabilities, injection vectors, memory corruption, and accidental secret leakage before code touches production.",
    color: "#ef4444",
  },
  {
    id: "performance",
    name: "Performance Profiler",
    icon: "⚡",
    tag: "Big-O Asymptotics",
    headline: "Algorithmic speedups & memory tuning",
    description:
      "Evaluates Big-O time and space complexity. Flags redundant allocations, quadratic hotspots, and returns vectorized, non-blocking implementations.",
    color: "#10b981",
  },
  {
    id: "tests",
    name: "Test Suite Generator",
    icon: "🧪",
    tag: "Automated QA",
    headline: "Exhaustive edge-case unit test suites",
    description:
      "Authors complete, runnable unit tests in pytest, Jest, JUnit 5, and Google Test with fixtures, boundary values, and mock assertions.",
    color: "#8b5cf6",
  },
];

const METRICS = [
  { value: "4x", label: "Parallel AI Agents", subtitle: "Concurrent evaluation in one pass" },
  { value: "< 250ms", label: "WebSocket Latency", subtitle: "Sub-second token streaming" },
  { value: "99.8%", label: "Vulnerability Catch Rate", subtitle: "Benchmarked on OWASP Top 10" },
  { value: "20,000+", label: "Concurrent Scale", subtitle: "Built on AWS ECS + Redis clusters" },
];

export default function Landing({ theme, toggleTheme }) {
  const [activeAgentTab, setActiveAgentTab] = useState("explain");

  return (
    <div className="landing-page">
      <Navbar theme={theme} toggleTheme={toggleTheme} />

      {/* ── 1. Hero Section ─────────────────────────────────────────────────── */}
      <section className="landing-hero">
        <div className="hero-glow-sphere top-left" />
        <div className="hero-glow-sphere bottom-right" />

        <div className="hero-announcement-badge">
          <span className="badge-sparkle">✨</span>
          <span>Introducing DebugVerse Multi-Agent v2.0</span>
          <span className="badge-arrow">→</span>
        </div>

        <h1 className="hero-title">
          Debug, Secure & Optimize <br />
          <span className="gradient-text">Complex Code at Scale.</span>
        </h1>

        <p className="hero-subtitle">
          DebugVerse replaces legacy single-prompt assistants with a parallel pipeline
          of 4 specialized AI agents: compiler diagnostics, security auditing,
          Big-O algorithmic profiling, and automated unit test generation.
        </p>

        <div className="hero-cta-group">
          <Link to="/debug" className="hero-primary-btn">
            <span>Launch Studio Free</span>
            <span className="btn-icon">⚡</span>
          </Link>
          <Link to="/pricing" className="hero-secondary-btn">
            View Tiers & Pricing
          </Link>
        </div>

        {/* ── 2. Live Interactive Mock Terminal ───────────────────────────────── */}
        <div className="hero-mockup-wrapper">
          <div className="mockup-window">
            <div className="mockup-header">
              <div className="mockup-dots">
                <span className="mockup-dot red" />
                <span className="mockup-dot yellow" />
                <span className="mockup-dot green" />
              </div>
              <div className="mockup-title">debugverse-agent-orchestrator — live stream</div>
              <div className="mockup-status">● 4 Agents Active</div>
            </div>

            <div className="mockup-body">
              <div className="mockup-sidebar">
                <div className="mockup-agent-item active">
                  <span className="agent-dot green" />
                  <span>Explain Agent</span>
                  <span className="agent-tag">Done</span>
                </div>
                <div className="mockup-agent-item active">
                  <span className="agent-dot green" />
                  <span>Security Auditor</span>
                  <span className="agent-tag">Done</span>
                </div>
                <div className="mockup-agent-item active">
                  <span className="agent-dot green" />
                  <span>Performance</span>
                  <span className="agent-tag">Done</span>
                </div>
                <div className="mockup-agent-item active">
                  <span className="agent-dot green" />
                  <span>Test Generator</span>
                  <span className="agent-tag">Done</span>
                </div>
              </div>

              <div className="mockup-terminal">
                <pre>
                  <code>
                    <span className="code-comment"># Parallel Agent Pipeline Result:</span>{"\n"}
                    <span className="code-keyword">def</span> <span className="code-func">authenticate_user</span>(token):{"\n"}
                    {"    "}<span className="code-comment"># [SECURITY AUDIT]: CWE-89 SQLi patched via parameterization</span>{"\n"}
                    {"    "}<span className="code-comment"># [PERFORMANCE]: O(n) scan replaced with indexed O(1) hash lookup</span>{"\n"}
                    {"    "}<span className="code-keyword">return</span> db.users.find_one({"{"}<span className="code-string">"token_hash"</span>: hash_secret(token){"}"}){"\n\n"}
                    <span className="code-success">✓ 4 of 4 agents finished analysis in 1.4s</span>{"\n"}
                    <span className="code-success">✓ Test suite generated with 8 parameterized edge cases</span>
                  </code>
                </pre>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── 3. High-Scale Metrics Bar ───────────────────────────────────────── */}
      <section className="metrics-strip">
        <div className="metrics-container">
          {METRICS.map((metric, idx) => (
            <div key={idx} className="metric-card">
              <div className="metric-value gradient-text">{metric.value}</div>
              <div className="metric-label">{metric.label}</div>
              <div className="metric-subtitle">{metric.subtitle}</div>
            </div>
          ))}
        </div>
      </section>

      {/* ── 4. The 4 Agents Deep Dive ───────────────────────────────────────── */}
      <section className="agents-section">
        <div className="section-header text-center">
          <span className="section-pill">Architectural Intelligence</span>
          <h2 className="section-title">4 Specialized Minds in Every Session</h2>
          <p className="section-subtitle">
            Why settle for one generic response? DebugVerse distributes your codebase
            across 4 concurrent agents operating with specialized personas.
          </p>
        </div>

        <div className="agents-showcase-container">
          <div className="agents-tab-selector">
            {AGENT_SHOWCASE.map((agent) => (
              <button
                key={agent.id}
                className={`agent-select-card ${activeAgentTab === agent.id ? "active" : ""}`}
                onClick={() => setActiveAgentTab(agent.id)}
              >
                <div className="agent-card-icon" style={{ borderColor: agent.color }}>
                  {agent.icon}
                </div>
                <div className="agent-card-meta">
                  <div className="agent-card-name">{agent.name}</div>
                  <div className="agent-card-tag">{agent.tag}</div>
                </div>
              </button>
            ))}
          </div>

          <div className="agent-display-card">
            {(() => {
              const agent = AGENT_SHOWCASE.find((a) => a.id === activeAgentTab);
              return (
                <div className="agent-detail-content">
                  <div className="agent-detail-header">
                    <span className="agent-detail-icon">{agent.icon}</span>
                    <div>
                      <h3 className="agent-detail-title">{agent.name}</h3>
                      <div className="agent-detail-tag">{agent.tag}</div>
                    </div>
                  </div>
                  <h4 className="agent-detail-headline">{agent.headline}</h4>
                  <p className="agent-detail-desc">{agent.description}</p>
                  <Link to="/debug" className="agent-try-link">
                    Try {agent.name} in Studio →
                  </Link>
                </div>
              );
            })()}
          </div>
        </div>
      </section>

      {/* ── 5. Enterprise Ready Stack ────────────────────────────────────────── */}
      <section className="tech-stack-section">
        <div className="section-header text-center">
          <span className="section-pill">Enterprise Reliability</span>
          <h2 className="section-title">Built on Industry-Standard Foundations</h2>
          <p className="section-subtitle">
            Engineered for high-concurrency production deployments up to 20,000+ simultaneous users.
          </p>
        </div>

        <div className="tech-grid">
          <div className="tech-card">
            <div className="tech-card-icon">⚡</div>
            <h4>FastAPI + WebSockets</h4>
            <p>Non-blocking asynchronous core with sub-second event streaming to browsers and IDEs.</p>
          </div>
          <div className="tech-card">
            <div className="tech-card-icon">🛡️</div>
            <h4>Supabase Auth & Database</h4>
            <p>PostgreSQL with Row-Level Security, JWT authentication, and automated session auditing.</p>
          </div>
          <div className="tech-card">
            <div className="tech-card-icon">💳</div>
            <h4>Stripe Billing</h4>
            <p>Production billing infrastructure supporting Pro and Enterprise recurring subscriptions.</p>
          </div>
          <div className="tech-card">
            <div className="tech-card-icon">🐳</div>
            <h4>Dockerized Sandboxes</h4>
            <p>Hardened micro-sandbox environments isolating untrusted user code runs safely.</p>
          </div>
          <div className="tech-card">
            <div className="tech-card-icon">☁️</div>
            <h4>AWS Bedrock & Claude 3.5</h4>
            <p>High-reasoning foundation models coupled with Google Gemini 2.5 Flash automatic failover.</p>
          </div>
          <div className="tech-card">
            <div className="tech-card-icon">📊</div>
            <h4>OpenTelemetry Observability</h4>
            <p>Distributed tracing, Prometheus metrics export, and health probes for 99.9% SLAs.</p>
          </div>
        </div>
      </section>

      {/* ── 6. Final Call to Action ─────────────────────────────────────────── */}
      <section className="landing-cta-banner">
        <div className="cta-banner-content">
          <h2>Ready to revolutionize your debugging workflow?</h2>
          <p>Join thousands of software engineers debugging with 4 AI agents today.</p>
          <div className="cta-banner-buttons">
            <Link to="/debug" className="cta-banner-primary">
              Open DebugVerse Studio
            </Link>
            <Link to="/pricing" className="cta-banner-secondary">
              Explore Plans
            </Link>
          </div>
        </div>
      </section>

      {/* ── 7. Footer ───────────────────────────────────────────────────────── */}
      <footer className="landing-footer">
        <div className="footer-content">
          <div className="footer-brand">
            <span className="footer-logo">DebugVerse.</span>
            <p>Autonomous AI Multi-Agent Code Debugging & Sandboxed Execution Platform.</p>
          </div>
          <div className="footer-links">
            <Link to="/debug">Studio</Link>
            <Link to="/pricing">Pricing</Link>
            <Link to="/auth">Sign In</Link>
            <a href="https://github.com" target="_blank" rel="noopener noreferrer">GitHub</a>
          </div>
        </div>
        <div className="footer-bottom">
          <p>© 2026 DebugVerse, Inc. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
}
