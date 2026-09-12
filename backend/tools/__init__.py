"""
MAJE – Tool Registry
All agent tools are registered here. The agent loop uses TOOL_REGISTRY.
"""
from __future__ import annotations

from tools.code_executor import run_shell_cmd, write_and_run_script
from tools.package_manager import apt_install, pip_install
from tools.web_search import download_file, search_web
from tools.file_manager import (
    deliver_file,
    list_files,
    save_module,
)
from tools.file_ops import read_file, write_file
from tools.memory_tools import save_memory, update_soul
from tools.ui_tools import create_ui_element, remove_ui_element, reorder_ui
from tools.pentesting import run_gobuster, run_nmap, run_sqlmap

TOOL_REGISTRY: dict[str, dict] = {
    # ── Code execution ────────────────────────────────────────────────────────
    "write_and_run_script": {
        "fn": write_and_run_script,
        "description": "Write and execute code in the sandbox. Args: code (str), language (str: python/javascript/bash/ruby)",
    },
    "run_shell": {
        "fn": run_shell_cmd,
        "description": "Run a shell command in the sandbox. Args: command (str)",
    },

    # ── Package management ────────────────────────────────────────────────────
    "pip_install": {
        "fn": pip_install,
        "description": "Install a Python package into the sandbox. Args: package (str)",
    },
    "apt_install": {
        "fn": apt_install,
        "description": "Install a system package via apt in the sandbox. Args: package (str)",
    },

    # ── Web ───────────────────────────────────────────────────────────────────
    "search_web": {
        "fn": search_web,
        "description": "Search the web. Args: query (str), max_results (int, optional)",
    },
    "download_file": {
        "fn": download_file,
        "description": "Download a file from a URL into /maje/files/. Args: url (str), filename (str, optional)",
    },

    # ── Files ─────────────────────────────────────────────────────────────────
    "read_file": {
        "fn": read_file,
        "description": "Read a file the user shared (in /maje/files/) or any /maje/ file. Args: path (str)",
    },
    "write_file": {
        "fn": write_file,
        "description": "Write text content to a file in /maje/ (e.g. files/report.txt). Args: path (str), content (str)",
    },
    "save_module": {
        "fn": save_module,
        "description": "Save a reusable skill/module permanently. Args: name (str), code (str), description (str)",
    },
    "deliver_file": {
        "fn": deliver_file,
        "description": "Make a file available for the user to download in the app. Args: path (str)",
    },
    "list_files": {
        "fn": list_files,
        "description": "List files in a /maje/ subdirectory. Args: directory (str: scripts/tools/skills/files/workspace/soul)",
    },

    # ── Memory & soul ─────────────────────────────────────────────────────────
    "save_memory": {
        "fn": save_memory,
        "description": "Save an important long-term memory entry. Args: content (str), tags (str, comma-separated)",
    },
    "update_soul": {
        "fn": update_soul,
        "description": "Update MAJE's self-description (soul). Args: text (str)",
    },

    # ── UI customization ('Für MAJE' screen) ──────────────────────────────────
    "create_ui_element": {
        "fn": create_ui_element,
        "description": "Add a button or widget to the 'Für MAJE' custom screen. Args: label (str), action (str), linked_script (str), element_type (str: button/widget)",
    },
    "remove_ui_element": {
        "fn": remove_ui_element,
        "description": "Remove an element from the 'Für MAJE' screen. Args: element_id (str)",
    },
    "reorder_ui": {
        "fn": reorder_ui,
        "description": "Reorder elements on the 'Für MAJE' screen. Args: order (list of element IDs)",
    },

    # ── Pentesting (whitelist-gated, network-enabled sandbox) ────────────────
    "nmap": {
        "fn": run_nmap,
        "description": "Run an nmap scan. Args: target (str), flags (str, optional). Only whitelisted targets.",
    },
    "gobuster": {
        "fn": run_gobuster,
        "description": "Run a gobuster directory scan. Args: target (str), wordlist (str, optional). Whitelist-gated.",
    },
    "sqlmap": {
        "fn": run_sqlmap,
        "description": "Run a sqlmap SQL-injection test. Args: target (str), flags (str, optional). Whitelist-gated.",
    },
}
