python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -U pip wheel
pip install -e .
Write-Host "✅ Setup complete. Optional: install FreeCAD for STEP export."
