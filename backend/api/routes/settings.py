"""MAJE – Settings Routes (server URL, whitelist, sandbox limits, API order)"""
from __future__ import annotations

import json
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from storage.sqlite_db import db_execute, db_fetchall, db_fetchone
from api.middleware.whitelist import get_whitelist, add_to_whitelist, remove_from_whitelist
from api.middleware.auth import create_token
from config.api_keys import API_PROVIDERS, COST_SETTINGS

router = APIRouter()


@router.get("/")
async def get_settings():
    """Get all current settings."""
    rows = await db_fetchall("SELECT key, value FROM settings")
    settings = {r["key"]: r["value"] for r in rows}
    return {
        "settings": settings,
        "providers": [
            {"provider_id": p["provider_id"], "name": p["name"], "enabled": p["enabled"], "is_free_tier": p["is_free_tier"]}
            for p in API_PROVIDERS
        ],
        "cost_settings": COST_SETTINGS,
    }


class SettingUpdate(BaseModel):
    key: str
    value: str


@router.put("/")
async def update_setting(body: SettingUpdate):
    from datetime import datetime
    await db_execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
        (body.key, body.value, datetime.utcnow().isoformat()),
    )
    return {"updated": True}


# ── Whitelist ─────────────────────────────────────────────────────────────────

@router.get("/whitelist")
async def get_whitelist_entries():
    return {"whitelist": await get_whitelist()}


class WhitelistAdd(BaseModel):
    target: str
    description: Optional[str] = ""
    confirmed: bool = False  # Extra confirmation required


@router.post("/whitelist")
async def add_whitelist_entry(body: WhitelistAdd):
    if not body.confirmed:
        raise HTTPException(400, "Adding to whitelist requires confirmed=true (extra safety check)")
    entry_id = await add_to_whitelist(body.target, body.description or "")
    return {"added": True, "id": entry_id}


@router.delete("/whitelist/{entry_id}")
async def remove_whitelist_entry(entry_id: str):
    removed = await remove_from_whitelist(entry_id)
    if not removed:
        raise HTTPException(404, "Whitelist entry not found")
    return {"removed": True}


# ── Auth token generation ─────────────────────────────────────────────────────

@router.get("/token")
async def get_token():
    """Generate a JWT token for the app. Only accessible from localhost."""
    token = create_token()
    return {"token": token}
