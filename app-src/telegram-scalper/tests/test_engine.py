"""End-to-end tests: raw Telegram text in, paper orders out."""

from __future__ import annotations

import pytest

from tgscalper import config as config_module
from tgscalper.brokers.paper import PaperBroker
from tgscalper.engine import Engine
from tgscalper.journal import Journal
from tgscalper.models import MessageRef, OrderType, Side
from tgscalper.symbols import SymbolResolver

CHAT_ID = -1001234567890


@pytest.fixture
def setup(tmp_path):
    config = config_module.load("does-not-exist.yaml", env={})
    config.risk.hours.days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
    broker = PaperBroker(starting_balance=10_000.0)
    journal = Journal(tmp_path / "journal.sqlite")
    engine = Engine(config, broker, journal, SymbolResolver(aliases=config.aliases))
    engine.start()
    yield engine, broker, journal, config
    engine.stop()
    journal.close()


def post(engine, text: str, message_id: int = 1, reply_to: int | None = None):
    return engine.handle(
        text,
        MessageRef(
            chat_id=CHAT_ID,
            message_id=message_id,
            sender_id=999,
            chat_title="Test Group",
            reply_to_message_id=reply_to,
        ),
    )


class TestOpening:
    def test_a_signal_becomes_a_position(self, setup):
        engine, broker, _, _ = setup
        decision = post(engine, "GOLD BUY 2350\nSL 2344\nTP1 2360\nTP2 2370")
        assert decision.accepted
        assert decision.placed == 1
        positions = broker.positions()
        assert len(positions) == 1
        assert positions[0].symbol == "XAUUSD"
        assert positions[0].side is Side.BUY
        assert positions[0].stop_loss == 2344
        assert positions[0].take_profit == 2360  # tp_mode defaults to "first"

    def test_split_mode_opens_one_position_per_target(self, setup):
        engine, broker, _, config = setup
        config.execution.tp_mode = "split"
        config.risk.max_open_per_symbol = 5
        decision = post(engine, "GOLD BUY 2350\nSL 2344\nTP1 2360\nTP2 2370\nTP3 2380")
        assert decision.placed == 3
        assert sorted(p.take_profit for p in broker.positions()) == [2360, 2370, 2380]

    def test_size_follows_the_risk_percentage(self, setup):
        engine, broker, _, _ = setup
        post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360")
        # $100 budget / ($6 * $100 per lot) rounded down to the 0.01 step.
        assert broker.positions()[0].volume == pytest.approx(0.16)

    def test_group_multiplier_is_applied(self, setup):
        engine, broker, _, _ = setup
        from tgscalper.config import GroupConfig

        group = GroupConfig(id=CHAT_ID, title="Half size", risk_multiplier=0.5)
        engine.handle(
            "GOLD BUY 2350\nSL 2344\nTP 2360",
            MessageRef(chat_id=CHAT_ID, message_id=1, chat_title="Half size"),
            group,
        )
        assert broker.positions()[0].volume == pytest.approx(0.08)

    def test_chit_chat_places_nothing(self, setup):
        engine, broker, _, _ = setup
        decision = post(engine, "good luck everyone today 🙏")
        assert not decision.accepted
        assert broker.positions() == []

    def test_duplicate_repost_is_ignored(self, setup):
        engine, broker, _, _ = setup
        assert post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=1).accepted
        second = post(engine, "gold buy now 2350 sl 2344 tp 2360", message_id=2)
        assert not second.accepted
        assert "duplicate" in second.reason
        assert len(broker.positions()) == 1

    def test_max_open_per_symbol_blocks_the_second_entry(self, setup):
        engine, broker, _, config = setup
        config.risk.max_open_per_symbol = 1
        assert post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=1).accepted
        second = post(engine, "GOLD BUY 2352\nSL 2346\nTP 2362", message_id=2)
        assert not second.accepted
        assert "per symbol" in second.reason

    def test_blocked_symbol_is_refused(self, setup):
        engine, broker, _, config = setup
        config.risk.block_symbols = ["XAUUSD"]
        assert not post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360").accepted
        assert broker.positions() == []

    def test_as_stated_entry_creates_a_pending_order(self, setup):
        engine, broker, _, config = setup
        config.execution.entry = "as_stated"
        broker.seed_price("XAUUSD", 2360.0)
        decision = post(engine, "BUY LIMIT GOLD @ 2350\nSL 2344\nTP 2365")
        assert decision.accepted
        # Buying below the market is a limit order, and it must stay pending.
        assert broker.positions() == []
        pending = broker.pending_orders()
        assert len(pending) == 1
        assert pending[0].open_price == 2350

    def test_slippage_guard_skips_a_move_that_already_ran(self, setup):
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 0
        config.execution.max_entry_slippage_points = 100  # $1.00 on gold
        # Signal says buy 2350 but the market is already 2355.
        broker.seed_price("XAUUSD", 2355.0)
        decision = engine.handle(
            "GOLD BUY 2350\nSL 2344\nTP 2360",
            MessageRef(chat_id=CHAT_ID, message_id=1),
        )
        assert not decision.accepted
        assert "already moved" in decision.reason


