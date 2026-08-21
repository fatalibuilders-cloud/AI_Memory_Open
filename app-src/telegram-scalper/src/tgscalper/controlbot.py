"""The bot you chat with: /start, /status, /selectgroup, /pause.

Two Telegram connections run side by side, and the split matters:

* the **user client** (listener.py) signs in as you and reads the signal
  groups — the only thing that can, since a bot cannot see a chat it has not
  been added to;
* the **bot client** here is the control panel: it takes your commands and
  reports back.

The bot never reads signals. Point a bot token at this expecting it to watch
your groups and it will sit silent, because that is not a thing bots can do.

Everything is owner-locked. A bot wired to a live trading account that answers
whoever finds it is a liability, so commands from any other user id are
refused and logged.
"""

from __future__ import annotations

import asyncio
import html
import logging
from datetime import datetime, timezone
from typing import Any, Optional

from .config import Config
from .engine import Engine
from .groupstate import GroupSelection, selection_path
from .journal import Journal

log = logging.getLogger(__name__)

MENU = """<b>TeleScalper</b> — signal copier

<b>Watching</b>
/status — mode, balance, open trades
/groups — which groups are being copied
/selectgroup — choose groups (up to {limit})

<b>Control</b>
/pause — stop opening new trades
/resume — start again
/trades — recent decisions
/settings — everything currently in force
/connect — check the broker link

Managing trades already open keeps working while paused, so a
"close" or "SL to BE" from an admin is still followed.

<i>This bot only answers while the copier is running on your PC.
Silence from it means the program has stopped — and while it is
stopped, nothing is being copied.</i>
"""


def _esc(text: object) -> str:
    return html.escape(str(text), quote=False)


