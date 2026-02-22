"""
File upload endpoint — accepts images and stores them in data/uploads/.
Returns the server-side path so the job can reference it.
"""
from __future__ import annotations
import os
import uuid
from pathlib import Path
from fastapi import APIRouter, UploadFile, File, HTTPException

router = APIRouter()

ALLOWED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".bmp", ".tiff"}
MAX_SIZE_MB = 20


@router.post("")
async def upload_file(file: UploadFile = File(...)):
    ext = Path(file.filename or "image.png").suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"Unsupported file type: {ext}. Allowed: {ALLOWED_EXTENSIONS}")

    data_dir = os.getenv("CAD_AGENT_DATA_DIR", "data")
    upload_dir = Path(data_dir) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    # Read file content
    content = await file.read()
    if len(content) > MAX_SIZE_MB * 1024 * 1024:
        raise HTTPException(413, f"File too large. Max {MAX_SIZE_MB}MB")

    # Save with unique name
    unique_name = f"{uuid.uuid4().hex[:12]}{ext}"
    save_path = upload_dir / unique_name
    save_path.write_bytes(content)

    return {
        "filename": file.filename,
        "path": str(save_path.resolve()),
        "size_bytes": len(content),
    }
