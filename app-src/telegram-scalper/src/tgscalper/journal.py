"""SQLite record of every message seen, every decision taken, every order sent.

Three jobs:

1. Audit — when a trade appears in your account you can point at the exact
   Telegram post that caused it.
2. Memory across restarts — duplicate detection, hourly signal counts and the
   day's opening balance survive the bot being restarted mid-session.
3. Follow-ups — maps a signal's message id to the broker tickets it opened, so
   "close that one" (as a Telegram reply) finds the right positions.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from contextlib import closing
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

from .models import MessageRef, OrderRequest, OrderResult, Signal

SCHEMA = """
CREATE TABLE IF NOT EXISTS signals (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    ts            TEXT NOT NULL,
    chat_id       INTEGER,
    chat_title    TEXT,
    message_id    INTEGER,
    sender_id     INTEGER,
    action        TEXT,
    symbol        TEXT,
    side          TEXT,
    entry         REAL,
    stop_loss     REAL,
    take_profits  TEXT,
    fingerprint   TEXT,
    accepted      INTEGER NOT NULL,
    reason        TEXT,
    raw_text      TEXT
);
CREATE INDEX IF NOT EXISTS idx_signals_fp ON signals (fingerprint, ts);
CREATE INDEX IF NOT EXISTS idx_signals_msg ON signals (chat_id, message_id);

CREATE TABLE IF NOT EXISTS orders (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts          TEXT NOT NULL,
    signal_id   INTEGER,
    chat_id     INTEGER,
    message_id  INTEGER,
    ticket      INTEGER,
    symbol      TEXT,
    side        TEXT,
    order_type  TEXT,
    volume      REAL,
    price       REAL,
    stop_loss   REAL,
    take_profit REAL,
    leg         INTEGER,
    live        INTEGER,
    ok          INTEGER,
    error       TEXT,
    closed_at   TEXT,
    close_price REAL,
    profit      REAL,
    FOREIGN KEY (signal_id) REFERENCES signals (id)
);
CREATE INDEX IF NOT EXISTS idx_orders_msg ON orders (chat_id, message_id);
CREATE INDEX IF NOT EXISTS idx_orders_ticket ON orders (ticket);

