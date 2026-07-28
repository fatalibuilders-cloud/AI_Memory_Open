<#
.SYNOPSIS
    One-shot installer for tgscalper on Windows.

.DESCRIPTION
    Installs Python and Git if missing, fetches the project, creates a virtual
    environment, installs dependencies including the MetaTrader5 package,
    writes .env from your answers, and runs the doctor check.

    Safe to re-run: it updates an existing install and keeps your .env unless
    you ask it to overwrite.

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File setup.ps1
    powershell -ExecutionPolicy Bypass -File setup.ps1 -Broker deriv
#>

[CmdletBinding()]
param(
    # Which ready-made config profile to start from.
    [ValidateSet('deriv', 'exness', 'default')]
    [string]$Broker = 'deriv',

    # Where to install. Defaults to a folder in your user profile.
    [string]$InstallDir = "$env:USERPROFILE\tgscalper",

    # Skip the interactive credential prompts (write .env yourself later).
    [switch]$NoPrompt
)

$ErrorActionPreference = 'Stop'
$RepoUrl = 'https://github.com/fatalibuilders-cloud/AI_Memory_Open.git'
$ProjectSubPath = 'app-src\telegram-scalper'

function Write-Step   { param($m) Write-Host "`n==> $m" -ForegroundColor Cyan }
function Write-Ok     { param($m) Write-Host "    OK  $m" -ForegroundColor Green }
function Write-Warn   { param($m) Write-Host "    !   $m" -ForegroundColor Yellow }
function Write-Fail   { param($m) Write-Host "    X   $m" -ForegroundColor Red }

function Test-Command {
    param($Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Install-WithWinget {
    param($Id, $Label)
    if (-not (Test-Command 'winget')) {
        throw "$Label is missing and winget is unavailable. Install $Label manually, then re-run this script."
    }
    Write-Warn "$Label not found - installing via winget (this can take a few minutes)"
    winget install --id $Id --exact --silent --accept-source-agreements --accept-package-agreements | Out-Null
    # winget updates PATH for new processes only; refresh this session.
    $env:Path = [Environment]::GetEnvironmentVariable('Path', 'Machine') + ';' +
                [Environment]::GetEnvironmentVariable('Path', 'User')
}

Write-Host @"
+--------------------------------------------------------------+
|  tgscalper - Telegram signal copier                          |
|  Windows installer                                           |
+--------------------------------------------------------------+
"@ -ForegroundColor Magenta

# ---------------------------------------------------------------- 1. Python
Write-Step 'Checking Python'
$python = $null
foreach ($candidate in @('python', 'python3', 'py')) {
    if (Test-Command $candidate) {
        try {
            $version = & $candidate --version 2>&1
            if ($version -match 'Python (\d+)\.(\d+)') {
                $major = [int]$Matches[1]; $minor = [int]$Matches[2]
                if ($major -eq 3 -and $minor -ge 10) { $python = $candidate; break }
                Write-Warn "$candidate is $version - need 3.10 or newer"
            }
        } catch { }
    }
}
if (-not $python) {
    Install-WithWinget -Id 'Python.Python.3.12' -Label 'Python 3.12'
    $python = 'python'
    if (-not (Test-Command $python)) {
        throw 'Python installed but is not on PATH yet. Close this window, open a NEW PowerShell, and re-run.'
    }
}
Write-Ok (& $python --version)

# ------------------------------------------------------------------ 2. Git
Write-Step 'Checking Git'
if (-not (Test-Command 'git')) {
    Install-WithWinget -Id 'Git.Git' -Label 'Git'
    if (-not (Test-Command 'git')) {
        throw 'Git installed but is not on PATH yet. Close this window, open a NEW PowerShell, and re-run.'
    }
}
Write-Ok (git --version)

# ------------------------------------------------------------- 3. Get code
Write-Step 'Fetching the project'
$repoRoot = $InstallDir
$projectDir = Join-Path $repoRoot $ProjectSubPath

if (Test-Path (Join-Path $repoRoot '.git')) {
    Write-Ok "Existing install found at $repoRoot - updating"
    Push-Location $repoRoot
    try { git pull --ff-only 2>&1 | Out-Null } catch { Write-Warn 'Could not fast-forward; keeping local state' }
    Pop-Location
} else {
    # Already inside a checkout? Use it rather than cloning a second copy.
    $here = Get-Location
    if ((Test-Path (Join-Path $here 'src\tgscalper')) -and (Test-Path (Join-Path $here 'pyproject.toml'))) {
        $projectDir = $here.Path
        Write-Ok "Using the checkout in the current directory: $projectDir"
    } else {
        Write-Host "    cloning $RepoUrl"
        Write-Host "    (a private repo will ask you to sign in to GitHub)"
        git clone --depth 1 $RepoUrl $repoRoot
        if ($LASTEXITCODE -ne 0) {
            throw "Clone failed. If the repository is private, sign in when prompted, or download the ZIP from GitHub, extract it, and run this script from inside $ProjectSubPath."
        }
    }
}
if (-not (Test-Path $projectDir)) { throw "Project folder not found at $projectDir" }
Set-Location $projectDir
Write-Ok $projectDir

# --------------------------------------------------- 4. Virtual environment
Write-Step 'Creating the virtual environment'
if (-not (Test-Path '.venv')) { & $python -m venv .venv }
$venvPython = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path $venvPython)) { throw "Virtual environment was not created at $venvPython" }
Write-Ok '.venv'

