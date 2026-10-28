"""Convert the prepped photo into a monochrome ASCII portrait that types itself in.

Each row is revealed by a left-to-right clip wipe with a block cursor riding the
edge, staggered top to bottom. Plays once and freezes (SMIL, so GitHub runs it).

    python scripts/make_ascii_svg.py            # writes avi-ascii.svg
    STATIC=1 python scripts/make_ascii_svg.py   # frozen frame, for previews
"""

import os
from pathlib import Path
from xml.sax.saxutils import escape

import numpy as np
from PIL import Image

from svg_frame import BAR_H, FONT, PAD, close_svg, open_svg

ROOT = Path(__file__).resolve().parent.parent
SRC_GRAY = ROOT / "assets" / "source-prepped.png"
SRC_MASK = ROOT / "assets" / "source-mask.png"
OUT = ROOT / "ascii-portrait.svg"

WIDTH, HEIGHT = 370, 440
COLS = 76
CELL_W = (WIDTH - 2 * PAD) / COLS
FONT_SIZE = CELL_W / 0.6
LINE_H = FONT_SIZE * 1.08
ROWS = int((HEIGHT - BAR_H - 2 * PAD) // LINE_H)

# portion of the prepped image to keep, as fractions (left, top, right);
# the bottom edge follows from the grid's aspect ratio
CROP = (0.14, 0.0, 0.86)

RAMP = " .`:-=+*cs#%@"  # sparse -> dense
INVERT = os.environ.get("INVERT", "0") == "1"  # 1: dark pixels print dense glyphs (negative)
GAMMA = 0.85  # < 1 lifts mid-tones
FLOOR = 1  # min ramp index inside the subject, so dark clothes keep a silhouette
NBSP = "\u00a0"  # inner gaps must not collapse
FG = "#c9d1d9"
CURSOR = "#39d353"

ROW_DUR = 0.32
ROW_STAGGER = 0.055
START = 0.3


def to_grid() -> list[str]:
    gray = Image.open(SRC_GRAY).convert("L")
    mask = Image.open(SRC_MASK).convert("L")

    # crop to head and shoulders at the aspect the character grid needs
    w, h = gray.size
    left, top, right = round(CROP[0] * w), round(CROP[1] * h), round(CROP[2] * w)
    bottom = min(h, top + round((right - left) * (ROWS * LINE_H) / (COLS * CELL_W)))
    box = (left, top, right, bottom)
    gray, mask = gray.crop(box), mask.crop(box)

    g = np.asarray(gray.resize((COLS, ROWS), Image.LANCZOS), dtype=np.float32) / 255.0
    m = np.asarray(mask.resize((COLS, ROWS), Image.LANCZOS)) > 110

    # stretch the subject's tones to the full ramp
    lo, hi = np.percentile(g[m], [2, 98])
    g = np.clip((g - lo) / max(hi - lo, 1e-6), 0, 1)
    density = (1 - g if INVERT else g) ** GAMMA
    idx = np.maximum(np.round(density * (len(RAMP) - 1)).astype(int), FLOOR)
    idx[~m] = 0
    return ["".join(RAMP[i] for i in row).rstrip() for row in idx]


def main() -> None:
    static = os.environ.get("STATIC") == "1"
    rows = to_grid()
    x0, y0 = PAD, BAR_H + PAD
    text_w = WIDTH - 2 * PAD

    out = [open_svg(WIDTH, HEIGHT, "~/portrait.txt", "ASCII portrait of Breno Lopes")]
    out.append(
        f'<g font-family="{FONT}" font-size="{FONT_SIZE:.2f}" fill="{FG}" '
        f'xml:space="preserve">'
    )
    defs = []
    for i, line in enumerate(rows):
        if not line:
            continue
        y = y0 + i * LINE_H
        # renderers collapse leading spaces, so position each row's first glyph
        lead = len(line) - len(line.lstrip())
        x = x0 + lead * CELL_W
        width = (len(line) - lead) * CELL_W
        text = (
            f'<text x="{x:.2f}" y="{y + FONT_SIZE * 0.85:.2f}" textLength="{width:.2f}" '
            f'lengthAdjust="spacingAndGlyphs">{escape(line.lstrip()).replace(" ", NBSP)}</text>'
        )
        if static:
            out.append(text)
            continue
        begin = START + i * ROW_STAGGER
        defs.append(
            f'<clipPath id="r{i}"><rect x="{x:.2f}" y="{y:.2f}" width="0" height="{LINE_H + 0.5:.2f}">'
            f'<animate attributeName="width" from="0" to="{width:.2f}" begin="{begin:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/></rect></clipPath>'
        )
        out.append(f'<g clip-path="url(#r{i})">{text}</g>')
        out.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{CELL_W:.2f}" height="{LINE_H:.2f}" '
            f'fill="{CURSOR}" opacity="0">'
            f'<set attributeName="opacity" to="0.9" begin="{begin:.3f}s"/>'
            f'<animate attributeName="x" from="{x:.2f}" to="{x + width:.2f}" begin="{begin:.3f}s" '
            f'dur="{ROW_DUR}s" fill="freeze"/>'
            f'<set attributeName="opacity" to="0" begin="{begin + ROW_DUR:.3f}s"/></rect>'
        )
    out.append("</g>")
    if defs:
        out.insert(1, "<defs>" + "".join(defs) + "</defs>")
    out.append(close_svg())

    OUT.write_text("".join(out))
    print(f"wrote {OUT.name} ({COLS}x{ROWS} chars, {'static' if static else 'animated'})")


if __name__ == "__main__":
    main()
