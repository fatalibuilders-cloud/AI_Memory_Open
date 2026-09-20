"""The one command the operator actually types.

Every command in this project has to be run from the project folder with
the venv's python, and a session spent typing them from C:\\Users\\<name>
produced nothing but "not a git repository" and "is not recognized as the
name of a cmdlet". update.ps1 sets its own working directory, so a full
path works from anywhere — which makes it the only thing worth typing.
"""

import re
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent.parent / "update.ps1"
TEXT = SCRIPT.read_text(encoding="utf-8")


def test_it_sets_its_own_working_directory():
    """Without this the full-path invocation runs git in the wrong folder."""
    assert "Set-Location $PSScriptRoot" in TEXT


def test_the_steps_are_numbered_consistently():
    """A renumbered step that says [3/4] in a five-step script is how a
    person loses track of whether the thing finished."""
    steps = re.findall(r"\[(\d+)/(\d+)\]", TEXT)
    assert steps, "no steps found"
    total = {t for _, t in steps}
    assert len(total) == 1, f"mixed totals: {total}"
    seen = sorted({int(n) for n, _ in steps})
    assert seen == list(range(1, int(total.pop()) + 1)), seen


def test_the_documented_flags_exist():
    """The header is the only documentation anyone reads."""
    for flag in ("-Preset", "-Rate"):
        assert flag in TEXT.split("param(")[0], f"{flag} undocumented"
        assert flag.lstrip("-") in TEXT.split("param(")[1][:400], f"{flag} unbound"


def test_settings_are_applied_before_the_check_and_the_start():
    """A preset that fails must not reach the restart, and the config
    check must see what the preset wrote."""
    # The INVOCATIONS, not the mentions: the comment above them names
    # rate.py first, which would make an index search agree for the
    # wrong reason.
    preset_at = TEXT.index("$python preset.py")
    rate_at = TEXT.index("$python rate.py")
    check_at = TEXT.index("$python check_config.py")
    start_at = TEXT.index("Start-ScheduledTask")
    assert preset_at < rate_at < check_at < start_at


def test_a_rate_nothing_can_carry_stops_before_the_restart():
    """rate.py exits non-zero when no symbol survives; restarting into
    that configuration would trade the symbols it just refused."""
    after_rate = TEXT[TEXT.index("$python rate.py"):
                      TEXT.index("$python check_config.py")]
    assert "$LASTEXITCODE -ne 0" in after_rate
    assert "exit 1" in after_rate


def test_the_bot_is_stopped_before_anything_reads_the_terminal():
    """Two processes sharing one MT5 terminal interfere, and rate.py
    reads bars from it."""
    assert TEXT.index("Stop-ScheduledTask") < TEXT.index("$python rate.py")
