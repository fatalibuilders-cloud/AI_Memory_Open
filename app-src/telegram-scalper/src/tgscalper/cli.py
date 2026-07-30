"""Command line interface.

    tgscalper doctor            check config, credentials and broker connectivity
    tgscalper chats             list the chats this account can see, with their ids
    tgscalper admins <chat>     list the admin ids of one chat
    tgscalper parse <file>      parse messages from a file, no broker involved
    tgscalper dryrun <file>     run those messages through the paper broker
    tgscalper run               start the live listener
    tgscalper report            summarise the journal
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional

from . import config as config_module
from .brokers import build_broker
from .brokers.paper import PaperBroker
from .engine import Engine
from .journal import Journal
from .models import MessageRef
from .parser import parse

log = logging.getLogger("tgscalper")


def setup_logging(level: str = "INFO", log_file: Optional[str] = None) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stdout)]
    if log_file:
        path = Path(log_file)
        path.parent.mkdir(parents=True, exist_ok=True)
        handlers.append(logging.FileHandler(path, encoding="utf-8"))
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=handlers,
        force=True,
    )
    # Telethon is chatty at INFO and drowns out our own lines.
    logging.getLogger("telethon").setLevel(logging.WARNING)


# Where the .env actually came from, so `doctor` can report it. Silence about
# this is what makes a missing or misplaced .env so hard to diagnose.
ENV_SOURCE: str = "not loaded"


def load_env(explicit: Optional[str] = None) -> None:
    """Load .env, looking in the obvious places and saying which one won.

    `load_dotenv()` with no arguments walks up from *this file's* directory,
    not the working directory, so a .env sitting right next to the user is
    quietly ignored. Both locations are checked here, cwd first.
    """
    global ENV_SOURCE
    try:
        from dotenv import load_dotenv
    except ImportError:
        ENV_SOURCE = (
            "python-dotenv is NOT installed, so .env was ignored entirely "
            "(fix: pip install python-dotenv)"
        )
        return

    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    candidates.append(Path.cwd() / ".env")
    # The project root, two levels above src/tgscalper/cli.py.
    candidates.append(Path(__file__).resolve().parents[2] / ".env")

    for candidate in candidates:
        if candidate.is_file():
            load_dotenv(candidate, override=False)
            ENV_SOURCE = str(candidate)
            return
    ENV_SOURCE = f"no .env found (looked in {', '.join(str(c) for c in candidates)})"


def load_config(path: str, env_path: Optional[str] = None) -> config_module.Config:
    load_env(env_path)
    return config_module.load(path)


def _diagnose_env_file() -> list[str]:
    """Explain *why* the credentials did not load, rather than just that they didn't.

    Nearly every report of this comes down to one of three things, none of
    which is obvious from the outside: the editor appended .txt to the
    filename, the values were pasted with quotes, or the file is somewhere
    other than the folder the bot runs from.
    """
    notes: list[str] = []
    cwd = Path.cwd()
    # Inspect whatever load_env actually resolved; fall back to the cwd copy.
    env_path = Path(ENV_SOURCE) if Path(ENV_SOURCE).is_file() else cwd / ".env"

    if not env_path.exists():
        notes.append(f"no .env file in {cwd}")
        # Notepad silently appends .txt unless the name is quoted when saving.
        strays = sorted(
            path.name
            for path in cwd.glob(".env*")
            if path.name != ".env" and path.name != ".env.example"
        )
        if strays:
            notes.append(
                f"found {', '.join(strays)} instead — Notepad added an extension. "
                f"Rename it: Rename-Item {strays[0]} .env"
            )
        else:
            notes.append("create it by running: .\\windows\\credentials.ps1")
        return notes

    try:
        text = env_path.read_text(encoding="utf-8-sig")
    except OSError as exc:
        notes.append(f".env exists but could not be read: {exc}")
        return notes

    keys: dict[str, str] = {}
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        keys[key.strip()] = value.strip()

    if "TG_API_ID" not in keys:
        notes.append(f"{env_path} has no TG_API_ID line at all")
    elif not keys["TG_API_ID"]:
        notes.append(f"{env_path} has TG_API_ID but nothing after the '='")
    elif not keys["TG_API_ID"].isdigit():
        notes.append(
            f"TG_API_ID is {keys['TG_API_ID']!r}, which is not a plain number — "
            "remove any quotes or spaces; it should look like TG_API_ID=12345678"
        )
    if not keys.get("TG_API_HASH"):
        notes.append(f"{env_path} has no usable TG_API_HASH value")
    return notes


def _split_messages(raw: str) -> list[str]:
    """Split a fixture file into messages on lines of three or more dashes."""
    blocks = [block.strip() for block in raw.split("\n---")]
    return [block.lstrip("-\n") for block in blocks if block.strip()]


# --- commands ---------------------------------------------------------------


def cmd_doctor(args: argparse.Namespace) -> int:
    problems: list[str] = []
    notes: list[str] = []

    try:
        config = load_config(args.config, getattr(args, "env", None))
    except Exception as exc:
        print(f"config: FAILED — {exc}")
        return 1
    print(f"config: ok ({args.config})")

    print(f"env file: {ENV_SOURCE}")

    telegram = config.telegram
    if not telegram.api_id or not telegram.api_hash:
        problems.append("TG_API_ID / TG_API_HASH not set in .env")
        problems.extend(_diagnose_env_file())
    else:
        print(f"telegram credentials: present (api_id {telegram.api_id})")
    session = Path(f"{config.session_path}.session")
    if session.exists():
        print(f"telegram session: {session} (already logged in)")
    else:
        notes.append(f"no session yet at {session} — run `tgscalper run` once to log in")

    groups = telegram.enabled_groups
    if not groups:
        problems.append("no groups configured under telegram.groups in config.yaml")
    else:
        idle = len(telegram.groups) - len(groups)
        print(
            f"groups enabled: {len(groups)} / {telegram.max_groups}"
            + (f" ({idle} more listed but disabled)" if idle else "")
        )
        for group in groups:
            multiplier = (
                f", size x{group.risk_multiplier}" if group.risk_multiplier != 1.0 else ""
            )
            senders = f"{len(group.senders)} sender(s) allow-listed" if group.senders else "all admins"
            print(f"  - {group.title or group.key} [{group.key}] — {senders}{multiplier}")

    mode = "LIVE" if config.execution.live_enabled else "PAPER"
    print(f"execution mode: {mode}")
    if not config.execution.live_enabled and config.execution.live_block_reason:
        print(f"  reason: {config.execution.live_block_reason}")

    print(
        f"risk: {config.risk.risk_per_trade_pct}% per trade, max {config.risk.max_lot} lots, "
        f"max {config.risk.max_open_trades} open, daily stop {config.risk.max_daily_loss_pct}%"
    )

    try:
        broker = build_broker(config)
        broker.connect()
        account = broker.account_info()
        symbols = broker.available_symbols()
        print(
            f"broker: {broker.name} connected — balance {account.balance:.2f} "
            f"{account.currency}, {len(symbols) or 'n/a'} symbols"
        )
        if symbols:
            from .symbols import SymbolResolver

            resolver = SymbolResolver(
                suffix=config.broker.suffix,
                overrides=config.broker.symbol_overrides,
                aliases=config.aliases,
            )
            resolver.load_available(symbols)
            for probe in ("GOLD", "EURUSD", "US30"):
                resolved = resolver.resolve(probe)
                print(f"  symbol check: {probe} -> {resolved or 'NOT TRADABLE'}")
        broker.close()
    except Exception as exc:
        problems.append(f"broker: {exc}")

    try:
        journal = Journal(config.journal_path)
        journal.close()
        print(f"journal: ok ({config.journal_path})")
    except Exception as exc:
        problems.append(f"journal: {exc}")

    for note in notes:
        print(f"note: {note}")
    for problem in problems:
        print(f"PROBLEM: {problem}")
    return 1 if problems else 0


def cmd_symbols(args: argparse.Namespace) -> int:
    """Show what the broker lists, and what the bot's names resolve to.

    The fastest way to settle suffix/override questions: it prints the
    terminal's own symbol strings rather than what anyone assumes they are.
    """
    from .symbols import SymbolResolver

    config = load_config(args.config, getattr(args, "env", None))
    broker = build_broker(config)
    broker.connect()
    available = broker.available_symbols()

    if not available:
        print(
            f"broker '{broker.name}' does not expose a symbol list "
            "(paper mode accepts anything). Connect the real broker to inspect it."
        )
        broker.close()
        return 0

    if args.search:
        needle = args.search.lower()
        matches = [name for name in available if needle in name.lower()]
        print(f"{len(matches)} of {len(available)} symbols match {args.search!r}:")
        for name in sorted(matches):
            print(f"  {name}")
        broker.close()
        return 0

    resolver = SymbolResolver(
        suffix=config.broker.suffix,
        overrides=config.broker.symbol_overrides,
        aliases=config.aliases,
    )
    resolver.load_available(available)
    print(f"broker lists {len(available)} symbols. How the bot's names map onto them:\n")
    probes = args.probe or [
        "GOLD", "EURUSD", "GBPUSD", "USDJPY", "US30", "NAS100",
        "V75", "V100", "BOOM500", "CRASH1000", "STEPINDEX",
    ]
    unresolved: list[str] = []
    for probe in probes:
        resolved = resolver.resolve(probe)
        print(f"  {probe:<12} -> {resolved or 'NOT TRADABLE on this account'}")
        if not resolved:
            unresolved.append(probe)
    if unresolved:
        print(
            "\nAnything 'NOT TRADABLE' is either absent from your account type or "
            "named differently.\nRun with --search to hunt for it, e.g.:"
            f"\n    tgscalper symbols --search {unresolved[0][:4].lower()}"
            "\nthen set broker.suffix or a broker.symbol_overrides entry."
        )
    broker.close()
    return 0


def cmd_chats(args: argparse.Namespace) -> int:
    config = load_config(args.config, getattr(args, "env", None))

    async def run() -> None:
        from .listener import TelegramListener

        listener = TelegramListener(config, engine=None)  # type: ignore[arg-type]
        await listener.connect()
        print(f"{'id':>16}  {'type':<9}  title")
        async for dialog in listener.client.iter_dialogs():
            entity = dialog.entity
            if dialog.is_user:
                continue
            kind = "channel" if getattr(entity, "broadcast", False) else "group"
            if args.search and args.search.lower() not in (dialog.name or "").lower():
                continue
            print(f"{dialog.id:>16}  {kind:<9}  {dialog.name}")
        await listener.client.disconnect()
        print("\nCopy the ids you want into config.yaml under telegram.groups.")

    asyncio.run(run())
    return 0


def cmd_admins(args: argparse.Namespace) -> int:
    config = load_config(args.config, getattr(args, "env", None))

    async def run() -> None:
        from telethon.tl.types import ChannelParticipantsAdmins

        from .listener import TelegramListener

        listener = TelegramListener(config, engine=None)  # type: ignore[arg-type]
        await listener.connect()
        target: object = int(args.chat) if str(args.chat).lstrip("-").isdigit() else args.chat
        entity = await listener.client.get_entity(target)
        print(f"admins of {getattr(entity, 'title', target)}:")
        if getattr(entity, "broadcast", False):
            print("  (broadcast channel — every post is from an admin already)")
        admins = await listener.client.get_participants(entity, filter=ChannelParticipantsAdmins)
        for admin in admins:
            handle = f"@{admin.username}" if admin.username else "(no username)"
            print(f"  {admin.id:>14}  {handle:<20} {admin.first_name or ''}")
        print("\nPut the ids under that group's `senders:` list to trade only their posts.")
        await listener.client.disconnect()

    asyncio.run(run())
    return 0


def cmd_parse(args: argparse.Namespace) -> int:
    config = load_config(args.config, getattr(args, "env", None))
    raw = Path(args.file).read_text(encoding="utf-8") if args.file != "-" else sys.stdin.read()
    messages = _split_messages(raw)
    accepted = 0
    for index, message in enumerate(messages, start=1):
        result = parse(
            message,
            aliases=config.aliases,
            require_sl=config.execution.require_stop_loss,
        )
        preview = message.replace("\n", " | ")[:70]
        if result.ok and result.signal:
            accepted += 1
            print(f"{index:>3}. TRADE  {preview}\n       -> {result.signal.summary()}")
            for warning in result.warnings:
                print(f"       note: {warning}")
        else:
            print(f"{index:>3}. skip   {preview}\n       -> {result.error}")
    print(f"\n{accepted}/{len(messages)} messages would produce a trade.")
    return 0


def cmd_dryrun(args: argparse.Namespace) -> int:
    config = load_config(args.config, getattr(args, "env", None))
    setup_logging(args.log_level or config.log_level, None)
    # A dry run never touches the real broker, whatever config.yaml says.
    config.execution.live_enabled = False
    config.execution.live_block_reason = "dryrun command forces paper mode"
    if not args.respect_hours:
        # The session window is about when a signal arrives, not about whether it
        # parses. Replaying a file at midnight would otherwise reject everything
        # and tell you nothing. Pass --respect-hours to test that guard itself.
        config.risk.hours.start = "00:00"
        config.risk.hours.end = "23:59"
        config.risk.hours.days = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
        print("(trading-hours guard relaxed for this dry run; use --respect-hours to enforce it)\n")

    raw = Path(args.file).read_text(encoding="utf-8") if args.file != "-" else sys.stdin.read()
    journal_path = (args.journal or ":memory:") if args.ephemeral else (
        args.journal or config.journal_path
    )
    journal = Journal(journal_path)
    broker = PaperBroker(starting_balance=config.execution.paper_balance)
    engine = Engine(config, broker, journal)
    engine.start()

    group = config.telegram.enabled_groups[0] if config.telegram.enabled_groups else None
    for index, message in enumerate(_split_messages(raw), start=1):
        source = MessageRef(
            chat_id=group.id or -1 if group else -1,
            message_id=index,
            chat_title=group.title if group else "dryrun",
        )
        decision = engine.handle(message, source, group)
        verdict = f"placed {decision.placed} order(s)" if decision.accepted else f"skipped: {decision.reason}"
        print(f"{index:>3}. {verdict}")
    account = broker.account_info()
    print(f"\npaper balance {account.balance:.2f}, {len(broker.positions())} position(s) open")
    engine.stop()
    journal.close()
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    config = load_config(args.config, getattr(args, "env", None))
    setup_logging(args.log_level or config.log_level, config.log_file)

    journal = Journal(config.journal_path)
    broker = build_broker(config)
    engine = Engine(config, broker, journal)

    if config.execution.live_enabled:
        log.warning("LIVE TRADING ENABLED — real orders will be placed on %s", config.broker.provider)

    from .listener import TelegramListener

    listener = TelegramListener(config, engine)
    try:
        engine.start()
        asyncio.run(listener.run())
    except KeyboardInterrupt:
        log.info("stopped by user")
    except Exception as exc:
        log.exception("listener stopped: %s", exc)
        journal.record_event("crash", str(exc))
        return 1
    finally:
        engine.stop()
        journal.record_event("stop", "listener shut down")
        journal.close()
    return 0


def cmd_report(args: argparse.Namespace) -> int:
    config = load_config(args.config, getattr(args, "env", None))
    journal = Journal(config.journal_path)
    summary = journal.summary(days=args.days)
    print(f"last {summary['days']} day(s)")
    print(f"  signals traded   : {summary['signals_accepted']}")
    print(f"  messages skipped : {summary['signals_skipped']}")
    print(f"  orders attempted : {summary['orders_attempted']} ({summary['orders_filled']} filled)")
    print(f"  of which live    : {summary['live_orders']}")
    print(f"  recorded P&L     : {summary['recorded_pnl']}")
    reasons = summary["top_skip_reasons"]
    if isinstance(reasons, list) and reasons:
        print("  most common skip reasons:")
        for reason, count in reasons:
            print(f"    {count:>4}x {reason}")
    if args.recent:
        print("\nmost recent messages:")
        for row in journal.recent(args.recent):
            mark = "TRADE" if row["accepted"] else "skip "
            detail = row["reason"] or f"{row['side'] or ''} {row['symbol'] or ''}".strip()
            print(f"  {row['ts']}  {mark}  {row['chat_title'] or '':<20.20} {detail}")
    journal.close()
    return 0


# --- wiring -----------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="tgscalper",
        description="Copy trade signals from your Telegram groups to your broker.",
    )
    parser.add_argument("--config", default="config.yaml", help="path to config.yaml")
    parser.add_argument(
        "--env", default=None, help="path to the .env file (default: ./.env, then the project root)"
    )
    parser.add_argument("--log-level", default=None, help="DEBUG, INFO, WARNING, ERROR")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("doctor", help="check config, credentials and broker").set_defaults(
        func=cmd_doctor
    )

    symbols = sub.add_parser("symbols", help="inspect the broker's symbol names")
    symbols.add_argument("--search", default="", help="list broker symbols containing this text")
    symbols.add_argument(
        "--probe", nargs="*", default=None, help="check specific names, e.g. --probe V75 GOLD"
    )
    symbols.set_defaults(func=cmd_symbols)

    chats = sub.add_parser("chats", help="list chats with their ids")
    chats.add_argument("--search", default="", help="filter by title")
    chats.set_defaults(func=cmd_chats)

    admins = sub.add_parser("admins", help="list the admins of one chat")
    admins.add_argument("chat", help="chat id or @username")
    admins.set_defaults(func=cmd_admins)

    parse_cmd = sub.add_parser("parse", help="parse messages from a file (no broker)")
    parse_cmd.add_argument("file", help="file of messages separated by --- lines, or - for stdin")
    parse_cmd.set_defaults(func=cmd_parse)

    dryrun = sub.add_parser("dryrun", help="run messages through the paper broker")
    dryrun.add_argument("file", help="file of messages separated by --- lines, or - for stdin")
    dryrun.add_argument("--journal", default=None, help="journal path override")
    dryrun.add_argument(
        "--ephemeral", action="store_true", help="use an in-memory journal instead of the real one"
    )
    dryrun.add_argument(
        "--respect-hours",
        action="store_true",
        help="also apply the trading-hours guard (relaxed by default for replays)",
    )
    dryrun.set_defaults(func=cmd_dryrun)

    run = sub.add_parser("run", help="start listening to Telegram")
    run.set_defaults(func=cmd_run)

    report = sub.add_parser("report", help="summarise the journal")
    report.add_argument("--days", type=int, default=7)
    report.add_argument("--recent", type=int, default=10, help="also list N recent messages")
    report.set_defaults(func=cmd_report)

    return parser


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command in {"doctor", "chats", "admins", "parse", "report", "symbols"}:
        setup_logging(args.log_level or "WARNING", None)
    try:
        return int(args.func(args))
    except KeyboardInterrupt:
        return 130
    except Exception as exc:
        log.error("%s: %s", type(exc).__name__, exc)
        if (args.log_level or "").upper() == "DEBUG":
            raise
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
