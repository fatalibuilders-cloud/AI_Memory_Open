"""tgscalper — copy trade signals from your own Telegram groups to your broker.

Layout:
    parser.py    text -> Signal
    symbols.py   "GOLD" -> the symbol your broker actually lists
    risk.py      sizing and the pre-trade guards
    brokers/     execution adapters (paper by default, MetaTrader 5 for live)
    journal.py   SQLite audit trail and follow-up bookkeeping
    engine.py    message -> decision -> orders
    listener.py  Telethon client for your account
    cli.py       command line entry points
"""

__version__ = "0.1.0"
