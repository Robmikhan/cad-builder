# services/cad/exporters.py
from __future__ import annotations

from pathlib import Path
from typing import Any
import traceback

import cadquery as cq
from cadquery import exporters


class ExportError(RuntimeError):
    pass


def _exec_cadquery_source(source_code: str) -> cq.Workplane:
    """
    Execute CadQuery Python source that must define a variable named `result`.
    Returns `result` as a CadQuery object.
    """
    glb: dict[str, Any] = {}
    loc: dict[str, Any] = {}

    try:
        exec(source_code, glb, loc)
    except Exception as e:
        raise ExportError(f"CAD script execution failed: {e}\n{traceback.format_exc()}")

    obj = loc.get("result") or glb.get("result")
    if obj is None:
        raise ExportError("CAD script did not define `result`.")

    # Accept both Workplane and Shape-like; normalize to Workplane when possible
    if isinstance(obj, cq.Workplane):
        return obj

    # Some scripts may set result to a Shape; wrap it.
    try:
        return cq.Workplane("XY").newObject([obj])
    except Exception as e:
        raise ExportError(f"`result` is not a valid CadQuery object: {e}")


def export_step_from_cadquery_source(source_code: str, step_out_path: str) -> None:
    """
    Export STEP from CadQuery source. Raises ExportError on failure.
    """
    wp = _exec_cadquery_source(source_code)

    out = Path(step_out_path)
    out.parent.mkdir(parents=True, exist_ok=True)

    # exporters.export works with Workplane or Shape
    try:
        exporters.export(wp, str(out), exportType="STEP")
    except TypeError:
        # Older cadquery versions sometimes omit exportType kwarg
        exporters.export(wp, str(out))
    except Exception as e:
        raise ExportError(f"STEP export failed: {e}\n{traceback.format_exc()}")


def export_stl_from_cadquery_source(source_code: str, stl_out_path: str) -> None:
    wp = _exec_cadquery_source(source_code)
    out = Path(stl_out_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        exporters.export(wp, str(out), exportType="STL")
    except TypeError:
        exporters.export(wp, str(out))
