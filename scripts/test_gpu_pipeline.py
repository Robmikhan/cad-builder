"""
Real GPU test: feed an image through the full IMAGE pipeline using TripoSR on local GPU.
First run downloads model weights (~1.5GB from HuggingFace).

Usage:
    .venv\Scripts\python scripts\test_gpu_pipeline.py [path/to/image.png]

If no image is provided, generates a simple test image.
"""
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

# Ensure project root is on path
_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from services.db.repo import Repo
from services.pipelines.run_pipeline import run_job_pipeline


def create_test_image(out_path: Path) -> str:
    """Create a simple solid-colored 512x512 image as a test input."""
    from PIL import Image
    img = Image.new("RGB", (512, 512), color=(180, 180, 200))
    # Draw a simple rectangle shape in the center to give the model something
    from PIL import ImageDraw
    draw = ImageDraw.Draw(img)
    draw.rectangle([128, 128, 384, 384], fill=(60, 60, 80))
    draw.ellipse([200, 200, 312, 312], fill=(180, 180, 200))  # hole-like feature
    img.save(str(out_path))
    print(f"  Created test image: {out_path}")
    return str(out_path)


def main():
    print("=" * 60)
    print("  CAD Builder — Real GPU Pipeline Test")
    print("=" * 60)

    data_dir = str(_ROOT / "data")
    os.environ["CAD_AGENT_DATA_DIR"] = data_dir
    repo = Repo(data_dir)

    # Get or create test image
    if len(sys.argv) > 1 and Path(sys.argv[1]).is_file():
        image_path = str(Path(sys.argv[1]).resolve())
        print(f"\n  Using provided image: {image_path}")
    else:
        img_dir = _ROOT / "data" / "test_inputs"
        img_dir.mkdir(parents=True, exist_ok=True)
        image_path = create_test_image(img_dir / "test_bracket.png")

    # Create job
    job_id = str(uuid.uuid4())
    job = {
        "job_id": job_id,
        "status": "QUEUED",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "part_spec": {
            "part_name": "GPU Test Part",
            "mode": "IMAGE",
            "units": "mm",
            "tolerance_mm": 0.2,
            "inputs": {"image_paths": [image_path]},
        },
        "artifacts": {},
        "metrics": {"runtime_sec": 0.0, "num_iterations": 0},
        "error": "",
    }
    repo.save_job(job)
    print(f"\n  Job ID: {job_id}")
    print(f"  Running IMAGE pipeline with real GPU inference...")
    print(f"  (First run downloads TripoSR weights ~1.5GB)\n")

    # Run pipeline
    run_job_pipeline(job_id, repo)

    # Results
    result = repo.load_job(job_id)
    print(f"\n{'=' * 60}")
    print(f"  RESULTS")
    print(f"{'=' * 60}")
    print(f"  Status:  {result['status']}")
    print(f"  Runtime: {result['metrics']['runtime_sec']:.2f}s")

    if result.get("error"):
        print(f"  ERROR:   {result['error']}")
        return 1

    artifacts = result.get("artifacts", {})
    for k, v in artifacts.items():
        if isinstance(v, str):
            p = Path(v)
            exists = p.is_file()
            size = f"{p.stat().st_size:,} bytes" if exists else "MISSING"
            print(f"  {k}: {size}")
        else:
            print(f"  {k}: {v}")

    step_path = artifacts.get("step_path")
    if step_path and Path(step_path).is_file():
        print(f"\n  STEP file: {step_path}")
        print(f"  STEP size: {Path(step_path).stat().st_size:,} bytes")
        print(f"\n  SUCCESS — Real GPU image-to-STEP pipeline works!")
    else:
        print(f"\n  WARNING: No STEP file produced")

    # Print events
    events = repo.load_events(job_id)
    print(f"\n  Pipeline events:")
    for ev in events:
        print(f"    [{ev.get('event_type')}]")

    print(f"{'=' * 60}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
