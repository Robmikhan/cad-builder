from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import trimesh


def scale_mesh_to_mm(
    mesh_in: str,
    mesh_out: str,
    target_mm: float,
    measured_axis: str = "X",
) -> Tuple[str, float]:
    """
    Scale mesh so that its bounding-box dimension along measured_axis matches target_mm.

    measured_axis: "X" | "Y" | "Z"
    Returns: (mesh_out, scale_factor)
    """
    axis_map = {"X": 0, "Y": 1, "Z": 2}
    if measured_axis not in axis_map:
        raise ValueError("measured_axis must be X/Y/Z")

    m = trimesh.load(mesh_in, force="mesh")
    if m.is_empty:
        raise RuntimeError(f"Empty mesh: {mesh_in}")

    bounds = m.bounds
    dims = bounds[1] - bounds[0]
    current = float(dims[axis_map[measured_axis]])
    if current <= 1e-9:
        raise RuntimeError("Mesh has near-zero size on chosen axis; choose another axis.")

    scale = float(target_mm / current)
    m.apply_scale(scale)

    out = Path(mesh_out)
    out.parent.mkdir(parents=True, exist_ok=True)

    # Save as GLB if possible, else PLY
    if out.suffix.lower() in [".glb", ".gltf"]:
        m.export(str(out))
    else:
        # default to PLY if unknown extension
        out = out.with_suffix(".ply")
        m.export(str(out))

    return str(out), scale
