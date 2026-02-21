from __future__ import annotations
import logging
from pathlib import Path

import numpy as np
from PIL import Image

_log = logging.getLogger(__name__)


def _remove_background(image_path: str, out_path: str) -> str:
    """Remove background using rembg, save as RGBA PNG, return path."""
    import rembg

    img = Image.open(image_path).convert("RGB")
    session = rembg.new_session()
    result = rembg.remove(np.array(img), session=session)

    # Convert RGBA result to RGB with gray background (ideal for TripoSR)
    rgba = np.array(result, dtype=np.float32) / 255.0
    rgb = rgba[:, :, :3] * rgba[:, :, 3:4] + (1 - rgba[:, :, 3:4]) * 0.5
    clean_img = Image.fromarray((rgb * 255.0).astype(np.uint8))
    clean_img.save(out_path)
    return out_path


def step_02_segment(job: dict, ctx: dict, repo):
    """Remove background from input images using rembg for cleaner mesh reconstruction."""
    inputs = job["part_spec"].get("inputs") or {}
    image_paths = inputs.get("image_paths") or []
    if not image_paths:
        repo.event(job["job_id"], "segment_skipped", {"note": "No image_paths in part_spec."})
        return ctx

    out_dir = Path(ctx["out_dir"])
    clean_dir = out_dir / "segmented"
    clean_dir.mkdir(parents=True, exist_ok=True)

    cleaned = []
    for i, img_path in enumerate(image_paths):
        clean_path = str(clean_dir / f"clean_{i}.png")
        try:
            _remove_background(img_path, clean_path)
            cleaned.append(clean_path)
            _log.info("Background removed: %s -> %s", img_path, clean_path)
        except Exception as e:
            _log.warning("Background removal failed for %s: %s — using original", img_path, e)
            cleaned.append(img_path)

    ctx["segmented_images"] = cleaned
    repo.event(job["job_id"], "segment_ok", {"cleaned_images": len(cleaned)})
    return ctx
