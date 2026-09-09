const vscode = require("vscode");
const http = require("http");
const https = require("https");
const { URL } = require("url");

/**
 * DebugVerse VSCode Extension
 * Provides parallel multi-agent debugging directly within the IDE.
 */

let currentPanel = null;

function activate(context) {
  console.log("DebugVerse extension activated.");

  // ── Command 1: Analyze Selection / File with 4-Agent Pipeline ───────────────
  const analyzeCmd = vscode.commands.registerCommand(
    "debugverse.analyzeSelection",
    async () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) {
        vscode.window.showWarningMessage("DebugVerse: Open a file to analyze.");
        return;
      }

      const selection = editor.selection;
      const code = selection.isEmpty
        ? editor.document.getText()
        : editor.document.getText(selection);

      if (!code.trim()) {
        vscode.window.showWarningMessage("DebugVerse: Selection or file is empty.");
        return;
      }

      const languageId = editor.document.languageId;
      const config = vscode.workspace.getConfiguration("debugverse");
      const apiUrl = config.get("apiUrl") || "http://localhost:8001";
      const token = config.get("token") || "dev-mock-token";

      // Open or reveal Webview Panel
      if (currentPanel) {
        currentPanel.reveal(vscode.ViewColumn.Beside);
      } else {
        currentPanel = vscode.window.createWebviewPanel(
          "debugverseAnalysis",
          "DebugVerse — 4x Multi-Agent",
          vscode.ViewColumn.Beside,
          {
            enableScripts: true,
            retainContextWhenHidden: true,
          }
        );

        currentPanel.onDidDispose(() => {
          currentPanel = null;
        });
      }

      currentPanel.webview.html = getWebviewContent(languageId);

      // Trigger SSE multi-agent stream
      startMultiAgentStream(currentPanel.webview, apiUrl, token, code, languageId);
    }
  );

  // ── Command 2: Index Workspace into RAG Vector Store ───────────────────────
  const indexCmd = vscode.commands.registerCommand(
    "debugverse.indexWorkspace",
    async () => {
      const workspaceFolders = vscode.workspace.workspaceFolders;
      if (!workspaceFolders || workspaceFolders.length === 0) {
        vscode.window.showWarningMessage("DebugVerse: No workspace folder open.");
        return;
      }

      const config = vscode.workspace.getConfiguration("debugverse");
      const apiUrl = config.get("apiUrl") || "http://localhost:8001";
      const token = config.get("token") || "dev-mock-token";

      vscode.window.withProgress(
        {
          location: vscode.ProgressLocation.Notification,
          title: "DebugVerse: Indexing workspace into RAG vector store...",
          cancellable: false,
        },
        async (progress) => {
          try {
            const files = await vscode.workspace.findFiles(
              "**/*.{py,js,jsx,ts,tsx,java,cpp,c,h}",
              "**/{node_modules,venv,.git,dist,build}/**",
              50
            );

            if (files.length === 0) {
              vscode.window.showInformationMessage("DebugVerse: No supported source files found to index.");
              return;
            }

            const payloadFiles = [];
            for (const fileUri of files) {
              const doc = await vscode.workspace.openTextDocument(fileUri);
              payloadFiles.push({
                path: vscode.workspace.asRelativePath(fileUri),
                content: doc.getText(),
              });
            }

            await postJson(`${apiUrl}/rag/index`, token, {
              files: payloadFiles,
              session_id: "vscode-workspace",
            });

            vscode.window.showInformationMessage(
              `DebugVerse: Successfully indexed ${payloadFiles.length} file(s) into semantic vector store!`
            );
          } catch (err) {
            vscode.window.showErrorMessage(`DebugVerse indexing error: ${err.message}`);
          }
        }
      );
    }
  );

  // ── Command 3: Open Web Studio ─────────────────────────────────────────────
  const studioCmd = vscode.commands.registerCommand(
    "debugverse.openStudio",
    () => {
      vscode.env.openExternal(vscode.Uri.parse("http://localhost:3001"));
    }
  );

  context.subscriptions.push(analyzeCmd, indexCmd, studioCmd);
}

function deactivate() {
  if (currentPanel) {
    currentPanel.dispose();
  }
}

// ── HTTP Helper: POST JSON ───────────────────────────────────────────────────
function postJson(urlStr, token, payload) {
  return new Promise((resolve, reject) => {
    const url = new URL(urlStr);
    const isHttps = url.protocol === "https:";
    const client = isHttps ? https : http;

    const data = JSON.stringify(payload);
    const options = {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(data),
        Authorization: `Bearer ${token}`,
      },
    };

    const req = client.request(options, (res) => {
      let body = "";
      res.on("data", (chunk) => (body += chunk));
      res.on("end", () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(body));
          } catch {
            resolve(body);
          }
        } else {
          reject(new Error(`HTTP ${res.statusCode}: ${body}`));
        }
      });
    });

    req.on("error", reject);
    req.write(data);
    req.end();
  });
}

