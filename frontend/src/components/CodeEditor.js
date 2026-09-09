import React, { useState, useRef, useEffect, useCallback } from "react";
import Editor from "@monaco-editor/react";
import axios from "axios";
import { marked } from "marked";
import { useAuth } from "../context/AuthContext";
import AgentPanel from "./AgentPanel";
import Navbar from "./Navbar";

// Helper for suppressing ResizeObserver errors
const ignoreResizeObserverError = () => {
  const resizeObserverError = console.error;
  console.error = (...args) => {
    if (args[0]?.includes?.("ResizeObserver loop")) {
      return;
    }
    resizeObserverError(...args);
  };
};

const API_BASE = process.env.REACT_APP_API_URL || "http://localhost:8000";

const CodeEditor = () => {
  // ── Auth ──────────────────────────────────────────────────────────────────
  const { getToken } = useAuth();

  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("javascript");
  const [selectedModel, setSelectedModel] = useState("auto");
  const [activeModelInfo, setActiveModelInfo] = useState("");
  const [ragCitations, setRagCitations] = useState([]);
  const [ragDrawerOpen, setRagDrawerOpen] = useState(false);
  const [debugResponse, setDebugResponse] = useState("");
  const [executionOutput, setExecutionOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [debugHistory, setDebugHistory] = useState([]);

  // Multi-turn conversational chat state (inspired by microsoft/rag_skills)
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState("");
  const [chatLoading, setChatLoading] = useState(false);

  // ── Multi-Agent Parallel Pipeline & WebSocket State ───────────────────────
  const [sidebarTab, setSidebarTab] = useState("multi-agent");
  const [multiAgentRunning, setMultiAgentRunning] = useState(false);
  const [agentOutputs, setAgentOutputs] = useState({
    explain: "",
    security: "",
    performance: "",
    tests: "",
  });
  const [agentStatuses, setAgentStatuses] = useState({
    explain: "idle",
    security: "idle",
    performance: "idle",
    tests: "idle",
  });
  
  const editorRef = useRef(null);
  const editorContainerRef = useRef(null);
  const placeholder = "// Type or paste your code here to debug...\n";
  const [theme, setTheme] = useState(() => localStorage.getItem('dv-theme') || 'dark');

  const toggleTheme = () => {
    const next = theme === 'dark' ? 'light' : 'dark';
    setTheme(next);
    localStorage.setItem('dv-theme', next);
    document.documentElement.setAttribute('data-theme', next);
  };

  // ── Load history from API (falls back to localStorage for offline) ─────────
  const loadHistory = useCallback(async () => {
    try {
      const token = await getToken();
      const res = await fetch(`${API_BASE}/history?limit=10`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (res.ok) {
        const data = await res.json();
        setDebugHistory(data.map(s => ({
          id: s.id,
          timestamp: new Date(s.created_at).toLocaleTimeString(),
          language: s.language,
          code: s.code,
          response: s.ai_response || "",
          type: "debug",
        })));
        return;
      }
    } catch { /* fallback to localStorage */ }
    const saved = localStorage.getItem("debug_history");
    if (saved) setDebugHistory(JSON.parse(saved));
  }, [getToken]);

  useEffect(() => {
    ignoreResizeObserverError();
    loadHistory();
  }, [loadHistory]);

  // ── Keyboard Shortcuts ───────────────────────────────────────────────────────
  const handleDebugRef = useRef(null);
  const handleRunRef   = useRef(null);

  useEffect(() => {
    const onKeyDown = (e) => {
      // Ctrl+Shift+D → AI Debug
      if (e.ctrlKey && e.shiftKey && e.key.toLowerCase() === 'd') {
        e.preventDefault();
        handleDebugRef.current?.();
      }
      // Ctrl+Enter → Run Code
      if (e.ctrlKey && !e.shiftKey && e.key === 'Enter') {
        e.preventDefault();
        handleRunRef.current?.();
      }
      // Ctrl+L → Clear Editor
      if (e.ctrlKey && e.key.toLowerCase() === 'l') {
        e.preventDefault();
        setCode('');
        setDebugResponse('');
        setExecutionOutput('');
        setError('');
      }
    };
    window.addEventListener('keydown', onKeyDown);
    return () => window.removeEventListener('keydown', onKeyDown);
  }, []);
  // ─────────────────────────────────────────────────────────────────────────────

  const handleEditorChange = (value) => {
    setCode(value);
    setError("");
  };

  const handleEditorMount = (editor, monaco) => {
    editorRef.current = editor;
    
    // Set placeholder if empty
    if (!code) {
      setCode(placeholder);
    }

    editor.updateOptions({
      fontSize: 14,
      fontFamily: "'JetBrains Mono', monospace",
      lineNumbers: "on",
      minimap: { enabled: false },
      scrollBeyondLastLine: false,
      automaticLayout: true,
      padding: { top: 20 },
      cursorBlinking: "smooth",
      cursorSmoothCaretAnimation: "on",
      smoothScrolling: true,
      roundedSelection: true,
    });
  };

  // ── Multi-Agent Debug (Parallel 4-Agent Execution via WebSocket / SSE) ─────
  const handleMultiAgentDebug = async () => {
    const cleanCode = code.trim();
    if (!cleanCode || cleanCode === placeholder.trim() || multiAgentRunning) {
      if (!cleanCode || cleanCode === placeholder.trim()) {
        setError("Please enter some code to analyze");
      }
      return;
    }

    setError("");
    setSidebarTab("multi-agent");
    setMultiAgentRunning(true);
    setAgentOutputs({
      explain: "",
      security: "",
      performance: "",
      tests: "",
    });
    setAgentStatuses({
      explain: "running",
      security: "running",
      performance: "running",
      tests: "running",
    });

    const sessionId = `dv-${Date.now()}`;
    let socketOpened = false;

    // 1. Try WebSocket connection first for real-time bidirectional streaming
    try {
      const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:";
      let wsHost = "localhost:8001";
      try {
        const urlObj = new URL(API_BASE);
        wsHost = urlObj.host;
      } catch (_) {}

      const wsUrl = `${wsProtocol}//${wsHost}/ws/debug/${sessionId}`;
      const ws = new WebSocket(wsUrl);

      await new Promise((resolve, reject) => {
        const timer = setTimeout(() => {
          if (!socketOpened) {
            ws.close();
            reject(new Error("WebSocket timeout"));
          }
        }, 3000);

        ws.onopen = () => {
          socketOpened = true;
          clearTimeout(timer);
          ws.send(
            JSON.stringify({
              action: "debug",
              code: cleanCode,
              language,
              context: { error: executionOutput },
            })
          );
          resolve();
        };

        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            if (data.type === "start" && data.agent) {
              setAgentStatuses((prev) => ({ ...prev, [data.agent]: "running" }));
            } else if (data.type === "chunk" && data.agent) {
              setAgentOutputs((prev) => ({
                ...prev,
                [data.agent]: (prev[data.agent] || "") + (data.text || ""),
              }));
            } else if (data.type === "complete" && data.agent) {
              setAgentStatuses((prev) => ({ ...prev, [data.agent]: "complete" }));
            } else if (data.type === "error" && data.agent) {
              setAgentStatuses((prev) => ({ ...prev, [data.agent]: "error" }));
            } else if (data.type === "all_complete") {
              setMultiAgentRunning(false);
              ws.close();
            }
          } catch (_) {}
        };

        ws.onerror = (err) => {
          clearTimeout(timer);
          reject(err);
        };

        ws.onclose = () => {
          setMultiAgentRunning(false);
        };
      });

    } catch (wsErr) {
      // 2. Seamless HTTP SSE Fallback if WebSockets are blocked or unavailable
      try {
        const token = await getToken();
        const response = await fetch(`${API_BASE}/debug/multi-agent`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Authorization: `Bearer ${token}`,
          },
          body: JSON.stringify({
            code: cleanCode,
            language,
            session_id: sessionId,
            context: { error: executionOutput },
          }),
        });

        if (!response.ok) throw new Error("Multi-agent request failed");

        const reader = response.body.getReader();
        const decoder = new TextDecoder();

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;
          const chunk = decoder.decode(value);
          const lines = chunk.split("\n\n");
          for (const line of lines) {
            if (!line.startsWith("data: ")) continue;
            try {
              const data = JSON.parse(line.replace("data: ", ""));
              if (data.type === "start" && data.agent) {
                setAgentStatuses((prev) => ({ ...prev, [data.agent]: "running" }));
              } else if (data.type === "chunk" && data.agent) {
                setAgentOutputs((prev) => ({
                  ...prev,
                  [data.agent]: (prev[data.agent] || "") + (data.text || ""),
                }));
              } else if (data.type === "complete" && data.agent) {
                setAgentStatuses((prev) => ({ ...prev, [data.agent]: "complete" }));
              } else if (data.type === "error" && data.agent) {
                setAgentStatuses((prev) => ({ ...prev, [data.agent]: "error" }));
              } else if (data.type === "all_complete") {
                setMultiAgentRunning(false);
              }
            } catch (_) {}
          }
        }
      } catch (sseErr) {
        setError("Multi-agent evaluation error. Please check your backend connection.");
      } finally {
        setMultiAgentRunning(false);
      }
    }
  };

  const handleDebug = async () => {
    const cleanCode = code.trim();
    if (!cleanCode || cleanCode === placeholder.trim()) {
      setError("Please enter some code to debug");
      return;
    }

    try {
      setSidebarTab("single-agent");
      setLoading(true);
      setError("");
      setExecutionOutput("");
      setDebugResponse("");
      setRagCitations([]);
      setActiveModelInfo("");
      setChatMessages([]);

      const token = await getToken();
      const response = await fetch(`${API_BASE}/debug/stream`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          code: cleanCode,
          language,
          model: selectedModel,
          session_id: "debug-session",
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulatedMarkdown = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        // Parse SSE lines: "data: {...}\n\n"
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const parsed = JSON.parse(line.slice(6)); // strip "data: "
            if (parsed.type === "meta") {
              if (parsed.rag_citations) setRagCitations(parsed.rag_citations);
              if (parsed.model_selected) setActiveModelInfo(parsed.model_selected);
              continue;
            }
            if (parsed.status === "done") break;
            if (parsed.token) {
              accumulatedMarkdown += parsed.token;
              setDebugResponse(accumulatedMarkdown);
            }
            if (parsed.model && !activeModelInfo) {
              setActiveModelInfo(parsed.model);
            }
          } catch (_) {
            // ignore partial JSON lines
          }
        }
      }

      // Save to history (API first, localStorage fallback)
      const historyItem = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        language,
        code: cleanCode,
        response: accumulatedMarkdown,
        type: "debug",
      };
      setDebugHistory(prev => [historyItem, ...prev.slice(0, 9)]);
      try {
        const token = await getToken();
        await fetch(`${API_BASE}/history`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "Authorization": `Bearer ${token}` },
          body: JSON.stringify({ language, code: cleanCode, raw_markdown: accumulatedMarkdown, model_used: activeModelInfo }),
        });
      } catch {
        // fallback: persist to localStorage
        const newHistory = [historyItem, ...debugHistory.slice(0, 9)];
        localStorage.setItem("debug_history", JSON.stringify(newHistory));
      }

    } catch (err) {
      setError("Failed to connect to AI backend. Is the server running?");
    } finally {
      setLoading(false);
    }
  };

  const handleSendChat = async (e) => {
    e?.preventDefault();
    const query = chatInput.trim();
    if (!query || chatLoading) return;

    setChatLoading(true);
    setChatInput("");
    const userMsg = { role: "user", content: query };
    const assistantMsgIndex = chatMessages.length + 1;
    setChatMessages((prev) => [...prev, userMsg, { role: "assistant", content: "" }]);

    try {
      const token = await getToken();
      const response = await fetch(`${API_BASE}/debug/chat`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Authorization": `Bearer ${token}`,
        },
        body: JSON.stringify({
          message: query,
          code: code.trim(),
          language,
          model: selectedModel,
          session_id: "debug-session",
        }),
      });

      if (!response.ok) throw new Error("Chat request failed");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";
      const updateAssistantMessage = (newText) => {
        setChatMessages((prev) => {
          const updated = [...prev];
          if (updated[assistantMsgIndex]) {
            updated[assistantMsgIndex] = {
              ...updated[assistantMsgIndex],
              content: newText,
            };
          }
          return updated;
        });
      };

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n").filter((l) => l.startsWith("data: "));
        for (const line of lines) {
          try {
            const parsed = JSON.parse(line.slice(6));
            if (parsed.token) {
              accumulated += parsed.token;
              updateAssistantMessage(accumulated);
            }
          } catch (_) {}
        }
      }
    } catch (err) {
      setChatMessages((prev) => [
        ...prev,
        { role: "assistant", content: "⚠️ Failed to stream follow-up response. Please verify backend status." },
      ]);
    } finally {
      setChatLoading(false);
    }
  };

  const handleRun = async () => {
    const cleanCode = code.trim();
    if (!cleanCode || cleanCode === placeholder.trim()) {
      setError("Please enter some code to run");
      return;
    }

    try {
      setRunning(true);
      setError("");
      setExecutionOutput("Launching sandbox environment... 🚀\n");
      const token = await getToken();
      const response = await axios.post(`${API_BASE}/execute`, {
        code: cleanCode,
        language: language,
      }, {
        headers: { Authorization: `Bearer ${token}` },
      });

      if (response.data.status === "error") {
        setError("Execution failed");
      }
      setExecutionOutput(response.data.output);
      setDebugResponse("");
    } catch (err) {
      setExecutionOutput("Execution Error: Check if the Docker sandbox is built and the backend is running.\n" + (err.response?.data?.output || ""));
      setError("Connection refused");
    } finally {
      setRunning(false);
    }
  };

  const clearHistory = async () => {
    setDebugHistory([]);
    localStorage.removeItem("debug_history");
    try {
      const token = await getToken();
      await fetch(`${API_BASE}/history`, {
        method: "DELETE",
        headers: { Authorization: `Bearer ${token}` },
      });
    } catch { /* non-critical */ }
  };

  // Wire refs after functions are defined
  useEffect(() => { handleDebugRef.current = handleDebug; });
  useEffect(() => { handleRunRef.current = handleRun; });

  return (
    <div className="App">
      <Navbar theme={theme} toggleTheme={toggleTheme} />

      <div className="code-editor-container">
        {/* Main Editor Section */}
        <section className="editor-section" ref={editorContainerRef}>
          <div className="editor-header">
            <div className="header-left">
              <span style={{color: 'var(--text-muted)', fontSize: '0.8rem', marginRight: '6px'}}>Language:</span>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="language-selector"
              >
                <option value="javascript">JavaScript</option>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
                <option value="c">C</option>
              </select>

              <span style={{color: 'var(--text-muted)', fontSize: '0.8rem', margin: '0 6px 0 14px'}}>AI Model:</span>
              <select
                value={selectedModel}
                onChange={(e) => setSelectedModel(e.target.value)}
                className="language-selector model-select-pill"
              >
                <option value="auto">🤖 Auto (Smart Router)</option>
                <option value="claude-3-5-sonnet">☁️ Claude 3.5 Sonnet (AWS Bedrock)</option>
                <option value="gemini-2-5-flash">⚡ Gemini 2.5 Flash</option>
              </select>
            </div>
            <div className="header-right">
              {activeModelInfo && (
                <span className="active-model-tag">
                  {activeModelInfo}
                </span>
              )}
               <span style={{color: 'var(--accent-primary)', fontSize: '0.8rem', marginLeft: '8px'}}>● Connected</span>
            </div>
          </div>

          <div className="editor-wrapper">
            <Editor
              height="100%"
              defaultLanguage={language === "c" ? "cpp" : language}
              language={language === "c" ? "cpp" : language}
              value={code}
              onChange={handleEditorChange}
              onMount={handleEditorMount}
              theme={theme === 'dark' ? 'vs-dark' : 'vs'}
              loading={<div className="editor-loading">Initializing environment...</div>}
            />
          </div>

          <div className="button-group">
            <button
              onClick={handleMultiAgentDebug}
              disabled={loading || running || multiAgentRunning}
              className="multi-agent-button"
              title="Parallel 4-Agent Analysis (Security, Performance, Tests, Root Cause)"
            >
              {multiAgentRunning ? "⏳ Running 4 Agents..." : "⚡ Multi-Agent (4x AI)"}
            </button>
            <button
              onClick={handleDebug}
              disabled={loading || running || multiAgentRunning}
              className="debug-button"
              title="AI Debug (Ctrl+Shift+D)"
            >
              {loading ? "⏳ Streaming..." : "✨ AI Debug"}
              <span className="shortcut-hint">⌃⇧D</span>
            </button>
            <button
              onClick={handleRun}
              disabled={loading || running || multiAgentRunning}
              className="run-button"
              title="Run Code (Ctrl+Enter)"
            >
              {running ? "Executing..." : "▶ Run Code"}
              <span className="shortcut-hint">⌃↵</span>
            </button>
          </div>
        </section>

        {/* Dynamic Sidebar with Multi-Agent & Diagnostic Tabs */}
        <aside className="sidebar-section">
          {/* Top Tab Bar */}
          <div className="sidebar-tabs" role="tablist">
            <button
              className={`sidebar-tab-btn tab-multi-agent ${sidebarTab === 'multi-agent' ? 'active' : ''}`}
              onClick={() => setSidebarTab('multi-agent')}
            >
              ⚡ 4-Agent Pipeline
            </button>
            <button
              className={`sidebar-tab-btn ${sidebarTab === 'single-agent' ? 'active' : ''}`}
              onClick={() => setSidebarTab('single-agent')}
            >
              🤖 Single Agent
            </button>
            <button
              className={`sidebar-tab-btn ${sidebarTab === 'console' ? 'active' : ''}`}
              onClick={() => setSidebarTab('console')}
            >
              📟 Console {executionOutput ? '●' : ''}
            </button>
            <button
              className={`sidebar-tab-btn ${sidebarTab === 'history' ? 'active' : ''}`}
              onClick={() => setSidebarTab('history')}
            >
              🕒 History
            </button>
          </div>

          {/* TAB 1: Multi-Agent Parallel Pipeline */}
          {sidebarTab === 'multi-agent' && (
            <AgentPanel
              agentOutputs={agentOutputs}
              agentStatuses={agentStatuses}
              isRunning={multiAgentRunning}
            />
          )}

          {/* TAB 2: Single Agent Analysis + Conversational Followup */}
          {sidebarTab === 'single-agent' && (
            <div className="sidebar-card">
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px'}}>
                <h3 style={{marginBottom: 0}}>{error ? "❌ Error" : "🤖 Single Agent Analysis"}</h3>
                {activeModelInfo && !error && (
                  <span className="model-chip">{activeModelInfo}</span>
                )}
              </div>

              {/* RAG Knowledge Citations */}
              {ragCitations.length > 0 && !error && (
                <div className="rag-citations-container">
                  <button 
                    type="button"
                    className="rag-toggle-button"
                    onClick={() => setRagDrawerOpen(o => !o)}
                  >
                    <span>📚 Verified RAG References ({ragCitations.length})</span>
                    <span>{ragDrawerOpen ? '▲ Hide' : '▼ View Docs'}</span>
                  </button>
                  {ragDrawerOpen && (
                    <div className="rag-citations-list">
                      {ragCitations.map(doc => (
                        <div key={doc.id} className="rag-citation-item">
                          <a href={doc.url} target="_blank" rel="noopener noreferrer" className="rag-doc-link">
                            {doc.title} ↗
                          </a>
                          <p className="rag-doc-summary">{doc.summary}</p>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {error ? (
                <div className="error-message">{error}</div>
              ) : (
                <>
                  <div 
                    className="debug-output"
                    dangerouslySetInnerHTML={{ __html: marked.parse(debugResponse || (loading ? "*Analyzing code with RAG and LLM reasoning...*" : "*Click 'AI Debug' or run code to generate single-agent analysis.*")) }}
                  />

                  {/* Multi-turn Iterative Follow-up Chat */}
                  {debugResponse && !loading && (
                    <div className="followup-chat-container">
                      <div className="followup-chat-header">
                        💬 Iterative Debugging Assistant (Conversational Memory)
                      </div>

                      {chatMessages.length > 0 && (
                        <div className="chat-messages-scroll">
                          {chatMessages.map((msg, idx) => (
                            <div key={idx} className={`chat-bubble chat-bubble--${msg.role}`}>
                              <span className="chat-bubble-role">
                                {msg.role === 'user' ? 'You' : 'AI'}
                              </span>
                              <div 
                                className="chat-bubble-content"
                                dangerouslySetInnerHTML={{ __html: marked.parse(msg.content || (chatLoading && idx === chatMessages.length - 1 ? "*Thinking...*" : "")) }}
                              />
                            </div>
                          ))}
                        </div>
                      )}

                      <form onSubmit={handleSendChat} className="chat-input-form">
                        <input
                          type="text"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          placeholder="Ask follow-up (e.g. 'Add unit tests', 'Make it thread-safe')..."
                          className="chat-text-input"
                          disabled={chatLoading}
                        />
                        <button type="submit" disabled={chatLoading || !chatInput.trim()} className="chat-send-btn">
                          {chatLoading ? "..." : "Send"}
                        </button>
                      </form>
                    </div>
                  )}
                </>
              )}
            </div>
          )}

          {/* TAB 3: Console Output */}
          {sidebarTab === 'console' && (
            <div className="sidebar-card">
              <h3>📟 Console Sandbox Output</h3>
              <div className="execution-output">
                {executionOutput || "No console execution output yet. Click '▶ Run Code' to execute in the Docker sandbox."}
              </div>
            </div>
          )}

          {/* TAB 4: History Activity */}
          {sidebarTab === 'history' && (
            <div className="sidebar-card">
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px'}}>
                <h3 style={{marginBottom: 0}}>🕒 Recent Activity</h3>
                {debugHistory.length > 0 && (
                  <span onClick={clearHistory} style={{fontSize: '0.7rem', color: 'var(--text-muted)', cursor: 'pointer', textDecoration: 'underline'}}>Clear All</span>
                )}
              </div>
              <div className="history-list">
                {debugHistory.length === 0 ? (
                  <p style={{fontSize: '0.85rem', color: 'var(--text-muted)'}}>No recent activity found.</p>
                ) : (
                  debugHistory.map(item => (
                    <div key={item.id} className="history-item" onClick={() => {
                      setLanguage(item.language);
                      setCode(item.code);
                      if (item.type === 'debug') {
                        setDebugResponse(item.response);
                        setExecutionOutput("");
                        setSidebarTab("single-agent");
                      }
                    }} style={{
                      padding: '10px',
                      borderRadius: '8px',
                      background: 'var(--bg-tertiary)',
                      marginBottom: '8px',
                      cursor: 'pointer',
                      fontSize: '0.8rem',
                      transition: 'var(--transition-fast)',
                      border: '1px solid transparent'
                    }}>
                      <div style={{display: 'flex', justifyContent: 'space-between', color: 'var(--text-secondary)'}}>
                        <span>{item.language.toUpperCase()}</span>
                        <span>{item.timestamp}</span>
                      </div>
                      <div style={{color: 'var(--text-muted)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}}>
                        {item.code.substring(0, 30)}...
                      </div>
                    </div>
                  ))
                )}
              </div>
            </div>
          )}
        </aside>
      </div>

      <footer className="App-footer">
        <div style={{textAlign: 'center', color: 'var(--text-muted)', fontSize: '0.9rem'}}>
          <p>© 2026 DebugVerse. All rights reserved.</p>
        </div>
      </footer>
    </div>
  );
};

export default CodeEditor;
