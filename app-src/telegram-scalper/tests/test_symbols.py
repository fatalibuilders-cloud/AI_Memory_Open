"""Symbol vocabulary and broker-naming resolution."""

from __future__ import annotations

from tgscalper.symbols import SymbolResolver, find_symbol


class TestFindSymbol:
    def test_gold_aliases(self):
        for text in ["GOLD BUY NOW", "buy xauusd", "XAU/USD sell", "xau-usd", "GOLDUSD long"]:
            assert find_symbol(text) == "XAUUSD", text

    def test_fx_pairs_joined_and_separated(self):
        assert find_symbol("BUY EURUSD 1.08") == "EURUSD"
        assert find_symbol("sell eur/usd") == "EURUSD"
        assert find_symbol("GBP-JPY short") == "GBPJPY"

    def test_indices(self):
        assert find_symbol("buy us30") == "US30"
        assert find_symbol("DOW long") == "US30"
        assert find_symbol("nasdaq buy") == "NAS100"
        assert find_symbol("US100 sell") == "NAS100"

    def test_crypto_and_oil(self):
        assert find_symbol("BTC buy") == "BTCUSD"
        assert find_symbol("buy bitcoin") == "BTCUSD"
        assert find_symbol("sell WTI") == "USOIL"

    def test_ordinary_words_are_not_symbols(self):
        for text in [
            "close all trades now",
            "SL to BE",
            "good luck team",
            "TARGET reached",
            "market is quiet",
        ]:
            assert find_symbol(text) is None, text

    def test_longest_alias_wins(self):
        # "XAU/USD" must not be truncated to a bare "XAU" match.
        assert find_symbol("SELL XAU/USD NOW") == "XAUUSD"

    def test_custom_alias(self):
        aliases = {"XAUUSD": ["GOLD", "GOLDIE"]}
        assert find_symbol("buy goldie now", aliases) == "XAUUSD"


class TestResolver:
    def test_bare_name_when_the_broker_list_is_unknown(self):
        assert SymbolResolver().resolve("GOLD") == "XAUUSD"

    def test_suffix_is_applied(self):
        resolver = SymbolResolver(suffix=".m")
        assert resolver.resolve("GOLD") == "XAUUSD.m"

    def test_suffixed_name_is_picked_from_the_broker_list(self):
        resolver = SymbolResolver(suffix=".m")
        resolver.load_available(["XAUUSD.m", "EURUSD.m", "US30.m"])
        assert resolver.resolve("gold") == "XAUUSD.m"
        assert resolver.resolve("dow") == "US30.m"

    def test_falls_back_to_the_bare_name_when_the_suffixed_one_is_absent(self):
        resolver = SymbolResolver(suffix=".m")
        resolver.load_available(["XAUUSD", "EURUSD"])
        assert resolver.resolve("gold") == "XAUUSD"

    def test_broker_that_names_gold_gold(self):
        resolver = SymbolResolver()
        resolver.load_available(["GOLD", "EURUSD"])
        assert resolver.resolve("XAUUSD") == "GOLD"

    def test_explicit_override_wins(self):
        resolver = SymbolResolver(overrides={"NAS100": "USTEC.cash"})
        resolver.load_available(["USTEC.cash", "NAS100"])
        assert resolver.resolve("nasdaq") == "USTEC.cash"

    def test_untradable_symbol_returns_none(self):
        resolver = SymbolResolver()
        resolver.load_available(["EURUSD", "GBPUSD"])
        assert resolver.resolve("BTC") is None

    def test_brokers_own_casing_is_returned(self):
        resolver = SymbolResolver()
        resolver.load_available(["XauUsd"])
        assert resolver.resolve("gold") == "XauUsd"

    def test_unknown_text_resolves_to_nothing(self):
        assert SymbolResolver().resolve("close everything") is None
