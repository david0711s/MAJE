"""
MAJE – Whitelists
1) Pentesting target whitelist (hard gate, server-side – cannot be bypassed by prompts).
2) Access whitelist (phone numbers / passcodes) backed by the settings table.
"""
from __future__ import annotations

import ipaddress
import json
import re
import uuid
from datetime import datetime
from typing import Optional, Tuple
from urllib.parse import urlparse

from storage.sqlite_db import db_execute, db_fetchall, db_fetchone

# Default whitelisted ranges (user can add their own in the app)
DEFAULT_WHITELIST: list[str] = [
    "10.10.0.0/16",    # TryHackMe VPN range (standard)
    "10.0.0.0/16",
    "10.129.0.0/16",   # HackTheBox VPN range
]

ACCESS_SETTINGS_KEY = "access_whitelist"

DEFAULT_ACCESS_CONFIG = {
    "active": False,
    "allowed_numbers": [],
    "allowed_passcodes": [],
}


# ═══════════════════════════════════════════════════════════════════════════════
#  ACCESS WHITELIST (phone numbers / passcodes)
# ═══════════════════════════════════════════════════════════════════════════════

def verify_access(sender: Optional[str], passcode: Optional[str], config: dict) -> Tuple[bool, str]:
    """Check whether a sender/passcode may use MAJE.

    Returns (allowed, reason). Kept dependency-free so it is unit-testable.
    """
    if not config or not config.get("active", False):
        return True, "whitelist_disabled"

    numbers = config.get("allowed_numbers", []) or []
    passcodes = config.get("allowed_passcodes", []) or []

    if sender and sender in numbers:
        return True, "allowed_number"
    if passcode and passcode in passcodes:
        return True, "allowed_passcode"

    return False, "access_denied"


async def get_access_config() -> dict:
    """Load the access whitelist config from the settings table."""
    row = await db_fetchone("SELECT value FROM settings WHERE key = ?", (ACCESS_SETTINGS_KEY,))
    if not row:
        return dict(DEFAULT_ACCESS_CONFIG)
    try:
        cfg = json.loads(row["value"])
        return {
            "active": bool(cfg.get("active", False)),
            "allowed_numbers": list(cfg.get("allowed_numbers", [])),
            "allowed_passcodes": list(cfg.get("allowed_passcodes", [])),
        }
    except Exception:
        return dict(DEFAULT_ACCESS_CONFIG)


async def save_access_config(config: dict) -> dict:
    """Persist the access whitelist config."""
    clean = {
        "active": bool(config.get("active", False)),
        "allowed_numbers": [str(n).strip() for n in config.get("allowed_numbers", []) if str(n).strip()],
        "allowed_passcodes": [str(p).strip() for p in config.get("allowed_passcodes", []) if str(p).strip()],
    }
    await db_execute(
        "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
        (ACCESS_SETTINGS_KEY, json.dumps(clean), datetime.utcnow().isoformat()),
    )
    return clean


# ═══════════════════════════════════════════════════════════════════════════════
#  PENTEST TARGET WHITELIST
# ═══════════════════════════════════════════════════════════════════════════════

async def whitelist_check(target: str) -> Tuple[bool, str]:
    """Check if a target (IP, CIDR, or domain) is a whitelisted pentest target."""
    entries = await get_whitelist()
    host = target
    if "://" in target:
        parsed = urlparse(target)
        host = parsed.hostname or target
    # Strip a URL path / port if present
    host = host.split("/")[0]
    if ":" in host and not re.match(r"^[0-9a-fA-F:]+$", host):
        host = host.split(":")[0]

    for entry in entries:
        if _matches(host, entry["target"]):
            return True, f"Matched whitelist entry: {entry['target']}"

    return False, f"'{host}' is not on the whitelist. Add it in Settings → Security."


def _matches(host: str, pattern: str) -> bool:
    """Check if host matches a whitelist pattern (IP, CIDR, or exact/wildcard domain)."""
    if host == pattern:
        return True

    try:
        ip = ipaddress.ip_address(host)
        network = ipaddress.ip_network(pattern, strict=False)
        return ip in network
    except ValueError:
        pass

    if pattern.startswith("*."):
        return host.endswith(pattern[1:])

    if re.match(r"^[a-z0-9-]+\.thm$", host, re.IGNORECASE):
        if pattern in ("*.thm", "tryhackme"):
            return True

    return False


async def get_whitelist() -> list[dict]:
    """Get all pentest whitelist entries from DB + defaults."""
    db_entries = await db_fetchall("SELECT * FROM whitelist ORDER BY added_at DESC")
    db_targets = {e["target"] for e in db_entries}
    all_entries = list(db_entries)
    for default in DEFAULT_WHITELIST:
        if default not in db_targets:
            all_entries.append(
                {"id": f"default_{default}", "target": default, "description": "Default range", "added_at": ""}
            )
    return all_entries


async def add_to_whitelist(target: str, description: str = "") -> str:
    """Add a target to the pentest whitelist."""
    entry_id = uuid.uuid4().hex[:12]
    await db_execute(
        "INSERT OR IGNORE INTO whitelist (id, target, description, added_at) VALUES (?, ?, ?, ?)",
        (entry_id, target, description, datetime.utcnow().isoformat()),
    )
    return entry_id


async def remove_from_whitelist(entry_id: str) -> bool:
    existing = await db_fetchone("SELECT * FROM whitelist WHERE id = ?", (entry_id,))
    if not existing:
        return False
    await db_execute("DELETE FROM whitelist WHERE id = ?", (entry_id,))
    return True
