# Re-tune the bot for the instruments it actually trades.
#
#   .\retune.ps1                                   # preview only, changes nothing
#   .\retune.ps1 -Apply                            # write the tuned values
#   .\retune.ps1 -Apply -Drop USDCHFm,NZDUSDm,XAGUSDm -Stages "0.10:0,0.25:0.10"
#
# The bot must be stopped while this runs: two processes sharing one MT5
# terminal interfere, and the tuner needs live quotes. This stops it, makes
# the changes, and starts it again. Every .env edit is backed up first.
#
# Run from the fms-trading-bot folder, as administrator (the scheduled
# task's process will not stop otherwise).

param(
    # Write the tuned values. Without this the script only measures and shows.
    [switch]$Apply,
    # Symbols to remove from SYMBOLS, e.g. the ones the tuner flags as too wide.
    [string[]]$Drop = @(),
    # Protection ladder, "trigger:lock,trigger:lock". The tuner scales it per
    # instrument, so give the figures you want on a normal forex pair.
    [string]$Stages = ""
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$task = "FMSTradingBot"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "=== Re-tuning the FMS trading bot ===" -ForegroundColor Cyan
if (-not $Apply) {
    Write-Host "    PREVIEW MODE - nothing will be written. Add -Apply to commit." -ForegroundColor Yellow
}

if (-not (Test-Path $python)) {
    Write-Host "  .venv missing - run deploy\setup-windows.ps1 first." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path .\.env)) {
    Write-Host "  No .env here. Run this from the fms-trading-bot folder." -ForegroundColor Red
    exit 1
}

$isAdmin = ([Security.Principal.WindowsPrincipal] `
    [Security.Principal.WindowsIdentity]::GetCurrent()
    ).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if (-not $isAdmin) {
    Write-Host "`n  NOTE: not running as administrator. If the bot refuses to stop," -ForegroundColor Yellow
    Write-Host "  close this window and re-open PowerShell with Run as administrator." -ForegroundColor Yellow
}

# --- 1. stop the bot --------------------------------------------------------
Write-Host "`n[1/6] Stopping the bot..."
Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2

$stubborn = @()
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$PSScriptRoot*" } |
    ForEach-Object {
        $pidToKill = $_.ProcessId
        Stop-Process -Id $pidToKill -Force -ErrorAction SilentlyContinue
        Start-Sleep -Milliseconds 500
        if (Get-Process -Id $pidToKill -ErrorAction SilentlyContinue) {
            & taskkill.exe /PID $pidToKill /F /T 2>&1 | Out-Null
            Start-Sleep -Milliseconds 500
            if (Get-Process -Id $pidToKill -ErrorAction SilentlyContinue) { $stubborn += $pidToKill }
        }
    }
if ($stubborn.Count -gt 0) {
    Write-Host "`n  COULD NOT STOP the bot (pid $($stubborn -join ', '))." -ForegroundColor Red
    Write-Host "  The tuner would fight it for the MT5 terminal and read bad quotes." -ForegroundColor Red
    Write-Host "  Re-run from an ADMINISTRATOR PowerShell. Nothing has been changed." -ForegroundColor Red
    exit 1
}
Write-Host "      bot stopped"

# --- 2. edit .env -----------------------------------------------------------
Write-Host "`n[2/6] Adjusting .env..."
$envLines = Get-Content .\.env -Encoding UTF8
$changed = $false
$emptied = $false

# -Drop XAGUSDm,NZDUSDm is an array when typed at a PowerShell prompt, but a
# single comma-joined string if it arrives quoted or through -File. Accept both,
# otherwise the quoted form silently drops nothing.
$Drop = @($Drop | Where-Object { $_ } | ForEach-Object { $_.Split(',') } |
          ForEach-Object { $_.Trim() } | Where-Object { $_ })

