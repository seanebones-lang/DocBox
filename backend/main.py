"""
DocBox Backend - Enterprise Healthcare RAG System
Main application entry point with FastAPI.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import sentry_sdk
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config import settings
from api.routes import auth, patients, appointments, clinics, kiosk, rag, graph, admin
from database.postgres import engine, Base
from graph.neo4j_client import Neo4jClient
from rag.embeddings import EmbeddingService
from security.audit import AuditLogger


# Initialize Sentry for error tracking
if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.app_env,
        traces_sample_rate=1.0 if settings.app_env == "development" else 0.1,
    )

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Application lifespan management.
    Handles startup and shutdown events.
    """
    # Startup
    print(f"Starting {settings.app_name} - {settings.app_env} environment")
    
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize Neo4j connection
    neo4j_client = Neo4jClient()
    await neo4j_client.verify_connectivity()
    app.state.neo4j_client = neo4j_client
    
    # Initialize embedding service
    embedding_service = EmbeddingService()
    app.state.embedding_service = embedding_service
    
    # Initialize audit logger
    audit_logger = AuditLogger()
    app.state.audit_logger = audit_logger
    
    print("✓ Database connections established")
    print("✓ Services initialized")
    
    yield
    
    # Shutdown
    print("Shutting down services...")
    await neo4j_client.close()
    await engine.dispose()
    print("✓ Shutdown complete")


# Initialize FastAPI application
app = FastAPI(
    title=settings.app_name,
    description="Enterprise Healthcare RAG System with Graph Database and AI-Powered Insights",
    version="1.0.0",
    docs_url=f"/api/{settings.api_version}/docs",
    redoc_url=f"/api/{settings.api_version}/redoc",
    openapi_url=f"/api/{settings.api_version}/openapi.json",
    lifespan=lifespan,
)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Total-Count", "X-Page", "X-Per-Page"],
)

# Trusted Host Middleware
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=settings.get_allowed_hosts,
)


# Health check endpoint
@app.get("/health", tags=["System"])
async def health_check() -> dict:
    """
    Health check endpoint for monitoring and load balancers.
    Returns application status and version.
    """
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": "1.0.0",
        "environment": settings.app_env,
    }


# Readiness probe
@app.get("/ready", tags=["System"])
async def readiness_check(request: Request) -> dict:
    """
    Readiness probe for Kubernetes.
    Checks if all dependencies are available.
    """
    try:
        # Check database connectivity
        async with engine.connect() as conn:
            await conn.execute("SELECT 1")
        
        # Check Neo4j connectivity
        neo4j_client = request.app.state.neo4j_client
        await neo4j_client.verify_connectivity()
        
        return {
            "status": "ready",
            "database": "connected",
            "graph_db": "connected",
        }
    except Exception as e:
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not_ready", "error": str(e)},
        )


# Liveness probe
@app.get("/live", tags=["System"])
async def liveness_check() -> dict:
    """
    Liveness probe for Kubernetes.
    Returns 200 if application is running.
    """
    return {"status": "alive"}


# Include API routers
app.include_router(
    auth.router,
    prefix=f"/api/{settings.api_version}/auth",
    tags=["Authentication"],
)
app.include_router(
    patients.router,
    prefix=f"/api/{settings.api_version}/patients",
    tags=["Patients"],
)
app.include_router(
    appointments.router,
    prefix=f"/api/{settings.api_version}/appointments",
    tags=["Appointments"],
)
app.include_router(
    clinics.router,
    prefix=f"/api/{settings.api_version}/clinics",
    tags=["Clinics"],
)
app.include_router(
    kiosk.router,
    prefix=f"/api/{settings.api_version}/kiosk",
    tags=["Kiosk"],
)
app.include_router(
    rag.router,
    prefix=f"/api/{settings.api_version}/rag",
    tags=["RAG Queries"],
)
app.include_router(
    graph.router,
    prefix=f"/api/{settings.api_version}/graph",
    tags=["Graph Analytics"],
)
app.include_router(
    admin.router,
    prefix=f"/api/{settings.api_version}/admin",
    tags=["Administration"],
)


# Prometheus metrics endpoint
if settings.enable_metrics:
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Global exception handler for unhandled errors.
    Logs errors and returns appropriate response.
    """
    if settings.app_env != "production":
        # In development, return detailed error
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "Internal server error",
                "detail": str(exc),
                "type": type(exc).__name__,
            },
        )
    
    # In production, return generic error
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "Internal server error"},
    )


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.backend_host,
        port=settings.backend_port,
        reload=settings.debug,
        log_level=settings.log_level.lower(),
    )

