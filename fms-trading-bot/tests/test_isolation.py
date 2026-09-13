"""The suite must not read the operator's live configuration.

Six tests failed on the trading machine and passed everywhere else. The
cause was not any of the six: `Settings.load()` reads `.env` from the
working directory, and a tuned account's FIXED_LOT, MIN_EFFICIENCY and
STRATEGY seeped in through os.environ.setdefault. A suite that changes
its answers when the account is re-tuned cannot be trusted to catch the
next bug, and the bugs it exists to catch have each already cost money.
"""

import os
import tempfile
from pathlib import Path

from tests.helpers import settings

HOSTILE = """\
STRATEGY=liquidity_sweep
TIMEFRAME=M1
FIXED_LOT=0.07
EMA_FAST=5
EMA_SLOW=13
RR_TARGET=9.0
MIN_EFFICIENCY=0.90
CONFLUENCE_MIN=3
RISK_PCT=4.0
MAX_OPEN_POSITIONS=99
"""


def _with_dotenv(body: str):
    """Load settings from a directory containing this .env file."""
    here = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, ".env").write_text(body, encoding="utf-8")
        os.chdir(tmp)
        try:
            return settings()
        finally:
            os.chdir(here)


def test_a_live_dotenv_cannot_change_what_the_tests_prove():
    clean, polluted = settings(), _with_dotenv(HOSTILE)
    for field in ("strategy", "timeframe", "fixed_lot", "ema_fast",
                  "ema_slow", "rr_target", "min_efficiency",
                  "confluence_min", "risk_pct", "max_open_positions"):
        assert getattr(clean, field) == getattr(polluted, field), field


def test_the_overrides_a_test_asks_for_still_apply():
    """Ignoring the file must not mean ignoring the test's own settings."""
    s = settings(FIXED_LOT=0.05, RR_TARGET=4.0, STRATEGY="pin_bar")
    assert s.fixed_lot == 0.05
    assert s.rr_target == 4.0
    assert s.strategy == "pin_bar"


def test_a_bom_prefixed_dotenv_is_still_read_by_the_bot():
    """Skipping the file in tests must not break reading it for real.

    Windows PowerShell writes UTF-8 with a byte-order mark, which once
    blanked TG_BOT_TOKEN by making the mark part of the variable name.
    """
    from fmsbot.config import Settings
    here = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, ".env").write_text("﻿TG_PASSWORD=frombom\n",
                                     encoding="utf-8")
        os.chdir(tmp)
        try:
            os.environ.pop("TG_PASSWORD", None)
            assert Settings.load().tg_password == "frombom"
        finally:
            os.environ.pop("TG_PASSWORD", None)
            os.chdir(here)
