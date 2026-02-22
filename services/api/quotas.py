"""
Subscription tier definitions and job quota enforcement.

Tiers are stored in a local JSON file: data/api_keys.json
Each entry maps an API key to its tier, creation date, and optional expiry.

Environment:
  CAD_AGENT_API_KEYS is still respected for backward compat (unlimited tier).
  Keys in api_keys.json have quota enforcement.
"""
from __future__ import annotations
import json
import logging
import os
import secrets
import time
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)

# ── Tier Definitions ──
TIERS = {
    "free_trial": {
        "label": "Free Trial",
        "max_jobs_per_month": 10,
        "trial_days": 14,
        "pipelines": ["PROMPT"],
        "price_monthly": 0,
    },
    "starter": {
        "label": "Starter",
        "max_jobs_per_month": 100,
        "trial_days": 0,
        "pipelines": ["PROMPT", "IMAGE"],
        "price_monthly": 19,
        "stripe_link": os.getenv("STRIPE_LINK_STARTER", ""),
    },
    "pro": {
        "label": "Pro",
        "max_jobs_per_month": 500,
        "trial_days": 0,
        "pipelines": ["PROMPT", "IMAGE", "VIDEO"],
        "price_monthly": 49,
        "stripe_link": os.getenv("STRIPE_LINK_PRO", ""),
    },
    "business": {
        "label": "Business",
        "max_jobs_per_month": 2000,
        "trial_days": 0,
        "pipelines": ["PROMPT", "IMAGE", "VIDEO"],
        "price_monthly": 149,
        "stripe_link": os.getenv("STRIPE_LINK_BUSINESS", ""),
    },
    "unlimited": {
        "label": "Unlimited",
        "max_jobs_per_month": 999999,
        "trial_days": 0,
        "pipelines": ["PROMPT", "IMAGE", "VIDEO"],
        "price_monthly": 0,
    },
}


def _keys_path() -> Path:
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    return Path(data_dir) / "api_keys.json"


def _load_keys() -> dict:
    p = _keys_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            _log.warning("Corrupted api_keys.json, starting fresh")
    return {}


def _save_keys(keys: dict) -> None:
    p = _keys_path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(keys, indent=2), encoding="utf-8")


def create_trial_key(email: str = "") -> dict:
    """Generate a free trial API key (14 days, 10 jobs/month)."""
    key = f"cad_trial_{secrets.token_hex(16)}"
    now = datetime.now(timezone.utc)
    entry = {
        "tier": "free_trial",
        "email": email,
        "created_at": now.isoformat(),
        "expires_at": (now + timedelta(days=14)).isoformat(),
        "jobs_this_month": 0,
        "month_reset": now.strftime("%Y-%m"),
    }
    keys = _load_keys()
    keys[key] = entry
    _save_keys(keys)
    return {"api_key": key, **entry}


def create_paid_key(tier: str, email: str = "") -> dict:
    """Generate a paid API key for a given tier."""
    if tier not in TIERS or tier == "free_trial":
        raise ValueError(f"Invalid paid tier: {tier}")
    key = f"cad_{tier}_{secrets.token_hex(16)}"
    now = datetime.now(timezone.utc)
    entry = {
        "tier": tier,
        "email": email,
        "created_at": now.isoformat(),
        "expires_at": "",
        "jobs_this_month": 0,
        "month_reset": now.strftime("%Y-%m"),
    }
    keys = _load_keys()
    keys[key] = entry
    _save_keys(keys)
    return {"api_key": key, **entry}


def get_key_info(api_key: str) -> Optional[dict]:
    """Look up an API key's tier and usage. Returns None if not found."""
    # Check legacy env-based keys first (unlimited tier)
    legacy_keys = {k.strip() for k in os.getenv("CAD_AGENT_API_KEYS", "").split(",") if k.strip()}
    if api_key in legacy_keys:
        return {
            "tier": "unlimited",
            "email": "",
            "created_at": "",
            "expires_at": "",
            "jobs_this_month": 0,
            "month_reset": "",
        }

    keys = _load_keys()
    return keys.get(api_key)


def check_quota(api_key: str) -> tuple[bool, str]:
    """
    Check if the API key can create a new job.
    Returns (allowed, reason).
    """
    # No auth configured = open access
    legacy_keys = {k.strip() for k in os.getenv("CAD_AGENT_API_KEYS", "").split(",") if k.strip()}
    if not legacy_keys and not _keys_path().exists():
        return True, "open_access"

    if not api_key:
        return False, "API key required"

    # Legacy keys = unlimited
    if api_key in legacy_keys:
        return True, "unlimited"

    keys = _load_keys()
    entry = keys.get(api_key)
    if not entry:
        return False, "Invalid API key"

    tier_name = entry.get("tier", "free_trial")
    tier = TIERS.get(tier_name, TIERS["free_trial"])

    # Check expiry (trial keys)
    if entry.get("expires_at"):
        expiry = datetime.fromisoformat(entry["expires_at"])
        if datetime.now(timezone.utc) > expiry:
            return False, "Trial expired. Please upgrade to a paid plan."

    # Reset monthly counter if new month
    current_month = datetime.now(timezone.utc).strftime("%Y-%m")
    if entry.get("month_reset") != current_month:
        entry["jobs_this_month"] = 0
        entry["month_reset"] = current_month
        keys[api_key] = entry
        _save_keys(keys)

    # Check quota
    if entry["jobs_this_month"] >= tier["max_jobs_per_month"]:
        return False, f"Monthly quota reached ({tier['max_jobs_per_month']} jobs). Please upgrade your plan."

    return True, "ok"


def increment_usage(api_key: str) -> None:
    """Increment the job counter for an API key."""
    keys = _load_keys()
    if api_key in keys:
        current_month = datetime.now(timezone.utc).strftime("%Y-%m")
        if keys[api_key].get("month_reset") != current_month:
            keys[api_key]["jobs_this_month"] = 0
            keys[api_key]["month_reset"] = current_month
        keys[api_key]["jobs_this_month"] = keys[api_key].get("jobs_this_month", 0) + 1
        _save_keys(keys)


def get_usage(api_key: str) -> dict:
    """Get usage stats for the current billing period."""
    info = get_key_info(api_key)
    if not info:
        return {"error": "Invalid API key"}

    tier_name = info.get("tier", "free_trial")
    tier = TIERS.get(tier_name, TIERS["free_trial"])

    # Calculate days remaining for trials
    days_remaining = None
    if info.get("expires_at"):
        expiry = datetime.fromisoformat(info["expires_at"])
        delta = expiry - datetime.now(timezone.utc)
        days_remaining = max(0, delta.days)

    return {
        "tier": tier_name,
        "tier_label": tier["label"],
        "jobs_used": info.get("jobs_this_month", 0),
        "jobs_limit": tier["max_jobs_per_month"],
        "jobs_remaining": max(0, tier["max_jobs_per_month"] - info.get("jobs_this_month", 0)),
        "pipelines": tier["pipelines"],
        "price_monthly": tier["price_monthly"],
        "days_remaining": days_remaining,
        "email": info.get("email", ""),
    }
