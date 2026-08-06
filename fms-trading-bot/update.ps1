# One command to update the bot correctly.
#
#   .\update.ps1
#
# git pull only changes files on disk — the running bot keeps executing the
# code it loaded at startup, so an update needs stop + pull + start in that
# order. Doing it by hand caused repeated "Unknown command" confusion, and
# running git while the bot holds files open leaves git stuck on a y/n
# unlink prompt. This does the whole sequence and reports what changed.
#
# Run from the fms-trading-bot folder. Administrator is recommended so the
# scheduled task's process can be stopped.

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot

$task = "FMSTradingBot"
Write-Host "=== Updating the FMS trading bot ===" -ForegroundColor Cyan

$before = (git rev-parse --short HEAD 2>$null)

# --- 1. stop -----------------------------------------------------------
Write-Host "`n[1/4] Stopping the bot..."
Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

# Kill any python still running from THIS folder (the scheduled task does
# not always take its child with it, and two bots on one Telegram token
# collide with HTTP 409).
$killed = 0
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$PSScriptRoot*" } |
    ForEach-Object {
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
        if ($?) { $killed++ }
    }
if ($killed -gt 0) {
    Write-Host "      stopped $killed bot process(es)"
} else {
    Write-Host "      no bot process was running"
}
Start-Sleep -Seconds 1

# --- 2. pull -------------------------------------------------------------
Write-Host "`n[2/4] Fetching the latest code..."
git pull --no-rebase 2>&1 | ForEach-Object { "      $_" }

$after = (git rev-parse --short HEAD 2>$null)
if ($before -eq $after) {
    Write-Host "`n      Already up to date ($after)." -ForegroundColor Yellow
} else {
    Write-Host "`n      Updated $before -> $after" -ForegroundColor Green
    Write-Host "      Changes:"
    git log --oneline "$before..$after" 2>$null | ForEach-Object { "        $_" }
}

# --- 3. sanity check -------------------------------------------------------
Write-Host "`n[3/4] Checking the configuration..."
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "      .venv missing — run deploy\setup-windows.ps1 first." -ForegroundColor Red
    exit 1
}
& $python -c @"
import sys
from fmsbot.config import Settings
s = Settings.load()
problems = s.validate()
if problems:
    print('      CONFIG ERRORS:')
    for p in problems:
        print('        -', p)
    sys.exit(1)
accounts = s.broker_configs()
print(f'      OK: {len(accounts)} account(s) — ' +
      ', '.join(f'{c.name}({c.kind})' for c in accounts))
print(f'      {s.timeframe} | EMA{s.ema_fast}/{s.ema_slow} | ' +
      (f'{s.fixed_lot} lot' if s.fixed_lot > 0 else f'{s.risk_pct}% risk'))
"@
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n      Fix .env before starting: notepad .env" -ForegroundColor Red
    exit 1
}

# --- 4. start ---------------------------------------------------------------
Write-Host "`n[4/4] Starting the bot..."
Start-ScheduledTask -TaskName $task
Start-Sleep -Seconds 8

$state = (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue).State
Write-Host "      scheduled task: $state"

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Recent log:"
if (Test-Path .\bot.log) {
    Get-Content .\bot.log -Tail 8 | ForEach-Object { "  $_" }
}
Write-Host "`nOn your phone: /help lists the commands this build supports."
Write-Host "Watch the log with:  Get-Content .\bot.log -Tail 30 -Wait"
