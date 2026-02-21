from pathlib import Path
import tempfile

from services.cad.cadquery_runner import make_parametric_block
from services.cad.exporters import export_step_from_cadquery_source


def test_step_export_creates_file():
    prog = make_parametric_block(10, 10, 10, "mm")
    with tempfile.TemporaryDirectory() as d:
        out = Path(d) / "x.step"
        export_step_from_cadquery_source(prog["source"], str(out))
        assert out.exists()
        assert out.stat().st_size > 1000
