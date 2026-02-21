from __future__ import annotations
from pathlib import Path
from typing import Optional, Tuple
import trimesh


def find_mesh_file(output_dir: str) -> Optional[str]:
    """
    SF3D typically outputs .glb, TripoSR may output .obj/.glb depending on options.
    We just search for the newest likely mesh file.
    """
    out = Path(output_dir)
    if not out.exists():
        return None

    exts = [".glb", ".gltf", ".obj", ".ply", ".stl"]
    candidates = []
    for p in out.rglob("*"):
        if p.is_file() and p.suffix.lower() in exts:
            candidates.append(p)

    if not candidates:
        return None

    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return str(candidates[0])


def bounding_box_dims_mm(mesh_path: str) -> Tuple[float, float, float]:
    """
    Returns axis-aligned bounding box dimensions (same unit as mesh).
    Many recon tools output in arbitrary scale; you should provide ONE real measurement to scale later.
    """
    m = trimesh.load(mesh_path, force="mesh")
    if m.is_empty:
        raise RuntimeError(f"Mesh is empty: {mesh_path}")

    bounds = m.bounds  # [[minx,miny,minz],[maxx,maxy,maxz]]
    dims = bounds[1] - bounds[0]
    return float(dims[0]), float(dims[1]), float(dims[2])
