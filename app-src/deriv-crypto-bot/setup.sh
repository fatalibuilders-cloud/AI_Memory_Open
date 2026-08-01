#!/usr/bin/env bash
# One-command setup: virtualenv, dependencies, and a .env to fill in.
# Safe to re-run — it never overwrites an existing .env.
#
#   ./setup.sh
#
set -euo pipefail

cd "$(dirname "$0")"

echo
echo "=============================================================="
echo "  DERIV CRYPTO BOT — SETUP"
echo "=============================================================="
echo

# -- Python ---------------------------------------------------------------

if ! command -v python3 >/dev/null 2>&1; then
    echo "  ERROR: python3 is not installed."
    echo "  Install Python 3.10 or newer, then run this again."
    exit 1
fi

version=$(python3 -c 'import sys; print("%d.%d" % sys.version_info[:2])')
if ! python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    echo "  ERROR: Python 3.10 or newer is required (found $version)."
    exit 1
fi
echo "  [ok] Python $version"

# -- Virtual environment --------------------------------------------------

if [ ! -d .venv ]; then
    python3 -m venv .venv
    echo "  [ok] Created virtual environment (.venv)"
else
    echo "  [ok] Virtual environment already exists"
fi

# shellcheck disable=SC1091
source .venv/bin/activate

python -m pip install --quiet --upgrade pip
python -m pip install --quiet -r requirements.txt
echo "  [ok] Installed dependencies"

python -m pip install --quiet pytest
echo "  [ok] Installed pytest"

# -- Configuration --------------------------------------------------------

if [ ! -f .env ]; then
    cp .env.example .env
    echo "  [ok] Created .env from the template"
    created_env=1
else
    echo "  [ok] .env already exists — left untouched"
    created_env=0
fi

# -- Self-test ------------------------------------------------------------

echo
echo "  Running the test suite..."
# pyproject already sets -q; grep the summary rather than adding another -q,
# which would suppress the very line we want.
if summary=$(python -m pytest 2>&1 | grep -E '[0-9]+ (passed|failed)' | tail -1); then
    echo "  [ok] ${summary:-tests passed}"
else
    echo "  [!!] Tests failed. Run 'python -m pytest' to see why."
    exit 1
fi

# -- What next ------------------------------------------------------------

echo
echo "=============================================================="
echo "  NEXT STEPS"
echo "=============================================================="
echo
if [ "$created_env" -eq 1 ]; then
    echo "  1. Get a Deriv API token:"
    echo "       - Log in at deriv.com and switch to your VIRTUAL (demo) account"
    echo "       - Settings > API token"
    echo "       - Tick 'Read' and 'Trade' only. Not Payments. Not Admin."
    echo
    echo "  2. Put it in .env:"
    echo "       DERIV_API_TOKEN=your_token_here"
    echo
    echo "  3. Verify it works (this places no trades):"
else
    echo "  1. Verify your setup (this places no trades):"
fi
echo "       source .venv/bin/activate"
echo "       python -m deriv_bot.check"
echo
echo "  The check tells you whether everything is wired up, and prints"
echo "  the real payout ratio to use when backtesting."
echo
echo "  If you open a new terminal later, either cd back here first:"
echo "       cd '$(pwd)'"
echo "  or use the full path, which works from anywhere:"
echo "       '$(pwd)/.venv/bin/python' -m deriv_bot.check"
echo
echo "  Real-money trading is OFF by default and stays off until you"
echo "  set DERIV_ALLOW_REAL_MONEY=true yourself."
echo
