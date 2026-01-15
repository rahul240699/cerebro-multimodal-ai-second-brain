"""
FastAPI Main Application
Entry point for the Cerebro API server
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import ingestion, query, health
from app.core.config import settings

# Initialize FastAPI application
app = FastAPI(
    title="Cerebro API",
    description="Multimodal AI Second Brain - Personal Intelligence Layer",
    version="0.1.0",
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routers
app.include_router(health.router, prefix="/api", tags=["health"])
app.include_router(ingestion.router, prefix="/api/ingest", tags=["ingestion"])
app.include_router(query.router, prefix="/api/query", tags=["query"])


@app.get("/health")
async def root_health_check():
    """Root-level health check for Railway/Render"""
    return {
        "status": "healthy",
        "service": "Cerebro API",
        "version": "0.1.0"
    }


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "Cerebro API is running",
        "docs": "/docs",
        "health": "/health"
    }


@app.on_event("startup")
async def startup_event():
    """Initialize services on application startup"""
    print("🧠 Cerebro API is starting up...")
    # Database connection will be initialized on first request


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on application shutdown"""
    print("🧠 Cerebro API is shutting down...")
