from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime, timezone

def write_manifest(path: str, manifest: dict) -> None:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    manifest["generated_at"] = datetime.now(timezone.utc).isoformat()
    p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
