"""Tests for durable state and the trade journal."""

import json
from datetime import datetime, timedelta, timezone

import pytest

from deriv_bot.state import DailyState, StateStore, utc_day


@pytest.fixture
def paths(tmp_path):
    return str(tmp_path / "state.json"), str(tmp_path / "trades.jsonl")


class TestDailyRollover:
    def test_same_day_does_not_reset(self):
        daily = DailyState(realized_pnl=-5.0, trades_opened=3)
        assert not daily.roll_over_if_needed()
        assert daily.realized_pnl == -5.0

    def test_new_day_resets_counters_and_halt(self):
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        daily = DailyState(
            day=utc_day(yesterday),
            realized_pnl=-50.0,
            trades_opened=9,
            halted=True,
            halt_reason="loss limit",
        )
        assert daily.roll_over_if_needed()
        assert daily.realized_pnl == 0.0
        assert daily.trades_opened == 0
        assert not daily.halted
        assert daily.halt_reason == ""
        assert daily.day == utc_day()


class TestPersistence:
    def test_missing_file_starts_fresh(self, paths):
        store = StateStore(*paths)
        assert store.daily.realized_pnl == 0.0
        assert store.daily.day == utc_day()

    def test_round_trip(self, paths):
        store = StateStore(*paths)
        store.daily.realized_pnl = -3.25
        store.daily.trades_opened = 4
        store.save()
        assert StateStore(*paths).daily.realized_pnl == -3.25

    def test_corrupt_file_starts_fresh_instead_of_crashing(self, paths):
        state_path, journal_path = paths
        with open(state_path, "w", encoding="utf-8") as handle:
            handle.write("{not json")
        assert StateStore(state_path, journal_path).daily.realized_pnl == 0.0

    def test_unknown_fields_are_ignored(self, paths):
        state_path, journal_path = paths
        with open(state_path, "w", encoding="utf-8") as handle:
            json.dump({"day": utc_day(), "realized_pnl": -1.0, "from_the_future": True}, handle)
        assert StateStore(state_path, journal_path).daily.realized_pnl == -1.0

    def test_creates_nested_directories(self, tmp_path):
        store = StateStore(str(tmp_path / "a" / "b" / "state.json"), str(tmp_path / "a" / "t.jsonl"))
        store.save()
        assert (tmp_path / "a" / "b" / "state.json").exists()


class TestAccounting:
    def test_open_increments_the_daily_count(self, paths):
        store = StateStore(*paths)
        store.record_open({"contract_id": 1, "symbol": "cryBTCUSD"})
        assert store.daily.trades_opened == 1

    def test_win_and_loss_are_tallied(self, paths):
        store = StateStore(*paths)
        store.record_settlement(1.85, {"contract_id": 1})
        store.record_settlement(-1.0, {"contract_id": 2})
        assert store.daily.wins == 1
        assert store.daily.losses == 1
        assert store.daily.trades_settled == 2
        assert abs(store.daily.realized_pnl - 0.85) < 1e-9

    def test_journal_is_one_json_object_per_line(self, paths):
        state_path, journal_path = paths
        store = StateStore(state_path, journal_path)
        store.record_open({"contract_id": 1, "symbol": "cryBTCUSD"})
        store.record_settlement(-1.0, {"contract_id": 1, "symbol": "cryBTCUSD"})

        with open(journal_path, encoding="utf-8") as handle:
            events = [json.loads(line) for line in handle if line.strip()]
        assert [e["event"] for e in events] == ["open", "settled"]
        assert all("ts" in e for e in events)

    def test_halt_is_recorded_once(self, paths):
        state_path, journal_path = paths
        store = StateStore(state_path, journal_path)
        store.halt("loss limit")
        store.halt("something else")
        assert store.daily.halt_reason == "loss limit"

        with open(journal_path, encoding="utf-8") as handle:
            halts = [json.loads(line) for line in handle if '"halt"' in line]
        assert len(halts) == 1
