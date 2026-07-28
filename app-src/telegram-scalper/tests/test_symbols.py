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


DERIV_MT5_SYMBOLS = [
    "Volatility 10 Index",
    "Volatility 25 Index",
    "Volatility 75 Index",
    "Volatility 100 Index",
    "Boom 500 Index",
    "Boom 1000 Index",
    "Crash 500 Index",
    "Crash 1000 Index",
    "Step Index",
    "Jump 75 Index",
    "XAUUSD",
    "EURUSD",
]


class TestDerivSynthetics:
    """Deriv names them "Volatility 75 Index"; groups write "V75" or "vix75"."""

    def test_shorthand_spellings(self):
        assert find_symbol("V75 buy now") == "V75"
        assert find_symbol("buy vix75") == "V75"
        assert find_symbol("VIX 75 sell") == "V75"
        assert find_symbol("vol 75 long") == "V75"
        assert find_symbol("R_75 buy") == "V75"

    def test_full_broker_name_in_the_message(self):
        assert find_symbol("Volatility 75 Index sell now") == "V75"

    def test_boom_and_crash(self):
        assert find_symbol("BOOM 500 BUY") == "BOOM500"
        assert find_symbol("boom1000 buy now") == "BOOM1000"
        assert find_symbol("crash 1000 sell") == "CRASH1000"
        assert find_symbol("C500 sell now") == "CRASH500"

    def test_step_and_jump(self):
        assert find_symbol("sell step index") == "STEPINDEX"
        assert find_symbol("J75 buy") == "JUMP75"

    def test_volatility_levels_are_distinct(self):
        assert find_symbol("buy V100") == "V100"
        assert find_symbol("buy V25") == "V25"
        assert find_symbol("buy V10") == "V10"

    def test_bare_words_are_never_synthetics(self):
        # These must stay chat. A bare CRASH/BOOM/STEP alias would invent trades.
        for text in [
            "market crash incoming, be careful",
            "boom! nice profit today",
            "step by step guide for new members",
            "the vol is high today",
            "jump on this one quickly",
        ]:
            assert find_symbol(text) is None, text

    def test_resolves_to_the_spaced_broker_name(self):
        resolver = SymbolResolver()
        resolver.load_available(DERIV_MT5_SYMBOLS)
        assert resolver.resolve("V75") == "Volatility 75 Index"
        assert resolver.resolve("vix 75") == "Volatility 75 Index"
        assert resolver.resolve("boom 500") == "Boom 500 Index"
        assert resolver.resolve("crash1000") == "Crash 1000 Index"
        assert resolver.resolve("step index") == "Step Index"

    def test_forex_still_resolves_on_a_deriv_account(self):
        resolver = SymbolResolver()
        resolver.load_available(DERIV_MT5_SYMBOLS)
        assert resolver.resolve("gold") == "XAUUSD"

    def test_synthetic_absent_from_the_account_is_refused(self):
        resolver = SymbolResolver()
        resolver.load_available(["Volatility 75 Index"])
        assert resolver.resolve("boom 500") is None


class TestExnessNaming:
    """Exness is an ordinary MT5 broker; only the symbol suffix varies."""

    def test_plain_names(self):
        resolver = SymbolResolver()
        resolver.load_available(["XAUUSD", "EURUSD", "GBPUSD"])
        assert resolver.resolve("gold") == "XAUUSD"

    def test_cent_account_suffix(self):
        resolver = SymbolResolver(suffix="m")
        resolver.load_available(["XAUUSDm", "EURUSDm"])
        assert resolver.resolve("gold") == "XAUUSDm"
        assert resolver.resolve("eur/usd") == "EURUSDm"

    def test_suffix_config_does_not_break_unsuffixed_accounts(self):
        # Same config.yaml pointed at a Standard account must still work.
        resolver = SymbolResolver(suffix="m")
        resolver.load_available(["XAUUSD", "EURUSD"])
        assert resolver.resolve("gold") == "XAUUSD"
