"""Tests for the crypto-only invariant and contract-shape resolution."""

import pytest

from deriv_bot.market import (
    duration_seconds,
    find_contract,
    is_crypto,
    parse_duration,
    resolve_duration,
    select_symbols,
)

from conftest import make_config


def symbol(name, market="cryptocurrency", is_open=1, suspended=0):
    return {
        "symbol": name,
        "display_name": name,
        "market": market,
        "submarket": "non_stable_coin",
        "exchange_is_open": is_open,
        "is_trading_suspended": suspended,
    }


UNIVERSE = [
    symbol("cryBTCUSD"),
    symbol("cryETHUSD"),
    symbol("frxEURUSD", market="forex"),
    symbol("R_100", market="synthetic_index"),
    symbol("OTC_SPC", market="indices"),
]


class TestIsCrypto:
    def test_accepts_cryptocurrency(self):
        assert is_crypto({"market": "cryptocurrency"})

    def test_is_case_and_whitespace_insensitive(self):
        assert is_crypto({"market": " Cryptocurrency "})

    @pytest.mark.parametrize("market", ["forex", "synthetic_index", "indices", "commodities", ""])
    def test_rejects_every_other_market(self, market):
        assert not is_crypto({"market": market})

    def test_rejects_missing_market_field(self):
        assert not is_crypto({"symbol": "cryBTCUSD"})


class TestSelectSymbols:
    def test_keeps_only_crypto(self):
        selected = select_symbols(UNIVERSE, make_config())
        assert [s.symbol for s in selected] == ["cryBTCUSD", "cryETHUSD"]

    def test_allowlist_cannot_smuggle_in_a_non_crypto_symbol(self):
        # The central safety property: naming forex in DERIV_SYMBOLS drops it.
        config = make_config(symbols=("frxEURUSD", "cryBTCUSD"))
        selected = select_symbols(UNIVERSE, config)
        assert [s.symbol for s in selected] == ["cryBTCUSD"]

    def test_allowlist_of_only_non_crypto_yields_nothing(self):
        config = make_config(symbols=("frxEURUSD", "R_100"))
        assert select_symbols(UNIVERSE, config) == []

    def test_unknown_symbols_are_dropped(self):
        config = make_config(symbols=("cryNOPEUSD",))
        assert select_symbols(UNIVERSE, config) == []

    def test_closed_markets_are_skipped(self):
        universe = [symbol("cryBTCUSD", is_open=0), symbol("cryETHUSD")]
        assert [s.symbol for s in select_symbols(universe, make_config())] == ["cryETHUSD"]

    def test_suspended_symbols_are_skipped(self):
        universe = [symbol("cryBTCUSD", suspended=1), symbol("cryETHUSD")]
        assert [s.symbol for s in select_symbols(universe, make_config())] == ["cryETHUSD"]

    def test_max_symbols_caps_the_universe(self):
        universe = [symbol(f"cry{i}USD") for i in range(10)]
        assert len(select_symbols(universe, make_config(max_symbols=3))) == 3

    def test_empty_input_is_handled(self):
        assert select_symbols([], make_config()) == []


class TestParseDuration:
    @pytest.mark.parametrize(
        "text,expected",
        [("5m", (5, "m")), ("1t", (1, "t")), ("365d", (365, "d")), ("30s", (30, "s")), ("2h", (2, "h"))],
    )
    def test_valid(self, text, expected):
        assert parse_duration(text) == expected

    @pytest.mark.parametrize("text", ["", "m", "5x", "abc", "0m", "-5m", "5"])
    def test_invalid_returns_none(self, text):
        assert parse_duration(text) is None

    def test_seconds_conversion(self):
        assert duration_seconds(5, "m") == 300
        assert duration_seconds(1, "d") == 86400
        assert duration_seconds(3, "t") is None


class TestFindContract:
    def test_finds_matching_spot_callput(self):
        contracts = {
            "available": [
                {"contract_type": "PUT", "contract_category": "callput", "start_type": "spot"},
                {"contract_type": "CALL", "contract_category": "callput", "start_type": "spot"},
            ]
        }
        assert find_contract(contracts, "CALL")["contract_type"] == "CALL"

    def test_ignores_other_categories(self):
        contracts = {
            "available": [
                {"contract_type": "CALL", "contract_category": "multiplier", "start_type": "spot"}
            ]
        }
        assert find_contract(contracts, "CALL") is None

    def test_ignores_forward_starting(self):
        contracts = {
            "available": [
                {"contract_type": "CALL", "contract_category": "callput", "start_type": "forward"}
            ]
        }
        assert find_contract(contracts, "CALL") is None

    def test_ignores_barrier_contracts(self):
        contracts = {
            "available": [
                {
                    "contract_type": "CALL",
                    "contract_category": "callput",
                    "start_type": "spot",
                    "barrier_category": "american",
                }
            ]
        }
        assert find_contract(contracts, "CALL") is None

    def test_empty_availability(self):
        assert find_contract({"available": []}, "CALL") is None
        assert find_contract({}, "CALL") is None


class TestResolveDuration:
    def test_keeps_configured_duration_when_in_range(self):
        entry = {"min_contract_duration": "1m", "max_contract_duration": "1d"}
        assert resolve_duration(entry, make_config(trade_duration=5)) == (5, "m")

    def test_raises_to_the_minimum(self):
        entry = {"min_contract_duration": "15m", "max_contract_duration": "1d"}
        assert resolve_duration(entry, make_config(trade_duration=5)) == (15, "m")

    def test_lowers_to_the_maximum(self):
        entry = {"min_contract_duration": "1m", "max_contract_duration": "10m"}
        assert resolve_duration(entry, make_config(trade_duration=60)) == (10, "m")

    def test_tick_quoted_contract_falls_back_when_units_mismatch(self):
        entry = {"min_contract_duration": "5t", "max_contract_duration": "10t"}
        assert resolve_duration(entry, make_config(trade_duration=5)) == (5, "t")

    def test_tick_preference_is_clamped_numerically(self):
        entry = {"min_contract_duration": "5t", "max_contract_duration": "10t"}
        config = make_config(trade_duration=99, trade_duration_unit="t")
        assert resolve_duration(entry, config) == (10, "t")

    def test_missing_bounds_keeps_configuration(self):
        assert resolve_duration({}, make_config(trade_duration=7)) == (7, "m")

    def test_unparseable_bounds_keep_configuration(self):
        entry = {"min_contract_duration": "???", "max_contract_duration": "???"}
        assert resolve_duration(entry, make_config(trade_duration=7)) == (7, "m")
