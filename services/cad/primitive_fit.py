from __future__ import annotations
from dataclasses import dataclass
from typing import List, Tuple, Optional
import numpy as np
import trimesh


@dataclass
class CylinderCut:
    axis: str          # "X" | "Y" | "Z"
    radius: float
    center: Tuple[float, float]  # (u, v) in plane perpendicular to axis
    through: bool = True


@dataclass
class PrimitiveFitResult:
    bbox_LWH: Tuple[float, float, float]
    cylinders: List[CylinderCut]
    notes: List[str]


def _axis_index(axis: str) -> int:
    return {"X": 0, "Y": 1, "Z": 2}[axis]


def fit_primitives(mesh_path: str, max_cylinders: int = 8) -> PrimitiveFitResult:
    """
    Heuristic primitive fitting:
    - Use mesh AABB for main body L/W/H
    - Detect cylindrical holes by slicing + circle fitting on vertex projections
    This is intentionally conservative and not perfect, but works well on many parts.

    Returns cylinders aligned to primary axes only.
    """
    m = trimesh.load(mesh_path, force="mesh")
    if m.is_empty:
        raise RuntimeError(f"Empty mesh: {mesh_path}")

    bounds = m.bounds
    dims = bounds[1] - bounds[0]
    L, W, H = float(dims[0]), float(dims[1]), float(dims[2])

    notes: List[str] = []
    cylinders: List[CylinderCut] = []

    # Determine the "thin axis" (often plate thickness) and "primary plane"
    axis_order = np.argsort(dims)  # smallest -> largest
    thin_axis = int(axis_order[0])
    thin_axis_name = ["X", "Y", "Z"][thin_axis]
    notes.append(f"Thin axis guessed as {thin_axis_name} (often thickness).")

    # We'll attempt hole detection along the thin axis first (typical through-holes in plates)
    axes_to_try = [thin_axis_name] + [a for a in ["X", "Y", "Z"] if a != thin_axis_name]

    verts = np.asarray(m.vertices)

    for axis in axes_to_try:
        if len(cylinders) >= max_cylinders:
            break

        ai = _axis_index(axis)
        # Project vertices onto the plane perpendicular to axis: (u, v)
        uv_axes = [i for i in [0, 1, 2] if i != ai]
        uv = verts[:, uv_axes]  # Nx2

        # Cluster projected points to find repeated circular features.
        # Fast heuristic: use k-means-like binning by radius from centroid of full cloud.
        centroid = uv.mean(axis=0)
        r = np.linalg.norm(uv - centroid, axis=1)

        # Look for strong radius modes: histogram peaks (candidate circles)
        hist, bin_edges = np.histogram(r, bins=80)
        peak_idxs = np.argsort(hist)[::-1][:10]  # top peaks
        tried_radii = set()

        for pi in peak_idxs:
            if len(cylinders) >= max_cylinders:
                break
            count = int(hist[pi])
            if count < 150:  # ignore tiny peaks (tuneable)
                continue

            rad = float(0.5 * (bin_edges[pi] + bin_edges[pi + 1]))
            # Avoid duplicates
            key = round(rad, 2)
            if key in tried_radii:
                continue
            tried_radii.add(key)

            # Candidate: circle centered near centroid, radius=rad
            # Sanity checks: radius should be reasonable relative to bbox
            if rad < 0.5 or rad > max(L, W, H) * 0.45:
                continue

            cylinders.append(
                CylinderCut(
                    axis=axis,
                    radius=rad,
                    center=(float(centroid[0]), float(centroid[1])),
                    through=True,
                )
            )

        if cylinders:
            notes.append(f"Detected {len(cylinders)} cylinder candidates along axis {axis}.")
            break

    if not cylinders:
        notes.append("No cylinders confidently detected; falling back to bbox-only CAD.")

    return PrimitiveFitResult(bbox_LWH=(L, W, H), cylinders=cylinders, notes=notes)
