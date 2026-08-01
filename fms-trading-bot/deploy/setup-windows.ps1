# One-shot setup for the FMS bot on a Windows PC / VPS (AWS free-tier
# Windows Server, broker VPS, or your own PC).
#
# Run from an ADMIN PowerShell inside the fms-trading-bot directory:
#   Set-ExecutionPolicy -Scope Process Bypass -Force
#   .\deploy\setup-windows.ps1
#
# What it does:
#   1. Installs Python 3.12 if missing (via winget)
#   2. Creates .venv and installs requirements (incl. MetaTrader5)
#   3. Creates .env from the template if missing (you then edit it)
#   4. Registers a Scheduled Task that starts the bot at boot and
#      keeps it running (the runner loop restarts it if it crashes)
#
# NOTE: you must still install the MetaTrader 5 terminal yourself and log
# into your (demo!) account in it once — https://www.metatrader5.com

$ErrorActionPreference = "Stop"
$BotDir = Split-Path -Parent $PSScriptRoot
Set-Location $BotDir
Write-Host "==> Bot directory: $BotDir"

# --- 1. Python ---------------------------------------------------------
$py = Get-Command py -ErrorAction SilentlyContinue
if (-not $py) {
    Write-Host "==> Installing Python 3.12 via winget..."
    winget install -e --id Python.Python.3.12 --accept-package-agreements --accept-source-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
}

# --- 2. venv + deps ------------------------------------------------------
Write-Host "==> Creating virtualenv + installing dependencies..."
py -m venv .venv
& .\.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
& .\.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt

# --- 3. .env ---------------------------------------------------------------
if (-not (Test-Path .env)) {
    Copy-Item .env.example .env
    Write-Host "==> Created .env from template - YOU MUST EDIT IT (notepad $BotDir\.env)"
}

# --- 4. Scheduled task -------------------------------------------------------
Write-Host "==> Registering scheduled task 'FMSTradingBot'..."
$runner = Join-Path $BotDir "deploy\run-bot.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$runner`"" `
    -WorkingDirectory $BotDir
$trigger = New-ScheduledTaskTrigger -AtStartup
$settings = New-ScheduledTaskSettingsSet -RestartCount 999 `
    -RestartInterval (New-TimeSpan -Minutes 1) `
    -ExecutionTimeLimit (New-TimeSpan -Days 3650) `
    -StartWhenAvailable
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERDOMAIN\$env:USERNAME" `
    -LogonType S4U -RunLevel Highest

Unregister-ScheduledTask -TaskName "FMSTradingBot" -Confirm:$false -ErrorAction SilentlyContinue
Register-ScheduledTask -TaskName "FMSTradingBot" -Action $action -Trigger $trigger `
    -Settings $settings -Principal $principal | Out-Null

Write-Host @"

======================================================================
Setup complete. Next steps:

  1. Install MetaTrader 5 and log into your DEMO account once,
     then enable the 'Algo Trading' toolbar button.

  2. Edit your credentials:   notepad $BotDir\.env
     (TG_BOT_TOKEN, TG_PASSWORD, MT5_LOGIN/PASSWORD/SERVER)

  3. Test in the foreground:  .\.venv\Scripts\python.exe main.py
     (then /login from your phone; Ctrl+C to stop)

  4. Start the background task:
     Start-ScheduledTask -TaskName FMSTradingBot
     Logs: Get-Content $BotDir\bot.log -Tail 50 -Wait

The task auto-starts on boot; the runner restarts the bot if it crashes.
Stop it any time with: Stop-ScheduledTask -TaskName FMSTradingBot
======================================================================
"@
