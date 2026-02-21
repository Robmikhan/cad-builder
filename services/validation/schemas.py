import json
from pathlib import Path
from jsonschema import Draft202012Validator
from referencing import Registry, Resource

def _schemas_dir() -> Path:
    return Path(__file__).resolve().parent.parent.parent / "schemas"

def _load_schema(name: str) -> dict:
    p = _schemas_dir() / name
    return json.loads(p.read_text(encoding="utf-8"))

_PART_SPEC = _load_schema("part_spec.schema.json")
_JOB = _load_schema("job.schema.json")
_CAD = _load_schema("cad_program.schema.json")
_REPORT = _load_schema("validation_report.schema.json")

# Build a registry so $ref between schemas resolves correctly
_REGISTRY = Registry().with_resources([
    ("part_spec.schema.json", Resource.from_contents(_PART_SPEC)),
    ("job.schema.json", Resource.from_contents(_JOB)),
    ("cad_program.schema.json", Resource.from_contents(_CAD)),
    ("validation_report.schema.json", Resource.from_contents(_REPORT)),
])

def validate_part_spec(spec: dict) -> None:
    Draft202012Validator(_PART_SPEC, registry=_REGISTRY).validate(spec)

def validate_job(job: dict) -> None:
    Draft202012Validator(_JOB, registry=_REGISTRY).validate(job)

def validate_cad_program(cad_prog: dict) -> None:
    Draft202012Validator(_CAD, registry=_REGISTRY).validate(cad_prog)

def validate_validation_report(report: dict) -> None:
    Draft202012Validator(_REPORT, registry=_REGISTRY).validate(report)
