"""MAJE – Settings Routes (server, whitelist, sandbox limits, API keys)"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from storage.sqlite_db import db_execute, db_fetchall, db_fetchone
from api.middleware.whitelist import (
    add_to_whitelist,
    get_access_config,
    get_whitelist,
    remove_from_whitelist,
    save_access_config,
)
from api.middleware.auth import create_token
from sandbox.sandbox_config import get_limits, update_limits
from config.api_keys import API_PROVIDERS, COST_SETTINGS

router = APIRouter()


def _api_keys_status() -> list[dict]:
    status = []
    for p in API_PROVIDERS:
        keys = [k for k in p.get("keys", []) if k and not str(k).startswith("DEIN_")]
        status.append({"provider": p["name"], "provider_id": p["provider_id"], "configured": bool(keys)})
    return status


def _sandbox_payload() -> dict:
    limits = get_limits()
    return {
        "max_memory_mb": limits["memory_mb"],
        "cpu_quota": limits["cpu_quota"],
        "timeout_seconds": limits["timeout_seconds"],
        "allowed_root": "/maje",
    }


@router.get("/")
async def get_settings():
    """Get all current settings (app-compatible shape)."""
    rows = await db_fetchall("SELECT key, value FROM settings")
    settings = {r["key"]: r["value"] for r in rows}
    return {
        "settings": settings,
        "providers": [
            {"provider_id": p["provider_id"], "name": p["name"], "enabled": p.get("enabled", True),
             "is_free_tier": p.get("is_free_tier", False)}
            for p in API_PROVIDERS
        ],
        "cost_settings": COST_SETTINGS,
        "whitelist": await get_access_config(),
        "sandbox": _sandbox_payload(),
        "api_keys_status": _api_keys_status(),
    }


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.put("/")
async def update_setting(body: SettingUpdate):
    await db_execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
        (body.key, body.value, datetime.utcnow().isoformat()),
    )
    return {"updated": True}


# ── Sandbox limits ────────────────────────────────────────────────────────────

class SandboxConfig(BaseModel):
    max_memory_mb: Optional[int] = None
    cpu_quota: Optional[float] = None
    timeout_seconds: Optional[int] = None
    allowed_root: Optional[str] = None


@router.get("/sandbox")
async def get_sandbox():
    return _sandbox_payload()


@router.post("/sandbox")
async def set_sandbox(body: SandboxConfig):
    update_limits(
        memory_mb=body.max_memory_mb,
        cpu_quota=body.cpu_quota,
        timeout_seconds=body.timeout_seconds,
    )
    await db_execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
        ("sandbox", body.model_dump_json(), datetime.utcnow().isoformat()),
    )
    return {"updated": True, "sandbox": _sandbox_payload()}


# ── Access whitelist (phone numbers / passcodes) ──────────────────────────────

class AccessWhitelist(BaseModel):
    active: bool = False
    allowed_numbers: list[str] = []
    allowed_passcodes: list[str] = []


@router.get("/whitelist")
async def get_access_whitelist():
    return await get_access_config()


@router.post("/whitelist")
async def set_access_whitelist(body: AccessWhitelist):
    return {"updated": True, "whitelist": await save_access_config(body.model_dump())}


# ── Pentest target whitelist (hard gate for scanning tools) ───────────────────

class TargetAdd(BaseModel):
    target: str
    description: Optional[str] = ""
    confirmed: bool = False


@router.get("/targets")
async def get_targets():
    return {"whitelist": await get_whitelist()}


@router.post("/targets")
async def add_target(body: TargetAdd):
    if not body.confirmed:
        raise HTTPException(400, "Adding a scan target requires confirmed=true (extra safety check)")
    entry_id = await add_to_whitelist(body.target, body.description or "")
    return {"added": True, "id": entry_id}


@router.delete("/targets/{entry_id}")
async def remove_target(entry_id: str):
    if not await remove_from_whitelist(entry_id):
        raise HTTPException(404, "Whitelist entry not found")
    return {"removed": True}


# ── Auth token generation (localhost only) ────────────────────────────────────

@router.get("/token")
async def get_token(request: Request):
    """Generate a JWT token for the app. Only accessible from localhost."""
    client_host = request.client.host if request.client else ""
    if client_host not in ("127.0.0.1", "::1", "localhost"):
        raise HTTPException(403, "Token generation is only allowed from localhost (use SSH port-forward).")
    return {"token": create_token()}
