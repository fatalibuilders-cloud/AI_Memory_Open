<#
.SYNOPSIS
    Fills in .env by asking questions, one at a time.

.DESCRIPTION
    Use this when setup.ps1's prompts were skipped, or when a credential
    changes. Existing values are kept unless you type a new one, so it is safe
    to re-run just to fix a single field.

    Everything is typed at a prompt rather than pasted as a command, so
    PowerShell never tries to interpret your api hash as code.

.EXAMPLE
    .\windows\credentials.ps1
    .\windows\credentials.ps1 -TelegramOnly
#>

[CmdletBinding()]
param(
    [switch]$TelegramOnly,
    [switch]$BrokerOnly,
    [switch]$SkipDoctor
)

$ErrorActionPreference = 'Stop'

$projectDir = Split-Path -Parent $PSScriptRoot
$envPath = Join-Path $projectDir '.env'

# ---------------------------------------------------------- read what exists
$values = [ordered]@{}
if (Test-Path $envPath) {
    foreach ($line in Get-Content $envPath) {
        if ($line -match '^\s*([A-Z0-9_]+)\s*=\s*(.*)$') {
            $values[$Matches[1]] = $Matches[2]
        }
    }
    Write-Host "Editing $envPath" -ForegroundColor Cyan
} else {
    Write-Host "Creating $envPath" -ForegroundColor Cyan
}

function Test-BotToken {
    param([string]$Value)
    return $Value -match '^\d{6,}:[A-Za-z0-9_-]{30,}$'
}

function Ask {
    param(
        [string]$Key,
        [string]$Label,
        [switch]$Secret,
        # Returns '' when the value is acceptable, or the reason it is not.
        [scriptblock]$Validate
    )
    $current = $values[$Key]

    # A value already on disk that fails validation must not be keepable —
    # otherwise pressing Enter silently preserves the mistake, which is exactly
    # how a bot token survived in TG_API_ID through several passes.
    $currentBad = ''
    if ($current -and $Validate) { $currentBad = & $Validate $current }

    while ($true) {
        $shown = if (-not $current) { '(empty)' }
                 elseif ($currentBad) { "(current value is INVALID: $currentBad)" }
                 elseif ($Secret)     { '(set - press Enter to keep)' }
                 else                 { "(current: $current)" }

        Write-Host ''
        Write-Host "  $Label" -ForegroundColor White
        Write-Host "  $shown" -ForegroundColor $(if ($currentBad) { 'Red' } else { 'DarkGray' })
        if ($currentBad) {
            Write-Host '  Enter a correct value - the old one cannot be kept.' -ForegroundColor Yellow
        }
        $answer = Read-Host "  $Key"

        if ([string]::IsNullOrWhiteSpace($answer)) {
            if (-not $currentBad) { return }        # keep what was there
            Write-Host '  Skipping leaves this broken.' -ForegroundColor Yellow
            $again = Read-Host '  Type SKIP to leave it anyway, or press Enter to try again'
            if ($again -eq 'SKIP') { return }
            continue
        }

        $answer = $answer.Trim()
        if ($Validate) {
            $problem = & $Validate $answer
            if ($problem) {
                Write-Host "  Not accepted: $problem" -ForegroundColor Red
                continue
            }
        }
        $values[$Key] = $answer
        return
    }
}

# Catches the single most common mistake: pasting a BotFather token where the
# api_id belongs. They are unrelated credentials that look equally official.
$ValidateApiId = {
    param($v)
    if (Test-BotToken $v) {
        return 'that is a BotFather BOT TOKEN (it has a colon). The api_id is just digits, from my.telegram.org'
    }
    if ($v -notmatch '^\d+$') { return 'the api_id is digits only, no colon, no quotes' }
    if ($v.Length -lt 5)      { return 'too short to be an api_id' }
    return ''
}

$ValidateApiHash = {
    param($v)
    if (Test-BotToken $v) { return 'that is a BotFather bot token, not the api_hash' }
    if ($v -notmatch '^[0-9a-fA-F]{32}$') {
        return 'the api_hash is exactly 32 letters/digits from my.telegram.org'
    }
    return ''
}

Write-Host @'

Type each value and press Enter. Press Enter on its own to keep the current
value. Pasting into a prompt is safe - PowerShell will not try to run it.
'@ -ForegroundColor DarkGray

