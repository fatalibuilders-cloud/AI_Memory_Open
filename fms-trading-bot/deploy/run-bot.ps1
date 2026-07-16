# Keeps the bot alive: restarts it 15s after any exit/crash.
# Started hidden by the 'FMSTradingBot' scheduled task; output goes to bot.log.
$BotDir = Split-Path -Parent $PSScriptRoot
Set-Location $BotDir
while ($true) {
    & "$BotDir\.venv\Scripts\python.exe" "$BotDir\main.py" *>> "$BotDir\bot.log"
    Add-Content "$BotDir\bot.log" "[runner] bot exited at $(Get-Date -Format s), restarting in 15s"
    Start-Sleep -Seconds 15
}
