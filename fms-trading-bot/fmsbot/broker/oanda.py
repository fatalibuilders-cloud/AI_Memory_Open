"""OANDA v20 REST adapter — runs on Linux, Mac and Windows (no MT5 needed).

Covers forex pairs and spot metals (XAU_USD gold, XAG_USD silver); OANDA
does not offer stocks — use the MT5 broker for stock CFDs.

Setup:
  1. Open a free demo ("practice") account at oanda.com.
  2. Account portal -> Manage API Access -> generate a personal token.
  3. .env: BROKER=oanda, OANDA_API_TOKEN=..., OANDA_ACCOUNT_ID=xxx-xxx-xxxxxxx-xxx,
     OANDA_ENV=practice   (switch to "live" only after weeks of demo).

Symbols may be written either OANDA-style (EUR_USD, XAU_USD) or MT5-style
(EURUSD, XAUUSD) — they are normalized automatically.
"""

from __future__ import annotations

import calendar
import json
import logging
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Optional

from .base import Bar, Broker, BrokerError, OrderReceipt, Position

log = logging.getLogger("fmsbot.oanda")

HOSTS = {
    "practice": "https://api-fxpractice.oanda.com",
    "live": "https://api-fxtrade.oanda.com",
}
_GRANULARITY = {"M1": "M1", "M5": "M5", "M15": "M15", "M30": "M30",
                "H1": "H1", "H4": "H4", "D1": "D"}


def normalize_symbol(symbol: str) -> str:
    """EURUSD -> EUR_USD, XAUUSD -> XAU_USD; already-underscored names pass through."""
    s = symbol.upper().strip()
    if "_" in s:
        return s
    if len(s) == 6:
        return f"{s[:3]}_{s[3:]}"
    return s


def _parse_time(rfc3339: str) -> int:
    # OANDA returns e.g. "2026-07-18T12:34:56.000000000Z" (nanoseconds)
    return calendar.timegm(time.strptime(rfc3339[:19], "%Y-%m-%dT%H:%M:%S"))


