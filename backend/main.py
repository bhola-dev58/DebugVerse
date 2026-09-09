"""
DebugVerse — FastAPI Backend
Industry-grade AI code debugger with auth, billing, RAG, and multi-model routing.

Endpoints:
  GET  /health              — health check
  GET  /ready               — readiness probe (checks DB + Redis + AI)
  GET  /ai/status           — AI provider availability
  POST /debug               — synchronous debug (non-streaming)
  POST /debug/stream        — SSE streaming debug (auth + rate limited)
  POST /debug/chat          — multi-turn iterative chat (auth + rate limited)
  POST /execute             — sandboxed code execution (auth + rate limited)
  GET  /history             — user's debug session history
  POST /history             — save a session
  DEL  /history/{id}        — delete one session
  DEL  /history             — clear all sessions
  GET  /history/stats       — usage statistics
  GET  /billing/checkout    — create Stripe checkout session (upgrade)
  POST /billing/webhook     — Stripe webhook receiver
  GET  /billing/portal      — Stripe billing portal (manage subscription)
  GET  /billing/status      — current user subscription status
"""

from fastapi import FastAPI, HTTPException, Depends, Request, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv
import os
import logging
import subprocess
import tempfile
import re
import json
import hashlib
from markdown import markdown

# ── Logging ───────────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# ── Environment ───────────────────────────────────────────────────────────────
load_dotenv()
load_dotenv(os.path.join(os.path.dirname(__file__), ".env"))

# ── AI Setup ──────────────────────────────────────────────────────────────────
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("GEMINI_API_KEY not found in environment. Check backend/.env")

from google import genai
client_genai = genai.Client(api_key=api_key)
MODEL_ID = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
logger.info(f"Gemini configured: {MODEL_ID}")

# ── AI Modules ────────────────────────────────────────────────────────────────
try:
    from backend.ai import AIProviderManager, RAGEngine, ConversationMemoryManager, ModelRouter
    from backend.agents import AgentOrchestrator
except ImportError:
    from ai import AIProviderManager, RAGEngine, ConversationMemoryManager, ModelRouter
    from agents import AgentOrchestrator

ai_manager = AIProviderManager()
rag_service = RAGEngine()
memory_service = ConversationMemoryManager()
orchestrator = AgentOrchestrator(provider_manager=ai_manager)

# ── Auth & Billing ────────────────────────────────────────────────────────────
try:
    from backend.auth.supabase_client import get_current_user, get_optional_user
    from backend.auth.rate_limiter import debug_rate_limiter, execute_rate_limiter, chat_rate_limiter
    from backend.billing.stripe_client import (
        create_checkout_session,
        create_billing_portal_session,
        handle_stripe_webhook,
        get_subscription_status,
    )
except ImportError:
    from auth.supabase_client import get_current_user, get_optional_user
    from auth.rate_limiter import debug_rate_limiter, execute_rate_limiter, chat_rate_limiter
    from billing.stripe_client import (
        create_checkout_session,
        create_billing_portal_session,
        handle_stripe_webhook,
        get_subscription_status,
    )

# ── API Routers ───────────────────────────────────────────────────────────────
try:
    from backend.api.history import router as history_router
    from backend.api.rag_api import router as rag_router
except ImportError:
    from api.history import router as history_router
    from api.rag_api import router as rag_router

# ── Config ────────────────────────────────────────────────────────────────────
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
APP_VERSION = "1.0.0"

# ── FastAPI App ───────────────────────────────────────────────────────────────
app = FastAPI(
    title="DebugVerse API",
    description="AI-powered code debugger with RAG, multi-model routing, and sandboxed execution",
    version=APP_VERSION,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS — restrict to frontend domain in production ──────────────────────────
allowed_origins = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-Request-ID"],
    expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Limit"],
)

# ── Middleware: Observability & Security ──────────────────────────────────────
try:
    from backend.middleware.observability import ObservabilityMiddleware, metrics_endpoint, setup_opentelemetry
    from backend.middleware.security import SecurityHeadersMiddleware, PayloadSanitizationMiddleware
