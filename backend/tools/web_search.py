"""
MAJE Tool – Web Search (Tavily) + File Download
"""
from __future__ import annotations

import os
import httpx
from pathlib import Path
from typing import Optional

from loguru import logger

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
FILES_DIR = Path(MAJE_ROOT) / "files"


async def search_web(query: str, max_results: int = 5, task_id: Optional[str] = None, **kwargs) -> str:
    """Search the web using Tavily API."""
    import sys
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
    from config.api_keys import EXTERNAL_SERVICES

    tavily_cfg = EXTERNAL_SERVICES.get("tavily", {})
    keys = [k for k in tavily_cfg.get("keys", []) if k and not k.startswith("DEIN_")]

    if not keys:
        return "ERROR: No Tavily API key configured. Add it to config/api_keys.py under EXTERNAL_SERVICES['tavily']"

    try:
        from tavily import TavilyClient
        client = TavilyClient(api_key=keys[0])
        response = client.search(query=query, max_results=max_results)
        results = response.get("results", [])
        if not results:
            return "No results found."
        output = f"Search results for: {query}\n\n"
        for i, r in enumerate(results, 1):
            output += f"{i}. {r.get('title', 'No title')}\n"
            output += f"   URL: {r.get('url', '')}\n"
            output += f"   {r.get('content', '')[:300]}\n\n"
        return output
    except Exception as e:
        return f"Search error: {e}"


async def download_file(url: str, filename: Optional[str] = None, task_id: Optional[str] = None, **kwargs) -> str:
    """Download a file from a URL to /maje/files/."""
    FILES_DIR.mkdir(parents=True, exist_ok=True)

    if not filename:
        filename = url.split("/")[-1].split("?")[0] or "downloaded_file"

    dest = FILES_DIR / filename

    try:
        async with httpx.AsyncClient(timeout=60, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            dest.write_bytes(response.content)
        return f"File downloaded to /maje/files/{filename} ({len(response.content)} bytes)"
    except Exception as e:
        return f"Download error: {e}"
