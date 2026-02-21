import json
import os
from pathlib import Path
from typing import Optional

class LocalQueue:
    """
    Simple file-backed queue:
      data/queue.json contains list of job_ids.
    Replaceable with Redis/Celery later.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.qfile = Path(data_dir) / "queue.json"
        os.makedirs(Path(data_dir), exist_ok=True)
        if not self.qfile.exists():
            self.qfile.write_text("[]", encoding="utf-8")

    def enqueue(self, job_id: str) -> None:
        items = json.loads(self.qfile.read_text(encoding="utf-8"))
        items.append(job_id)
        self.qfile.write_text(json.dumps(items), encoding="utf-8")

    def dequeue(self) -> Optional[str]:
        items = json.loads(self.qfile.read_text(encoding="utf-8"))
        if not items:
            return None
        job_id = items.pop(0)
        self.qfile.write_text(json.dumps(items), encoding="utf-8")
        return job_id
