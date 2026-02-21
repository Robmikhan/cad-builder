#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

mkdir -p data/cache/models

pip install -U "huggingface_hub[cli]"

# Safe defaults: download only if you want local weights.
huggingface-cli download stabilityai/TripoSR --local-dir data/cache/models/triposr --local-dir-use-symlinks False || true
huggingface-cli download stabilityai/stable-fast-3d --local-dir data/cache/models/sf3d --local-dir-use-symlinks False || true
huggingface-cli download tencent/Hunyuan3D-2 --local-dir data/cache/models/hunyuan3d --local-dir-use-symlinks False || true

echo "✅ Model downloads attempted (some may require auth/accepting license)."
