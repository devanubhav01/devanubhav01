"""
Renders a terminal-style "sysinfo" panel as a self-animating SVG.
Each row fades in with a short stagger, like it's typing itself out.

Usage:
    python tools/render_panel.py            # writes sysinfo.svg
    PREVIEW=1 python tools/render_panel.py   # writes a still-frame preview
"""

import os
from pathlib import Path

OUTPUT_PATH = Path("sysinfo.svg")

TITLE = "sysinfo.sh"

ROWS = [
    ("role", "Software Engineer"),
    ("focus", "AI / ML & Full Stack Dev"),
    ("stack", "Python · React · AWS"),
    ("now", "Building AI-powered systems"),
    ("learning", "System Design · LLM tuning"),
    ("ping", "devanubhav01@github"),
]

ACCENT = "#8b5cf6"
FG = "#c9d1d9"
BG = "#0d1117"
HEADER_BG = "#161b22"
MUTED = "#6e7681"

WIDTH = 460
ROW_HEIGHT = 32
HEADER_HEIGHT = 54
PADDING_BOTTOM = 24
ROW_START_DELAY = 0.2
ROW_STAGGER = 0.5
ROW_FADE_DUR = 0.4


def escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(preview: bool) -> str:
    height = HEADER_HEIGHT + len(ROWS) * ROW_HEIGHT + PADDING_BOTTOM

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}">',
        "<defs>",
        "<style>",
        f'.label {{ font-family: "Courier New", monospace; font-size: 14px; '
        f'fill: {ACCENT}; font-weight: bold; }}',
        f'.value {{ font-family: "Courier New", monospace; font-size: 14px; fill: {FG}; }}',
        f'.prompt {{ font-family: "Courier New", monospace; font-size: 13px; fill: {MUTED}; }}',
        "</style>",
        "</defs>",
        f'<rect width="{WIDTH}" height="{height}" rx="10" ry="10" fill="{BG}"/>',
        f'<rect width="{WIDTH}" height="34" rx="10" ry="10" fill="{HEADER_BG}"/>',
        f'<rect y="20" width="{WIDTH}" height="14" fill="{HEADER_BG}"/>',
        '<circle cx="20" cy="17" r="6" fill="#ff5f56"/>',
        '<circle cx="40" cy="17" r="6" fill="#ffbd2e"/>',
        '<circle cx="60" cy="17" r="6" fill="#27c93f"/>',
        f'<text x="{WIDTH / 2:.0f}" y="21" text-anchor="middle" class="prompt">{escape(TITLE)}</text>',
        '<text x="24" y="66" class="prompt">$ ./sysinfo --verbose</text>',
    ]

    y = 102
    for i, (label, value) in enumerate(ROWS):
        begin = ROW_START_DELAY + i * ROW_STAGGER
        opacity_attr = "1" if preview else "0"
        parts.append(f'<g opacity="{opacity_attr}">')
        parts.append(f'<text x="24" y="{y}" class="label">{escape(label)}</text>')
        parts.append(f'<text x="120" y="{y}" class="value">{escape(value)}</text>')
        if not preview:
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="{ROW_FADE_DUR}s" fill="freeze"/>'
            )
        parts.append("</g>")
        y += ROW_HEIGHT

    cursor_y = y - ROW_HEIGHT + 8
    cursor_begin = ROW_START_DELAY + len(ROWS) * ROW_STAGGER + 0.4
    parts.append(f'<rect x="24" y="{cursor_y}" width="9" height="14" fill="{ACCENT}">')
    if not preview:
        parts.append(
            f'<animate attributeName="opacity" values="1;0;1" dur="1s" '
            f'begin="{cursor_begin:.2f}s" repeatCount="indefinite"/>'
        )
    parts.append("</rect>")

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    preview = os.environ.get("PREVIEW") == "1"
    svg = build_svg(preview=preview)
    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Saved: {OUTPUT_PATH} ({'preview' if preview else 'animated'})")


if __name__ == "__main__":
    main()
