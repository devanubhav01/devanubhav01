"""
Draws the contribution calendar (from assets/contributions.json) as a
grid of rounded squares in a custom accent color ramp, animating in by
column (week) rather than by row.

Usage:
    python tools/render_graph.py
    # writes graph.svg
"""

import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path

INPUT_PATH = Path("assets/contributions.json")
OUTPUT_PATH = Path("graph.svg")

LEVELS = ["#1a1a2e", "#16537e", "#1c7ed6", "#4dabf7", "#a5d8ff"]
# index 0 = no activity, index 4 = top activity tier

BG = "#0d1117"
TEXT = "#c9d1d9"
MUTED = "#6e7681"

CELL = 12
GAP = 3
LEFT_PAD = 40
TOP_PAD = 20
BOTTOM_PAD = 50

COL_STAGGER = 0.03
CELL_FADE_DUR = 0.3


def load_data() -> dict:
    if not INPUT_PATH.exists():
        raise SystemExit(f"Missing {INPUT_PATH}. Run tools/pull_contributions.py first.")
    return json.loads(INPUT_PATH.read_text(encoding="utf-8"))


def group_by_week(days: list[dict]) -> list[list[dict]]:
    if not days:
        return []
    days_sorted = sorted(days, key=lambda d: d["date"])
    first_date = datetime.strptime(days_sorted[0]["date"], "%Y-%m-%d")
    # Align first week to start on Sunday like GitHub's own calendar
    offset = (first_date.weekday() + 1) % 7

    weeks = defaultdict(lambda: [None] * 7)
    for i, day in enumerate(days_sorted):
        idx = i + offset
        week_idx = idx // 7
        weekday = idx % 7
        weeks[week_idx][weekday] = day

    return [weeks[k] for k in sorted(weeks.keys())]


def main():
    data = load_data()
    days = data.get("days", [])
    stats = data.get("stats", {})
    weeks = group_by_week(days)

    n_weeks = len(weeks)
    width = LEFT_PAD + n_weeks * (CELL + GAP)
    height = TOP_PAD + 7 * (CELL + GAP) + BOTTOM_PAD

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" '
        f'height="{height}" viewBox="0 0 {width} {height}">',
        f'<rect width="{width}" height="{height}" fill="{BG}"/>',
        "<defs>",
        f'<style>text {{ font-family: "Courier New", monospace; fill: {TEXT}; }}</style>',
        "</defs>",
    ]

    for week_idx, week in enumerate(weeks):
        x = LEFT_PAD + week_idx * (CELL + GAP)
        begin = week_idx * COL_STAGGER

        for weekday, day in enumerate(week):
            y = TOP_PAD + weekday * (CELL + GAP)
            level = day["level"] if day else 0
            level = max(0, min(level, len(LEVELS) - 1))
            color = LEVELS[level]

            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2" ry="2" '
                f'fill="{color}" opacity="0">'
            )
            parts.append(
                f'<animate attributeName="opacity" from="0" to="1" '
                f'begin="{begin:.2f}s" dur="{CELL_FADE_DUR}s" fill="freeze"/>'
            )
            parts.append("</rect>")

    legend_y = height - BOTTOM_PAD + 24
    parts.append(f'<text x="{LEFT_PAD}" y="{legend_y - 20}" font-size="12">Less</text>')
    lx = LEFT_PAD + 40
    for color in LEVELS:
        parts.append(
            f'<rect x="{lx}" y="{legend_y - 30}" width="{CELL}" height="{CELL}" rx="2" ry="2" fill="{color}"/>'
        )
        lx += CELL + GAP
    parts.append(f'<text x="{lx + 6}" y="{legend_y - 20}" font-size="12">More</text>')

    summary = (
        f"streak: {stats.get('current_streak', 0)}d "
        f"· longest: {stats.get('longest_streak', 0)}d "
        f"· busiest: {stats.get('busiest_day', '—')}"
    )
    parts.append(
        f'<text x="{LEFT_PAD}" y="{legend_y}" font-size="13" fill="{MUTED}">{summary}</text>'
    )

    parts.append("</svg>")

    OUTPUT_PATH.write_text("\n".join(parts), encoding="utf-8")
    print(f"Saved: {OUTPUT_PATH} ({n_weeks} weeks)")


if __name__ == "__main__":
    main()
