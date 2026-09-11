"""
MAJE Tool – Package Manager (pip + apt in sandbox)
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
TOOLS_DIR = Path(MAJE_ROOT) / "tools"


async def pip_install(package: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Install a Python package in the sandbox's tools directory."""
    from sandbox.docker_manager import sandbox_manager
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    code = f"import subprocess; result = subprocess.run(['pip', 'install', '{package}', '--target', '/workspace/tools'], capture_output=True, text=True); print(result.stdout); print(result.stderr)"
    result = await sandbox_manager.run_code(
        code=code,
        language="python",
        task_id=task_id,
    )
    if result.get("exit_code", -1) == 0:
        return f"✅ Successfully installed {package}"
    return f"❌ Failed to install {package}:\n{result.get('stderr', '')}"


async def apt_install(package: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Install a system package via apt in the sandbox."""
    from sandbox.docker_manager import sandbox_manager
    result = await sandbox_manager.run_shell(
        command=f"apt-get update -qq && apt-get install -y {package}",
        task_id=task_id,
    )
    if result.get("exit_code", -1) == 0:
        return f"✅ Successfully installed {package} via apt"
    return f"❌ Failed to install {package}:\n{result.get('stderr', '')}"
