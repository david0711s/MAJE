"""
MAJE – Sandbox Configuration
Resource limits for Docker containers (env-aware, runtime adjustable via the app).
"""
from __future__ import annotations

import os

# ── Defaults (overridable via environment variables) ─────────────────────────
_DEFAULT_MEMORY_MB = int(os.getenv("SANDBOX_MAX_MEMORY_MB", "512"))
_DEFAULT_CPU_QUOTA = float(os.getenv("SANDBOX_CPU_QUOTA", "1.0"))
_DEFAULT_TIMEOUT = int(os.getenv("SANDBOX_TIMEOUT_SECONDS", "60"))

# Runtime-adjustable limits (updated from the app via POST /settings/sandbox)
_runtime_limits: dict[str, float] = {
    "memory_mb": _DEFAULT_MEMORY_MB,
    "cpu_quota": _DEFAULT_CPU_QUOTA,
    "timeout_seconds": _DEFAULT_TIMEOUT,
}


def get_limits() -> dict:
    """Return the currently effective sandbox limits (docker-ready format)."""
    mem_mb = int(_runtime_limits["memory_mb"])
    return {
        "memory_mb": mem_mb,
        "memory": f"{mem_mb}m",
        "cpu_quota": float(_runtime_limits["cpu_quota"]),
        "timeout_seconds": int(_runtime_limits["timeout_seconds"]),
        "network_disabled": True,
    }


def update_limits(memory_mb=None, cpu_quota=None, timeout_seconds=None) -> dict:
    """Update runtime limits, clamped to sane ranges. Returns the new limits."""
    if memory_mb is not None:
        _runtime_limits["memory_mb"] = max(64, min(int(memory_mb), 8192))
    if cpu_quota is not None:
        _runtime_limits["cpu_quota"] = max(0.1, min(float(cpu_quota), 8.0))
    if timeout_seconds is not None:
        _runtime_limits["timeout_seconds"] = max(5, min(int(timeout_seconds), 3600))
    return get_limits()


# Supported languages and their Docker images + run commands
_LANGUAGES: dict[str, dict] = {
    "python": {
        "image": "python:3.12-slim",
        "extension": ".py",
        "run_cmd": "python {script}",
        "network_disabled": True,
    },
    "javascript": {
        "image": "node:20-slim",
        "extension": ".js",
        "run_cmd": "node {script}",
        "network_disabled": True,
    },
    "typescript": {
        "image": "node:20-slim",
        "extension": ".ts",
        "run_cmd": "npx ts-node {script}",
        "network_disabled": True,
    },
    "bash": {
        "image": "ubuntu:22.04",
        "extension": ".sh",
        "run_cmd": "bash {script}",
        "network_disabled": True,
    },
    "shell": {
        "image": "ubuntu:22.04",
        "extension": ".sh",
        "run_cmd": "bash -c {script}",
        "network_disabled": True,
    },
    "ruby": {
        "image": "ruby:3.3-slim",
        "extension": ".rb",
        "run_cmd": "ruby {script}",
        "network_disabled": True,
    },
    # Pentesting runs in a network-enabled nmap image (whitelist-gated at tool level)
    "pentest": {
        "image": "instrumentisto/nmap",
        "extension": ".sh",
        "run_cmd": "bash -c {script}",
        "network_disabled": False,
    },
}


def network_allowed() -> bool:
    """Whether normal (non-pentest) sandbox code may use the network.

    Default: OFF (safer). Set SANDBOX_ALLOW_NETWORK=1 in the .env to let the agent
    install packages / download things from inside the sandbox.
    """
    return os.getenv("SANDBOX_ALLOW_NETWORK", "0").strip().lower() in ("1", "true", "yes", "on")


SANDBOX_CONFIG: dict = {
    "languages": _LANGUAGES,
    # Kept for backwards compatibility – prefer get_limits() at runtime.
    "limits": get_limits(),
}
