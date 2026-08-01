"""FMS bot — Forex / Metals / Stocks auto-trader with a Telegram phone remote.

Architecture:
    phone (Telegram app) <-> Telegram Bot API <-> this bot <-> broker (MetaTrader 5)

The bot runs 24/7 on a PC / VPS next to a MetaTrader 5 terminal and trades
an EMA-crossover strategy with ATR-based stops and strict risk limits.
Your phone is the remote control: log in with a password, then start,
pause, monitor and close positions from anywhere.
"""

__version__ = "0.1.0"
