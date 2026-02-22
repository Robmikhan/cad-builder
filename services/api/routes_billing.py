"""
Billing and usage API routes.
- POST /trial — generate a free trial API key
- GET /usage — current month's usage stats for the authenticated key
- GET /tiers — public tier listing with prices
"""
from __future__ import annotations
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from services.api.quotas import (
    TIERS, create_trial_key, get_usage, get_key_info,
)

router = APIRouter()


class TrialRequest(BaseModel):
    email: str = ""


@router.post("/trial")
def request_trial(body: TrialRequest):
    """Generate a 14-day free trial API key."""
    result = create_trial_key(email=body.email)
    return result


@router.get("/usage")
def get_current_usage(request: Request):
    """Get usage stats for the current API key."""
    api_key = request.headers.get("x-api-key", "")
    if not api_key:
        raise HTTPException(401, "Provide X-API-Key header to check usage")
    usage = get_usage(api_key)
    if "error" in usage:
        raise HTTPException(404, usage["error"])
    return usage


@router.get("/tiers")
def list_tiers():
    """Public endpoint: list available subscription tiers."""
    result = []
    for tid, t in TIERS.items():
        if tid == "unlimited":
            continue
        result.append({
            "id": tid,
            "label": t["label"],
            "price_monthly": t["price_monthly"],
            "max_jobs_per_month": t["max_jobs_per_month"],
            "pipelines": t["pipelines"],
            "trial_days": t["trial_days"],
            "stripe_link": t.get("stripe_link", ""),
        })
    return result
