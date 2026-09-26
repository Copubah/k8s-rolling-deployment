import json
import logging
import os
import socket
import time
from contextlib import asynccontextmanager
from datetime import datetime, timezone

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger("api")
REQUESTS = Counter("app_http_requests_total", "HTTP requests", ["path", "status"])
LATENCY = Histogram("app_http_request_duration_seconds", "HTTP duration", ["path"])


def create_app():
    version = os.getenv("APP_VERSION", "dev")
    delay = max(0, float(os.getenv("STARTUP_DELAY_SECONDS", "0")))
    fail_ready = os.getenv("FAIL_READINESS", "false").lower() == "true"

    @asynccontextmanager
    async def lifespan(app):
        app.state.started = time.monotonic()
        log.info(json.dumps({"event": "startup", "version": version}))
        yield
        log.info(json.dumps({"event": "shutdown", "version": version}))

    app = FastAPI(lifespan=lifespan)

    def payload(status):
        return {
            "version": version,
            "hostname": socket.gethostname(),
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": status,
        }

    def ready():
        return time.monotonic() - app.state.started >= delay and not fail_ready

    @app.middleware("http")
    async def observe(request: Request, call_next):
        start = time.perf_counter()
        path = request.url.path
        label = path if path in {"/api/version", "/health/live", "/health/ready", "/metrics"} else "other"
        try:
            response = await call_next(request)
        except Exception:
            log.exception(json.dumps({"event": "exception", "path": label}))
            response = JSONResponse(payload("error"), status_code=500)
        elapsed = time.perf_counter() - start
        if path != "/metrics":
            REQUESTS.labels(label, str(response.status_code)).inc()
            LATENCY.labels(label).observe(elapsed)
            log.info(
                json.dumps(
                    {
                        "event": "request",
                        "path": label,
                        "status": response.status_code,
                        "duration_ms": round(elapsed * 1000, 2),
                    }
                )
            )
        response.headers["Cache-Control"] = "no-store"
        return response

    @app.get("/api/version")
    async def get_version():
        return JSONResponse(payload("ready" if ready() else "not_ready"), status_code=200 if ready() else 503)

    @app.get("/health/live")
    async def live():
        return payload("alive")

    @app.get("/health/ready")
    async def readiness():
        return JSONResponse(payload("ready" if ready() else "not_ready"), status_code=200 if ready() else 503)

    @app.get("/metrics")
    async def metrics():
        return Response(generate_latest(), headers={"Content-Type": CONTENT_TYPE_LATEST})

    return app


app = create_app()