Write-Step 'Installing dependencies (a minute or two)'
& $venvPython -m pip install --upgrade pip --quiet
& $venvPython -m pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) { throw 'Dependency install failed - check the output above.' }
Write-Ok 'telethon, PyYAML, python-dotenv, pytest'

# The package lives under src\, so it must be installed for `python -m tgscalper`
# to resolve. Editable, so a `git pull` takes effect without reinstalling.
& $venvPython -m pip install -e . --quiet
if ($LASTEXITCODE -ne 0) { throw 'Installing the tgscalper package failed - check the output above.' }
Write-Ok 'tgscalper (editable install)'

# MetaTrader5 is Windows-only and lives outside requirements.txt so the test
# suite stays runnable on other platforms.
& $venvPython -m pip install MetaTrader5 --quiet
if ($LASTEXITCODE -eq 0) { Write-Ok 'MetaTrader5' }
else { Write-Warn 'MetaTrader5 failed to install - live trading will not work until it does' }

# --------------------------------------------------------------- 5. Config
Write-Step 'Setting up config.yaml'
$profileMap = @{ deriv = 'config.deriv.yaml'; exness = 'config.example.yaml'; default = 'config.example.yaml' }
$source = $profileMap[$Broker]
if (Test-Path 'config.yaml') {
    Write-Ok 'config.yaml already exists - left untouched'
} else {
    Copy-Item $source 'config.yaml'
    Write-Ok "config.yaml created from $source ($Broker profile)"
}

# ------------------------------------------------------------------ 6. .env
Write-Step 'Setting up .env'
$writeEnv = $true
if (Test-Path '.env') {
    if ($NoPrompt) { $writeEnv = $false }
    else {
        $answer = Read-Host '    .env already exists. Overwrite it? (y/N)'
        $writeEnv = ($answer -eq 'y' -or $answer -eq 'Y')
    }
    if (-not $writeEnv) { Write-Ok '.env left untouched' }
}

if ($writeEnv -and $NoPrompt) {
    Copy-Item '.env.example' '.env' -Force
    Write-Ok '.env created from the template - fill it in before running'
    $writeEnv = $false
}

