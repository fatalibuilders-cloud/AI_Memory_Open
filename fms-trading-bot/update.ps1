# One command to update the bot correctly.
#
#   .\update.ps1
#
# git pull only changes files on disk — the running bot keeps executing the
# code it loaded at startup, so an update needs stop + pull + start in that
# order. This does the whole sequence and reports what changed.
#
# Run from the fms-trading-bot folder. Administrator is needed to stop the
# scheduled task's process; the script says so if it is not elevated.

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
Write-Host "`n[1/4] Stopping the bot..."
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
Write-Host "`n[2/4] Fetching the latest code..."
git pull --no-rebase 2>&1 | ForEach-Object { "      $_" }

$after = (git rev-parse --short HEAD 2>$null)
if ($before -eq $after) {
    Write-Host "`n      Already up to date ($after)." -ForegroundColor Yellow
} else {
    Write-Host "`n      Updated $before -> $after" -ForegroundColor Green
    git log --oneline "$before..$after" 2>$null | ForEach-Object { "        $_" }
}

# --- 3. sanity check -------------------------------------------------------
Write-Host "`n[3/4] Checking the configuration..."
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "      .venv missing - run deploy\setup-windows.ps1 first." -ForegroundColor Red
    exit 1
}
& $python check_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n      Fix .env before starting:  notepad .env" -ForegroundColor Red
    Write-Host "      The bot has NOT been restarted." -ForegroundColor Red
    exit 1
}

# --- 4. start ---------------------------------------------------------------
Write-Host "`n[4/4] Starting the bot..."
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