except ImportError:
    from middleware.observability import ObservabilityMiddleware, metrics_endpoint, setup_opentelemetry
    from middleware.security import SecurityHeadersMiddleware, PayloadSanitizationMiddleware

app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(PayloadSanitizationMiddleware)
app.add_middleware(ObservabilityMiddleware)

# Initialize OpenTelemetry Tracing
setup_opentelemetry(app)

# Prometheus metrics endpoint
app.add_api_route("/metrics", metrics_endpoint, methods=["GET"], include_in_schema=False)

# ── Include routers ───────────────────────────────────────────────────────────
app.include_router(history_router)
app.include_router(rag_router)


# ── Request ID Middleware ─────────────────────────────────────────────────────
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4())[:8])
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


# ── Request Models ────────────────────────────────────────────────────────────
class CodeRequest(BaseModel):
    code: str
    language: str
    model: Optional[str] = "auto"
    session_id: Optional[str] = "default"


class ChatRequest(BaseModel):
    message: str
    code: Optional[str] = None
    language: Optional[str] = "python"
    model: Optional[str] = "auto"
    session_id: Optional[str] = "default"


class MultiAgentRequest(BaseModel):
    code: str
    language: str
    agents: Optional[List[str]] = None
    session_id: Optional[str] = "default"
    context: Optional[Dict[str, Any]] = None


class CheckoutRequest(BaseModel):
    plan: str = "pro"  # "pro" | "enterprise"


# ── Health & Readiness ────────────────────────────────────────────────────────
@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "version": APP_VERSION,
        "service": "DebugVerse API",
    }


@app.get("/ready")
async def readiness_check():
    """
    Readiness probe — checks all dependencies.
    Returns 503 if any critical dependency is down.
    """
    checks = {
        "gemini": ai_manager.gemini.is_configured,
        "bedrock": ai_manager.bedrock.is_configured,
    }

    # Redis check
    try:
        from auth.rate_limiter import _get_redis
        r = _get_redis()
        if r:
            r.ping()
            checks["redis"] = True
        else:
            checks["redis"] = False
    except Exception:
        checks["redis"] = False

    all_healthy = checks["gemini"]  # Gemini is the only critical dep
    return JSONResponse(
        status_code=200 if all_healthy else 503,
        content={"status": "ready" if all_healthy else "degraded", "checks": checks},
    )


@app.get("/ai/status")
async def get_ai_status():
    """Returns availability of AWS Bedrock, Claude 3.5, and Gemini models."""
    return ai_manager.get_status()


# ── Billing Endpoints ─────────────────────────────────────────────────────────
@app.post("/billing/checkout")
async def billing_checkout(
    body: CheckoutRequest,
    current_user: Dict = Depends(get_current_user),
):
    """Create a Stripe checkout session to upgrade the user's plan."""
    try:
        url = create_checkout_session(
            user_id=current_user["sub"],
            user_email=current_user.get("email", ""),
            plan=body.plan,
        )
        if not url:
            return {"url": None, "message": "Billing not configured. Contact support."}
        return {"url": url}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Checkout error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@app.post("/billing/webhook")
