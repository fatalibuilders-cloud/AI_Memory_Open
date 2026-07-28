<#
.SYNOPSIS
    Runs tgscalper using the project's virtual environment.

.DESCRIPTION
    Saves you from activating .venv by hand. Every argument is passed straight
    through to the tgscalper CLI.

.EXAMPLE
    .\windows\run.ps1 doctor
    .\windows\run.ps1 chats
    .\windows\run.ps1 symbols --search volatility
    .\windows\run.ps1 run
    .\windows\run.ps1 report --days 7
#>

$ErrorActionPreference = 'Stop'

# Resolve the project root from this script's own location, so the command
# works from any working directory.
$projectDir = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectDir '.venv\Scripts\python.exe'

if (-not (Test-Path $venvPython)) {
    Write-Host "Virtual environment not found at $venvPython" -ForegroundColor Red
    Write-Host 'Run the installer first:' -ForegroundColor Yellow
    Write-Host '    powershell -ExecutionPolicy Bypass -File .\windows\setup.ps1'
    exit 1
}

Push-Location $projectDir
try {
    & $venvPython -m tgscalper @args
    exit $LASTEXITCODE
} finally {
    Pop-Location
}
