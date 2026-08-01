"""Preflight check: verify a token and configuration end to end.

    python -m deriv_bot.check

Connects, authorizes, inspects the account, lists the crypto universe, pulls
candles, runs the strategy over them, and prices a real contract — then reports
whether the bot is ready to run.

**It never buys anything.** It requests a `proposal`, which is a price quote,
and stops there. Running it costs nothing and risks nothing.

One output is worth the run on its own: the **real payout ratio** Deriv quotes
for your symbol and duration. That is the single largest assumption in any
backtest, and this is the only way to measure it rather than guess.
"""

from __future__ import annotations

import asyncio
import logging
import sys
from datetime import datetime, timezone

from .api import ConnectionLost, DerivAPI, DerivError, silence_background_errors
from .config import Config, ConfigError
from .indicators import Candle
from .market import find_contract, is_crypto, resolve_duration, select_symbols
from .strategy import evaluate

log = logging.getLogger(__name__)

GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
BOLD = "\033[1m"
RESET = "\033[0m"


class Report:
    """Collects pass/warn/fail results and prints them as they happen."""

    def __init__(self, colour: bool = True) -> None:
        self.colour = colour
        self.failures: list[str] = []
        self.warnings: list[str] = []

    def _paint(self, text: str, code: str) -> str:
        return f"{code}{text}{RESET}" if self.colour else text

    def heading(self, text: str) -> None:
        print(f"\n{self._paint(text, BOLD)}")
        print("-" * 62)

    def ok(self, label: str, detail: str = "") -> None:
        mark = self._paint("PASS", GREEN)
        print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))

    def warn(self, label: str, detail: str = "") -> None:
        mark = self._paint("WARN", YELLOW)
        print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))
        self.warnings.append(label)

    def fail(self, label: str, detail: str = "") -> None:
        mark = self._paint("FAIL", RED)
        print(f"  [{mark}] {label}" + (f"  {detail}" if detail else ""))
        self.failures.append(label)

    def note(self, text: str) -> None:
        print(f"         {text}")


async def run_checks(config: Config, report: Report) -> None:
    silence_background_errors()
    api = DerivAPI(config)

    # -- connection and authorization ------------------------------------
    report.heading("1. Connection")
    try:
        account = await api.connect()
    except DerivError as exc:
        if exc.code in {"InvalidToken", "AuthorizationRequired"}:
            report.fail("Token rejected by Deriv", exc.message)
            report.note("Create a new token: Deriv > Settings > API token")
            report.note("Scopes needed: Read and Trade. Not Payments, not Admin.")
        else:
            report.fail(f"Deriv returned an error ({exc.code})", exc.message)
        return
    except (ConnectionLost, OSError, asyncio.TimeoutError) as exc:
        report.fail("Could not reach Deriv", str(exc))
        report.note(f"Endpoint: {config.endpoint}")
        if "proxy" in str(exc).lower():
            report.note("A proxy rejected the connection. If you are on a")
            report.note("corporate or restricted network, WebSocket traffic to")
            report.note("Deriv may be blocked. Try a different network.")
        else:
            report.note("Check your internet connection and any firewall or proxy.")
        return

    report.ok("Connected", config.endpoint)
    report.ok("Token accepted", f"app_id={config.app_id}")

    try:
        await _account_checks(api, config, account, report)
        await _universe_checks(api, config, report)
    finally:
        await api.close()


