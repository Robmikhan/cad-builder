from services.validation.schemas import validate_part_spec

def test_part_spec_schema_minimal():
    validate_part_spec({
        "part_name": "x",
        "mode": "PROMPT",
        "units": "mm",
        "tolerance_mm": 0.2
    })
