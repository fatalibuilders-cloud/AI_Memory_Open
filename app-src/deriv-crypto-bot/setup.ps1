# One-command setup for Windows PowerShell.
# Creates a virtual environment, installs dependencies, runs the tests, and
# scaffolds a .env for you to fill in. Safe to re-run - never overwrites .env.
#
#   .\setup.ps1
#
# If PowerShell refuses to run this ("running scripts is disabled"), use:
#   powershell -ExecutionPolicy Bypass -File .\setup.ps1

$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

Write-Host ""
Write-Host "=============================================================="
Write-Host "  DERIV CRYPTO BOT - SETUP (Windows)"
Write-Host "=============================================================="
Write-Host ""

# -- Python ---------------------------------------------------------------

$python = $null
foreach ($candidate in @("python", "py")) {
    if (Get-Command $candidate -ErrorAction SilentlyContinue) {
        $python = $candidate
        break
    }
}

if (-not $python) {
    Write-Host "  ERROR: Python was not found." -ForegroundColor Red
    Write-Host "  Install Python 3.10 or newer from python.org, and tick"
    Write-Host "  'Add Python to PATH' during installation."
    exit 1
}

$version = & $python -c "import sys; print('%d.%d' % sys.version_info[:2])"
& $python -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)"
if ($LASTEXITCODE -ne 0) {
    Write-Host "  ERROR: Python 3.10 or newer is required (found $version)." -ForegroundColor Red
    exit 1
}
Write-Host "  [ok] Python $version"

# -- Virtual environment --------------------------------------------------

if (-not (Test-Path ".venv")) {
    & $python -m venv .venv
    Write-Host "  [ok] Created virtual environment (.venv)"
} else {
    Write-Host "  [ok] Virtual environment already exists"
}

# Call the venv's python directly. Activating inside a script would not
# persist to your shell anyway, and this avoids execution-policy trouble.
$venvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "  ERROR: virtual environment looks broken ($venvPython missing)." -ForegroundColor Red
    Write-Host "  Delete the .venv folder and run this again."
    exit 1
}

& $venvPython -m pip install --quiet --upgrade pip
& $venvPython -m pip install --quiet -r requirements.txt
Write-Host "  [ok] Installed dependencies"

& $venvPython -m pip install --quiet pytest
Write-Host "  [ok] Installed pytest"

# -- Configuration --------------------------------------------------------

$createdEnv = $false
if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "  [ok] Created .env from the template"
    $createdEnv = $true
} else {
    Write-Host "  [ok] .env already exists - left untouched"
}

# -- Self-test ------------------------------------------------------------

Write-Host ""
Write-Host "  Running the test suite..."
$testOutput = & $venvPython -m pytest 2>&1 | Out-String
if ($LASTEXITCODE -ne 0) {
    Write-Host "  [!!] Tests failed. Run '.venv\Scripts\python.exe -m pytest' to see why." -ForegroundColor Red
    Write-Host $testOutput
    exit 1
}
$summary = ($testOutput -split "`n" | Select-String -Pattern "\d+ (passed|failed)" | Select-Object -Last 1)
if ($summary) {
    Write-Host "  [ok] $($summary.ToString().Trim())"
} else {
    Write-Host "  [ok] tests passed"
}

# -- What next ------------------------------------------------------------

Write-Host ""
Write-Host "=============================================================="
Write-Host "  NEXT STEPS"
Write-Host "=============================================================="
Write-Host ""
if ($createdEnv) {
    Write-Host "  1. Get a Deriv API token:"
    Write-Host "       - Log in at deriv.com, switch to your VIRTUAL (demo) account"
    Write-Host "       - Settings > API token"
    Write-Host "       - Tick 'Read' and 'Trade' only. Not Payments. Not Admin."
    Write-Host ""
    Write-Host "  2. Open .env in Notepad and paste the token in:"
    Write-Host "       notepad .env"
    Write-Host "     Find the line starting DERIV_API_TOKEN= and put it after the ="
    Write-Host ""
    Write-Host "  3. Verify it works (this places no trades):"
} else {
    Write-Host "  1. Verify your setup (this places no trades):"
}
Write-Host "       .venv\Scripts\python.exe -m deriv_bot.check"
Write-Host ""
Write-Host "  The check tells you whether everything is wired up, and prints"
Write-Host "  the real payout ratio to use when backtesting."
Write-Host ""
Write-Host "  If you open a new terminal later, either cd back here first:"
Write-Host "       cd '$PSScriptRoot'"
Write-Host "  or use the full path, which works from anywhere:"
Write-Host "       & '$venvPython' -m deriv_bot.check"
Write-Host ""
Write-Host "  Real-money trading is OFF by default and stays off until you"
Write-Host "  set DERIV_ALLOW_REAL_MONEY=true yourself."
Write-Host ""
