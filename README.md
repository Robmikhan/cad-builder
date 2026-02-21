# cad-agent — Prompt/Image/Video → Parametric CAD → STEP (Agentic)

This repo is an agentic pipeline that converts:
- PROMPT (text) OR
- IMAGE (photos) OR
- VIDEO (video)

into:
1) preview mesh (GLB/OBJ) [IMAGE/VIDEO paths are pluggable]
2) parametric CAD program (CadQuery or FreeCAD Python)
3) STEP export (when FreeCAD is installed)
4) validation report + repair loop
5) job bundle zip with metadata

## What works immediately
- PROMPT pipeline: generates CadQuery parametric script + validates + bundles.
- STEP export is enabled when FreeCAD is installed (see setup).

## What is wired but pluggable
- IMAGE pipeline steps: segmentation + image->mesh + image->cad
- VIDEO pipeline steps: COLMAP + pointcloud->cad
These are implemented as adapters/stubs because local installations differ.
The code is structured so you can drop in any new HF/GitHub model and set it in configs/models.yaml.

## Supabase
Optional. If SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set, the API/worker will persist jobs, artifacts, reports, events to Supabase.
If not set, it uses local JSON files in data/outputs/<job_id>/.

See .env.example.

## Run
Linux:
  bash scripts/setup_linux.sh
  bash scripts/run_dev.sh
  bash scripts/run_worker.sh

## API
- POST /jobs : create job
- GET /jobs/{job_id} : job status + artifacts
- GET /jobs/{job_id}/bundle : download result zip
- GET /models : list configured models + local availability

## Roadmap (built-in hooks)
- golden set eval harness: services/eval
- model upgrades: scripts/upgrade_models.sh + configs/upgrade_policy.yaml
- observability: job_events table + JSON logs

## Safety
If you use this system for regulated items, you are responsible for legal compliance.
This repo is generic CAD automation and does not embed weapon-part designs.
