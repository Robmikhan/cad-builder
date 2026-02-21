#!/usr/bin/env bash
set -euo pipefail
source .venv/bin/activate

mkdir -p data/cache/repos

# SF3D
if [ ! -d "data/cache/repos/stable-fast-3d" ]; then
  git clone https://github.com/Stability-AI/stable-fast-3d data/cache/repos/stable-fast-3d
fi
pip install -r data/cache/repos/stable-fast-3d/requirements.txt

# TripoSR
if [ ! -d "data/cache/repos/TripoSR" ]; then
  git clone https://github.com/VAST-AI-Research/TripoSR data/cache/repos/TripoSR
fi
pip install -r data/cache/repos/TripoSR/requirements.txt

echo "✅ Vision repos installed."
echo "ℹ️ SF3D may require Hugging Face access + 'huggingface-cli login' per their README."
