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


class TestBitcoinOnly:
    """Restricting to Bitcoin is the configured default, so it gets its own
    coverage — including that an alias can never escape the crypto filter."""

    UNIVERSE = [
        symbol("cryBTCUSD"),
        symbol("cryETHUSD"),
        symbol("cryLTCUSD"),
        symbol("frxEURUSD", market="forex"),
        symbol("R_100", market="synthetic_index"),
    ]

    def select(self, aliases, universe=None):
        config = make_config(symbols=tuple(aliases))
        return [s.symbol for s in select_symbols(universe or self.UNIVERSE, config)]

    @pytest.mark.parametrize("alias", ["cryBTCUSD", "crybtcusd", "CRYBTCUSD", "BTC", "btc"])
    def test_bitcoin_resolves_from_several_spellings(self, alias):
        assert self.select([alias]) == ["cryBTCUSD"]

    def test_display_name_resolves(self):
        universe = [
            {**symbol("cryBTCUSD"), "display_name": "BTC/USD"},
            {**symbol("cryETHUSD"), "display_name": "ETH/USD"},
        ]
        assert self.select(["BTC/USD"], universe) == ["cryBTCUSD"]

    def test_bitcoin_only_excludes_every_other_coin(self):
        selected = self.select(["BTC"])
        assert selected == ["cryBTCUSD"]
        assert "cryETHUSD" not in selected
        assert "cryLTCUSD" not in selected

    def test_an_alias_cannot_reach_a_non_crypto_symbol(self):
        # The central invariant, restated for aliases: however it is spelled,
        # a match is only ever drawn from the crypto-filtered set.
        assert self.select(["EUR"]) == []
        assert self.select(["frxEURUSD"]) == []
        assert self.select(["R_100"]) == []

    def test_a_too_short_alias_does_not_match_everything(self):
        assert self.select(["c"]) == []

    def test_exact_match_wins_over_substring(self):
        universe = [symbol("cryBTCUSD"), symbol("cryBTCUSDT")]
        assert self.select(["cryBTCUSD"], universe) == ["cryBTCUSD"]

    def test_a_substring_may_match_several_pairs(self):
        universe = [symbol("cryBTCUSD"), symbol("cryBTCEUR"), symbol("cryETHUSD")]
        assert sorted(self.select(["BTC"], universe)) == ["cryBTCEUR", "cryBTCUSD"]

    def test_multiple_aliases_combine(self):
        assert sorted(self.select(["BTC", "ETH"])) == ["cryBTCUSD", "cryETHUSD"]

    def test_duplicate_aliases_do_not_duplicate_symbols(self):
        assert self.select(["BTC", "cryBTCUSD", "btc"]) == ["cryBTCUSD"]

    def test_a_closed_bitcoin_market_yields_nothing(self):
        universe = [symbol("cryBTCUSD", is_open=0), symbol("cryETHUSD")]
        assert self.select(["BTC"], universe) == []

    def test_unmatched_alias_is_reported(self, caplog):
        import logging

        with caplog.at_level(logging.ERROR):
            assert self.select(["DOGE"]) == []
        assert "DOGE" in caplog.text
        assert "cryBTCUSD" in caplog.text  # lists what is available

    def test_non_crypto_alias_says_why(self, caplog):
        import logging

        with caplog.at_level(logging.ERROR):
            self.select(["frxEURUSD"])
        assert "not a cryptocurrency" in caplog.text
