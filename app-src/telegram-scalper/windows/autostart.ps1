<#
.SYNOPSIS
    Registers tgscalper as a Scheduled Task so it starts at logon and restarts
    itself if it stops.

.DESCRIPTION
    Intended for a Windows VPS you leave running. The task starts the listener
    at logon, and Task Scheduler restarts it on failure.

    It cannot help with the other half: MetaTrader 5 must also be running and
    logged in, with Algo Trading enabled. Set MT5 to start with Windows and to
    remember its password, or the bot will connect to Telegram and then have
    nowhere to send orders.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File .\windows\autostart.ps1
    powershell -ExecutionPolicy Bypass -File .\windows\autostart.ps1 -Remove
#>

[CmdletBinding()]
param(
    [string]$TaskName = 'tgscalper',
    [switch]$Remove
)

$ErrorActionPreference = 'Stop'

$projectDir = Split-Path -Parent $PSScriptRoot
$runScript = Join-Path $projectDir 'windows\run.ps1'

if ($Remove) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'." -ForegroundColor Green
    } else {
        Write-Host "No scheduled task named '$TaskName'." -ForegroundColor Yellow
    }
    exit 0
}

if (-not (Test-Path $runScript)) { throw "run.ps1 not found at $runScript" }

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runScript`" run" `
    -WorkingDirectory $projectDir

$trigger = New-ScheduledTaskTrigger -AtLogOn

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0)   # 0 = never kill it

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description 'Telegram signal copier (tgscalper)' | Out-Null

Write-Host @"

Scheduled task '$TaskName' registered.

  starts    : at logon, and retries every minute if it stops
  runs      : $runScript run
  working in: $projectDir

Manage it with:
    Start-ScheduledTask   -TaskName $TaskName
    Stop-ScheduledTask    -TaskName $TaskName
    Get-ScheduledTaskInfo -TaskName $TaskName
    .\windows\autostart.ps1 -Remove

The task runs hidden, so watch it through the log instead:
    Get-Content .\logs\tgscalper.log -Wait -Tail 40

Before relying on this, make sure MetaTrader 5 also starts with Windows and
logs in on its own. Telegram alone is not enough to place a trade.

"@ -ForegroundColor Green
