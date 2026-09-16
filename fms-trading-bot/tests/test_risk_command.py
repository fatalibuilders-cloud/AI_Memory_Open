"""Changing the risk per trade, and having it stay changed.

RISK_PCT=0.0011% meant one trade could lose about a dollar on a $93k
account, and the broker's smallest lot could not obey it: nearly every
signal was refused for a day. /risk existed to fix that from the phone
and only changed the number in memory — so the next restart silently
restored the cap, and the account went back to refusing everything.
"""

import os
import tempfile
from pathlib import Path

from fmsbot import envfile
from tests.helpers import FakeBroker, make_bot, settings

EXISTING = """\
# credentials
TG_BOT_TOKEN=abc
MT5_LOGIN=12345

# risk
RISK_PCT=0.0011          # about a dollar
MAX_OPEN_POSITIONS=6
"""


def _in_temp_env(body, fn):
    here = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, ".env").write_text(body, encoding="utf-8")
        os.chdir(tmp)
        try:
            return fn(Path(tmp, ".env"))
        finally:
            os.chdir(here)


def test_the_new_value_reaches_the_file():
    def check(path):
        changes = envfile.save({"RISK_PCT": "0.5"})
        assert changes == ["RISK_PCT: 0.0011 -> 0.5"], changes
        return path.read_text(encoding="utf-8")
    out = _in_temp_env(EXISTING, check)
    assert "RISK_PCT=0.5" in out
    assert "0.0011" not in out


def test_comments_and_order_survive_the_edit():
    """People hand-edit this file; it must still look like theirs."""
    out = _in_temp_env(EXISTING, lambda p: (envfile.save({"RISK_PCT": "0.5"}),
                                            p.read_text(encoding="utf-8"))[1])
    assert "# credentials" in out and "# risk" in out
    assert out.index("TG_BOT_TOKEN") < out.index("RISK_PCT")
    assert "MAX_OPEN_POSITIONS=6" in out


def test_a_setting_that_was_never_there_is_appended():
    out = _in_temp_env(EXISTING, lambda p: (envfile.save({"SL_MONEY": "1.02"}),
                                            p.read_text(encoding="utf-8"))[1])
    assert "SL_MONEY=1.02" in out


def test_writing_the_same_value_changes_nothing():
    assert _in_temp_env(EXISTING, lambda p: envfile.save({"RISK_PCT": "0.0011"})) == []


def test_a_backup_is_kept_because_this_file_holds_the_credentials():
    def check(path):
        envfile.save({"RISK_PCT": "0.5"})
        return Path(str(path) + ".bak").read_text(encoding="utf-8")
    assert "RISK_PCT=0.0011" in _in_temp_env(EXISTING, check)


def test_a_byte_order_mark_does_not_become_part_of_a_name():
    """PowerShell's UTF8 and Notepad both write one, and it once made
    the first variable unreadable, blanking the bot's Telegram token."""
    def check(path):
        envfile.save({"RISK_PCT": "0.5"})
        raw = path.read_bytes()
        assert not raw.startswith(b"\xef\xbb\xbf"), "wrote a BOM"
        return path.read_text(encoding="utf-8")
    out = _in_temp_env("﻿TG_BOT_TOKEN=abc\nRISK_PCT=0.0011\n", check)
    assert "TG_BOT_TOKEN=abc" in out and "RISK_PCT=0.5" in out


# -- the command ------------------------------------------------------

def _bot(**over):
    env = {"SYMBOLS": "EURUSDm", "FIXED_LOT": 0}
    env.update(over)
    s = settings(**env)
    bot, session, _ = make_bot(s, FakeBroker(balance=92929.45), ["EURUSDm"])
    session.connected = True
    bot.sessions = [session]
    return bot


def test_the_command_says_what_the_new_risk_is_in_money():
    out = _in_temp_env(EXISTING, lambda p: _bot()._dispatch("risk", ["0.5"]))
    assert "0.5%" in out
    assert "464" in out, out          # 0.5% of 92929.45
    assert "saved to .env" in out


def test_a_file_it_cannot_write_is_reported_not_swallowed():
    """Silently keeping the change in memory only is the bug being fixed."""
    here = os.getcwd()
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)                      # no .env here at all
        try:
            out = _bot()._dispatch("risk", ["0.5"])
        finally:
            os.chdir(here)
    assert "NOT saved" in out and "revert on restart" in out


def test_an_absolute_cap_is_mentioned_because_it_still_binds():
    out = _in_temp_env(EXISTING, lambda p: _bot(
        MAX_LOSS_PER_TRADE=1.0)._dispatch("risk", ["0.5"]))
    assert "MAX_LOSS_PER_TRADE" in out


def test_a_fixed_lot_makes_the_risk_setting_inert_and_says_so():
    out = _in_temp_env(EXISTING, lambda p: _bot(
        FIXED_LOT=0.02)._dispatch("risk", ["0.5"]))
    assert "FIXED_LOT" in out and "0.02" in out


def test_the_bounds_are_still_enforced():
    bot = _bot()
    assert "between 0 and 5" in bot._dispatch("risk", ["9"])
    assert "between 0 and 5" in bot._dispatch("risk", ["0"])
    assert bot.s.risk_pct != 9
