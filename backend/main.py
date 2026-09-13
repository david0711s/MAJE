"""
MAJE Backend – Main FastAPI Application
"""
from __future__ import annotations

import json
import os
import sys

# Make backend and repo root importable
_BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT_STR = os.path.abspath(os.path.join(_BACKEND_DIR, ".."))
if _BACKEND_DIR not in sys.path:
    sys.path.insert(0, _BACKEND_DIR)
if _REPO_ROOT_STR not in sys.path:
    sys.path.insert(0, _REPO_ROOT_STR)

from dotenv import load_dotenv
load_dotenv()

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from storage.redis_client import redis_client
from storage.sqlite_db import init_db, db_fetchone
from api.middleware.auth import AuthMiddleware
from api.routes import (
    autonomy,
    chat,
    costs,
    files,
    settings,
    soul,
    tasks,
    ui_elements,
    voice,
)

# Portable default for MAJE_ROOT: ./data inside repo root if unset or on Windows /maje
_REPO_ROOT = Path(__file__).resolve().parent.parent
_DEFAULT_DATA = _REPO_ROOT / "data"

if not os.getenv("MAJE_ROOT") or (os.name == "nt" and os.getenv("MAJE_ROOT") == "/maje"):
    os.environ["MAJE_ROOT"] = str(_DEFAULT_DATA)

MAJE_ROOT = os.getenv("MAJE_ROOT")


def _ensure_dirs():
    for sub in ("scripts", "tools", "skills", "files", "workspace", "soul/memory", "keys"):
        Path(MAJE_ROOT, sub).mkdir(parents=True, exist_ok=True)


async def _apply_saved_sandbox_limits():
    """Apply sandbox limits persisted by the app (settings.sandbox)."""
    from sandbox.sandbox_config import update_limits
    row = await db_fetchone("SELECT value FROM settings WHERE key = ?", ("sandbox",))
    if not row:
        return
    try:
        cfg = json.loads(row["value"])
        update_limits(
            memory_mb=cfg.get("max_memory_mb"),
            cpu_quota=cfg.get("cpu_quota"),
            timeout_seconds=cfg.get("timeout_seconds"),
        )
        logger.info(f"Applied saved sandbox limits: {cfg}")
    except Exception as e:
        logger.warning(f"Could not apply saved sandbox limits: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 MAJE Backend starting up...")
    _ensure_dirs()
    await redis_client.connect()
    await init_db()
    await _apply_saved_sandbox_limits()
    logger.info("✅ MAJE Backend ready.")
    yield
    logger.info("🛑 MAJE Backend shutting down...")
    await redis_client.disconnect()


app = FastAPI(
    title="MAJE Agent API",
    description="Personal AI Agent MAJE – Backend API",
    version="3.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ─────────────────────────────────────────────────────────────────────
_origins = [o.strip() for o in os.getenv("ALLOW_ORIGINS", "*").split(",") if o.strip()]
_origin_regex = os.getenv("ALLOW_ORIGIN_REGEX", "").strip() or None
# If a regex is configured and origins is the default "*", prefer the regex.
if _origin_regex and _origins == ["*"]:
    _origins = []
app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_origin_regex=_origin_regex,
    allow_credentials="*" not in _origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Auth Middleware ───────────────────────────────────────────────────────────
app.add_middleware(AuthMiddleware)

# ── Routers ──────────────────────────────────────────────────────────────────
app.include_router(chat.router,         prefix="/chat",       tags=["Chat"])
app.include_router(tasks.router,        prefix="/tasks",      tags=["Tasks"])
app.include_router(files.router,        prefix="/files",      tags=["Files"])
app.include_router(soul.router,         prefix="/soul",       tags=["Soul & Memory"])
app.include_router(ui_elements.router,  prefix="/ui",         tags=["UI Elements"])
app.include_router(settings.router,     prefix="/settings",   tags=["Settings"])
app.include_router(costs.router,        prefix="/costs",      tags=["Costs"])
app.include_router(autonomy.router,     prefix="/autonomy",   tags=["Autonomy"])
app.include_router(voice.router,        prefix="/voice",      tags=["Voice"])


@app.get("/health")
async def health():
    redis_ok = await redis_client.ping()
    return {"status": "ok", "redis": redis_ok, "version": "3.0.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    host = os.getenv("HOST", "0.0.0.0")
    logger.info(f"🚀 Starte MAJE Backend auf http://{host}:{port}")
    logger.info(f"📖 Swagger-Doku: http://localhost:{port}/docs")
    uvicorn.run("main:app", host=host, port=port, reload=True)
