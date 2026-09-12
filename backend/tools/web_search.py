"""
MAJE Tool – Web Search + File Download
Supports multiple providers (Tavily → Serper → Brave). Keys may be set in
config/api_keys.py (EXTERNAL_SERVICES) or via environment variables.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

import httpx
from loguru import logger

MAJE_ROOT = os.getenv("MAJE_ROOT", "/maje")
FILES_DIR = Path(MAJE_ROOT) / "files"


def _first_key(name: str) -> Optional[str]:
    """Look up the first usable key for an external service (config → env)."""
    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
        from config.api_keys import EXTERNAL_SERVICES
        cfg = EXTERNAL_SERVICES.get(name, {})
        keys = [k for k in cfg.get("keys", []) if k and not str(k).startswith("DEIN_")]
        if keys:
            return keys[0]
    except Exception:
        pass
    env_map = {"tavily": "TAVILY_API_KEY", "serper": "SERPER_API_KEY", "brave_search": "BRAVE_API_KEY"}
    env_name = env_map.get(name)
    return os.getenv(env_name) if env_name else None


def _format(query: str, results: list[dict]) -> str:
    if not results:
        return "No results found."
    output = f"Search results for: {query}\n\n"
    for i, r in enumerate(results, 1):
        output += f"{i}. {r.get('title', 'No title')}\n   URL: {r.get('url', '')}\n   {r.get('snippet', '')[:300]}\n\n"
    return output


async def _search_tavily(query: str, max_results: int) -> Optional[str]:
    key = _first_key("tavily")
    if not key:
        return None
    from tavily import TavilyClient
    client = TavilyClient(api_key=key)
    response = client.search(query=query, max_results=max_results)
    results = [
        {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("content", "")}
        for r in response.get("results", [])
    ]
    return _format(query, results)


async def _search_serper(query: str, max_results: int) -> Optional[str]:
    key = _first_key("serper")
    if not key:
        return None
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.post(
            "https://google.serper.dev/search",
            headers={"X-API-KEY": key, "Content-Type": "application/json"},
            json={"q": query, "num": max_results},
        )
        resp.raise_for_status()
        data = resp.json()
    results = [
        {"title": r.get("title"), "url": r.get("link"), "snippet": r.get("snippet", "")}
        for r in data.get("organic", [])[:max_results]
    ]
    return _format(query, results)


async def _search_brave(query: str, max_results: int) -> Optional[str]:
    key = _first_key("brave_search")
    if not key:
        return None
    async with httpx.AsyncClient(timeout=30) as client:
        resp = await client.get(
            "https://api.search.brave.com/res/v1/web/search",
            headers={"X-Subscription-Token": key, "Accept": "application/json"},
            params={"q": query, "count": max_results},
        )
        resp.raise_for_status()
        data = resp.json()
    results = [
        {"title": r.get("title"), "url": r.get("url"), "snippet": r.get("description", "")}
        for r in data.get("web", {}).get("results", [])[:max_results]
    ]
    return _format(query, results)


async def search_web(query: str, max_results: int = 5, task_id: Optional[str] = None, **kwargs) -> str:
    """Search the web using the first configured provider (Tavily → Serper → Brave)."""
    errors = []
    for provider in (_search_tavily, _search_serper, _search_brave):
        try:
            result = await provider(query, max_results)
            if result is not None:
                return result
        except Exception as e:  # try the next provider
            errors.append(f"{provider.__name__}: {e}")

    if errors:
        return "Search error:\n" + "\n".join(errors)
    return ("ERROR: No search provider configured. Add a Tavily, Serper or Brave key to "
            "config/api_keys.py (EXTERNAL_SERVICES) or set TAVILY_API_KEY.")


async def download_file(url: str, filename: Optional[str] = None, task_id: Optional[str] = None, **kwargs) -> str:
    """Download a file from a URL to /maje/files/."""
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    if not filename:
        filename = url.split("/")[-1].split("?")[0] or "downloaded_file"
    filename = "".join(c for c in filename if c.isalnum() or c in "._- ()[]") or "downloaded_file"
    dest = FILES_DIR / filename

    try:
        async with httpx.AsyncClient(timeout=120, follow_redirects=True) as client:
            response = await client.get(url)
            response.raise_for_status()
            dest.write_bytes(response.content)
        return f"File downloaded to /maje/files/{filename} ({len(response.content)} bytes)"
    except Exception as e:
        return f"Download error: {e}"
