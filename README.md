<div align="center">

# DebugVerse

**AI-powered code debugger & sandboxed executor — built for developers, by developers.**

[![Python](https://img.shields.io/badge/Python-3.10+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-19-61DAFB?style=flat&logo=react&logoColor=black)](https://react.dev)
[![Docker](https://img.shields.io/badge/Docker-Sandbox-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Gemini AI](https://img.shields.io/badge/Gemini-2.0_Flash-8E75B2?style=flat&logo=google&logoColor=white)](https://deepmind.google/gemini)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat)](LICENSE)

[Live Demo](#) · [Report Bug](https://github.com/bhola-dev58/DebugVerse/issues) · [Request Feature](https://github.com/bhola-dev58/DebugVerse/issues)

</div>

---

## What is DebugVerse?

DebugVerse is a full-stack AI debugging platform where you paste your code, and it instantly:
- **Analyzes** it using Google Gemini 2.0 Flash for errors, anti-patterns, and best practices
- **Executes** it inside an isolated Docker sandbox — safely, with no network access and a 10-second timeout

Supports **Python, JavaScript, Java, C++, and C**.

---

## Features

| Feature | Description |
|---|---|
| 🤖 AI Debugging | Powered by Gemini 2.0 Flash — finds bugs and suggests fixes |
| ▶ Code Execution | Runs code in a Docker sandbox with zero network access |
| 🛡️ Secure Sandbox | Non-root user, isolated container, execution timeout |
| 📝 Monaco Editor | VS Code-quality editor with syntax highlighting |
| 🕒 Session History | Remembers your last 10 debug sessions per browser tab |
| 📱 Responsive UI | Works on desktop, tablet, and mobile |

---

## Architecture

```
Browser (React + Monaco Editor)
        │
        │  HTTP (axios)
        ▼
FastAPI Backend (Python)
   ├── /debug  ──► Google Gemini API  ──► AI debug response
   └── /execute ──► Docker Sandbox
                        └── ubuntu:22.04 (gcc, g++, python3, node, java)
                             runs code with --network none, 10s timeout
```

---

## Tech Stack

**Backend**
- [FastAPI](https://fastapi.tiangolo.com/) — async Python web framework
- [Google Generative AI SDK](https://pypi.org/project/google-generativeai/) — Gemini 2.0 Flash
- [Docker](https://www.docker.com/) — sandboxed code execution
- `python-dotenv`, `uvicorn`, `markdown`

**Frontend**
- [React 19](https://react.dev/) with React Router
- [Monaco Editor](https://github.com/microsoft/monaco-editor) — the engine behind VS Code
- [Axios](https://axios-http.com/)
- Vanilla CSS with CSS custom properties (glassmorphism design)

---

## Getting Started

### Prerequisites

- Node.js 18+ and npm
- Python 3.10+
- Docker (for code execution)

### 1. Clone the repository

```bash
git clone https://github.com/bhola-dev58/DebugVerse.git
cd DebugVerse
```

### 2. Set up environment variables

Create a `.env` file inside the `backend/` directory:

```bash
# backend/.env
GEMINI_API_KEY=your_api_key_here
```

Get your free API key at [aistudio.google.com](https://aistudio.google.com/).

### 3. Build the Docker sandbox

The code execution feature requires a local Docker image:

```bash
cd backend/sandbox
chmod +x build.sh
./build.sh
cd ../..
```

### 4. Install dependencies & run

```bash
chmod +x setup.sh run.sh
./setup.sh   # installs Python venv + frontend node_modules
./run.sh     # starts both servers concurrently
```

| Service | URL |
|---|---|
| Frontend | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |

### Stopping the servers

```bash
chmod +x kill_ports.sh
./kill_ports.sh
```

---

## Project Structure

```
DebugVerse/
├── backend/
│   ├── sandbox/
│   │   ├── Dockerfile      # Ubuntu sandbox with gcc, g++, python3, node, java
│   │   └── build.sh        # Builds the debugverse-sandbox Docker image
│   ├── .env                # API keys (not committed to git)
│   └── main.py             # FastAPI app — /debug and /execute endpoints
├── frontend/
│   └── src/
│       ├── components/
│       │   └── CodeEditor.js   # Monaco editor + debug/run UI
│       ├── pages/
│       │   └── AboutUs.js      # About page
│       ├── App.js              # Router + landing page
│       ├── App.css             # Component styles
│       └── index.css           # Global design tokens + theme
├── setup.sh                # One-command dependency installer
├── run.sh                  # Starts backend + frontend concurrently
├── kill_ports.sh           # Stops servers and cleans logs
└── requirements.txt        # Python dependencies
```

---

## API Reference

### `POST /debug`
Analyze code for bugs and best practices using Gemini AI.

```json
Request:  { "code": "string", "language": "python" }
Response: { "debug_response": "<html>...", "status": "success" }
```

### `POST /execute`
Execute code inside the Docker sandbox.

```json
Request:  { "code": "string", "language": "python" }
Response: { "output": "Hello World\n", "status": "success" }
```

---

##  Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

This project is licensed under the MIT License.

---
