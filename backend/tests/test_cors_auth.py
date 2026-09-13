"""
MAJE – CORS + Auth Middleware Tests
Stellt sicher, dass die CORS-Vorabanfrage (OPTIONS) NICHT von der Auth-Middleware
blockiert wird – sonst bekommt die Web-App bei jedem Request "Network Error".
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "backend"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.testclient import TestClient

from api.middleware.auth import AuthMiddleware

app = FastAPI()
# Gleiche Reihenfolge wie in main.py: CORS zuerst, Auth danach (= Auth aussen)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
app.add_middleware(AuthMiddleware)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/settings/")
async def settings():
    return {"ok": True}


client = TestClient(app)


def test_cors_preflight_is_not_blocked_by_auth():
    resp = client.options(
        "/settings/",
        headers={
            "Origin": "https://maje-bot.netlify.app",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
    )
    assert resp.status_code in (200, 204), f"Preflight wurde blockiert: {resp.status_code}"
    assert resp.headers.get("access-control-allow-origin") in ("*", "https://maje-bot.netlify.app")


def test_health_is_public():
    resp = client.get("/health", headers={"Origin": "https://maje-bot.netlify.app"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"


def test_normal_request_still_requires_auth(monkeypatch):
    monkeypatch.setenv("AUTH_REQUIRED", "true")
    resp = client.get("/settings/", headers={"Origin": "https://maje-bot.netlify.app"})
    assert resp.status_code == 401
