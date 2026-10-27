"""Regenerate the two accuracy panels of slide 08b from accuracy-sweep.json.

Both axes are labelled explicitly; the thesis marker is gone and SCKF is not
drawn, because it reproduces the CKF curve by construction (same rule).
"""

import json
import math
from pathlib import Path

HERE = Path(__file__).parent
data = json.loads((HERE / "accuracy-sweep.json").read_text())
sigmas = data["sigmas_deg"]
summary = data["summary"]

COLORS = {"EKF": "#8b6ab1", "UKF": "var(--accent)", "CKF": "var(--accent2)"}
ORDER = ("EKF", "UKF", "CKF")
W, H = 580, 440
LEFT, RIGHT, TOP, BOTTOM = 100, 20, 54, 360


def px(s):
    lo, hi = -0.30103, 1.47712  # log10(0.5) .. log10(30)
    return LEFT + (math.log10(s) - lo) / (hi - lo) * (W - RIGHT - LEFT)


def make_panel(metric, title, axis_title, ymin, ymax, ticks):
    vals = {name: summary[name][metric] for name in ORDER}
    y = lambda v: TOP + (1 - (v - ymin) / (ymax - ymin)) * (BOTTOM - TOP)
    mid = (LEFT + W - RIGHT) / 2
    out = []
    a = out.append
    a(f'<svg viewBox="0 0 {W} {H}" style="width:100%;max-width:580px" role="img" '
      f'aria-label="{title} {axis_title} against radar bearing noise, from 0.5 to 30 '
      f'degrees, for EKF, UKF and CKF.">')

    a(f'<text x="{LEFT}" y="22" font-family="var(--font)" font-size="20" font-weight="650" '
      f'fill="var(--fg)">{title}</text>')
    a(f'<text transform="translate(26 {(TOP + BOTTOM) / 2:.1f}) rotate(-90)" '
      f'font-family="var(--font)" font-size="14" fill="var(--muted)" '
      f'text-anchor="middle">{axis_title}</text>')

    a('<g stroke="var(--line)" stroke-width="1">')
    for t in ticks:
        a(f'<path d="M{LEFT} {y(t):.1f} H{W - RIGHT}"/>')
    a('</g>')
    a('<g font-family="var(--font)" font-size="14" fill="var(--muted)" text-anchor="end">')
    for t in ticks:
        a(f'<text x="{LEFT - 9}" y="{y(t) + 4:.1f}">{t:g}</text>')
    a('</g>')

    a('<g font-family="var(--font)" font-size="13" fill="var(--muted)" text-anchor="middle">')
    for s in sigmas:
        a(f'<text x="{px(s):.1f}" y="{BOTTOM + 20}">{s:g}&#176;</text>')
    a('</g>')
    a(f'<text x="{mid:.1f}" y="{BOTTOM + 48}" font-family="var(--font)" font-size="14" '
      f'fill="var(--muted)" text-anchor="middle">radar bearing noise &#963;&#952; (deg)</text>')

    for name in ORDER:
        pts = " ".join(f"{px(s):.1f},{y(v):.1f}" for s, v in zip(sigmas, vals[name]))
        a(f'<polyline points="{pts}" fill="none" stroke="{COLORS[name]}" stroke-width="3" '
          f'stroke-linejoin="round" stroke-linecap="round"/>')
    for name in ORDER:
        for s, v in zip(sigmas, vals[name]):
            a(f'<circle cx="{px(s):.1f}" cy="{y(v):.1f}" r="4.5" fill="{COLORS[name]}" '
              f'stroke="var(--bg)" stroke-width="1.2"/>')

    if metric == "pos_rmse":
        a(f'<text x="{px(0.5) + 9:.1f}" y="{y(summary["EKF"][metric][0]) - 10:.1f}" '
          f'font-family="var(--font)" font-size="13" fill="var(--muted)">all three</text>')
    a('</svg>')
    return "\n".join(out)


panels = (make_panel("pos_rmse", "Position", "RMSE (m)", 0., .4, (0., .1, .2, .3, .4))
          + "\n<div class=\"acc-divider\"></div>\n"
          + make_panel("vel_rmse", "Velocity", "RMSE (m/s)", .14, .25, (.15, .18, .21, .24)))

target = HERE.parents[1] / "presentation/3/08b-where-does-accuracy-show.html"
html = target.read_text()
start = html.index("<!-- ACC_PANELS -->")
end = html.index("<!-- /ACC_PANELS -->") + len("<!-- /ACC_PANELS -->")
target.write_text(html[:start] + "<!-- ACC_PANELS -->\n" + panels + "\n<!-- /ACC_PANELS -->" + html[end:])
print("updated", target.name)
