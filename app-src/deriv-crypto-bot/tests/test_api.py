"""Tests for the API client's error translation and rate limiter.

The connect-failure tests exist because a real run behind a rejecting proxy
produced an uncaught traceback: `websockets` raises its own exception
hierarchy, and neither the trader's reconnect loop nor the preflight check
handled it. Everything that can fail while opening the socket is now
translated to ConnectionLost at this boundary.
"""

import asyncio

import pytest
from websockets.exceptions import (
    ConnectionClosedError,
    InvalidHandshake,
    InvalidURI,
    WebSocketException,
)

from deriv_bot.api import ConnectionLost, DerivAPI, DerivError, RateLimiter, _redact

from conftest import make_config


class ProxyRejected(WebSocketException):
    """Stands in for websockets.InvalidProxyStatus, which varies by version."""

    def __str__(self) -> str:
        return "proxy rejected connection: HTTP 403"


class TestConnectFailures:
    def connect_raising(self, monkeypatch, error):
        api = DerivAPI(make_config())

        async def boom(*args, **kwargs):
            raise error

        monkeypatch.setattr("deriv_bot.api.ws_connect", boom)
        return api

    @pytest.mark.parametrize(
        "error",
        [
            ProxyRejected(),
            InvalidURI("wss://bad", "nope"),
            InvalidHandshake("bad handshake"),
            OSError("name resolution failed"),
            ConnectionRefusedError("refused"),
        ],
    )
    def test_socket_errors_become_connection_lost(self, monkeypatch, error):
        api = self.connect_raising(monkeypatch, error)
        with pytest.raises(ConnectionLost):
            asyncio.run(api.connect())

    def test_the_original_cause_is_preserved(self, monkeypatch):
        api = self.connect_raising(monkeypatch, ProxyRejected())
        with pytest.raises(ConnectionLost) as info:
            asyncio.run(api.connect())
        assert isinstance(info.value.__cause__, WebSocketException)
        assert "proxy" in str(info.value).lower()

    def test_no_socket_is_left_behind_after_a_failure(self, monkeypatch):
        api = self.connect_raising(monkeypatch, ProxyRejected())
        with pytest.raises(ConnectionLost):
            asyncio.run(api.connect())
        assert not api.connected


class TestSendGuards:
    def test_send_without_a_connection_raises(self):
        api = DerivAPI(make_config())
        with pytest.raises(ConnectionLost, match="not connected"):
            asyncio.run(api.send({"ping": 1}))

    def test_close_is_safe_when_never_connected(self):
        asyncio.run(DerivAPI(make_config()).close())  # must not raise


class TestErrorTranslation:
    def test_deriv_error_carries_code_and_message(self):
        error = DerivError("InvalidToken", "token is invalid")
        assert error.code == "InvalidToken"
        assert "InvalidToken" in str(error)
        assert "token is invalid" in str(error)


class TestRedaction:
    def test_authorize_token_is_masked(self):
        assert _redact({"authorize": "secret"})["authorize"] == "***"

    def test_other_fields_are_untouched(self):
        assert _redact({"ticks_history": "cryBTCUSD"})["ticks_history"] == "cryBTCUSD"

    def test_nothing_secret_survives(self):
        redacted = _redact({"authorize": "sk-live-123", "api_token": "sk-live-123"})
        assert "sk-live-123" not in str(redacted)


class TestRateLimiter:
    def test_allows_a_burst_up_to_capacity(self):
        async def run():
            limiter = RateLimiter(rate=1000, capacity=5)
            for _ in range(5):
                await limiter.acquire()

        asyncio.run(asyncio.wait_for(run(), timeout=1.0))

    def test_throttles_beyond_capacity(self):
        async def run():
            limiter = RateLimiter(rate=50, capacity=1)
            loop = asyncio.get_running_loop()
            start = loop.time()
            await limiter.acquire()
            await limiter.acquire()  # must wait ~1/50s for a token
            return loop.time() - start

        assert asyncio.run(run()) > 0.01
