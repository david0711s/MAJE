"""
MAJE Tool – File Manager (save_module, deliver_file, list_files)
"""
from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Optional

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")


async def save_module(name: str, code: str, description: str = "", task_id: Optional[str] = None, **kwargs) -> str:
    """Save a reusable skill module to /maje/skills/."""
    skills_dir = Path(MAJE_ROOT) / "skills"
    skills_dir.mkdir(parents=True, exist_ok=True)

    # Sanitize name
    safe_name = "".join(c for c in name if c.isalnum() or c in "_-").lower()
    if not safe_name:
        return "ERROR: Invalid module name"

    skill_file = skills_dir / f"{safe_name}.py"
    skill_file.write_text(code, encoding="utf-8")

    meta = {
        "name": name,
        "safe_name": safe_name,
        "description": description,
        "task_id": task_id,
        "created_at": datetime.utcnow().isoformat(),
    }
    meta_file = skills_dir / f"{safe_name}.meta.json"
    meta_file.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return f"✅ Module '{name}' saved to /maje/skills/{safe_name}.py"


async def deliver_file(path: str, task_id: Optional[str] = None, **kwargs) -> str:
    """
    Mark a file as 'delivered' so the user can download it from the app.
    Copies to /maje/files/ if not already there.
    """
    source = Path(path)
    if not source.exists():
        return f"ERROR: File not found: {path}"

    files_dir = Path(MAJE_ROOT) / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    dest = files_dir / source.name

    import shutil
    shutil.copy2(str(source), str(dest))

    meta = {
        "filename": source.name,
        "original_path": str(source),
        "task_id": task_id,
        "delivered_at": datetime.utcnow().isoformat(),
        "size_bytes": dest.stat().st_size,
    }
    meta_path = files_dir / f"{source.name}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    return f"✅ File available for download: /maje/files/{source.name}"


async def list_files(directory: str = "files", task_id: Optional[str] = None, **kwargs) -> str:
    """List files in a /maje/ subdirectory."""
    valid_dirs = {"scripts", "tools", "skills", "files", "workspace", "soul"}
    if directory not in valid_dirs:
        return f"ERROR: Invalid directory. Choose from: {valid_dirs}"

    target = Path(MAJE_ROOT) / directory
    if not target.exists():
        return f"Directory /maje/{directory}/ is empty or doesn't exist yet."

    entries = []
    for p in sorted(target.iterdir()):
        if p.suffix == ".json" and p.stem.endswith(".meta"):
            continue  # Skip meta files from listing
        size = p.stat().st_size if p.is_file() else 0
        entries.append(f"{'📁' if p.is_dir() else '📄'} {p.name} ({size} bytes)")

    if not entries:
        return f"/maje/{directory}/ is empty."

    return f"Contents of /maje/{directory}/:\n" + "\n".join(entries)
