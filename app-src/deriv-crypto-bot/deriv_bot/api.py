"""Deriv WebSocket API client.

A thin request/response layer over Deriv's WebSocket v3 API. Requests carry a
`req_id` and responses are matched back to the caller's future by that id, so
several requests can be in flight at once.

The client deliberately avoids streaming subscriptions. Everything the bot
needs (candles, balance, contract status) is polled, which makes reconnection
after a network blip a matter of dialing again rather than rebuilding
subscription state — the property that matters most for a process expected to
stay up 24/7.
"""

from __future__ import annotations

import asyncio
import itertools
import json
import logging
import time
from typing import Any

try:  # websockets >= 13
    from websockets.asyncio.client import connect as ws_connect
except ImportError:  # pragma: no cover - older websockets releases
    from websockets.legacy.client import connect as ws_connect  # type: ignore

from websockets.exceptions import ConnectionClosed, WebSocketException

from .config import Config

log = logging.getLogger(__name__)

# Calls that must never appear in logs with their arguments intact.
_SENSITIVE_KEYS = {"authorize", "api_token", "token"}


class DerivError(Exception):
    """An error payload returned by the Deriv API."""

    def __init__(self, code: str, message: str, request: dict | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.request = request


class ConnectionLost(Exception):
    """The socket closed while a request was outstanding."""


class RateLimiter:
    """Token bucket that smooths request bursts below Deriv's per-minute cap."""

    def __init__(self, rate: float, capacity: int) -> None:
        self.rate = rate
        self.capacity = capacity
        self._tokens = float(capacity)
        self._updated = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            while True:
                now = time.monotonic()
                self._tokens = min(self.capacity, self._tokens + (now - self._updated) * self.rate)
                self._updated = now
                if self._tokens >= 1:
                    self._tokens -= 1
                    return
                await asyncio.sleep((1 - self._tokens) / self.rate)


def _redact(request: dict) -> dict:
    return {k: ("***" if k in _SENSITIVE_KEYS else v) for k, v in request.items()}


class DerivAPI:
    """One logical session against Deriv. Reusable across reconnections."""

    def __init__(self, config: Config) -> None:
        self.config = config
        self._socket: Any = None
        self._reader: asyncio.Task | None = None
        self._keepalive: asyncio.Task | None = None
        self._pending: dict[int, asyncio.Future] = {}
        self._req_ids = itertools.count(1)
        # Deriv's documented general limit is well above this; staying under it
        # by a wide margin keeps headroom for retries.
        self._limiter = RateLimiter(rate=1.5, capacity=10)
        self.account: dict = {}

    # -- lifecycle --------------------------------------------------------

    @property
    def connected(self) -> bool:
        return self._socket is not None

    def _url(self) -> str:
        return f"{self.config.endpoint}?app_id={self.config.app_id}&l=EN&brand=deriv"

    async def connect(self) -> dict:
        """Dial the socket and authorize. Returns the authorize payload."""
        await self.close()
        log.info("connecting to %s (app_id=%s)", self.config.endpoint, self.config.app_id)
        self._socket = await ws_connect(
            self._url(),
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
            max_size=8 * 1024 * 1024,
        )
        self._reader = asyncio.create_task(self._read_loop(), name="deriv-reader")
        self._keepalive = asyncio.create_task(self._keepalive_loop(), name="deriv-keepalive")

        response = await self.send({"authorize": self.config.api_token})
        self.account = response.get("authorize", {})
        log.info(
            "authorized: loginid=%s currency=%s virtual=%s",
            self.account.get("loginid"),
            self.account.get("currency"),
            self.account.get("is_virtual"),
        )
        return self.account

    async def close(self) -> None:
        """Tear the session down. Safe to call when already closed."""
        for task in (self._reader, self._keepalive):
            if task and not task.done():
                task.cancel()
        for task in (self._reader, self._keepalive):
            if task:
                try:
                    await task
                except (asyncio.CancelledError, Exception):  # noqa: BLE001
                    pass
        self._reader = None
        self._keepalive = None

        if self._socket is not None:
            try:
                await self._socket.close()
            except (WebSocketException, OSError):
                pass
            self._socket = None

        self._fail_pending(ConnectionLost("session closed"))

    def _fail_pending(self, exc: Exception) -> None:
        for future in list(self._pending.values()):
            if not future.done():
                future.set_exception(exc)
        self._pending.clear()

    # -- background tasks -------------------------------------------------

    async def _read_loop(self) -> None:
        socket = self._socket
        try:
            async for raw in socket:
                try:
                    message = json.loads(raw)
                except json.JSONDecodeError:
                    log.warning("discarding non-JSON frame from Deriv")
                    continue
                self._dispatch(message)
        except ConnectionClosed as exc:
            log.warning("socket closed: %s", exc)
            self._fail_pending(ConnectionLost(str(exc)))
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # noqa: BLE001 - reader must never die silently
            log.exception("reader loop failed")
            self._fail_pending(ConnectionLost(str(exc)))

    def _dispatch(self, message: dict) -> None:
        req_id = message.get("req_id")
        future = self._pending.pop(req_id, None) if req_id is not None else None
        if future is None:
            if message.get("msg_type") != "ping":
                log.debug("unmatched message: %s", message.get("msg_type"))
            return
        if future.done():
            return
        future.set_result(message)

    async def _keepalive_loop(self) -> None:
        """Application-level ping. Deriv drops idle sessions after ~2 minutes."""
        try:
            while True:
                await asyncio.sleep(30)
                try:
                    await self.send({"ping": 1}, timeout=15)
                except (ConnectionLost, asyncio.TimeoutError, DerivError):
                    return
        except asyncio.CancelledError:
            raise

    # -- requests ---------------------------------------------------------

    async def send(self, request: dict, *, timeout: float | None = None) -> dict:
        """Send one request and await its response.

        Raises DerivError for API-level errors and ConnectionLost if the socket
        drops before the response arrives.
        """
        if self._socket is None:
            raise ConnectionLost("not connected")

        await self._limiter.acquire()

        req_id = next(self._req_ids)
        payload = {**request, "req_id": req_id}
        future: asyncio.Future = asyncio.get_running_loop().create_future()
        self._pending[req_id] = future

        try:
            await self._socket.send(json.dumps(payload))
        except (ConnectionClosed, WebSocketException, OSError) as exc:
            self._pending.pop(req_id, None)
            raise ConnectionLost(f"send failed: {exc}") from exc

        try:
            response = await asyncio.wait_for(
                future, timeout=timeout or self.config.request_timeout
            )
        except asyncio.TimeoutError:
            self._pending.pop(req_id, None)
            log.warning("request timed out: %s", _redact(request))
            raise
        finally:
            self._pending.pop(req_id, None)

        error = response.get("error")
        if error:
            raise DerivError(
                error.get("code", "UnknownError"),
                error.get("message", "no message"),
                _redact(request),
            )
        return response

    # -- typed helpers ----------------------------------------------------

    async def active_symbols(self) -> list[dict]:
        response = await self.send({"active_symbols": "brief", "product_type": "basic"})
        return response.get("active_symbols", [])

    async def contracts_for(self, symbol: str, currency: str) -> dict:
        response = await self.send(
            {"contracts_for": symbol, "currency": currency, "product_type": "basic"}
        )
        return response.get("contracts_for", {})

    async def candles(self, symbol: str, granularity: int, count: int) -> list[dict]:
        response = await self.send(
            {
                "ticks_history": symbol,
                "style": "candles",
                "granularity": granularity,
                "count": count,
                "end": "latest",
            }
        )
        return response.get("candles", [])

    async def balance(self) -> dict:
        response = await self.send({"balance": 1})
        return response.get("balance", {})

    async def proposal(self, request: dict) -> dict:
        response = await self.send({"proposal": 1, **request})
        return response.get("proposal", {})

    async def buy(self, proposal_id: str, max_price: float) -> dict:
        response = await self.send({"buy": proposal_id, "price": max_price})
        return response.get("buy", {})

    async def open_contract(self, contract_id: int) -> dict:
        response = await self.send({"proposal_open_contract": 1, "contract_id": contract_id})
        return response.get("proposal_open_contract", {})
