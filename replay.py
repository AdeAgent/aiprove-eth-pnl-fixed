"""Replay a position series with next-bar open fills, taker fees, and size-scaled slippage."""

from __future__ import annotations

import csv
import math
import os
import sys
from typing import Sequence

from costs import LOT_ETH, SLIP_CAP, SLIP_COEFF, TAKER_FEE


def load_bars(path: str) -> list[dict]:
    with open(path, newline="") as f:
        rows = list(csv.DictReader(f))
    for r in rows:
        for k in ("minute", "open", "high", "low", "close", "volume"):
            r[k] = float(r[k])
    return rows


def replay(bars: Sequence[dict], targets: Sequence[float], lot: float = LOT_ETH) -> dict:
    if len(targets) != len(bars):
        raise ValueError(f"positions ({len(targets)}) != bars ({len(bars)})")
    cash = 0.0
    pos = 0.0
    fees = 0.0
    slip_cost = 0.0
    trades = 0
    equity = []
    for i, bar in enumerate(bars):
        if i >= 1:
            desired = float(targets[i - 1]) * lot
            dq = desired - pos
            if abs(dq) > 1e-12:
                vol = max(float(bar["volume"]), 1e-9)
                slip = min(SLIP_COEFF * abs(dq) / vol, SLIP_CAP)
                fill = float(bar["open"]) * (1.0 + math.copysign(slip, dq))
                fee = TAKER_FEE * abs(dq) * fill
                cash -= dq * fill + fee
                fees += fee
                slip_cost += abs(dq) * float(bar["open"]) * slip
                pos += dq
                trades += 1
        eq = cash + pos * float(bar["close"])
        equity.append(eq)
    peak = -1e300
    max_dd = 0.0
    for eq in equity:
        if eq > peak:
            peak = eq
        dd = eq - peak
        if dd < max_dd:
            max_dd = dd
    return {
        "net_pnl": equity[-1] if equity else 0.0,
        "max_drawdown": max_dd,
        "fees": fees,
        "slip_cost": slip_cost,
        "trades": trades,
        "final_position": pos,
        "equity": equity,
    }


def slice_pnl(equity: Sequence[float], start: int, end: int) -> float:
    prev = 0.0 if start == 0 else equity[start - 1]
    return equity[end - 1] - prev


def main() -> None:
    root = os.path.dirname(os.path.abspath(__file__))
    path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(root, "bars.csv")
    sys.path.insert(0, root)
    from strategy import generate_positions

    bars = load_bars(path)
    pos = generate_positions(bars)
    r = replay(bars, pos)
    n = len(bars)
    print(f"bars              {n}")
    print(f"net_pnl_after_costs {r['net_pnl']:.4f} USDT")
    print(f"max_drawdown      {r['max_drawdown']:.4f} USDT")
    print(f"fees              {r['fees']:.4f} USDT")
    print(f"slip_cost         {r['slip_cost']:.4f} USDT")
    print(f"trades            {r['trades']}")
    print(f"final_position    {r['final_position']}")
    print(f"first_75_pnl      {slice_pnl(r['equity'], 0, 1080):.4f} USDT")
    print(f"last_25_pnl       {slice_pnl(r['equity'], 1080, n):.4f} USDT")
    print(f"last_17_pnl       {slice_pnl(r['equity'], 1200, n):.4f} USDT")
    # trade log
    prev = 0
    print("trades:")
    for i, p in enumerate(pos):
        if i == 0:
            continue
        if pos[i - 1] != prev:
            # filled at this bar open
            print(f"  fill_bar={i} minute={int(bars[i]['minute'])} open={bars[i]['open']:.2f} "
                  f"{prev:+d} -> {pos[i-1]:+d}")
            prev = pos[i - 1]


if __name__ == "__main__":
    main()
