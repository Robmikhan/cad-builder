"""
Simple in-memory rate limiter middleware.
Limits requests per IP per window. Configurable via env vars.
"""
from __future__ import annotations
import os
import time
from collections import defaultdict
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware

_MAX_REQUESTS = int(os.getenv("CAD_AGENT_RATE_LIMIT", "60"))  # per window
_WINDOW_SEC = int(os.getenv("CAD_AGENT_RATE_WINDOW_SEC", "60"))


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)
        self._hits: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next):
        if _MAX_REQUESTS <= 0:
            return await call_next(request)

        client_ip = request.client.host if request.client else "unknown"
        now = time.time()
        cutoff = now - _WINDOW_SEC

        # Prune old entries
        self._hits[client_ip] = [t for t in self._hits[client_ip] if t > cutoff]

        if len(self._hits[client_ip]) >= _MAX_REQUESTS:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Max {_MAX_REQUESTS} requests per {_WINDOW_SEC}s.",
            )

        self._hits[client_ip].append(now)
        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(_MAX_REQUESTS)
        response.headers["X-RateLimit-Remaining"] = str(_MAX_REQUESTS - len(self._hits[client_ip]))
        return response
