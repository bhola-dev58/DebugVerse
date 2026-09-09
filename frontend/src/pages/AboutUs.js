// src/pages/AboutUs.js
import React from "react";
import { Link } from "react-router-dom";
import "./AboutUs.css";

const TECH = [
  { icon: "🐍", name: "Python 3.10+", desc: "Backend runtime & async pipeline" },
  { icon: "⚡", name: "FastAPI", desc: "High-throughput async REST & SSE" },
  { icon: "⚛️", name: "React 19", desc: "Modern UI & client state" },
  { icon: "🖥️", name: "Monaco Editor", desc: "VS Code editing engine" },
  { icon: "🐳", name: "Docker", desc: "Isolated multi-runtime sandbox" },
  { icon: "🤖", name: "Claude 3.5 & Gemini", desc: "Multi-model GenAI reasoning" },
  { icon: "☁️", name: "AWS Cloud", desc: "ECS, Bedrock & scalable infra" },
  { icon: "🔗", name: "LangChain & RAG", desc: "Context-aware retrieval & agents" },
];

const AboutUs = () => {
  return (
    <div className="about-page">
      {/* Navbar */}
      <nav className="navbar">
        <div className="navbar-brand">
          <Link to="/" className="logo" style={{ textDecoration: "none" }}>
            DebugVerse.
          </Link>
        </div>
        <div className="navbar-links">
          <Link to="/">Home</Link>
          <Link to="/debug">Editor</Link>
        </div>
      </nav>

      {/* Hero */}
      <section className="about-hero">
        <div className="about-hero-content">
          <div className="about-badge">📖 About the Project</div>
          <h1 className="about-title">
            Built to Make <span className="highlight">Debugging</span> Effortless
          </h1>
          <p className="about-desc">
            DebugVerse is a full-stack AI debugging platform that combines a VS Code-quality
            Monaco editor, real-time Gemini AI analysis via server-sent events, and a 
            Dockerized sandbox for safe, isolated code execution — all running in your browser.
          </p>
          <Link to="/debug" className="cta-button">
            Open Editor <span className="button-arrow">→</span>
          </Link>
        </div>
      </section>

      {/* Developer Card */}
      <section className="about-section">
        <h2 className="section-title">The Developer</h2>
        <div className="dev-card">
          <div className="dev-avatar">
            <span>BK</span>
          </div>
          <div className="dev-info">
            <h3>bhola-dev58</h3>
            <p className="dev-role">
              Software Engineer (Full-Stack + Generative AI) | Building Production Apps | AWS Certified | LangChain • RAG • System Design
            </p>
            <div className="dev-skills-badges">
              <span className="dev-badge">⚡ Full-Stack + GenAI</span>
              <span className="dev-badge">☁️ AWS Certified</span>
              <span className="dev-badge">🔗 LangChain & RAG</span>
              <span className="dev-badge">🏗️ System Design</span>
              <span className="dev-badge">🤖 Claude 3.5 & Gemini</span>
            </div>
            <p className="dev-bio">
              Software Engineer passionate about engineering production-ready, highly scalable systems.
              Architecting DebugVerse to bridge deep generative AI insights, multi-runtime code sandboxing,
              and low-latency streaming for next-generation developer tooling.
            </p>
            <div className="dev-links">
              <a
                href="https://github.com/bhola-dev58"
                target="_blank"
                rel="noopener noreferrer"
                className="dev-link"
              >
                🐙 GitHub Profile
              </a>
              <a href="mailto:support@debugverse.dev" className="dev-link">
                📩 Contact
              </a>
            </div>
          </div>
        </div>
      </section>

      {/* Tech Stack */}
      <section className="about-section about-section--alt">
        <h2 className="section-title">Tech Stack</h2>
        <div className="tech-grid">
          {TECH.map((t) => (
            <div key={t.name} className="tech-card">
              <div className="tech-icon">{t.icon}</div>
              <h4>{t.name}</h4>
              <p>{t.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Architecture */}
      <section className="about-section">
        <h2 className="section-title">Architecture</h2>
        <div className="arch-diagram">
          <div className="arch-node arch-node--browser">
            <span>🌐 Browser</span>
            <small>React + Monaco</small>
          </div>
          <div className="arch-arrow">HTTP →</div>
          <div className="arch-node arch-node--backend">
            <span>⚡ FastAPI</span>
            <small>Python Backend</small>
          </div>
          <div className="arch-split">
            <div className="arch-branch">
              <div className="arch-arrow">→ SSE stream</div>
              <div className="arch-node arch-node--ai">
                <span>🤖 Gemini</span>
                <small>AI Analysis</small>
              </div>
            </div>
            <div className="arch-branch">
              <div className="arch-arrow">→ docker run</div>
              <div className="arch-node arch-node--docker">
                <span>🐳 Docker</span>
                <small>Sandbox Execution</small>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Key features */}
      <section className="about-section about-section--alt">
        <h2 className="section-title">What Makes It Stand Out</h2>
        <div className="standout-grid">
          <div className="standout-card">
            <h4>🔄 Real-Time Streaming</h4>
            <p>
              Uses <code>StreamingResponse</code> on FastAPI and the browser's
              native <code>ReadableStream</code> API — no third-party SSE library
              needed. Tokens render progressively like ChatGPT.
            </p>
          </div>
          <div className="standout-card">
            <h4>🛡️ Security-First Sandbox</h4>
            <p>
              Code runs in a non-root Docker container with <code>--network none</code>,
              a 10-second timeout, and resource caps. No user code ever touches the host.
            </p>
          </div>
          <div className="standout-card">
            <h4>🎨 Full Theme System</h4>
            <p>
              Dark/light mode built on CSS custom properties with a{" "}
              <code>data-theme</code> attribute toggle. Monaco editor theme syncs automatically.
              Preference persists via <code>localStorage</code>.
            </p>
          </div>
          <div className="standout-card">
            <h4>⌨️ Power-User UX</h4>
            <p>
              Keyboard shortcuts (<kbd>Ctrl+Enter</kbd>, <kbd>Ctrl+Shift+D</kbd>,{" "}
              <kbd>Ctrl+L</kbd>), persistent debug history, and a Monaco editor
              tuned with JetBrains Mono font.
            </p>
          </div>
        </div>
      </section>

      {/* Footer */}
      <footer className="App-footer" style={{ marginTop: 0 }}>
        <div className="footer-content">
          <div className="footer-section">
            <span className="logo" style={{ fontSize: "1.2rem" }}>
              DebugVerse.
            </span>
            <p>Making debugging smarter and faster</p>
          </div>
          <div className="footer-section">
            <p>
              © 2026 DebugVerse · Built by{" "}
              <a
                href="https://github.com/bhola-dev58"
                target="_blank"
                rel="noopener noreferrer"
              >
                bhola-dev58
              </a>
            </p>
            <div className="footer-links">
              <a
                href="https://github.com/bhola-dev58/DebugVerse"
                target="_blank"
                rel="noopener noreferrer"
              >
                GitHub
              </a>
              <Link to="/">Home</Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};

export default AboutUs;
