"""Telethon listener: watches your chosen groups and feeds the engine.

This logs in as *your Telegram account* over MTProto, not as a bot. That is a
deliberate design decision, not a shortcut:

* A Bot API bot can only read messages in chats it has been added to, and needs
  privacy mode disabled by that chat's owner. You cannot add a bot to someone
  else's signal group, so a bot token simply cannot see those messages.
* A user client sees exactly what you see — which is the whole point, since you
  are already a member of these groups.

The session file it creates is as sensitive as your password. Keep it on the
machine that runs the bot and nowhere else.
"""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from .config import Config, GroupConfig
from .engine import Engine
from .models import Decision, MessageRef

log = logging.getLogger(__name__)


def _import_telethon() -> tuple[Any, Any, Any]:
    try:
        from telethon import TelegramClient, events  # type: ignore[import-not-found]
        from telethon.tl.types import (  # type: ignore[import-not-found]
            ChannelParticipantsAdmins,
        )
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("Telethon is not installed. Run: pip install telethon") from exc
    return TelegramClient, events, ChannelParticipantsAdmins


class TelegramListener:
    def __init__(self, config: Config, engine: Engine, control_bot: Any = None) -> None:
        self.config = config
        self.engine = engine
        self.control_bot = control_bot
        self.client: Any = None
        # chat_id -> the GroupConfig that produced it
        self._groups: dict[int, GroupConfig] = {}
        # chat_id -> (allowed sender ids, fetched_at)
        self._admins: dict[int, tuple[set[int], float]] = {}
        self._broadcast: set[int] = set()

    # --- connection ---

    async def connect(self) -> None:
        TelegramClient, _, _ = _import_telethon()
        telegram = self.config.telegram
        if not telegram.api_id or not telegram.api_hash:
            raise RuntimeError(
                "TG_API_ID / TG_API_HASH are missing. Create them at "
                "https://my.telegram.org -> API development tools, then put them in .env"
            )
        self.client = TelegramClient(
            str(self.config.session_path), telegram.api_id, telegram.api_hash
        )
        await self.client.start(
            phone=lambda: telegram.phone or input("Phone number (with country code): "),
            password=(lambda: telegram.twofa_password) if telegram.twofa_password else None,
        )
        me = await self.client.get_me()
        log.info("Telegram connected as %s (id %s)", me.first_name or me.username, me.id)

    async def resolve_groups(self) -> None:
        """Turn configured ids/usernames into live entities, and cache admins."""
        for group in self.config.telegram.enabled_groups:
            target: Any = group.id if group.id is not None else group.username
            try:
                entity = await self.client.get_entity(target)
            except Exception as exc:
                log.error(
                    "cannot resolve group %s (%s): %s. For private groups use the numeric "
                    "id from `tgscalper chats`, and make sure this account is a member.",
                    group.title or target,
                    target,
                    exc,
                )
                continue
            chat_id = int(getattr(entity, "id", 0))
            # Telethon reports channel ids without the -100 prefix; index both so
            # whichever form arrives on an event finds its config.
            self._groups[chat_id] = group
            self._groups[int(f"-100{chat_id}") if chat_id > 0 else chat_id] = group
            group.title = group.title or getattr(entity, "title", "") or str(target)

            is_broadcast = bool(getattr(entity, "broadcast", False))
            if is_broadcast:
                # Only admins can post in a broadcast channel, so every message
                # there is already admin-authored.
                self._broadcast.add(chat_id)
                log.info("watching channel %s (broadcast — all posts are admin posts)", group.title)
            else:
                await self._refresh_admins(entity, chat_id)
                log.info(
                    "watching group %s (%d allowed senders)",
                    group.title,
                    len(self._admins.get(chat_id, (set(), 0))[0]),
                )
        if not self._groups:
            raise RuntimeError(
                "no groups could be resolved — run `tgscalper chats` to list the ids "
                "of the chats this account can see, then put them in config.yaml"
            )

    async def _refresh_admins(self, entity: Any, chat_id: int) -> None:
        _, _, ChannelParticipantsAdmins = _import_telethon()
        group = self._groups.get(chat_id)
        if group is None:
            return
        if group.senders:
            # An explicit sender list always wins over whatever Telegram reports.
            self._admins[chat_id] = ({int(item) for item in group.senders}, time.time())
            return
        try:
            admins = await self.client.get_participants(
                entity, filter=ChannelParticipantsAdmins
            )
            self._admins[chat_id] = ({int(admin.id) for admin in admins}, time.time())
        except Exception as exc:
            # Small legacy groups and some privacy settings refuse the admin list.
            log.warning(
                "could not read the admin list for %s (%s). Falling back to accepting "
                "any sender in this chat — set `senders:` in config.yaml to lock it down.",
                group.title or chat_id,
                exc,
            )
            self._admins[chat_id] = (set(), time.time())

    # --- message handling ---

    def _allowed_sender(self, chat_id: int, sender_id: Optional[int], is_post: bool) -> bool:
        if not self.config.telegram.admin_only:
            return True
        if is_post or chat_id in self._broadcast:
            return True
        allowed, _ = self._admins.get(chat_id, (set(), 0.0))
        if not allowed:
            return True  # admin list unavailable; already warned at startup
        return sender_id is not None and int(sender_id) in allowed

    def _group_for(self, chat_id: int) -> Optional[GroupConfig]:
        group = self._groups.get(chat_id)
        if group is not None:
            return group
        # Normalise the -100 channel prefix in both directions.
        text = str(chat_id)
        if text.startswith("-100"):
            return self._groups.get(int(text[4:]))
        return self._groups.get(int(f"-100{abs(chat_id)}"))

    async def _on_message(self, event: Any) -> None:
        message = event.message
        text = (message.message or "").strip()
        if not text:
            return  # a chart image with no caption tells us nothing

        chat_id = int(event.chat_id)
        group = self._group_for(chat_id)
        if group is None:
            return

        sender_id = int(message.sender_id) if message.sender_id else None
        is_post = bool(getattr(message, "post", False))
        if not self._allowed_sender(chat_id, sender_id, is_post):
            log.debug("ignoring message from non-admin %s in %s", sender_id, group.title)
            return

        source = MessageRef(
            chat_id=chat_id,
            message_id=int(message.id),
            sender_id=sender_id,
            chat_title=group.title,
            sent_at=message.date,
            reply_to_message_id=(
                int(message.reply_to.reply_to_msg_id)
                if getattr(message, "reply_to", None)
                else None
            ),
        )

        log.info("[%s] %s", group.title, text.replace("\n", " | ")[:160])
        # Broker calls block; keep them off the event loop so the next signal is
        # still being received while this one is being placed.
        decision: Decision = await asyncio.to_thread(
            self.engine.handle, text, source, group
        )
        await self._notify(decision, group)

    async def _notify(self, decision: Decision, group: GroupConfig) -> None:
        bot = self.control_bot
        settings = self.config.control_bot
        # With a control bot running, receipts belong in that chat — it is where
        # the user is already looking.
        use_bot = bot is not None and settings.enabled and settings.notify
        target = self.config.telegram.notify_to

        if not use_bot and not target:
            return
        want_skips = settings.notify_skips if use_bot else self.config.telegram.notify_skips
        if not decision.accepted and not want_skips:
            return

        signal = decision.signal
        if decision.accepted and signal is not None:
            mode = "LIVE" if self.engine.broker.is_live else "PAPER"
            tickets = ", ".join(
                str(order.ticket) for order in decision.orders if order.ok and order.ticket
            )
            lines = [
                f"{mode} {signal.summary()}",
                f"from: {group.title}",
            ]
            if tickets:
                lines.append(f"ticket(s): {tickets}")
            failed = [order.error for order in decision.orders if not order.ok and order.error]
            if failed:
                lines.append("errors: " + "; ".join(failed))
            body = "\n".join(lines)
        else:
            body = f"skipped ({group.title}): {decision.reason}"

        if use_bot:
            await bot.notify(body)
            return
        try:
            await self.client.send_message(target, body)
        except Exception as exc:
            log.warning("could not send notification: %s", exc)

    # --- run loop ---

    async def run(self) -> None:
        _, events, _ = _import_telethon()
        await self.connect()

        # The control bot comes up before the groups are resolved, so that a
        # first-time user with nothing selected can still send /selectgroup.
        if self.control_bot is not None:
            try:
                await self.control_bot.start()
            except Exception as exc:
                log.error("control bot failed to start: %s", exc)
                self.control_bot = None

        try:
            await self.resolve_groups()
        except RuntimeError:
            if self.control_bot is None:
                raise
            # No groups chosen yet is a normal first run when there is a bot to
            # choose them with; idle instead of exiting.
            log.warning("no groups selected yet — send /selectgroup to your bot")
            await self.control_bot.notify(
                "No groups are selected yet.\nSend /selectgroup to choose which "
                "ones to copy."
            )
            await self.client.run_until_disconnected()
            return
        self.engine.journal.record_event("listener_start", f"{len(self._groups)} chat ids watched")

        chats = list(self._groups.keys())
        self.client.add_event_handler(self._on_message, events.NewMessage(chats=chats))
        # Admins routinely post a signal then edit in the SL/TP moments later.
        self.client.add_event_handler(self._on_message, events.MessageEdited(chats=chats))

        asyncio.create_task(self._heartbeat())
        log.info(
            "listening — %d group(s), %s mode. Ctrl-C to stop.",
            len(self.config.telegram.enabled_groups),
            "LIVE" if self.engine.broker.is_live else "PAPER",
        )
        await self.client.run_until_disconnected()

    async def _heartbeat(self) -> None:
        """Periodic proof of life, and a chance to refresh stale admin lists."""
        interval = max(300, self.config.telegram.admin_refresh_seconds)
        while True:
            await asyncio.sleep(interval)
            try:
                account = self.engine.broker.account_info()
                log.info(
                    "heartbeat: connected=%s equity=%.2f %s",
                    self.client.is_connected(),
                    account.equity,
                    account.currency,
                )
            except Exception as exc:
                log.warning("heartbeat could not read the account: %s", exc)
            for chat_id in list(self._groups):
                if chat_id in self._broadcast:
                    continue
                cached = self._admins.get(chat_id)
                if cached and time.time() - cached[1] < self.config.telegram.admin_refresh_seconds:
                    continue
                try:
                    entity = await self.client.get_entity(chat_id)
                    await self._refresh_admins(entity, chat_id)
                except Exception as exc:
                    log.debug("admin refresh failed for %s: %s", chat_id, exc)
