"""MAJE – Files Routes (serves the /maje/ tree, upload, view & download)"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import FileResponse

router = APIRouter()
MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
ALLOWED_DIRS = {"scripts", "tools", "skills", "files", "soul", "workspace"}
MAX_VIEW_BYTES = 512 * 1024  # 512 KB preview limit


def _safe_path(rel_path: str) -> Path:
    """Resolve a path and ensure it stays inside MAJE_ROOT."""
    root = Path(MAJE_ROOT).resolve()
    resolved = (root / rel_path).resolve()
    if resolved != root and not str(resolved).startswith(str(root) + os.sep):
        raise HTTPException(403, "Access denied: path outside /maje/")
    return resolved


def _sanitize_filename(name: str) -> str:
    name = Path(name).name  # strip any directories
    cleaned = "".join(c for c in name if c.isalnum() or c in "._- ()[]").strip()
    return cleaned or "upload.bin"


def _build_tree(root: Path, max_depth: int = 3, depth: int = 0) -> list[dict]:
    """Recursively build a file tree with metadata."""
    if depth > max_depth or not root.exists():
        return []
    result = []
    for p in sorted(root.iterdir()):
        if p.name.startswith("."):
            continue
        if p.suffix == ".json" and p.stem.endswith(".meta"):
            continue
        entry: dict = {
            "name": p.name,
            "path": str(p.relative_to(MAJE_ROOT)).replace("\\", "/"),
            "type": "directory" if p.is_dir() else "file",
            "is_dir": p.is_dir(),
            "size": p.stat().st_size if p.is_file() else None,
            "modified": p.stat().st_mtime,
        }
        meta_path = p.parent / f"{p.name}.meta.json"
        if meta_path.exists():
            try:
                entry["meta"] = json.loads(meta_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        if p.is_dir():
            entry["children"] = _build_tree(p, max_depth, depth + 1)
        result.append(entry)
    return result


def _tree_response(root: Path):
    if not root.exists():
        return {"tree": []}
    return {"tree": _build_tree(root)}


@router.get("")
@router.get("/")
async def get_file_tree():
    """Return the complete /maje/ directory tree with metadata."""
    return _tree_response(Path(MAJE_ROOT))


@router.get("/tree")
async def get_tree():
    return _tree_response(Path(MAJE_ROOT))


@router.get("/tree/{directory}")
async def get_directory_tree(directory: str):
    if directory not in ALLOWED_DIRS:
        raise HTTPException(400, f"Invalid directory. Allowed: {sorted(ALLOWED_DIRS)}")
    return {"directory": directory, "entries": _build_tree(Path(MAJE_ROOT) / directory, max_depth=2)}


@router.get("/view")
async def view_file(path: str):
    """Return the (text) content of a file for in-app preview."""
    resolved = _safe_path(path)
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(404, "File not found")
    raw = resolved.read_bytes()
    is_binary = b"\x00" in raw[:1024]
    content = "(Binärdatei – keine Vorschau verfügbar)"
    if not is_binary:
        content = raw[:MAX_VIEW_BYTES].decode("utf-8", errors="replace")
        if len(raw) > MAX_VIEW_BYTES:
            content += f"\n\n… (gekürzt, {len(raw)} Bytes gesamt)"
    return {"path": path, "name": resolved.name, "size": resolved.stat().st_size, "content": content}


@router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    subdir: str = Form("files"),
    task_id: Optional[str] = Form(None),
):
    """Upload a file (from the app) into a /maje/ subdirectory."""
    target_dir_name = subdir if subdir in ALLOWED_DIRS else "files"
    target_dir = Path(MAJE_ROOT) / target_dir_name / (task_id or "")
    target_dir.mkdir(parents=True, exist_ok=True)
    try:
        os.chmod(target_dir, 0o777)
    except Exception:
        pass

    dest = target_dir / _sanitize_filename(file.filename or "upload.bin")
    data = await file.read()
    dest.write_bytes(data)

    rel = str(dest.relative_to(MAJE_ROOT)).replace("\\", "/")
    return {"uploaded": True, "name": dest.name, "path": rel, "size": len(data)}


@router.delete("/file")
async def delete_file(path: str):
    resolved = _safe_path(path)
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(404, "File not found")
    resolved.unlink()
    meta = resolved.parent / f"{resolved.name}.meta.json"
    if meta.exists():
        meta.unlink()
    return {"deleted": True, "path": path}


@router.get("/download/{path:path}")
async def download_file(path: str):
    """Download a specific file from /maje/."""
    resolved = _safe_path(path)
    if not resolved.exists() or not resolved.is_file():
        raise HTTPException(404, "File not found")
    return FileResponse(str(resolved), filename=resolved.name)
