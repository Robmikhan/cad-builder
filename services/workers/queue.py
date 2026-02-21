import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Optional

class LocalQueue:
    """
    Simple file-backed queue with file locking:
      data/queue.json contains list of job_ids.
    Replaceable with Redis/Celery later.
    """
    def __init__(self, data_dir: str):
        self.data_dir = data_dir
        self.qfile = Path(data_dir) / "queue.json"
        self._lockfile = Path(data_dir) / "queue.lock"
        os.makedirs(Path(data_dir), exist_ok=True)
        if not self.qfile.exists():
            self.qfile.write_text("[]", encoding="utf-8")

    @contextmanager
    def _lock(self, timeout: float = 5.0):
        """Simple cross-platform file lock using a .lock file."""
        deadline = time.monotonic() + timeout
        while True:
            try:
                fd = os.open(str(self._lockfile), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break
            except FileExistsError:
                if time.monotonic() >= deadline:
                    # Stale lock — force remove and retry once
                    try:
                        os.remove(str(self._lockfile))
                    except OSError:
                        pass
                    continue
                time.sleep(0.05)
        try:
            yield
        finally:
            try:
                os.remove(str(self._lockfile))
            except OSError:
                pass

    def enqueue(self, job_id: str) -> None:
        with self._lock():
            items = json.loads(self.qfile.read_text(encoding="utf-8"))
            items.append(job_id)
            self.qfile.write_text(json.dumps(items), encoding="utf-8")

    def dequeue(self) -> Optional[str]:
        with self._lock():
            items = json.loads(self.qfile.read_text(encoding="utf-8"))
            if not items:
                return None
            job_id = items.pop(0)
            self.qfile.write_text(json.dumps(items), encoding="utf-8")
            return job_id
