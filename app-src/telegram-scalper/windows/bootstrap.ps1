# tgscalper bootstrap — the one-line entry point.
#
# Paste this single line into PowerShell:
#
#   irm https://raw.githubusercontent.com/fatalibuilders-cloud/AI_Memory_Open/claude/telegram-scalper-tce5zw/app-src/telegram-scalper/windows/bootstrap.ps1 | iex
#
# It installs Git if missing, downloads the project, and hands over to
# setup.ps1 which does the real work.
#
# Options — set BEFORE running the line above:
#   $env:TGSCALPER_BROKER = 'exness'          # deriv (default) | exness | default
#   $env:TGSCALPER_DIR    = 'D:\tgscalper'    # install location
#
# NOTE: no param() block here on purpose. This script is executed through
# `iex`, which cannot pass parameters — hence the environment variables.

$ErrorActionPreference = 'Stop'

# Running from `iex` means the process policy has not been relaxed yet, and
# setup.ps1 is invoked from disk, so it would otherwise be blocked.
Set-ExecutionPolicy -Scope Process Bypass -Force

$Branch     = 'claude/telegram-scalper-tce5zw'
$RepoUrl    = 'https://github.com/fatalibuilders-cloud/AI_Memory_Open.git'
$Broker     = if ($env:TGSCALPER_BROKER) { $env:TGSCALPER_BROKER } else { 'deriv' }
$InstallDir = if ($env:TGSCALPER_DIR)    { $env:TGSCALPER_DIR }    else { "$env:USERPROFILE\tgscalper" }

Write-Host "`n=== tgscalper bootstrap ===" -ForegroundColor Magenta
Write-Host "    profile : $Broker"
Write-Host "    folder  : $InstallDir`n"

# ------------------------------------------------------------------- Git
if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
    Write-Host '==> Installing Git' -ForegroundColor Cyan
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        throw 'Git is missing and winget is unavailable. Install Git from https://git-scm.com/download/win, then re-run this line.'
    }
    winget install --id Git.Git --exact --silent `
        --accept-source-agreements --accept-package-agreements | Out-Null
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User') + ';' +
                "$env:ProgramFiles\Git\cmd"
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw 'Git installed but is not on PATH yet. Close this window, open a NEW PowerShell, and paste the line again.'
    }
}
Write-Host "    git: $(git --version)" -ForegroundColor Green

# ---------------------------------------------------------------- Project
if (Test-Path (Join-Path $InstallDir '.git')) {
    Write-Host '==> Updating the existing copy' -ForegroundColor Cyan
    Push-Location $InstallDir
    try {
        git fetch origin $Branch --depth 1 2>&1 | Out-Null
        git checkout $Branch 2>&1 | Out-Null
        git reset --hard "origin/$Branch" 2>&1 | Out-Null
    } catch {
        Write-Host '    could not update; continuing with what is on disk' -ForegroundColor Yellow
    }
    Pop-Location
} else {
    Write-Host '==> Downloading the project' -ForegroundColor Cyan
    git clone --depth 1 --branch $Branch $RepoUrl $InstallDir
    if ($LASTEXITCODE -ne 0) { throw "Download failed. Check your internet connection and try again." }
}

$projectDir = Join-Path $InstallDir 'app-src\telegram-scalper'
$setup = Join-Path $projectDir 'windows\setup.ps1'
if (-not (Test-Path $setup)) { throw "setup.ps1 not found at $setup" }

Set-Location $projectDir
& $setup -Broker $Broker
