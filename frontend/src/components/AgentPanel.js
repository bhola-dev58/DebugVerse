import React, { useState } from "react";
import { marked } from "marked";
import "./AgentPanel.css";

const AGENT_CONFIG = {
  explain: {
    id: "explain",
    name: "Root Cause",
    fullName: "Root Cause Explainer",
    icon: "🔍",
    badgeColor: "#3b82f6",
    tagline: "Compiler diagnostics, bug origin & corrected code",
  },
  security: {
    id: "security",
    name: "Security",
    fullName: "Security Auditor",
    icon: "🛡️",
    badgeColor: "#ef4444",
    tagline: "OWASP Top 10, injection flaws & credential leaks",
  },
  performance: {
    id: "performance",
    name: "Performance",
    fullName: "Performance Profiler",
    icon: "⚡",
    badgeColor: "#10b981",
    tagline: "Big-O complexity, memory hotspots & speedups",
  },
  tests: {
    id: "tests",
    name: "Test Suite",
    fullName: "Test Generator",
    icon: "🧪",
    badgeColor: "#8b5cf6",
    tagline: "Automated unit tests with boundary & edge cases",
  },
};

export default function AgentPanel({ agentOutputs = {}, agentStatuses = {}, isRunning = false }) {
  const [activeTab, setActiveTab] = useState("explain");
  const [copied, setCopied] = useState(false);
  const [exportCopied, setExportCopied] = useState(false);

  const currentAgent = AGENT_CONFIG[activeTab] || AGENT_CONFIG.explain;
  const currentOutput = agentOutputs[activeTab] || "";
  const currentStatus = agentStatuses[activeTab] || "idle";

  const handleCopyCurrent = () => {
    if (!currentOutput) return;
    navigator.clipboard.writeText(currentOutput);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const handleExportAll = () => {
    const combined = Object.keys(AGENT_CONFIG)
      .map((key) => {
        const cfg = AGENT_CONFIG[key];
        const content = agentOutputs[key] || "No output generated.";
        return `# [${cfg.icon} ${cfg.fullName}]\n\n${content}\n\n---\n`;
      })
      .join("\n");

    navigator.clipboard.writeText(combined);
    setExportCopied(true);
    setTimeout(() => setExportCopied(false), 2000);
  };

  return (
    <div className="agent-panel-container">
      {/* Header with tabs and multi-agent indicator */}
      <div className="agent-panel-header">
        <div className="agent-panel-title-group">
          <div className="multi-agent-pulse-badge">
            <span className={`pulse-dot ${isRunning ? "active" : ""}`} />
            <span className="badge-text">4 Parallel AI Agents</span>
          </div>
        </div>

        <div className="agent-panel-actions">
          <button
            className="agent-action-btn"
            onClick={handleCopyCurrent}
            disabled={!currentOutput}
            title="Copy current tab to clipboard"
          >
            {copied ? "Copied!" : "Copy Report"}
          </button>
          <button
            className="agent-action-btn primary"
            onClick={handleExportAll}
            disabled={!Object.values(agentOutputs).some(Boolean)}
            title="Export full 4-agent audit"
          >
            {exportCopied ? "All Reports Copied!" : "Export All (Markdown)"}
          </button>
        </div>
      </div>

      {/* Agent Tab Bar */}
      <div className="agent-tabs-bar" role="tablist">
        {Object.keys(AGENT_CONFIG).map((key) => {
          const cfg = AGENT_CONFIG[key];
          const status = agentStatuses[key] || "idle";
          const hasContent = Boolean(agentOutputs[key]);
          const isActive = activeTab === key;

          return (
            <button
              key={key}
              role="tab"
              aria-selected={isActive}
              className={`agent-tab ${isActive ? "active" : ""} status-${status}`}
              onClick={() => setActiveTab(key)}
            >
              <span className="agent-tab-icon">{cfg.icon}</span>
              <span className="agent-tab-name">{cfg.name}</span>
              <span className={`status-indicator ${status}`} title={`Status: ${status}`}>
                {status === "running" && <span className="spinner-mini" />}
                {status === "complete" && <span className="check-mini">✓</span>}
                {status === "error" && <span className="error-mini">!</span>}
                {status === "idle" && hasContent && <span className="dot-mini" />}
              </span>
            </button>
          );
        })}
      </div>

      {/* Active Agent Banner */}
      <div className="agent-banner">
        <div className="agent-banner-info">
          <span className="agent-banner-icon">{currentAgent.icon}</span>
          <div>
            <div className="agent-banner-title">{currentAgent.fullName}</div>
            <div className="agent-banner-tagline">{currentAgent.tagline}</div>
          </div>
        </div>
        <div className="agent-banner-status">
          {currentStatus === "running" && (
            <span className="status-pill running">
              <span className="status-pill-dot" /> Streaming insights...
            </span>
          )}
          {currentStatus === "complete" && (
            <span className="status-pill complete">✓ Analysis Ready</span>
          )}
          {currentStatus === "error" && (
            <span className="status-pill error">⚠ Evaluation Error</span>
          )}
          {currentStatus === "idle" && !currentOutput && (
            <span className="status-pill idle">Awaiting Run</span>
          )}
        </div>
      </div>

      {/* Output Content Area */}
      <div className="agent-output-scrollable">
        {currentOutput ? (
          <div
            className="agent-markdown-body"
            dangerouslySetInnerHTML={{
              __html: marked.parse(currentOutput, { breaks: true }),
            }}
          />
        ) : (
          <div className="agent-empty-state">
            <div className="empty-state-icon">{currentAgent.icon}</div>
            <h4>{currentAgent.fullName} is ready</h4>
            <p>
              Click <strong>"Multi-Agent Debug"</strong> to run all 4 specialized agents in parallel
              (Security, Performance, Unit Tests, and Root Cause Diagnostics).
            </p>
          </div>
        )}
      </div>
    </div>
  );
}
