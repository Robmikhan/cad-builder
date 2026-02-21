#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y \
  git wget curl unzip \
  python3 python3-venv python3-pip \
  build-essential cmake ninja-build pkg-config \
  ffmpeg \
  libgl1-mesa-glx libglib2.0-0

python3 -m venv .venv
source .venv/bin/activate
pip install -U pip wheel

pip install -e .

echo "✅ Setup complete. Activate with: source .venv/bin/activate"
echo "ℹ️ Optional: install FreeCAD for STEP export (system install recommended)."
