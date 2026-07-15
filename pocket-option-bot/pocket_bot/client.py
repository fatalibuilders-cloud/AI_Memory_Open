"""Async WebSocket client for the Pocket Option platform feed.

Speaks the socket.io v4 (EIO=4) style protocol used by the Pocket Option
web app:

  server -> "0{...}"                 engine.io open
  client -> "40"                     namespace connect
  server -> "40{"sid":...}"          namespace connected
  client -> 42["auth",{...}]         the SSID auth frame (from the browser)
  server -> "2"  / client -> "3"     ping / pong keepalive
  server -> 42["event",payload]      plain JSON events
  server -> 451-["event",{_placeholder}] followed by a BINARY frame that
            carries the JSON payload (Pocket Option sends most data this way)

Only events needed for trading are handled; everything else is ignored.
"""

from __future__ import annotations

import asyncio
import json
import logging
import ssl
import time
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Optional

import websockets

log = logging.getLogger("pocket_bot.client")

DEMO_REGIONS = [
    "wss://demo-api-eu.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://try-demo-eu.po.market/socket.io/?EIO=4&transport=websocket",
]

LIVE_REGIONS = [
    "wss://api-eu.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-sc.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-msk.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-fr.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-fin.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-us-north.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-us-south.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-in.po.market/socket.io/?EIO=4&transport=websocket",
    "wss://api-hk.po.market/socket.io/?EIO=4&transport=websocket",
]

HEADERS = {
    "Origin": "https://pocketoption.com",
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}


@dataclass
class OrderResult:
    order_id: Any
    asset: str
    direction: str
    amount: float
    profit: Optional[float] = None   # net PnL once the option closes
    open_payload: Optional[dict] = None
    close_payload: Optional[dict] = None

    @property
    def won(self) -> Optional[bool]:
        if self.profit is None:
            return None
        return self.profit > 0


class PocketOptionError(RuntimeError):
    pass


