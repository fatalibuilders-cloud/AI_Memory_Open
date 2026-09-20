# One command to update the bot correctly.
#
#   .\update.ps1
#   .\update.ps1 -Preset scalp1000 -Rate 1000
#
# It sets its own working directory, so the FULL PATH works from anywhere
# and there is no folder to be in first:
#
#   & "C:\Users\<you>\AI_Memory_Open\fms-trading-bot\update.ps1" -Rate 1000
#
# git pull only changes files on disk — the running bot keeps executing the
# code it loaded at startup, so an update needs stop + pull + start in that
# order. This does the whole sequence and reports what changed.
#
# Run from the fms-trading-bot folder. Administrator is needed to stop the
# scheduled task's process; the script says so if it is not elevated.

param(
    # Apply a tuning preset after pulling, e.g. -Preset scalp1000
    [string]$Preset = "",
    # Solve the exits for this many trades a day and write them, e.g. -Rate 1000
    [int]$Rate = 0
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$task = "FMSTradingBot"
Write-Host "=== Updating the FMS trading bot ===" -ForegroundColor Cyan

$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "`n  NOTE: not running as administrator." -ForegroundColor Yellow
    Write-Host "  The bot process may refuse to stop ('Access is denied'), and the"
    Write-Host "  old code would keep running. If that happens, close this window,"
    Write-Host "  right-click PowerShell -> Run as administrator, and re-run."
}

$before = (git rev-parse --short HEAD 2>$null)

# --- 1. stop -----------------------------------------------------------
Write-Host "`n[1/5] Stopping the bot..."
Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Kill any python still running from THIS folder. The scheduled task does not
# always take its child with it, and two bots on one Telegram token collide
# with HTTP 409.
$stubborn = @()
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$PSScriptRoot*" } |
    ForEach-Object {
        $pidToKill = $_.ProcessId
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        if (Get-Process -Id $pidToKill -ErrorAction SilentlyContinue) {
            # second attempt: taskkill can stop processes Stop-Process cannot
            & taskkill.exe /PID $pidToKill /F /T 2>&1 | Out-Null
            Start-Sleep -Milliseconds 500
            if (Get-Process -Id $pidToKill -ErrorAction SilentlyContinue) {
                $stubborn += $pidToKill
            }
        }
    }

if ($stubborn.Count -gt 0) {
    Write-Host "`n  COULD NOT STOP the bot (pid $($stubborn -join ', '))." -ForegroundColor Red
    Write-Host "  It will keep running the OLD code, so the update would not take" -ForegroundColor Red
    Write-Host "  effect. Re-run this script from an ADMINISTRATOR PowerShell." -ForegroundColor Red
    Write-Host "  Nothing has been changed." -ForegroundColor Red
    exit 1
}
Write-Host "      bot stopped"

# --- 2. pull -------------------------------------------------------------
Write-Host "`n[2/5] Fetching the latest code..."
git pull --no-rebase 2>&1 | ForEach-Object { "      $_" }

$after = (git rev-parse --short HEAD 2>$null)
if ($before -eq $after) {
    Write-Host "`n      Already up to date ($after)." -ForegroundColor Yellow
} else {
    Write-Host "`n      Updated $before -> $after" -ForegroundColor Green
    git log --oneline "$before..$after" 2>$null | ForEach-Object { "        $_" }
}

$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "      .venv missing - run deploy\setup-windows.ps1 first." -ForegroundColor Red
    exit 1
}

# --- 3. settings -----------------------------------------------------------
# Between the pull and the check, because a preset that fails to apply must
# not reach the start step, and rate.py needs the preset's slot counts.
if ($Preset) {
    Write-Host "`n[3/5] Applying preset '$Preset'..."
    & $python preset.py $Preset
    if ($LASTEXITCODE -ne 0) {
        Write-Host "      preset failed - nothing started." -ForegroundColor Red
        exit 1
    }
}
if ($Rate -gt 0) {
    Write-Host "`n[3/5] Solving the exits for $Rate trades/day..."
    & $python rate.py --target $Rate --apply
    if ($LASTEXITCODE -ne 0) {
        Write-Host "`n      No symbol can carry that rate - see the reasons above."
        Write-Host "      The bot has NOT been restarted." -ForegroundColor Red
        exit 1
    }
}

# --- 4. sanity check -------------------------------------------------------
Write-Host "`n[4/5] Checking the configuration..."
& $python check_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n      Fix .env before starting:  notepad .env" -ForegroundColor Red
    Write-Host "      The bot has NOT been restarted." -ForegroundColor Red
    exit 1
}

# --- 5. start ---------------------------------------------------------------
Write-Host "`n[5/5] Starting the bot..."
Start-ScheduledTask -TaskName $task
Start-Sleep -Seconds 8

$state = (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue).State
Write-Host "      scheduled task: $state"

Write-Host "`n=== Done ===" -ForegroundColor Cyan
if (Test-Path .\bot.log) {
    Write-Host "Recent log:"
    Get-Content .\bot.log -Tail 8 | ForEach-Object { "  $_" }
}
Write-Host "`nOn your phone: /help lists the commands this build supports."
Write-Host "Watch the log with:  Get-Content .\bot.log -Tail 30 -Wait"
