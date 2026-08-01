"""Binance USDⓈ-M Futures adapter (stdlib only — no external packages).

Unlike Exness/Deriv/Vantage this is NOT MetaTrader: Binance has its own
signed REST API, so this is a real adapter rather than a trait module.
Futures rather than Spot, because the bot needs positions with attached
stop-loss and take-profit, which Spot does not provide.

Setup:
  1. TESTNET FIRST: https://testnet.binancefuture.com — free, funded with
     play money, and the exact same API. Set BINANCE_TESTNET=1.
  2. Create an API key with *Futures trading* enabled. Do NOT enable
     withdrawals. Restrict it to your IP if you can.
  3. .env: BROKER=binance, BINANCE_API_KEY, BINANCE_API_SECRET,
     BINANCE_TESTNET=1

Symbols are Binance-style: BTCUSDT, ETHUSDT (not BTCUSD).

Note on leverage: futures positions are leveraged and can be liquidated,
which is a harder failure than a stop-loss. Keep leverage low and size
small; the bot's own risk limits still apply on top.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .base import Bar, Broker, BrokerError, OrderReceipt, Position

log = logging.getLogger("fmsbot.binance")

LIVE_HOST = "https://fapi.binance.com"
TEST_HOST = "https://testnet.binancefuture.com"

_INTERVAL = {"M1": "1m", "M5": "5m", "M15": "15m", "M30": "30m",
             "H1": "1h", "H4": "4h", "D1": "1d"}


class BinanceBroker(Broker):
    broker_name = "Binance Futures"

    def __init__(self, api_key: str, api_secret: str, testnet: bool = True):
        self.host = TEST_HOST if testnet else LIVE_HOST
        self.testnet = testnet
        self.key = api_key.strip()
        self.secret = api_secret.strip().encode()
        self._filters: dict[str, dict] = {}
        self._connected = False

    # -- HTTP ------------------------------------------------------------

    def _request(self, method: str, path: str, params: Optional[dict] = None,
                 signed: bool = False) -> object:
        params = dict(params or {})
        if signed:
            params["timestamp"] = int(time.time() * 1000)
            params["recvWindow"] = 10_000
            query = urllib.parse.urlencode(params)
            signature = hmac.new(self.secret, query.encode(), hashlib.sha256).hexdigest()
            query = f"{query}&signature={signature}"
        else:
            query = urllib.parse.urlencode(params)

        url = f"{self.host}{path}"
        data = None
        if method == "GET":
            if query:
                url = f"{url}?{query}"
        else:
            data = query.encode()

        req = urllib.request.Request(url, data=data, method=method,
                                     headers={"X-MBX-APIKEY": self.key})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode())
                message = f"{detail.get('code')}: {detail.get('msg')}"
            except Exception:
                message = exc.reason
            raise BrokerError(f"Binance {method} {path}: {message}") from exc
        except urllib.error.URLError as exc:
            raise BrokerError(f"Binance unreachable: {exc.reason}") from exc

    # -- lifecycle ---------------------------------------------------------

    def connect(self) -> None:
        info = self._request("GET", "/fapi/v1/exchangeInfo")
        for s in info.get("symbols", []):
            filters = {f["filterType"]: f for f in s.get("filters", [])}
            self._filters[s["symbol"]] = {
                "step": float(filters.get("LOT_SIZE", {}).get("stepSize", 0.001)),
                "min": float(filters.get("LOT_SIZE", {}).get("minQty", 0.001)),
                "max": float(filters.get("LOT_SIZE", {}).get("maxQty", 1e9)),
                "tick": float(filters.get("PRICE_FILTER", {}).get("tickSize", 0.01)),
                "precision": int(s.get("quantityPrecision", 3)),
                "price_precision": int(s.get("pricePrecision", 2)),
            }
        self._connected = True
        balance = self.balance()
        log.info("Binance Futures connected (%s): balance %.2f USDT, %d symbols",
                 "TESTNET" if self.testnet else "LIVE", balance, len(self._filters))

    def disconnect(self) -> None:
        self._connected = False

    def _require(self) -> None:
        if not self._connected:
            raise BrokerError("Not connected to Binance")

    def _filter(self, symbol: str) -> dict:
        f = self._filters.get(symbol.upper())
        if f is None:
            raise BrokerError(
                f"Symbol {symbol} not found on Binance Futures. "
                f"Names look like BTCUSDT, ETHUSDT.")
        return f

    # -- account -------------------------------------------------------------

    def _account(self) -> dict:
        self._require()
        return self._request("GET", "/fapi/v2/account", signed=True)

    def balance(self) -> float:
        for asset in self._account().get("assets", []):
            if asset.get("asset") == "USDT":
                return float(asset.get("walletBalance", 0))
        return 0.0

    def equity(self) -> float:
        for asset in self._account().get("assets", []):
            if asset.get("asset") == "USDT":
                return float(asset.get("marginBalance", asset.get("walletBalance", 0)))
        return 0.0

    # -- market data -----------------------------------------------------------

    def bars(self, symbol: str, timeframe: str, count: int) -> list[Bar]:
        self._require()
        interval = _INTERVAL.get(timeframe)
        if interval is None:
            raise BrokerError(f"Unsupported timeframe {timeframe}")
        rows = self._request("GET", "/fapi/v1/klines", {
            "symbol": symbol.upper(), "interval": interval,
            "limit": min(count, 1500),
        })
        if not rows:
            raise BrokerError(f"No bars for {symbol}")
        return [Bar(int(r[0] // 1000), float(r[1]), float(r[2]),
                    float(r[3]), float(r[4])) for r in rows]

    # -- trading ------------------------------------------------------------------

    def market_order(self, symbol: str, side: str, volume: float,
                     sl: float, tp: float, comment: str = "") -> OrderReceipt:
        self._require()
        symbol = symbol.upper()
        f = self._filter(symbol)
        qty = self._round_qty(symbol, volume)
        if qty <= 0:
            raise BrokerError(f"Quantity {volume} rounds to 0 for {symbol}")
        binance_side = "BUY" if side == "buy" else "SELL"
        opposite = "SELL" if side == "buy" else "BUY"

        entry = self._request("POST", "/fapi/v1/order", {
            "symbol": symbol, "side": binance_side,
            "type": "MARKET", "quantity": qty,
        }, signed=True)
        order_id = int(entry.get("orderId", 0))
        fill_price = float(entry.get("avgPrice") or 0) or self._mark_price(symbol)

        # Attach exits. closePosition=true so they always close the whole
        # position and cannot be left dangling at the wrong size.
        for order_type, stop in (("STOP_MARKET", sl), ("TAKE_PROFIT_MARKET", tp)):
            try:
                self._request("POST", "/fapi/v1/order", {
                    "symbol": symbol, "side": opposite, "type": order_type,
                    "stopPrice": self._round_price(symbol, stop),
                    "closePosition": "true", "workingType": "MARK_PRICE",
                }, signed=True)
            except BrokerError as exc:
                log.error("%s attach failed for %s: %s — closing the position "
                          "rather than leaving it unprotected.", order_type, symbol, exc)
                try:
                    self.close_position(order_id, symbol=symbol)
                except Exception:
                    log.exception("Could not close unprotected position on %s!", symbol)
                raise

        return OrderReceipt(ticket=order_id, symbol=symbol, side=side,
                            volume=qty, price=fill_price,
                            sl=self._round_price(symbol, sl),
                            tp=self._round_price(symbol, tp))

    def positions(self, symbol: Optional[str] = None) -> list[Position]:
        self._require()
        rows = self._request("GET", "/fapi/v2/positionRisk", signed=True)
        out = []
        for p in rows:
            amount = float(p.get("positionAmt", 0))
            if amount == 0:
                continue
            if symbol and p["symbol"].upper() != symbol.upper():
                continue
            out.append(Position(
                ticket=0,                       # Binance keys positions by symbol
                symbol=p["symbol"],
                side="buy" if amount > 0 else "sell",
                volume=abs(amount),
                entry_price=float(p.get("entryPrice", 0)),
                sl=0.0, tp=0.0,
                profit=float(p.get("unRealizedProfit", 0)),
            ))
        return out

    def close_position(self, ticket: int, symbol: Optional[str] = None) -> float:
        """Binance identifies positions by symbol, so pass `symbol`."""
        self._require()
        candidates = self.positions(symbol)
        if not candidates:
            raise BrokerError(f"No open position for {symbol or ticket}")
        pos = candidates[0]
        profit = pos.profit
        self._request("POST", "/fapi/v1/order", {
            "symbol": pos.symbol,
            "side": "SELL" if pos.side == "buy" else "BUY",
            "type": "MARKET", "quantity": self._round_qty(pos.symbol, pos.volume),
            "reduceOnly": "true",
        }, signed=True)
        # cancel the now-orphaned stop/target orders
        try:
            self._request("DELETE", "/fapi/v1/allOpenOrders",
                          {"symbol": pos.symbol}, signed=True)
        except BrokerError:
            log.warning("Could not cancel remaining orders on %s", pos.symbol)
        return profit

    # -- sizing ---------------------------------------------------------------------

    def volume_for_risk(self, symbol: str, sl_distance: float, risk_amount: float) -> float:
        """Quantity such that hitting the stop loses ~risk_amount USDT.

        Quote currency is USDT, so 1.0 of price movement per 1 unit = 1 USDT.
        """
        self._require()
        if sl_distance <= 0:
            raise BrokerError("sl_distance must be > 0")
        return self._round_qty(symbol, risk_amount / sl_distance)

    def volume_from_lots(self, symbol: str, lots: float) -> float:
        """There are no 'lots' on Binance — 1 lot is treated as 1 coin."""
        return self._round_qty(symbol, lots)

    def _round_qty(self, symbol: str, qty: float) -> float:
        f = self._filter(symbol)
        step = f["step"] or 0.001
        qty = max(f["min"], min(f["max"], float(qty)))
        return round(round(qty / step) * step, f["precision"])

    def _round_price(self, symbol: str, price: float) -> float:
        f = self._filter(symbol)
        tick = f["tick"] or 0.01
        return round(round(price / tick) * tick, f["price_precision"])

    def _mark_price(self, symbol: str) -> float:
        data = self._request("GET", "/fapi/v1/premiumIndex", {"symbol": symbol.upper()})
        return float(data.get("markPrice", 0))