// ── SSE Stream Reader ────────────────────────────────────────────────────────
function startMultiAgentStream(webview, apiUrl, token, code, language) {
  const url = new URL(`${apiUrl}/debug/multi-agent`);
  const isHttps = url.protocol === "https:";
  const client = isHttps ? https : http;

  const payload = JSON.stringify({
    code: code,
    language: language,
    agents: ["explain", "security", "performance", "test_generator"],
  });

  const req = client.request(
    {
      hostname: url.hostname,
      port: url.port || (isHttps ? 443 : 80),
      path: url.pathname,
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "Content-Length": Buffer.byteLength(payload),
        Authorization: `Bearer ${token}`,
      },
    },
    (res) => {
      let buffer = "";

      res.on("data", (chunk) => {
        buffer += chunk.toString();
        const lines = buffer.split("\n");
        buffer = lines.pop(); // Keep unfinished line

        for (const line of lines) {
          const trimmed = line.trim();
          if (trimmed.startsWith("data:")) {
            try {
              const data = JSON.parse(trimmed.slice(5).trim());
              webview.postMessage(data);
            } catch (e) {
              // Non-JSON SSE ping or keepalive
            }
          }
        }
      });

      res.on("end", () => {
        webview.postMessage({ type: "stream_end" });
      });
    }
  );

  req.on("error", (err) => {
    webview.postMessage({
      type: "error",
      message: `Failed to connect to DebugVerse API: ${err.message}`,
    });
  });

  req.write(payload);
  req.end();
}

// ── Webview HTML Template ────────────────────────────────────────────────────
function getWebviewContent(languageId) {
  return `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>DebugVerse Analysis</title>
  <style>
    :root {
      --bg: #090d16;
      --card-bg: rgba(15, 23, 42, 0.7);
      --border: rgba(148, 163, 184, 0.15);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent: #00f0ff;
      --green: #10b981;
    }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 16px;
      margin: 0;
    }
    .header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 1px solid var(--border);
      padding-bottom: 12px;
      margin-bottom: 16px;
    }
    .title {
      font-size: 1.1rem;
      font-weight: 700;
      color: var(--text);
      display: flex;
      align-items: center;
      gap: 8px;
    }
    .badge {
      font-size: 0.7rem;
      background: rgba(0, 240, 255, 0.15);
      color: var(--accent);
      border: 1px solid var(--accent);
      padding: 2px 8px;
      border-radius: 12px;
      font-weight: 600;
    }
    .tabs {
      display: flex;
      gap: 8px;
      margin-bottom: 16px;
      border-bottom: 1px solid var(--border);
      padding-bottom: 8px;
    }
    .tab-btn {
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 6px 12px;
      border-radius: 6px;
      cursor: pointer;
      font-size: 0.85rem;
      display: flex;
      align-items: center;
      gap: 6px;
      transition: all 0.2s;
    }
    .tab-btn.active {
      background: rgba(0, 240, 255, 0.1);
      border-color: var(--accent);
      color: var(--accent);
      font-weight: 600;
    }
    .panel {
      display: none;
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 16px;
      min-height: 240px;
      white-space: pre-wrap;
      font-family: "JetBrains Mono", Consolas, monospace;
      font-size: 0.85rem;
      line-height: 1.5;
      overflow-x: auto;
    }
    .panel.active {
      display: block;
    }
    .status-dot {
      width: 8px;
      height: 8px;
      border-radius: 50%;
      display: inline-block;
      background: #64748b;
    }
    .status-dot.running {
      background: #f59e0b;
      animation: pulse 1s infinite;
    }
    .status-dot.done {
      background: var(--green);
    }
    @keyframes pulse {
      0% { opacity: 0.4; }
      50% { opacity: 1; }
      100% { opacity: 0.4; }
    }
  </style>
</head>
<body>
  <div class="header">
    <div class="title">
      ⚡ DebugVerse 4-Agent Pipeline
      <span class="badge">PRO MAX</span>
    </div>
    <div id="overall-status" style="font-size: 0.8rem; color: var(--accent);">Initializing...</div>
  </div>

  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('explain')">
      <span class="status-dot" id="dot-explain"></span> Root Cause
    </button>
    <button class="tab-btn" onclick="switchTab('security')">
      <span class="status-dot" id="dot-security"></span> Security
    </button>
    <button class="tab-btn" onclick="switchTab('performance')">
      <span class="status-dot" id="dot-performance"></span> Performance
    </button>
    <button class="tab-btn" onclick="switchTab('test_generator')">
      <span class="status-dot" id="dot-test_generator"></span> Unit Tests
    </button>
  </div>

  <div id="panel-explain" class="panel active">Waiting for Root Cause Explainer...</div>
  <div id="panel-security" class="panel">Waiting for Security Auditor...</div>
  <div id="panel-performance" class="panel">Waiting for Performance Profiler...</div>
  <div id="panel-test_generator" class="panel">Waiting for Test Generator...</div>

  <script>
    const agentTexts = {
      explain: "",
      security: "",
      performance: "",
      test_generator: ""
    };

    function switchTab(agentId) {
      document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
      document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));

      event.currentTarget.classList.add('active');
      document.getElementById('panel-' + agentId).classList.add('active');
    }

    window.addEventListener('message', event => {
      const msg = event.data;
      if (!msg) return;

      if (msg.type === 'agent_start') {
        const dot = document.getElementById('dot-' + msg.agent);
        if (dot) dot.className = 'status-dot running';
        document.getElementById('overall-status').innerText = '4 Agents Running in Parallel...';
      } else if (msg.type === 'agent_chunk') {
        agentTexts[msg.agent] = (agentTexts[msg.agent] || '') + msg.chunk;
        const panel = document.getElementById('panel-' + msg.agent);
        if (panel) panel.innerText = agentTexts[msg.agent];
      } else if (msg.type === 'agent_complete') {
        const dot = document.getElementById('dot-' + msg.agent);
        if (dot) dot.className = 'status-dot done';
      } else if (msg.type === 'pipeline_complete') {
        document.getElementById('overall-status').innerText = '✓ Analysis Completed in ' + (msg.elapsed_seconds || '1.8') + 's';
      } else if (msg.type === 'error') {
        document.getElementById('overall-status').innerText = 'Error: ' + msg.message;
      }
    });
  </script>
</body>
</html>`;
}

module.exports = {
  activate,
  deactivate,
};
