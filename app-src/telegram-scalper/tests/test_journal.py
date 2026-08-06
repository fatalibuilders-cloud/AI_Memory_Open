"""Journal behaviour: audit trail, dedupe memory and follow-up bookkeeping."""

from __future__ import annotations

import pytest

from tgscalper.journal import Journal
from tgscalper.models import (
    Action,
    MessageRef,
    OrderRequest,
    OrderResult,
    OrderType,
    Side,
    Signal,
)


@pytest.fixture
def journal(tmp_path):
    instance = Journal(tmp_path / "journal.sqlite")
    yield instance
    instance.close()


def a_signal(entry: float = 2350.0) -> Signal:
    return Signal(
        action=Action.OPEN,
        symbol="XAUUSD",
        side=Side.BUY,
        entry=entry,
        stop_loss=2344.0,
        take_profits=[2360.0],
        raw_text="GOLD BUY 2350 SL 2344 TP 2360",
        source=MessageRef(chat_id=-100123, message_id=7, sender_id=42, chat_title="VIP"),
    )


def an_order(symbol: str = "XAUUSD") -> OrderRequest:
    return OrderRequest(
        symbol=symbol,
        side=Side.BUY,
        order_type=OrderType.MARKET,
        volume=0.16,
        stop_loss=2344.0,
        take_profit=2360.0,
    )


class TestRecording:
    def test_signal_and_order_are_stored(self, journal):
        signal_id = journal.record_signal(a_signal(), accepted=True)
        assert signal_id > 0
        journal.record_order(
            signal_id,
            a_signal().source,
            an_order(),
            OrderResult(ok=True, ticket=555, filled_price=2350.1, volume=0.16),
            live=False,
        )
        summary = journal.summary(days=1)
        assert summary["signals_accepted"] == 1
        assert summary["orders_filled"] == 1
        assert summary["live_orders"] == 0

    def test_skips_are_recorded_with_a_reason(self, journal):
        journal.record_skip(
            MessageRef(chat_id=-100123, message_id=8), "no trade direction found", "gm all"
        )
        summary = journal.summary(days=1)
        assert summary["signals_skipped"] == 1
        assert ("no trade direction found", 1) in summary["top_skip_reasons"]

    def test_live_orders_are_flagged(self, journal):
        signal_id = journal.record_signal(a_signal(), accepted=True)
        journal.record_order(
            signal_id,
            a_signal().source,
            an_order(),
            OrderResult(ok=True, ticket=1, volume=0.1),
            live=True,
        )
        assert journal.summary(days=1)["live_orders"] == 1

    def test_failed_orders_keep_their_error(self, journal):
        signal_id = journal.record_signal(a_signal(), accepted=True)
        journal.record_order(
            signal_id,
            a_signal().source,
            an_order(),
            OrderResult(ok=False, error="market closed"),
            live=False,
        )
        summary = journal.summary(days=1)
        assert summary["orders_attempted"] == 1
        assert summary["orders_filled"] == 0


class TestDedupe:
    def test_the_same_fingerprint_is_remembered(self, journal):
        signal = a_signal()
        journal.record_signal(signal, accepted=True)
        assert journal.seen_fingerprint(signal.fingerprint(), window_minutes=30)

    def test_a_different_setup_is_not_a_duplicate(self, journal):
        journal.record_signal(a_signal(2350.0), accepted=True)
        assert not journal.seen_fingerprint(a_signal(2355.0).fingerprint(), window_minutes=30)

    def test_rejected_signals_do_not_count_as_duplicates(self, journal):
        # A signal we refused must not block the corrected repost that follows.
        signal = a_signal()
        journal.record_signal(signal, accepted=False, reason="spread too wide")
        assert not journal.seen_fingerprint(signal.fingerprint(), window_minutes=30)

    def test_a_zero_window_disables_dedupe(self, journal):
        signal = a_signal()
        journal.record_signal(signal, accepted=True)
        assert not journal.seen_fingerprint(signal.fingerprint(), window_minutes=0)


