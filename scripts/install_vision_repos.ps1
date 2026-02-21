# Install vision model repos and dependencies for IMAGE pipeline on Windows
# Prerequisites: NVIDIA GPU, CUDA Toolkit, .venv with PyTorch CUDA
# Usage: .\.venv\Scripts\Activate.ps1; .\scripts\install_vision_repos.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== CAD Builder — Vision Repos Setup ===" -ForegroundColor Cyan

# 1. Check prerequisites
Write-Host "`n[1/5] Checking prerequisites..."
.\.venv\Scripts\python -c "import torch; assert torch.cuda.is_available(), 'CUDA not available'; print(f'  PyTorch {torch.__version__} with {torch.cuda.get_device_name(0)}')"
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyTorch CUDA not available. Run:" -ForegroundColor Red
    Write-Host "  .venv\Scripts\pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121"
    exit 1
}

# 2. Create repos directory
New-Item -ItemType Directory -Path "data\cache\repos" -Force | Out-Null

# 3. Clone TripoSR
Write-Host "`n[2/5] Cloning TripoSR..."
if (-not (Test-Path "data\cache\repos\TripoSR")) {
    git clone https://github.com/VAST-AI-Research/TripoSR data\cache\repos\TripoSR
} else {
    Write-Host "  Already exists, skipping."
}

# 4. Clone SF3D
Write-Host "`n[3/5] Cloning Stable Fast 3D..."
if (-not (Test-Path "data\cache\repos\stable-fast-3d")) {
    git clone https://github.com/Stability-AI/stable-fast-3d data\cache\repos\stable-fast-3d
} else {
    Write-Host "  Already exists, skipping."
}

# 5. Install Python dependencies
Write-Host "`n[4/5] Installing Python dependencies..."
.\.venv\Scripts\pip install omegaconf einops transformers huggingface-hub rembg onnxruntime-gpu imageio[ffmpeg] xatlas moderngl PyMCubes

# 6. Patch TripoSR to use PyMCubes fallback (avoids torchmcubes CUDA compile)
Write-Host "`n[5/5] Patching TripoSR for PyMCubes fallback..."
$isosurface = "data\cache\repos\TripoSR\tsr\models\isosurface.py"
$content = Get-Content $isosurface -Raw
if ($content -notmatch "mcubes as _mcubes") {
    $content = $content -replace "from torchmcubes import marching_cubes", @"
try:
    from torchmcubes import marching_cubes
except ImportError:
    import mcubes as _mcubes
    import numpy as np
    import torch

    def marching_cubes(vol, threshold):
        if torch.is_tensor(vol):
            vol = vol.detach().cpu().numpy()
        verts, faces = _mcubes.marching_cubes(vol, threshold)
        return torch.from_numpy(verts.astype(np.float32)), torch.from_numpy(faces.astype(np.int64))
"@
    Set-Content $isosurface $content -Encoding UTF8
    Write-Host "  Patched isosurface.py with PyMCubes fallback."
} else {
    Write-Host "  Already patched."
}

Write-Host "`n=== Setup complete ===" -ForegroundColor Green
Write-Host "Model weights will auto-download on first run (~1.5GB for TripoSR)."
Write-Host "Run GPU check:  .venv\Scripts\python scripts\check_gpu.py"
Write-Host "Run GPU test:   .venv\Scripts\python scripts\test_gpu_pipeline.py"
