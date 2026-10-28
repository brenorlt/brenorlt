"""Shared terminal-window chrome so all profile SVGs look like one set."""

from xml.sax.saxutils import escape

BG = "#0d1117"
BORDER = "#30363d"
TITLE_FG = "#7d8590"
FONT = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
BAR_H = 28
PAD = 14


def open_svg(width: int, height: int, title: str, label: str) -> str:
    """Opening <svg> tag, window background and title bar."""
    dots = "".join(
        f'<circle cx="{16 + i * 16}" cy="{BAR_H / 2}" r="5" fill="{c}"/>'
        for i, c in enumerate(("#ff5f57", "#febc2e", "#28c840"))
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-label="{escape(label)}">'
        f'<rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="10" '
        f'fill="{BG}" stroke="{BORDER}"/>'
        f'<line x1="0.5" y1="{BAR_H}" x2="{width - 0.5}" y2="{BAR_H}" stroke="{BORDER}"/>'
        f"{dots}"
        f'<text x="{width / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="11" fill="{TITLE_FG}">{escape(title)}</text>'
    )


def close_svg() -> str:
    return "</svg>\n"
