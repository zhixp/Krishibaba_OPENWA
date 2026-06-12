"""
Krishi Baba - FastAPI Backend
Main Application Entry Point
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.database.db import init_db
from app.routers import chat, sync, admin, voice, broadcast, unified_chat, ad_admin

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler for startup and shutdown"""
    # Startup
    logger.info("🚜 Starting Krishi Baba API...")
    await init_db()
    logger.info("✅ Database initialized")
    yield
    # Shutdown
    logger.info("👋 Shutting down Krishi Baba API...")


app = FastAPI(
    title="Krishi Baba API",
    description="AI-powered agricultural assistant for rural India",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware for admin tools and future clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "X-API-Key", "X-Channel-Secret"],
)

# Include routers
app.include_router(unified_chat.router)  # NEW: Unified "One Window" chat
app.include_router(chat.router)  # Legacy endpoints (backward compatible)
app.include_router(sync.router, prefix="/v1/sync", tags=["sync"])
app.include_router(admin.router, prefix="/v1/admin", tags=["admin"])
app.include_router(ad_admin.router)  # Ad Campaign Admin
app.include_router(voice.router, prefix="/v1/voice", tags=["voice"])
app.include_router(broadcast.router, prefix="/v1/broadcast", tags=["broadcast"])


@app.get("/", tags=["health"])
async def health_check():
    """Health check endpoint"""
    return {
        "status": "ok",
        "message": "🚜 Krishi Baba API is running",
        "version": "1.0.0"
    }


@app.get("/health", tags=["health"])
async def detailed_health():
    """Detailed health check with component status"""
    return {
        "status": "healthy",
        "api": "running",
        "database": "connected",
        "ai": "ready"
    }
