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
    """Install a Python package in the sandbox's tools directory (network enabled)."""
    from sandbox.docker_manager import sandbox_manager
    TOOLS_DIR.mkdir(parents=True, exist_ok=True)

    pkg = "".join(c for c in package if c.isalnum() or c in "._-=<>! ~[]").strip()
    if not pkg:
        return "ERROR: Invalid package name."

    code = (
        "import subprocess; "
        f"result = subprocess.run(['pip', 'install', '{pkg}', '--target', '/workspace/tools'], "
        "capture_output=True, text=True); print(result.stdout); print(result.stderr)"
    )
    result = await sandbox_manager.run_code(
        code=code,
        language="python",
        task_id=task_id,
        network=True,          # installs need internet access
        timeout=300,
    )
    if result.get("exit_code", -1) == 0:
        return f"✅ Successfully installed {package} (into /workspace/tools)"
    return f"❌ Failed to install {package}:\n{result.get('stderr', '')}\n{result.get('stdout', '')[-1500:]}"


async def apt_install(package: str, task_id: Optional[str] = None, **kwargs) -> str:
    """Install a system package via apt in the sandbox (network + writable rootfs)."""
    from sandbox.docker_manager import sandbox_manager

    pkg = "".join(c for c in package if c.isalnum() or c in "._+-").strip()
    if not pkg:
        return "ERROR: Invalid package name."

    result = await sandbox_manager.run_shell(
        command=f"apt-get update -qq && apt-get install -y --no-install-recommends {pkg}",
        task_id=task_id,
        network=True,
        writable_rootfs=True,  # apt must write to /var
        timeout=300,
    )
    if result.get("exit_code", -1) == 0:
        return f"✅ Successfully installed {package} via apt"
    return f"❌ Failed to install {package}:\n{result.get('stderr', '')}\n{result.get('stdout', '')[-1500:]}"
