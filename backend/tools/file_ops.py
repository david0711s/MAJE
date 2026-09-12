"""
MAJE Tool – File Operations
read_file / write_file for files the user shares (uploaded) or MAJE creates.
All paths are confined to MAJE_ROOT.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
MAX_READ_BYTES = 200 * 1024  # 200 KB


def _safe_path(rel_path: str) -> Path:
    root = Path(MAJE_ROOT).resolve()
    # Allow both '/maje/files/x' and 'files/x'
    clean = rel_path.replace("\\", "/").lstrip("/")
    if clean.startswith("maje/"):
        clean = clean[len("maje/"):]
    resolved = (root / clean).resolve()
    if resolved != root and not str(resolved).startswith(str(root) + os.sep):
        raise ValueError("Path outside /maje/ is not allowed.")
    return resolved


async def read_file(path: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Read a text file from /maje/ (e.g. a file the user uploaded to files/)."""
    try:
        target = _safe_path(path)
    except ValueError as e:
        return f"ERROR: {e}"
    if not target.exists() or not target.is_file():
        return f"ERROR: File not found: {path}"
    raw = target.read_bytes()
    if b"\x00" in raw[:1024]:
        return f"ERROR: '{path}' is a binary file ({len(raw)} bytes) and cannot be read as text."
    text = raw[:MAX_READ_BYTES].decode("utf-8", errors="replace")
    if len(raw) > MAX_READ_BYTES:
        text += f"\n\n… (truncated, {len(raw)} bytes total)"
    return f"Contents of {path}:\n{text}"


async def write_file(path: str, content: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Write text content to a file inside /maje/."""
    try:
        target = _safe_path(path)
    except ValueError as e:
        return f"ERROR: {e}"
    target.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(target.parent, 0o777)
    except Exception:
        pass
    target.write_text(content, encoding="utf-8")
    return f"✅ File written: {target} ({len(content)} bytes)"