class TestSlippageAsShareOfStop:
    """The instrument-agnostic guard: how far price ran, relative to the stop."""

    def test_a_prompt_fill_is_allowed(self, setup):
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 50
        # Entry 2350, stop 2344 ($6 stop). Market at 2351 = 17% of the stop.
        broker.seed_price("XAUUSD", 2351.0)
        assert post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360").accepted

    def test_a_move_that_ran_most_of_the_way_is_skipped(self, setup):
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 50
        # Market at 2354 = 67% of the $6 stop already gone.
        broker.seed_price("XAUUSD", 2354.0)
        decision = post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360")
        assert not decision.accepted
        assert "the move is gone" in decision.reason

    def test_price_moving_against_the_signal_is_not_slippage(self, setup):
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 50
        # Market at 2348: a *better* entry than posted. Never a reason to skip.
        broker.seed_price("XAUUSD", 2348.0)
        assert post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360").accepted

    def test_sell_side(self, setup):
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 50
        # Sell posted at 2350 with a 2356 stop; market already down at 2346.
        broker.seed_price("XAUUSD", 2346.0)
        decision = post(engine, "GOLD SELL 2350\nSL 2356\nTP 2340")
        assert not decision.accepted
        assert "the move is gone" in decision.reason

    def test_the_same_setting_works_on_a_synthetic_index(self, setup):
        """The reason this guard is stop-relative.

        A points limit tuned for gold ($1.50) would reject every V75 signal,
        since V75 trades near 250,000 and moves that far instantly.
        """
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 50
        config.risk.allow_symbols = []
        # Entry 250000, stop 249000 (1000-wide). Market at 250200 = 20% used.
        broker.seed_price("V75", 250200.0)
        assert post(engine, "V75 BUY 250000\nSL 249000\nTP 252000").accepted

    def test_synthetic_that_did_run_too_far_is_skipped(self, setup):
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 50
        config.risk.allow_symbols = []
        # Market at 250700 = 70% of the 1000-wide stop already gone.
        broker.seed_price("V75", 250700.0)
        decision = post(engine, "V75 BUY 250000\nSL 249000\nTP 252000")
        assert not decision.accepted
        assert "the move is gone" in decision.reason

    def test_disabled_by_zero(self, setup):
        engine, broker, _, config = setup
        config.execution.max_entry_slippage_pct_of_stop = 0
        config.execution.max_entry_slippage_points = 0
        broker.seed_price("XAUUSD", 2355.0)
        assert post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360").accepted

    def test_pending_orders_are_exempt(self, setup):
        engine, broker, _, config = setup
        config.execution.entry = "as_stated"
        config.execution.max_entry_slippage_pct_of_stop = 1
        broker.seed_price("XAUUSD", 2354.0)
        # A pending order sits and waits for its price; slippage is irrelevant.
        assert post(engine, "BUY LIMIT GOLD @ 2350\nSL 2344\nTP 2360").accepted


