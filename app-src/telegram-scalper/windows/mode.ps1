<#
.SYNOPSIS
    Switch between the built-in simulator and your real MT5 account.

.DESCRIPTION
    Three things, and they are not the same:

      paper   - the built-in simulator. Invented fills, no broker involved.
                Good for checking that signals parse; tells you nothing about
                spreads, slippage or rejected orders.

      broker  - orders go to MetaTrader 5. On a DEMO account that is virtual
                money with real market behaviour, which is the honest way to
                test. On a REAL account it is your money.

    Whether "broker" means demo or real money is decided by which account
    MetaTrader 5 is logged into, not by this script. The engine asks MT5
    directly and refuses to start on a real-money account unless
    execution.allow_real_money is set in config.yaml.

.EXAMPLE
    .\windows\mode.ps1 broker
    .\windows\mode.ps1 paper
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('paper', 'broker', 'live')]
    [string]$Mode,

    # Do not restart the copier afterwards.
    [switch]$NoRestart
)

$ErrorActionPreference = 'Stop'

$projectDir = Split-Path -Parent $PSScriptRoot
Set-Location $projectDir

$configPath = Join-Path $projectDir 'config.yaml'
$envPath = Join-Path $projectDir '.env'
if (-not (Test-Path $configPath)) { throw "config.yaml not found in $projectDir" }
if (-not (Test-Path $envPath))    { throw ".env not found in $projectDir" }

$wantBroker = $Mode -in @('broker', 'live')
$target = if ($wantBroker) { 'live' } else { 'paper' }

function Write-Step { param($m) Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Ok   { param($m) Write-Host "    OK  $m" -ForegroundColor Green }
function Write-Warn { param($m) Write-Host "    !   $m" -ForegroundColor Yellow }

# ------------------------------------------------------------- config.yaml
Write-Step "Setting execution.mode to '$target'"
$config = Get-Content $configPath -Raw
# Targeted replacement keeps every comment in the file intact, which a YAML
# round-trip would strip.
$updated = [regex]::Replace(
    $config,
    '(?m)^(\s*mode:\s*)(paper|live)(\s*(?:#.*)?)$',
    { param($m) $m.Groups[1].Value + $target + $m.Groups[3].Value },
    1
)
if ($updated -eq $config -and $config -notmatch "(?m)^\s*mode:\s*$target\b") {
    throw "Could not find an 'execution.mode:' line in config.yaml to change."
}
Set-Content -Path $configPath -Value $updated -NoNewline
Write-Ok "config.yaml -> mode: $target"

# --------------------------------------------------------------------- .env
Write-Step 'Setting the live acknowledgement in .env'
$ack = if ($wantBroker) { 'I_UNDERSTAND_THE_RISK' } else { '' }
$lines = [System.Collections.Generic.List[string]](Get-Content $envPath)
$found = $false
for ($i = 0; $i -lt $lines.Count; $i++) {
    if ($lines[$i] -match '^\s*TGSCALPER_ALLOW_LIVE\s*=') {
        $lines[$i] = "TGSCALPER_ALLOW_LIVE=$ack"
        $found = $true
    }
}
if (-not $found) { $lines.Add("TGSCALPER_ALLOW_LIVE=$ack") }
[System.IO.File]::WriteAllLines($envPath, $lines, [System.Text.UTF8Encoding]::new($false))
Write-Ok $(if ($wantBroker) { '.env -> acknowledgement set' } else { '.env -> acknowledgement cleared' })

if ($wantBroker) {
    Write-Warn 'MetaTrader 5 must be OPEN, logged in, with Algo Trading enabled.'
    Write-Warn 'Whichever account MT5 is logged into is the account that gets traded.'
}

# ------------------------------------------------------------------- verify
Write-Step 'Checking what that connects to'
& (Join-Path $PSScriptRoot 'run.ps1') doctor

# ------------------------------------------------------------------ restart
if (-not $NoRestart) {
    Write-Step 'Restarting the copier so the change takes effect'
    $running = @(Get-CimInstance Win32_Process -Filter "Name='python.exe'" -ErrorAction SilentlyContinue |
        Where-Object { $_.CommandLine -like '*tgscalper*' })
    foreach ($process in $running) {
        Stop-Process -Id $process.ProcessId -Force -ErrorAction SilentlyContinue
        Write-Ok "stopped old copier (PID $($process.ProcessId))"
    }
    Start-Sleep -Seconds 2
    & (Join-Path $PSScriptRoot 'autostart.ps1') -KeepSleepSettings
} else {
    Write-Warn 'Not restarted. The change applies next time it starts.'
}
