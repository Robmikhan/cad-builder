import logging
import os
import time
from services.workers.queue import LocalQueue
from services.db.repo import Repo
from services.pipelines.run_pipeline import run_job_pipeline

_log = logging.getLogger(__name__)

def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    q = LocalQueue(data_dir)
    repo = Repo(data_dir)
    sleep_sec = 1.0

    _log.info("Worker started, polling %s", q.qfile)

    while True:
        job_id = q.dequeue()
        if not job_id:
            time.sleep(sleep_sec)
            continue
        _log.info("Processing job %s", job_id)
        try:
            run_job_pipeline(job_id, repo)
            _log.info("Job %s finished", job_id)
        except Exception:
            _log.exception("Unhandled error processing job %s (pipeline may have already marked it FAILED)", job_id)

if __name__ == "__main__":
    main()