class TestManagement:
    def _open(self, engine, message_id: int = 1):
        decision = post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=message_id)
        assert decision.accepted
        return decision

    def test_close_all_closes_the_position(self, setup):
        engine, broker, _, _ = setup
        self._open(engine)
        decision = post(engine, "close all trades", message_id=2)
        assert decision.accepted
        assert broker.positions() == []

    def test_reply_targets_only_that_signal(self, setup):
        engine, broker, _, config = setup
        config.risk.max_open_per_symbol = 5
        config.risk.dedupe_window_minutes = 0
        self._open(engine, message_id=10)
        post(engine, "EURUSD BUY 1.0850\nSL 1.0820\nTP 1.0900", message_id=11)
        assert len(broker.positions()) == 2

        # Replying to the gold post must leave the EURUSD trade alone.
        decision = post(engine, "close this one", message_id=12, reply_to=10)
        assert decision.accepted
        remaining = broker.positions()
        assert len(remaining) == 1
        assert remaining[0].symbol == "EURUSD"

    def test_symbol_named_in_the_follow_up_is_used(self, setup):
        engine, broker, _, config = setup
        config.risk.max_open_per_symbol = 5
        config.risk.dedupe_window_minutes = 0
        self._open(engine, message_id=1)
        post(engine, "EURUSD BUY 1.0850\nSL 1.0820\nTP 1.0900", message_id=2)
        post(engine, "close gold now", message_id=3)
        assert [p.symbol for p in broker.positions()] == ["EURUSD"]

    def test_break_even_moves_the_stop_to_entry(self, setup):
        engine, broker, _, config = setup
        config.risk.breakeven_offset_points = 20
        self._open(engine)
        decision = post(engine, "SL to BE guys", message_id=2)
        assert decision.accepted
        assert broker.positions()[0].stop_loss == pytest.approx(2350.20)

    def test_move_stop_to_a_better_price(self, setup):
        engine, broker, _, _ = setup
        self._open(engine)
        assert post(engine, "move SL to 2348", message_id=2).accepted
        assert broker.positions()[0].stop_loss == 2348

    def test_widening_the_stop_is_refused(self, setup):
        engine, broker, _, _ = setup
        self._open(engine)
        decision = post(engine, "move SL to 2340", message_id=2)
        assert not decision.accepted
        assert broker.positions()[0].stop_loss == 2344  # untouched

    def test_partial_close_reduces_the_volume(self, setup):
        engine, broker, _, _ = setup
        self._open(engine)
        before = broker.positions()[0].volume
        assert post(engine, "close half", message_id=2).accepted
        after = broker.positions()[0].volume
        assert after < before
        assert after == pytest.approx(round(before / 2, 2), abs=0.01)

    def test_management_with_nothing_open_is_a_no_op(self, setup):
        engine, broker, _, _ = setup
        decision = post(engine, "close all trades")
        assert not decision.accepted
        assert "no matching open position" in decision.reason

    def test_cancel_removes_a_pending_order(self, setup):
        engine, broker, _, config = setup
        config.execution.entry = "as_stated"
        broker.seed_price("XAUUSD", 2360.0)
        post(engine, "BUY LIMIT GOLD @ 2350\nSL 2344\nTP 2365", message_id=1)
        assert len(broker.pending_orders()) == 1
        assert post(engine, "cancel that signal", message_id=2).accepted
        assert broker.pending_orders() == []


