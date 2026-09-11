"""
MAJE – Pentesting Target Whitelist (Hard Gate)
Serverseitige Prüfung aller Pentesting-Tool-Ziele.
Unabhängig vom Agent-Reasoning – kann nicht per Prompt umgangen werden.
"""
from __future__ import annotations

import ipaddress
import re
from urllib.parse import urlparse
from typing import Tuple

from storage.sqlite_db import db_fetchall, db_execute, db_fetchone
import uuid
from datetime import datetime

# Default whitelisted ranges (empty by default, user must add their own)
DEFAULT_WHITELIST: list[str] = [
    # TryHackMe VPN range (standard)
    "10.10.0.0/16",
    "10.0.0.0/16",
    # HackTheBox VPN range
    "10.129.0.0/16",
]


async def whitelist_check(target: str) -> Tuple[bool, str]:
    """
    Check if a target (IP, CIDR, or domain) is whitelisted.
    Returns (is_allowed, reason).
    """
    entries = await get_whitelist()

    # Extract host from URL if needed
    host = target
    if "://" in target:
        parsed = urlparse(target)
        host = parsed.hostname or target

    for entry in entries:
        if _matches(host, entry["target"]):
            return True, f"Matched whitelist entry: {entry['target']}"

    return False, f"'{host}' is not on the whitelist. Add it in Settings → Security."


def _matches(host: str, pattern: str) -> bool:
    """Check if host matches a whitelist pattern (IP, CIDR, or exact domain)."""
    # Exact match
    if host == pattern:
        return True

    # CIDR range check
    try:
        ip = ipaddress.ip_address(host)
        network = ipaddress.ip_network(pattern, strict=False)
        return ip in network
    except ValueError:
        pass

    # Wildcard domain match (*.example.com)
    if pattern.startswith("*."):
        domain_suffix = pattern[1:]
        return host.endswith(domain_suffix)

    # TryHackMe / HackTheBox hostname patterns
    if re.match(r"^[a-z0-9-]+\.thm$", host, re.IGNORECASE):
        if pattern == "*.thm" or pattern == "tryhackme":
            return True

    return False


async def get_whitelist() -> list[dict]:
    """Get all whitelist entries from DB + defaults."""
    db_entries = await db_fetchall("SELECT * FROM whitelist ORDER BY added_at DESC")
    # Merge defaults (only if not already in DB)
    db_targets = {e["target"] for e in db_entries}
    all_entries = list(db_entries)
    for default in DEFAULT_WHITELIST:
        if default not in db_targets:
            all_entries.append({"id": f"default_{default}", "target": default, "description": "Default range", "added_at": ""})
    return all_entries


async def add_to_whitelist(target: str, description: str = "") -> str:
    """Add a target to the whitelist. Requires extra confirmation (handled in router)."""
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
