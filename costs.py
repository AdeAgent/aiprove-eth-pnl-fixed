"""Default cost model used for local scoring.

The official sandbox has not published numeric fee/slippage constants, only
that entries are costed with maker + taker fees and slippage scaled by size,
with no phantom fills. These defaults follow Binance spot VIP0-style taker
fees and a linear participation impact. If the sandbox uses different
constants it will re-apply them when it replays positions; the strategy
itself does not depend on the numbers.
"""

# Fraction of notional charged on each fill. All fills in this entry are
# next-bar market orders (taker). Maker is recorded for completeness.
MAKER_FEE = 0.0008
TAKER_FEE = 0.0010

# Additional slippage fraction = SLIP_COEFF * |trade_qty| / bar_volume,
# capped at SLIP_CAP so a tiny-volume bar cannot produce a nonsense fill.
SLIP_COEFF = 0.10
SLIP_CAP = 0.05

# Position unit. generate_positions returns lots in {-1, 0, +1}.
LOT_ETH = 1.0
