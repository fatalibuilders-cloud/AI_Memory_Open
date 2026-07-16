"""Minimal Telegram Bot API client + phone remote-control interface.

Uses stdlib urllib long-polling — no external dependency. You create the
bot once with @BotFather, put its token in .env, then from your phone:

    /login <password>   authorize this chat (persisted across restarts)
    /status             mode, day stats, open positions
    /balance            balance & equity
    /positions          open positions with floating PnL
    /close <ticket>     close one position
    /closeall           close everything
    /resume             enable auto-trading
    /pause              disable auto-trading (positions stay open)
    /risk <pct>         set % of balance risked per trade
    /logout             de-authorize this chat

Only authorized chats can issue commands; everyone else gets a login
prompt. Trade opens/closes are pushed to all authorized chats.
"""

from __future__ import annotations

import json
import logging
import threading
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger("fmsbot.telegram")

API = "https://api.telegram.org/bot{token}/{method}"


class TelegramRemote:
    def __init__(self, token: str, password: str, state_file: str,
                 command_handler: Callable[[int, str, list[str]], Optional[str]]):
        """command_handler(chat_id, command, args) -> reply text (or None)."""
        self.token = token
        self.password = password
        self.state_path = Path(state_file)
        self.handler = command_handler
        self.authorized: set[int] = set()
        self._offset = 0
        self._stop = threading.Event()
        self._thread: Optional[threading.Thread] = None
        self._failed_logins: dict[int, list[float]] = {}
        self._load_state()

    # -- persistence -----------------------------------------------------

    def _load_state(self) -> None:
        try:
            data = json.loads(self.state_path.read_text())
            self.authorized = set(int(c) for c in data.get("authorized", []))
        except (OSError, ValueError):
            pass

    def _save_state(self) -> None:
        try:
            self.state_path.write_text(json.dumps({"authorized": sorted(self.authorized)}))
        except OSError:
            log.exception("Could not persist telegram state")

    # -- API ------------------------------------------------------------------

    def _call(self, method: str, http_timeout: float = 15, **params) -> dict:
        url = API.format(token=self.token, method=method)
        body = urllib.parse.urlencode(params).encode()
        req = urllib.request.Request(url, data=body)
        with urllib.request.urlopen(req, timeout=http_timeout) as resp:
            return json.loads(resp.read().decode())

    def send(self, chat_id: int, text: str) -> None:
        try:
            self._call("sendMessage", chat_id=chat_id, text=text)
        except Exception as exc:
            log.warning("sendMessage failed: %s", exc)

    def broadcast(self, text: str) -> None:
        for chat in list(self.authorized):
            self.send(chat, text)

    # -- polling loop ------------------------------------------------------------

    def start(self) -> None:
        self._thread = threading.Thread(target=self._poll_loop, name="tg-poll", daemon=True)
        self._thread.start()
        log.info("Telegram remote started (%d authorized chat(s) restored).",
                 len(self.authorized))

    def stop(self) -> None:
        self._stop.set()

    def _poll_loop(self) -> None:
        while not self._stop.is_set():
            try:
                resp = self._call("getUpdates", http_timeout=60,
                                  offset=self._offset, timeout=50)
                for update in resp.get("result", []):
                    self._offset = update["update_id"] + 1
                    msg = update.get("message") or {}
                    text = (msg.get("text") or "").strip()
                    chat = msg.get("chat", {}).get("id")
                    if chat is None or not text:
                        continue
                    try:
                        self._on_message(int(chat), text)
                    except Exception:
                        log.exception("Error handling %r", text)
            except Exception as exc:
                log.warning("Polling error (%s), retrying in 5s...", exc)
                time.sleep(5)

    # -- auth + dispatch -------------------------------------------------------------

    def _on_message(self, chat_id: int, text: str) -> None:
        parts = text.split()
        command = parts[0].lower().lstrip("/").split("@")[0]
        args = parts[1:]

        if command == "login":
            self._handle_login(chat_id, args)
            return
        if command in ("start", "help"):
            self.send(chat_id, self._help(chat_id))
            return
        if chat_id not in self.authorized:
            self.send(chat_id, "Not authorized. Log in first: /login <password>")
            return
        if command == "logout":
            self.authorized.discard(chat_id)
            self._save_state()
            self.send(chat_id, "Logged out.")
            return
        reply = self.handler(chat_id, command, args)
        if reply:
            self.send(chat_id, reply)

    def _handle_login(self, chat_id: int, args: list[str]) -> None:
        # simple brute-force throttle: max 5 attempts / 10 minutes per chat
        now = time.time()
        attempts = [t for t in self._failed_logins.get(chat_id, []) if now - t < 600]
        if len(attempts) >= 5:
            self.send(chat_id, "Too many attempts. Try again later.")
            return
        if args and args[0] == self.password:
            self.authorized.add(chat_id)
            self._failed_logins.pop(chat_id, None)
            self._save_state()
            self.send(chat_id, "✅ Logged in. You control the bot now — /status to begin, "
                               "/help for all commands.")
            log.info("Chat %s authorized.", chat_id)
        else:
            attempts.append(now)
            self._failed_logins[chat_id] = attempts
            self.send(chat_id, "Wrong password.")

    def _help(self, chat_id: int) -> str:
        if chat_id not in self.authorized:
            return ("FMS trading bot remote.\n"
                    "Log in first: /login <password>")
        return ("Commands:\n"
                "/status — mode, day stats\n"
                "/balance — balance & equity\n"
                "/positions — open positions\n"
                "/close <ticket> — close one\n"
                "/closeall — close everything\n"
                "/resume — enable auto-trading\n"
                "/pause — stop opening new trades\n"
                "/risk <pct> — set risk per trade\n"
                "/logout")
