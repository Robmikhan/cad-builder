import os
from services.workers.queue import LocalQueue
from services.db.repo import Repo

def get_data_dir() -> str:
    return os.getenv("CAD_AGENT_DATA_DIR", "data")

def get_queue() -> LocalQueue:
    return LocalQueue(get_data_dir())

def get_repo() -> Repo:
    return Repo(get_data_dir())
