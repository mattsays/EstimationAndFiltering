"""Regenerate the deck's static SVG series from uncertainty-results.json."""
import json
import re
from pathlib import Path


def main():
    """Update plotted means and confidence bands without changing the slide layout."""
    folder = Path(__file__).parent
    data = json.loads((folder / 'uncertainty-results.json').read_text())
    deck = folder / 'deck-draft.html'
    html = deck.read_text()
    start = html.index('<svg', html.index('class="slide build cost-slide"'))
    end = html.index('</svg>', start) + len('</svg>')
    chart = html[start:end]
    axes = '<g font-family="var(--font)" font-size="22" fill="var(--muted)">'
    for y in [0, 200, 400, 600, 800]:
        py = 365 - y * 300 / 850
        axes += f'<path d="M100 {py} H950" stroke="var(--line)"/><text x="80" y="{py + 7}" text-anchor="end">{y}</text>'
    for x in [25, 200, 400, 600, 800, 1000, 1200]:
        px = 100 + (x - 25) * 850 / 1175
        axes += f'<text x="{px}" y="398" text-anchor="middle">{x}</text>'
    axes += '<text x="100" y="30">Position RMSE (m), first 30 updates</text><text x="525" y="437" text-anchor="middle">Initial position standard deviation per axis (m)</text></g>'
    chart = re.sub(r'<g\b[^>]*>.*?</g>', lambda _: axes, chart, count=1)
    for name in ('EKF', 'UKF', 'CKF'):
        pattern = r'<g(?: data-step="2")?><polygon[^>]*>.*?</g>'
        group = next(m for m in re.finditer(pattern, chart) if f'>{name}</text>' in m.group())
        rows = data['results']
        def point(row, value):
            return f"{100 + (row['position_sd_m'] - 25) * 850 / 1175},{365 - value * 300 / 850}"
        means = [point(row, row['methods'][name]['rmse_m']) for row in rows]
        band = [point(row, row['methods'][name]['ci95_m'][1]) for row in rows]
        band += [point(row, row['methods'][name]['ci95_m'][0]) for row in reversed(rows)]
        text = group.group()
        text = re.sub(r'(<polygon points=")[^"]*', lambda m: m[1] + ' '.join(band), text)
        text = re.sub(r'(<polyline points=")[^"]*', lambda m: m[1] + ' '.join(means), text)
        color = {'EKF':'#8b6ab1', 'UKF':'var(--accent)', 'CKF':'var(--accent2)'}[name]
        text = re.sub(r'<circle\b[^>]*/>', '', text)
        circles = ''.join(f'<circle cx="{p.split(",")[0]}" cy="{p.split(",")[1]}" r="4" fill="{color}"/>' for p in means)
        text = text.replace('<text ', circles + '<text ', 1)
        chart = chart[:group.start()] + text + chart[group.end():]
    html = html[:start] + chart + html[end:]
    deck.write_text(html)


if __name__ == '__main__':
    main()
