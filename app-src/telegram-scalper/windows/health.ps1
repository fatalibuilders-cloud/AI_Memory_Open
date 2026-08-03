<#
.SYNOPSIS
    Answers one question: is the copier actually running right now?

.DESCRIPTION
    When the control bot stops replying, the bot cannot tell you why — it is
    the thing that is down. This looks from the outside instead: is the process
    alive, is the scheduled task registered and what did it last return, what
    do the logs say, and when was the last signal seen.

    Run it any time the bot goes quiet.

.EXAMPLE
    .\windows\health.ps1
    .\windows\health.ps1 -Fix
#>

[CmdletBinding()]
param(
    [string]$TaskName = 'tgscalper',
    # Try to start whatever is not running.
    [switch]$Fix
)

$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location $projectDir

function Head { param($m) Write-Host "`n$m" -ForegroundColor Cyan;
                Write-Host ('-' * 62) -ForegroundColor DarkGray }
function Ok   { param($m) Write-Host "  [OK]   $m" -ForegroundColor Green }
function Bad  { param($m) Write-Host "  [DOWN] $m" -ForegroundColor Red }
function Note { param($m) Write-Host "         $m" -ForegroundColor DarkGray }

Write-Host "`n==============================================================" -ForegroundColor Magenta
Write-Host "  TGSCALPER - IS IT RUNNING?" -ForegroundColor Magenta
Write-Host "==============================================================" -ForegroundColor Magenta
Write-Host "  $projectDir" -ForegroundColor DarkGray

$problems = New-Object System.Collections.Generic.List[string]

# ------------------------------------------------------------ 1. process
Head '1. The copier process'
$running = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -and $_.CommandLine -like '*tgscalper*' })

if ($running.Count -gt 0) {
    Ok "running (PID $($running[0].ProcessId))"
    Note 'Your bot should be answering. If it is not, check the log below.'
} else {
    Bad 'not running - nothing is watching your groups, and the bot cannot reply'
    $problems.Add('copier not running')
}

# ---------------------------------------------------- 2. scheduled task
Head '2. Scheduled task (starts it automatically)'
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
if ($task) {
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    Ok "registered, state: $($task.State)"
    Note "last run    : $($info.LastRunTime)"
    Note "last result : $($info.LastTaskResult)  (0 = ok, 267009 = currently running)"
    if ($info.LastTaskResult -ne 0 -and $info.LastTaskResult -ne 267009) {
        $problems.Add("scheduled task exited with code $($info.LastTaskResult)")
    }
} else {
    Bad "no scheduled task named '$TaskName'"
    Note 'It will not restart on its own after a reboot.'
    $problems.Add('autostart not set up')
}

# ------------------------------------------------------------- 3. login
Head '3. Telegram login'
if (Test-Path 'data\tgscalper.session') {
    Ok 'session file present - no phone code needed to start'
} else {
    Bad 'no session file - must log in once interactively'
    Note 'Run: .\windows\run.ps1 run   and type the code Telegram sends you'
    $problems.Add('not logged in')
}

# ------------------------------------------------------------ 4. groups
Head '4. Groups being copied'
if (Test-Path 'data\groups.json') {
    try {
        $groups = Get-Content 'data\groups.json' -Raw | ConvertFrom-Json
        $count = @($groups.enabled).Count
        if ($count -gt 0) {
            Ok "$count group(s) selected"
            foreach ($id in $groups.enabled) {
                $title = $groups.titles.$("$id")
                Note "  $(if ($title) { $title } else { $id })"
            }
        } else {
            Bad 'no groups selected - send /selectgroup to your bot'
            $problems.Add('no groups selected')
        }
    } catch {
        Bad "groups.json unreadable: $_"
    }
} else {
    Bad 'no group selection saved - send /selectgroup to your bot'
    $problems.Add('no groups selected')
}

# ----------------------------------------------------------- 5. the log
Head '5. Recent log'
if (Test-Path 'logs\tgscalper.log') {
    $log = Get-Item 'logs\tgscalper.log'
    $age = (Get-Date) - $log.LastWriteTime
    Note "last written $([int]$age.TotalMinutes) min ago ($($log.LastWriteTime))"
    if ($age.TotalMinutes -gt 15 -and $running.Count -gt 0) {
        Note 'Quiet for a while, which is normal when no signals have arrived.'
    }
    Write-Host ''
    Get-Content 'logs\tgscalper.log' -Tail 25 | ForEach-Object {
        $colour = if ($_ -match 'ERROR|CRITICAL') { 'Red' }
                  elseif ($_ -match 'WARNING')    { 'Yellow' }
                  else                            { 'Gray' }
        Write-Host "  $_" -ForegroundColor $colour
    }
} else {
    Note 'no log file yet - it has never completed a start'
}

# ----------------------------------------------------------- 6. verdict
Head 'Verdict'
if ($problems.Count -eq 0) {
    Write-Host '  Everything is up. Send /status to your bot to confirm.' -ForegroundColor Green
} else {
    Write-Host "  $($problems.Count) problem(s):" -ForegroundColor Yellow
    foreach ($problem in $problems) { Write-Host "    - $problem" -ForegroundColor Yellow }

    if ($Fix) {
        Write-Host "`n  Fixing..." -ForegroundColor Cyan
        if ($problems -contains 'autostart not set up') {
            & (Join-Path $PSScriptRoot 'autostart.ps1')
        } elseif ($problems -contains 'copier not running' -and $task) {
            Start-ScheduledTask -TaskName $TaskName
            Start-Sleep -Seconds 5
            Write-Host '  Started. Send /status to your bot.' -ForegroundColor Green
        } else {
            Write-Host '  Nothing here can be fixed automatically - see the notes above.' -ForegroundColor Yellow
        }
    } else {
        Write-Host "`n  Try:  .\windows\health.ps1 -Fix" -ForegroundColor Cyan
    }
}
Write-Host ''
