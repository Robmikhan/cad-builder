from __future__ import annotations
import builtins
import os
import threading
import traceback
from typing import Tuple, List

_EXEC_TIMEOUT = int(os.getenv("CAD_AGENT_CAD_TIMEOUT_SEC", "30"))

# Whitelist of allowed builtins for sandboxed execution
_SAFE_BUILTINS = {
    k: getattr(builtins, k) for k in [
        "abs", "all", "any", "bool", "dict", "enumerate", "filter", "float",
        "frozenset", "hasattr", "int", "isinstance", "issubclass", "iter",
        "len", "list", "map", "max", "min", "next", "print", "property",
        "range", "repr", "reversed", "round", "set", "slice", "sorted",
        "str", "sum", "tuple", "type", "zip", "True", "False", "None",
        "ValueError", "TypeError", "RuntimeError", "Exception",
        "StopIteration", "KeyError", "IndexError", "AttributeError",
    ] if hasattr(builtins, k)
}

# Only allow importing cadquery and math
_ALLOWED_MODULES = {"cadquery", "math"}


def _safe_import(name, *args, **kwargs):
    if name not in _ALLOWED_MODULES:
        raise ImportError(f"Import of '{name}' is not allowed in CAD sandbox. Only {_ALLOWED_MODULES} are permitted.")
    return __builtins__["__import__"](name, *args, **kwargs) if isinstance(__builtins__, dict) else builtins.__import__(name, *args, **kwargs)


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
    Executes CadQuery code in a sandboxed namespace with:
    - Restricted builtins (no os, sys, subprocess, open, etc.)
    - Only cadquery and math imports allowed
    - Timeout protection via threading
    Returns (ok, issues).
    """
    result_container = {"ok": False, "issues": [], "done": False}

    def _exec():
        try:
            sandbox_globals = {
                "__builtins__": {**_SAFE_BUILTINS, "__import__": _safe_import},
            }
            sandbox_locals = {}
            exec(source_code, sandbox_globals, sandbox_locals)
            obj = sandbox_locals.get("result") or sandbox_globals.get("result")
            if obj is None:
                result_container["issues"] = ["No 'result' object produced by CAD script."]
            else:
                result_container["ok"] = True
        except Exception:
            result_container["issues"] = [traceback.format_exc()[:2000]]
        finally:
            result_container["done"] = True

    t = threading.Thread(target=_exec, daemon=True)
    t.start()
    t.join(timeout=_EXEC_TIMEOUT)

    if not result_container["done"]:
        return False, [f"CAD script execution timed out after {_EXEC_TIMEOUT}s"]

    return result_container["ok"], result_container["issues"]
