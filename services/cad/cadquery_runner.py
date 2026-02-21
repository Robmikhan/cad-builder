from __future__ import annotations
from dataclasses import dataclass
from typing import Tuple, List
import traceback

def make_parametric_block(L: float, W: float, H: float, units: str) -> dict:
    """
    Creates a simple parametric CadQuery model program (as python code string).
    """
    src = f'''
import cadquery as cq

# Parameters
L = {L}
W = {W}
H = {H}

result = cq.Workplane("XY").box(L, W, H)

# Export variable must be named "result"
'''
    return {
        "language": "CADQUERY_PY",
        "source": src.strip(),
        "parameters": {"L": L, "W": W, "H": H},
        "exports": ["STEP", "STL"]
    }

def run_cadquery_safely(source_code: str) -> Tuple[bool, List[str]]:
    """
    Executes CadQuery code in a restricted-ish namespace.
    Returns (ok, issues).
    """
    try:
        glb = {}
        loc = {}
        exec(source_code, glb, loc)
        obj = loc.get("result") or glb.get("result")
        if obj is None:
            return False, ["No 'result' object produced by CAD script."]
        return True, []
    except Exception:
        return False, [traceback.format_exc()[:2000]]
