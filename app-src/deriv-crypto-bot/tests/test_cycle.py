"""End-to-end tests for one trading cycle, against a fake Deriv API.

These exercise the real Trader code path — universe selection, signal, risk
check, proposal, buy, settlement — without touching the network.
"""

import asyncio

import pytest

from deriv_bot.state import StateStore
from deriv_bot.trader import Trader

from conftest import make_config
from test_strategy import PEAK, VALLEY, candles, scan


def signalling_candles():
    """The shortest candle window that makes the default strategy trade."""
    config = make_config(min_separation_atr=0.0)
    trades = scan(VALLEY, config)
    assert trades, "fixture produced no signal"
    end, _ = trades[0]
    return [
        {"epoch": c.epoch, "open": c.open, "high": c.high, "low": c.low, "close": c.close}
        for c in candles(VALLEY)[:end]
    ]


FLAT_CANDLES = [
    {"epoch": 1000 + i * 60, "open": 100.0, "high": 100.5, "low": 99.5, "close": 100.0}
    for i in range(80)
]


class FakeAPI:
    """Stands in for DerivAPI, recording what the trader tried to do."""

    def __init__(self, symbols, candle_data, *, balance=1000.0):
        self._symbols = symbols
        self._candles = candle_data
        self._balance = balance
        self.account = {"loginid": "VRTC1", "currency": "USD", "is_virtual": 1}
        self.buys: list[tuple[str, float]] = []
        self.candle_requests: list[str] = []
        self.contract_requests: list[str] = []
        self._next_contract_id = 1000
        self.settlements: dict[int, dict] = {}

    async def balance(self):
        return {"balance": self._balance, "currency": "USD"}

    async def active_symbols(self):
        return self._symbols

    async def candles(self, symbol, granularity, count):
        self.candle_requests.append(symbol)
        return self._candles

    async def contracts_for(self, symbol, currency):
        self.contract_requests.append(symbol)
        return {
            "available": [
                {
                    "contract_type": "CALL",
                    "contract_category": "callput",
                    "start_type": "spot",
                    "barrier_category": "euro_atm",
                    "min_contract_duration": "1m",
                    "max_contract_duration": "1d",
                },
                {
                    "contract_type": "PUT",
                    "contract_category": "callput",
                    "start_type": "spot",
                    "barrier_category": "euro_atm",
                    "min_contract_duration": "1m",
                    "max_contract_duration": "1d",
                },
            ]
        }

    async def proposal(self, request):
        self._last_proposal = request
        return {"id": "prop-1", "ask_price": request["amount"], "payout": request["amount"] * 1.85}

    async def buy(self, proposal_id, max_price):
        self._next_contract_id += 1
        self.buys.append((self._last_proposal["symbol"], max_price))
        return {"contract_id": self._next_contract_id, "buy_price": max_price}

    async def open_contract(self, contract_id):
        return self.settlements.get(contract_id, {"is_sold": 0})


def crypto(name):
    return {
        "symbol": name,
        "display_name": name,
        "market": "cryptocurrency",
        "submarket": "non_stable_coin",
        "exchange_is_open": 1,
        "is_trading_suspended": 0,
    }


def forex(name):
    return {**crypto(name), "market": "forex", "submarket": "major_pairs"}


def build(tmp_path, universe, candle_data, **overrides):
    config = make_config(
        min_separation_atr=0.0,
        kill_switch_file=str(tmp_path / "KILL"),
        state_file=str(tmp_path / "state.json"),
        journal_file=str(tmp_path / "trades.jsonl"),
        **overrides,
    )
    store = StateStore(config.state_file, config.journal_file)
    trader = Trader(config, store)
    trader.api = FakeAPI(universe, candle_data)
    trader.currency = "USD"
    return trader


def run_cycle(trader):
    asyncio.run(trader._cycle())


class TestHappyPath:
    def test_a_signal_results_in_a_buy(self, tmp_path):
        trader = build(tmp_path, [crypto("cryBTCUSD")], signalling_candles())
        run_cycle(trader)
        assert len(trader.api.buys) == 1
        assert trader.api.buys[0][0] == "cryBTCUSD"
        assert len(trader.open_trades) == 1
        assert trader.store.daily.trades_opened == 1

    def test_no_signal_means_no_buy(self, tmp_path):
        trader = build(tmp_path, [crypto("cryBTCUSD")], FLAT_CANDLES)
        run_cycle(trader)
        assert trader.api.buys == []

    def test_dry_run_never_buys(self, tmp_path):
        trader = build(tmp_path, [crypto("cryBTCUSD")], signalling_candles(), dry_run=True)
        run_cycle(trader)
        assert trader.api.buys == []
        assert trader.open_trades == {}


