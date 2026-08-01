# Keeps the bot alive: restarts it 15s after any exit/crash.
# Started hidden by the 'FMSTradingBot' scheduled task; output goes to bot.log.
$BotDir = Split-Path -Parent $PSScriptRoot
Set-Location $BotDir

# Stopping the scheduled task does not always kill the python child, and two
# bots polling one Telegram token get HTTP 409 Conflict. Clear any orphan
# from this folder before starting.
Get-CimInstance Win32_Process -Filter "Name = 'python.exe'" -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -like "*$BotDir*" -and $_.ProcessId -ne $PID } |
    ForEach-Object {
        Add-Content "$BotDir\bot.log" "[runner] stopping orphaned bot pid $($_.ProcessId)"
        Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
    }
while ($true) {
    & "$BotDir\.venv\Scripts\python.exe" "$BotDir\main.py" *>> "$BotDir\bot.log"
    Add-Content "$BotDir\bot.log" "[runner] bot exited at $(Get-Date -Format s), restarting in 15s"
    Start-Sleep -Seconds 15
}
