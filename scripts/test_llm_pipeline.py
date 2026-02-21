"""
Live test: PROMPT pipeline with Ollama LLM generating CadQuery code.
Verifies the full chain: LLM generation → validation → STEP export.

Usage:
    .venv\Scripts\python scripts\test_llm_pipeline.py
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from services.db.repo import Repo
from services.pipelines.run_pipeline import run_job_pipeline


def main():
    print("=" * 60)
    print("  CAD Builder — LLM PROMPT Pipeline Test")
    print("=" * 60)

    # Check Ollama is running
    from services.llm.ollama_client import is_available, OLLAMA_MODEL
    if not is_available():
        print("\n  ERROR: Ollama is not running!")
        print("  Start it with: ollama serve")
        print("  Or ensure the Ollama desktop app is running.")
        return 1

    print(f"\n  Ollama: connected, model={OLLAMA_MODEL}")

    data_dir = str(_ROOT / "data")
    os.environ["CAD_AGENT_DATA_DIR"] = data_dir
    repo = Repo(data_dir)

    # Create a rich part spec to test LLM generation
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "part_spec": {
            "part_name": "Mounting Bracket",
            "mode": "PROMPT",
            "units": "mm",
            "tolerance_mm": 0.2,
            "use_case": "An L-shaped mounting bracket with two holes for M5 bolts and a fillet on the inner corner",
            "dimensions": {"L": 60, "W": 40, "H": 30},
            "materials": {"material": "aluminum", "process": "CNC"},
            "constraints": {"must_be_parametric": True},
        },
        "artifacts": {},
        "metrics": {"runtime_sec": 0.0, "num_iterations": 0},
        "error": "",
    }
    repo.save_job(job)

    print(f"  Job ID: {job_id}")
    print(f"  Part: {job['part_spec']['part_name']}")
    print(f"  Description: {job['part_spec']['use_case']}")
    print(f"\n  Running PROMPT pipeline with LLM...\n")

    run_job_pipeline(job_id, repo)

    result = repo.load_job(job_id)
    print(f"\n{'=' * 60}")
    print(f"  RESULTS")
    print(f"{'=' * 60}")
    print(f"  Status:     {result['status']}")
    print(f"  Runtime:    {result['metrics']['runtime_sec']:.2f}s")
    print(f"  Iterations: {result['metrics'].get('num_iterations', 0)}")

    if result.get("error"):
        print(f"  ERROR: {result['error']}")
        return 1

    # Show generated code
    cad_path = result["artifacts"].get("cad_script_path")
    if cad_path and Path(cad_path).is_file():
        cad_prog = json.loads(Path(cad_path).read_text(encoding="utf-8"))
        print(f"\n  Generated CadQuery source:")
        print(f"  {'-' * 40}")
        for line in cad_prog["source"].split("\n"):
            print(f"    {line}")
        print(f"  {'-' * 40}")
        print(f"  Parameters: {cad_prog.get('parameters', {})}")

    step_path = result["artifacts"].get("step_path")
    if step_path and Path(step_path).is_file():
        size = Path(step_path).stat().st_size
        print(f"\n  STEP file: {step_path}")
        print(f"  STEP size: {size:,} bytes")

    events = repo.load_events(job_id)
    event_types = [e["event_type"] for e in events]
    print(f"\n  Pipeline events: {event_types}")

    # Check if LLM was actually used
    for ev in events:
        if ev["event_type"] == "text2cad_ok":
            method = ev.get("payload", {}).get("method", "unknown")
            print(f"\n  Generation method: {method}")
            if method == "llm":
                print("  LLM successfully generated the CadQuery code!")
            else:
                print("  WARNING: Fell back to parametric block (LLM may have failed)")

    print(f"\n{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
