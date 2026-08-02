<#
.SYNOPSIS
    Keeps tgscalper running without a PowerShell window open.

.DESCRIPTION
    The copier only watches your groups while its process is alive. Run it by
    hand and it dies with the window — close the terminal, log out, or let the
    machine sleep, and copying silently stops.

    This registers a Scheduled Task that starts it at logon and restarts it if
    it stops, and by default also stops the computer sleeping, which is the
    usual reason an overnight run goes quiet.

    It cannot keep MetaTrader 5 running. MT5 must be open and logged in with
    Algo Trading enabled, or there is nowhere to send orders.

.EXAMPLE
    .\windows\autostart.ps1
    .\windows\autostart.ps1 -KeepSleepSettings
    .\windows\autostart.ps1 -Remove
#>

[CmdletBinding()]
param(
    [string]$TaskName = 'tgscalper',
    [switch]$Remove,
    # Leave the machine's power settings alone.
    [switch]$KeepSleepSettings,
    # Register the task but do not start it now.
    [switch]$NoStart
)

$ErrorActionPreference = 'Stop'

$projectDir = Split-Path -Parent $PSScriptRoot
$runScript = Join-Path $projectDir 'windows\run.ps1'

function Write-Step { param($m) Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Ok   { param($m) Write-Host "    OK  $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Host "    !   $m" -ForegroundColor Yellow }

if ($Remove) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'." -ForegroundColor Green
    } else {
        Write-Host "No scheduled task named '$TaskName'." -ForegroundColor Yellow
    }
    Write-Host 'Sleep settings were left as they are. Restore them with:' -ForegroundColor DarkGray
    Write-Host '    powercfg /change standby-timeout-ac 30' -ForegroundColor DarkGray
    exit 0
}

if (-not (Test-Path $runScript)) { throw "run.ps1 not found at $runScript" }

# ------------------------------------------------------------- session check
Write-Step 'Checking the Telegram session'
$session = Join-Path $projectDir 'data\tgscalper.session'
if (-not (Test-Path $session)) {
    Write-Warn 'No Telegram session yet.'
    Write-Host @'
    A background task cannot type your login code. Run this once in a normal
    window first, enter the code, then come back and run this script:

        .\windows\run.ps1 run
'@ -ForegroundColor Yellow
    throw 'Log in interactively first.'
}
Write-Ok 'session present, no interactive login needed'

# -------------------------------------------------------------- sleep policy
if (-not $KeepSleepSettings) {
    Write-Step 'Stopping the computer from sleeping'
    # Sleep suspends the process and drops the Telegram connection. The display
    # may still switch off; only standby matters here.
    powercfg /change standby-timeout-ac 0 2>&1 | Out-Null
    powercfg /change hibernate-timeout-ac 0 2>&1 | Out-Null
    Write-Ok 'standby and hibernate disabled while on mains power'
    Write-Warn 'On battery the machine will still sleep, and copying stops when it does'
} else {
    Write-Warn 'Power settings untouched - if this machine sleeps, copying stops'
}

# ---------------------------------------------------------------------- task
Write-Step 'Registering the scheduled task'

$action = New-ScheduledTaskAction `
    -Execute 'powershell.exe' `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runScript`" run" `
    -WorkingDirectory $projectDir

$triggers = @(New-ScheduledTaskTrigger -AtLogOn)

$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -StartWhenAvailable `
    -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Seconds 0) `
    -MultipleInstances IgnoreNew

if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
    Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
}

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $triggers `
    -Settings $settings `
    -Description 'Telegram signal copier (tgscalper)' | Out-Null
Write-Ok "task '$TaskName' registered - starts at logon, retries every minute"

if (-not $NoStart) {
    Start-ScheduledTask -TaskName $TaskName
    Start-Sleep -Seconds 3
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    Write-Ok "started (last result: $($info.LastTaskResult))"
}

Write-Host @"

Running in the background now. Send /status to your bot to confirm.

Watch it:
    Get-Content .\logs\tgscalper.log -Wait -Tail 40

Control it:
    Stop-ScheduledTask  -TaskName $TaskName
    Start-ScheduledTask -TaskName $TaskName
    .\windows\autostart.ps1 -Remove

Two things this cannot do for you:

  1. MetaTrader 5 must be open and logged in, with Algo Trading enabled.
     Set MT5 to start with Windows as well, or the copier will read your
     groups and have nowhere to send the orders.

  2. It cannot survive the machine being shut down, or losing internet.
     A laptop that closes at night is not a trading server - if you want
     this running while you sleep, a Windows VPS is the honest answer.

"@ -ForegroundColor Green
