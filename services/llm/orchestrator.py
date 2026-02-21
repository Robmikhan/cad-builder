"""
LLM orchestrator — powers smart CadQuery generation and repair.
Uses Ollama (local) by default. Set LLM_PROVIDER=ollama to enable.
Falls back gracefully if Ollama is not running.
"""
from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from typing import Optional

_log = logging.getLogger(__name__)
_PROMPTS_DIR = Path(__file__).parent / "prompts"


def enabled() -> bool:
    """Check if LLM is configured and reachable."""
    provider = os.getenv("LLM_PROVIDER", "ollama").lower()
    if provider == "none":
        return False
    if provider == "ollama":
        from services.llm.ollama_client import is_available
        return is_available()
    return False


def _load_prompt(name: str) -> str:
    p = _PROMPTS_DIR / f"{name}.md"
    if p.exists():
        return p.read_text(encoding="utf-8").strip()
    return ""


def generate_cadquery(part_spec: dict) -> Optional[dict]:
    """
    Use LLM to generate CadQuery code from a part specification.
    Returns a cad_program dict or None if LLM is not available.
    """
    if not enabled():
        _log.info("LLM not available — falling back to parametric block generator")
        return None

    from services.llm.ollama_client import generate, extract_code_block

    system = _load_prompt("system")
    dims = part_spec.get("dimensions") or {}
    dims_str = ", ".join(f"{k}={v}" for k, v in dims.items()) if dims else "not specified"
    materials = part_spec.get("materials") or {}
    mat_str = materials.get("material", "not specified")
    process_str = materials.get("process", "not specified")
    use_case = part_spec.get("use_case", "")
    constraints = part_spec.get("constraints") or {}

    prompt = f"""Generate CadQuery Python code for this part:

Part name: {part_spec.get('part_name', 'unnamed')}
Units: {part_spec.get('units', 'mm')}
Dimensions: {dims_str}
Material: {mat_str}
Manufacturing process: {process_str}
Use case / description: {use_case or 'general purpose part'}
Tolerance: {part_spec.get('tolerance_mm', 0.2)} mm
Must be parametric: {constraints.get('must_be_parametric', True)}
Symmetry hint: {constraints.get('symmetry_hint', 'NONE')}

RULES:
1. Use `import cadquery as cq` at the top
2. Store the final shape in a variable called `result`
3. Use named parameters (L, W, H, radius, etc.) at the top for easy editing
4. Keep it simple and manufacturable — prefer boxes, cylinders, fillets, chamfers, holes
5. Use `.box()`, `.cylinder()`, `.hole()`, `.fillet()`, `.chamfer()`, `.cut()`, `.union()` etc.
6. All dimensions in {part_spec.get('units', 'mm')}
7. Output ONLY the Python code, no explanations

Example format:
```python
import cadquery as cq

# Parameters
L = 40.0
W = 25.0
H = 12.0
hole_d = 5.0
fillet_r = 2.0

result = (
    cq.Workplane("XY")
    .box(L, W, H)
    .faces(">Z")
    .workplane()
    .hole(hole_d)
    .edges("|Z")
    .fillet(fillet_r)
)
```"""

    try:
        response = generate(prompt, system=system, temperature=0.2, max_tokens=2048)
        source = extract_code_block(response)

        if "import cadquery" not in source:
            source = "import cadquery as cq\n\n" + source
        if "result" not in source:
            _log.warning("LLM output missing 'result' variable, falling back")
            return None

        # Extract parameters from the source (simple heuristic: lines like `X = number`)
        params = {}
        for line in source.split("\n"):
            line = line.strip()
            if "=" in line and not line.startswith("#") and not line.startswith("result"):
                parts = line.split("=", 1)
                name = parts[0].strip()
                if name.isidentifier() and name != "cq":
                    try:
                        val = float(parts[1].strip().rstrip(","))
                        params[name] = val
                    except (ValueError, IndexError):
                        pass

        return {
            "language": "CADQUERY_PY",
            "source": source.strip(),
            "parameters": params,
            "exports": ["STEP", "STL"],
        }
    except Exception as e:
        _log.warning("LLM CadQuery generation failed: %s", e)
        return None


def repair_cadquery(source: str, error: str, part_spec: dict, max_attempts: int = 3) -> Optional[str]:
    """
    Use LLM to fix broken CadQuery code based on validation errors.
    Returns fixed source code or None if repair fails.
    """
    if not enabled():
        return None

    from services.llm.ollama_client import generate, extract_code_block

    system = _load_prompt("cad_repair")

    for attempt in range(max_attempts):
        prompt = f"""The following CadQuery code failed validation:

```python
{source}
```

Error:
{error}

Part name: {part_spec.get('part_name', '')}
Units: {part_spec.get('units', 'mm')}

Fix the code. Keep the same parameter names. Store the result in `result`.
Output ONLY the fixed Python code, no explanations."""

        try:
            response = generate(prompt, system=system, temperature=0.1, max_tokens=2048)
            fixed = extract_code_block(response)
            if "result" in fixed and "cadquery" in fixed:
                _log.info("LLM repair attempt %d: produced candidate", attempt + 1)
                return fixed.strip()
        except Exception as e:
            _log.warning("LLM repair attempt %d failed: %s", attempt + 1, e)

        # Use the error from this attempt for the next try
        error = f"Previous fix attempt also failed. Original error: {error}"

    return None
