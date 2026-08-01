#!/usr/bin/env python3
r"""Read trading signals from a Telegram group and (optionally) trade them.

    pip install telethon
    .\.venv\Scripts\python.exe signal_copier.py --list-chats     # find the group
    .\.venv\Scripts\python.exe signal_copier.py                 # PAPER mode
    .\.venv\Scripts\python.exe signal_copier.py --live           # place real orders
    .\.venv\Scripts\python.exe signal_copier.py --report         # the group's record

DEFAULT IS PAPER MODE, and that is the point. It logs every signal and
records what it would have done, so that after a few weeks you can answer
the only question that matters: is this group actually profitable? Most
are not. Measure first, trade second.

Setup:
  1. Get api_id and api_hash from https://my.telegram.org (Apps).
  2. Put them in .env as TG_API_ID and TG_API_HASH.
  3. Run --list-chats and copy the group id into SIGNAL_CHAT_ID in .env.

Note this signs in as YOUR Telegram account (a session file is created,
which grants full access to your Telegram — keep it private, it is
git-ignored). Trades still pass through the bot's own risk limits.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from fmsbot.config import KNOWN_BROKERS, Settings
from fmsbot.signals import broker_symbol, parse_signal

LOG_PATH = Path("signal_log.jsonl")


def log_event(record: dict) -> None:
    record["ts"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def load_log() -> list[dict]:
    if not LOG_PATH.is_file():
        return []
    out = []
    for line in LOG_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except ValueError:
                continue
    return out


# ----------------------------------------------------------------------
# reporting
# ----------------------------------------------------------------------

def report() -> int:
    events = load_log()
    signals = [e for e in events if e.get("kind") == "signal"]
    if not signals:
        print("No signals logged yet. Run the copier in paper mode for a while first.")
        return 0

    tradeable = [s for s in signals if s.get("tradeable")]
    skipped = len(signals) - len(tradeable)
    placed = [e for e in events if e.get("kind") == "order"]

    print("=" * 66)
    print("SIGNAL GROUP REPORT")
    print("=" * 66)
    first, last = signals[0]["ts"][:10], signals[-1]["ts"][:10]
    print(f"  period            : {first} .. {last}")
    print(f"  messages parsed   : {len(signals)} signals detected")
    print(f"  tradeable         : {len(tradeable)}  (had both SL and TP)")
    print(f"  skipped           : {skipped}  (missing levels / unmapped symbol)")
    print(f"  orders placed     : {len(placed)}")

    by_symbol: dict[str, int] = {}
    for s in tradeable:
        by_symbol[s["symbol"]] = by_symbol.get(s["symbol"], 0) + 1
    if by_symbol:
        print("\n  signals by symbol:")
        for sym, n in sorted(by_symbol.items(), key=lambda x: -x[1]):
            print(f"     {sym:10} {n}")

    rr = [s["rr"] for s in tradeable if s.get("rr")]
    if rr:
        avg = sum(rr) / len(rr)
        print(f"\n  average reward:risk as posted : {avg:.2f}")
        if avg < 1.0:
            print("     Below 1.0 — this group needs a win rate above "
                  f"{100 / (1 + avg):.0f}% just to break even before costs.")
        else:
            print(f"     Needs a win rate above {100 / (1 + avg):.0f}% to break even "
                  "before costs.")

    print("\n  NOTE: this reports what the group POSTED, not what it earned.")
    print("  For real outcomes, compare against your account history after")
    print("  running paper mode for several weeks. A group that posts 1:3 RR")
    print("  but wins 20% of the time is a losing group.")
    return 0


# ----------------------------------------------------------------------
# telegram
# ----------------------------------------------------------------------

def require_telethon():
    try:
        from telethon import TelegramClient, events  # noqa: PLC0415
    except ImportError:
        sys.exit("Telethon is not installed. Run:  pip install telethon")
    return TelegramClient, events


async def list_chats(api_id: int, api_hash: str) -> None:
    TelegramClient, _ = require_telethon()
    async with TelegramClient("signal_session", api_id, api_hash) as client:
        print("Your groups and channels:\n")
        async for dialog in client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                print(f"  {dialog.id:>16}   {dialog.name}")
        print("\nCopy the id of your signal group into SIGNAL_CHAT_ID in .env")


async def run_copier(settings: Settings, chat_id: int, api_id: int, api_hash: str,
                     live: bool, max_signals_per_day: int) -> None:
    TelegramClient, events = require_telethon()

    broker = None
    available: list[str] | None = None
    if live:
        from fmsbot.broker import build_broker
        from fmsbot.risk import RiskManager
        from symbols import list_symbols
        broker = build_broker(settings)
        broker.connect()
        risk = RiskManager(settings)
        available = [name for name, _ in list_symbols(settings.broker, broker)]
        print(f"LIVE MODE — orders will be placed on account {settings.mt5_login} "
              f"at {settings.fixed_lot or str(settings.risk_pct) + '%'} per trade.")
    else:
        suffix = KNOWN_BROKERS.get(settings.active_broker, {}).get("suffix", "")
        print("PAPER MODE — signals are logged, no orders are placed.")

    placed_today = {"day": datetime.now(timezone.utc).date(), "n": 0}
    client = TelegramClient("signal_session", api_id, api_hash)

    @client.on(events.NewMessage(chats=chat_id))
    async def handler(event):  # noqa: ANN001
        text = event.message.message or ""
        sig = parse_signal(text)
        if sig is None:
            return

        rr = None
        if sig.entry and sig.sl and sig.tp:
            risk_d = abs(sig.entry - sig.sl)
            reward_d = abs(sig.tp - sig.entry)
            rr = round(reward_d / risk_d, 2) if risk_d > 0 else None

        record = {
            "kind": "signal", "side": sig.side, "symbol": sig.symbol,
            "entry": sig.entry, "sl": sig.sl, "tp": sig.tp, "rr": rr,
            "tradeable": sig.tradeable, "warnings": sig.warnings,
            "raw": sig.raw[:400],
        }
        log_event(record)
        print(f"\n[{datetime.now().strftime('%H:%M:%S')}] {sig}"
              + (f"  RR {rr}" if rr else ""))
        for w in sig.warnings:
            print(f"    warning: {w}")

        if not sig.tradeable:
            print("    -> not traded (needs both SL and TP)")
            return
        if sig.warnings:
            print("    -> not traded (levels look wrong)")
            return
        if not live:
            print("    -> paper mode, logged only")
            return

        if placed_today["day"] != datetime.now(timezone.utc).date():
            placed_today.update(day=datetime.now(timezone.utc).date(), n=0)
        if placed_today["n"] >= max_signals_per_day:
            print(f"    -> blocked: daily signal cap ({max_signals_per_day}) reached")
            return

        symbol = broker_symbol(sig.symbol, "", available)
        if symbol is None:
            print(f"    -> blocked: {sig.symbol} not offered on this account")
            log_event({"kind": "blocked", "reason": "symbol unavailable",
                       "symbol": sig.symbol})
            return

        balance, equity = broker.balance(), broker.equity()
        positions = broker.positions()
        same = [p for p in positions if p.symbol.lower() == symbol.lower()]
        ok, reason = risk.can_enter(symbol, balance, equity, len(positions), len(same))
        if not ok:
            print(f"    -> blocked by risk manager: {reason}")
            log_event({"kind": "blocked", "reason": reason, "symbol": symbol})
            return

        try:
            if settings.fixed_lot > 0:
                volume = broker.volume_from_lots(symbol, settings.fixed_lot)
            else:
                sl_distance = abs((sig.entry or sig.sl) - sig.sl)
                volume = broker.volume_for_risk(
                    symbol, sl_distance, risk.risk_amount(balance))
            receipt = broker.market_order(symbol, sig.side, volume,
                                          sig.sl, sig.tp, comment="signal copy")
        except Exception as exc:
            print(f"    -> order failed: {exc}")
            log_event({"kind": "error", "error": str(exc), "symbol": symbol})
            return

        risk.record_entry(symbol)
        placed_today["n"] += 1
        print(f"    -> ORDER PLACED #{receipt.ticket} {receipt.volume} lots "
              f"@ {receipt.price}")
        log_event({"kind": "order", "ticket": receipt.ticket, "symbol": symbol,
                   "side": sig.side, "volume": receipt.volume,
                   "price": receipt.price, "sl": receipt.sl, "tp": receipt.tp})

    await client.start()
    me = await client.get_me()
    entity = await client.get_entity(chat_id)
    print(f"Listening as {me.first_name} on '{getattr(entity, 'title', chat_id)}'.")
    print("Signals are appended to signal_log.jsonl — run --report any time.")
    print("Ctrl+C to stop.\n")
    try:
        await client.run_until_disconnected()
    finally:
        if broker:
            broker.disconnect()


def main() -> int:
    p = argparse.ArgumentParser(description="Copy trading signals from Telegram")
    p.add_argument("--live", action="store_true",
                   help="place real orders (default: paper mode, log only)")
    p.add_argument("--list-chats", action="store_true", help="show your groups and ids")
    p.add_argument("--report", action="store_true", help="summarise logged signals")
    p.add_argument("--chat-id", type=int, help="override SIGNAL_CHAT_ID")
    p.add_argument("--max-per-day", type=int, default=5,
                   help="cap orders from signals per day (default 5)")
    args = p.parse_args()

    if args.report:
        return report()

    settings = Settings.load()
    api_id = int(os.environ.get("TG_API_ID", "0") or 0)
    api_hash = os.environ.get("TG_API_HASH", "").strip()
    if not api_id or not api_hash:
        print("TG_API_ID / TG_API_HASH missing from .env.", file=sys.stderr)
        print("Get them from https://my.telegram.org -> API development tools.",
              file=sys.stderr)
        return 2

    if args.list_chats:
        asyncio.run(list_chats(api_id, api_hash))
        return 0

    chat_id = args.chat_id or int(os.environ.get("SIGNAL_CHAT_ID", "0") or 0)
    if not chat_id:
        print("SIGNAL_CHAT_ID not set. Run with --list-chats to find it.",
              file=sys.stderr)
        return 2

    if args.live:
        problems = settings.validate()
        if problems:
            for msg in problems:
                print(f"CONFIG ERROR: {msg}", file=sys.stderr)
            return 2
        print()
        print("*** LIVE SIGNAL COPYING ***")
        print("Orders will be placed from messages written by other people.")
        print(f"Account {settings.mt5_login} ({settings.mt5_server})")
        print(f"Size {settings.fixed_lot or str(settings.risk_pct) + '%'} per trade, "
              f"max {args.max_per_day} signals/day")
        if input("Type 'yes' to continue: ").strip().lower() != "yes":
            print("Aborted.")
            return 1

    asyncio.run(run_copier(settings, chat_id, api_id, api_hash,
                           args.live, args.max_per_day))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
