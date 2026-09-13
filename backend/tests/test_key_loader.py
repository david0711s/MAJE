"""
MAJE – API-Key Loader Tests (plaintext + optional encryption)
"""
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from config import key_loader


def test_roundtrip_plaintext(tmp_path, monkeypatch):
    keys_file = tmp_path / "keys.json"
    monkeypatch.setenv("MAJE_KEYS_FILE", str(keys_file))
    monkeypatch.delenv("MAJE_KEYS_KEY", raising=False)
    # Make sure no env keys leak into the result
    for env in key_loader.ENV_MAP.values():
        monkeypatch.delenv(env, raising=False)

    key_loader.save_keys({"gemini": ["k1", "k2"], "groq": ["g1"]})

    assert keys_file.exists()
    # Plaintext file must be readable JSON
    on_disk = json.loads(keys_file.read_text(encoding="utf-8"))
    assert on_disk["gemini"] == ["k1", "k2"]

    loaded = key_loader.load_keys()
    assert loaded["gemini"] == ["k1", "k2"]
    assert loaded["groq"] == ["g1"]


def test_placeholder_keys_are_ignored(tmp_path, monkeypatch):
    keys_file = tmp_path / "keys.json"
    monkeypatch.setenv("MAJE_KEYS_FILE", str(keys_file))
    monkeypatch.delenv("MAJE_KEYS_KEY", raising=False)

    key_loader.save_keys({"gemini": ["DEIN_GEMINI_API_KEY_HIER", "real-key"]})
    loaded = key_loader.load_keys()
    assert loaded["gemini"] == ["real-key"]


def test_detect_provider():
    assert key_loader.detect_provider("gsk_abc123") == "groq"
    assert key_loader.detect_provider("AIzaSyABCDEF") == "gemini"
    assert key_loader.detect_provider("tvly-dev-abc") == "tavily"
    assert key_loader.detect_provider("sk-ant-xyz") == "anthropic"
    assert key_loader.detect_provider("voellig-unbekannt") is None


def test_mask():
    assert set(key_loader.mask("AIzaSyABCDEFGH1234")) == {"•"}
    assert key_loader.mask("short") == "•" * 12
    assert key_loader.mask("") == ""
