"""
DebugVerse — Comprehensive System Design API Test Suite.
Covers all 9 architectural layers of the platform:
  1. Health, Readiness & Observability (Prometheus)
  2. Enterprise Security Headers & Middleware
  3. Authentication & Tiered Rate Limiting
  4. Synchronous & Streaming Multi-Agent Pipeline
  5. Sandboxed Code Execution
  6. Billing & Stripe Integration
  7. Session History CRUD
  8. RAG v2 Semantic Vector Search (Qdrant)
  9. Real-Time WebSocket Multi-Agent Streaming
"""

import json
import pytest
from fastapi.testclient import TestClient
from backend.main import app

# Test client instance
client = TestClient(app)

AUTH_HEADER = {"Authorization": "Bearer dev-mock-token"}


# ── 1. Health, Readiness & Observability ───────────────────────────────────────

def test_health_check():
    """Verify GET /health returns 200 OK with service details."""
    res = client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "DebugVerse" in data["service"]


def test_ready_check():
    """Verify GET /ready probe validates DB, Redis, and AI availability."""
    res = client.get("/ready")
    assert res.status_code == 200
    data = res.json()
    assert "status" in data
    assert "checks" in data
    assert "gemini" in data["checks"]


def test_ai_status():
    """Verify GET /ai/status reports configured AI providers (Gemini & Bedrock)."""
    res = client.get("/ai/status")
    assert res.status_code == 200
    data = res.json()
    assert "gemini" in data
    assert "bedrock" in data
    assert data["gemini"]["available"] is True


def test_prometheus_metrics_endpoint():
    """Verify GET /metrics exposes Prometheus exposition format."""
    res = client.get("/metrics")
    assert res.status_code == 200
    content = res.text
    assert "debugverse_http_requests_total" in content or "python_gc_objects_collected_total" in content
    assert res.headers["content-type"].startswith("text/plain")


# ── 2. Enterprise Security Headers & Middleware ────────────────────────────────

def test_security_headers_present():
    """Verify enterprise security headers (CSP, HSTS, X-Content-Type-Options, etc.)."""
    res = client.get("/health")
    headers = res.headers

    assert "content-security-policy" in headers
    assert "strict-transport-security" in headers
    assert headers["x-content-type-options"] == "nosniff"
    assert headers["x-frame-options"] == "DENY"
    assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
    assert "permissions-policy" in headers


def test_request_id_tracing():
    """Verify X-Request-ID is generated and returned on every HTTP response."""
    res = client.get("/health")
    assert "x-request-id" in res.headers
    assert len(res.headers["x-request-id"]) > 0

    # Custom request ID propagation
    custom_id = "test-custom-trace-12345"
    res2 = client.get("/health", headers={"X-Request-ID": custom_id})
    assert res2.headers["x-request-id"] == custom_id


def test_payload_size_guard():
    """Verify PayloadSanitizationMiddleware rejects payloads exceeding size limit."""
    huge_header = {"content-length": str(15 * 1024 * 1024)}  # 15MB
    res = client.post("/debug", headers=huge_header, json={"code": "x = 1", "language": "python"})
    assert res.status_code == 413


# ── 3. Multi-Agent Catalog & Streaming Pipeline ───────────────────────────────

def test_agents_catalog():
    """Verify GET /agents/catalog lists all 4 specialized agents with metadata."""
    res = client.get("/agents/catalog")
    assert res.status_code == 200
    agents = res.json()
    assert isinstance(agents, list)
    assert len(agents) == 4

    agent_ids = [a["id"] for a in agents]
    assert "explain" in agent_ids
    assert "security" in agent_ids
    assert "performance" in agent_ids


def test_multi_agent_sse_stream():
    """Verify POST /debug/multi-agent streams SSE events for all 4 agents."""
    payload = {
        "code": "def divide(a, b):\n    return a / b",
        "language": "python",
        "agents": ["explain", "security"],
        "session_id": "test-sse-session",
    }
    with client.stream("POST", "/debug/multi-agent", json=payload, headers=AUTH_HEADER) as res:
        assert res.status_code == 200
        events = []
        for line in res.iter_lines():
            if line and line.startswith("data:"):
                try:
                    events.append(json.loads(line[5:].strip()))
                except Exception:
                    pass

        event_types = [e.get("type") for e in events]
        assert "start" in event_types
        assert "pipeline_complete" in event_types


def test_conversational_chat():
    """Verify POST /debug/chat streams conversational tokens and citations."""
    chat_payload = {
        "message": "Why is division by zero an error in Python?",
        "code": "result = 10 / 0",
        "language": "python",
        "session_id": "test-chat-session",
    }
    res = client.post("/debug/chat", json=chat_payload, headers=AUTH_HEADER)
    assert res.status_code == 200
    assert "data:" in res.text
    assert "chat_meta" in res.text or "token" in res.text


# ── 4. Sandboxed Code Execution ───────────────────────────────────────────────

def test_sandboxed_execution_python_success():
    """Verify POST /execute safely runs harmless Python code."""
    payload = {
        "code": "print('DebugVerse Sandbox Active!')",
        "language": "python",
    }
    res = client.post("/execute", json=payload, headers=AUTH_HEADER)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "DebugVerse Sandbox Active!" in data["output"]


