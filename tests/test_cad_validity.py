from services.cad.cadquery_runner import make_parametric_block, run_cadquery_safely

def test_cadquery_exec():
    prog = make_parametric_block(10, 10, 10, "mm")
    ok, issues = run_cadquery_safely(prog["source"])
    assert ok, issues
