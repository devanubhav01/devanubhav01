"""
Converts assets/photo-ready.png into a monochrome ASCII portrait SVG that
draws itself in, row by row, using per-row clip-path animation.

Usage:
    python tools/render_portrait.py
    # writes portrait.svg
"""

from pathlib import Path

import numpy as np
from PIL import Image

INPUT_PATH = Path("assets/photo-ready.png")
OUTPUT_PATH = Path("portrait.svg")

# left = light/empty, right = dense/dark
GLYPHS = " '.,:;~+*xXO#"

ACCENT_COLOR = "#a78bfa"
BG_COLOR = "#0d1117"

# Character grid size — tune for detail vs. clutter.
COLS = 70
ROWS = 90

CHAR_W = 6.2
CHAR_H = 11
FONT_SIZE = 11

ROW_DELAY_MS = 40  # stagger between rows starting to draw
ROW_DRAW_MS = 250  # how long each row's wipe-in animation takes


def image_to_grid(img: Image.Image) -> np.ndarray:
    gray = img.convert("L").resize((COLS, ROWS))
    arr = np.array(gray, dtype=np.float32) / 255.0
    return arr


def brightness_to_glyph(value: float) -> str:
    # value: 0 (dark) .. 1 (light) -> pick from the light end for
    # brighter pixels, dense end for darker pixels
    idx = int((1.0 - value) * (len(GLYPHS) - 1))
    idx = max(0, min(len(GLYPHS) - 1, idx))
    return GLYPHS[idx]


def build_svg(grid: np.ndarray) -> str:
    width = COLS * CHAR_W
    height = ROWS * CHAR_H

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">',
        f'<rect width="{width:.0f}" height="{height:.0f}" fill="{BG_COLOR}"/>',
        "<defs>",
        f'<style>text {{ font-family: "Courier New", monospace; '
        f'font-size: {FONT_SIZE}px; fill: {ACCENT_COLOR}; }}</style>',
        "</defs>",
    ]

    for row_idx in range(ROWS):
        row_chars = "".join(
            brightness_to_glyph(grid[row_idx, col_idx]) for col_idx in range(COLS)
        )
        row_chars_escaped = (
            row_chars.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        )

        clip_id = f"clip-row-{row_idx}"
        y = (row_idx + 1) * CHAR_H
        begin = (row_idx * ROW_DELAY_MS) / 1000.0

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'<rect x="0" y="{y - CHAR_H:.1f}" width="0" height="{CHAR_H}">')
        parts.append(
            f'<animate attributeName="width" from="0" to="{width:.0f}" '
            f'begin="{begin:.3f}s" dur="{ROW_DRAW_MS / 1000:.3f}s" fill="freeze"/>'
        )
        parts.append("</rect>")
        parts.append("</clipPath>")

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(
            f'<text x="0" y="{y:.1f}" xml:space="preserve">{row_chars_escaped}</text>'
        )
        parts.append("</g>")

    parts.append("</svg>")
    return "\n".join(parts)


def main():
    if not INPUT_PATH.exists():
        print(f"Missing {INPUT_PATH}. Run tools/clean_photo.py first.")
        raise SystemExit(1)

    img = Image.open(INPUT_PATH)
    grid = image_to_grid(img)
    svg = build_svg(grid)

    OUTPUT_PATH.write_text(svg, encoding="utf-8")
    print(f"Saved: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