class PocketOptionClient:
    """Connection + trading primitives. One instance per account session."""

    def __init__(self, ssid: str, demo: bool = True):
        self.ssid = ssid.strip()
        self.demo = demo
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.balance: Optional[float] = None
        self.authenticated = asyncio.Event()
        self.payout: dict[str, float] = {}          # asset -> payout %
        self._pending_event: Optional[str] = None   # event name awaiting binary body
        self._open_waiters: dict[Any, asyncio.Future] = {}   # requestId -> future(open payload)
        self._close_waiters: dict[Any, asyncio.Future] = {}  # order id  -> future(profit)
        self._request_id = int(time.time())
        self._tick_handler: Optional[Callable[[str, float, float], Awaitable[None]]] = None
        self._listen_task: Optional[asyncio.Task] = None
        self._closed = False

    # ------------------------------------------------------------------
    # connection
    # ------------------------------------------------------------------

    async def connect(self) -> None:
        regions = DEMO_REGIONS if self.demo else LIVE_REGIONS
        last_err: Optional[Exception] = None
        for url in regions:
            try:
                log.info("Connecting to %s ...", url.split("/socket.io")[0])
                await self._connect_one(url)
                log.info("Authenticated. Balance: %s", self.balance)
                return
            except Exception as exc:  # try the next region
                last_err = exc
                log.warning("Region failed (%s), trying next...", exc)
                await self._teardown()
        raise PocketOptionError(f"Could not authenticate on any region: {last_err}")

    async def _connect_one(self, url: str) -> None:
        ssl_ctx = ssl.create_default_context()
        self.ws = await websockets.connect(
            url,
            additional_headers=HEADERS,
            ping_interval=None,      # Pocket Option uses engine.io ping, not WS ping
            max_size=8 * 1024 * 1024,
            open_timeout=15,
        )
        self.authenticated.clear()
        self._closed = False

        # engine.io handshake: wait for "0{...}", answer "40"
        opening = await asyncio.wait_for(self.ws.recv(), timeout=10)
        if not str(opening).startswith("0"):
            raise PocketOptionError(f"Unexpected opening frame: {opening!r}")
        await self.ws.send("40")

        self._listen_task = asyncio.create_task(self._listen(), name="po-listen")

        try:
            await asyncio.wait_for(self.authenticated.wait(), timeout=20)
        except asyncio.TimeoutError:
            raise PocketOptionError("Auth timed out — SSID invalid/expired or wrong region.")

    async def _teardown(self) -> None:
        self._closed = True
        if self._listen_task:
            self._listen_task.cancel()
            self._listen_task = None
        if self.ws:
            try:
                await self.ws.close()
            except Exception:
                pass
            self.ws = None

    async def close(self) -> None:
        await self._teardown()

    @property
    def connected(self) -> bool:
        return self.ws is not None and not self._closed and self.authenticated.is_set()

    # ------------------------------------------------------------------
    # message loop
    # ------------------------------------------------------------------

    async def _listen(self) -> None:
        assert self.ws is not None
        try:
            async for raw in self.ws:
                try:
                    if isinstance(raw, (bytes, bytearray)):
                        await self._on_binary(bytes(raw))
                    else:
                        await self._on_text(str(raw))
                except Exception:
                    log.exception("Error handling frame: %.200s", raw)
        except websockets.ConnectionClosed as exc:
            if not self._closed:
                log.warning("Connection closed by server: %s", exc)
        finally:
            self.authenticated.clear()
            self._closed = True
            for fut in list(self._open_waiters.values()) + list(self._close_waiters.values()):
                if not fut.done():
                    fut.set_exception(PocketOptionError("Connection lost"))

    async def _on_text(self, msg: str) -> None:
        if msg == "2":                       # engine.io ping -> pong
            await self.ws.send("3")
            return
        if msg.startswith("40"):             # namespace connected -> authenticate
            await self.ws.send(self.ssid)
            return
        if msg.startswith("451-"):           # event with binary attachment
            try:
                event = json.loads(msg[4:])[0]
            except Exception:
                event = None
            self._pending_event = event
            return
        if msg.startswith("42"):             # plain JSON event
            try:
                data = json.loads(msg[2:])
            except Exception:
                return
            if isinstance(data, list) and data:
                await self._dispatch(data[0], data[1] if len(data) > 1 else None)

    async def _on_binary(self, blob: bytes) -> None:
        event, self._pending_event = self._pending_event, None
        if event is None:
            return
        if blob[:1] == b"\x04":              # engine.io binary type prefix, if present
            blob = blob[1:]
        try:
            payload = json.loads(blob.decode("utf-8"))
        except Exception:
            log.debug("Non-JSON binary payload for %s (%d bytes)", event, len(blob))
            return
        await self._dispatch(event, payload)

    async def _dispatch(self, event: str, payload: Any) -> None:
        if event == "successauth":
            log.info("Auth OK.")
            self.authenticated.set()
        elif event in ("successupdateBalance", "updateBalance"):
            if isinstance(payload, dict) and "balance" in payload:
                self.balance = float(payload["balance"])
                log.info("Balance update: %.2f", self.balance)
        elif event == "updateStream":
            # payload: [[asset, unix_ts, price], ...]
            if self._tick_handler and isinstance(payload, list):
                for item in payload:
                    if isinstance(item, list) and len(item) >= 3:
                        await self._tick_handler(str(item[0]), float(item[1]), float(item[2]))
        elif event == "successopenOrder":
            if isinstance(payload, dict):
                req = payload.get("requestId")
                fut = self._open_waiters.pop(req, None)
                if fut and not fut.done():
                    fut.set_result(payload)
        elif event == "failopenOrder":
            # No reliable requestId on failure frames — fail all pending opens.
            for req, fut in list(self._open_waiters.items()):
                if not fut.done():
                    fut.set_exception(PocketOptionError(f"Order rejected: {payload}"))
                self._open_waiters.pop(req, None)
        elif event == "successcloseOrder":
            if isinstance(payload, dict):
                for deal in payload.get("deals", []):
                    fut = self._close_waiters.pop(deal.get("id"), None)
                    if fut and not fut.done():
                        fut.set_result(deal)
        elif event == "updatePayout":
            pass  # payout catalogue; asset-level payout arrives elsewhere
        else:
            log.debug("Unhandled event %s", event)

    # ------------------------------------------------------------------
    # public API
    # ------------------------------------------------------------------

    def on_tick(self, handler: Callable[[str, float, float], Awaitable[None]]) -> None:
        """Register async handler(asset, timestamp, price) for streamed ticks."""
        self._tick_handler = handler

    async def subscribe(self, asset: str, period_seconds: int = 60) -> None:
        """Subscribe to the live price stream for an asset."""
        await self._emit("changeSymbol", {"asset": asset, "period": period_seconds})
        log.info("Subscribed to %s (period %ss)", asset, period_seconds)

    async def buy(
        self,
        asset: str,
        amount: float,
        direction: str,               # "call" (up) or "put" (down)
        duration_seconds: int,
        timeout: float = 15.0,
    ) -> OrderResult:
        """Place a binary option order and wait for open confirmation."""
        if direction not in ("call", "put"):
            raise ValueError("direction must be 'call' or 'put'")
        if not self.connected:
            raise PocketOptionError("Not connected/authenticated")

        self._request_id += 1
        req_id = self._request_id
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._open_waiters[req_id] = fut

        await self._emit("openOrder", {
            "asset": asset,
            "amount": round(float(amount), 2),
            "action": direction,
            "isDemo": 1 if self.demo else 0,
            "requestId": req_id,
            "optionType": 100,
            "time": int(duration_seconds),
        })
        log.info("Order sent: %s %s $%.2f / %ss", asset, direction.upper(), amount, duration_seconds)

        try:
            payload = await asyncio.wait_for(fut, timeout=timeout)
        finally:
            self._open_waiters.pop(req_id, None)

        return OrderResult(
            order_id=payload.get("id"),
            asset=asset,
            direction=direction,
            amount=amount,
            open_payload=payload,
        )

    async def wait_result(self, order: OrderResult, duration_seconds: int) -> OrderResult:
        """Wait for the option to expire and fill in the profit."""
        fut: asyncio.Future = asyncio.get_running_loop().create_future()
        self._close_waiters[order.order_id] = fut
        try:
            deal = await asyncio.wait_for(fut, timeout=duration_seconds + 30)
            order.close_payload = deal
            order.profit = float(deal.get("profit", 0.0))
        except asyncio.TimeoutError:
            log.warning("No close event for order %s within timeout.", order.order_id)
        finally:
            self._close_waiters.pop(order.order_id, None)
        return order

    async def _emit(self, event: str, payload: Any) -> None:
        assert self.ws is not None
        await self.ws.send('42["' + event + '",' + json.dumps(payload, separators=(",", ":")) + "]")