class OandaBroker(Broker):
    def __init__(self, token: str, account_id: str, environment: str = "practice"):
        if environment not in HOSTS:
            raise BrokerError(f"OANDA_ENV must be practice or live, got {environment!r}")
        self.host = HOSTS[environment]
        self.environment = environment
        self.token = token
        self.account_id = account_id
        self.currency = "USD"
        self._instruments: dict[str, dict] = {}
        self._connected = False

    # -- HTTP -----------------------------------------------------------

    def _request(self, method: str, path: str, params: Optional[dict] = None,
                 body: Optional[dict] = None) -> dict:
        url = self.host + path
        if params:
            url += "?" + urllib.parse.urlencode(params)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
        })
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            try:
                detail = json.loads(exc.read().decode())
                message = detail.get("errorMessage") or detail
            except Exception:
                message = exc.reason
            raise BrokerError(f"OANDA {method} {path}: {exc.code} {message}") from exc
        except urllib.error.URLError as exc:
            raise BrokerError(f"OANDA unreachable: {exc.reason}") from exc

    # -- lifecycle ------------------------------------------------------------

    def connect(self) -> None:
        summary = self._request("GET", f"/v3/accounts/{self.account_id}/summary")["account"]
        self.currency = summary.get("currency", "USD")
        instruments = self._request(
            "GET", f"/v3/accounts/{self.account_id}/instruments").get("instruments", [])
        self._instruments = {i["name"]: i for i in instruments}
        self._connected = True
        log.info("OANDA connected: account %s (%s), balance %.2f %s, %d instruments%s",
                 self.account_id, self.environment, float(summary["balance"]),
                 self.currency, len(self._instruments),
                 " [PRACTICE]" if self.environment == "practice" else " [LIVE]")

    def disconnect(self) -> None:
        self._connected = False

    def _require(self) -> None:
        if not self._connected:
            raise BrokerError("Not connected to OANDA")

    def _instrument(self, symbol: str) -> dict:
        name = normalize_symbol(symbol)
        info = self._instruments.get(name)
        if info is None:
            raise BrokerError(
                f"Instrument {name} not available on this OANDA account "
                f"(check the symbol; stocks are not offered by OANDA)")
        return info

    # -- account ----------------------------------------------------------------

    def _summary(self) -> dict:
        self._require()
        return self._request("GET", f"/v3/accounts/{self.account_id}/summary")["account"]

    def balance(self) -> float:
        return float(self._summary()["balance"])

    def equity(self) -> float:
        return float(self._summary()["NAV"])

    # -- market data ---------------------------------------------------------------

    def bars(self, symbol: str, timeframe: str, count: int) -> list[Bar]:
        self._require()
        gran = _GRANULARITY.get(timeframe)
        if gran is None:
            raise BrokerError(f"Unsupported timeframe {timeframe}")
        name = normalize_symbol(symbol)
        data = self._request("GET", f"/v3/instruments/{name}/candles", params={
            "granularity": gran, "count": min(count, 5000), "price": "M",
        })
        bars = []
        for c in data.get("candles", []):
            mid = c["mid"]
            bars.append(Bar(_parse_time(c["time"]), float(mid["o"]), float(mid["h"]),
                            float(mid["l"]), float(mid["c"])))
        if not bars:
            raise BrokerError(f"No bars for {name}")
        return bars

    # -- trading ----------------------------------------------------------------------

    def market_order(self, symbol: str, side: str, volume: float,
                     sl: float, tp: float, comment: str = "") -> OrderReceipt:
        self._require()
        info = self._instrument(symbol)
        name = info["name"]
        precision = int(info.get("displayPrecision", 5))
        units = int(round(volume)) if side == "buy" else -int(round(volume))
        if units == 0:
            raise BrokerError("Volume rounds to 0 units")
        body = {"order": {
            "type": "MARKET",
            "instrument": name,
            "units": str(units),
            "timeInForce": "FOK",
            "positionFill": "DEFAULT",
            "stopLossOnFill": {"price": f"{sl:.{precision}f}"},
            "takeProfitOnFill": {"price": f"{tp:.{precision}f}"},
        }}
        resp = self._request("POST", f"/v3/accounts/{self.account_id}/orders", body=body)
        fill = resp.get("orderFillTransaction")
        if not fill:
            reject = resp.get("orderRejectTransaction") or resp.get("orderCancelTransaction") or {}
            raise BrokerError(f"Order rejected: {reject.get('reason', resp)}")
        trade_id = int(fill.get("tradeOpened", {}).get("tradeID", fill.get("id", 0)))
        return OrderReceipt(
            ticket=trade_id, symbol=name, side=side,
            volume=abs(float(fill["units"])), price=float(fill["price"]),
            sl=float(body["order"]["stopLossOnFill"]["price"]),
            tp=float(body["order"]["takeProfitOnFill"]["price"]),
        )

    def current_price(self, symbol: str, side: str) -> float:
        self._require()
        name = normalize_symbol(symbol)
        data = self._request("GET", f"/v3/accounts/{self.account_id}/pricing",
                             params={"instruments": name})
        prices = data.get("prices") or []
        if not prices:
            raise BrokerError(f"No pricing for {name}")
        book = prices[0]
        quotes = book.get("asks" if side == "buy" else "bids") or []
        if quotes:
            return float(quotes[0]["price"])
        # fall back to the mid if the book side is empty
        return float(book.get("closeoutAsk" if side == "buy" else "closeoutBid", 0))

    def positions(self, symbol: Optional[str] = None) -> list[Position]:
        self._require()
        trades = self._request(
            "GET", f"/v3/accounts/{self.account_id}/openTrades").get("trades", [])
        wanted = normalize_symbol(symbol) if symbol else None
        out = []
        for t in trades:
            if wanted and t["instrument"] != wanted:
                continue
            units = float(t["currentUnits"])
            out.append(Position(
                ticket=int(t["id"]), symbol=t["instrument"],
                side="buy" if units > 0 else "sell", volume=abs(units),
                entry_price=float(t["price"]),
                sl=float(t.get("stopLossOrder", {}).get("price", 0) or 0),
                tp=float(t.get("takeProfitOrder", {}).get("price", 0) or 0),
                profit=float(t.get("unrealizedPL", 0) or 0),
            ))
        return out

    def close_position(self, ticket: int) -> float:
        self._require()
        resp = self._request(
            "PUT", f"/v3/accounts/{self.account_id}/trades/{ticket}/close",
            body={"units": "ALL"})
        fill = resp.get("orderFillTransaction", {})
        return float(fill.get("pl", 0) or 0)

    # -- sizing --------------------------------------------------------------------------

    def volume_from_lots(self, symbol: str, lots: float) -> float:
        """OANDA trades in units: 1 standard lot = 100,000 units."""
        self._require()
        info = self._instrument(symbol)
        units = float(lots) * 100_000.0
        units = max(units, float(info.get("minimumTradeSize", 1)))
        units = min(units, float(info.get("maximumOrderUnits", 1e9)))
        return float(int(units))

    def volume_for_risk(self, symbol: str, sl_distance: float, risk_amount: float) -> float:
        """Units such that hitting the SL loses ~risk_amount (account currency).

        Loss = units * sl_distance * (quote currency -> account currency rate).
        """
        self._require()
        if sl_distance <= 0:
            raise BrokerError("sl_distance must be > 0")
        info = self._instrument(symbol)
        name = info["name"]
        quote = name.split("_")[-1]
        rate = self._quote_to_account_rate(quote)
        units = risk_amount / (sl_distance * rate)
        min_size = float(info.get("minimumTradeSize", 1))
        units = max(units, min_size)
        max_units = float(info.get("maximumOrderUnits", 1e9))
        return float(int(min(units, max_units)))

    def _quote_to_account_rate(self, quote: str) -> float:
        if quote == self.currency:
            return 1.0
        direct = f"{quote}_{self.currency}"      # e.g. JPY account? quote USD -> USD_JPY
        inverse = f"{self.currency}_{quote}"
        try:
            if direct in self._instruments:
                return self.bars(direct, "M1", 1)[-1].close
            if inverse in self._instruments:
                price = self.bars(inverse, "M1", 1)[-1].close
                return 1.0 / price if price else 1.0
        except BrokerError:
            pass
        log.warning("No conversion pair for %s->%s; sizing assumes rate 1.0",
                    quote, self.currency)
        return 1.0
