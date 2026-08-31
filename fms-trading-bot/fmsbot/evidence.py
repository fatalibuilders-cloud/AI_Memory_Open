"""Does this configuration actually make money? Keep score, and act on it.

The bot's own history is the argument for this file. Over 139 real trades
it won 21.6% of the time against a 42.9% chance rate — z = -5.07, a
one-in-two-million result — and lost $46.28. The evidence that it was
losing was conclusive long before trade 139, and nothing was watching.

So this keeps a running record of every closed trade and applies one
question to it: could a strategy with no edge at all have produced this?
When the answer is "not plausibly, and it is losing", trading stops. When
the answer is "not plausibly, and it is winning", the configuration has
earned the right to be considered.

The record is keyed to a fingerprint of the settings that produced it.
Change the strategy, the timeframe or the exits and the scoring starts
again, because results from a different configuration are not evidence
about this one.
"""

from __future__ import annotations

import json
import logging
import math
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

log = logging.getLogger("fmsbot.evidence")

PROVING = "proving"
PASSED = "passed"
FAILED = "failed"


def _phi(z: float) -> float:
    """P(Z <= z) for a standard normal, without a numerics dependency."""
    return 0.5 * math.erfc(-z / math.sqrt(2.0))


@dataclass
class Evidence:
    """A running, persisted record of what one configuration really did."""

    fingerprint: str = ""
    pnls: list[float] = field(default_factory=list)
    started: float = field(default_factory=time.time)
    #: Verdict already announced, so a halt is reported once, not every loop.
    announced: str = ""

    #: Below this many trades no verdict is possible. 30 is the point where
    #: the normal approximation behind the test starts to hold.
    min_trades: int = 30
    #: Deliberately stricter than the usual 0.05. The test is applied after
    #: every trade, and repeated looks at growing data find "significance"
    #: by chance far more often than a single look does.
    alpha: float = 0.01

    path: Optional[Path] = None

    # -- persistence -----------------------------------------------------

    @classmethod
    def load(cls, path: str | Path, fingerprint: str,
             min_trades: int = 30, alpha: float = 0.01) -> "Evidence":
        p = Path(path)
        ev = cls(fingerprint=fingerprint, path=p,
                 min_trades=min_trades, alpha=alpha)
        if not p.is_file():
            return ev
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            log.warning("Could not read %s (%s) — scoring starts fresh", p, exc)
            return ev
        if data.get("fingerprint") != fingerprint:
            log.info("Settings changed since the last record — scoring restarts. "
                     "Results from a different configuration are not evidence "
                     "about this one.")
            return ev
        ev.pnls = [float(x) for x in data.get("pnls", [])]
        ev.started = float(data.get("started", ev.started))
        ev.announced = str(data.get("announced", ""))
        return ev

    def save(self) -> None:
        if not self.path:
            return
        try:
            self.path.write_text(json.dumps({
                "fingerprint": self.fingerprint,
                "pnls": self.pnls,
                "started": self.started,
                "announced": self.announced,
            }), encoding="utf-8")
        except OSError as exc:
            log.warning("Could not save the trade record: %s", exc)

    def reset(self) -> None:
        self.pnls, self.started, self.announced = [], time.time(), ""
        self.save()

    # -- recording -------------------------------------------------------

    def record(self, pnl: float) -> None:
        self.pnls.append(float(pnl))
        self.save()

    # -- statistics ------------------------------------------------------

    @property
    def count(self) -> int:
        return len(self.pnls)

    @property
    def wins(self) -> list[float]:
        return [p for p in self.pnls if p > 0]

    @property
    def gross_profit(self) -> float:
        return sum(self.wins)

    @property
    def gross_loss(self) -> float:
        return -sum(p for p in self.pnls if p <= 0)

    @property
    def net(self) -> float:
        return sum(self.pnls)

    @property
    def win_rate(self) -> float:
        return 100.0 * len(self.wins) / self.count if self.pnls else 0.0

    @property
    def profit_factor(self) -> float:
        loss = self.gross_loss
        if loss <= 0:
            return float("inf") if self.gross_profit > 0 else 0.0
        return self.gross_profit / loss

    @property
    def mean(self) -> float:
        return self.net / self.count if self.pnls else 0.0

    @property
    def stdev(self) -> float:
        if self.count < 2:
            return 0.0
        m = self.mean
        return math.sqrt(sum((p - m) ** 2 for p in self.pnls) / (self.count - 1))

    @property
    def z(self) -> float:
        """How many standard errors the average trade sits from zero.

        Zero is the honest null: a strategy with no edge, after costs,
        averages nothing per trade. Profit factor says which side of the
        line the record falls on; this says whether the distance is more
        than the noise in a sample this size.
        """
        if self.count < 2:
            return 0.0
        sd = self.stdev
        # A bot with fixed cash exits can close many trades at identical
        # amounts, leaving a spread of essentially zero. The ratio then
        # explodes on floating-point dust rather than on evidence, so treat
        # a negligible spread as the certainty it really is and keep the
        # number in a range that means something when printed.
        if sd <= max(abs(self.mean), 1e-12) * 1e-9:
            return 0.0 if self.mean == 0 else math.copysign(99.0, self.mean)
        return max(-99.0, min(99.0, self.mean / (sd / math.sqrt(self.count))))

    # -- judgement -------------------------------------------------------

    def verdict(self) -> str:
        if self.count < self.min_trades:
            return PROVING
        z = self.z
        if _phi(z) < self.alpha and self.profit_factor < 1.0:
            return FAILED
        if (1.0 - _phi(z)) < self.alpha and self.profit_factor > 1.0:
            return PASSED
        return PROVING

    def explain(self) -> str:
        """The record in full, for /evidence on the phone."""
        if not self.pnls:
            return ("No closed trades recorded yet for these settings.\n"
                    "Scoring begins with the first one.")
        v = self.verdict()
        pf = self.profit_factor
        pf_text = "inf" if pf == float("inf") else f"{pf:.2f}"
        days = max((time.time() - self.started) / 86400.0, 0.01)
        lines = [
            f"{self.count} trades over {days:.1f} days",
            f"net {self.net:+.2f}, profit factor {pf_text}",
            f"win rate {self.win_rate:.1f}% ({len(self.wins)} of {self.count})",
            f"average trade {self.mean:+.4f}",
        ]
        if self.count >= 2:
            lines.append(f"z {self.z:+.2f} against a zero-edge null")
        if v == PROVING and self.count < self.min_trades:
            lines.append(f"\nSTILL PROVING — {self.min_trades - self.count} more "
                         f"trades before a verdict is possible.")
        elif v == PROVING:
            lines.append("\nSTILL PROVING — the result so far is within what "
                         "no edge at all would produce. That is not a pass.")
        elif v == FAILED:
            lines.append(f"\nFAILED — this configuration is losing by more than "
                         f"chance explains (p < {self.alpha}). Trading is halted.")
        else:
            lines.append(f"\nPASSED — profitable by more than chance explains "
                         f"(p < {self.alpha}). That earns a demo, not confidence.")
        return "\n".join(lines)


def fingerprint(settings, strategy_name: str) -> str:
    """Identify the configuration a record belongs to.

    Only the settings that change what a trade IS are included. Changing
    the Telegram password or the log level must not throw away a record;
    changing the strategy or the exits must.
    """
    parts = [
        strategy_name, settings.timeframe, settings.entry_mode,
        settings.ema_fast, settings.ema_slow, settings.rsi_period,
        settings.atr_period, settings.atr_sl_mult, settings.atr_tp_mult,
        settings.tp_money, settings.sl_money, settings.tp_runner_money,
        settings.entry_confirm_money,
        settings.trail_atr_mult, settings.trail_start_money,
        sorted(settings.symbol_overrides.items()),
    ]
    return "|".join(str(p) for p in parts)
