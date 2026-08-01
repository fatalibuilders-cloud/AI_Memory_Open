"""Entrypoint: `python -m deriv_bot`.

Loads configuration, wires up logging and signal handling, then hands control
to the trader. SIGINT and SIGTERM ask the trader to wind down at the next safe
point rather than killing it mid-trade, so a `docker stop` or a systemd restart
never orphans a position the bot has not recorded.
"""

from __future__ import annotations

import asyncio
import logging
import os
import signal
import sys

from .config import Config, ConfigError
from .state import StateStore
from .trader import Trader, UnsafeAccount

log = logging.getLogger("deriv_bot")


def _load_dotenv() -> None:
    """Load a local .env if python-dotenv is installed. Optional by design:
    in production the environment is usually supplied by systemd or Docker."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    for candidate in (".env", os.path.join(os.path.dirname(__file__), "..", ".env")):
        if os.path.exists(candidate):
            load_dotenv(candidate, override=False)
            return


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S%z",
        stream=sys.stdout,
    )
    # The websockets library logs every frame at DEBUG, which drowns the bot's
    # own output without adding much.
    logging.getLogger("websockets").setLevel(logging.WARNING)


async def _run(config: Config) -> int:
    store = StateStore(config.state_file, config.journal_file)
    trader = Trader(config, store)

    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, trader.request_stop)
        except (NotImplementedError, RuntimeError):  # pragma: no cover - non-POSIX
            pass

    log.info("deriv-crypto-bot starting — cryptocurrency only, running continuously")
    log.info(
        "limits: stake=%.2f max_open=%d max_trades_per_day=%d daily_loss_limit=%.2f dry_run=%s",
        config.stake,
        config.max_open_trades,
        config.max_trades_per_day,
        config.daily_loss_limit,
        config.dry_run,
    )
    if store.daily.halted:
        log.warning("resuming a halted day (%s): %s", store.daily.day, store.daily.halt_reason)

    try:
        await trader.run()
    except UnsafeAccount as exc:
        log.error("REFUSING TO START: %s", exc)
        return 2
    except Exception as exc:  # noqa: BLE001 - top-level guard, reported below
        log.exception("fatal error: %s", exc)
        return 1
    return 0


def main() -> int:
    _load_dotenv()
    try:
        config = Config.from_env()
    except ConfigError as exc:
        _setup_logging("INFO")
        log.error("configuration error: %s", exc)
        log.error("copy .env.example to .env and fill it in, then try again")
        return 2

    _setup_logging(config.log_level)
    try:
        return asyncio.run(_run(config))
    except KeyboardInterrupt:
        log.info("interrupted")
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