# ------------------------------------------------------------------ Telegram
if (-not $BrokerOnly) {
    Write-Host "`n--- TELEGRAM -------------------------------------------------" -ForegroundColor Yellow
    Write-Host @'
  Get these from https://my.telegram.org
    1. Log in with your phone number and the code Telegram sends you
    2. Open "API development tools"
    3. Create an app (any name, e.g. "signals") if you have not already
    4. Copy App api_id and App api_hash from that page
'@ -ForegroundColor DarkGray

    Ask -Key 'TG_API_ID'   -Label 'App api_id (a number, ~8 digits, NO colon)' -Validate $ValidateApiId
    Ask -Key 'TG_API_HASH' -Label 'App api_hash (32 letters and digits)' -Validate $ValidateApiHash
    Ask -Key 'TG_PHONE'    -Label 'Your phone number with country code, e.g. +254700000000'
    Ask -Key 'TG_2FA_PASSWORD' -Label 'Telegram 2FA password - leave empty unless you set one' -Secret

    Write-Host "`n--- CONTROL BOT (optional) -----------------------------------" -ForegroundColor Yellow
    Write-Host @'
  A @BotFather bot you chat with to run the copier: /status, /selectgroup,
  /pause. It is the control panel only - it cannot read your signal groups,
  because no bot can read a chat it has not been added to. Your account
  login above still does the listening.

  Leave both blank to skip and drive everything from PowerShell instead.
    Token: @BotFather -> /mybots -> your bot -> API Token
    Your user id: message @userinfobot, or send /start to your own bot and
    read the id back from its reply.
'@ -ForegroundColor DarkGray

    Ask -Key 'TG_BOT_TOKEN' -Label 'Bot token (looks like 8739513225:AAHq...)' -Secret
    Ask -Key 'TG_OWNER_ID'  -Label 'Your Telegram user id (digits only) - the ONLY user the bot obeys'
}

# -------------------------------------------------------------------- Broker
if (-not $TelegramOnly) {
    Write-Host "`n--- BROKER (MetaTrader 5) ------------------------------------" -ForegroundColor Yellow
    Write-Host @'
  Use your MT5 TRADING ACCOUNT, not the broker website login.
    Exness: personal area -> your MT5 account number and its password
    Deriv : dashboard -> MT5 -> the account created there
'@ -ForegroundColor DarkGray

    Ask -Key 'MT5_LOGIN'    -Label 'MT5 account number'
    Ask -Key 'MT5_PASSWORD' -Label 'MT5 password' -Secret
    Ask -Key 'MT5_SERVER'   -Label 'MT5 server name, exactly as shown (e.g. Exness-MT5Real5)'

    if (-not $values['MT5_TERMINAL_PATH']) {
        foreach ($guess in @(
            "$env:ProgramFiles\MetaTrader 5\terminal64.exe",
            "$env:ProgramFiles\Exness MT5\terminal64.exe",
            "$env:ProgramFiles\Exness Technologies Ltd\terminal64.exe",
            "$env:ProgramFiles\Deriv MT5\terminal64.exe",
            "${env:ProgramFiles(x86)}\MetaTrader 5\terminal64.exe"
        )) {
            if (Test-Path $guess) {
                $values['MT5_TERMINAL_PATH'] = $guess
                Write-Host "`n  Found MT5: $guess" -ForegroundColor Green
                break
            }
        }
    }
}

# --------------------------------------------------------------------- write
foreach ($key in @('TG_API_ID','TG_API_HASH','TG_PHONE','TG_2FA_PASSWORD',
                   'TG_BOT_TOKEN','TG_OWNER_ID',
                   'MT5_LOGIN','MT5_PASSWORD','MT5_SERVER','MT5_TERMINAL_PATH',
                   'TGSCALPER_ALLOW_LIVE')) {
    if (-not $values.Contains($key)) { $values[$key] = '' }
}

$lines = [System.Collections.Generic.List[string]]::new()
$lines.Add('# Written by windows\credentials.ps1. Treat this file as secret.')
$lines.Add('')
foreach ($key in $values.Keys) { $lines.Add("$key=$($values[$key])") }

# WriteAllLines writes UTF-8 with no byte-order mark. Windows PowerShell 5.1's
# `Set-Content -Encoding UTF8` prepends a BOM, which turns the first key into
# an unreadable name for any parser that is not expecting it.
[System.IO.File]::WriteAllLines($envPath, $lines, [System.Text.UTF8Encoding]::new($false))

Write-Host "`nSaved $envPath" -ForegroundColor Green

$missing = @('TG_API_ID','TG_API_HASH','TG_PHONE') | Where-Object { -not $values[$_] }
if ($missing) {
    Write-Host "Still empty: $($missing -join ', ')" -ForegroundColor Yellow
    Write-Host 'Telegram will not connect until those are filled in.' -ForegroundColor Yellow
}

if (-not $SkipDoctor) {
    Write-Host "`nRe-checking..." -ForegroundColor Cyan
    & (Join-Path $projectDir 'windows\run.ps1') doctor
}
