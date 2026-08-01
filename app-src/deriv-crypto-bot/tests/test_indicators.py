from deriv_bot.indicators import Candle, atr, ema, rsi


def make_candles(closes, spread=1.0):
    return [
        Candle(epoch=1000 + i * 60, open=c, high=c + spread, low=c - spread, close=c)
        for i, c in enumerate(closes)
    ]


class TestEma:
    def test_warmup_is_none_then_seeded_with_sma(self):
        values = [1, 2, 3, 4, 5]
        result = ema(values, 3)
        assert result[:2] == [None, None]
        assert result[2] == 2.0  # (1+2+3)/3

    def test_short_input_is_all_none(self):
        assert ema([1, 2], 5) == [None] * 2

    def test_follows_a_constant_series(self):
        result = ema([7.0] * 20, 5)
        assert result[-1] == 7.0

    def test_known_progression(self):
        # multiplier for period 3 is 0.5
        result = ema([1, 2, 3, 10], 3)
        assert result[3] == (10 - 2.0) * 0.5 + 2.0  # 6.0

    def test_length_always_matches_input(self):
        assert len(ema(list(range(50)), 9)) == 50


class TestRsi:
    def test_all_gains_is_one_hundred(self):
        assert rsi(list(range(1, 40)), 14)[-1] == 100.0

    def test_all_losses_is_zero(self):
        assert rsi(list(range(40, 1, -1)), 14)[-1] == 0.0

    def test_flat_series_has_no_movement(self):
        # No gains and no losses: avg_loss is zero, so RSI is defined as 100.
        assert rsi([5.0] * 30, 14)[-1] == 100.0

    def test_warmup_region_is_none(self):
        result = rsi([float(i) for i in range(30)], 14)
        assert all(v is None for v in result[:14])
        assert result[14] is not None

    def test_bounded_between_zero_and_hundred(self):
        closes = [10, 12, 11, 13, 15, 14, 16, 18, 17, 19, 21, 20, 22, 24, 23, 25, 27, 26]
        for value in rsi([float(c) for c in closes], 5):
            if value is not None:
                assert 0.0 <= value <= 100.0


class TestAtr:
    def test_constant_range_gives_that_range(self):
        # Every candle spans exactly 2.0 and closes flat, so ATR settles at 2.0.
        candles = make_candles([100.0] * 30, spread=1.0)
        assert abs(atr(candles, 14)[-1] - 2.0) < 1e-9

    def test_short_input_is_all_none(self):
        assert atr(make_candles([1.0, 2.0]), 14) == [None, None]

    def test_gap_widens_true_range(self):
        calm = atr(make_candles([100.0] * 30), 14)[-1]
        jumpy = atr(make_candles([100.0] * 25 + [140.0] * 5), 14)[-1]
        assert jumpy > calm


class TestCandle:
    def test_parses_api_payload_with_string_numbers(self):
        candle = Candle.from_api(
            {"epoch": "1700000000", "open": "1.5", "high": "2.5", "low": "1.0", "close": "2.0"}
        )
        assert candle.epoch == 1700000000
        assert candle.high == 2.5
        assert isinstance(candle.close, float)