async def billing_webhook(request: Request):
    """
    Stripe webhook endpoint.
    Must be registered in Stripe Dashboard → Webhooks.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        result = handle_stripe_webhook(payload, sig_header)
        return {"status": "ok", "processed": result}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Webhook error: {e}")
        raise HTTPException(status_code=500, detail="Webhook processing failed")


@app.get("/billing/portal")
async def billing_portal(current_user: Dict = Depends(get_current_user)):
    """Create a Stripe Billing Portal session to manage subscription."""
    sub = get_subscription_status(current_user["sub"])
    customer_id = sub.get("stripe_customer_id")
    if not customer_id:
        raise HTTPException(status_code=404, detail="No active subscription found. Upgrade first.")
    try:
        url = create_billing_portal_session(customer_id)
        return {"url": url}
    except Exception as e:
        logger.error(f"Billing portal error: {e}")
        raise HTTPException(status_code=500, detail="Failed to open billing portal")


@app.get("/billing/status")
async def billing_status(current_user: Dict = Depends(get_current_user)):
    """Return current subscription tier and status for the authenticated user."""
    return {
        "user_id": current_user["sub"],
        "email": current_user.get("email"),
        **get_subscription_status(current_user["sub"]),
    }


def _log_usage(user_id: str, event_type: str, model: str = "", language: str = "", session_id: str = ""):
    """Fire-and-forget usage event logging to Supabase."""
    try:
        try:
            from backend.auth.supabase_client import _get_supabase
        except ImportError:
            from auth.supabase_client import _get_supabase
        client = _get_supabase()
        if client:
            client.table("usage_events").insert({
                "user_id": user_id,
                "event_type": event_type,
                "model_used": model,
                "language": language,
                "session_id": session_id,
            }).execute()
    except Exception as e:
        logger.warning(f"Usage logging failed (non-critical): {e}")


# ── Debug Endpoints ───────────────────────────────────────────────────────────
@app.post("/debug")
async def debug_code(
    request: CodeRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _rate: None = Depends(debug_rate_limiter),
):
    """Synchronous debug endpoint with RAG + model routing."""
    try:
        logger.info(f"[debug] user={current_user['sub']} lang={request.language} model={request.model}")

        rag_docs = rag_service.retrieve(request.code, request.language)
        rag_context = rag_service.format_rag_context(rag_docs)
        routing_info = ModelRouter.classify_complexity(request.code, request.language)
        selected_model = routing_info["recommended_model"] if request.model == "auto" else request.model

        system_prompt = (
            f"You are an expert AI software debugger and code optimization engineer.\n"
            f"Programming Language: {request.language}\n"
            f"Complexity Tier: {routing_info['tier']}\n\n"
            f"{rag_context}\n\n"
            f"Structure your response with:\n"
            f"1. **Root Cause Analysis** (identify syntax, logical, or runtime errors)\n"
            f"2. **Corrected Code Solution** (ready to run)\n"
            f"3. **Optimization & Best Practices**"
        )
        prompt = f"Please debug the following {request.language} code:\n```{request.language}\n{request.code}\n```"

        accumulated_text = ""
        active_model_name = selected_model
        async for chunk in ai_manager.stream_debug(prompt, system_prompt, model_preference=selected_model):
            if chunk.get("token"):
                accumulated_text += chunk["token"]
            if chunk.get("model"):
                active_model_name = chunk["model"]

        memory = memory_service.get_or_create_memory(request.session_id)
        memory.add_turn("user", prompt, code_snippet=request.code)
        memory.add_turn("assistant", accumulated_text)

        # Async: log usage
        background_tasks.add_task(
            _log_usage, current_user["sub"], "debug", active_model_name, request.language, request.session_id
        )

        return {
            "debug_response": markdown(accumulated_text),
            "raw_markdown": accumulated_text,
            "model_used": active_model_name,
            "rag_citations": rag_docs,
            "routing": routing_info,
            "status": "success",
        }
    except Exception as e:
        logger.error(f"debug_code error: {e}")
        return {"debug_response": str(e), "status": "error"}


@app.post("/debug/stream")
async def debug_code_stream(
    request: CodeRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _rate: None = Depends(debug_rate_limiter),
):
    """Stream AI debug response with RAG context and model routing via SSE."""
    rag_docs = rag_service.retrieve(request.code, request.language)
    rag_context = rag_service.format_rag_context(rag_docs)
    routing_info = ModelRouter.classify_complexity(request.code, request.language)
    selected_model = routing_info["recommended_model"] if request.model == "auto" else request.model

    system_prompt = (
        f"You are an expert AI software debugger and code optimization engineer.\n"
        f"Programming Language: {request.language}\n"
        f"Complexity Tier: {routing_info['tier']}\n\n"
        f"{rag_context}\n\n"
        f"Structure your response with:\n"
        f"1. **Root Cause Analysis**\n"
        f"2. **Corrected Code Solution**\n"
        f"3. **Optimization & Best Practices**"
    )
    prompt = f"Please debug the following {request.language} code:\n```{request.language}\n{request.code}\n```"

    async def token_generator():
        meta_event = json.dumps({
            "type": "meta",
            "model_requested": request.model,
            "model_selected": selected_model,
            "rag_citations": rag_docs,
            "routing": routing_info,
            "user_tier": current_user.get("tier", "free"),
            "status": "init",
        })
        yield f"data: {meta_event}\n\n"

        full_response = ""
        active_model = selected_model
        try:
            async for chunk in ai_manager.stream_debug(prompt, system_prompt, model_preference=selected_model):
                token = chunk.get("token", "")
                if token:
                    full_response += token
                if chunk.get("model"):
                    active_model = chunk["model"]
                payload = json.dumps({
                    "token": token,
                    "model": chunk.get("model", selected_model),
                    "status": chunk.get("status", "streaming"),
                })
                yield f"data: {payload}\n\n"

            memory = memory_service.get_or_create_memory(request.session_id)
            memory.add_turn("user", prompt, code_snippet=request.code)
            memory.add_turn("assistant", full_response)

            # Log usage (background, non-blocking for the stream)
            background_tasks.add_task(
                _log_usage, current_user["sub"], "debug", active_model, request.language, request.session_id
            )

        except Exception as e:
            error_payload = json.dumps({"token": f"\n\n**Error:** {str(e)}", "status": "error"})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/debug/chat")
async def debug_chat_stream(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _rate: None = Depends(chat_rate_limiter),
):
    """Multi-turn iterative follow-up debugging session with ConversationBufferMemory."""
    memory = memory_service.get_or_create_memory(request.session_id)
    history_context = memory.get_formatted_context()

    rag_docs = rag_service.retrieve(request.code or request.message, request.language or "python")
    rag_context = rag_service.format_rag_context(rag_docs)

    system_prompt = (
        f"You are DebugVerse AI Assistant conducting an interactive debugging session.\n"
        f"Target Language: {request.language}\n\n"
        f"{rag_context}\n\n"
        f"{history_context}\n\n"
        f"Answer the user's follow-up question concisely with actionable code diffs or explanations."
    )

    async def chat_token_generator():
        meta_event = json.dumps({
            "type": "chat_meta",
            "session_id": request.session_id,
            "rag_citations": rag_docs,
            "status": "init",
        })
        yield f"data: {meta_event}\n\n"

        full_response = ""
        try:
            async for chunk in ai_manager.stream_debug(
                request.message, system_prompt, model_preference=request.model or "auto"
            ):
                token = chunk.get("token", "")
                if token:
                    full_response += token
                payload = json.dumps({
                    "token": token,
                    "model": chunk.get("model", "auto"),
                    "status": chunk.get("status", "streaming"),
                })
                yield f"data: {payload}\n\n"

            memory.add_turn("user", request.message, code_snippet=request.code)
            memory.add_turn("assistant", full_response)
            background_tasks.add_task(
                _log_usage, current_user["sub"], "chat", "auto", request.language, request.session_id
            )
        except Exception as e:
            error_payload = json.dumps({"token": f"\n\n**Error:** {str(e)}", "status": "error"})
            yield f"data: {error_payload}\n\n"

    return StreamingResponse(
        chat_token_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


# ── Multi-Agent Parallel Pipeline & WebSocket ────────────────────────────────
@app.get("/agents/catalog")
async def get_agents_catalog():
    """Return available agents metadata for UI."""
    return orchestrator.get_agent_metadata()


@app.post("/debug/multi-agent")
async def debug_multi_agent(
    request: MultiAgentRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _rate: None = Depends(debug_rate_limiter),
):
    """
    Stream all 4 specialized AI agents concurrently via SSE.
    """
    logger.info(f"[multi-agent] user={current_user['sub']} lang={request.language} agents={request.agents}")

    async def sse_agent_generator():
        try:
            async for event in orchestrator.stream_all_parallel(
                code=request.code,
                language=request.language,
                context=request.context,
                selected_agents=request.agents,
            ):
                yield f"data: {json.dumps(event)}\n\n"

            background_tasks.add_task(
                _log_usage,
                current_user["sub"],
                "debug",
                "multi-agent-orchestrator",
                request.language,
                request.session_id or "multi-agent",
            )
        except Exception as e:
            logger.error(f"Multi-agent streaming error: {e}", exc_info=True)
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        sse_agent_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.websocket("/ws/debug/{session_id}")
async def websocket_debug_session(websocket: WebSocket, session_id: str):
    """
    High-performance bidirectional WebSocket endpoint for live multi-agent streaming.
    """
    await websocket.accept()
    logger.info(f"[WebSocket] Connected: session={session_id}")

    try:
        while True:
            data = await websocket.receive_json()
            action = data.get("action", "debug")

            if action == "ping":
                await websocket.send_json({"type": "pong"})
                continue

            if action == "debug":
                code = data.get("code", "")
                language = data.get("language", "python")
                context = data.get("context", {})
                selected_agents = data.get("agents", None)

                await orchestrator.broadcast_to_websocket(
                    websocket=websocket,
                    code=code,
                    language=language,
                    context=context,
                    selected_agents=selected_agents,
                )
    except WebSocketDisconnect:
        logger.info(f"[WebSocket] Disconnected: session={session_id}")
    except Exception as e:
        logger.error(f"[WebSocket] Error in session {session_id}: {e}", exc_info=True)
        try:
            await websocket.send_json({"type": "error", "message": str(e)})
        except Exception:
            pass


# ── Code Execution ────────────────────────────────────────────────────────────
@app.post("/execute")
async def execute_code(
    request: CodeRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict = Depends(get_current_user),
    _rate: None = Depends(execute_rate_limiter),
):
    """Execute code in a security-hardened Docker sandbox."""
    try:
        logger.info(f"[execute] user={current_user['sub']} lang={request.language}")

        ext = ""
        compile_cmd = None
        run_cmd = ""
        file_name = ""

        lang = request.language.lower()
        if lang == "python":
            ext, run_cmd = ".py", "python3 code.py"
        elif lang in ["cpp", "c++"]:
            ext = ".cpp"
            compile_cmd = "g++ code.cpp -o a.out"
            run_cmd = "./a.out"
        elif lang == "c":
            ext = ".c"
            compile_cmd = "gcc code.c -o a.out"
            run_cmd = "./a.out"
        elif lang == "java":
            class_match = re.search(r"class\s+(\w+)", request.code)
            class_name = class_match.group(1) if class_match else "Main"
            file_name = f"{class_name}.java"
            compile_cmd = f"javac {file_name}"
            run_cmd = f"java {class_name}"
        elif lang == "javascript":
            ext, run_cmd = ".js", "node code.js"
        else:
            return {"output": f"Unsupported language: {request.language}", "status": "error"}

        with tempfile.TemporaryDirectory() as tmpdir:
            os.chmod(tmpdir, 0o755)
            if lang != "java":
                file_name = f"code{ext}"
            file_path = os.path.join(tmpdir, file_name)
            with open(file_path, "w") as f:
                f.write(request.code)
            os.chmod(file_path, 0o644)

            docker_cmd = [
                "docker", "run", "--rm",
                "--network", "none",
                "--memory", "256m",
                "--memory-swap", "256m",
                "--cpus", "1.0",
                "--pids-limit", "100",
                "--ulimit", "nofile=1024:1024",
                "--read-only",
                "--tmpfs", "/tmp:rw,size=64m",
                "-v", f"{tmpdir}:/home/sandboxuser:ro",
                "--user", "nobody",
                "debugverse-sandbox",
                "bash", "-c",
                f"cp -r /home/sandboxuser /tmp/work && cd /tmp/work && "
                f"{compile_cmd + ' && ' if compile_cmd else ''}{run_cmd}",
            ]

            process = subprocess.run(
                docker_cmd,
                capture_output=True,
                text=True,
                timeout=10,
            )

            status_str = "success" if process.returncode == 0 else "error"
            output = process.stdout if status_str == "success" else (
                f"STDOUT:\n{process.stdout}\n\nSTDERR:\n{process.stderr}"
            )

            background_tasks.add_task(
                _log_usage, current_user["sub"], "execute", "", request.language, request.session_id
            )
            return {"output": output, "status": status_str}

    except subprocess.TimeoutExpired:
        logger.error("Execution timed out")
        return {"output": "Error: Execution timed out (10s limit exceeded)", "status": "error"}
    except Exception as e:
        logger.error(f"execute_code error: {e}")
        return {"output": str(e), "status": "error"}


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
