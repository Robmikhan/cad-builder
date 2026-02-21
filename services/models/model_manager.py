from __future__ import annotations
import os
import yaml
from pathlib import Path
from services.models.hf_downloader import HFModelRef, download
from services.models.versioning import write_manifest

class ModelManager:
    def __init__(self):
        self.cfg = yaml.safe_load(Path("configs/models.yaml").read_text(encoding="utf-8"))
        self.cache_dir = self.cfg["defaults"]["cache_dir"]

    def status(self) -> dict:
        models = self._flatten_models()
        for m in models:
            local_dir = self._local_dir_for(m)
            m["local_dir"] = local_dir
            m["available"] = Path(local_dir).exists() and any(Path(local_dir).iterdir()) if Path(local_dir).exists() else False
        return {"models": models}

    def snapshot_manifest(self) -> dict:
        s = self.status()
        # Strip large fields
        for m in s["models"]:
            m.pop("available", None)
        return s

    def upgrade(self, policy_path: str) -> dict:
        # Minimal: download configured HF models; discovery/eval hooks live in services/eval
        st = self.status()
        for m in st["models"]:
            if m["provider"] == "huggingface":
                local_dir = self._local_dir_for(m)
                ref = HFModelRef(repo_id=m["source"], revision=m.get("revision","main"), local_dir=local_dir)
                try:
                    download(ref)
                except Exception:
                    # Some models require accepting license / auth; ignore but record.
                    pass
        write_manifest("data/cache/model_manifest.json", st)
        return st

    def _flatten_models(self) -> list[dict]:
        out = []
        # segmentation
        seg = self.cfg.get("segmentation", {}).get("primary")
        if seg:
            out.append(seg)
        # image->mesh candidates
        cand = self.cfg.get("reconstruction", {}).get("image_to_mesh", {}).get("candidates", [])
        out.extend(cand)
        # text/multiview->mesh candidates
        out.extend(self.cfg.get("reconstruction", {}).get("text_or_multiview_to_mesh", {}).get("candidates", []))
        # video->pcd
        v = self.cfg.get("reconstruction", {}).get("video_to_pointcloud")
        if v:
            out.append(v)
        # cad generation
        cg = self.cfg.get("cad_generation", {})
        for k in ["image_to_cad", "text_to_cad", "pointcloud_to_cad"]:
            if cg.get(k):
                out.append(cg[k])
        # kernel
        k = self.cfg.get("cad_kernel", {}).get("primary")
        if k:
            out.append(k)
        return out

    def _local_dir_for(self, m: dict) -> str:
        name = m["name"]
        return str(Path(self.cache_dir) / name)

if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["status", "upgrade"])
    p.add_argument("--policy", default="configs/upgrade_policy.yaml")
    args = p.parse_args()

    mm = ModelManager()
    if args.cmd == "status":
        print(mm.status())
    else:
        print(mm.upgrade(args.policy))
