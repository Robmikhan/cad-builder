from __future__ import annotations
import subprocess
from pathlib import Path
from services.vision.mesh_utils import find_mesh_file

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_sf3d(image_path: str, output_dir: str) -> str:
    """
    Runs SF3D official repo inference:
      python run.py <image> --output-dir <dir>
    """
    repo_dir = _PROJECT_ROOT / "data" / "cache" / "repos" / "stable-fast-3d"
    run_py = repo_dir / "run.py"
    if not run_py.exists():
        raise RuntimeError("SF3D repo not found. Run: bash scripts/install_vision_repos.sh")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cmd = ["python", str(run_py), image_path, "--output-dir", output_dir]
    proc = subprocess.run(cmd, cwd=str(repo_dir), capture_output=True, text=True)

    if proc.returncode != 0:
        raise RuntimeError(
            "SF3D failed.\n"
            f"STDOUT:\n{proc.stdout[-2000:]}\n\nSTDERR:\n{proc.stderr[-2000:]}"
        )

    mesh = find_mesh_file(output_dir)
    if not mesh:
        raise RuntimeError("SF3D completed but no mesh file found in output_dir.")
    return mesh