CREATE TABLE IF NOT EXISTS day_marks (
    day     TEXT PRIMARY KEY,
    balance REAL NOT NULL,
    ts      TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS events (
    id     INTEGER PRIMARY KEY AUTOINCREMENT,
    ts     TEXT NOT NULL,
    kind   TEXT NOT NULL,
    detail TEXT
);
"""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class Journal:
    def __init__(self, path: str | Path = "data/journal.sqlite") -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        # The engine runs on worker threads (asyncio.to_thread), so several
        # messages can reach the journal at once. sqlite3 tolerates the shared
        # connection only with check_same_thread=False, and even then
        # interleaved statement/commit pairs corrupt each other's transactions
        # — "cannot commit - no transaction is active". One lock around every
        # database touch removes the interleaving entirely.
        self._lock = threading.RLock()
        with self._lock:
            # WAL keeps reads (the report command) from blocking the live writer.
            self.conn.execute("PRAGMA journal_mode=WAL")
            with closing(self.conn.cursor()) as cursor:
                cursor.executescript(SCHEMA)
            self.conn.commit()

    def close(self) -> None:
        with self._lock:
            self.conn.close()

    def _write(self, sql: str, params: tuple[object, ...] = ()) -> int:
        """Run one statement and commit it, atomically against other threads."""
        with self._lock:
            cursor = self.conn.execute(sql, params)
            self.conn.commit()
            return int(cursor.lastrowid or 0)

    def _read(self, sql: str, params: tuple[object, ...] | list[object] = ()) -> list[sqlite3.Row]:
        with self._lock:
            return self.conn.execute(sql, params).fetchall()

    # --- writes ---

    def record_signal(self, signal: Signal, accepted: bool, reason: str = "") -> int:
        source = signal.source or MessageRef(chat_id=0, message_id=0)
        return self._write(
            """INSERT INTO signals (ts, chat_id, chat_title, message_id, sender_id, action,
                                    symbol, side, entry, stop_loss, take_profits, fingerprint,
                                    accepted, reason, raw_text)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                _now(),
                source.chat_id,
                source.chat_title,
                source.message_id,
                source.sender_id,
                signal.action.value,
                signal.symbol,
                signal.side.value if signal.side else None,
                signal.entry,
                signal.stop_loss,
                json.dumps(signal.take_profits),
                signal.fingerprint(),
                int(accepted),
                reason,
                signal.raw_text[:4000],
            ),
        )

    def record_skip(self, source: Optional[MessageRef], reason: str, raw_text: str) -> None:
        """Log a message we chose not to trade, so nothing is invisible."""
        reference = source or MessageRef(chat_id=0, message_id=0)
        self._write(
            """INSERT INTO signals (ts, chat_id, chat_title, message_id, sender_id, action,
                                    symbol, accepted, reason, raw_text)
               VALUES (?,?,?,?,?,?,?,?,?,?)""",
            (
                _now(),
                reference.chat_id,
                reference.chat_title,
                reference.message_id,
                reference.sender_id,
                "SKIP",
                "",
                0,
                reason,
                raw_text[:4000],
            ),
        )

    def record_order(
        self,
        signal_id: int,
        source: Optional[MessageRef],
        request: OrderRequest,
        result: OrderResult,
        live: bool,
    ) -> None:
        reference = source or MessageRef(chat_id=0, message_id=0)
        self._write(
            """INSERT INTO orders (ts, signal_id, chat_id, message_id, ticket, symbol, side,
                                   order_type, volume, price, stop_loss, take_profit, leg,
                                   live, ok, error)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                _now(),
                signal_id,
                reference.chat_id,
                reference.message_id,
                result.ticket,
                request.symbol,
                request.side.value,
                request.order_type.value,
                result.volume or request.volume,
                result.filled_price or request.price,
                request.stop_loss,
                request.take_profit,
                request.leg,
                int(live),
                int(result.ok),
                result.error,
            ),
        )

    def record_close(
        self, ticket: int, close_price: Optional[float], profit: Optional[float] = None
    ) -> None:
        self._write(
            "UPDATE orders SET closed_at = ?, close_price = ?, profit = ? WHERE ticket = ?",
            (_now(), close_price, profit, ticket),
        )

    def record_event(self, kind: str, detail: str = "") -> None:
        self._write("INSERT INTO events (ts, kind, detail) VALUES (?,?,?)", (_now(), kind, detail))

    # --- reads ---

    def seen_fingerprint(self, fingerprint: str, window_minutes: int) -> Optional[str]:
        """Return the timestamp of a matching accepted signal inside the window."""
        if window_minutes <= 0:
            return None
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=window_minutes)).isoformat()
        rows = self._read(
            """SELECT ts FROM signals
               WHERE fingerprint = ? AND accepted = 1 AND ts >= ?
               ORDER BY ts DESC LIMIT 1""",
            (fingerprint, cutoff),
        )
        return rows[0]["ts"] if rows else None

    def accepted_since(self, minutes: int) -> int:
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=minutes)).isoformat()
        rows = self._read(
            "SELECT COUNT(*) AS n FROM signals WHERE accepted = 1 AND action = 'OPEN' AND ts >= ?",
            (cutoff,),
        )
        return int(rows[0]["n"]) if rows else 0

    def tickets_for_message(self, chat_id: int, message_id: int) -> list[int]:
        """Broker tickets opened by one Telegram post (for reply-based follow-ups)."""
        rows = self._read(
            """SELECT ticket FROM orders
               WHERE chat_id = ? AND message_id = ? AND ok = 1 AND ticket IS NOT NULL
                 AND closed_at IS NULL""",
            (chat_id, message_id),
        )
        return [int(row["ticket"]) for row in rows]

    def open_tickets(self, chat_id: Optional[int] = None, symbol: Optional[str] = None) -> list[int]:
        query = "SELECT ticket FROM orders WHERE ok = 1 AND ticket IS NOT NULL AND closed_at IS NULL"
        params: list[object] = []
        if chat_id is not None:
            query += " AND chat_id = ?"
            params.append(chat_id)
        if symbol:
            query += " AND UPPER(symbol) = ?"
            params.append(symbol.upper())
        query += " ORDER BY id DESC"
        return [int(row["ticket"]) for row in self._read(query, params)]

    def day_start_balance(self, balance: float, day: Optional[date] = None) -> float:
        """Record and return the balance the day opened with.

        First call each day stores the mark; later calls return the stored value,
        so the daily-loss guard survives a restart without resetting.
        """
        key = (day or datetime.now(timezone.utc).date()).isoformat()
        with self._lock:
            rows = self._read("SELECT balance FROM day_marks WHERE day = ?", (key,))
            if rows:
                return float(rows[0]["balance"])
            self._write(
                "INSERT INTO day_marks (day, balance, ts) VALUES (?,?,?)", (key, balance, _now())
            )
        return balance

    def summary(self, days: int = 7) -> dict[str, object]:
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        signals = self._read(
            """SELECT accepted, COUNT(*) AS n FROM signals WHERE ts >= ? GROUP BY accepted""",
            (cutoff,),
        )
        counts = {int(row["accepted"]): int(row["n"]) for row in signals}
        orders = self._read(
            """SELECT COUNT(*) AS n, SUM(ok) AS filled, SUM(COALESCE(profit, 0)) AS pnl,
                      SUM(live) AS live_orders
               FROM orders WHERE ts >= ?""",
            (cutoff,),
        )[0]
        top_reasons = self._read(
            """SELECT reason, COUNT(*) AS n FROM signals
               WHERE ts >= ? AND accepted = 0 AND reason != ''
               GROUP BY reason ORDER BY n DESC LIMIT 5""",
            (cutoff,),
        )
        return {
            "days": days,
            "signals_accepted": counts.get(1, 0),
            "signals_skipped": counts.get(0, 0),
            "orders_attempted": int(orders["n"] or 0),
            "orders_filled": int(orders["filled"] or 0),
            "live_orders": int(orders["live_orders"] or 0),
            "recorded_pnl": round(float(orders["pnl"] or 0.0), 2),
            "top_skip_reasons": [(row["reason"], int(row["n"])) for row in top_reasons],
        }

    def skipped(self, days: int = 1, limit: int = 30, reason: str = "") -> list[sqlite3.Row]:
        """Messages that were not traded, with their original text.

        The reason alone ("no trade direction found") says the parser failed
        but not what it failed on. The raw text is what makes a parser fix
        possible.
        """
        cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query = """SELECT ts, chat_title, reason, raw_text FROM signals
                   WHERE accepted = 0 AND ts >= ? AND raw_text != ''"""
        params: list[object] = [cutoff]
        if reason:
            query += " AND reason LIKE ?"
            params.append(f"%{reason}%")
        query += " ORDER BY id DESC LIMIT ?"
        params.append(limit)
        return self._read(query, params)

    def recent(self, limit: int = 20) -> list[sqlite3.Row]:
        return self._read(
            """SELECT ts, chat_title, action, symbol, side, entry, stop_loss, accepted, reason
               FROM signals ORDER BY id DESC LIMIT ?""",
            (limit,),
        )
