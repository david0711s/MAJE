"""MAJE – Files Routes (serves /maje/ directory tree + downloads)"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

router = APIRouter()
MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
ALLOWED_DIRS = {"scripts", "tools", "skills", "files", "soul", "workspace"}


def _build_tree(root: Path, max_depth: int = 3, depth: int = 0) -> list[dict]:
    """Recursively build file tree with metadata."""
    if depth > max_depth or not root.exists():
        return []
    result = []
    for p in sorted(root.iterdir()):
        if p.name.startswith("."):
            continue
        if p.suffix == ".json" and p.stem.endswith(".meta"):
            continue  # Skip meta sidecars from tree
        entry: dict = {
            "name": p.name,
            "path": str(p.relative_to(MAJE_ROOT)),
            "type": "directory" if p.is_dir() else "file",
            "size": p.stat().st_size if p.is_file() else None,
            "modified": p.stat().st_mtime,
        }
        # Attach metadata if sidecar exists
        meta_path = p.parent / f"{p.name}.meta.json"
        if meta_path.exists():
            try:
                entry["meta"] = json.loads(meta_path.read_text())
            except Exception:
                pass
        if p.is_dir():
            entry["children"] = _build_tree(p, max_depth, depth + 1)
        result.append(entry)
    return result


@router.get("/tree")
async def get_file_tree():
    """Return the complete /maje/ directory tree with metadata."""
    root = Path(MAJE_ROOT)
    if not root.exists():
        return {"tree": []}
    return {"tree": _build_tree(root)}


@router.get("/tree/{directory}")
async def get_directory_tree(directory: str):
    """Return tree for a specific /maje/ subdirectory."""
    if directory not in ALLOWED_DIRS:
        raise HTTPException(400, f"Invalid directory. Allowed: {ALLOWED_DIRS}")
    target = Path(MAJE_ROOT) / directory
    return {"directory": directory, "entries": _build_tree(target, max_depth=2)}


@router.get("/download/{path:path}")
async def download_file(path: str):
    """Download a specific file from /maje/."""
    # Security: only allow files within /maje/
    full_path = Path(MAJE_ROOT) / path
    resolved = full_path.resolve()
    maje_resolved = Path(MAJE_ROOT).resolve()

    if not str(resolved).startswith(str(maje_resolved)):
        raise HTTPException(403, "Access denied: path outside /maje/")
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(404, "File not found")

    return FileResponse(str(resolved), filename=resolved.name)
