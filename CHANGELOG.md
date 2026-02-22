# Changelog

## v0.2.0 — Market-Ready MVP (2026-02-22)

### Frontend
- Professional landing page with feature showcase and how-it-works flow
- Dark theme dashboard with job stats, auto-refresh, and jobs table
- New Job page with PROMPT mode (dimensions) and IMAGE mode (drag-and-drop upload)
- Job Detail page with tabs: Overview, 3D Preview (model-viewer), CAD Script, Events
- Real-time SSE streaming for live pipeline progress
- Job deletion with confirmation dialog
- STEP / STL / Bundle download buttons
- Settings page for API key configuration and server health monitoring
- Models page showing installed AI models

### Backend
- API key authentication middleware (optional, via `CAD_AGENT_API_KEYS`)
- Rate limiting middleware (configurable per-IP)
- Sandboxed CadQuery execution (restricted builtins, only cadquery+math imports, timeout)
- Image upload endpoint with file type validation
- SSE streaming endpoint for real-time pipeline events
- STL export (on-the-fly from CadQuery source)
- GLB mesh download for 3D preview
- Job deletion endpoint
- Health check endpoint with uptime
- Stale job recovery on worker startup
- Frontend SPA serving from FastAPI (StaticFiles + 404 fallback)
- All API routes under `/api` prefix

### DevOps
- Multi-stage GPU Dockerfile (Node build → NVIDIA CUDA 12.1 runtime)
- Docker Compose with GPU reservations and health-based depends_on
- GitHub Actions CI (Python tests + lint + frontend build)
- Golden set evaluation harness with test cases

### Documentation
- Complete README rewrite with architecture, API reference, config table
- MIT License
- Updated .env.example with all configuration options

## v0.1.0 — Foundation (2026-02-21)

### Core Pipeline
- PROMPT pipeline: text → LLM (Ollama qwen2.5-coder:7b) → CadQuery → validate → STEP export → bundle
- IMAGE pipeline: photo → rembg → SF3D/TripoSR/InstantMesh mesh → primitive fitting → CadQuery → STEP
- VIDEO pipeline: pluggable stubs for COLMAP + point2cad
- LLM auto-repair loop (up to N attempts)
- Background removal with rembg
- 3D mesh reconstruction with fallback chain (SF3D → TripoSR → InstantMesh)

### Infrastructure
- FastAPI server with job queue and worker
- Dual persistence (local JSON + optional Supabase)
- JSON Schema validation for all data types
- 29 unit/integration tests
