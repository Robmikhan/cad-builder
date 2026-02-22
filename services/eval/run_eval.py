"""
Golden-set evaluation harness.
Runs each case in services/eval/golden_set/ through the pipeline
and validates against expected.json criteria.

Usage:
    python -m services.eval.run_eval
"""
from __future__ import annotations
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_ROOT))


def main():
    from services.db.repo import Repo
    from services.pipelines.run_pipeline import run_job_pipeline

    data_dir = str(_ROOT / "data")
    os.environ.setdefault("CAD_AGENT_DATA_DIR", data_dir)
    repo = Repo(data_dir)

    golden = _ROOT / "services" / "eval" / "golden_set"
    cases = sorted([p for p in golden.iterdir() if p.is_dir()])

    if not cases:
        print("No golden set cases found.")
        return

    results = []
    passed = 0
    failed = 0

    for case_dir in cases:
        spec_file = case_dir / "part_spec.json"
        expected_file = case_dir / "expected.json"
        if not spec_file.exists():
            continue

        spec = json.loads(spec_file.read_text(encoding="utf-8"))
        expected = json.loads(expected_file.read_text(encoding="utf-8")) if expected_file.exists() else {}

        job_id = f"eval-{uuid.uuid4().hex[:8]}"
        job = {
            "job_id": job_id,
            "status": "QUEUED",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "part_spec": spec,
            "artifacts": {},
            "metrics": {"runtime_sec": 0.0, "num_iterations": 0},
            "error": "",
        }
        repo.save_job(job)

        print(f"\n{'='*60}")
        print(f"  Case: {case_dir.name}")
        print(f"  Part: {spec.get('part_name', '?')}")

        try:
            run_job_pipeline(job_id, repo)
            result_job = repo.load_job(job_id)
            issues = []

            # Check: should_succeed
            if expected.get("should_succeed", True):
                if result_job["status"] != "DONE":
                    issues.append(f"Expected DONE, got {result_job['status']}: {result_job.get('error', '')[:200]}")

            # Check: must_contain_in_source
            cad_path = (result_job.get("artifacts") or {}).get("cad_script_path")
            if cad_path and Path(cad_path).is_file():
                cad_prog = json.loads(Path(cad_path).read_text(encoding="utf-8"))
                source = cad_prog.get("source", "")
                for keyword in expected.get("must_contain_in_source", []):
                    if keyword not in source:
                        issues.append(f"Source missing '{keyword}'")

            # Check: min_step_file_bytes
            step_path = (result_job.get("artifacts") or {}).get("step_path")
            min_bytes = expected.get("min_step_file_bytes", 0)
            if min_bytes > 0 and step_path and Path(step_path).is_file():
                actual = Path(step_path).stat().st_size
                if actual < min_bytes:
                    issues.append(f"STEP file too small: {actual} < {min_bytes} bytes")

            status = "PASS" if not issues else "FAIL"
            if status == "PASS":
                passed += 1
            else:
                failed += 1

            runtime = result_job.get("metrics", {}).get("runtime_sec", 0)
            print(f"  Status: {status} ({runtime:.1f}s)")
            for issue in issues:
                print(f"    - {issue}")

            results.append({"case": case_dir.name, "status": status, "issues": issues, "runtime": runtime})

        except Exception as e:
            failed += 1
            print(f"  Status: ERROR — {e}")
            results.append({"case": case_dir.name, "status": "ERROR", "issues": [str(e)]})

    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed, {len(results)} total")
    print(f"{'='*60}\n")

    # Save results
    out = _ROOT / "data" / "eval_results.json"
    out.write_text(json.dumps({"results": results}, indent=2), encoding="utf-8")
    print(f"Results saved to {out}")

    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main() or 0)
