"""
MAJE – JWT Auth Middleware
Validates Bearer token on all routes except /health and /docs.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from jose import jwt, JWTError
from loguru import logger

JWT_SECRET = os.getenv("JWT_SECRET", "CHANGE_ME_IN_PRODUCTION_USE_LONG_RANDOM_STRING")
JWT_ALGORITHM = "HS256"

# Routes that don't require auth.
# /settings/token is intentionally public BUT restricted to localhost inside the handler,
# so the very first JWT can be bootstrapped without a chicken-and-egg problem.
PUBLIC_PATHS = {"/health", "/docs", "/redoc", "/openapi.json", "/settings/token"}


class AuthMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # CORS preflight must NEVER require auth – the browser sends OPTIONS first
        # (needed because we send an Authorization header). Blocking it would make
        # every request from the web app fail with "Network Error".
        if request.method == "OPTIONS":
            return await call_next(request)

        # Allow public paths
        if request.url.path in PUBLIC_PATHS or request.url.path.startswith("/docs"):
            return await call_next(request)

        # Allow WebSocket upgrades (auth handled inside WS handler)
        if request.headers.get("upgrade", "").lower() == "websocket":
            return await call_next(request)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return JSONResponse({"detail": "Missing or invalid Authorization header"}, status_code=401)

        token = auth_header.split(" ", 1)[1]
        try:
            payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
            request.state.user = payload
        except JWTError as e:
            return JSONResponse({"detail": f"Invalid token: {e}"}, status_code=401)

        return await call_next(request)


def create_token(user_id: str = "maje_user") -> str:
    """Generate a JWT token (called once during setup)."""
    payload = {"sub": user_id, "type": "access"}
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def verify_ws_token(token: str) -> bool:
    """Verify a token for WebSocket connections."""
    try:
        jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return True
    except JWTError:
        return False
