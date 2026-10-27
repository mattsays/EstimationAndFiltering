"""Regenerate the cost SVG of slide 08 from the ship-benchmark snapshot.

The chart shows seconds per track for the three filters used in the course.
Numbers come from ship-results.json (50 tracks, 800 scans, same machine), not
from hand-typed values, so a rerun updates the bars and the labels together.
The bars grow on slide entry; see .cost-bar / .cost-value in slideui.css.
"""

import json
from pathlib import Path

HERE = Path(__file__).parent
data = json.loads((HERE / "ship-results.json").read_text())
methods = data["method"]

name = {"EKF": "EKF", "CKF": "CKF", "UKF": "UKF"}
color = {"EKF": "#8b6ab1", "CKF": "var(--accent2)", "UKF": "var(--accent)"}
order = sorted(methods, key=lambda k: methods[k]["time_s_per_track"])
tmax = 0.16
W, H = 1100, 340
X0, X1 = 140, 1010
SCALE = (X1 - X0) / tmax
rows = [85, 180, 275]
BAR_H = 36
bar_delay = {"EKF": .10, "CKF": .25, "UKF": .40}

out = []
a = out.append
a(f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:1100px" role="img" '
  f'aria-label="Seconds per track for EKF, CKF and UKF on the ship benchmark: '
  f'EKF {methods["EKF"]["time_s_per_track"]:.3f} seconds, '
  f'CKF {methods["CKF"]["time_s_per_track"]:.3f}, '
  f'UKF {methods["UKF"]["time_s_per_track"]:.3f}.">')

a('<g font-family="var(--font)" font-size="19" font-weight="600" fill="var(--fg)">')
a('<text x="0" y="22">Seconds per track (ship benchmark, 800 scans)</text>')
a('</g>')

a('<g stroke="var(--line)">')
for tick in (0., .05, .10, .15):
    x = X0 + tick * SCALE
    a(f'<path d="M{x:.1f} 50 V305"/>')
a('</g>')
a('<g font-family="var(--font)" font-size="16" fill="var(--muted)" text-anchor="middle">')
for tick in (0., .05, .10, .15):
    x = X0 + tick * SCALE
    a(f'<text x="{x:.1f}" y="327">{tick:g}</text>')
a('</g>')

base = methods["EKF"]["time_s_per_track"]
for key, y in zip(order, rows):
    t = methods[key]["time_s_per_track"]
    width = t * SCALE
    per_scan = t / data["scans"] * 1e6
    ratio = t / base
    delay = bar_delay[key]
    a('<g font-family="var(--font)">')
    a(f'<text x="126" y="{y + 3}" text-anchor="end" font-size="30" font-weight="650" '
      f'fill="var(--fg)">{name[key]}</text>')
    a(f'<text x="126" y="{y + 24}" text-anchor="end" font-size="15" fill="var(--muted)">'
      f'{per_scan:.0f} µs · {ratio:.1f}×</text>')
    a(f'<rect class="cost-bar" x="{X0}" y="{y - BAR_H / 2}" width="{width:.1f}" '
      f'height="{BAR_H}" rx="6" fill="{color[key]}" '
      f'style="animation-delay:{delay:.2f}s"/>')
    a(f'<text class="cost-value" x="{X0 + width + 12:.1f}" y="{y + 8}" font-size="22" '
      f'font-weight="600" fill="var(--fg)" '
      f'style="animation-delay:{delay + .65:.2f}s">{t:.3f} s</text>')
    a('</g>')

a('</svg>')
svg = "\n".join(out)

target = HERE.parents[1] / "presentation/3/08-what-does-one-update-cost.html"
html = target.read_text()
start = html.index("<svg")
end = html.index("</svg>") + len("</svg>")
target.write_text(html[:start] + svg + html[end:])
print("updated", target.name)
