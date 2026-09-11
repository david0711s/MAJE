# config/__init__.py
# Macht das config-Verzeichnis zu einem Python-Paket
import os
import shutil

_dir = os.path.dirname(__file__)
_api_keys = os.path.join(_dir, "api_keys.py")
_example = os.path.join(_dir, "api_keys.example.py")

if not os.path.exists(_api_keys) and os.path.exists(_example):
    try:
        shutil.copyfile(_example, _api_keys)
    except Exception:
        pass

try:
    from .api_keys import API_PROVIDERS, EXTERNAL_SERVICES, COST_SETTINGS, INTERNAL
except ImportError:
    from .api_keys_example import API_PROVIDERS, EXTERNAL_SERVICES, COST_SETTINGS, INTERNAL

__all__ = ["API_PROVIDERS", "EXTERNAL_SERVICES", "COST_SETTINGS", "INTERNAL"]