class TestJournalIntegration:
    def test_accepted_and_skipped_are_both_recorded(self, setup):
        engine, _, journal, _ = setup
        post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=1)
        post(engine, "good morning team", message_id=2)
        summary = journal.summary(days=1)
        assert summary["signals_accepted"] == 1
        assert summary["signals_skipped"] >= 1
        assert summary["orders_filled"] == 1
        assert summary["live_orders"] == 0  # paper only

    def test_tickets_are_linked_to_the_message(self, setup):
        engine, _, journal, _ = setup
        decision = post(engine, "GOLD BUY 2350\nSL 2344\nTP 2360", message_id=77)
        tickets = journal.tickets_for_message(CHAT_ID, 77)
        assert tickets == [order.ticket for order in decision.orders if order.ok]

    def test_a_broken_message_cannot_crash_the_engine(self, setup):
        engine, _, _, _ = setup
        for text in ["", "   ", "🔥🔥🔥", "SL SL SL TP TP", "BUY " * 200]:
            decision = engine.handle(text, MessageRef(chat_id=CHAT_ID, message_id=1))
            assert not decision.accepted


class TestDerivSyntheticSpecs:
    """Paper specs for synthetics. Approximations, but they must not mislead."""

    def test_volatility_and_boom_have_different_minimum_lots(self):
        broker = PaperBroker()
        volatility = broker.symbol_info("Volatility 75 Index")
        boom = broker.symbol_info("Boom 500 Index")
        # This gap is the point: 0.2 lots of Boom is a very different risk to
        # 0.001 lots of V75, and a dry run should show that before you go live.
        assert volatility.volume_min == 0.001
        assert boom.volume_min == 0.2

    def test_contract_size_is_one_unit_per_index_point(self):
        broker = PaperBroker()
        for name in ("Volatility 75 Index", "Boom 500 Index", "Crash 1000 Index"):
            info = broker.symbol_info(name)
            assert info.value_per_price_unit() == pytest.approx(1.0), name

    def test_short_and_long_names_get_the_same_spec(self):
        broker = PaperBroker()
        assert broker.symbol_info("V75").volume_min == broker.symbol_info(
            "Volatility 75 Index"
        ).volume_min

    def test_a_synthetic_signal_sizes_and_places(self, setup):
        engine, broker, _, config = setup
        config.risk.allow_symbols = []
        decision = post(engine, "V75 BUY 250000\nSL 249000\nTP 252000")
        assert decision.accepted
        position = broker.positions()[0]
        # $100 budget / (~1000-wide stop * $1 per point) ≈ 0.1 lots, less the
        # spread, and always rounded down onto the 0.001 step — never above.
        assert 0.09 <= position.volume <= 0.1
        assert position.symbol == "V75"

    def test_boom_signal_respects_the_larger_minimum_lot(self, setup):
        engine, broker, _, config = setup
        config.risk.allow_symbols = []
        decision = post(engine, "BOOM 500 BUY 12500\nSL 12400\nTP 12700")
        assert decision.accepted
        assert broker.positions()[0].volume >= 0.2


class TestPaperBrokerSafety:
    def test_default_config_never_goes_live(self):
        config = config_module.load("does-not-exist.yaml", env={})
        assert not config.execution.live_enabled

    def test_live_mode_without_the_env_acknowledgement_stays_on_paper(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("execution:\n  mode: live\n")
        config = config_module.load(path, env={})
        assert not config.execution.live_enabled
        assert "TGSCALPER_ALLOW_LIVE" in config.execution.live_block_reason

    def test_live_mode_with_the_acknowledgement_is_enabled(self, tmp_path):
        path = tmp_path / "config.yaml"
        path.write_text("execution:\n  mode: live\n")
        config = config_module.load(
            path, env={"TGSCALPER_ALLOW_LIVE": config_module.LIVE_ACK}
        )
        assert config.execution.live_enabled

    def test_build_broker_returns_paper_unless_live(self):
        from tgscalper.brokers import build_broker

        config = config_module.load("does-not-exist.yaml", env={})
        config.broker.provider = "mt5"  # would be MT5 if live were enabled
        broker = build_broker(config)
        assert isinstance(broker, PaperBroker)
        assert not broker.is_live
