"""
MAJE – Docker Sandbox Manager
Runs code/commands in hardened, throwaway containers with strict resource limits.

Key fixes vs. the previous version:
  * ``timeout`` was passed to ``containers.run`` (invalid kwarg -> every call failed).
    Now we create + start detached, wait with a timeout and kill on overrun.
  * Containers are hardened: non-root user, all capabilities dropped,
    no-new-privileges, pids limit, read-only rootfs (writable /tmp), mem-swap = mem.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Optional

import docker
from docker.errors import DockerException, ImageNotFound
from loguru import logger

from .sandbox_config import SANDBOX_CONFIG, get_limits

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
SANDBOX_UID = os.getenv("SANDBOX_UID", "1000")


class SandboxManager:
    def __init__(self):
        try:
            self._docker = docker.from_env()
        except DockerException as e:  # pragma: no cover - depends on environment
            logger.warning(f"Docker not available: {e}. Code execution will be disabled.")
            self._docker = None

    def is_available(self) -> bool:
        return self._docker is not None

    async def run_code(
        self,
        code: str,
        language: str = "python",
        task_id: Optional[str] = None,
        timeout: Optional[int] = None,
        task: Optional[str] = None,  # alias used by some callers
        writable_rootfs: bool = False,
        image: Optional[str] = None,
    ) -> dict:
        """Execute code in an isolated, hardened Docker container.

        Returns: {"stdout": str, "stderr": str, "exit_code": int, "output_path": str}
        """
        if not self.is_available():
            return {"stdout": "", "stderr": "Docker not available on this system.", "exit_code": -1, "output_path": None}

        lang_config = SANDBOX_CONFIG["languages"].get((language or "python").lower())
        if not lang_config:
            return {"stdout": "", "stderr": f"Unsupported language: {language}", "exit_code": -1, "output_path": None}

        limits = get_limits()
        eff_timeout = int(timeout or limits["timeout_seconds"])

        # Write code to a per-task workspace file (bind-mounted into the container)
        suffix = lang_config["extension"]
        script_name = f"script_{uuid.uuid4().hex[:8]}{suffix}"
        workspace = Path(MAJE_ROOT) / "workspace" / (task_id or task or "tmp")
        workspace.mkdir(parents=True, exist_ok=True)
        try:
            os.chmod(workspace, 0o777)
        except Exception:
            pass
        script_path = workspace / script_name
        script_path.write_text(code, encoding="utf-8")
        try:
            os.chmod(script_path, 0o644)
        except Exception:
            pass

        logger.info(f"Running {language} script in sandbox: {script_name} (timeout {eff_timeout}s)")

        try:
            return await asyncio.to_thread(
                self._run_container,
                lang_config=lang_config,
                script_path=str(script_path),
                workspace=str(workspace),
                timeout=eff_timeout,
                network_disabled=lang_config.get("network_disabled", True),
                writable_rootfs=writable_rootfs,
                image_override=image,
            )
        except Exception as e:  # noqa: BLE001 - surface any docker error to the agent
            logger.error(f"Sandbox error: {e}")
            return {"stdout": "", "stderr": str(e), "exit_code": -1, "output_path": str(workspace)}
    def _ensure_image(self, image: str):
        try:
            self._docker.images.get(image)
        except ImageNotFound:
            logger.info(f"Pulling sandbox image: {image}")
            self._docker.images.pull(image)

    def _run_container(
        self,
        lang_config: dict,
        script_path: str,
        workspace: str,
        timeout: int,
        network_disabled: bool,
        writable_rootfs: bool = False,
        image_override: Optional[str] = None,
    ) -> dict:
        """Synchronous docker create+start+wait (called via asyncio.to_thread)."""
        limits = get_limits()
        image = image_override or lang_config["image"]
        self._ensure_image(image)

        cmd = lang_config["run_cmd"].format(script=f"/workspace/{Path(script_path).name}")

        container = self._docker.containers.create(
            image=image,
            command=cmd,
            volumes={workspace: {"bind": "/workspace", "mode": "rw"}},
            working_dir="/workspace",
            environment={"HOME": "/tmp", "PIP_CACHE_DIR": "/tmp/.pip", "TMPDIR": "/tmp"},
            # ── Resource limits ────────────────────────────────────────────
            mem_limit=f"{limits['memory_mb']}m",
            memswap_limit=f"{limits['memory_mb']}m",  # == mem -> swap effectively disabled
            nano_cpus=int(limits["cpu_quota"] * 1e9),
            pids_limit=256,                            # fork-bomb protection
            # ── Isolation / hardening ──────────────────────────────────────
            network_disabled=network_disabled,
            user=f"{SANDBOX_UID}:{SANDBOX_UID}",
            cap_drop=["ALL"],
            security_opt=["no-new-privileges:true"],
            read_only=not writable_rootfs,
            tmpfs={"/tmp": "rw,size=128m,noexec"},
            init=True,
            detach=True,
            labels={"maje.sandbox": "true"},
        )

        try:
            container.start()
            try:
                wait_result = container.wait(timeout=timeout)
                exit_code = int(wait_result.get("StatusCode", -1))
            except Exception:
                # Wait timed out -> container still running -> kill it.
                logger.warning(f"Sandbox timeout ({timeout}s) reached – killing container.")
                try:
                    container.kill()
                except Exception:
                    pass
                try:
                    container.wait(timeout=5)
                except Exception:
                    pass
                return {
                    "stdout": "",
                    "stderr": f"Timeout: execution exceeded {timeout}s and was killed.",
                    "exit_code": 124,
                    "output_path": workspace,
                }

            logs = container.logs(stdout=True, stderr=True)
            output = logs.decode("utf-8", errors="replace") if isinstance(logs, bytes) else str(logs)
            return {"stdout": output, "stderr": "", "exit_code": exit_code, "output_path": workspace}
        finally:
            try:
                container.remove(force=True)
            except Exception:
                pass

    async def run_shell(
        self,
        command: str,
        task_id: Optional[str] = None,
        timeout: int = 30,
        writable_rootfs: bool = False,
    ) -> dict:
        """Run an arbitrary shell command in the sandbox."""
        return await self.run_code(
            code=command,
            language="shell",
            task_id=task_id,
            timeout=timeout,
            writable_rootfs=writable_rootfs,
        )

    async def run_pentest(
        self,
        command: str,
        task_id: Optional[str] = None,
        timeout: int = 300,
    ) -> dict:
        """Run a network command in the network-enabled pentest sandbox."""
        return await self.run_code(
            code=command,
            language="pentest",
            task_id=task_id,
            timeout=timeout,
        )


# Singleton
sandbox_manager = SandboxManager()