class TestCryptoOnly:
    def test_forex_symbols_are_never_requested_or_bought(self, tmp_path):
        symbols = [crypto("cryBTCUSD"), forex("frxEURUSD"), forex("frxGBPUSD")]
        trader = build(tmp_path, symbols, signalling_candles())
        run_cycle(trader)
        assert trader.api.candle_requests == ["cryBTCUSD"]
        assert trader.api.contract_requests == ["cryBTCUSD"]
        assert [symbol for symbol, _ in trader.api.buys] == ["cryBTCUSD"]

    def test_a_universe_with_no_crypto_trades_nothing(self, tmp_path):
        trader = build(tmp_path, [forex("frxEURUSD")], signalling_candles())
        run_cycle(trader)
        assert trader.api.candle_requests == []
        assert trader.api.buys == []

    def test_configured_forex_symbol_is_ignored(self, tmp_path):
        symbols = [crypto("cryBTCUSD"), forex("frxEURUSD")]
        trader = build(tmp_path, symbols, signalling_candles(), symbols=("frxEURUSD",))
        run_cycle(trader)
        assert trader.api.buys == []


class TestRiskIntegration:
    def test_kill_switch_stops_the_cycle(self, tmp_path):
        trader = build(tmp_path, [crypto("cryBTCUSD")], signalling_candles())
        open(trader.config.kill_switch_file, "w").close()
        run_cycle(trader)
        assert trader.api.buys == []

    def test_halted_day_stops_the_cycle(self, tmp_path):
        trader = build(tmp_path, [crypto("cryBTCUSD")], signalling_candles())
        trader.store.halt("loss limit")
        run_cycle(trader)
        assert trader.api.buys == []

    def test_max_open_trades_is_respected_across_symbols(self, tmp_path):
        symbols = [crypto("cryBTCUSD"), crypto("cryETHUSD"), crypto("cryLTCUSD")]
        trader = build(tmp_path, symbols, signalling_candles(), max_open_trades=2)
        run_cycle(trader)
        assert len(trader.api.buys) == 2

    def test_cooldown_prevents_a_repeat_buy_next_cycle(self, tmp_path):
        trader = build(tmp_path, [crypto("cryBTCUSD")], signalling_candles(), symbol_cooldown=3600)
        run_cycle(trader)
        trader.open_trades.clear()  # pretend it settled
        run_cycle(trader)
        assert len(trader.api.buys) == 1

    def test_stake_is_capped_by_the_balance_fraction(self, tmp_path):
        trader = build(
            tmp_path, [crypto("cryBTCUSD")], signalling_candles(), stake=500.0, max_stake_fraction=0.01
        )
        run_cycle(trader)
        assert trader.api.buys[0][1] == pytest.approx(10.0)  # 1% of 1000


class TestSettlement:
    def test_a_sold_contract_is_recorded_and_closed_out(self, tmp_path):
        trader = build(tmp_path, [crypto("cryBTCUSD")], signalling_candles())
        run_cycle(trader)
        contract_id = next(iter(trader.open_trades))

        trader.api.settlements[contract_id] = {
            "is_sold": 1,
            "profit": 0.85,
            "status": "won",
            "sell_price": 1.85,
        }
        asyncio.run(trader._settle_open_trades())

        assert trader.open_trades == {}
        assert trader.store.daily.wins == 1
        assert trader.store.daily.realized_pnl == pytest.approx(0.85)

    def test_a_loss_that_breaches_the_limit_halts_the_bot(self, tmp_path):
        trader = build(
            tmp_path, [crypto("cryBTCUSD")], signalling_candles(), daily_loss_limit=1.0
        )
        run_cycle(trader)
        contract_id = next(iter(trader.open_trades))
        trader.api.settlements[contract_id] = {
            "is_sold": 1,
            "profit": -1.0,
            "status": "lost",
            "sell_price": 0.0,
        }
        run_cycle(trader)  # settles, then refreshes limits
        assert trader.store.daily.halted
        assert "loss limit" in trader.store.daily.halt_reason
