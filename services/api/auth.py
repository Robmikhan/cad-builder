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
_PUBLIC_PATHS = {"/health", "/api/health", "/docs", "/openapi.json", "/redoc", "/api/trial", "/api/tiers"}


def _get_valid_keys() -> set[str]:
    raw = os.getenv("CAD_AGENT_API_KEYS", "").strip()
    if not raw:
        return set()
    return {k.strip() for k in raw.split(",") if k.strip()}


def _has_managed_keys() -> bool:
    """Check if any managed keys exist in api_keys.json."""
    from pathlib import Path
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    keys_file = Path(data_dir) / "api_keys.json"
    if keys_file.exists():
        try:
            import json
            keys = json.loads(keys_file.read_text(encoding="utf-8"))
            return len(keys) > 0
        except Exception:
            pass
    return False


def _is_valid_managed_key(api_key: str) -> bool:
    """Check if an API key exists in api_keys.json."""
    from pathlib import Path
    import json
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    keys_file = Path(data_dir) / "api_keys.json"
    if keys_file.exists():
        try:
            keys = json.loads(keys_file.read_text(encoding="utf-8"))
            return api_key in keys
        except Exception:
            pass
    return False


class ApiKeyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        env_keys = _get_valid_keys()
        has_managed = _has_managed_keys()

        # If no keys configured anywhere, auth is disabled (local dev mode)
        if not env_keys and not has_managed:
            return await call_next(request)

        # Skip auth for public paths and OPTIONS
        if request.url.path in _PUBLIC_PATHS or request.method == "OPTIONS":
            return await call_next(request)

        # Skip auth for non-API paths (frontend)
        if not request.url.path.startswith("/api/"):
            return await call_next(request)

        # Check X-API-Key header against both env keys and managed keys
        api_key = request.headers.get("x-api-key", "")
        if api_key in env_keys or _is_valid_managed_key(api_key):
            return await call_next(request)

        raise HTTPException(status_code=401, detail="Invalid or missing API key")
