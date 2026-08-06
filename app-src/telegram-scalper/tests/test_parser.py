"""Parser tests. Every case here is a format real signal groups actually post."""

from __future__ import annotations

import pytest

from tgscalper.models import Action, OrderType, Side
from tgscalper.parser import parse


def signal(text: str, **kwargs):
    result = parse(text, **kwargs)
    assert result.ok, f"expected a signal, got: {result.error}"
    return result.signal


def rejected(text: str, **kwargs) -> str:
    result = parse(text, **kwargs)
    assert not result.ok, f"expected a rejection, got: {result.signal and result.signal.summary()}"
    return result.error


class TestOpenSignals:
    def test_multiline_gold_with_three_targets(self):
        parsed = signal("🔥 GOLD BUY NOW 2350.5\nSL 2344\nTP1 2355\nTP2 2360\nTP3 2370")
        assert parsed.symbol == "XAUUSD"
        assert parsed.side is Side.BUY
        assert parsed.entry == 2350.5
        assert parsed.stop_loss == 2344
        assert parsed.take_profits == [2355, 2360, 2370]

    def test_entry_zone_uses_midpoint(self):
        parsed = signal("BUY XAUUSD @ 2350-2352\nSL: 2344\nTP: 2355, 2360, 2370")
        assert parsed.entry_zone == (2350.0, 2352.0)
        assert parsed.entry == 2351.0
        assert parsed.take_profits == [2355, 2360, 2370]

    def test_sell_limit_keeps_pending_order_type(self):
        parsed = signal("SELL LIMIT EURUSD\nEntry: 1.0850\nSL 1.0880\nTP 1.0800")
        assert parsed.side is Side.SELL
        assert parsed.order_type is OrderType.LIMIT
        assert parsed.entry == 1.0850
        assert parsed.stop_loss == 1.0880

    def test_inline_single_line_format(self):
        parsed = signal("SELL GBP/JPY 188.50 SL 189.00 TP 187.50")
        assert parsed.symbol == "GBPJPY"
        assert parsed.side is Side.SELL
        assert parsed.entry == 188.50

    def test_index_symbol_digits_are_not_read_as_price(self):
        parsed = signal("BUY US30 44250\nSL 44100\nTP 44500")
        assert parsed.symbol == "US30"
        assert parsed.entry == 44250  # not 30

    def test_nas100_with_two_targets(self):
        parsed = signal("SELL NAS100 @ 19850 SL 19900 TP1 19800 TP2 19750")
        assert parsed.symbol == "NAS100"
        assert parsed.entry == 19850
        assert parsed.take_profits == [19800, 19750]

    def test_market_order_without_a_price(self):
        parsed = signal("Buy gold now\nsl 2344\ntp 2360")
        assert parsed.entry is None
        assert parsed.order_type is OrderType.MARKET

    def test_slash_notation_for_sl_and_tp(self):
        parsed = signal("BUY BTC 61000\nS/L 60200\nT/P 62000")
        assert parsed.symbol == "BTCUSD"
        assert parsed.stop_loss == 60200

    def test_decimal_comma(self):
        parsed = signal("BUY EURUSD 1,0850\nSL 1,0820\nTP 1,0900")
        assert parsed.entry == 1.0850
        assert parsed.stop_loss == 1.0820

    def test_thousands_separator(self):
        parsed = signal("BUY US30 44,250\nSL 44,100\nTP 44,500")
        assert parsed.entry == 44250
        assert parsed.stop_loss == 44100

    def test_two_digit_shorthand_is_expanded(self):
        parsed = signal("gold buy 2350 sl 44 tp 60")
        assert parsed.stop_loss == 2344
        assert parsed.take_profits == [2360]
        assert any("shorthand" in warning for warning in parsed.warnings)

    def test_take_profit_written_out(self):
        parsed = signal("BUY XAUUSD 2350\nStop Loss: 2344\nTake Profit: 2360")
        assert parsed.stop_loss == 2344
        assert parsed.take_profits == [2360]

    def test_targets_keyword(self):
        parsed = signal("SELL EURUSD 1.0850\nSL 1.0880\nTargets: 1.0820 1.0800")
        assert parsed.take_profits == [1.0820, 1.0800]

    def test_long_and_short_are_directions(self):
        assert signal("LONG XAUUSD 2350 SL 2344 TP 2360").side is Side.BUY
        assert signal("SHORT XAUUSD 2350 SL 2356 TP 2340").side is Side.SELL

    def test_stop_in_pips_is_kept_as_a_distance(self):
        parsed = signal("BUY EURUSD 1.0850\nSL 30 pips\nTP 1.0900")
        assert parsed.stop_loss is None
        assert parsed.sl_pips == 30

    def test_noise_lines_do_not_become_prices(self):
        parsed = signal(
            "GOLD BUY 2350\nSL 2344\nTP 2360\nTimeframe M15\nRisk 1%\nLot 0.05\nRR 1:2"
        )
        assert parsed.entry == 2350
        assert parsed.stop_loss == 2344
        assert parsed.take_profits == [2360]

    def test_deriv_volatility_index(self):
        parsed = signal("V75 BUY NOW 250000\nSL 249000\nTP 252000")
        assert parsed.symbol == "V75"
        assert parsed.side is Side.BUY
        assert parsed.entry == 250000

    def test_boom_index_digits_are_not_read_as_the_price(self):
        # "BOOM 500" must be masked, exactly like "US30".
        parsed = signal("BOOM 500 BUY 12500 SL 12400 TP 12700")
        assert parsed.symbol == "BOOM500"
        assert parsed.entry == 12500  # not 500

    def test_crash_index_sell(self):
        parsed = signal("CRASH 1000 SELL 9800\nSL 9900\nTP 9600")
        assert parsed.symbol == "CRASH1000"
        assert parsed.side is Side.SELL
        assert parsed.stop_loss == 9900

    def test_step_index_with_decimals(self):
        parsed = signal("Step Index BUY 8945.6 SL 8940.2 TP 8955.0")
        assert parsed.symbol == "STEPINDEX"
        assert parsed.entry == 8945.6

    def test_duplicate_target_restated_in_footer(self):
        parsed = signal("BUY GOLD 2350\nSL 2344\nTP1 2360\nTP2 2370\nRemember TP1 2360 is key")
        assert parsed.take_profits == [2360, 2370]


