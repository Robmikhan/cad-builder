"""
API key authentication middleware.
Set CAD_AGENT_API_KEYS as a comma-separated list of valid keys.
If not set, auth is disabled (open access for local dev).
"""
from __future__ import annotations
import os
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

# Paths that don't require auth
_PUBLIC_PATHS = {"/health", "/docs", "/openapi.json", "/redoc"}


def _get_valid_keys() -> set[str]:
    raw = os.getenv("CAD_AGENT_API_KEYS", "").strip()
    if not raw:
        return set()
    return {k.strip() for k in raw.split(",") if k.strip()}


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        valid_keys = _get_valid_keys()

        # If no keys configured, auth is disabled (local dev mode)
        if not valid_keys:
            return await call_next(request)

        # Skip auth for public paths and OPTIONS
        if request.url.path in _PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Check X-API-Key header
        api_key = request.headers.get("x-api-key", "")
        if api_key not in valid_keys:
            raise HTTPException(status_code=401, detail="Invalid or missing API key")

        return await call_next(request)
