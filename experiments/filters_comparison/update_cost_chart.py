"""Regenerate the cost/accuracy SVG of the module-3 slide from the two JSON snapshots.

Left: median time per prediction and update (benchmark-results.json).
Right: position RMSE at two initial uncertainties (uncertainty-results.json),
so accuracy is never presented as a single general ranking.
"""
import json
from pathlib import Path

HERE = Path(__file__).parent
bench = json.loads((HERE / "benchmark-results.json").read_text())["results"]
sweep = {row["position_sd_m"]: row["methods"]
         for row in json.loads((HERE / "uncertainty-results.json").read_text())["results"]}

cost_rows = ["EKF", "KF", "CKF", "UKF"]          # sorted by measured time
label = {"EKF": "EKF", "KF": "KF*", "CKF": "CKF", "UKF": "UKF"}
sub = {"EKF": "1 evaluation", "KF": "converted",
       "CKF": "8 points", "UKF": "9 points"}
color = {"EKF": "#8b6ab1", "KF": "#7d8794",
         "CKF": "var(--accent2)", "UKF": "var(--accent)"}

T0, T1, TMAX = 96, 448, 45.0
COST_Y = [58, 110, 162, 214]
BAR_H = 16

RX0, RX1 = 641, 1021
PANELS = [
    (100, 40, 64, [84, 112, 140], 158, "prior 100 m: all three within 0.1 m"),
    (1200, 700, 186, [206, 234, 262], 280, "prior 1,200 m: EKF at 2.1× the CKF"),
]
ACC = ["EKF", "UKF", "CKF"]

sx = lambda t: T0 + t / TMAX * (T1 - T0)
ax = lambda value, vmax: RX0 + value / vmax * (RX1 - RX0)

out = []
a = out.append
a('<svg viewBox="0 0 1120 292" style="width:100%;max-width:1100px" role="img" '
  'aria-label="Median time per prediction and update for the four filters, next to position RMSE '
  'at a 100 metre and at a 1,200 metre initial position uncertainty. EKF 17.2 microseconds, converted '
  'KF 19.0, CKF 34.7, UKF 41.3. At 100 metres EKF 26.4, UKF 26.3, CKF 26.3. '
  'At 1,200 metres EKF 696, UKF 390, CKF 336.">')

# ---- cost track (step 1) -------------------------------------------------
a('<g font-family="var(--font)" font-size="17" fill="var(--muted)">')
a('<text x="96" y="20">Time per predict + update (μs)</text>')
a('<text x="530" y="20" text-anchor="end" font-size="15">vs EKF</text>')
a('</g>')

a('<g stroke="var(--line)">')
for t in (0, 10, 20, 30, 40):
    a(f'<path d="M{sx(t):.1f} 34 V232"/>')
a('</g>')

a('<g font-family="var(--font)" font-size="15" fill="var(--muted)" text-anchor="middle">')
for t in (0, 10, 20, 30, 40):
    a(f'<text x="{sx(t):.1f}" y="244">{t}</text>')
a('</g>')

for name, y in zip(cost_rows, COST_Y):
    r = bench[name]
    w = sx(r["time_us"]) - T0
    a('<g font-family="var(--font)">')
    a(f'<text x="88" y="{y - 2}" text-anchor="end" font-size="22" font-weight="650" '
      f'fill="var(--fg)">{label[name]}</text>')
    a(f'<text x="88" y="{y + 15}" text-anchor="end" font-size="13" fill="var(--muted)">'
      f'{sub[name]}</text>')
    a(f'<rect x="{T0}" y="{y - BAR_H / 2}" width="{w:.1f}" height="{BAR_H}" rx="4" '
      f'fill="{color[name]}"/>')
    a(f'<text x="{T0 + w + 7:.1f}" y="{y + 6}" font-size="18" font-weight="600" '
      f'fill="var(--fg)">{r["time_us"]:.1f}</text>')
    a(f'<text x="530" y="{y + 5}" text-anchor="end" font-size="15" fill="var(--muted)">'
      f'{r["time_us"] / bench["EKF"]["time_us"]:.1f}×</text>')
    a('</g>')

# ---- accuracy by regime (step 2) ----------------------------------------
a('<path d="M560 6 V286" stroke="var(--line)"/>')
a('<g font-family="var(--font)" font-size="17" fill="var(--muted)">')
a('<text x="585" y="20">Position RMSE (m) by initial uncertainty</text>')
a('<text x="585" y="38" font-size="13">same uncertainty sweep as the previous slide</text>')
a('</g>')

for value, vmax, title_y, ys, axis_y, title in PANELS:
    a('<g font-family="var(--font)">')
    a(f'<text x="585" y="{title_y}" font-size="15" font-weight="600" fill="var(--fg)">'
      f'{title}</text>')
    a('</g>')
    a('<g stroke="var(--line)">')
    for frac in (0, 0.5, 1):
        a(f'<path d="M{ax(frac * vmax, vmax):.1f} {ys[0] - 8} V{ys[-1] + 8}"/>')
    a('</g>')
    a('<g font-family="var(--font)" font-size="13" fill="var(--muted)" text-anchor="middle">')
    for frac in (0, 0.5, 1):
        a(f'<text x="{ax(frac * vmax, vmax):.1f}" y="{axis_y}">{frac * vmax:g}</text>')
    a('</g>')
    for name, y in zip(ACC, ys):
        r = sweep[value][name]["rmse_m"]
        w = ax(r, vmax) - RX0
        a('<g font-family="var(--font)">')
        a(f'<text x="633" y="{y + 5}" text-anchor="end" font-size="14" fill="var(--muted)">'
          f'{name}</text>')
        a(f'<rect x="{RX0}" y="{y - BAR_H / 2}" width="{w:.1f}" height="{BAR_H}" rx="4" '
          f'fill="{color[name]}"/>')
        a(f'<text x="{RX0 + w + 6:.1f}" y="{y + 5}" font-size="15" font-weight="600" '
          f'fill="var(--fg)">{r:.1f}</text>')
        a('</g>')
a('</svg>')
svg = "\n".join(out)

target = HERE.parents[1] / "presentation/3/08b-what-does-accuracy-cost.html"
html = target.read_text()
start = html.index('<svg')
end = html.index('</svg>') + len('</svg>')
target.write_text(html[:start] + svg + html[end:])
print(f"updated {target.name}")
