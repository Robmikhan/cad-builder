# Install CAD Builder as a Windows startup task
# Run this ONCE as Administrator to make the server + tunnel auto-start on boot

$TaskName = "CADBuilder"
$ProjectDir = "C:\Users\robmi\CAD BUILDER"
$Script = "$ProjectDir\scripts\start_server.ps1"

# Remove existing task if present
Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue

# Create the task
$action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -ExecutionPolicy Bypass -File `"$Script`"" `
    -WorkingDirectory $ProjectDir

$trigger = New-ScheduledTaskTrigger -AtLogon
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 3 `
    -RestartInterval (New-TimeSpan -Minutes 1)

$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Highest

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "CAD Builder API server + Cloudflare tunnel"

Write-Host ""
Write-Host "Installed '$TaskName' scheduled task." -ForegroundColor Green
Write-Host "The server + tunnel will auto-start when you log in."
Write-Host ""
Write-Host "To manage:"
Write-Host "  Start now:   Start-ScheduledTask -TaskName $TaskName"
Write-Host "  Stop:        Stop-ScheduledTask -TaskName $TaskName"
Write-Host "  Remove:      Unregister-ScheduledTask -TaskName $TaskName"
Write-Host "  Logs:        Get-Content '$ProjectDir\logs\startup.log' -Tail 20"
Write-Host ""
