"""
MAJE – API-Key Loader
Zentrale, skalierbare Key-Verwaltung. Keys werden zusammengeführt aus:

  1. config/keys.json   (übersichtlich, beliebig viele Keys pro Provider)
     -> optional verschlüsselt (Fernet), aktiv nur wenn MAJE_KEYS_KEY gesetzt ist
  2. Umgebungsvariablen  (.env): GEMINI_API_KEY, GROQ_API_KEY, TAVILY_API_KEY, ...
  3. den Standard-Werten in config/api_keys.py (Fallback)

Die Datei ist gitignored und wird mit chmod 600 abgelegt.
"""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
from typing import Optional

# Provider-ID  ->  Umgebungsvariable (jeweils EIN Key pro Variable)
ENV_MAP: dict[str, str] = {
    "gemini": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "mistral": "MISTRAL_API_KEY",
    "together": "TOGETHER_API_KEY",
    "tavily": "TAVILY_API_KEY",
    "serper": "SERPER_API_KEY",
    "brave_search": "BRAVE_API_KEY",
    "firecrawl": "FIRECRAWL_API_KEY",
}

# Provider, die in keys.json erlaubt sind (LLM-Provider + externe Dienste)
PROVIDER_LABELS: dict[str, str] = {
    "gemini": "Google Gemini (kostenlos)",
    "groq": "Groq (kostenlos, auch Whisper-Sprache)",
    "deepseek": "DeepSeek (kostenpflichtig)",
    "openai": "OpenAI (kostenpflichtig)",
    "anthropic": "Anthropic Claude (kostenpflichtig)",
    "mistral": "Mistral (kostenpflichtig)",
    "together": "Together AI (kostenpflichtig)",
    "tavily": "Tavily Web-Suche",
    "serper": "Serper Web-Suche",
    "brave_search": "Brave Web-Suche",
    "firecrawl": "Firecrawl Scraping",
}


def keys_file_path() -> Path:
    """Where keys.json lives.

    Priority:
      1. MAJE_KEYS_FILE (expliziter Pfad)
      2. <MAJE_ROOT>/keys/keys.json  (Container: persistentes Volume, UID 1000 -> beschreibbar)
      3. config/keys.json            (lokale Entwicklung)
    """
    override = os.getenv("MAJE_KEYS_FILE")
    if override:
        return Path(override)
    maje_root = os.getenv("MAJE_ROOT")
    if maje_root:
        return Path(maje_root) / "keys" / "keys.json"
    return Path("config/keys.json")


def _placeholder(key: str) -> bool:
    return (not key) or str(key).startswith("DEIN_")


def _fernet():
    """Return a Fernet instance if MAJE_KEYS_KEY is set, else None."""
    raw = os.getenv("MAJE_KEYS_KEY")
    if not raw:
        return None
    try:
        from cryptography.fernet import Fernet
        key = raw.encode() if isinstance(raw, str) else raw
        return Fernet(key)
    except Exception:
        return None


def encryption_enabled() -> bool:
    return _fernet() is not None


def generate_key() -> str:
    """Generate a new Fernet key (to put into MAJE_KEYS_KEY)."""
    from cryptography.fernet import Fernet
    return Fernet.generate_key().decode()


# ── Load / Save ───────────────────────────────────────────────────────────────

def load_keys(include_env: bool = True) -> dict[str, list[str]]:
    """Load keys from keys.json (optionally encrypted) and, if desired, env variables."""
    data: dict[str, list[str]] = {}

    path = keys_file_path()
    if path.exists():
        try:
            raw = path.read_bytes()
            fnet = _fernet()
            if fnet:
                try:
                    raw = fnet.decrypt(raw)
                except Exception:
                    pass  # file might be plaintext
            parsed = json.loads(raw.decode("utf-8"))
            if isinstance(parsed, dict):
                for pid, keys in parsed.items():
                    if isinstance(keys, str):
                        keys = [keys]
                    data[pid] = [k for k in (keys or []) if not _placeholder(k)]
        except Exception:
            pass

    if include_env:
        for pid, env_name in ENV_MAP.items():
            val = os.getenv(env_name)
            if val and not _placeholder(val):
                data.setdefault(pid, [])
                if val not in data[pid]:
                    data[pid].append(val)

    return data


def save_keys(data: dict[str, list[str]], encrypt: Optional[bool] = None) -> None:
    """Persist keys to keys.json (encrypted if a key is configured and encrypt != False)."""
    cleaned = {
        pid: [k for k in (keys or []) if not _placeholder(k)]
        for pid, keys in data.items()
    }
    cleaned = {pid: keys for pid, keys in cleaned.items() if keys}

    path = keys_file_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = json.dumps(cleaned, indent=2, ensure_ascii=False).encode("utf-8")

    fnet = _fernet()
    use_enc = fnet is not None and (encrypt is None or encrypt)
    path.write_bytes(fnet.encrypt(payload) if use_enc else payload)

    try:
        os.chmod(path, 0o600)
    except Exception:
        pass


# ── Apply to the running config ───────────────────────────────────────────────

def apply_keys(providers: list[dict], external: dict, keys: dict[str, list[str]]) -> None:
    """Mutate the in-memory provider configs with the loaded keys (hot-reload)."""
    for p in providers:
        pid = p.get("provider_id")
        if pid in keys and keys[pid]:
            p["keys"] = list(keys[pid])
    for name, cfg in external.items():
        if name in keys and keys[name]:
            cfg["keys"] = list(keys[name])
            cfg["enabled"] = True


def collect_current(providers: list[dict], external: dict) -> dict[str, list[str]]:
    """Return currently configured (non-placeholder) keys per provider."""
    result: dict[str, list[str]] = {}
    for p in providers:
        keys = [k for k in p.get("keys", []) if not _placeholder(k)]
        if keys:
            result[p["provider_id"]] = keys
    for name, cfg in external.items():
        keys = [k for k in cfg.get("keys", []) if not _placeholder(k)]
        if keys:
            result[name] = keys
    return result


# Präfix -> Provider-ID (für die Ein-Feld-Eingabe "Key einfügen")
_PREFIX_MAP: list[tuple[str, str]] = [
    ("AIza", "gemini"),
    ("gsk_", "groq"),
    ("tvly-", "tavily"),
    ("sk-ant-", "anthropic"),
    ("sk-or-", "openai"),
    ("sk-", "openai"),
]


def detect_provider(key: str) -> Optional[str]:
    """Erkennt den Anbieter am Key-Präfix (None = unbekannt)."""
    k = (key or "").strip()
    for prefix, pid in _PREFIX_MAP:
        if k.startswith(prefix):
            return pid
    return None


def mask(key: str) -> str:
    """Vollständig maskiert – der Key ist für das Auge nicht erkennbar."""
    return "•" * 12 if key else ""
