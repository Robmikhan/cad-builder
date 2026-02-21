import json
from pathlib import Path
from jsonschema import Draft202012Validator

def _load_schema(name: str) -> dict:
    p = Path("schemas") / name
    return json.loads(p.read_text(encoding="utf-8"))

_PART_SPEC = _load_schema("part_spec.schema.json")
_JOB = _load_schema("job.schema.json")
_CAD = _load_schema("cad_program.schema.json")
_REPORT = _load_schema("validation_report.schema.json")

def validate_part_spec(spec: dict) -> None:
    Draft202012Validator(_PART_SPEC).validate(spec)

def validate_job(job: dict) -> None:
    Draft202012Validator(_JOB).validate(job)

def validate_cad_program(cad_prog: dict) -> None:
    Draft202012Validator(_CAD).validate(cad_prog)

def validate_validation_report(report: dict) -> None:
    Draft202012Validator(_REPORT).validate(report)
