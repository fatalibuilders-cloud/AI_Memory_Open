<#
.SYNOPSIS
    ATR trailing stops (chandelier exit) for every open position.

.DESCRIPTION
    Reads open positions and price history from MetaTrader 5, computes an
    ATR trailing stop for each, and sends the new stop back to the broker.

    PowerShell cannot talk to MT5 directly -- its API is a Python package
    that speaks to the terminal over local IPC -- so this calls bridge.py,
    which reuses the bot's own broker layer. That means it works against
    Exness, Deriv, Vantage, OANDA and Binance unchanged.

    STOP THE BOT FIRST. Two processes sharing one MT5 terminal interfere,
    and both would be moving the same stops.

    Note: the bot already does this continuously when TRAIL_ATR_MULT is
    set. Use this script for positions opened by hand or by another EA,
    or to watch the arithmetic on real numbers.

.EXAMPLE
    .\Trail-Stops.ps1
    Show what it would do. Changes nothing.

.EXAMPLE
    .\Trail-Stops.ps1 -Apply -Multiplier 1.5
    Move the stops.

.EXAMPLE
    .\Trail-Stops.ps1 -Apply -Watch -IntervalSeconds 30
    Keep trailing until you press Ctrl+C.
#>

param(
    [double]$Multiplier = 1.5,
    [int]$Period = 14,
    [string]$Timeframe = "M5",
    [string]$Account,
    # Leave a position alone until it is at least this far ahead, in cash.
    [double]$StartMoney = 0.0,
    [switch]$Apply,
    [switch]$Watch,
    [int]$IntervalSeconds = 30
)

Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Host "  .venv missing - run deploy\setup-windows.ps1 first." -ForegroundColor Red
    exit 1
}

# Peaks must survive between passes: a trailing stop measured from the
# current price follows the trade back down, which is not a trailing stop.
$peakFile = Join-Path $PSScriptRoot "trail_peaks.json"
$script:Peaks = @{}
if (Test-Path $peakFile) {
    try {
        (Get-Content $peakFile -Raw | ConvertFrom-Json).PSObject.Properties |
            ForEach-Object { $script:Peaks[$_.Name] = [double]$_.Value }
    } catch {
        Write-Host "  (could not read $peakFile - peaks start fresh)" -ForegroundColor Yellow
    }
}

function Save-Peaks {
    try { $script:Peaks | ConvertTo-Json -Compress | Set-Content $peakFile -Encoding ASCII }
    catch { Write-Host "  (could not save peaks: $_)" -ForegroundColor Yellow }
}

function Invoke-Bridge {
    param([string[]]$BridgeArgs)
    $all = @("bridge.py") + $BridgeArgs
    if ($Account) { $all += @("--account", $Account) }
    $raw = & $python @all 2>&1
    try { $result = $raw | ConvertFrom-Json }
    catch {
        return [pscustomobject]@{ ok = $false; error = "bridge did not return JSON: $raw" }
    }
    return $result
}

function Get-ATR {
    <#  Wilder's Average True Range.
        Seeded with a simple mean of the first `Period` true ranges, then
        smoothed -- the same definition MetaTrader and the bot use, so the
        three agree on the same bars. #>
    param(
        [double[]]$High,
        [double[]]$Low,
        [double[]]$Close,
        [int]$Period = 14
    )
    $n = $Close.Count
    if ($n -lt ($Period + 1) -or $High.Count -ne $n -or $Low.Count -ne $n) {
        return $null
    }
    $tr = New-Object System.Collections.Generic.List[double]
    for ($i = 1; $i -lt $n; $i++) {
        $prev = $Close[$i - 1]
        $a = $High[$i] - $Low[$i]
        $b = [Math]::Abs($High[$i] - $prev)
        $c = [Math]::Abs($Low[$i] - $prev)
        $tr.Add([Math]::Max($a, [Math]::Max($b, $c)))
    }
    if ($tr.Count -lt $Period) { return $null }
    $value = 0.0
    for ($i = 0; $i -lt $Period; $i++) { $value += $tr[$i] }
    $value = $value / $Period
    for ($i = $Period; $i -lt $tr.Count; $i++) {
        $value = (($value * ($Period - 1)) + $tr[$i]) / $Period
    }
    return $value
}

function Get-ATRTrailingStop {
    <#  Chandelier exit.

        Measured from the best price the trade has REACHED, not the price
        now: trailing off the current price lets the stop follow the trade
        back down. And it only ever tightens, so a stop is never moved
        further from price to give a losing trade more room.

        MinStopDistance is the broker's own limit. A stop closer than that
        is rejected outright (MT5 retcode 10011, "bad stops") and the
        update is silently lost, so the candidate is pulled back to the
        closest legal place instead of being thrown away. #>
    param(
        [double]$CurrentPrice,
        [double]$HighestSinceEntry,
        [double]$LowestSinceEntry,
        [double]$ATR,
        [double]$Multiplier = 1.5,
        [double]$CurrentStop = 0,
        [double]$MinStopDistance = 0,
        [string]$Direction = "buy"
    )

    $candidateStop = if ($Direction -eq "buy") {
        $HighestSinceEntry - ($Multiplier * $ATR)
    } else {
        $LowestSinceEntry + ($Multiplier * $ATR)
    }

    if ($MinStopDistance -gt 0) {
        if ($Direction -eq "buy") {
            $candidateStop = [Math]::Min($candidateStop, $CurrentPrice - $MinStopDistance)
        } else {
            $candidateStop = [Math]::Max($candidateStop, $CurrentPrice + $MinStopDistance)
        }
    }

    if ($CurrentStop -eq 0) { return $candidateStop }

    # Ratchet only -- never let the stop move backward
    if ($Direction -eq "buy") {
        return [Math]::Max($CurrentStop, $candidateStop)
    } else {
        return [Math]::Min($CurrentStop, $candidateStop)
    }
}

