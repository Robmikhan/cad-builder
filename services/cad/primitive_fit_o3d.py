# services/cad/primitive_fit_o3d.py
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple, Optional
import math

import numpy as np

try:
    import open3d as o3d
except Exception:  # pragma: no cover
    o3d = None


@dataclass
class Plane:
    normal: Tuple[float, float, float]
    d: float
    inliers: int


@dataclass
class AxisCylinder:
    axis: str  # "X"|"Y"|"Z"
    radius: float
    center_uv: Tuple[float, float]  # center in the plane perpendicular to axis
    inliers: int
    through: bool = True


@dataclass
class PrimitiveFitO3DResult:
    bbox_LWH: Tuple[float, float, float]
    bbox_center: Tuple[float, float, float]
    planes: List[Plane]
    cylinders: List[AxisCylinder]
    notes: List[str]


def _require_o3d():
    if o3d is None:
        raise RuntimeError("Open3D not installed. pip install open3d")


def _load_mesh_as_pcd(mesh_path: str, n_points: int = 60000, voxel: float = 0.0) -> "o3d.geometry.PointCloud":
    _require_o3d()
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    if mesh.is_empty():
        raise RuntimeError(f"Empty mesh: {mesh_path}")

    # Compute normals if needed
    mesh.compute_vertex_normals()

    # Sample points uniformly
    pcd = mesh.sample_points_uniformly(number_of_points=n_points)
    if voxel and voxel > 0:
        pcd = pcd.voxel_down_sample(voxel_size=voxel)

    # Normals for the point cloud
    if not pcd.has_normals():
        pcd.estimate_normals()
    return pcd


def _aabb_dims(pcd: "o3d.geometry.PointCloud") -> Tuple[float, float, float]:
    aabb = pcd.get_axis_aligned_bounding_box()
    ext = aabb.get_extent()
    return float(ext[0]), float(ext[1]), float(ext[2])


def _dominant_planes(
    pcd: "o3d.geometry.PointCloud",
    max_planes: int = 3,
    distance_threshold: float = 0.5,
    ransac_n: int = 3,
    num_iterations: int = 1000,
    min_inliers: int = 2000,
) -> Tuple[List[Plane], "o3d.geometry.PointCloud", List[str]]:
    """
    Iteratively segment planes and remove them.
    """
    _require_o3d()
    planes: List[Plane] = []
    notes: List[str] = []

    remaining = pcd
    for i in range(max_planes):
        if len(remaining.points) < max(5000, min_inliers):
            break

        model, inliers = remaining.segment_plane(
            distance_threshold=distance_threshold,
            ransac_n=ransac_n,
            num_iterations=num_iterations,
        )
        a, b, c, d = model
        inl = len(inliers)
        if inl < min_inliers:
            break

        n = (float(a), float(b), float(c))
        planes.append(Plane(normal=n, d=float(d), inliers=inl))
        notes.append(f"Plane {i}: normal={n}, inliers={inl}")

        remaining = remaining.select_by_index(inliers, invert=True)

    return planes, remaining, notes


def _axis_from_vector(v: np.ndarray) -> str:
    # Choose closest axis for an approximate alignment to X/Y/Z
    v = v / (np.linalg.norm(v) + 1e-12)
    axes = {"X": np.array([1, 0, 0.0]), "Y": np.array([0, 1, 0.0]), "Z": np.array([0, 0, 1.0])}
    best = max(axes.items(), key=lambda kv: abs(float(np.dot(v, kv[1]))))
    return best[0]


def _project_uv(points: np.ndarray, axis: str) -> np.ndarray:
    # Drop axis coordinate -> UV
    if axis == "X":
        return points[:, [1, 2]]
    if axis == "Y":
        return points[:, [0, 2]]
    return points[:, [0, 1]]  # Z


