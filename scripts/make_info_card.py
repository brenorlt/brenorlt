"""Hand-authored neofetch-style info card that prints line by line.

Edit LINES below, then:

    python scripts/make_info_card.py            # writes info-card.svg
    STATIC=1 python scripts/make_info_card.py   # frozen frame, for previews
"""

import os
from pathlib import Path
from xml.sax.saxutils import escape

from svg_frame import BAR_H, FONT, PAD, close_svg, open_svg

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "info-card.svg"

WIDTH, HEIGHT = 490, 440
FONT_SIZE = 13
LINE_H = 21
KEY_W = 11  # characters reserved for the key column

USER, HOST = "breno", "github"
LINES = [
    ("Name", "Breno Lopes"),
    ("Role", "Software Developer, backend-focused"),
    ("Focus", "Node.js / TypeScript, exploring Go"),
    ("Languages", "TypeScript, Go, JavaScript, Python"),
    ("Backend", "Node.js, NestJS, Go, REST APIs"),
    ("Frontend", "React, Next.js, TailwindCSS"),
    ("Data", "PostgreSQL, Supabase"),
    ("Infra", "Docker, microservices"),
    ("Learning", "System Design, Clean Architecture"),
    ("Ask me", "Backend, NestJS, DB optimization"),
    ("Contact", "brenotolentino.dev@gmail.com"),
]

ACCENT = "#39d353"
KEY = "#58a6ff"
FG = "#c9d1d9"
MUTED = "#7d8590"
SWATCHES = ["#484f58", "#ff7b72", "#3fb950", "#d29922", "#58a6ff", "#bc8cff", "#39c5cf", "#e6edf3"]

START = 0.5
STAGGER = 0.12


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    char_w = FONT_SIZE * 0.6
    x = PAD + 4
    y = BAR_H + PAD + FONT_SIZE + 4

    rows = []  # (svg fragment, height consumed)
    title = (
        f'<tspan fill="{ACCENT}" font-weight="700">{USER}</tspan><tspan fill="{FG}">@</tspan>'
        f'<tspan fill="{ACCENT}" font-weight="700">{HOST}</tspan>'
    )
    rows.append((f'<text x="{x}" y="{{y}}">{title}</text>', LINE_H))
    rows.append((f'<text x="{x}" y="{{y}}" fill="{MUTED}">{"-" * (len(USER) + len(HOST) + 1)}</text>', LINE_H))
    for key, value in LINES:
        rows.append((
            f'<text x="{x}" y="{{y}}"><tspan fill="{KEY}" font-weight="700">{escape(key)}</tspan>'
            f'<tspan fill="{MUTED}">:</tspan>'
            f'<tspan x="{x + KEY_W * char_w:.1f}" fill="{FG}">{escape(value)}</tspan></text>',
            LINE_H,
        ))
    rows.append(("", LINE_H * 0.6))
    sw = 22
    rects = "".join(
        f'<rect x="{x + i * (sw + 6)}" y="{{top}}" width="{sw}" height="14" rx="3" fill="{c}"/>'
        for i, c in enumerate(SWATCHES)
    )
    rows.append((f"<g>{rects}</g>", LINE_H))
    rows.append(("", LINE_H * 0.4))
    rows.append((
        f'<text x="{x}" y="{{y}}"><tspan fill="{ACCENT}">{USER}@{HOST}</tspan>'
        f'<tspan fill="{FG}"> ~ $ </tspan></text>'
        f'<rect x="{x + (len(USER) + len(HOST) + 6) * char_w:.1f}" y="{{top}}" width="{char_w:.1f}" '
        f'height="{FONT_SIZE + 2}" fill="{FG}" class="blink"/>',
        LINE_H,
    ))

    style = (
        "<style>"
        ".l{opacity:0;animation:in .45s ease-out forwards}"
        "@keyframes in{from{opacity:0;transform:translateX(-8px)}to{opacity:1;transform:none}}"
        ".blink{animation:blink 1.1s steps(1) infinite}"
        "@keyframes blink{50%{opacity:0}}"
        "</style>"
    )
    out = [open_svg(WIDTH, HEIGHT, "~/neofetch", "Breno Lopes — neofetch-style info card")]
    if not static:
        out.append(style)
    out.append(f'<g font-family="{FONT}" font-size="{FONT_SIZE}" fill="{FG}">')
    n = 0
    for frag, h in rows:
        if frag:
            body = frag.replace("{y}", f"{y:.1f}").replace("{top}", f"{y - FONT_SIZE + 1:.1f}")
            if static:
                out.append(body)
            else:
                out.append(f'<g class="l" style="animation-delay:{START + n * STAGGER:.2f}s">{body}</g>')
            n += 1
        y += h
    out.append("</g>")
    out.append(close_svg())

    OUT.write_text("".join(out))
    print(f"wrote {OUT.name} ({n} lines, {'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
