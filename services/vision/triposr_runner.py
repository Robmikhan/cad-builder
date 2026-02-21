from __future__ import annotations
import sys
import subprocess
from pathlib import Path
from services.vision.mesh_utils import find_mesh_file

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_triposr(image_path: str, output_dir: str, timeout_sec: int = 300) -> str:
    """
    Runs TripoSR official repo inference:
      python run.py <image> --output-dir <dir> --model-save-format glb
    Uses sys.executable so the current venv (with PyMCubes shim etc.) is used.
    """
    repo_dir = _PROJECT_ROOT / "data" / "cache" / "repos" / "TripoSR"
    run_py = repo_dir / "run.py"
    if not run_py.exists():
        raise RuntimeError("TripoSR repo not found. Run: scripts/install_vision_repos.ps1")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(run_py),
        image_path,
        "--output-dir", output_dir,
        "--model-save-format", "glb",
    ]
    proc = subprocess.run(
        cmd, cwd=str(repo_dir), capture_output=True, text=True, timeout=timeout_sec,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            "TripoSR failed.\n"
            f"STDOUT:\n{proc.stdout[-2000:]}\n\nSTDERR:\n{proc.stderr[-2000:]}"
        )

    mesh = find_mesh_file(output_dir)
    if not mesh:
        raise RuntimeError("TripoSR completed but no mesh file found in output_dir.")
    return mesh