def _ransac_circle_uv(
    uv: np.ndarray,
    rng: np.random.RandomState,
    iters: int = 1200,
    dist_thresh: float = 0.35,
    min_inliers: int = 1200,
    radius_range: Optional[Tuple[float, float]] = None,
) -> Optional[Tuple[np.ndarray, float, np.ndarray]]:
    """
    RANSAC circle fit in 2D.
    Returns (center(2,), radius, inlier_mask)
    """
    n = uv.shape[0]
    if n < 3000:
        return None

    best_inliers = 0
    best = None

    # Precompute for speed
    idxs = np.arange(n)

    for _ in range(iters):
        # sample 3 non-collinear points
        i1, i2, i3 = rng.choice(idxs, 3, replace=False)
        p1, p2, p3 = uv[i1], uv[i2], uv[i3]

        # Compute circumcenter
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        det = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
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
        inliers = np.abs(d - r) <= dist_thresh
        cnt = int(inliers.sum())
        if cnt > best_inliers:
            best_inliers = cnt
            best = (center, r, inliers)

    if best is None or best_inliers < min_inliers:
        return None
    return best


def fit_primitives_open3d(
    mesh_path: str,
    voxel: float = 0.4,
    n_points: int = 70000,
    max_planes: int = 3,
    max_cylinders: int = 6,
    seed: int = 42,
) -> PrimitiveFitO3DResult:
    """
    Open3D-driven primitive fitting:
    - planes: via segment_plane (built-in RANSAC)
    - cylinders: via custom 2D circle RANSAC on UV projections, axis chosen by dominant plane/thin dimension
    """
    _require_o3d()
    rng = np.random.RandomState(seed)
    pcd = _load_mesh_as_pcd(mesh_path, n_points=n_points, voxel=voxel)
    L, W, H = _aabb_dims(pcd)
    notes: List[str] = [f"AABB dims: L={L:.2f}, W={W:.2f}, H={H:.2f} (scaled units)"]

    # Plane segmentation
    planes, rem, plane_notes = _dominant_planes(
        pcd,
        max_planes=max_planes,
        distance_threshold=max(0.2, voxel * 0.8),
        num_iterations=1200,
        min_inliers=max(1500, int(0.03 * len(pcd.points))),
    )
    notes.extend(plane_notes)

    # Determine likely hole axis:
    # Heuristic: smallest AABB axis is thickness -> holes likely along that axis
    dims = np.array([L, W, H], dtype=float)
    thin_axis_idx = int(np.argmin(dims))
    axis = ["X", "Y", "Z"][thin_axis_idx]
    notes.append(f"Chosen primary cylinder axis: {axis} (thin axis heuristic)")

    # Candidate points for cylinder detection:
    # Use remaining points after plane removal to emphasize edges/holes
    pts = np.asarray(rem.points)
    if pts.shape[0] < 5000:
        pts = np.asarray(pcd.points)  # fallback to all points

    uv = _project_uv(pts, axis=axis)

    # Set radius range relative to part size to avoid absurd circles
    rmax = 0.45 * float(np.max(dims))
    rmin = max(0.6, 0.01 * float(np.max(dims)))

    cylinders: List[AxisCylinder] = []
    working_uv = uv.copy()
    working_pts = pts.copy()

    for k in range(max_cylinders):
        fit = _ransac_circle_uv(
            working_uv,
            rng,
            iters=1200,
            dist_thresh=max(0.25, voxel * 0.6),
            min_inliers=max(900, int(0.02 * len(working_uv))),
            radius_range=(rmin, rmax),
        )
        if fit is None:
            break

        center, radius, inlier_mask = fit
        inl = int(inlier_mask.sum())
        cylinders.append(AxisCylinder(axis=axis, radius=float(radius), center_uv=(float(center[0]), float(center[1])), inliers=inl))
        notes.append(f"Cylinder {k}: axis={axis}, r={radius:.2f}, inliers={inl}")

        # Remove inliers to find additional circles
        keep = ~inlier_mask
        if int(keep.sum()) < 4000:
            break
        working_uv = working_uv[keep]
        working_pts = working_pts[keep]

    if not cylinders:
        notes.append("No cylinders found with Open3D RANSAC; consider providing a cleaner image, more points, or scaling.")

    aabb = pcd.get_axis_aligned_bounding_box()
    aabb_center = aabb.get_center()
    bbox_center = (float(aabb_center[0]), float(aabb_center[1]), float(aabb_center[2]))
    return PrimitiveFitO3DResult(
        bbox_LWH=(L, W, H),
        bbox_center=bbox_center,
        planes=planes,
        cylinders=cylinders,
        notes=notes,
    )