if ($writeEnv) {
    Write-Host ''
    Write-Host '    TELEGRAM --------------------------------------------------' -ForegroundColor White
    Write-Host '    Get these from https://my.telegram.org -> API development tools'
    Write-Host '    They identify the app, not your account. You sign in with your'
    Write-Host '    phone once and a session file is stored locally.'
    Write-Host ''
    $apiId    = Read-Host '    TG_API_ID'
    $apiHash  = Read-Host '    TG_API_HASH'
    $phone    = Read-Host '    TG_PHONE (with country code, e.g. +254700000000)'

    Write-Host ''
    Write-Host '    BROKER (MetaTrader 5) --------------------------------------' -ForegroundColor White
    if ($Broker -eq 'deriv') {
        Write-Host '    Use the MT5 account created in your Deriv dashboard -' -ForegroundColor Yellow
        Write-Host '    NOT your deriv.com website login.' -ForegroundColor Yellow
    } elseif ($Broker -eq 'exness') {
        Write-Host '    Use the MT5 account from your Exness personal area.' -ForegroundColor Yellow
    }
    Write-Host ''
    $mt5Login  = Read-Host '    MT5_LOGIN (account number)'
    $mt5Secure = Read-Host '    MT5_PASSWORD' -AsSecureString
    $mt5Pass   = [Runtime.InteropServices.Marshal]::PtrToStringAuto(
                    [Runtime.InteropServices.Marshal]::SecureStringToBSTR($mt5Secure))
    $mt5Server = Read-Host '    MT5_SERVER (exactly as shown on the account)'

    $terminal = ''
    foreach ($guess in @(
        "$env:ProgramFiles\MetaTrader 5\terminal64.exe",
        "$env:ProgramFiles\Deriv MT5\terminal64.exe",
        "$env:ProgramFiles\Exness MT5\terminal64.exe",
        "${env:ProgramFiles(x86)}\MetaTrader 5\terminal64.exe"
    )) {
        if (Test-Path $guess) { $terminal = $guess; break }
    }
    if ($terminal) { Write-Ok "MT5 terminal found: $terminal" }
    else { Write-Warn 'MT5 terminal not found in the usual places - leaving the path blank so it attaches to a running terminal' }

    $envBody = @"
# Written by windows\setup.ps1. Treat this file as secret.
TG_API_ID=$apiId
TG_API_HASH=$apiHash
TG_PHONE=$phone
TG_2FA_PASSWORD=

MT5_LOGIN=$mt5Login
MT5_PASSWORD=$mt5Pass
MT5_SERVER=$mt5Server
MT5_TERMINAL_PATH=$terminal

# Live trading stays OFF until this says exactly I_UNDERSTAND_THE_RISK
# *and* config.yaml has execution.mode: live.
TGSCALPER_ALLOW_LIVE=
"@
    Set-Content -Path '.env' -Value $envBody -Encoding UTF8
    Write-Ok '.env written'
}

# --------------------------------------------------------------- 7. Verify
Write-Step 'Running the self-check'
& $venvPython -m tgscalper doctor
Write-Host ''

# ----------------------------------------------------------------- 8. Done
$runScript = Join-Path $projectDir 'windows\run.ps1'
Write-Host @"

+--------------------------------------------------------------+
|  Installed.                                                  |
+--------------------------------------------------------------+

Installed at: $projectDir

Next, in order:

  1. Find your group ids (asks for your phone code the first time):
         .\windows\run.ps1 chats

  2. Put up to 5 ids into config.yaml under telegram.groups
         notepad config.yaml

  3. Check your broker's symbol names line up:
         .\windows\run.ps1 symbols

  4. Watch it on PAPER for a few days - real signals, simulated fills:
         .\windows\run.ps1 run
         .\windows\run.ps1 report --days 3

  5. Only then consider live trading. It needs BOTH:
         config.yaml  ->  execution.mode: live
         .env         ->  TGSCALPER_ALLOW_LIVE=I_UNDERSTAND_THE_RISK

Keep MetaTrader 5 open and logged in with Algo Trading enabled while the
bot runs. On a laptop that sleeps, it stops copying - a Windows VPS is the
usual home for this.

"@ -ForegroundColor Green
