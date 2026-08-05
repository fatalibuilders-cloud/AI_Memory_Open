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

$startupCmd = Join-Path ([Environment]::GetFolderPath('Startup')) 'tgscalper.cmd'

if ($Remove) {
    if (Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue) {
        Stop-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
        Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
        Write-Host "Removed scheduled task '$TaskName'." -ForegroundColor Green
    } else {
        Write-Host "No scheduled task named '$TaskName'." -ForegroundColor Yellow
    }
    if (Test-Path $startupCmd) {
        Remove-Item $startupCmd -Force
        Write-Host "Removed startup entry $startupCmd." -ForegroundColor Green
    }
    Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*tgscalper*' } |
        ForEach-Object {
            Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
            Write-Host "Stopped running copier (PID $($_.ProcessId))." -ForegroundColor Green
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
    # powercfg usually needs elevation. Failing to change a power setting must
    # never stop the task being registered — that would trade the whole point
    # of this script for a nice-to-have.
    try {
        $null = powercfg /change standby-timeout-ac 0 2>&1
        $null = powercfg /change hibernate-timeout-ac 0 2>&1
        if ($LASTEXITCODE -eq 0) {
            Write-Ok 'standby and hibernate disabled while on mains power'
        } else {
            Write-Warn 'could not change power settings (usually needs an admin window)'
            Write-Warn 'Set Settings > System > Power > Screen and sleep > Never by hand'
        }
    } catch {
        Write-Warn "could not change power settings: $_"
        Write-Warn 'Set Settings > System > Power > Screen and sleep > Never by hand'
    }
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
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false -ErrorAction SilentlyContinue
}

# Registering a task can be refused outright — group policy, security software,
# or a machine that simply requires elevation for the task store. Claiming
# success here regardless is worse than failing: it sends you away believing
# the copier will come back after a reboot when nothing has been set up.
$method = ''
try {
    Register-ScheduledTask `
        -TaskName $TaskName `
        -Action $action `
        -Trigger $triggers `
        -Settings $settings `
        -Description 'Telegram signal copier (tgscalper)' `
        -ErrorAction Stop | Out-Null
    $method = 'task'
    Write-Ok "task '$TaskName' registered - starts at logon, retries every minute"
} catch {
    Write-Warn "Windows refused to register the task: $($_.Exception.Message)"
    Write-Warn 'Falling back to the Startup folder, which never needs admin rights.'
}

if (-not $method) {
    # A .cmd in the per-user Startup folder is the lowest-privilege autostart
    # Windows offers. No elevation, no task store, no policy to satisfy.
    $body = @(
        '@echo off',
        "cd /d ""$projectDir""",
        "start """" /min powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File ""$runScript"" run"
    )
    [System.IO.File]::WriteAllLines($startupCmd, $body, [System.Text.ASCIIEncoding]::new())
    if (Test-Path $startupCmd) {
        $method = 'startup'
        Write-Ok "startup entry created: $startupCmd"
        Write-Warn 'This starts it at logon but will NOT restart it if it crashes.'
    } else {
        throw "Could not set up autostart by either method. Start it by hand with: .\windows\run.ps1 run"
    }
}

# --------------------------------------------------------------- start it now
if (-not $NoStart) {
    Write-Step 'Starting it now'
    $already = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*tgscalper*' })
    if ($already.Count -gt 0) {
        Write-Ok "already running (PID $($already[0].ProcessId))"
    } else {
        # Launched directly rather than through the task, so that this works
        # identically whichever autostart method was used above.
        Start-Process -FilePath 'powershell.exe' `
            -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-WindowStyle', 'Hidden',
                          '-File', "`"$runScript`"", 'run' `
            -WorkingDirectory $projectDir `
            -WindowStyle Hidden

        # Verify rather than assume: a process that dies on startup is exactly
        # the failure this script exists to prevent.
        $up = $false
        foreach ($attempt in 1..10) {
            Start-Sleep -Seconds 2
            $found = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
                Where-Object { $_.CommandLine -like '*tgscalper*' })
            if ($found.Count -gt 0) { $up = $true; break }
        }
        if ($up) {
            Write-Ok 'running - send /status to your bot to confirm'
        } else {
            Write-Warn 'it did not stay running. See what happened with:'
            Write-Warn '    .\windows\run.ps1 run'
            Write-Warn '(that shows the error in the window instead of hiding it)'
        }
    }
}

Write-Host @"

Autostart method: $(if ($method -eq 'task') { 'Scheduled Task (restarts on failure)' } else { 'Startup folder (starts at logon only)' })

Watch it:
    Get-Content .\logs\tgscalper.log -Wait -Tail 40

Check on it any time:
    .\windows\health.ps1

Stop it, or undo all of this:
    .\windows\autostart.ps1 -Remove

Two things this cannot do for you:

  1. MetaTrader 5 must be open and logged in, with Algo Trading enabled.
     Set MT5 to start with Windows as well, or the copier will read your
     groups and have nowhere to send the orders.

  2. It cannot survive the machine being shut down, or losing internet.
     A laptop that closes at night is not a trading server - if you want
     this running while you sleep, a Windows VPS is the honest answer.

"@ -ForegroundColor Green
