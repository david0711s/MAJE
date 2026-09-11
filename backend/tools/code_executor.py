"""
MAJE Tool – Code Executor
write_and_run_script: executes code in Docker sandbox, saves to /maje/scripts/
"""
from __future__ import annotations

import os
import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from sandbox.docker_manager import sandbox_manager

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
SCRIPTS_DIR = Path(MAJE_ROOT) / "scripts"


async def write_and_run_script(
    code: str,
    language: str = "python",
    task_id: Optional[str] = None,
    **kwargs,
) -> str:
    """Write code to /maje/scripts/, execute in sandbox, return output."""
    SCRIPTS_DIR.mkdir(parents=True, exist_ok=True)

    result = await sandbox_manager.run_code(code=code, language=language, task_id=task_id)

    # Save script with metadata
    script_id = uuid.uuid4().hex[:8]
    lang_ext = {"python": ".py", "javascript": ".js", "bash": ".sh", "typescript": ".ts", "ruby": ".rb"}
    ext = lang_ext.get(language.lower(), ".txt")
    date_str = datetime.utcnow().strftime("%Y-%m-%d")
    script_name = f"{date_str}_{script_id}{ext}"
    script_path = SCRIPTS_DIR / script_name

    script_path.write_text(code, encoding="utf-8")

    # Write metadata sidecar
    meta = {
        "script_id": script_id,
        "filename": script_name,
        "language": language,
        "task_id": task_id,
        "created_at": datetime.utcnow().isoformat(),
        "exit_code": result.get("exit_code"),
        "description": f"Script created by MAJE for task {task_id}",
    }
    meta_path = SCRIPTS_DIR / f"{script_name}.meta.json"
    meta_path.write_text(json.dumps(meta, indent=2), encoding="utf-8")

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)

    output = f"Script saved as {script_name}\nExit code: {exit_code}\n"
    if stdout:
        output += f"STDOUT:\n{stdout}\n"
    if stderr:
        output += f"STDERR:\n{stderr}\n"

    return output


async def run_shell_cmd(command: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Run a shell command in the sandbox."""
    result = await sandbox_manager.run_shell(command=command, task_id=task_id)
    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)
    return f"Exit code: {exit_code}\nSTDOUT:\n{stdout}\nSTDERR:\n{stderr}"