class ControlBot:
    def __init__(
        self,
        config: Config,
        engine: Engine,
        journal: Journal,
        listener: Any = None,
    ) -> None:
        self.config = config
        self.engine = engine
        self.journal = journal
        self.listener = listener  # TelegramListener, for enumerating dialogs
        self.client: Any = None
        self.started_at = datetime.now(timezone.utc)
        self._selection = GroupSelection.load(selection_path(config)) or GroupSelection()
        # Cache of the dialog list behind /selectgroup, keyed by a short index
        # because callback payloads are capped at 64 bytes.
        self._dialog_cache: dict[int, tuple[int, str]] = {}

    # --- lifecycle ---

    async def start(self) -> None:
        from telethon import TelegramClient, events  # type: ignore[import-not-found]

        settings = self.config.control_bot
        telegram = self.config.telegram
        if not settings.token:
            raise RuntimeError("TG_BOT_TOKEN is not set; cannot start the control bot")

        # Telethon needs api_id/api_hash even for a bot login — the token
        # authenticates the bot, the pair identifies the client application.
        self.client = TelegramClient(
            str(self.config.session_path) + "-bot", telegram.api_id, telegram.api_hash
        )
        await self.client.start(bot_token=settings.token)
        me = await self.client.get_me()
        log.info("control bot connected as @%s", me.username)

        self.client.add_event_handler(self._on_command, events.NewMessage(pattern=r"^/"))
        self.client.add_event_handler(self._on_callback, events.CallbackQuery())

        if settings.owner_id:
            try:
                greeting = f"<b>Started.</b> Mode: {self._mode()}."
                if not self.engine.broker_ready:
                    greeting += (
                        "\n\n⚠️ <b>But the broker is NOT connected, so nothing "
                        "can be traded:</b>\n"
                        f"<code>{_esc(self.engine.broker_error or 'unavailable')}</code>\n\n"
                        "Open MetaTrader 5, log in, enable Algo Trading, then /connect."
                    )
                else:
                    greeting += " Send /status for details."
                await self.client.send_message(settings.owner_id, greeting, parse_mode="html")
            except Exception as exc:
                log.warning("could not greet the owner: %s", exc)

    async def stop(self) -> None:
        if self.client is not None:
            await self.client.disconnect()

    # --- authorisation ---

    def _authorised(self, user_id: Optional[int]) -> bool:
        owner = self.config.control_bot.owner_id
        return bool(owner and user_id and int(user_id) == int(owner))

    async def _deny(self, event: Any, user_id: Optional[int]) -> None:
        log.warning("refused control-bot command from user id %s", user_id)
        await event.respond(
            "This bot is private.\n\n"
            f"If you are the owner, set <code>control_bot.owner_id: {user_id}</code> "
            "in config.yaml and restart.",
            parse_mode="html",
        )

    # --- command routing ---

    async def _on_command(self, event: Any) -> None:
        user_id = event.sender_id
        if not self._authorised(user_id):
            await self._deny(event, user_id)
            return

        command = (event.raw_text or "").split()[0].lstrip("/").split("@")[0].lower()
        handlers = {
            "start": self._cmd_start,
            "help": self._cmd_start,
            "menu": self._cmd_start,
            "status": self._cmd_status,
            "groups": self._cmd_groups,
            "selectgroup": self._cmd_selectgroup,
            "selectgroups": self._cmd_selectgroup,
            "pause": self._cmd_pause,
            "resume": self._cmd_resume,
            "trades": self._cmd_trades,
            "risk": self._cmd_risk,
            "settings": self._cmd_settings,
            "connect": self._cmd_connect,
            "id": self._cmd_id,
        }
        handler = handlers.get(command)
        if handler is None:
            await event.respond(
                f"Unknown command /{_esc(command)}. Send /help for the list.",
                parse_mode="html",
            )
            return
        try:
            await handler(event)
        except Exception as exc:  # a bad command must not kill the bot
            log.exception("control bot command /%s failed", command)
            await event.respond(f"That failed: {_esc(exc)}", parse_mode="html")

    # --- commands ---

    async def _cmd_start(self, event: Any) -> None:
        await event.respond(
            MENU.format(limit=self.config.telegram.max_groups), parse_mode="html"
        )

    async def _cmd_id(self, event: Any) -> None:
        await event.respond(
            f"Your Telegram user id is <code>{event.sender_id}</code>", parse_mode="html"
        )

    def _mode(self) -> str:
        return "LIVE" if self.engine.broker.is_live else "PAPER"

    async def _cmd_status(self, event: Any) -> None:
        lines = [f"<b>Mode:</b> {self._mode()}"]
        if not self.engine.broker.is_live and self.config.execution.live_block_reason:
            lines.append(f"<i>{_esc(self.config.execution.live_block_reason)}</i>")
        if self.engine.paused:
            lines.append("<b>PAUSED</b> — no new trades will be opened")
        if not self.engine.broker_ready:
            # Lead with this: nothing can trade while it is true, and it is the
            # single most common reason for a bot that looks alive but does
            # nothing.
            lines.append(
                f"\n⚠️ <b>BROKER NOT CONNECTED — no trades can be placed.</b>\n"
                f"<code>{_esc(self.engine.broker_error or 'unavailable')}</code>\n"
                "Open MetaTrader 5, log in, enable Algo Trading, then send /connect.\n"
            )

        try:
            account = await asyncio.to_thread(self.engine.broker.account_info)
            positions = await asyncio.to_thread(self.engine.broker.positions)
            label = {
                "PAPER": "simulated, no broker",
                "DEMO": "demo — virtual money",
                "CONTEST": "contest account",
                "REAL": "⚠️ REAL MONEY",
            }.get(account.trade_mode.upper(), account.trade_mode)
            where = f" {account.login}@{account.server}" if account.login else ""
            lines.append(f"<b>Account:</b> {_esc(label)}{_esc(where)}")
            lines.append(
                f"<b>Balance:</b> {account.balance:,.2f} {account.currency} "
                f"(equity {account.equity:,.2f})"
            )
            floating = sum(position.profit for position in positions)
            lines.append(f"<b>Open:</b> {len(positions)} position(s), P&amp;L {floating:,.2f}")
            for position in positions[:10]:
                lines.append(
                    f"  • {_esc(position.symbol)} {position.side.value} "
                    f"{position.volume} @ {position.open_price} → {position.profit:,.2f}"
                )
        except Exception as exc:
            lines.append(f"<b>Broker:</b> not reachable — {_esc(exc)}")

        groups = self.config.telegram.enabled_groups
        lines.append(f"<b>Groups:</b> {len(groups)} / {self.config.telegram.max_groups}")
        for group in groups:
            lines.append(f"  • {_esc(group.title or group.key)}")

        summary = await asyncio.to_thread(self.journal.summary, 1)
        lines.append(
            f"<b>Today:</b> {summary['signals_accepted']} traded, "
            f"{summary['signals_skipped']} ignored, "
            f"{summary['orders_filled']} order(s) filled"
        )
        uptime = datetime.now(timezone.utc) - self.started_at
        lines.append(f"<b>Uptime:</b> {int(uptime.total_seconds() // 60)} min")
        await event.respond("\n".join(lines), parse_mode="html")

    async def _cmd_groups(self, event: Any) -> None:
        groups = self.config.telegram.enabled_groups
        if not groups:
            await event.respond(
                "No groups selected yet. Send /selectgroup to choose up to "
                f"{self.config.telegram.max_groups}.",
                parse_mode="html",
            )
            return
        lines = [f"<b>Copying {len(groups)} group(s):</b>"]
        for group in groups:
            multiplier = (
                f" — size ×{group.risk_multiplier}" if group.risk_multiplier != 1.0 else ""
            )
            lines.append(f"  • {_esc(group.title or group.key)}{multiplier}")
        lines.append("\nSend /selectgroup to change the selection.")
        await event.respond("\n".join(lines), parse_mode="html")

    async def _cmd_selectgroup(self, event: Any) -> None:
        if self.listener is None or self.listener.client is None:
            await event.respond(
                "The Telegram account is not connected yet, so I cannot list your "
                "groups. Wait a moment and try again.",
                parse_mode="html",
            )
            return

        dialogs = await self._list_dialogs()
        if not dialogs:
            await event.respond("No groups or channels found on this account.")
            return
        await event.respond(
            f"<b>Tap to start or stop copying.</b>\nUp to "
            f"{self.config.telegram.max_groups} at once; ✅ means it is being copied.",
            parse_mode="html",
            buttons=self._group_buttons(dialogs),
        )

    async def _list_dialogs(self) -> list[tuple[int, str]]:
        """Group/channel dialogs on the user account, newest activity first."""
        found: list[tuple[int, str]] = []
        async for dialog in self.listener.client.iter_dialogs(limit=200):
            if dialog.is_user:
                continue
            found.append((int(dialog.id), dialog.name or str(dialog.id)))
        self._dialog_cache = {index: item for index, item in enumerate(found)}
        return found

    def _group_buttons(self, dialogs: list[tuple[int, str]]) -> list[list[Any]]:
        from telethon import Button  # type: ignore[import-not-found]

        rows: list[list[Any]] = []
        for index, (chat_id, title) in self._dialog_cache.items():
            mark = "✅" if chat_id in self._selection.enabled else "▫️"
            label = title if len(title) <= 30 else title[:29] + "…"
            # Callback data is limited to 64 bytes, hence the index indirection.
            rows.append([Button.inline(f"{mark} {label}", data=f"g:{index}".encode())])
        rows.append([Button.inline("Done", data=b"done")])
        return rows

    async def _cmd_pause(self, event: Any) -> None:
        self.engine.paused = True
        self.engine.paused_reason = "paused from Telegram"
        self.journal.record_event("paused", "via control bot")
        await event.respond(
            "<b>Paused.</b> No new trades will be opened.\n"
            "Trades already open are still managed — a close or break-even from "
            "an admin will still be followed.\n\nSend /resume to start again.",
            parse_mode="html",
        )

    async def _cmd_resume(self, event: Any) -> None:
        self.engine.paused = False
        self.engine.paused_reason = ""
        self.journal.record_event("resumed", "via control bot")
        await event.respond(
            f"<b>Running.</b> Mode: {self._mode()}. New signals will be copied again.",
            parse_mode="html",
        )

    async def _cmd_trades(self, event: Any) -> None:
        parts = (event.raw_text or "").split()
        try:
            count = min(int(parts[1]), 25) if len(parts) > 1 else 10
        except ValueError:
            count = 10
        rows = await asyncio.to_thread(self.journal.recent, count)
        if not rows:
            await event.respond("Nothing recorded yet.")
            return
        lines = ["<b>Recent decisions</b>"]
        for row in rows:
            when = str(row["ts"])[11:16]
            if row["accepted"]:
                detail = f"{row['side'] or ''} {row['symbol'] or ''}".strip()
                lines.append(f"✅ {when} {_esc(detail)}")
            else:
                lines.append(f"▫️ {when} {_esc((row['reason'] or 'ignored')[:70])}")
        await event.respond("\n".join(lines), parse_mode="html")

    async def _cmd_risk(self, event: Any) -> None:
        risk = self.config.risk
        execution = self.config.execution
        sizing = (
            f"fixed {risk.fixed_lot} lots"
            if risk.fixed_lot is not None
            else f"{risk.risk_per_trade_pct}% of balance per trade"
        )
        await event.respond(
            "\n".join(
                [
                    f"<b>Sizing:</b> {sizing} (max {risk.max_lot} lots)",
                    f"<b>Open limit:</b> {risk.max_open_trades} total, "
                    f"{risk.max_open_per_symbol} per symbol",
                    f"<b>Daily stop:</b> {risk.max_daily_loss_pct}%",
                    f"<b>Targets:</b> {execution.tp_mode} (max {execution.max_tps})",
                    f"<b>Stop required:</b> {'yes' if execution.require_stop_loss else 'no'}",
                    f"<b>Hours:</b> {risk.hours.start}–{risk.hours.end} "
                    f"{', '.join(risk.hours.days)}",
                    f"<b>Symbols:</b> {', '.join(risk.allow_symbols) or 'any that resolve'}",
                    "",
                    "<i>Edit config.yaml and restart to change these.</i>",
                ]
            ),
            parse_mode="html",
        )

    async def _cmd_settings(self, event: Any) -> None:
        """Everything currently in force, in one message."""
        config = self.config
        risk = config.risk
        lines = [
            f"<b>Mode:</b> {self._mode()}",
            f"<b>Broker:</b> {config.broker.provider}"
            + (f" (suffix {config.broker.suffix})" if config.broker.suffix else ""),
            f"<b>Entry:</b> {config.execution.entry}, targets {config.execution.tp_mode}",
            f"<b>Sizing:</b> "
            + (
                f"fixed {risk.fixed_lot} lots"
                if risk.fixed_lot is not None
                else f"{risk.risk_per_trade_pct}% per trade"
            )
            + f", max {risk.max_lot} lots",
            f"<b>Limits:</b> {risk.max_open_trades} open, {risk.max_open_per_symbol} per symbol, "
            f"daily stop {risk.max_daily_loss_pct}%",
            f"<b>Hours:</b> {risk.hours.start}–{risk.hours.end} "
            f"({', '.join(risk.hours.days)}), your computer's clock",
            f"<b>Symbols:</b> {', '.join(risk.allow_symbols) or 'any that resolve'}",
            f"<b>Duplicates:</b> ignored within {risk.dedupe_window_minutes} min",
            f"<b>Groups:</b> {len(config.telegram.enabled_groups)} / {config.telegram.max_groups}",
            "",
            "<i>Edit config.yaml and restart to change any of this.</i>",
        ]
        await event.respond("\n".join(lines), parse_mode="html")

    async def _cmd_connect(self, event: Any) -> None:
        """Check the broker link, and try to rebuild it if it has dropped.

        MT5 connections die when the terminal is closed or restarted, and the
        failure is otherwise invisible until a signal arrives and cannot be
        filled.
        """
        broker = self.engine.broker
        try:
            account = await asyncio.to_thread(broker.account_info)
            await event.respond(
                f"<b>{broker.name}</b> is connected.\n"
                f"Balance {account.balance:,.2f} {account.currency}, "
                f"equity {account.equity:,.2f}.\n"
                f"Mode: {self._mode()}.",
                parse_mode="html",
            )
            return
        except Exception as exc:
            await event.respond(f"Not connected ({_esc(exc)}). Reconnecting…", parse_mode="html")

        try:
            # Go through the engine so broker_ready and broker_error move with
            # it; reconnecting the broker behind its back would leave the
            # engine still refusing every signal.
            ok = await asyncio.to_thread(self.engine.retry_broker, 0.0)
            if not ok:
                raise RuntimeError(self.engine.broker_error or "still unreachable")
            account = await asyncio.to_thread(broker.account_info)
            symbols = await asyncio.to_thread(broker.available_symbols)
            await event.respond(
                f"<b>Reconnected.</b> Balance {account.balance:,.2f} {account.currency}, "
                f"{len(symbols) or 'n/a'} symbols.",
                parse_mode="html",
            )
        except Exception as exc:
            await event.respond(
                f"<b>Could not connect:</b> {_esc(exc)}\n\n"
                "For MetaTrader 5, check that the terminal is open, logged in, and that "
                "Algo Trading is enabled (Tools → Options → Expert Advisors).",
                parse_mode="html",
            )

    # --- inline buttons ---

    async def _on_callback(self, event: Any) -> None:
        if not self._authorised(event.sender_id):
            await event.answer("This bot is private.", alert=True)
            return

        data = (event.data or b"").decode()
        if data == "done":
            await event.edit(
                f"Selection saved — copying {len(self._selection.enabled)} group(s).\n"
                "Restart the bot for changes to take effect.",
            )
            return

        if not data.startswith("g:"):
            return
        try:
            index = int(data[2:])
        except ValueError:
            return
        entry = self._dialog_cache.get(index)
        if entry is None:
            await event.answer("That list is stale — send /selectgroup again.", alert=True)
            return

        chat_id, title = entry
        _, message = self._selection.toggle(
            chat_id, title, limit=self.config.telegram.max_groups
        )
        self._selection.save(selection_path(self.config))
        await event.answer(message)
        try:
            await event.edit(buttons=self._group_buttons(list(self._dialog_cache.values())))
        except Exception:
            pass  # unchanged markup makes Telegram reject the edit; harmless

    # --- notifications ---

    async def notify(self, text: str) -> None:
        owner = self.config.control_bot.owner_id
        if not owner or self.client is None:
            return
        try:
            await self.client.send_message(owner, text, parse_mode="html")
        except Exception as exc:
            log.warning("could not send control-bot notification: %s", exc)
