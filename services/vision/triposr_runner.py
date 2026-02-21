from __future__ import annotations
import subprocess
from pathlib import Path
from services.vision.mesh_utils import find_mesh_file


def run_triposr(image_path: str, output_dir: str) -> str:
    """
    Runs TripoSR official repo inference:
      python run.py <image> --output-dir <dir>
    """
    repo_dir = Path("data/cache/repos/TripoSR")
    run_py = repo_dir / "run.py"
    if not run_py.exists():
        raise RuntimeError("TripoSR repo not found. Run: bash scripts/install_vision_repos.sh")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cmd = ["python", str(run_py), image_path, "--output-dir", output_dir]
    proc = subprocess.run(cmd, cwd=str(repo_dir), capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(
            "TripoSR failed.\n"
            f"STDOUT:\n{proc.stdout[-2000:]}\n\nSTDERR:\n{proc.stderr[-2000:]}"
        )

    mesh = find_mesh_file(output_dir)
    if not mesh:
        raise RuntimeError("TripoSR completed but no mesh file found in output_dir.")
    return mesh
