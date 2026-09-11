"""
MAJE – Sandbox Configuration
Resource limits for Docker containers (tuned for 4GB RAM IONOS server).
"""

SANDBOX_CONFIG = {
    # Resource limits per container
    "limits": {
        "memory": "512m",           # 512 MB per container (room for 2-3 parallel)
        "cpu_quota": 0.5,           # 50% of one CPU core
        "network_disabled": True,   # No network by default (override for web tools)
        "timeout_default": 60,      # Seconds before container killed
    },

    # Supported languages and their Docker images + run commands
    "languages": {
        "python": {
            "image": "python:3.12-slim",
            "extension": ".py",
            "run_cmd": "python {script}",
        },
        "javascript": {
            "image": "node:20-slim",
            "extension": ".js",
            "run_cmd": "node {script}",
        },
        "typescript": {
            "image": "node:20-slim",
            "extension": ".ts",
            "run_cmd": "npx ts-node {script}",
        },
        "bash": {
            "image": "ubuntu:22.04",
            "extension": ".sh",
            "run_cmd": "bash {script}",
        },
        "shell": {
            "image": "ubuntu:22.04",
            "extension": ".sh",
            "run_cmd": "bash -c {script}",
        },
        "ruby": {
            "image": "ruby:3.3-slim",
            "extension": ".rb",
            "run_cmd": "ruby {script}",
        },
    },

    # Pentesting tools (network-enabled containers, whitelist-gated)
    "pentest": {
        "image": "instrumentisto/nmap",   # Only nmap by default; others added as needed
        "network_disabled": False,        # Needs network (whitelist enforced at API level)
        "memory": "256m",
        "cpu_quota": 0.3,
    },
}
