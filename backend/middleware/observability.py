"""
DebugVerse Observability Module.
Provides OpenTelemetry distributed tracing and Prometheus production metrics.
Designed for 20,000+ concurrent user scale monitoring.
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import (
    Counter,
    Histogram,
    Gauge,
    generate_latest,
    CONTENT_TYPE_LATEST,
)

logger = logging.getLogger("debugverse.observability")

# ── 1. Prometheus Metrics Definitions ───────────────────────────────────────────
# HTTP Request Tracking
HTTP_REQUESTS_TOTAL = Counter(
    "debugverse_http_requests_total",
    "Total count of HTTP requests processed by DebugVerse",
    ["method", "endpoint", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "debugverse_http_request_duration_seconds",
    "HTTP request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# AI Multi-Agent Metrics
ACTIVE_AGENT_SESSIONS = Gauge(
    "debugverse_active_agent_sessions",
    "Current active concurrent multi-agent debugging sessions",
    ["agent_type"],
)

AI_INFERENCE_DURATION_SECONDS = Histogram(
    "debugverse_ai_inference_duration_seconds",
    "Latency of AI model generations across providers",
    ["provider", "model"],
    buckets=(0.2, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0),
)

AI_TOKEN_USAGE_TOTAL = Counter(
    "debugverse_ai_tokens_total",
    "Estimated tokens consumed across AI providers",
    ["provider", "direction"],  # direction: prompt or completion
)

CONCURRENT_USERS_GAUGE = Gauge(
    "debugverse_concurrent_connections",
    "Number of active WebSocket and SSE client connections",
    ["connection_type"],
)


# ── 2. Observability Middleware ────────────────────────────────────────────────
class ObservabilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware that records Prometheus request duration, status codes, and path latencies.
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Avoid collecting metrics on the metrics endpoint itself to prevent skew
        path = request.url.path
        if path == "/metrics" or path == "/favicon.ico":
            return await call_next(request)

        method = request.method
        start_time = time.time()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception:
            status_code = 500
            raise
        finally:
            duration = max(time.time() - start_time, 0.0001)

            # Normalize parameterized endpoints for low-cardinality metrics
            normalized_path = self._normalize_path(path)
            HTTP_REQUESTS_TOTAL.labels(
                method=method, endpoint=normalized_path, status_code=str(status_code)
            ).inc()
            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method, endpoint=normalized_path
            ).observe(duration)

    @staticmethod
    def _normalize_path(path: str) -> str:
        """Collapse UUIDs, session IDs, and IDs into generic placeholders."""
        parts = path.strip("/").split("/")
        normalized = []
        for part in parts:
            if len(part) >= 16 or any(c.isdigit() for c in part) and len(part) > 8:
                normalized.append("{id}")
            else:
                normalized.append(part)
        return "/" + "/".join(normalized) if normalized else "/"


# ── 3. OpenTelemetry Setup ─────────────────────────────────────────────────────
def setup_opentelemetry(app=None):
    """
    Initialize OpenTelemetry SDK with tracer provider and FastAPI instrumentation.
    Degrades gracefully if OTel collector is not reachable.
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

        resource = Resource.create(
            attributes={
                "service.name": "debugverse-backend",
                "service.version": "2.0.0",
                "deployment.environment": "production",
            }
        )
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        if app is not None:
            FastAPIInstrumentor.instrument_app(app, tracer_provider=provider)
            logger.info("OpenTelemetry successfully instrumented on FastAPI application")

        return trace.get_tracer("debugverse.backend")
    except Exception as e:
        logger.warning(f"OpenTelemetry initialization skipped/fallback: {e}")
        return None


# ── 4. Prometheus Metrics Endpoint Handler ─────────────────────────────────────
async def metrics_endpoint():
    """Returns formatted Prometheus exposition data."""
    return Response(content=generate_latest(), media_type=CONTENT_TYPE_LATEST)
