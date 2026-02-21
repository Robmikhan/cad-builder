from __future__ import annotations
from dataclasses import dataclass
from huggingface_hub import snapshot_download
from pathlib import Path

@dataclass
class HFModelRef:
    repo_id: str
    revision: str
    local_dir: str

def download(ref: HFModelRef) -> str:
    Path(ref.local_dir).mkdir(parents=True, exist_ok=True)
    snapshot_download(
        repo_id=ref.repo_id,
        revision=ref.revision,
        local_dir=ref.local_dir,
        local_dir_use_symlinks=False
    )
    return ref.local_dir
