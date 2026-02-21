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
    bbox_center: Tuple[float, float, float]
    cylinders: List[CylinderCut]
    notes: List[str]


def _axis_index(axis: str) -> int:
    return {"X": 0, "Y": 1, "Z": 2}[axis]


def _ransac_circle_2d(
    uv: np.ndarray,
    rng: np.random.RandomState,
    iters: int = 800,
    dist_thresh: float = 0.35,
    min_inliers: int = 80,
    radius_range: Optional[Tuple[float, float]] = None,
) -> Optional[Tuple[np.ndarray, float, np.ndarray]]:
    """Simple 2D RANSAC circle fit. Returns (center, radius, inlier_mask) or None."""
    n = uv.shape[0]
    if n < min_inliers:
        return None

    best_inliers = 0
    best = None
    idxs = np.arange(n)

    for _ in range(iters):
        i1, i2, i3 = rng.choice(idxs, 3, replace=False)
        p1, p2, p3 = uv[i1], uv[i2], uv[i3]
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        det = 2.0 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        if abs(det) < 1e-9:
            continue
        ux = (
            (x1 * x1 + y1 * y1) * (y2 - y3)
            + (x2 * x2 + y2 * y2) * (y3 - y1)
            + (x3 * x3 + y3 * y3) * (y1 - y2)
        ) / det
        uy = (
            (x1 * x1 + y1 * y1) * (x3 - x2)
            + (x2 * x2 + y2 * y2) * (x1 - x3)
            + (x3 * x3 + y3 * y3) * (x2 - x1)
        ) / det
        center = np.array([ux, uy], dtype=float)
        r = float(np.linalg.norm(p1 - center))
        if radius_range is not None:
            rmin, rmax = radius_range
            if not (rmin <= r <= rmax):
                continue
        d = np.linalg.norm(uv - center, axis=1)
        inlier_mask = np.abs(d - r) <= dist_thresh
        cnt = int(inlier_mask.sum())
        if cnt > best_inliers:
            best_inliers = cnt
            best = (center, r, inlier_mask)

    if best is None or best_inliers < min_inliers:
        return None
    return best


def fit_primitives(mesh_path: str, max_cylinders: int = 8, seed: int = 42) -> PrimitiveFitResult:
    """
    Heuristic primitive fitting:
    - Use mesh AABB for main body L/W/H
    - Detect cylindrical holes via 2D RANSAC circle fitting on vertex projections
    This is intentionally conservative and not perfect, but works well on many parts.

    Returns cylinders aligned to primary axes only.
    """
    rng = np.random.RandomState(seed)

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

    rmax = 0.45 * float(np.max(dims))
    rmin = max(0.5, 0.01 * float(np.max(dims)))

    for axis in axes_to_try:
        if len(cylinders) >= max_cylinders:
            break

        ai = _axis_index(axis)
        uv_axes = [i for i in [0, 1, 2] if i != ai]
        working_uv = verts[:, uv_axes].copy()

        for _ in range(max_cylinders - len(cylinders)):
            fit = _ransac_circle_2d(
                working_uv,
                rng,
                iters=800,
                dist_thresh=max(0.3, 0.005 * float(np.max(dims))),
                min_inliers=max(80, int(0.02 * len(working_uv))),
                radius_range=(rmin, rmax),
            )
            if fit is None:
                break
            center, radius, inlier_mask = fit
            cylinders.append(
                CylinderCut(
                    axis=axis,
                    radius=float(radius),
                    center=(float(center[0]), float(center[1])),
                    through=True,
                )
            )
            # Remove inliers to find next circle
            keep = ~inlier_mask
            if int(keep.sum()) < 50:
                break
            working_uv = working_uv[keep]

        if cylinders:
            notes.append(f"Detected {len(cylinders)} cylinder candidates along axis {axis}.")
            break

    if not cylinders:
        notes.append("No cylinders confidently detected; falling back to bbox-only CAD.")

    bbox_mid = (bounds[0] + bounds[1]) / 2.0
    return PrimitiveFitResult(
        bbox_LWH=(L, W, H),
        bbox_center=(float(bbox_mid[0]), float(bbox_mid[1]), float(bbox_mid[2])),
        cylinders=cylinders,
        notes=notes,
    )