if ($Drop.Count -gt 0) {
    # SYMBOLS may be global or per-account (EXNESS_SYMBOLS, DERIV_SYMBOLS...),
    # so match any variable whose name ends in SYMBOLS.
    $envLines = $envLines | ForEach-Object {
        if ($_ -match '^\s*([A-Za-z0-9_]*SYMBOLS)\s*=\s*(.+?)\s*$') {
            $name = $Matches[1]
            $kept = $Matches[2].Split(',') |
                    ForEach-Object { $_.Trim() } |
                    Where-Object { $_ -and ($Drop -notcontains $_) }
            $removed = $Matches[2].Split(',') |
                       ForEach-Object { $_.Trim() } |
                       Where-Object { $Drop -contains $_ }
            if ($removed.Count -gt 0) {
                Write-Host "      $name - removed $($removed -join ', ')" -ForegroundColor Yellow
                $script:changed = $true
            }
            if ($removed.Count -gt 0 -and $kept.Count -eq 0) {
                Write-Host "      $name would be left with no symbols at all." -ForegroundColor Red
                $script:emptied = $true
            }
            "$name=$($kept -join ',')"
        } else { $_ }
    }
}

if ($Stages) {
    # One ladder, not two competing ones: PROFIT_STAGES wins over the single
    # BREAKEVEN_AT_MONEY, so leaving both set is a silent contradiction.
    $envLines = $envLines | Where-Object { $_ -notmatch '^\s*PROFIT_STAGES\s*=' }
    $envLines += "PROFIT_STAGES=$Stages"
    Write-Host "      PROFIT_STAGES=$Stages" -ForegroundColor Green
    $changed = $true
}

if ($emptied) {
    Write-Host "`n  Refusing to write: an account would be left with nothing to" -ForegroundColor Red
    Write-Host "  trade. Drop fewer symbols, or remove that account from" -ForegroundColor Red
    Write-Host "  ACTIVE_BROKERS instead. Nothing has been changed." -ForegroundColor Red
    Start-ScheduledTask -TaskName $task
    exit 1
}

if ($changed) {
    if ($Apply) {
        Copy-Item .\.env .\.env.pre-retune -Force
        # Not Set-Content -Encoding UTF8: Windows PowerShell 5.1 writes a
        # byte-order mark, which becomes part of the first variable's name.
        $noBom = New-Object System.Text.UTF8Encoding $false
        [System.IO.File]::WriteAllLines(
            (Join-Path $PSScriptRoot ".env"), [string[]]$envLines, $noBom)
        Write-Host "      written (previous copy in .env.pre-retune)"
    } else {
        Write-Host "      not written - preview mode"
    }
} else {
    Write-Host "      no changes requested"
}

# --- 3. measure -------------------------------------------------------------
Write-Host "`n[3/6] Measuring every symbol against the live terminal..."
Write-Host "      MT5 must be open and logged in, and the market open.`n"
if ($Apply) {
    & $python tune_symbols.py --apply
} else {
    & $python tune_symbols.py
}
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n  The tuner could not measure the market." -ForegroundColor Red
    Write-Host "  Open MT5, log in, check the market is open, then re-run." -ForegroundColor Red
    Write-Host "  The bot is still stopped - start it with:  Start-ScheduledTask -TaskName $task" -ForegroundColor Red
    exit 1
}

# --- 4. validate ------------------------------------------------------------
Write-Host "`n[4/6] Checking the configuration..."
& $python check_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n  Fix .env before starting:  notepad .env" -ForegroundColor Red
    Write-Host "  The bot has NOT been restarted." -ForegroundColor Red
    exit 1
}

# --- 5. restart -------------------------------------------------------------
if (-not $Apply) {
    Write-Host "`n[5/6] Preview finished - nothing was changed." -ForegroundColor Yellow
    Write-Host "      Read the RISK AT YOUR BALANCE table above before applying:"
    Write-Host "      any symbol marked over your limit cannot be traded safely at"
    Write-Host "      this account size, whatever the settings say."
    Write-Host "`n      To commit these values:" -ForegroundColor Cyan
    Write-Host "        .\retune.ps1 -Apply"
    Write-Host "`n[6/6] Restarting the bot with the settings it already had..."
} else {
    Write-Host "`n[5/6] Restarting the bot..."
}
Start-ScheduledTask -TaskName $task
Start-Sleep -Seconds 8
$state = (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue).State
Write-Host "      scheduled task: $state"

# --- 6. done ----------------------------------------------------------------
Write-Host "`n=== Done ===" -ForegroundColor Cyan
if (Test-Path .\bot.log) {
    Write-Host "Recent log:"
    Get-Content .\bot.log -Tail 8 | ForEach-Object { "  $_" }
}
Write-Host "`nWatch it work:  Get-Content .\bot.log -Tail 30 -Wait"
Write-Host "On your phone:  /status, then /why if a signal is refused."
