"""
Server-Sent Events (SSE) endpoint for real-time pipeline progress.
Client connects to /jobs/{job_id}/stream and receives events as they happen.
"""
from __future__ import annotations
import asyncio
import json
import os
from pathlib import Path
from fastapi import APIRouter
from starlette.responses import StreamingResponse

router = APIRouter()


@router.get("/{job_id}/stream")
async def stream_events(job_id: str):
    """SSE endpoint — streams pipeline events in real time until job completes."""
    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    events_path = Path(data_dir) / "outputs" / job_id / "events.jsonl"
    job_path = Path(data_dir) / "outputs" / job_id / "job.json"

    async def event_generator():
        seen = 0
        while True:
            # Read new events
            if events_path.exists():
                lines = events_path.read_text(encoding="utf-8").strip().splitlines()
                for line in lines[seen:]:
                    if line.strip():
                        yield f"data: {line}\n\n"
                        seen = len(lines)

            # Check if job is done
            if job_path.exists():
                try:
                    job = json.loads(job_path.read_text(encoding="utf-8"))
                    status = job.get("status", "")
                    if status in ("DONE", "FAILED"):
                        yield f"data: {json.dumps({'event_type': 'stream_end', 'status': status})}\n\n"
                        return
                except (json.JSONDecodeError, OSError):
                    pass

            await asyncio.sleep(1.0)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