class TestRejections:
    def test_stop_on_wrong_side_of_entry(self):
        assert "wrong side" in rejected("BUY GOLD 2350 SL 2360 TP 2370")

    def test_target_on_wrong_side_of_entry(self):
        assert "wrong side" in rejected("SELL GOLD 2350 SL 2356 TP 2360")

    def test_implausible_target(self):
        assert "implausibly far" in rejected("BUY GOLD 2350 SL 2344 TP 9999")

    def test_missing_stop_loss_when_required(self):
        assert "no stop loss" in rejected("BUY GOLD 2350 TP 2360")

    def test_missing_stop_loss_allowed_when_configured(self):
        parsed = signal("BUY GOLD 2350 TP 2360", require_sl=False)
        assert parsed.stop_loss is None

    def test_chit_chat_is_ignored(self):
        assert rejected("Good morning everyone, market is quiet today")

    def test_result_announcements_are_ignored(self):
        assert rejected("TP1 hit 🎉 congrats team")

    def test_analysis_is_not_an_order(self):
        # "bullish" must never be read as a BUY instruction.
        error = rejected("Analysis: gold looking bullish on H4, watch 2350 zone")
        assert error

    def test_hedged_language_needs_full_structure(self):
        error = rejected("Maybe buy gold around 2350 if it holds, sl 2344")
        assert "analysis" in error

    def test_no_symbol(self):
        assert "symbol" in rejected("BUY NOW 2350 SL 2344 TP 2360")

    def test_empty_message(self):
        assert "empty" in rejected("   ")

    def test_pending_order_without_a_price(self):
        assert "without an entry price" in rejected("BUY LIMIT GOLD\nSL 2344\nTP 2360")


class TestManagement:
    def test_break_even(self):
        assert signal("SL to BE now guys").action is Action.BREAKEVEN

    def test_break_even_spelled_out(self):
        assert signal("Move your SL to entry, trade is risk free now").action is Action.BREAKEVEN

    def test_close_all(self):
        assert signal("close all trades").action is Action.CLOSE

    def test_close_half(self):
        parsed = signal("Close half on gold")
        assert parsed.action is Action.CLOSE_PARTIAL
        assert parsed.close_fraction == 0.5
        assert parsed.symbol == "XAUUSD"

    def test_close_percentage(self):
        parsed = signal("Close 30% and hold the rest")
        assert parsed.action is Action.CLOSE_PARTIAL
        assert parsed.close_fraction == pytest.approx(0.3)

    def test_close_one_third(self):
        parsed = signal("book 1/3 here")
        assert parsed.close_fraction == pytest.approx(1 / 3)

    def test_move_stop_to_a_price(self):
        parsed = signal("Move SL to 2352")
        assert parsed.action is Action.MOVE_SL
        assert parsed.new_sl == 2352

    def test_cancel_pending(self):
        assert signal("Signal cancelled, delete the pending").action is Action.CANCEL_PENDING

    def test_close_the_buy_is_management_not_a_new_entry(self):
        # Contains "buy" but is plainly an instruction to exit.
        assert signal("close the buy on gold now").action is Action.CLOSE

    def test_close_100_percent_is_a_full_close(self):
        assert signal("close 100% now").action is Action.CLOSE

    def test_close_naming_the_instrument(self):
        parsed = signal("guys close gold now")
        assert parsed.action is Action.CLOSE
        assert parsed.symbol == "XAUUSD"

    def test_stops_to_entry(self):
        assert signal("stops to entry please").action is Action.BREAKEVEN


