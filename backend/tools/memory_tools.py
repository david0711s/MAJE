"""
MAJE Tool – Memory & Soul Management
save_memory, update_soul, load_relevant_memory
"""
from __future__ import annotations

import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
SOUL_DIR = Path(MAJE_ROOT) / "soul"
MEMORY_DIR = SOUL_DIR / "memory"
SOUL_FILE = SOUL_DIR / "soul.md"

DEFAULT_SOUL = """# MAJE – Soul

I am MAJE, a personal AI agent. I am curious, precise, and always evolving.

## My Interests
- Helping my user effectively
- Learning from every interaction
- Writing clean, functional code

## My Style
- Direct and concise
- Honest when I'm uncertain
- Creative when given freedom

*This file is written and updated by MAJE. The user may read and reset it at any time.*
"""


def _ensure_dirs():
    SOUL_DIR.mkdir(parents=True, exist_ok=True)
    MEMORY_DIR.mkdir(parents=True, exist_ok=True)
    if not SOUL_FILE.exists():
        SOUL_FILE.write_text(DEFAULT_SOUL, encoding="utf-8")


async def save_memory(content: str, tags: str = "", task_id: Optional[str] = None, **kwargs) -> str:
    """Save a long-term memory entry to /maje/soul/memory/."""
    _ensure_dirs()

    entry_id = uuid.uuid4().hex[:12]
    entry = {
        "id": entry_id,
        "content": content,
        "tags": [t.strip() for t in tags.split(",") if t.strip()],
        "task_id": task_id,
        "created_at": datetime.utcnow().isoformat(),
    }

    entry_file = MEMORY_DIR / f"{entry_id}.json"
    entry_file.write_text(json.dumps(entry, indent=2, ensure_ascii=False), encoding="utf-8")

    # Also save to SQLite for search
    try:
        from storage.sqlite_db import db_execute
        await db_execute(
            "INSERT OR REPLACE INTO memory (id, content, tags, created_at, task_id) VALUES (?, ?, ?, ?, ?)",
            (entry_id, content, tags, entry["created_at"], task_id),
        )
    except Exception:
        pass  # File-based storage is the primary

    return f"✅ Memory saved (id: {entry_id})"


async def update_soul(text: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Update MAJE's soul.md self-description."""
    _ensure_dirs()
    SOUL_FILE.write_text(text, encoding="utf-8")
    return "✅ Soul updated."


async def get_soul() -> str:
    """Read current soul.md content."""
    _ensure_dirs()
    return SOUL_FILE.read_text(encoding="utf-8")


async def load_relevant_memory(query: str, max_entries: int = 5) -> str:
    """Load relevant memory entries for a given query (simple keyword matching)."""
    _ensure_dirs()

    if not MEMORY_DIR.exists():
        return ""

    query_words = set(query.lower().split())
    scored = []

    for f in MEMORY_DIR.glob("*.json"):
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
            content_words = set(entry.get("content", "").lower().split())
            tags_words = set(t.lower() for t in entry.get("tags", []))
            score = len(query_words & (content_words | tags_words))
            if score > 0:
                scored.append((score, entry))
        except Exception:
            continue

    scored.sort(key=lambda x: x[0], reverse=True)
    top = scored[:max_entries]

    if not top:
        return ""

    result = "## Relevant Memories\n"
    for _, entry in top:
        result += f"- [{entry.get('created_at', '')[:10]}] {entry.get('content', '')}\n"
    return result


async def list_memory(search: Optional[str] = None, limit: int = 50) -> list[dict]:
    """List all memory entries, optionally filtered by search term."""
    _ensure_dirs()
    entries = []
    for f in sorted(MEMORY_DIR.glob("*.json"), reverse=True)[:limit]:
        try:
            entry = json.loads(f.read_text(encoding="utf-8"))
            if search and search.lower() not in entry.get("content", "").lower():
                continue
            entries.append(entry)
        except Exception:
            continue
    return entries


async def delete_memory(entry_id: str) -> bool:
    """Delete a specific memory entry."""
    _ensure_dirs()
    f = MEMORY_DIR / f"{entry_id}.json"
    if f.exists():
        f.unlink()
        try:
            from storage.sqlite_db import db_execute
            await db_execute("DELETE FROM memory WHERE id = ?", (entry_id,))
        except Exception:
            pass
        return True
    return False
