"""
MAJE – SQLite DB (persistent backup for settings, whitelist, UI elements, memory)
"""
from __future__ import annotations

import os
from pathlib import Path
import aiosqlite
from loguru import logger

def _resolve_db_path() -> str:
    path = os.getenv("SQLITE_PATH")
    if not path:
        root = os.getenv("MAJE_ROOT")
        if not root or (os.name == "nt" and root == "/maje"):
            root = str(Path(__file__).resolve().parent.parent.parent / "data")
        path = str(Path(root) / "soul" / "maje.db")
    return path

DB_PATH = _resolve_db_path()


async def init_db():
    """Create all tables if they don't exist."""
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executescript("""
            CREATE TABLE IF NOT EXISTS settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL,
                updated_at TEXT
            );

            CREATE TABLE IF NOT EXISTS whitelist (
                id TEXT PRIMARY KEY,
                target TEXT NOT NULL,
                description TEXT,
                added_at TEXT
            );

            CREATE TABLE IF NOT EXISTS ui_elements (
                id TEXT PRIMARY KEY,
                label TEXT NOT NULL,
                action TEXT NOT NULL,
                linked_script TEXT,
                element_type TEXT DEFAULT 'button',
                config TEXT DEFAULT '{}',
                order_index INTEGER DEFAULT 0,
                created_at TEXT,
                task_id TEXT
            );

            CREATE TABLE IF NOT EXISTS memory (
                id TEXT PRIMARY KEY,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                created_at TEXT,
                task_id TEXT
            );

            CREATE TABLE IF NOT EXISTS chat_history (
                id TEXT PRIMARY KEY,
                task_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TEXT
            );
        """)
        await db.commit()
    logger.success(f"✅ SQLite initialized at {DB_PATH}")


async def db_execute(query: str, params: tuple = ()):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(query, params)
        await db.commit()


async def db_fetchall(query: str, params: tuple = ()) -> list[dict]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]


async def db_fetchone(query: str, params: tuple = ()) -> dict | None:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute(query, params) as cursor:
            row = await cursor.fetchone()
            return dict(row) if row else None