class TestEmojiDirection:
    """Rooms that mark direction with an arrow instead of the word BUY/SELL."""

    def test_green_marker_is_a_buy(self):
        parsed = signal("XAUUSD 🟢 3350\nSL 3344\nTP 3360")
        assert parsed.side is Side.BUY
        assert parsed.entry == 3350
        assert parsed.stop_loss == 3344

    def test_red_marker_is_a_sell(self):
        parsed = signal("GOLD 🔻 3350\nSL 3356\nTP 3340")
        assert parsed.side is Side.SELL
        assert parsed.entry == 3350

    def test_arrows_work_too(self):
        assert signal("XAUUSD ⬆️ 3350 SL 3344 TP 3360").side is Side.BUY
        assert signal("XAUUSD ⬇️ 3350 SL 3356 TP 3340").side is Side.SELL

    def test_the_inference_is_flagged_as_a_warning(self):
        parsed = signal("XAUUSD 🟢 3350\nSL 3344\nTP 3360")
        assert any("arrow" in warning for warning in parsed.warnings)

    def test_market_entry_when_no_price_is_given(self):
        parsed = signal("🟢 GOLD\nSL 3344\nTP 3360")
        assert parsed.side is Side.BUY
        assert parsed.entry is None

    def test_a_word_direction_still_wins(self):
        # A red decoration must not flip an explicit BUY.
        parsed = signal("🔴 GOLD BUY 3350\nSL 3344\nTP 3360")
        assert parsed.side is Side.BUY

    def test_both_markers_infer_nothing(self):
        # "🟢 BUY 🔴 SELL" is a legend or a summary, not an order.
        assert not parse("XAUUSD 🟢 🔴 3350\nSL 3344\nTP 3360").ok

    def test_decorative_emoji_without_levels_is_ignored(self):
        for text in [
            "🚀🚀 great week team 🔥",
            "GOLD 🚀 to the moon boys",
            "📈 markets looking good today",
        ]:
            assert not parse(text).ok, text

    def test_an_arrow_alone_is_not_enough_without_a_stop(self):
        # Requiring both SL and TP is what keeps decoration from trading.
        assert not parse("XAUUSD 🟢 3350\nTP 3360").ok
        assert not parse("XAUUSD 🟢 3350\nSL 3344").ok


class TestChatterIsNotAnInstruction:
    """Regression guards. Every string here once triggered a false action."""

    def test_be_careful_is_not_break_even(self):
        # "be careful" contains "BE" — this must never move a live stop.
        assert not parse("Market is quiet ahead of NFP, be careful today").ok

    def test_be_patient_is_not_break_even(self):
        assert not parse("be patient guys, waiting for a good entry").ok

    def test_market_closed_is_not_a_close_instruction(self):
        assert not parse("Market closed, see you all on Monday").ok

    def test_closed_at_target_is_a_result_not_an_order(self):
        assert not parse("Trade closed at TP2, +40 pips 🎉").ok

    def test_greeting_does_nothing(self):
        assert not parse("Good morning everyone, welcome to the new members").ok

    def test_general_encouragement_does_nothing(self):
        assert not parse("Great week team, secure your gains and rest well").ok


class TestFingerprint:
    def test_same_setup_reposted_matches(self):
        first = signal("GOLD BUY 2350\nSL 2344\nTP 2360")
        second = signal("🔥🔥 gold buy now 2350 sl 2344 tp 2360 🔥🔥")
        assert first.fingerprint() == second.fingerprint()

    def test_different_levels_do_not_match(self):
        first = signal("GOLD BUY 2350\nSL 2344\nTP 2360")
        second = signal("GOLD BUY 2351\nSL 2344\nTP 2360")
        assert first.fingerprint() != second.fingerprint()

    def test_opposite_direction_does_not_match(self):
        first = signal("GOLD BUY 2350\nSL 2344\nTP 2360")
        second = signal("GOLD SELL 2350\nSL 2356\nTP 2340")
        assert first.fingerprint() != second.fingerprint()
