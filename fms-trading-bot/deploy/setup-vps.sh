#!/usr/bin/env bash
# One-shot setup for the FMS bot in OANDA mode on a fresh Ubuntu VPS
# (e.g. the Oracle Cloud Always-Free VM). MT5 mode needs Windows — use
# deploy/setup-windows.ps1 there instead.
#
# Usage (from the fms-trading-bot directory):
#   bash deploy/setup-vps.sh
set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="${SUDO_USER:-$USER}"
SERVICE=fms-bot

echo "==> Bot directory: $BOT_DIR (running as $RUN_USER)"

echo "==> Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip

echo "==> Creating virtualenv..."
cd "$BOT_DIR"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
# OANDA mode uses only the standard library — nothing else to install.

if [ ! -f .env ]; then
    cp .env.example .env
    sed -i 's/^BROKER=mt5/BROKER=oanda/' .env
    chmod 600 .env
    echo "==> Created .env (BROKER=oanda) — YOU MUST EDIT IT (nano .env)"
fi

echo "==> Installing systemd service..."
sudo tee /etc/systemd/system/${SERVICE}.service > /dev/null <<EOF
[Unit]
Description=FMS trading bot (OANDA)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${BOT_DIR}
ExecStart=${BOT_DIR}/.venv/bin/python ${BOT_DIR}/main.py
Restart=always
RestartSec=15
StartLimitIntervalSec=600
StartLimitBurst=20

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE}

cat <<MSG

======================================================================
Setup complete. Next steps:

  1. Edit credentials:            nano ${BOT_DIR}/.env
     Required: TG_BOT_TOKEN, TG_PASSWORD,
               OANDA_API_TOKEN, OANDA_ACCOUNT_ID (keep OANDA_ENV=practice)
     Symbols for OANDA, e.g.:     SYMBOLS=EUR_USD,XAU_USD

  2. Test in the foreground:      cd ${BOT_DIR} && .venv/bin/python main.py
     (then /login from your phone; Ctrl+C to stop)

  3. Start the service:           sudo systemctl start ${SERVICE}
     Watch logs:                  journalctl -u ${SERVICE} -f

The service auto-starts on boot and auto-restarts if the bot crashes.
======================================================================
MSG
