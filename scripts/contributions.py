#!/usr/bin/env python3
"""Draw a GitHub user's past-year contribution calendar as a dark SVG.

Usage: python contributions.py <github-username> <output.svg>

Uses only the standard library. Reads the public contribution calendar from
github.com, so no token is needed. Private contributions only appear if the
account has "Include private contributions on my profile" switched on.
"""
import datetime as dt
import re
import sys
import urllib.request

LEVELS = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]  # GitHub dark greens
FONT = "Inter, 'Segoe UI', -apple-system, Helvetica, Arial, sans-serif"
W = 1000


def fetch(user):
    req = urllib.request.Request(
        f"https://github.com/users/{user}/contributions",
        headers={"User-Agent": "Mozilla/5.0 (profile-readme-bot)"},
    )
    page = urllib.request.urlopen(req, timeout=30).read().decode("utf-8", "replace")
    cells = {}
    for tag in re.finditer(r"<td\b[^>]*>", page):
        t = tag.group(0)
        d = re.search(r'data-date="(\d{4}-\d{2}-\d{2})"', t)
        lv = re.search(r'data-level="(\d)"', t)
        if d and lv:
            cells[d.group(1)] = int(lv.group(1))
    m = re.search(r"([\d,]+)\s+contributions?\s+in\s+the\s+last\s+year", page)
    total = int(m.group(1).replace(",", "")) if m else None
    days = sorted((dt.date.fromisoformat(k), v) for k, v in cells.items())
    return days, total


def streaks(days):
    longest = run = 0
    for _, lv in days:
        run = run + 1 if lv else 0
        longest = max(longest, run)
    i = len(days) - 1
    if i >= 0 and days[i][1] == 0:  # today may not have a contribution yet
        i -= 1
    current = 0
    while i >= 0 and days[i][1]:
        current += 1
        i -= 1
    return current, longest


def render_svg(days, total):
    pitch, cell = 17, 14
    first = days[0][0]
    sunday0 = first - dt.timedelta(days=(first.weekday() + 1) % 7)
    cols = (days[-1][0] - sunday0).days // 7 + 1
    grid_w = cols * pitch - (pitch - cell)
    x0 = W - 36 - grid_w
    y0 = 134
    current, longest = streaks(days)
    active = sum(1 for _, lv in days if lv)
    headline = f"{total:,}" if total is not None else f"{active}"
    sub = "contributions in the last year" if total is not None else "active days in the last year"

    # month labels: keep a label only if the next month starts 3+ columns later
    cand, last = [], None
    for c in range(cols):
        month = (sunday0 + dt.timedelta(days=7 * c)).month
        if month != last:
            cand.append((c, month))
            last = month
    keep = [cand[i] for i in range(len(cand)) if i == len(cand) - 1 or cand[i + 1][0] - cand[i][0] >= 3]

    o = []
    o.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} 300" width="{W}" height="300" role="img" aria-labelledby="t">')
    o.append(f'<title id="t">GitHub contributions over the last year: {headline}</title>')
    o.append(f'<rect x="0.5" y="0.5" width="{W-1}" height="299" rx="20" fill="#0d1117" stroke="#30363d"/>')
    o.append(f'<g font-family="{FONT}">')
    o.append(f'<text x="36" y="62" font-size="38" font-weight="800" fill="#ffffff">{headline}</text>')
    o.append(f'<text x="36" y="86" font-size="14" fill="#8d97bd">{sub}</text>')
    stats = [(current, "day streak"), (longest, "longest streak"), (active, "active days")]
    for i, (n, label) in enumerate(stats):
        sx = 590 + i * 130
        o.append(f'<text x="{sx}" y="62" font-size="30" font-weight="800" fill="#a5a0ff">{n}</text>')
        o.append(f'<text x="{sx}" y="86" font-size="13" fill="#8d97bd">{label}</text>')
    for c, month in keep:
        mx = x0 + c * pitch
        o.append(f'<text x="{mx}" y="124" font-size="12" fill="#8d97bd">{dt.date(2000, month, 1).strftime("%b")}</text>')
    for row, name in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        o.append(f'<text x="{x0-10}" y="{y0 + row*pitch + 11}" font-size="11" fill="#8d97bd" text-anchor="end">{name}</text>')
    for d, lv in days:
        c = (d - sunday0).days // 7
        r = (d.weekday() + 1) % 7
        o.append(f'<rect x="{x0 + c*pitch}" y="{y0 + r*pitch}" width="{cell}" height="{cell}" rx="3" fill="{LEVELS[lv]}"/>')
    ly = 282
    right = W - 36
    o.append(f'<text x="{right}" y="{ly}" font-size="12" fill="#8d97bd" text-anchor="end">More</text>')
    start = right - 40 - (5 * pitch - (pitch - cell))
    for i, col in enumerate(LEVELS):
        o.append(f'<rect x="{start + i*pitch}" y="{ly-12}" width="{cell}" height="{cell}" rx="3" fill="{col}"/>')
    o.append(f'<text x="{start-8}" y="{ly}" font-size="12" fill="#8d97bd" text-anchor="end">Less</text>')
    o.append("</g></svg>")
    return "\n".join(o)


def main():
    if len(sys.argv) != 3:
        sys.exit("usage: contributions.py <github-username> <output.svg>")
    days, total = fetch(sys.argv[1])
    if len(days) < 300:
        sys.exit(f"only {len(days)} days found; keeping the existing file")
    with open(sys.argv[2], "w", encoding="utf-8") as f:
        f.write(render_svg(days, total))
    print(f"wrote {sys.argv[2]}: {len(days)} days, total={total}")


if __name__ == "__main__":
    main()
