"""
MAJE – Docker Sandbox Manager
Runs code/commands in isolated containers with strict resource limits.
"""
from __future__ import annotations

import os
import asyncio
import tempfile
import uuid
from pathlib import Path
from typing import Optional

import docker
from docker.errors import DockerException
from loguru import logger

from .sandbox_config import SANDBOX_CONFIG

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")


class SandboxManager:
    def __init__(self):
        try:
            self._docker = docker.from_env()
        except DockerException as e:
            logger.warning(f"Docker not available: {e}. Code execution will be disabled.")
            self._docker = None

    def is_available(self) -> bool:
        return self._docker is not None

    async def run_code(
        self,
        code: str,
        language: str = "python",
        task_id: Optional[str] = None,
        timeout: int = 60,
    ) -> dict:
        """
        Execute code in an isolated Docker container.
        Returns: {"stdout": str, "stderr": str, "exit_code": int, "output_path": str}
        """
        if not self.is_available():
            return {"stdout": "", "stderr": "Docker not available on this system.", "exit_code": -1, "output_path": None}

        # Determine image and run command
        lang_config = SANDBOX_CONFIG["languages"].get(language.lower())
        if not lang_config:
            return {"stdout": "", "stderr": f"Unsupported language: {language}", "exit_code": -1, "output_path": None}

        # Write code to temp file
        suffix = lang_config["extension"]
        script_name = f"script_{uuid.uuid4().hex[:8]}{suffix}"
        workspace = Path(MAJE_ROOT) / "workspace" / (task_id or "tmp")
        workspace.mkdir(parents=True, exist_ok=True)
        script_path = workspace / script_name
        script_path.write_text(code, encoding="utf-8")

        logger.info(f"Running {language} script in sandbox: {script_name}")

        try:
            result = await asyncio.to_thread(
                self._run_container,
                lang_config=lang_config,
                script_path=str(script_path),
                workspace=str(workspace),
                timeout=timeout,
            )
            return result
        except Exception as e:
            logger.error(f"Sandbox error: {e}")
            return {"stdout": "", "stderr": str(e), "exit_code": -1, "output_path": None}

    def _run_container(self, lang_config: dict, script_path: str, workspace: str, timeout: int) -> dict:
        """Synchronous Docker run (called via asyncio.to_thread)."""
        image = lang_config["image"]
        cmd = lang_config["run_cmd"].format(script=f"/workspace/{Path(script_path).name}")

        cfg = SANDBOX_CONFIG["limits"]
        try:
            container = self._docker.containers.run(
                image=image,
                command=cmd,
                volumes={workspace: {"bind": "/workspace", "mode": "rw"}},
                mem_limit=cfg["memory"],
                nano_cpus=int(cfg["cpu_quota"] * 1e9),
                network_disabled=cfg["network_disabled"],
                read_only=False,
                remove=True,
                detach=False,
                stdout=True,
                stderr=True,
                timeout=timeout,
            )
            output = container.decode("utf-8") if isinstance(container, bytes) else str(container)
            return {"stdout": output, "stderr": "", "exit_code": 0, "output_path": workspace}
        except docker.errors.ContainerError as e:
            return {
                "stdout": e.stdout.decode("utf-8") if e.stdout else "",
                "stderr": e.stderr.decode("utf-8") if e.stderr else str(e),
                "exit_code": e.exit_status,
                "output_path": workspace,
            }

    async def run_shell(self, command: str, task_id: Optional[str] = None, timeout: int = 30) -> dict:
        """Run an arbitrary shell command in the sandbox."""
        return await self.run_code(
            code=command,
            language="shell",
            task_id=task_id,
            timeout=timeout,
        )


# Singleton
sandbox_manager = SandboxManager()
