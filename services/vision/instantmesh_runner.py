"""
InstantMesh runner — efficient 3D mesh generation from a single image.
Uses the TencentARC/InstantMesh repo with FlexiCubes for high-quality meshes.
Auto-downloads model weights from HuggingFace on first run.
"""
from __future__ import annotations
import sys
import subprocess
from pathlib import Path
from services.vision.mesh_utils import find_mesh_file

_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def run_instantmesh(image_path: str, output_dir: str, timeout_sec: int = 300) -> str:
    """
    Run InstantMesh inference:
      python run.py configs/instant-mesh-large.yaml <image> --output_path <dir>
    Uses sys.executable so the current venv is used.
    """
    repo_dir = _PROJECT_ROOT / "data" / "cache" / "repos" / "InstantMesh"
    run_py = repo_dir / "run.py"
    config_yaml = repo_dir / "configs" / "instant-mesh-large.yaml"

    if not run_py.exists():
        raise RuntimeError(
            "InstantMesh repo not found. Clone it with:\n"
            "  git clone https://github.com/TencentARC/InstantMesh data/cache/repos/InstantMesh"
        )

    if not config_yaml.exists():
        raise RuntimeError(f"InstantMesh config not found: {config_yaml}")

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable, str(run_py),
        str(config_yaml),
        image_path,
        "--output_path", output_dir,
        "--no_rembg",  # We already removed bg in step_02
    ]
    proc = subprocess.run(
        cmd, cwd=str(repo_dir), capture_output=True, text=True, timeout=timeout_sec,
    )

    if proc.returncode != 0:
        raise RuntimeError(
            "InstantMesh failed.\n"
            f"STDOUT:\n{proc.stdout[-2000:]}\n\nSTDERR:\n{proc.stderr[-2000:]}"
        )

    # InstantMesh outputs to <output_dir>/instant-mesh-large/meshes/
    mesh_dirs = [
        Path(output_dir) / "instant-mesh-large" / "meshes",
        Path(output_dir) / "meshes",
        Path(output_dir),
    ]
    for d in mesh_dirs:
        if d.exists():
            mesh = find_mesh_file(str(d))
            if mesh:
                return mesh

    # Fallback: search the whole output directory
    mesh = find_mesh_file(output_dir)
    if not mesh:
        raise RuntimeError("InstantMesh completed but no mesh file found in output_dir.")
    return mesh
