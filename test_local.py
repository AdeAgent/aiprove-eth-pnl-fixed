import os
from replay import load_bars, replay, slice_pnl
from strategy import generate_positions

root = os.path.dirname(os.path.abspath(__file__))
bars = load_bars(os.path.join(root, "bars.csv"))
pos = generate_positions(bars)
assert len(pos) == 1440
assert set(pos) <= {-1, 0, 1}
r = replay(bars, pos)
assert abs(r["net_pnl"] - 54.8610) < 0.02, r["net_pnl"]
assert r["trades"] == 5
assert slice_pnl(r["equity"], 0, 1080) > 0
assert slice_pnl(r["equity"], 1080, 1440) >= 0
print("ok", round(r["net_pnl"], 4), r["trades"], round(r["max_drawdown"], 4))
