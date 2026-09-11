"""
MAJE Backend – Main FastAPI Application
"""
import sys
import os

# Make config directory importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from storage.redis_client import redis_client
from storage.sqlite_db import init_db
from api.middleware.auth import AuthMiddleware
from api.routes import chat, tasks, files, soul, ui_elements, settings, costs, autonomy


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup / shutdown lifecycle."""
    logger.info("🚀 MAJE Backend starting up...")
    await redis_client.connect()
    await init_db()
    logger.info("✅ MAJE Backend ready.")
    yield
    logger.info("🛑 MAJE Backend shutting down...")
    await redis_client.disconnect()


app = FastAPI(
    title="MAJE Agent API",
    description="Personal AI Agent MAJE – Backend API",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten in production via env var
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth Middleware ───────────────────────────────────────────────────────────
app.add_middleware(AuthMiddleware)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(chat.router,        prefix="/chat",       tags=["Chat"])
app.include_router(tasks.router,       prefix="/tasks",      tags=["Tasks"])
app.include_router(files.router,       prefix="/files",      tags=["Files"])
app.include_router(soul.router,        prefix="/soul",       tags=["Soul & Memory"])
app.include_router(ui_elements.router, prefix="/ui",         tags=["UI Elements"])
app.include_router(settings.router,    prefix="/settings",   tags=["Settings"])
app.include_router(costs.router,       prefix="/costs",      tags=["Costs"])
app.include_router(autonomy.router,    prefix="/autonomy",   tags=["Autonomy"])


@app.get("/health")
async def health():
    redis_ok = await redis_client.ping()
    return {"status": "ok", "redis": redis_ok, "version": "1.0.0"}
