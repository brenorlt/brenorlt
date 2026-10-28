"""Render data/contributions.json as an animated 53x7 contribution heatmap.

Boxes slide in along diagonals once, then freeze. Stats footer underneath.

    python scripts/render_heatmap_svg.py            # writes contrib-heatmap.svg
    STATIC=1 python scripts/render_heatmap_svg.py   # frozen frame, for previews
"""

import json
import os
from datetime import date
from pathlib import Path

from svg_frame import BAR_H, FONT, PAD, close_svg, open_svg

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "data" / "contributions.json"
OUT = ROOT / "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
#          none -> brightest (level 5 is a neon top end for the busiest days)
FG = "#c9d1d9"
MUTED = "#7d8590"
ACCENT = "#39d353"

WIDTH = 860
BOX, GAP = 12, 3
STEP = BOX + GAP
LABEL_W = 30
MONTH_H = 18
DIAG_DELAY = 0.025  # seconds per diagonal
START = 0.3


def level(day: dict, top: int) -> int:
    if top and day["count"] >= top:
        return 5
    return day["level"]


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    data = json.loads(SRC.read_text())
    days = data["days"]
    s = data["stats"]

    # neon level for the top ~3% of active days
    active = sorted(d["count"] for d in days if d["count"])
    top = active[int(len(active) * 0.97)] if len(active) >= 20 else 0

    # weeks start on Sunday, like GitHub's calendar
    first = date.fromisoformat(days[0]["date"])
    offset = (first.weekday() + 1) % 7
    weeks = (offset + len(days) + 6) // 7

    grid_w = weeks * STEP - GAP
    x0 = PAD + LABEL_W + (WIDTH - 2 * PAD - LABEL_W - grid_w) / 2
    y0 = BAR_H + PAD + MONTH_H
    grid_h = 7 * STEP - GAP
    height = int(y0 + grid_h + 62)

    out = [open_svg(WIDTH, height, "~/contributions.sh",
                    f"{data['total']} GitHub contributions in the last year")]
    if not static:
        n_diag = weeks + 7
        out.append(
            "<style>"
            ".c{opacity:0;animation:drop .5s cubic-bezier(.2,.7,.3,1) forwards}"
            "@keyframes drop{from{opacity:0;transform:translateY(-10px)}to{opacity:1;transform:none}}"
            ".f{opacity:0;animation:fade .6s ease-out forwards}"
            "@keyframes fade{to{opacity:1}}"
            + "".join(f".d{i}{{animation-delay:{START + i * DIAG_DELAY:.3f}s}}" for i in range(n_diag))
            + "</style>"
        )
        footer_delay = START + n_diag * DIAG_DELAY
    out.append(f'<g font-family="{FONT}">')

    # month labels on the first column of each month, skipping ones that would collide
    last_month, last_col = None, -9
    for i, d in enumerate(days):
        col = (i + offset) // 7
        month = d["date"][:7]
        if month == last_month:
            continue
        last_month = month
        if col - last_col >= 3 and col < weeks - 1:
            label = date.fromisoformat(d["date"]).strftime("%b")
            out.append(f'<text x="{x0 + col * STEP:.1f}" y="{y0 - 6}" font-size="10" fill="{MUTED}">{label}</text>')
            last_col = col
    for row, label in ((1, "Mon"), (3, "Wed"), (5, "Fri")):
        out.append(
            f'<text x="{x0 - 8:.1f}" y="{y0 + row * STEP + BOX - 2}" font-size="10" '
            f'text-anchor="end" fill="{MUTED}">{label}</text>'
        )

    for i, d in enumerate(days):
        col, row = divmod(i + offset, 7)
        cls = "" if static else f' class="c d{col + row}"'
        out.append(
            f'<rect{cls} x="{x0 + col * STEP:.1f}" y="{y0 + row * STEP}" width="{BOX}" height="{BOX}" '
            f'rx="2.5" fill="{PALETTE[level(d, top)]}"><title>{d["count"]} on {d["date"]}</title></rect>'
        )

    # footer: summary on the left, Less -> More legend on the right
    fy = y0 + grid_h + 28
    best = date.fromisoformat(s["best_day"]["date"]).strftime("%b %-d")
    fade = "" if static else f' class="f" style="animation-delay:{footer_delay:.2f}s"'
    out.append(
        f'<g{fade}><text x="{x0:.1f}" y="{fy}" font-size="12" fill="{FG}">'
        f'<tspan fill="{ACCENT}" font-weight="700">{data["total"]:,}</tspan> contributions in the last year'
        f'<tspan fill="{MUTED}">  ·  </tspan>streak <tspan fill="{ACCENT}">{s["current_streak"]}d</tspan>'
        f'<tspan fill="{MUTED}">  ·  </tspan>longest <tspan fill="{ACCENT}">{s["longest_streak"]}d</tspan>'
        f'<tspan fill="{MUTED}">  ·  </tspan>best day <tspan fill="{ACCENT}">{s["best_day"]["count"]}</tspan>'
        f'<tspan fill="{MUTED}"> ({best})</tspan></text>'
    )
    lx = x0 + grid_w - len(PALETTE) * (BOX + 3) - 30
    out.append(f'<text x="{lx - 6:.1f}" y="{fy}" font-size="10" text-anchor="end" fill="{MUTED}">Less</text>')
    for i, c in enumerate(PALETTE):
        out.append(f'<rect x="{lx + i * (BOX + 3):.1f}" y="{fy - 10}" width="{BOX}" height="{BOX}" rx="2.5" fill="{c}"/>')
    out.append(f'<text x="{lx + len(PALETTE) * (BOX + 3) + 3:.1f}" y="{fy}" font-size="10" fill="{MUTED}">More</text>')
    updated = data["fetched_at"][:10]
    out.append(
        f'<text x="{x0 + grid_w:.1f}" y="{fy + 20}" font-size="9" text-anchor="end" fill="{MUTED}">'
        f"updated {updated}</text></g>"
    )

    out.append("</g>")
    out.append(close_svg())
    OUT.write_text("".join(out))
    print(f"wrote {OUT.name} ({weeks} weeks, {'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
