"""FastAPI entry point for FinGuard AI backend.
Provides transaction management, expert system inference, assessments, dashboard metrics, data ingestion, and health checks.
"""

import uuid
import re
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.core.config import settings
from app.db.session import init_db, SessionLocal
from app.api import (
    dashboard,
    transactions,
    expert_system,
    assessments,
    models,
    analytics,
    cases,
    auth,
    users,
    audit,
)

logger = logging.getLogger("finguard")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize SQLite database schema and bootstrap initial accounts
    init_db()
    yield

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    description="FinGuard AI — Financial Transaction Intelligence, Expert System & Security Hardened API"
)

# CORS configuration – explicitly configured approved origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """
    Attach correlation ID to incoming requests and outgoing responses.
    Strictly whitelist-validates user-supplied correlation headers:
    any header containing CRLF, control characters, or non-identifier tokens
    is discarded and replaced with a fresh cryptographically random UUID4.
    """
    raw_cid = request.headers.get("X-Correlation-ID")
    if raw_cid and re.match(r"^[a-zA-Z0-9_\-\.]{1,64}$", raw_cid.strip()):
        correlation_id = raw_cid.strip()
    else:
        correlation_id = str(uuid.uuid4())

    request.state.correlation_id = correlation_id

    try:
        response: Response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        return response
    except Exception as exc:
        logger.exception(f"Unhandled error during request processing [correlation_id={correlation_id}]: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "detail": "An internal server error occurred.",
                "correlation_id": correlation_id,
            },
            headers={"X-Correlation-ID": correlation_id},
        )


# Register routers
app.include_router(auth.router, prefix="/api")
app.include_router(users.router, prefix="/api")
app.include_router(audit.router, prefix="/api")
app.include_router(dashboard.router, prefix="/api")
app.include_router(transactions.router, prefix="/api")
app.include_router(expert_system.router, prefix="/api")
app.include_router(assessments.router, prefix="/api")
app.include_router(models.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(cases.router, prefix="/api")


@app.get("/health", tags=["system"])
@app.get("/api/health", tags=["system"])
def health_liveness_check():
    """Liveness probe: verifies that the FastAPI web application process is responsive."""
    return {"status": "ok"}


@app.get("/api/health/ready", tags=["system"])
def health_readiness_check():
    """
    Readiness probe: verifies that backing database and expert systems are operational
    and ready to process transaction traffic.
    """
    db_status = "connected"
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
    except Exception as e:
        logger.error(f"Readiness check database failure: {e}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "unready",
                "database": "disconnected",
                "error": "Database connectivity failed.",
            },
        )

    from app.services.assessment_service import default_knowledge_base
    rules_count = len(default_knowledge_base.active_rules())

    return {
        "status": "ready",
        "database": db_status,
        "knowledge_base_rules": rules_count,
        "environment": "active",
    }