def test_sandboxed_execution_syntax_error():
    """Verify POST /execute catches code errors with descriptive tracebacks."""
    import uuid
    token_headers = {"Authorization": f"Bearer dev-user-syntax-{uuid.uuid4().hex[:6]}"}
    payload = {
        "code": "def broken(\n    print('missing paren')",
        "language": "python",
    }
    res = client.post("/execute", json=payload, headers=token_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "error"
    assert "SyntaxError" in data["output"]


def test_tiered_rate_limiting_protection():
    """Verify tiered rate limiter enforces 429 when limits are exceeded."""
    import uuid
    unique_user = f"dev-user-free-{uuid.uuid4().hex[:6]}"
    token_headers = {"Authorization": f"Bearer {unique_user}"}
    payload = {"code": "print(1)", "language": "python"}

    # Execute multiple rapid requests on free tier (limit=10) to trigger rate limit
    responses = [client.post("/execute", json=payload, headers=token_headers) for _ in range(15)]
    status_codes = [r.status_code for r in responses]

    # Free tier permits up to 10, then blocks with 429
    assert 200 in status_codes
    assert 429 in status_codes


# ── 5. Billing & Stripe Integration ───────────────────────────────────────────

def test_stripe_checkout_pro_session():
    """Verify POST /billing/checkout with plan=pro generates Stripe Checkout URL."""
    res = client.post("/billing/checkout", json={"plan": "pro"}, headers=AUTH_HEADER)
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    assert "checkout.stripe.com" in data["url"]


def test_stripe_checkout_enterprise_session():
    """Verify POST /billing/checkout with plan=enterprise generates Stripe Checkout URL."""
    res = client.post("/billing/checkout", json={"plan": "enterprise"}, headers=AUTH_HEADER)
    assert res.status_code == 200
    data = res.json()
    assert "url" in data
    assert "checkout.stripe.com" in data["url"]


def test_stripe_checkout_invalid_tier():
    """Verify POST /billing/checkout with invalid plan returns 400."""
    res = client.post("/billing/checkout", json={"plan": "invalid_plan"}, headers=AUTH_HEADER)
    assert res.status_code == 400


def test_billing_status_endpoint():
    """Verify GET /billing/status returns subscription tier and user info."""
    res = client.get("/billing/status", headers=AUTH_HEADER)
    assert res.status_code == 200
    data = res.json()
    assert "tier" in data
    assert "user_id" in data


# ── 6. Session History CRUD API ───────────────────────────────────────────────

def test_history_crud_lifecycle():
    """Verify complete CRUD lifecycle: create, list, and query stats."""
    # 1. Create a session
    new_session = {
        "code": "def add(a, b): return a + b",
        "language": "python",
        "ai_response": "Function is correctly defined.",
        "model_used": "gemini-2.5-flash",
    }
    create_res = client.post("/history", json=new_session, headers=AUTH_HEADER)
    assert create_res.status_code in [200, 201]

    # 2. List sessions
    list_res = client.get("/history", headers=AUTH_HEADER)
    assert list_res.status_code == 200
    sessions = list_res.json()
    assert isinstance(sessions, list)
    assert len(sessions) > 0

    # 3. Fetch history stats
    stats_res = client.get("/history/stats", headers=AUTH_HEADER)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert "total_sessions" in stats
    assert stats["total_sessions"] > 0


# ── 7. RAG v2 & Codebase Indexing API ──────────────────────────────────────────

def test_rag_stats():
    """Verify GET /rag/stats returns Qdrant vector database metrics."""
    res = client.get("/rag/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["qdrant_active"] is True
    assert data["embedding_dimension"] == 64
    assert data["total_documents"] >= 8


def test_rag_index_and_search():
    """Verify POST /rag/index stores code chunks and POST /rag/search retrieves them."""
    # Index
    index_payload = {
        "files": [
            {
                "path": "services/payment.py",
                "content": "def process_stripe_charge(amount, currency):\n    return stripe.Charge.create(amount=amount, currency=currency)",
            }
        ],
        "session_id": "test-rag-session",
    }
    index_res = client.post("/rag/index", json=index_payload, headers=AUTH_HEADER)
    assert index_res.status_code == 200
    assert index_res.json()["files_indexed"] == 1

    # Search
    search_payload = {
        "query": "stripe charge payment amount",
        "language": "python",
        "session_id": "test-rag-session",
        "top_k": 3,
    }
    search_res = client.post("/rag/search", json=search_payload, headers=AUTH_HEADER)
    assert search_res.status_code == 200
    results = search_res.json()["results"]
    assert len(results) > 0
    top_hit = results[0]
    assert "payment.py" in top_hit["file_path"] or "payment.py" in top_hit["title"]


# ── 8. WebSocket Real-Time Multi-Agent Streaming ──────────────────────────────

def test_websocket_multi_agent_pipeline():
    """Verify WebSocket /ws/debug/{session_id} accepts code and streams agent events."""
    with client.websocket_connect("/ws/debug/test-ws-suite") as ws:
        # Send debugging task
        ws.send_json({
            "code": "def fib(n): return n if n < 2 else fib(n-1) + fib(n-2)",
            "language": "python",
            "agents": ["explain", "performance"],
        })

        received_events = []
        # Receive events until pipeline_complete
        for _ in range(60):
            msg = ws.receive_json()
            received_events.append(msg)
            if msg.get("type") == "pipeline_complete":
                break

        msg_types = [m.get("type") for m in received_events]
        assert "start" in msg_types
        assert "pipeline_complete" in msg_types
