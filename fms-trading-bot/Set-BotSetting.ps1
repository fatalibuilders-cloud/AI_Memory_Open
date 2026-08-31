<#
.SYNOPSIS
    Change settings in .env safely, then restart the bot.

.DESCRIPTION
    Hand-editing .env has caused two outages in this project: an inline
    comment that crashed startup, and Notepad's byte-order mark blanking
    the first setting. This replaces or appends a value, keeps a backup,
    validates the result before restarting, and refuses to restart on a
    broken file.

.EXAMPLE
    .\Set-BotSetting.ps1 TRAIL_ATR_MULT=1.5
.EXAMPLE
    .\Set-BotSetting.ps1 TRAIL_ATR_MULT=1.5 TRAIL_START_MONEY=0.10
.EXAMPLE
    .\Set-BotSetting.ps1 TRAIL_ATR_MULT=1.5 -WhatIf     # show, change nothing
#>

param(
    # One or more KEY=VALUE pairs.
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$Setting,
    [switch]$WhatIf,
    # Change the file but leave the bot stopped.
    [switch]$NoRestart
)

$ErrorActionPreference = "Continue"
Set-Location $PSScriptRoot
$task = "FMSTradingBot"
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
$envPath = Join-Path $PSScriptRoot ".env"

if (-not $Setting -or $Setting.Count -eq 0) {
    Write-Host "Usage: .\Set-BotSetting.ps1 KEY=VALUE [KEY=VALUE ...]" -ForegroundColor Yellow
    exit 1
}
if (-not (Test-Path $envPath)) {
    Write-Host "  No .env here. Run this from the fms-trading-bot folder." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path $python)) {
    Write-Host "  .venv missing - run deploy\setup-windows.ps1 first." -ForegroundColor Red
    exit 1
}

# Parse first, change nothing until every pair is valid.
$pairs = [ordered]@{}
foreach ($s in $Setting) {
    if ($s -notmatch '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*(.*?)\s*$') {
        Write-Host "  Not a KEY=VALUE pair: '$s'" -ForegroundColor Red
        Write-Host "  Quote values containing spaces: `"PROFIT_STAGES=0.10:0,0.25:0.10`"" -ForegroundColor Red
        exit 1
    }
    $key = $Matches[1].ToUpper()
    $value = $Matches[2]
    # An unquoted '#' would be read as an inline comment and silently
    # truncate the value, so quote anything that contains one.
    if ($value -match '#' -and $value -notmatch '^".*"$') { $value = '"' + $value + '"' }
    $pairs[$key] = $value
}

Write-Host "=== Changing .env ===" -ForegroundColor Cyan
$lines = Get-Content $envPath -Encoding UTF8
$updated = New-Object System.Collections.Generic.List[string]
$seen = @{}

foreach ($line in $lines) {
    $matched = $false
    foreach ($key in $pairs.Keys) {
        if ($line -match "^\s*$([regex]::Escape($key))\s*=") {
            $old = ($line -split '=', 2)[1]
            Write-Host ("  {0,-24} {1}  ->  {2}" -f $key, $old.Trim(), $pairs[$key]) -ForegroundColor Yellow
            $updated.Add("$key=$($pairs[$key])")
            $seen[$key] = $true
            $matched = $true
            break
        }
    }
    if (-not $matched) { $updated.Add($line) }
}
foreach ($key in $pairs.Keys) {
    if (-not $seen.ContainsKey($key)) {
        Write-Host ("  {0,-24} (new)  ->  {1}" -f $key, $pairs[$key]) -ForegroundColor Green
        $updated.Add("$key=$($pairs[$key])")
    }
}

if ($WhatIf) {
    Write-Host "`n  -WhatIf: nothing was written." -ForegroundColor Yellow
    exit 0
}

# --- stop, write, validate ---------------------------------------------
Write-Host "`nStopping the bot..."
Stop-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$PSScriptRoot*" } |
    ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }

Copy-Item $envPath "$envPath.bak-setting" -Force
# Not Set-Content -Encoding UTF8: Windows PowerShell 5.1 writes a byte-order
# mark, which becomes part of the first variable's name.
$noBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllLines($envPath, [string[]]$updated, $noBom)
Write-Host "  written (previous copy in .env.bak-setting)"

Write-Host "`nChecking the configuration..."
& $python check_config.py
if ($LASTEXITCODE -ne 0) {
    Write-Host "`n  The new .env is not usable. Restoring the previous one." -ForegroundColor Red
    Copy-Item "$envPath.bak-setting" $envPath -Force
    Write-Host "  Restored. The bot has NOT been restarted." -ForegroundColor Red
    exit 1
}

if ($NoRestart) {
    Write-Host "`n  -NoRestart: the bot is stopped. Start it with:" -ForegroundColor Yellow
    Write-Host "    Start-ScheduledTask -TaskName $task"
    exit 0
}

Write-Host "`nRestarting the bot..."
Start-ScheduledTask -TaskName $task
Start-Sleep -Seconds 8
$state = (Get-ScheduledTask -TaskName $task -ErrorAction SilentlyContinue).State
Write-Host "  scheduled task: $state"

Write-Host "`n=== Done ===" -ForegroundColor Cyan
if (Test-Path .\bot.log) {
    Get-Content .\bot.log -Tail 8 | ForEach-Object { "  $_" }
}
Write-Host "`nOn your phone: /status, and /evidence to see the record."
