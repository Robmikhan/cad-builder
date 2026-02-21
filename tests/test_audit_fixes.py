"""Tests for the deep-audit fixes: queue locking, bundle subdirs, list_jobs robustness, etc."""
import json
import os
import zipfile
from pathlib import Path
from unittest.mock import MagicMock

import pytest


# --- Queue locking tests ---

def test_queue_enqueue_dequeue(tmp_path):
    from services.workers.queue import LocalQueue
    q = LocalQueue(str(tmp_path))
    q.enqueue("job-1")
    q.enqueue("job-2")
    assert q.dequeue() == "job-1"
    assert q.dequeue() == "job-2"
    assert q.dequeue() is None


def test_queue_lock_prevents_stale_lockfile(tmp_path):
    """If a stale .lock file exists, the queue should still work after timeout."""
    from services.workers.queue import LocalQueue
    q = LocalQueue(str(tmp_path))
    # Simulate a stale lock
    (tmp_path / "queue.lock").write_text("stale", encoding="utf-8")
    # Should still work (timeout forces removal of stale lock)
    q.enqueue("job-stale")
    assert q.dequeue() == "job-stale"


# --- Bundle subdirectory tests ---

def test_bundle_includes_subdirectory_files(tmp_path):
    from services.pipelines.steps.step_11_bundle_and_report import step_11_bundle_and_report

    out_dir = tmp_path / "output"
    out_dir.mkdir()
    # Top-level file
    (out_dir / "cad_program.json").write_text('{"test": true}', encoding="utf-8")
    # Subdirectory file (like mesh/)
    mesh_dir = out_dir / "mesh"
    mesh_dir.mkdir()
    (mesh_dir / "model.glb").write_bytes(b"fake-glb-data")

    job = {
        "job_id": "test-bundle-123",
        "part_spec": {"part_name": "test", "mode": "PROMPT", "units": "mm", "tolerance_mm": 0.2},
        "artifacts": {},
        "status": "DONE",
        "created_at": "2025-01-01T00:00:00Z",
        "metrics": {},
        "error": "",
    }
    ctx = {"out_dir": str(out_dir)}
    repo = MagicMock()

    step_11_bundle_and_report(job, ctx, repo)

    bundle_path = Path(job["artifacts"]["bundle_path"])
    assert bundle_path.exists()

    with zipfile.ZipFile(bundle_path, "r") as z:
        names = z.namelist()
        assert "cad_program.json" in names
        # The subdirectory file should be included with relative path
        assert "mesh/model.glb" in names or "mesh\\model.glb" in names


# --- list_jobs robustness tests ---

def test_list_jobs_skips_corrupted(tmp_path):
    from services.db.repo import Repo
    repo = Repo(str(tmp_path))

    # Create a valid job
    good_dir = tmp_path / "outputs" / "good-job"
    good_dir.mkdir(parents=True)
    (good_dir / "job.json").write_text(
        json.dumps({"job_id": "good-job", "status": "DONE"}),
        encoding="utf-8",
    )

    # Create a corrupted job
    bad_dir = tmp_path / "outputs" / "bad-job"
    bad_dir.mkdir(parents=True)
    (bad_dir / "job.json").write_text("{invalid json", encoding="utf-8")

    jobs = repo.list_jobs()
    assert len(jobs) == 1
    assert jobs[0]["job_id"] == "good-job"


def test_list_jobs_empty(tmp_path):
    from services.db.repo import Repo
    repo = Repo(str(tmp_path))
    assert repo.list_jobs() == []


def test_load_events_empty(tmp_path):
    from services.db.repo import Repo
    repo = Repo(str(tmp_path))
    assert repo.load_events("nonexistent") == []


# --- run_pipeline unknown mode ---

def test_run_pipeline_unknown_mode(tmp_path):
    from services.db.repo import Repo
    from services.pipelines.run_pipeline import run_job_pipeline

    os.environ["CAD_AGENT_DATA_DIR"] = str(tmp_path)
    repo = Repo(str(tmp_path))

    job = {
        "job_id": "bad-mode-job",
        "status": "QUEUED",
        "created_at": "2025-01-01T00:00:00Z",
        "part_spec": {"part_name": "x", "mode": "INVALID_MODE", "units": "mm", "tolerance_mm": 0.2},
        "artifacts": {},
        "metrics": {"runtime_sec": 0.0, "num_iterations": 0},
        "error": "",
    }
    repo.save_job(job)

    run_job_pipeline("bad-mode-job", repo)

    result = repo.load_job("bad-mode-job")
    assert result["status"] == "FAILED"
    assert "Unknown pipeline mode" in result["error"]


# --- VIDEO pipeline stubs raise NotImplementedError ---

def test_video_colmap_stub_raises():
    from services.pipelines.steps.step_04_video_recon_colmap import step_04_video_recon_colmap
    repo = MagicMock()
    with pytest.raises(NotImplementedError, match="COLMAP"):
        step_04_video_recon_colmap({"job_id": "x"}, {}, repo)


def test_pointcloud_to_cad_stub_raises():
    from services.pipelines.steps.step_06_pointcloud_to_cad import step_06_pointcloud_to_cad
    repo = MagicMock()
    with pytest.raises(NotImplementedError, match="Point2CAD"):
        step_06_pointcloud_to_cad({"job_id": "x"}, {}, repo)