function Invoke-TrailPass {
    $pos = Invoke-Bridge @("positions")
    if (-not $pos.ok) {
        Write-Host "  Could not read positions: $($pos.error)" -ForegroundColor Red
        Write-Host "  Is MT5 open and logged in, and the bot stopped?" -ForegroundColor Red
        return $false
    }
    if ($pos.positions.Count -eq 0) {
        Write-Host "  No open positions." -ForegroundColor DarkGray
        return $true
    }

    Write-Host ("  {0,-12} {1,-5} {2,10} {3,10} {4,10} {5,10}  {6}" -f `
        "symbol", "side", "price", "peak", "stop now", "new stop", "")
    Write-Host ("  " + ("-" * 74))

    $atrCache = @{}
    $infoCache = @{}
    foreach ($p in $pos.positions) {
        if (-not $atrCache.ContainsKey($p.symbol)) {
            $b = Invoke-Bridge @("bars", $p.symbol, $Timeframe, [string]($Period + 60))
            if (-not $b.ok) {
                Write-Host ("  {0,-12} no bars: {1}" -f $p.symbol, $b.error) -ForegroundColor Yellow
                continue
            }
            $atrCache[$p.symbol] = Get-ATR -High $b.high -Low $b.low -Close $b.close -Period $Period
            $infoCache[$p.symbol] = Invoke-Bridge @("info", $p.symbol)
        }
        $atr = $atrCache[$p.symbol]
        $info = $infoCache[$p.symbol]
        if ($null -eq $atr -or $atr -le 0 -or -not $info.ok) {
            Write-Host ("  {0,-12} could not measure" -f $p.symbol) -ForegroundColor Yellow
            continue
        }

        if ($p.profit -lt $StartMoney) {
            Write-Host ("  {0,-12} {1,-5} {2,10:N5} {3,52}" -f `
                $p.symbol, $p.side, $info.bid, "only $($p.profit) ahead - waiting") `
                -ForegroundColor DarkGray
            continue
        }

        # A long is closed at the bid, a short at the ask. Tracking the peak
        # on the entry side flatters every trade by one spread.
        $price = if ($p.side -eq "buy") { [double]$info.bid } else { [double]$info.ask }

        $key = [string]$p.ticket
        if ($script:Peaks.ContainsKey($key)) {
            $peak = if ($p.side -eq "buy") {
                [Math]::Max($script:Peaks[$key], $price)
            } else {
                [Math]::Min($script:Peaks[$key], $price)
            }
        } else {
            $peak = $price
        }
        $script:Peaks[$key] = $peak

        $newStop = Get-ATRTrailingStop -CurrentPrice $price `
            -HighestSinceEntry $peak -LowestSinceEntry $peak `
            -ATR $atr -Multiplier $Multiplier -CurrentStop ([double]$p.sl) `
            -MinStopDistance ([double]$info.min_stop) -Direction $p.side

        $moved = [Math]::Abs($newStop - [double]$p.sl)
        # Below a tenth of the trail distance it is not worth a request:
        # the stop gets nudged a fraction of a tick every pass and the
        # trade server throttles you.
        $worthIt = $moved -gt ($atr * $Multiplier * 0.1)

        $note = if (-not $worthIt) { "unchanged" }
                elseif ($Apply) { "MOVING" } else { "would move" }
        $colour = if ($worthIt -and $Apply) { "Green" }
                  elseif ($worthIt) { "Cyan" } else { "DarkGray" }
        Write-Host ("  {0,-12} {1,-5} {2,10:N5} {3,10:N5} {4,10:N5} {5,10:N5}  {6}" -f `
            $p.symbol, $p.side, $price, $peak, [double]$p.sl, $newStop, $note) `
            -ForegroundColor $colour

        if ($worthIt -and $Apply) {
            $r = Invoke-Bridge @("modify", [string]$p.ticket, [string]$newStop, [string]$p.tp)
            if (-not $r.ok) {
                Write-Host "      rejected: $($r.error)" -ForegroundColor Red
            }
        }
    }
    Save-Peaks
    return $true
}

Write-Host "=== ATR trailing stops ===" -ForegroundColor Cyan
Write-Host "    $Multiplier x ATR($Period) on $Timeframe" -NoNewline
if ($StartMoney -gt 0) { Write-Host ", from +$StartMoney" -NoNewline }
Write-Host ""
if (-not $Apply) {
    Write-Host "    PREVIEW - nothing will be sent. Add -Apply to move stops." -ForegroundColor Yellow
}
Write-Host "    The bot must be STOPPED: two processes cannot share one MT5 terminal." -ForegroundColor Yellow
Write-Host ""

if ($Watch) {
    Write-Host "Watching every $IntervalSeconds seconds. Ctrl+C to stop.`n"
    while ($true) {
        Write-Host ("[{0:HH:mm:ss}]" -f (Get-Date))
        if (-not (Invoke-TrailPass)) { break }
        Write-Host ""
        Start-Sleep -Seconds $IntervalSeconds
    }
} else {
    if (-not (Invoke-TrailPass)) { exit 1 }
}
