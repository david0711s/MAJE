"""MAJE – Settings Routes (server, whitelist, sandbox limits, API keys)"""
from __future__ import annotations

import json
import os
import ipaddress
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
from sandbox.sandbox_config import get_limits, network_allowed, update_limits
from config import api_keys as ak
from config import key_loader
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

def _is_local_request(request: Request) -> bool:
    """True if the request came directly from the host (not from the internet).

    Note: with Docker port mapping, a request to 127.0.0.1:8000 arrives inside the
    container from the bridge gateway (e.g. 172.18.0.1) – so we accept loopback
    AND private ranges, but NOT when proxy headers are present (i.e. via Caddy).
    """
    host = request.client.host if request.client else ""
    if host in ("127.0.0.1", "::1", "localhost"):
        return True
    if request.headers.get("x-forwarded-for") or request.headers.get("x-real-ip"):
        return False  # came through a reverse proxy -> treat as remote
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_loopback or ip.is_private
    except ValueError:
        return False


@router.get("/token")
async def get_token(request: Request):
    """Generate a JWT token for the app. Only accessible from localhost/private network."""
    if not _is_local_request(request):
        raise HTTPException(
            403,
            "Token generation is only allowed from localhost. "
            "Alternative on the server: docker compose exec -T maje-backend "
            "python -c \"from api.middleware.auth import create_token; print(create_token())\"",
        )
    return {"token": create_token()}


# ═══════════════════════════════════════════════════════════════════════════════
#  API-KEYS (zentral, skalierbar, optional verschlüsselt)
#  Keys werden in config/keys.json gespeichert (chmod 600) und zur Laufzeit
#  in die Provider-Config gemerged – kein Neustart/Build nötig.
# ═══════════════════════════════════════════════════════════════════════════════

def _encryption_available() -> bool:
    try:
        from cryptography.fernet import Fernet  # noqa: F401
        return True
    except Exception:
        return False


def _reload_keys() -> dict[str, list[str]]:
    data = key_loader.load_keys()
    key_loader.apply_keys(ak.API_PROVIDERS, ak.EXTERNAL_SERVICES, data)
    return data


@router.get("/status")
async def get_status():
    """Kompakter Einrichtungs-Status (für den Setup-Assistenten in der App)."""
    current = key_loader.collect_current(ak.API_PROVIDERS, ak.EXTERNAL_SERVICES)
    llm_ids = ["gemini", "groq", "deepseek", "openai", "anthropic", "mistral", "together"]
    llm_configured = [pid for pid in llm_ids if current.get(pid)]
    return {
        "server": "ok",
        "version": "3.0.0",
        "setup_complete": bool(llm_configured),
        "llm_keys_configured": bool(llm_configured),
        "configured_providers": llm_configured,
        "search_configured": bool(current.get("tavily") or current.get("serper") or current.get("brave_search")),
        "voice_configured": bool(current.get("groq")),
        "encryption_enabled": key_loader.encryption_enabled(),
        "sandbox_network": network_allowed(),
    }


@router.get("/keys")
async def get_api_keys():
    """List all providers with masked keys + encryption status."""
    current = key_loader.collect_current(ak.API_PROVIDERS, ak.EXTERNAL_SERVICES)
    providers = []
    for p in ak.API_PROVIDERS:
        pid = p["provider_id"]
        keys = current.get(pid, [])
        providers.append({
            "provider_id": pid,
            "name": p.get("name", pid),
            "label": key_loader.PROVIDER_LABELS.get(pid, p.get("name", pid)),
            "configured": bool(keys),
            "count": len(keys),
            "keys": [key_loader.mask(k) for k in keys],
            "is_free_tier": p.get("is_free_tier", False),
            "enabled": p.get("enabled", True),
        })
    for name, cfg in ak.EXTERNAL_SERVICES.items():
        keys = current.get(name, [])
        providers.append({
            "provider_id": name,
            "name": cfg.get("name", name),
            "label": key_loader.PROVIDER_LABELS.get(name, name),
            "configured": bool(keys),
            "count": len(keys),
            "keys": [key_loader.mask(k) for k in keys],
            "is_free_tier": False,
            "enabled": cfg.get("enabled", False),
        })
    return {
        "providers": providers,
        "encryption": {
            "available": _encryption_available(),
            "enabled": key_loader.encryption_enabled(),
            "key_configured": bool(os.getenv("MAJE_KEYS_KEY")),
        },
        "file": str(key_loader.keys_file_path()),
    }


class KeyUpdate(BaseModel):
    provider_id: str
    keys: list[str] = []
    replace: bool = False


@router.post("/keys")
async def set_api_keys(body: KeyUpdate):
    """Add (or replace) keys for a provider and hot-reload them."""
    data = key_loader.load_keys(include_env=False)  # only the file, not env
    new_keys = [k.strip() for k in body.keys if k and k.strip()]

    if body.replace:
        data[body.provider_id] = new_keys
    else:
        data.setdefault(body.provider_id, [])
        for k in new_keys:
            if k not in data[body.provider_id]:
                data[body.provider_id].append(k)

    key_loader.save_keys(data)
    _reload_keys()
    return {"updated": True, "provider_id": body.provider_id, "count": len(data.get(body.provider_id, []))}


@router.delete("/keys/{provider_id}")
async def delete_api_keys(provider_id: str, index: Optional[int] = None):
    """Remove all keys of a provider (or a single key via ?index=)."""
    data = key_loader.load_keys(include_env=False)
    if provider_id not in data:
        raise HTTPException(404, "Keine Keys für diesen Provider gespeichert.")
    if index is None:
        data.pop(provider_id, None)
    else:
        if 0 <= index < len(data[provider_id]):
            data[provider_id].pop(index)
        if not data.get(provider_id):
            data.pop(provider_id, None)
    key_loader.save_keys(data)
    _reload_keys()
    return {"deleted": True, "provider_id": provider_id}


class EncryptionToggle(BaseModel):
    enabled: bool


@router.post("/keys/encryption")
async def set_encryption(body: EncryptionToggle):
    """Re-save the keys file encrypted (needs MAJE_KEYS_KEY) or as plaintext."""
    if body.enabled and not key_loader.encryption_enabled():
        raise HTTPException(
            400,
            "Verschlüsselung nicht möglich: setze MAJE_KEYS_KEY in der .env "
            "(Key erzeugen mit GET /settings/keys/newkey).",
        )
    data = key_loader.load_keys(include_env=False)
    key_loader.save_keys(data, encrypt=body.enabled)
    _reload_keys()
    return {"updated": True, "encrypted": body.enabled and key_loader.encryption_enabled()}


@router.get("/keys/newkey")
async def new_encryption_key():
    """Generate a Fernet key for MAJE_KEYS_KEY (put it into the server .env)."""
    if not _encryption_available():
        raise HTTPException(400, "cryptography ist nicht installiert.")
    key = key_loader.generate_key()
    return {"key": key, "env_line": f"MAJE_KEYS_KEY={key}"}

