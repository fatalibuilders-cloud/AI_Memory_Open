#!/usr/bin/env bash
# One-shot setup for the Pocket Option bot on a fresh Ubuntu VPS
# (tested target: Oracle Cloud Always-Free Ubuntu 22.04/24.04, ARM or x86).
#
# Usage (from the pocket-option-bot directory):
#   bash deploy/setup-vps.sh
#
# What it does:
#   1. Installs python3-venv/pip
#   2. Creates .venv and installs requirements
#   3. Creates .env from the template if missing (you then edit it)
#   4. Installs + enables a systemd service (auto-start on boot, auto-restart)
set -euo pipefail

BOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUN_USER="${SUDO_USER:-$USER}"
SERVICE=pocket-bot

echo "==> Bot directory: $BOT_DIR (running as $RUN_USER)"

echo "==> Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq python3-venv python3-pip

echo "==> Creating virtualenv + installing dependencies..."
cd "$BOT_DIR"
python3 -m venv .venv
.venv/bin/pip install --quiet --upgrade pip
.venv/bin/pip install --quiet -r requirements.txt

if [ ! -f .env ]; then
    cp .env.example .env
    chmod 600 .env
    echo "==> Created .env from template — YOU MUST EDIT IT (PO_SSID etc.)"
fi

echo "==> Installing systemd service..."
sudo tee /etc/systemd/system/${SERVICE}.service > /dev/null <<EOF
[Unit]
Description=Pocket Option trading bot
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${BOT_DIR}
ExecStart=${BOT_DIR}/.venv/bin/python ${BOT_DIR}/main.py
Restart=always
RestartSec=15
# don't hammer reconnects forever if something is badly wrong
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

  1. Edit your credentials:        nano ${BOT_DIR}/.env
     (paste your PO_SSID — see README step 2; keep PO_DEMO=1 first!)

  2. Test in the foreground once:  cd ${BOT_DIR} && .venv/bin/python main.py
     (Ctrl+C to stop when you see ticks flowing)

  3. Start the service:            sudo systemctl start ${SERVICE}
     Watch logs:                   journalctl -u ${SERVICE} -f
     Stop:                         sudo systemctl stop ${SERVICE}

The service auto-starts on boot and auto-restarts if the bot crashes.
======================================================================
MSG
