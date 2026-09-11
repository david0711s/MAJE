"""
MAJE – Tool Registry
All agent tools are registered here. The agent loop uses TOOL_REGISTRY.
"""
from __future__ import annotations

from tools.code_executor import write_and_run_script, run_shell_cmd
from tools.package_manager import pip_install, apt_install
from tools.web_search import search_web, download_file
from tools.file_manager import save_module, deliver_file, list_files
from tools.memory_tools import save_memory, update_soul
from tools.ui_tools import create_ui_element, remove_ui_element, reorder_ui
from tools.pentesting import run_nmap, run_gobuster, run_sqlmap

TOOL_REGISTRY: dict[str, dict] = {
    # Code execution
    "write_and_run_script": {
        "fn": write_and_run_script,
        "description": "Write and execute code. Args: code (str), language (str: python/javascript/bash/ruby)",
    },
    "run_shell": {
        "fn": run_shell_cmd,
        "description": "Run a shell command in the sandbox. Args: command (str)",
    },

    # Package management
    "pip_install": {
        "fn": pip_install,
        "description": "Install a Python package. Args: package (str)",
    },
    "apt_install": {
        "fn": apt_install,
        "description": "Install a system package via apt. Args: package (str)",
    },

    # Web & files
    "search_web": {
        "fn": search_web,
        "description": "Search the web. Args: query (str)",
    },
    "download_file": {
        "fn": download_file,
        "description": "Download a file from a URL. Args: url (str), filename (str, optional)",
    },

    # File management
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
        "description": "List files in a /maje/ subdirectory. Args: directory (str: scripts/tools/skills/files/workspace)",
    },

    # Memory & soul
    "save_memory": {
        "fn": save_memory,
        "description": "Save an important long-term memory entry. Args: content (str), tags (str, comma-separated)",
    },
    "update_soul": {
        "fn": update_soul,
        "description": "Update MAJE's self-description (soul.md). Args: text (str)",
    },

    # UI customization (only affects the 'Für MAJE' screen)
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

    # Pentesting (whitelist-gated)
    "nmap": {
        "fn": run_nmap,
        "description": "Run nmap scan. Args: target (str), flags (str, optional). Only against whitelisted targets.",
    },
    "gobuster": {
        "fn": run_gobuster,
        "description": "Run gobuster directory scan. Args: target (str), wordlist (str, optional). Whitelist-gated.",
    },
    "sqlmap": {
        "fn": run_sqlmap,
        "description": "Run sqlmap SQL injection test. Args: target (str), flags (str, optional). Whitelist-gated.",
    },
}
