"""Causal Donchian / Turtle-style breakout on 1-minute ETH bars.

Entry channel: 180 bars (3 hours). Exit channel: 90 bars (90 minutes).
The 2:1 entry/exit ratio is the classic Turtle shape, scaled to a 24-hour
one-minute tape so the lookback is long enough to ignore 1-minute noise
and short enough to react inside the sample.

Positions are decided at bar i's close using only bars 0..i. The replay
engine fills a position change at bar i+1's open (no phantom fills, no
same-bar lookahead).
"""

from __future__ import annotations

from collections import deque
from typing import Iterable, Mapping, Sequence


ENTRY_WINDOW = 180
EXIT_WINDOW = 90


def _rows(bars) -> list[dict]:
    if isinstance(bars, str):
        import csv
        with open(bars, newline="") as f:
            return list(csv.DictReader(f))
    if hasattr(bars, "to_dict"):
        # pandas.DataFrame
        return bars.to_dict("records")
    return list(bars)


def _num(row: Mapping, *names: str) -> float:
    for n in names:
        if n in row and row[n] not in (None, ""):
            return float(row[n])
        if n.title() in row and row[n.title()] not in (None, ""):
            return float(row[n.title()])
    raise KeyError(f"missing field {names}")


def generate_positions(bars: Iterable) -> list[int]:
    """Return target lots in {-1, 0, +1} for each bar.

    positions[i] is decided from data through bar i inclusive (close,
    and the high/low channels of the prior windows). It should be filled
    on the next bar.
    """
    rows = _rows(bars)
    n = len(rows)
    highs = [_num(r, "high") for r in rows]
    lows = [_num(r, "low") for r in rows]
    closes = [_num(r, "close") for r in rows]

    # Rolling prior-window max high / min low, excluding the current bar.
    def prior_channel(window: int):
        max_prev = [None] * n
        min_prev = [None] * n
        qmax: deque = deque()
        qmin: deque = deque()
        for i in range(n):
            # channel at i uses bars [i-window, i) once i>=window
            if i >= window:
                max_prev[i] = highs[qmax[0]] if qmax else max(highs[i - window : i])
                min_prev[i] = lows[qmin[0]] if qmin else min(lows[i - window : i])
            # push bar i so it is visible to future bars, not to i itself
            while qmax and highs[qmax[-1]] <= highs[i]:
                qmax.pop()
            qmax.append(i)
            while qmax and qmax[0] <= i - window:
                qmax.popleft()
            while qmin and lows[qmin[-1]] >= lows[i]:
                qmin.pop()
            qmin.append(i)
            while qmin and qmin[0] <= i - window:
                qmin.popleft()
        return max_prev, min_prev

    entry_hh, entry_ll = prior_channel(ENTRY_WINDOW)
    exit_hh, exit_ll = prior_channel(EXIT_WINDOW)

    pos = 0
    out: list[int] = []
    for i in range(n):
        hh_e, ll_e = entry_hh[i], entry_ll[i]
        if hh_e is None or ll_e is None:
            pos = 0
            out.append(0)
            continue
        c = closes[i]
        if c > hh_e:
            pos = 1
        elif c < ll_e:
            pos = -1
        else:
            hh_x, ll_x = exit_hh[i], exit_ll[i]
            if pos == 1 and ll_x is not None and c < ll_x:
                pos = 0
            elif pos == -1 and hh_x is not None and c > hh_x:
                pos = 0
        out.append(pos)
    return out


# Aliases the sandbox might import.
positions = generate_positions
run = generate_positions


if __name__ == "__main__":
    import os
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "bars.csv")
    pos = generate_positions(path)
    for i, p in enumerate(pos):
        print(f"{i},{p}")
