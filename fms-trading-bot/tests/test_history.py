"""Fetching long histories from the terminal.

A 120-day M1 edge test returned "no data" on all six symbols with
(-2, 'Terminal: Invalid param'). Nothing was wrong with the account: one
request for 172,800 bars is refused outright, and the refusal is
indistinguishable from a symbol that has no history at all. The request
has to be split.
"""

from fmsbot.broker.mt5 import MT5Broker, _CHUNK
from fmsbot.broker.base import BrokerError


class FakeMT5:
    """A terminal holding `available` M1 bars that refuses big requests."""

    def __init__(self, available: int, limit: int = _CHUNK, drift: int = 0):
        self.available, self.limit, self.drift = available, limit, drift
        self.requests: list[tuple[int, int]] = []

    # -- the parts MT5Broker.bars touches ------------------------------
    def symbol_select(self, symbol, enable):
        return True

    def symbol_info(self, symbol):
        return object()

    def symbols_get(self, pattern=None):
        return []

    def last_error(self):
        return (-2, "Terminal: Invalid params")

    def copy_rates_from_pos(self, symbol, tf, start_pos, count):
        self.requests.append((start_pos, count))
        if count > self.limit:
            return None                    # exactly what the terminal does
        # Bar 0 is the newest; start_pos counts backwards from it.
        start_pos += self.drift            # a bar closed since the last call
        newest = self.available - 1 - start_pos
        oldest = max(newest - count + 1, 0)
        if newest < 0:
            return []
        return [{"time": i * 60, "open": 1.0, "high": 1.1, "low": 0.9,
                 "close": 1.0} for i in range(oldest, newest + 1)]


def _broker(fake):
    b = MT5Broker(login=1, password="x", server="s")
    b.mt5 = fake
    return b


def _bars_without_waiting(fake, *args):
    """bars(), with the history-download backoff skipped.

    The retry waits 2+5+8 seconds for a symbol whose history is still
    downloading. Paying that in a suite meant to run before every push
    trains people not to run it.
    """
    from fmsbot.broker import mt5 as mod
    real = mod.time.sleep
    mod.time.sleep = lambda _s: None
    try:
        return _broker(fake).bars(*args)
    finally:
        mod.time.sleep = real


def test_a_request_larger_than_one_chunk_is_split():
    fake = FakeMT5(available=172_800)
    bars = _broker(fake).bars("EURUSDm", "M1", 172_800)
    assert len(bars) == 172_800, len(bars)
    assert all(c <= _CHUNK for _, c in fake.requests), fake.requests


def test_the_bars_come_back_oldest_first_and_in_one_sequence():
    bars = _broker(FakeMT5(available=120_000)).bars("EURUSDm", "M1", 120_000)
    times = [b.time for b in bars]
    assert times == sorted(times)
    assert len(set(times)) == len(times), "a bar was served twice"
    assert times[1] - times[0] == 60


def test_a_short_history_is_returned_whole_not_refused():
    """Sixty days of M1 has no weekend bars: asking for 86,400 gets fewer."""
    bars = _broker(FakeMT5(available=43_200)).bars("EURUSDm", "M1", 86_400)
    assert len(bars) == 43_200


def test_a_bar_closing_mid_fetch_does_not_duplicate_or_skip_one():
    """Positions shift by one when a new bar prints between requests."""
    bars = _broker(FakeMT5(available=150_000, drift=1)).bars(
        "EURUSDm", "M1", 150_000)
    times = [b.time for b in bars]
    assert len(set(times)) == len(times), "a bar was served twice"
    assert times == sorted(times)


def test_no_history_at_all_is_still_an_error():
    try:
        _bars_without_waiting(FakeMT5(available=0), "EURUSDm", "M1", 1000)
    except BrokerError as exc:
        assert "No bars" in str(exc)
    else:
        raise AssertionError("an empty history must not pass silently")


def test_a_terminal_that_refuses_even_one_chunk_says_so():
    """The old failure mode, now only possible when nothing works."""
    try:
        _bars_without_waiting(FakeMT5(available=172_800, limit=10),
                              "EURUSDm", "M1", 172_800)
    except BrokerError as exc:
        assert "Invalid params" in str(exc)
    else:
        raise AssertionError("a refused request must not pass silently")
