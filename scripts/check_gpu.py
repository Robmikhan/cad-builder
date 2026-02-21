"""GPU diagnostic script — run to verify your setup is ready for vision models."""
import sys
import shutil

def main():
    print("=" * 60)
    print("  CAD Builder — GPU Diagnostic")
    print("=" * 60)

    errors = []

    # 1. Check nvidia-smi
    print("\n[1/5] NVIDIA Driver ...")
    if shutil.which("nvidia-smi"):
        import subprocess
        r = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"],
                           capture_output=True, text=True)
        if r.returncode == 0:
            print(f"  OK: {r.stdout.strip()}")
        else:
            errors.append("nvidia-smi failed")
            print(f"  FAIL: nvidia-smi returned error")
    else:
        errors.append("nvidia-smi not found")
        print("  FAIL: nvidia-smi not found. Install NVIDIA drivers.")

    # 2. Check nvcc
    print("\n[2/5] CUDA Toolkit (nvcc) ...")
    if shutil.which("nvcc"):
        import subprocess
        r = subprocess.run(["nvcc", "--version"], capture_output=True, text=True)
        for line in r.stdout.strip().splitlines():
            if "release" in line.lower():
                print(f"  OK: {line.strip()}")
                break
    else:
        errors.append("nvcc not found — CUDA Toolkit not installed or not in PATH")
        print("  FAIL: nvcc not found. Install CUDA Toolkit: winget install Nvidia.CUDA")

    # 3. Check PyTorch + CUDA
    print("\n[3/5] PyTorch CUDA ...")
    try:
        import torch
        if torch.cuda.is_available():
            print(f"  OK: PyTorch {torch.__version__}, GPU: {torch.cuda.get_device_name(0)}")
            print(f"      VRAM: {torch.cuda.get_device_properties(0).total_mem / 1e9:.1f} GB")
        else:
            errors.append("PyTorch installed but CUDA not available")
            print(f"  FAIL: PyTorch {torch.__version__} — CUDA not available")
    except ImportError:
        errors.append("PyTorch not installed")
        print("  FAIL: pip install torch --index-url https://download.pytorch.org/whl/cu121")

    # 4. Check vision repos
    print("\n[4/5] Vision model repos ...")
    from pathlib import Path
    project_root = Path(__file__).resolve().parent.parent
    sf3d_ok = (project_root / "data/cache/repos/stable-fast-3d/run.py").exists()
    triposr_ok = (project_root / "data/cache/repos/TripoSR/run.py").exists()
    print(f"  SF3D:    {'OK' if sf3d_ok else 'MISSING — git clone needed'}")
    print(f"  TripoSR: {'OK' if triposr_ok else 'MISSING — git clone needed'}")
    if not sf3d_ok:
        errors.append("SF3D repo not cloned")
    if not triposr_ok:
        errors.append("TripoSR repo not cloned")

    # 5. Check key deps
    print("\n[5/5] Key dependencies ...")
    deps = {
        "transformers": "transformers",
        "rembg": "rembg",
        "omegaconf": "omegaconf",
        "einops": "einops",
    }
    for name, pkg in deps.items():
        try:
            __import__(pkg)
            print(f"  {name}: OK")
        except ImportError:
            errors.append(f"{name} not installed")
            print(f"  {name}: MISSING")

    # Summary
    print("\n" + "=" * 60)
    if errors:
        print(f"  {len(errors)} ISSUE(S) FOUND:")
        for e in errors:
            print(f"    - {e}")
        print("=" * 60)
        return 1
    else:
        print("  ALL CHECKS PASSED — ready for GPU inference!")
        print("=" * 60)
        return 0

if __name__ == "__main__":
    sys.exit(main())
