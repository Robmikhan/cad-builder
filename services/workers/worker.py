import os
import time
from services.workers.queue import LocalQueue
from services.db.repo import Repo
from services.pipelines.run_pipeline import run_job_pipeline

def main():
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    q = LocalQueue(data_dir)
    repo = Repo(data_dir)
    sleep_sec = 1.0

    while True:
        job_id = q.dequeue()
        if not job_id:
            time.sleep(sleep_sec)
            continue
        run_job_pipeline(job_id, repo)

if __name__ == "__main__":
    main()
