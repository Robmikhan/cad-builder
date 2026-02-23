# CAD Builder — Auto-restart server + Cloudflare tunnel
# Run this script to start the API server and tunnel.
# Install as Windows startup task with: scripts/install_startup.ps1

$ErrorActionPreference = "SilentlyContinue"
$PROJECT = "C:\Users\robmi\CAD BUILDER"
$PYTHON = "$PROJECT\.venv\Scripts\python.exe"
$LOG_DIR = "$PROJECT\logs"

New-Item -ItemType Directory -Path $LOG_DIR -Force | Out-Null

function Write-Log($msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$ts  $msg" | Tee-Object -Append -FilePath "$LOG_DIR\startup.log"
}

# ── Start API Server ──
Write-Log "Starting CAD Builder API server..."
$apiJob = Start-Job -ScriptBlock {
    param($py, $proj, $logDir)
    while ($true) {
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "$ts  API server starting..." | Out-File -Append "$logDir\api.log"
        & $py -m uvicorn services.api.main:app --host 0.0.0.0 --port 8080 2>&1 |
            Out-File -Append "$logDir\api.log"
        "$ts  API server crashed — restarting in 5s..." | Out-File -Append "$logDir\api.log"
        Start-Sleep 5
    }
} -ArgumentList $PYTHON, $PROJECT, $LOG_DIR -WorkingDirectory $PROJECT

Write-Log "API server job started (ID: $($apiJob.Id))"

# Wait for API to be ready
Write-Log "Waiting for API to be ready..."
$ready = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep 2
    try {
        $r = Invoke-WebRequest -Uri "http://localhost:8080/api/health" -UseBasicParsing -TimeoutSec 3
        if ($r.StatusCode -eq 200) {
            $ready = $true
            break
        }
    } catch {}
}

if ($ready) {
    Write-Log "API server is healthy!"
} else {
    Write-Log "WARNING: API server not responding after 60s — starting tunnel anyway"
}

# ── Start Cloudflare Tunnel ──
Write-Log "Starting Cloudflare tunnel..."
$tunnelJob = Start-Job -ScriptBlock {
    param($logDir)
    while ($true) {
        $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        "$ts  Tunnel starting..." | Out-File -Append "$logDir\tunnel.log"
        cloudflared tunnel --url http://localhost:8080 2>&1 |
            Out-File -Append "$logDir\tunnel.log"
        "$ts  Tunnel crashed — restarting in 5s..." | Out-File -Append "$logDir\tunnel.log"
        Start-Sleep 5
    }
} -ArgumentList $LOG_DIR

Write-Log "Tunnel job started (ID: $($tunnelJob.Id))"

# Wait for tunnel URL
Start-Sleep 10
$tunnelUrl = Get-Content "$LOG_DIR\tunnel.log" -Tail 50 |
    Select-String "trycloudflare\.com" |
    ForEach-Object { ($_ -split "\s+")[-1] } |
    Select-Object -Last 1

if ($tunnelUrl) {
    Write-Log "PUBLIC URL: $tunnelUrl"
    Write-Host ""
    Write-Host "========================================" -ForegroundColor Green
    Write-Host "  CAD Builder is LIVE" -ForegroundColor Green
    Write-Host "  $tunnelUrl" -ForegroundColor Cyan
    Write-Host "========================================" -ForegroundColor Green
    Write-Host ""
} else {
    Write-Log "WARNING: Could not extract tunnel URL — check logs\tunnel.log"
}

Write-Log "Monitoring processes... (Ctrl+C to stop)"

# Keep running and monitor
while ($true) {
    Start-Sleep 30
    # Check API
    try {
        $null = Invoke-WebRequest -Uri "http://localhost:8080/api/health" -UseBasicParsing -TimeoutSec 5
    } catch {
        Write-Log "WARNING: API health check failed"
    }
}
