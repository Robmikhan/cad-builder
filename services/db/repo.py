from __future__ import annotations
import json
import logging
import os
from pathlib import Path
from datetime import datetime, timezone
import requests

_log = logging.getLogger(__name__)

class Repo:
    """
    Dual-mode persistence:
    - If SUPABASE_URL + SUPABASE_SERVICE_ROLE_KEY are set: write to Supabase tables + optional Storage upload.
    - Else: write to local filesystem in data/outputs/<job_id>/.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.supabase_url = os.getenv("SUPABASE_URL", "").strip()
        self.supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
        self.bucket = os.getenv("SUPABASE_BUCKET", "cad-bundles").strip()

    def _job_path(self, job_id: str) -> Path:
        p = Path(self.data_dir) / "outputs" / job_id / "job.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        return p

    def save_job(self, job: dict) -> None:
        # Local
        self._job_path(job["job_id"]).write_text(json.dumps(job, indent=2), encoding="utf-8")

        # Supabase (optional)
        if self._sb_enabled():
            self._sb_upsert("jobs", {
                "job_id": job["job_id"],
                "status": job["status"],
                "created_at": job["created_at"],
                "part_spec": job["part_spec"],
                "artifacts": job.get("artifacts", {}),
                "metrics": job.get("metrics", {}),
                "error": job.get("error","")
            })

    def load_job(self, job_id: str) -> dict | None:
        p = self._job_path(job_id)
        if p.exists():
            return json.loads(p.read_text(encoding="utf-8"))
        # Supabase read optional (not required for local-first)
        return None

    def list_jobs(self) -> list[dict]:
        outputs = Path(self.data_dir) / "outputs"
        if not outputs.exists():
            return []
        jobs = []
        for d in sorted(outputs.iterdir(), reverse=True):
            jf = d / "job.json"
            if jf.exists():
                try:
                    jobs.append(json.loads(jf.read_text(encoding="utf-8")))
                except (json.JSONDecodeError, OSError) as e:
                    _log.warning("Skipping corrupted job file %s: %s", jf, e)
        return jobs

    def load_events(self, job_id: str) -> list[dict]:
        p = Path(self.data_dir) / "outputs" / job_id / "events.jsonl"
        if not p.exists():
            return []
        events = []
        for line in p.read_text(encoding="utf-8").strip().splitlines():
            if line.strip():
                events.append(json.loads(line))
        return events

    def save_model_manifest(self, job_id: str, manifest: dict) -> None:
        # local file
        out_dir = Path(self.data_dir) / "outputs" / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "model_manifest.json"
        p.write_text(json.dumps(manifest, indent=2), encoding="utf-8")

        if self._sb_enabled():
            self._sb_upsert("model_manifests", {"job_id": job_id, "manifest": manifest})

    def event(self, job_id: str, event_type: str, payload: dict) -> None:
        # local append
        out_dir = Path(self.data_dir) / "outputs" / job_id
        out_dir.mkdir(parents=True, exist_ok=True)
        p = out_dir / "events.jsonl"
        line = json.dumps({
            "ts": datetime.now(timezone.utc).isoformat(),
            "job_id": job_id,
            "event_type": event_type,
            "payload": payload
        })
        with p.open("a", encoding="utf-8") as f:
            f.write(line + "\n")

        if self._sb_enabled():
            self._sb_insert("job_events", {
                "job_id": job_id,
                "event_type": event_type,
                "payload": payload
            })

    def upload_bundle_if_configured(self, job_id: str, bundle_path: str) -> None:
        if not self._sb_enabled():
            return
        # Optional: Supabase Storage upload via REST.
        # Many teams prefer using supabase-py; we keep it dependency-light here.
        # This method is a hook; implement if you want Storage in v1.
        return

    def _sb_enabled(self) -> bool:
        return bool(self.supabase_url and self.supabase_key)

    def _sb_headers(self) -> dict:
        return {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }

    def _sb_upsert(self, table: str, row: dict) -> None:
        url = f"{self.supabase_url}/rest/v1/{table}"
        # Upsert via POST with Prefer header
        headers = self._sb_headers()
        headers["Prefer"] = "resolution=merge-duplicates"
        r = requests.post(url, headers=headers, data=json.dumps(row))
        r.raise_for_status()

    def _sb_insert(self, table: str, row: dict) -> None:
        url = f"{self.supabase_url}/rest/v1/{table}"
        headers = self._sb_headers()
        r = requests.post(url, headers=headers, data=json.dumps(row))
        r.raise_for_status()
