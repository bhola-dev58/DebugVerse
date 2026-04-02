import React, { useState, useRef, useEffect } from "react";
import Editor from "@monaco-editor/react";
import axios from "axios";

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

const CodeEditor = () => {
  const [code, setCode] = useState("");
  const [language, setLanguage] = useState("javascript");
  const [debugResponse, setDebugResponse] = useState("");
  const [executionOutput, setExecutionOutput] = useState("");
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState("");
  const [debugHistory, setDebugHistory] = useState([]);
  
  const editorRef = useRef(null);
  const editorContainerRef = useRef(null);
  const decorationIdsRef = useRef([]);
  const placeholder = "// Type or paste your code here to debug...\n";

  useEffect(() => {
    ignoreResizeObserverError();
    
    // Load history from session storage if any
    const savedHistory = sessionStorage.getItem("debug_history");
    if (savedHistory) {
      setDebugHistory(JSON.parse(savedHistory));
    }
  }, []);

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

  const handleDebug = async () => {
    const cleanCode = code.trim();
    if (!cleanCode || cleanCode === placeholder.trim()) {
      setError("Please enter some code to debug");
      return;
    }

    try {
      setLoading(true);
      setError("");
      setExecutionOutput("");
      const response = await axios.post("http://localhost:8000/debug", {
        code: cleanCode,
        language,
      });

      const historyItem = {
        id: Date.now(),
        timestamp: new Date().toLocaleTimeString(),
        language,
        code: cleanCode,
        response: response.data.debug_response,
        type: "debug"
      };
      
      const newHistory = [historyItem, ...debugHistory.slice(0, 9)];
      setDebugHistory(newHistory);
      sessionStorage.setItem("debug_history", JSON.stringify(newHistory));

      if (response.data.status === "error") {
        setError(response.data.debug_response);
        setDebugResponse("");
      } else {
        setDebugResponse(response.data.debug_response);
        setError("");
      }
    } catch (err) {
      setError(err.response?.data?.debug_response || "Failed to analyze code.");
    } finally {
      setLoading(false);
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
      const response = await axios.post("http://localhost:8000/execute", {
        code: cleanCode,
        language: language === "cpp" ? "cpp" : language,
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

  const clearHistory = () => {
    setDebugHistory([]);
    sessionStorage.removeItem("debug_history");
  };

  return (
    <div className="App">
      <nav className="navbar">
        <div className="navbar-brand">
          <span className="logo">DebugVerse.</span>
        </div>
        <div className="navbar-links">
          <a href="/">Home</a>
          <a href="/debug">Editor</a>
          <button className="language-selector" style={{marginLeft: '20px'}}>v0.1.0-alpha</button>
        </div>
      </nav>

      <div className="code-editor-container">
        {/* Main Editor Section */}
        <section className="editor-section" ref={editorContainerRef}>
          <div className="editor-header">
            <div className="header-left">
              <span style={{color: 'var(--text-muted)', fontSize: '0.8rem', marginRight: '12px'}}>Language:</span>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="language-selector"
              >
                <option value="javascript">JavaScript</option>
                <option value="python">Python</option>
                <option value="java">Java</option>
                <option value="cpp">C++</option>
              </select>
            </div>
            <div className="header-right">
               <span style={{color: 'var(--accent-primary)', fontSize: '0.8rem'}}>● Connected</span>
            </div>
          </div>

          <div className="editor-wrapper">
            <Editor
              height="100%"
              defaultLanguage={language}
              language={language}
              value={code}
              onChange={handleEditorChange}
              onMount={handleEditorMount}
              theme="vs-dark"
              loading={<div className="editor-loading">Initializing environment...</div>}
            />
          </div>

          <div className="button-group">
            <button
              onClick={handleDebug}
              disabled={loading || running}
              className="debug-button"
            >
              {loading ? "Analyzing..." : "✨ AI Debug"}
            </button>
            <button
              onClick={handleRun}
              disabled={loading || running}
              className="run-button"
            >
              {running ? "Executing..." : "▶ Run Code"}
            </button>
          </div>
        </section>

        {/* Dynamic Sidebar for Results & History */}
        <aside className="sidebar-section">
          {/* Debug Response Card */}
          {(debugResponse || error) && (
            <div className="sidebar-card">
              <h3>{error ? "❌ Error" : "🤖 AI Analysis"}</h3>
              {error ? (
                <div className="error-message">{error}</div>
              ) : (
                <div 
                  className="debug-output"
                  dangerouslySetInnerHTML={{ __html: debugResponse }}
                />
              )}
            </div>
          )}

          {/* Execution Output Card */}
          {executionOutput && (
            <div className="sidebar-card">
              <h3>📟 Console Output</h3>
              <div className="execution-output">
                {executionOutput}
              </div>
            </div>
          )}

          {/* History Card */}
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
