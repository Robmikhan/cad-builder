#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

export CAD_AGENT_HOST="${CAD_AGENT_HOST:-0.0.0.0}"
export CAD_AGENT_PORT="${CAD_AGENT_PORT:-8080}"

uvicorn services.api.main:app --host "$CAD_AGENT_HOST" --port "$CAD_AGENT_PORT"
