# eth-pnl-fixed

Strategy for the AIProve `eth-pnl-fixed` bounty: net PnL after costs on the
frozen ETH/USDT 1-minute tape (`bars.csv`, 1,440 bars ending 2026-11-13 12:17 UTC).

## Strategy

A Turtle-style Donchian breakout, causal only:

- **Enter** when the close breaks the prior **180-bar** (3 hour) high or low.
- **Exit to flat** when the close breaks the prior **90-bar** opposite channel.
- The 2:1 entry/exit ratio is the classic Turtle shape, scaled to a 24-hour
  one-minute tape so the lookback ignores 1-minute noise but can still turn
  inside the day.
- Target position is in `{-1, 0, +1}` lots of 1 ETH.

Signals at bar `i` use data through that bar's close. Fills are at **bar `i+1`
open** (no same-bar or phantom fills).

This is not a short-and-hold on a down day. That beats the full sample slightly
but loses on the last six hours (the bounce). This rule is long early, short
through the midday dump, flat, then long again into the bounce.

## Cost model (local scoring)

The official README does not publish numeric fee or slippage constants. Local
replay uses, and documents:

| Parameter | Default | Meaning |
|-----------|---------|---------|
| `TAKER_FEE` | 10 bps | All fills are market orders at the next open |
| `MAKER_FEE` | 8 bps | Not used (no resting limits in this entry) |
| `SLIP_COEFF` | 0.10 | Slippage fraction = `0.10 * \|qty\| / bar_volume`, capped at 5% |

Net PnL is marked at close, in USDT, for a 1 ETH lot.

## Local results (default costs, 13 Nov 2026)

| Slice | Net PnL after costs | Notes |
|-------|---------------------|--------|
| Full 1,440 bars | **+54.86 USDT** | 5 fills, fees 9.92, slippage 5.42 |
| First 75% (0–1079) | +54.24 USDT | Walk-forward in-sample |
| Last 25% (1080–1439) | +0.62 USDT | Held-out 6 hours, still non-negative |
| Last 17% (1200–1439) | +27.53 USDT | Final 4-hour bounce |
| Max drawdown | −48.41 USDT | Tie-break metric |

Baselines on the same engine: buy-and-hold −72.36, short-and-hold +63.80
(but −36.79 on the last 25%), flat 0.

The sign of PnL stays positive if the taker fee is raised to 20 bps and
`SLIP_COEFF` to 0.20 (+39.53).

## Sandbox interface

```python
from strategy import generate_positions
# also exported as positions, run
pos = generate_positions(bars)   # DataFrame, list of dicts, or CSV path
# pos[i] in {-1, 0, +1}, decided at bar i close, fill at bar i+1 open
```

```sh
python3 replay.py bars.csv
python3 strategy.py bars.csv    # prints minute,position
```

Requires only Python 3 stdlib.