async def _account_checks(api: DerivAPI, config: Config, account: dict, report: Report) -> None:
    report.heading("2. Account")

    loginid = str(account.get("loginid", "unknown"))
    currency = config.currency or str(account.get("currency", "USD"))
    is_virtual = bool(account.get("is_virtual", 0))

    if is_virtual:
        report.ok("Virtual (demo) account", loginid)
        report.note("No real funds at risk. This is the right place to start.")
    elif not config.allow_real_money:
        report.fail("REAL-money account, but real-money trading is not enabled", loginid)
        report.note("The bot will refuse to start. That is deliberate.")
        report.note("Either use a demo-account token, or set DERIV_ALLOW_REAL_MONEY=true")
        report.note("if you genuinely intend to trade real money.")
    else:
        report.warn("REAL-money account, and real-money trading IS enabled", loginid)
        report.note("Live funds are at risk every time you start the bot.")
        report.note(f"Your daily loss limit is {config.daily_loss_limit:.2f} {currency}.")

    try:
        balance_info = await api.balance()
        balance = float(balance_info.get("balance", 0.0))
        report.ok("Balance readable", f"{balance:,.2f} {currency}")

        cap = balance * config.max_stake_fraction
        if balance <= 0:
            report.fail("Balance is zero", "nothing can be traded")
        elif cap < config.stake:
            report.warn(
                f"Stake will be reduced to {cap:.2f}",
                f"({config.max_stake_fraction:.0%} cap on a {balance:,.2f} balance)",
            )
        else:
            report.ok("Stake affordable", f"{config.stake:.2f} {currency} per trade")

        if config.daily_loss_limit > balance:
            report.warn(
                "Daily loss limit exceeds your balance",
                f"{config.daily_loss_limit:.2f} > {balance:,.2f}",
            )
            report.note("The limit cannot protect you — lower DAILY_LOSS_LIMIT.")
    except DerivError as exc:
        report.fail("Could not read balance", str(exc))


async def _universe_checks(api: DerivAPI, config: Config, report: Report) -> None:
    report.heading("3. Crypto universe")

    try:
        raw_symbols = await api.active_symbols()
    except DerivError as exc:
        report.fail("Could not list markets", str(exc))
        return

    crypto_total = sum(1 for entry in raw_symbols if is_crypto(entry))
    universe = select_symbols(raw_symbols, config)

    report.ok(f"{crypto_total} cryptocurrency symbols offered by Deriv")
    non_crypto = len(raw_symbols) - crypto_total
    report.ok(f"{non_crypto} non-crypto symbols excluded", "forex, indices, synthetics")

    if not universe:
        report.fail("No tradable crypto symbols after filtering")
        if config.symbols:
            report.note(f"DERIV_SYMBOLS is set to: {', '.join(config.symbols)}")
            report.note("Check for typos, or clear it to trade all open crypto.")
        return

    report.ok(f"{len(universe)} symbols selected", ", ".join(s.symbol for s in universe))

    # -- data and strategy ------------------------------------------------
    report.heading("4. Market data and strategy")
    symbol = universe[0].symbol

    try:
        raw_candles = await api.candles(symbol, config.candle_granularity, config.candle_count)
    except DerivError as exc:
        report.fail(f"Could not fetch candles for {symbol}", str(exc))
        return

    if not raw_candles:
        report.fail(f"No candle data returned for {symbol}")
        return

    candles = [Candle.from_api(entry) for entry in raw_candles]
    report.ok(
        f"Fetched {len(candles)} candles for {symbol}",
        f"{config.candle_granularity}s each",
    )

    age = datetime.now(timezone.utc).timestamp() - candles[-1].epoch
    if age > config.candle_granularity * 5:
        report.warn("Latest candle looks stale", f"{age / 60:.0f} minutes old")
    else:
        report.ok("Data is current", f"latest candle {age:.0f}s old")

    needed = config.ema_slow + max(config.rsi_period, config.atr_period) + 2
    if len(candles) < needed:
        report.fail(
            "Not enough candles to warm up the indicators", f"have {len(candles)}, need {needed}"
        )
        return
    report.ok("Enough history to warm up indicators", f"{len(candles)} >= {needed}")

    signal = evaluate(symbol, candles, config)
    if signal.is_trade:
        report.ok(f"Strategy says {signal.direction} right now", signal.reason)
    else:
        report.ok("Strategy sees no trade right now", signal.reason)
        report.note("That is normal — signals are infrequent by design.")

    # -- contract pricing --------------------------------------------------
    report.heading("5. Contract pricing")
    await _pricing_checks(api, config, report, symbol)


