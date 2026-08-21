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
    [switch]$Fix,
    # Also write everything to health-report.txt, for sharing.
    [switch]$Save
)

if ($Save) {
    $reportPath = Join-Path (Split-Path -Parent $PSScriptRoot) 'health-report.txt'
    Start-Transcript -Path $reportPath -Force | Out-Null
}

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

# --------------------------------------------------------- 2. autostart
Head '2. Autostart (brings it back after a reboot)'
$task = Get-ScheduledTask -TaskName $TaskName -ErrorAction SilentlyContinue
$startupCmd = Join-Path ([Environment]::GetFolderPath('Startup')) 'tgscalper.cmd'
$autostart = $false

if ($task) {
    $info = Get-ScheduledTaskInfo -TaskName $TaskName
    Ok "scheduled task registered, state: $($task.State)"
    Note "last run    : $($info.LastRunTime)"
    Note "last result : $($info.LastTaskResult)  (0 = ok, 267009 = currently running)"
    $autostart = $true
    if ($info.LastTaskResult -ne 0 -and $info.LastTaskResult -ne 267009) {
        $problems.Add("scheduled task exited with code $($info.LastTaskResult)")
    }
}
if (Test-Path $startupCmd) {
    Ok "startup entry present: $startupCmd"
    Note 'Starts at logon. Does not restart it if it crashes.'
    $autostart = $true
}
if (-not $autostart) {
    Bad 'nothing will start it automatically'
    Note 'It will not come back after a reboot, or if it stops.'
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

# -------------------------------------------------- 5. control bot token
Head '5. Control bot token'
$token = ''
if (Test-Path '.env') {
    foreach ($line in Get-Content '.env') {
        if ($line -match '^\s*TG_BOT_TOKEN\s*=\s*(.+)$') { $token = $Matches[1].Trim() }
    }
}
if (-not $token) {
    Note 'no TG_BOT_TOKEN set - the control bot is off, which is fine if you'
    Note 'drive everything from PowerShell.'
} else {
    # Ask Telegram directly. A revoked token is invisible from the outside:
    # the copier keeps working and the bot simply never answers, which looks
    # exactly like the copier being down.
    try {
        $reply = Invoke-RestMethod -Uri "https://api.telegram.org/bot$token/getMe" `
            -TimeoutSec 15 -ErrorAction Stop
        if ($reply.ok) {
            Ok "token valid - bot is @$($reply.result.username)"
        } else {
            Bad 'Telegram rejected the token'
            $problems.Add('bot token rejected')
        }
    } catch {
        if ("$_" -match '401|Unauthorized') {
            Bad 'token REJECTED by Telegram (401) - it has been revoked or changed'
            Note 'This alone explains a bot that never replies, even while the'
            Note 'copier is running normally and copying signals.'
            Note 'Get a fresh token: @BotFather -> /mybots -> your bot -> API Token'
            Note 'then run: .\windows\credentials.ps1'
            $problems.Add('bot token revoked')
        } else {
            Note "could not reach Telegram to check the token: $_"
            Note '(no internet, or a firewall - not necessarily a token problem)'
        }
    }
}

# ----------------------------------------------------------- 6. the log
Head '6. Recent log'
if (Test-Path 'logs\tgscalper.log') {
    $log = Get-Item 'logs\tgscalper.log'
    $age = (Get-Date) - $log.LastWriteTime
    Note "last written $([int]$age.TotalMinutes) min ago ($($log.LastWriteTime))"
    if ($age.TotalMinutes -gt 15 -and $running.Count -gt 0) {
        Note 'Quiet for a while, which is normal when no signals have arrived.'
    }
    # Named failures worth calling out before the raw tail, because they are
    # easy to scroll past and each has a specific fix.
    $log = Get-Content 'logs\tgscalper.log' -Tail 400
    if ($log -match 'control bot failed to start') {
        Bad 'the log says the control bot failed to start'
        Note 'The copier may still be running and copying signals - it is only'
        Note 'the Telegram replies that are missing. Usually a revoked token.'
        $problems.Add('control bot failed to start')
    }
    if ($log -match 'cannot commit|API misuse') {
        Note 'old database errors present - fixed on 2026-08-06, run: git pull'
    }
    if ($log -match 'REFUSING TO START') {
        Bad 'refused to start: MT5 is logged into a REAL MONEY account'
        Note 'Log MT5 into your demo account, or set execution.allow_real_money.'
        $problems.Add('real-money account refused')
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
        if ($problems -contains 'not logged in' -or $problems -contains 'no groups selected') {
            # Neither can be fixed without you: one needs a phone code typed in,
            # the other needs groups picked in Telegram.
            Write-Host '  This one needs you - see the notes above.' -ForegroundColor Yellow
        } else {
            # autostart.ps1 sets up autostart *and* starts it now, so it covers
            # both remaining problems.
            & (Join-Path $PSScriptRoot 'autostart.ps1')
        }
    } else {
        Write-Host "`n  Try:  .\windows\health.ps1 -Fix" -ForegroundColor Cyan
    }
}
Write-Host ''

if ($Save) {
    Stop-Transcript | Out-Null
    Write-Host "  Saved to $reportPath - send that file if you need help." -ForegroundColor Cyan
    Write-Host ''
}