class TestTicketMapping:
    def test_tickets_are_found_by_message(self, journal):
        signal = a_signal()
        signal_id = journal.record_signal(signal, accepted=True)
        for ticket in (101, 102):
            journal.record_order(
                signal_id,
                signal.source,
                an_order(),
                OrderResult(ok=True, ticket=ticket, volume=0.05),
                live=False,
            )
        assert journal.tickets_for_message(-100123, 7) == [101, 102]

    def test_closed_tickets_drop_out(self, journal):
        signal = a_signal()
        signal_id = journal.record_signal(signal, accepted=True)
        journal.record_order(
            signal_id,
            signal.source,
            an_order(),
            OrderResult(ok=True, ticket=101, volume=0.1),
            live=False,
        )
        journal.record_close(101, close_price=2360.0, profit=96.0)
        assert journal.tickets_for_message(-100123, 7) == []

    def test_failed_orders_are_not_returned_as_tickets(self, journal):
        signal = a_signal()
        signal_id = journal.record_signal(signal, accepted=True)
        journal.record_order(
            signal_id,
            signal.source,
            an_order(),
            OrderResult(ok=False, error="rejected"),
            live=False,
        )
        assert journal.tickets_for_message(-100123, 7) == []

    def test_open_tickets_filtered_by_chat_and_symbol(self, journal):
        signal = a_signal()
        signal_id = journal.record_signal(signal, accepted=True)
        journal.record_order(
            signal_id,
            signal.source,
            an_order("XAUUSD"),
            OrderResult(ok=True, ticket=201, volume=0.1),
            live=False,
        )
        journal.record_order(
            signal_id,
            signal.source,
            an_order("EURUSD"),
            OrderResult(ok=True, ticket=202, volume=0.1),
            live=False,
        )
        assert journal.open_tickets(chat_id=-100123, symbol="XAUUSD") == [201]
        assert sorted(journal.open_tickets(chat_id=-100123)) == [201, 202]
        assert journal.open_tickets(chat_id=-999) == []


class TestDailyMark:
    def test_the_first_call_stores_the_opening_balance(self, journal):
        assert journal.day_start_balance(10_000.0) == 10_000.0

    def test_later_calls_keep_the_original_mark(self, journal):
        journal.day_start_balance(10_000.0)
        # Equity has since dropped; the day's starting point must not move,
        # or the daily-loss halt would reset itself after every restart.
        assert journal.day_start_balance(9_500.0) == 10_000.0


class TestCounters:
    def test_accepted_signals_are_counted(self, journal):
        for index in range(3):
            signal = a_signal(2350.0 + index)
            journal.record_signal(signal, accepted=True)
        assert journal.accepted_since(60) == 3

    def test_skipped_signals_are_not_counted(self, journal):
        journal.record_signal(a_signal(), accepted=False, reason="blocked")
        assert journal.accepted_since(60) == 0


class TestPersistence:
    def test_data_survives_a_reopen(self, tmp_path):
        path = tmp_path / "journal.sqlite"
        first = Journal(path)
        signal = a_signal()
        first.record_signal(signal, accepted=True)
        first.close()

        second = Journal(path)
        # Dedupe memory must survive a restart mid-session.
        assert second.seen_fingerprint(signal.fingerprint(), window_minutes=30)
        assert second.summary(days=1)["signals_accepted"] == 1
        second.close()

    def test_recent_returns_newest_first(self, journal):
        journal.record_signal(a_signal(2350.0), accepted=True)
        journal.record_skip(MessageRef(chat_id=-100123, message_id=9), "chit chat", "hello")
        rows = journal.recent(5)
        assert rows[0]["action"] == "SKIP"


class TestThreadSafety:
    """The engine runs on worker threads, so the journal is hit concurrently.

    Before the lock this produced "cannot commit - no transaction is active"
    and "bad parameter or other API misuse" under real load, losing records.
    """

    def test_concurrent_writes_all_land(self, journal):
        import threading

        errors: list[Exception] = []

        def writer(index: int) -> None:
            try:
                for step in range(20):
                    journal.record_signal(a_signal(2350.0 + index * 100 + step), accepted=True)
                    journal.record_skip(
                        MessageRef(chat_id=-1, message_id=index), "noise", "chatter"
                    )
            except Exception as exc:  # pragma: no cover - only on regression
                errors.append(exc)

        threads = [threading.Thread(target=writer, args=(i,)) for i in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join()

        assert not errors, f"concurrent writes raised: {errors[:3]}"
        summary = journal.summary(days=1)
        assert summary["signals_accepted"] == 8 * 20
        assert summary["signals_skipped"] == 8 * 20

    def test_reads_and_writes_interleave_safely(self, journal):
        import threading

        errors: list[Exception] = []
        stop = threading.Event()

        def reader() -> None:
            try:
                while not stop.is_set():
                    journal.summary(days=1)
                    journal.recent(5)
                    journal.accepted_since(60)
            except Exception as exc:  # pragma: no cover - only on regression
                errors.append(exc)

        readers = [threading.Thread(target=reader) for _ in range(3)]
        for thread in readers:
            thread.start()
        try:
            for index in range(60):
                journal.record_signal(a_signal(2350.0 + index), accepted=True)
                journal.day_start_balance(10_000.0)
        finally:
            stop.set()
            for thread in readers:
                thread.join()

        assert not errors, f"interleaved access raised: {errors[:3]}"
