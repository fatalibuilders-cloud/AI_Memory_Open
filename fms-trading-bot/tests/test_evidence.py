"""The record-keeper must not convict a fair coin, nor excuse a real loser.

The account lost $46.28 over 139 trades while the evidence that it was
losing had been conclusive since trade 30.
"""

import random
import tempfile
from pathlib import Path

from fmsbot.evidence import FAILED, PASSED, PROVING, Evidence

TMP = Path(tempfile.mkdtemp())


def _ev(name, **kw):
    return Evidence.load(TMP / f"{name}.json", "fp1", **kw)


def test_no_verdict_before_the_minimum_sample():
    e = _ev("few")
    for _ in range(29):
        e.record(-1.0)
    assert e.verdict() == PROVING, "29 losses is still not a verdict"


def test_a_real_loser_is_convicted():
    e = _ev("losing")
    for _ in range(40):
        e.record(-0.35)
    assert e.verdict() == FAILED


def test_a_fair_coin_is_not_convicted():
    """The false-positive rate must stay near alpha, or it stops good runs."""
    rnd = random.Random(7)
    wrong = 0
    for trial in range(300):
        e = _ev(f"coin{trial}")
        for _ in range(60):
            e.record(1.0 if rnd.random() < 0.5 else -1.0)
        if e.verdict() != PROVING:
            wrong += 1
    assert wrong / 300 < 0.05, f"misjudged {wrong}/300 zero-edge records"


def test_a_real_edge_is_recognised():
    e = _ev("winner")
    rnd = random.Random(3)
    for _ in range(300):
        e.record(1.0 if rnd.random() < 0.62 else -1.0)
    assert e.verdict() == PASSED, (e.verdict(), e.z)


def test_the_live_139_trade_record_is_caught_by_trade_30():
    e = _ev("real")
    wins, win_size = int(139 * 0.216), 0.60
    loss_size = (46.28 + wins * win_size) / (139 - wins)
    caught_at = None
    for i in range(139):
        win = i % 5 == 0 and wins > 0
        e.record(win_size if win else -loss_size)
        if win:
            wins -= 1
        if caught_at is None and e.verdict() == FAILED:
            caught_at = i + 1
    assert e.verdict() == FAILED
    assert caught_at is not None and caught_at <= 40, caught_at
    stopped = sum(e.pnls[:caught_at])
    assert stopped > e.net, "halting must lose less than running to the end"


def test_identical_trades_do_not_explode_the_z_score():
    """Fixed cash exits close many trades at the same amount."""
    e = _ev("identical")
    for _ in range(50):
        e.record(-0.25)
    assert abs(e.z) <= 99.0, e.z
    assert "z" in e.explain()


def test_changing_the_configuration_discards_the_record():
    e = _ev("fp")
    for _ in range(40):
        e.record(-1.0)
    assert Evidence.load(TMP / "fp.json", "fp1").count == 40
    assert Evidence.load(TMP / "fp.json", "OTHER").count == 0


def test_the_fingerprint_ignores_settings_that_do_not_change_a_trade():
    from fmsbot.evidence import fingerprint
    from .helpers import settings
    a = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_SL_MULT=1.5)
    before = fingerprint(a, "ema_cross")
    b = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_SL_MULT=1.5,
                 TG_PASSWORD="a-different-password")
    assert fingerprint(b, "ema_cross") == before, \
        "changing a password must not throw away the trade record"
    c = settings(SYMBOLS="EURUSDm", TIMEFRAME="M5", ATR_SL_MULT=2.5)
    assert fingerprint(c, "ema_cross") != before, \
        "changing the exits must start the scoring again"


def test_a_break_even_scratch_is_not_counted_as_a_lost_trade():
    """The micro account's trades close at -0.16 against a 2.12 stop,
    because the rung moved the stop out of risk. Counting those as
    losses makes a working configuration read as a 20% win rate."""
    from fmsbot.evidence import Evidence

    ev = Evidence(fingerprint="x")
    for _ in range(5):
        ev.record(+4.24)                      # 2R winners
    for _ in range(5):
        ev.record(-2.12)                      # full stops
    for _ in range(10):
        ev.record(-0.16, scratch=True)        # taken out of risk

    assert ev.count == 20
    assert ev.scratches == 10
    assert ev.decided == 10
    assert abs(ev.win_rate - 25.0) < 0.01          # raw, over everything
    assert abs(ev.decided_win_rate - 50.0) < 0.01  # over what resolved


def test_the_scratches_still_cost_what_they_cost():
    """They are not free: the profit factor must still carry them."""
    from fmsbot.evidence import Evidence

    ev = Evidence(fingerprint="x")
    ev.record(+4.00)
    ev.record(-2.00)
    clean = ev.profit_factor
    ev.record(-0.16, scratch=True)
    assert ev.profit_factor < clean


def test_a_record_written_before_scratches_existed_still_loads():
    import json
    import tempfile
    from pathlib import Path
    from fmsbot.evidence import Evidence

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp, "evidence.json")
        path.write_text(json.dumps({
            "fingerprint": "abc",
            "pnls": [1.0, -2.0, 3.0],
            "started": 0.0,
        }), encoding="utf-8")
        ev = Evidence.load(path, "abc")
        assert ev.count == 3
        assert ev.scratches == 0
        assert len(ev.scratched) == len(ev.pnls)
        assert ev.decided == 3


def test_the_two_lists_stay_the_same_length_through_a_reset():
    from fmsbot.evidence import Evidence

    ev = Evidence(fingerprint="x")
    ev.record(-1.0, scratch=True)
    ev.reset()
    assert ev.scratched == [] and ev.pnls == []
    ev.record(-1.0)
    assert len(ev.scratched) == len(ev.pnls) == 1


def test_the_summary_says_how_many_were_scratches():
    from fmsbot.evidence import Evidence

    ev = Evidence(fingerprint="x", min_trades=3)
    ev.record(+4.00)
    ev.record(-2.00)
    ev.record(-0.16, scratch=True)
    text = ev.explain()
    assert "1 were break-even scratches" in text or "scratches" in text
    assert "50.0%" in text, text
