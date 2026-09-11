"""
MAJE Tool – UI Element Management
MAJE can only modify its own 'Für MAJE' custom screen.
Strict scope enforcement: these tools have NO effect outside that screen.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Optional

from storage.sqlite_db import db_execute, db_fetchall, db_fetchone
from loguru import logger


async def create_ui_element(
    label: str,
    action: str,
    linked_script: str = "",
    element_type: str = "button",
    config: str = "{}",
    task_id: Optional[str] = None,
    **kwargs,
) -> str:
    """
    Add a button or widget to the 'Für MAJE' custom screen.
    Rule: no duplicates, must have a real linked_script.
    """
    if not linked_script.strip():
        return "ERROR: create_ui_element requires a linked_script. No UI element without a real function."

    # Check for duplicates
    existing = await db_fetchall("SELECT * FROM ui_elements WHERE label = ?", (label,))
    if existing:
        return f"ERROR: A UI element with label '{label}' already exists. Remove it first or use a different label."

    # Get current max order
    rows = await db_fetchall("SELECT MAX(order_index) as max_order FROM ui_elements")
    max_order = (rows[0].get("max_order") or 0) + 1

    element_id = uuid.uuid4().hex[:12]
    await db_execute(
        """INSERT INTO ui_elements (id, label, action, linked_script, element_type, config, order_index, created_at, task_id)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (element_id, label, action, linked_script, element_type, config, max_order, datetime.utcnow().isoformat(), task_id),
    )
    logger.info(f"UI element created: {label} ({element_id})")
    return f"✅ UI element '{label}' added (id: {element_id})"


async def remove_ui_element(element_id: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Remove an element from the 'Für MAJE' screen."""
    existing = await db_fetchone("SELECT * FROM ui_elements WHERE id = ?", (element_id,))
    if not existing:
        return f"ERROR: No UI element with id '{element_id}'"

    await db_execute("DELETE FROM ui_elements WHERE id = ?", (element_id,))
    return f"✅ UI element '{existing['label']}' removed."


async def reorder_ui(order: list, task_id: Optional[str] = None, **kwargs) -> str:
    """Reorder UI elements. order = list of element IDs in desired order."""
    for idx, element_id in enumerate(order):
        await db_execute("UPDATE ui_elements SET order_index = ? WHERE id = ?", (idx, element_id))
    return f"✅ UI elements reordered ({len(order)} items)"


async def list_ui_elements() -> list[dict]:
    """Get all UI elements sorted by order_index."""
    return await db_fetchall("SELECT * FROM ui_elements ORDER BY order_index ASC")


async def cleanup_unused_ui_elements(active_scripts: list[str]) -> str:
    """
    MAJE's self-cleanup: remove UI elements whose linked_script no longer exists.
    Called periodically by the agent.
    """
    import os
    from pathlib import Path
    MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
    all_elements = await list_ui_elements()
    removed = []
    for el in all_elements:
        script = el.get("linked_script", "")
        if script and not Path(script).exists() and script not in active_scripts:
            await db_execute("DELETE FROM ui_elements WHERE id = ?", (el["id"],))
            removed.append(el["label"])
    if removed:
        return f"🧹 Cleaned up {len(removed)} unused UI elements: {', '.join(removed)}"
    return "✅ No unused UI elements found."
