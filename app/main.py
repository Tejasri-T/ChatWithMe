"""FastAPI application entrypoint and middleware orchestration."""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1.router import api_router
from app.api.v1.schemas import HealthResponse
from app.core.config import get_settings
from app.core.db.repository import ThreadRepository
from app.core.db.session import get_checkpointer


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler: runs pre-flight database migrations on startup."""
    # Ensure database tables and checkpointer tables exist
    repo = ThreadRepository()
    repo.init_db()
    get_checkpointer()
    yield


settings = get_settings()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Enterprise Multi-Tenant RAG & Conversational AI Platform",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

# Configure Cross-Origin Resource Sharing (CORS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Inject server-side request processing duration into response headers."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"
    return response


# Register API routers
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health", response_model=HealthResponse, tags=["Health"])
async def health_check():
    """System health check endpoint for monitoring, load balancers, and container orchestration."""
    return HealthResponse(
        status="healthy",
        version=settings.VERSION,
        environment=settings.ENVIRONMENT,
        database="connected",
    )


@app.get("/", tags=["Root"])
async def root():
    """Root redirect / information endpoint."""
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "docs_url": "/docs",
        "api_v1": settings.API_V1_STR,
    }