async def _pricing_checks(api: DerivAPI, config: Config, report: Report, symbol: str) -> None:
    currency = config.currency or "USD"
    try:
        contracts = await api.contracts_for(symbol, currency)
    except DerivError as exc:
        report.fail(f"Could not list contracts for {symbol}", str(exc))
        return

    entry = find_contract(contracts, "CALL")
    if entry is None:
        report.fail(f"No spot Rise/Fall contract offered for {symbol}")
        report.note("The bot cannot trade this symbol with its current settings.")
        return

    report.ok("Rise/Fall contract available", symbol)

    amount, unit = resolve_duration(entry, config)
    requested = f"{config.trade_duration}{config.trade_duration_unit}"
    if (amount, unit) != (config.trade_duration, config.trade_duration_unit):
        report.warn(
            f"Duration adjusted to {amount}{unit}",
            f"you asked for {requested}; Deriv allows "
            f"{entry.get('min_contract_duration')}-{entry.get('max_contract_duration')}",
        )
    else:
        report.ok("Duration accepted", f"{amount}{unit}")

    try:
        proposal = await api.proposal(
            {
                "symbol": symbol,
                "contract_type": "CALL",
                "amount": config.stake,
                "basis": "stake",
                "currency": currency,
                "duration": amount,
                "duration_unit": unit,
            }
        )
    except DerivError as exc:
        report.fail("Could not price a contract", str(exc))
        if exc.code == "PermissionDenied":
            report.note("Your token may be missing the 'Trade' scope.")
        return

    ask = float(proposal.get("ask_price", 0.0))
    payout = float(proposal.get("payout", 0.0))
    report.ok("Priced a real contract", f"stake {ask:.2f}, payout {payout:.2f} {currency}")
    report.note("(This was a price quote only. Nothing was bought.)")

    if ask > 0 and payout > 0:
        ratio = (payout - ask) / ask
        breakeven = 100.0 / (1.0 + ratio)
        print()
        report.ok(f"Real payout ratio: {ratio:.3f}", f"win returns {ratio:.3f}x your stake")
        report.note(f"You must win more than {breakeven:.1f}% of trades to break even.")
        report.note("Use this measured ratio in your backtests:")
        report.note(f"  python -m deriv_bot.backtest --days 30 --payout-ratio {ratio:.3f}")


def summarise(config: Config, report: Report) -> int:
    report.heading("Summary")

    if report.failures:
        print(f"  {report._paint('NOT READY', RED)} — {len(report.failures)} problem(s) to fix:")
        for item in report.failures:
            print(f"    - {item}")
        print("\n  Fix these, then run this check again.")
        return 1

    if report.warnings:
        print(f"  {report._paint('READY, with warnings', YELLOW)}:")
        for item in report.warnings:
            print(f"    - {item}")
    else:
        print(f"  {report._paint('READY', GREEN)} — everything checks out.")

    print("\n  Suggested next steps, in order:")
    print("    1. Backtest, using the measured payout ratio printed above:")
    print("         python -m deriv_bot.backtest --days 30 --save-candles btc.json")
    print("    2. Dry run, to watch it decide without trading:")
    print("         DERIV_DRY_RUN=true python -m deriv_bot")
    print("    3. Run it on demo, and leave it long enough to see losing days.")
    if not config.allow_real_money:
        print("\n  Real-money trading is OFF. It stays off until you set")
        print("  DERIV_ALLOW_REAL_MONEY=true yourself.")
    return 0


def main(argv: list[str] | None = None) -> int:
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m deriv_bot.check",
        description="Verify your Deriv token and configuration. Never places a trade.",
    )
    parser.add_argument("--no-colour", action="store_true", help="disable coloured output")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARNING, format="%(levelname)-7s %(message)s")
    logging.getLogger("websockets").setLevel(logging.ERROR)

    try:
        from .__main__ import _load_dotenv

        _load_dotenv()
        config = Config.from_env()
    except ConfigError as exc:
        print(f"\n  Configuration error: {exc}")
        print("\n  Copy .env.example to .env and fill in DERIV_APP_ID and")
        print("  DERIV_API_TOKEN, then run this again:")
        print("      cp .env.example .env")
        return 2

    colour = not args.no_colour and sys.stdout.isatty()
    report = Report(colour=colour)

    print("\n" + "=" * 62)
    print("  DERIV CRYPTO BOT — PREFLIGHT CHECK")
    print("=" * 62)
    print("  Verifies your token and settings. Places no trades.")

    try:
        asyncio.run(run_checks(config, report))
    except KeyboardInterrupt:
        print("\n  Interrupted.")
        return 1

    result = summarise(config, report)
    print("=" * 62 + "\n")
    return result


if __name__ == "__main__":
    raise SystemExit(main())
