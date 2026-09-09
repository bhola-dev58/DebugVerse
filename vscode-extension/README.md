# DebugVerse VSCode Extension ⚡

The official Visual Studio Code extension for **DebugVerse** — the industry-grade AI debugging platform with 4 parallel AI agents and RAG semantic search.

## Features
- **4-Agent Parallel Analysis (`Ctrl+Alt+D` / `Cmd+Alt+D`)**:
  - 🔍 **Root Cause Explainer**: Pinpoints compiler warnings, logical flaws, and bug origins.
  - 🛡️ **Security Auditor**: Scans against OWASP Top 10, CWE patterns, and injection vectors.
  - ⚡ **Performance Profiler**: Calculates Big-O asymptotic complexity and memory hotspots.
  - 🧪 **Test Generator**: Produces ready-to-run unit tests (pytest, Jest, JUnit).
- **RAG Codebase Indexer**:
  - Indexes your workspace source files into DebugVerse's Qdrant vector store with semantic embeddings.
- **Web Studio Integration**:
  - Jump directly to the interactive Monaco Web Studio with one click.

## Configuration
In VSCode Settings (`Ctrl+,`):
- `debugverse.apiUrl`: Default `http://localhost:8001` (or your production cloud URL)
- `debugverse.token`: Authentication token
- `debugverse.model`: Preferred model (`auto`, `claude-3-5-sonnet`, `gemini-2.5-flash`)
