"""Pocket Option auto-trading bot.

Connects to Pocket Option's WebSocket platform feed (the same one the
web app uses), streams live prices, runs a signal strategy over candles
and places binary-option trades with strict risk management.

Pocket Option has NO official public API. This client speaks the
socket.io-style protocol used by the web platform and authenticates with
the session string (SSID) captured from a logged-in browser session.
The protocol can change at any time and automated trading may violate
Pocket Option's terms of service — use at your own risk, and always
validate on a demo account first.
"""

__version__ = "0.1.0"
