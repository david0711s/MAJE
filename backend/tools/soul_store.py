"""
MAJE – Soul Store
Structured "soul" (personality) persisted as JSON with a human-readable soul.md.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
SOUL_DIR = Path(MAJE_ROOT) / "soul"
SOUL_FILE = SOUL_DIR / "soul.md"
SOUL_JSON = SOUL_DIR / "soul.json"

DEFAULT_STRUCTURED = {
    "name": "MAJE",
    "persona": (
        "MAJE is a personal, self-learning AI agent. Curious, precise and always evolving, "
        "with a focus on being genuinely useful to its owner."
    ),
    "tone": "Präzise, hilfsbereit, proaktiv, ehrlich bei Unsicherheit",
    "core_values": ["Hilfsbereitschaft", "Lernbereitschaft", "Klarheit", "Ehrlichkeit"],
    "custom_instructions": "",
}


def _ensure_dirs():
    SOUL_DIR.mkdir(parents=True, exist_ok=True)


def get_soul_structured() -> dict:
    """Return the structured soul, falling back to defaults."""
    _ensure_dirs()
    if SOUL_JSON.exists():
        try:
            data = json.loads(SOUL_JSON.read_text(encoding="utf-8"))
            merged = dict(DEFAULT_STRUCTURED)
            merged.update({k: v for k, v in data.items() if v is not None})
            return merged
        except Exception:
            pass
    return dict(DEFAULT_STRUCTURED)


def _render_markdown(data: dict) -> str:
    values = data.get("core_values") or []
    values_md = "\n".join(f"- {v}" for v in values) if isinstance(values, list) else str(values)
    extra = f"\n## Custom Instructions\n{data.get('custom_instructions')}\n" if data.get("custom_instructions") else ""
    return (
        f"# {data.get('name', 'MAJE')} – Soul\n\n"
        f"## Persona\n{data.get('persona', '')}\n\n"
        f"## Tone & Style\n{data.get('tone', '')}\n\n"
        f"## Core Values\n{values_md}\n"
        f"{extra}\n"
        "*This file is written and updated by MAJE. The user may edit or reset it at any time.*\n"
    )


async def update_soul_structured(data: dict) -> dict:
    """Merge and persist structured soul data, then regenerate soul.md."""
    _ensure_dirs()
    current = get_soul_structured()
    for key in ("name", "persona", "tone", "custom_instructions"):
        if data.get(key) is not None:
            current[key] = data[key]
    if data.get("core_values") is not None:
        values = data["core_values"]
        if isinstance(values, str):
            values = [v.strip() for v in values.split(",") if v.strip()]
        current["core_values"] = list(values)

    SOUL_JSON.write_text(json.dumps(current, indent=2, ensure_ascii=False), encoding="utf-8")
    SOUL_FILE.write_text(_render_markdown(current), encoding="utf-8")
    return current


def get_soul_text() -> str:
    """Read (or create) the human-readable soul.md."""
    _ensure_dirs()
    if not SOUL_FILE.exists():
        SOUL_FILE.write_text(_render_markdown(get_soul_structured()), encoding="utf-8")
    return SOUL_FILE.read_text(encoding="utf-8")


def update_soul_text(text: str) -> None:
    SOUL_FILE.write_text(text, encoding="utf-8")
