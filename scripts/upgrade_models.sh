#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

python -m services.models.model_manager upgrade --policy configs/upgrade_policy.yaml
