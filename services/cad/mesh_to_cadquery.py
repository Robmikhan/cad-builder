# services/cad/mesh_to_cadquery.py
from __future__ import annotations


def cadquery_from_mesh(mesh_path: str, units: str, max_cylinders: int = 6) -> dict:
    """
    Prefer Open3D RANSAC primitives if available; fallback to heuristic primitives.
    Output is a conservative parametric CadQuery model:
      - main box from AABB
      - cut holes (best-effort) aligned to an axis
    """
    try:
        from services.cad.primitive_fit_o3d import fit_primitives_open3d
        fit = fit_primitives_open3d(mesh_path, max_cylinders=max_cylinders)
        notes = fit.notes
        L, W, H = fit.bbox_LWH
        cylinders = fit.cylinders
        method = "open3d_ransac"
    except Exception as e:
        from services.cad.primitive_fit import fit_primitives
        fit2 = fit_primitives(mesh_path, max_cylinders=max_cylinders)
        notes = fit2.notes + [f"Open3D unavailable/failure: {e}"]
        L, W, H = fit2.bbox_LWH
        # Adapt cylinder structure
        cylinders = []
        for c in fit2.cylinders:
            cylinders.append({
                "axis": c.axis,
                "radius": c.radius,
                "center_uv": (c.center[0], c.center[1]),
                "inliers": 0
            })
        method = "heuristic"

    cuts_src = []
    params = {"L": float(L), "W": float(W), "H": float(H)}

    for i, c in enumerate(cylinders):
        if isinstance(c, dict):
            axis = c["axis"]
            radius = float(c["radius"])
            cu, cv = c["center_uv"]
        else:
            axis = c.axis
            radius = float(c.radius)
            cu, cv = c.center_uv

        # CadQuery hole() cuts normal to a selected face/workplane
        if axis == "Z":
            wp = "XY"
            cuts_src.append(
                f"# Hole {i} (axis=Z)\n"
                f"r{i} = {radius}\n"
                f"x{i} = {cu}\n"
                f"y{i} = {cv}\n"
                f'result = result.faces("{wp}").workplane().center(x{i}, y{i}).hole(2*r{i})'
            )
        elif axis == "Y":
            wp = "XZ"
            cuts_src.append(
                f"# Hole {i} (axis=Y)\n"
                f"r{i} = {radius}\n"
                f"x{i} = {cu}\n"
                f"z{i} = {cv}\n"
                f'result = result.faces("{wp}").workplane().center(x{i}, z{i}).hole(2*r{i})'
            )
        else:  # X
            wp = "YZ"
            cuts_src.append(
                f"# Hole {i} (axis=X)\n"
                f"r{i} = {radius}\n"
                f"y{i} = {cu}\n"
                f"z{i} = {cv}\n"
                f'result = result.faces("{wp}").workplane().center(y{i}, z{i}).hole(2*r{i})'
            )

        params[f"hole_{i}_diameter"] = 2.0 * radius

    notes_str = " | ".join([n.replace("\n", " ") for n in notes])
    cuts_block = "\n\n".join(cuts_src)

    src = (
        "import cadquery as cq\n"
        "\n"
        "# AABB-derived parameters (units after scaling)\n"
        f"L = {float(L)}\n"
        f"W = {float(W)}\n"
        f"H = {float(H)}\n"
        "\n"
        'result = cq.Workplane("XY").box(L, W, H)\n'
        "\n"
        f"# Fit method: {method}\n"
        f"# Notes: {notes_str}\n"
    )
    if cuts_block:
        src += "\n" + cuts_block + "\n"

    return {
        "language": "CADQUERY_PY",
        "source": src.strip(),
        "parameters": params,
        "exports": ["STEP", "STL"]
    }
