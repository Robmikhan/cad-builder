# CAD Builder — Text/Image → Parametric CAD → STEP/STL

An agentic pipeline that converts **text descriptions** or **photos** into production-ready parametric CAD files using local AI models.

## What It Does

| Input | Pipeline | Output |
|-------|----------|--------|
| **Text prompt** | LLM (Ollama) → CadQuery generation → validation + auto-repair → export | STEP, STL, CadQuery source |
| **Photo** | rembg → TripoSR/InstantMesh mesh → primitive fitting → CadQuery → export | STEP, STL, GLB mesh, CadQuery source |

## Features

- **LLM-powered CadQuery generation** — Ollama + qwen2.5-coder:7b generates real parametric CadQuery code from text descriptions
- **Auto-repair loop** — if validation fails, the LLM automatically fixes the code (up to N attempts)
- **Background removal** — rembg cleans input photos before mesh reconstruction
- **3D mesh reconstruction** — SF3D → TripoSR → InstantMesh fallback chain
- **Sandboxed execution** — CadQuery scripts run in a restricted sandbox (no os/sys/subprocess access)
- **Web UI** — React dashboard with job management, 3D model preview, drag-and-drop image upload
- **Real-time streaming** — SSE endpoint for live pipeline progress
- **API key auth** — optional API key middleware for production deployments
- **Dual persistence** — local JSON files + optional Supabase cloud sync
- **GPU-accelerated** — NVIDIA CUDA support for vision models (RTX 3060+ recommended)

## Quick Start

```bash
# 1. Clone and install
git clone <repo-url> && cd cad-builder
python -m venv .venv && .venv/Scripts/activate  # Windows
pip install -e .

# 2. Install Ollama (for LLM-powered generation)
winget install Ollama.Ollama
ollama pull qwen2.5-coder:7b

# 3. Install vision models (for IMAGE pipeline)
powershell scripts/install_vision_repos.ps1

# 4. Start the API server
uvicorn services.api.main:app --host 0.0.0.0 --port 8080

# 5. Start the worker (separate terminal)
python -m services.workers.worker

# 6. Build and serve the frontend
cd frontend && npm install && npm run build && cd ..
# Frontend is served automatically at http://localhost:8080
```

## Docker (GPU)

```bash
cd docker
docker compose up --build
# API + Worker + Frontend at http://localhost:8080
```

Requires NVIDIA Container Toolkit (`nvidia-docker2`) for GPU support.

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/jobs` | Create a new CAD generation job |
| `GET` | `/jobs` | List all jobs |
| `GET` | `/jobs/{id}` | Job status + artifacts |
| `GET` | `/jobs/{id}/events` | Pipeline event log |
| `GET` | `/jobs/{id}/stream` | SSE real-time event stream |
| `POST` | `/upload` | Upload an image file |
| `GET` | `/assets/{id}/step` | Download STEP file |
| `GET` | `/assets/{id}/stl` | Download STL file |
| `GET` | `/assets/{id}/glb` | Download GLB mesh for 3D preview |
| `GET` | `/assets/{id}/bundle` | Download complete ZIP bundle |
| `GET` | `/models` | List configured AI models |
| `GET` | `/health` | Health check |

## Configuration

Copy `.env.example` to `.env` and customize:

| Variable | Default | Description |
|----------|---------|-------------|
| `CAD_AGENT_API_KEYS` | *(empty = no auth)* | Comma-separated API keys |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `qwen2.5-coder:7b` | LLM model for CadQuery generation |
| `LLM_PROVIDER` | `ollama` | Set to `none` to disable LLM |
| `CAD_AGENT_MAX_REPAIR_ITERS` | `3` | Max LLM repair attempts |
| `CAD_AGENT_CAD_TIMEOUT_SEC` | `30` | CadQuery execution timeout |
| `SUPABASE_URL` | *(empty)* | Optional Supabase persistence |

## Architecture

```
frontend/          React + Tailwind + model-viewer (3D preview)
services/
  api/             FastAPI server + auth + SSE streaming
  cad/             CadQuery runner (sandboxed) + exporters
  db/              Dual persistence (local JSON + Supabase)
  llm/             Ollama client + orchestrator (generation + repair)
  pipelines/       Step-based pipeline engine
  vision/          SF3D, TripoSR, InstantMesh runners
  workers/         File-backed queue + worker with crash recovery
configs/           Pipeline steps, model manifest, observability
schemas/           JSON Schema validation for all data types
```

## AI Models Used

| Model | Purpose | VRAM | Status |
|-------|---------|------|--------|
| qwen2.5-coder:7b | CadQuery code generation + repair | ~5GB | via Ollama |
| rembg (U2-Net) | Background removal | ~200MB | Built-in |
| TripoSR | Image → 3D mesh | ~4GB | GPU required |
| InstantMesh | Image → 3D mesh (alt) | ~6GB | GPU required |
| SF3D | Image → 3D mesh (alt) | ~4GB | GPU required |

## Testing

```bash
python -m pytest tests/ -v     # 29+ unit/integration tests
python scripts/check_gpu.py     # Verify GPU + model setup
python scripts/test_llm_pipeline.py  # End-to-end LLM test
```

## Safety

This system runs AI-generated code in a sandbox with restricted builtins. Only `cadquery` and `math` imports are permitted. If you use this for regulated items, you are responsible for legal compliance.
