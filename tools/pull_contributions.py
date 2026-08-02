"""
Pulls the public contribution calendar HTML fragment GitHub serves for a
profile page (no OAuth / token required) and saves the parsed daily
counts, plus a few derived stats, as JSON.

Usage:
    python tools/pull_contributions.py
    # writes assets/contributions.json
"""

import json
import os
from datetime import datetime
from pathlib import Path

import httpx
from lxml import html

USERNAME = os.environ.get("GITHUB_USERNAME", "devanubhav01")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT_PATH = Path("assets/contributions.json")


def fetch_contributions() -> list[dict]:
    resp = httpx.get(URL, timeout=20, headers={"User-Agent": "profile-readme-bot"})
    resp.raise_for_status()
    tree = html.fromstring(resp.text)

    days = []
    # GitHub renders each day as a <td> with a data-date and either a
    # data-level attribute or an aria-label containing the count.
    cells = tree.xpath('//td[@data-date]')
    for cell in cells:
        date_str = cell.get("data-date")
        level = cell.get("data-level")
        if level is None:
            # older markup fallback: derive level from class name
            css_class = cell.get("class", "")
            level = next(
                (c.replace("day-", "") for c in css_class.split() if c.startswith("day-")),
                "0",
            )
        try:
            level_int = int(level)
        except (TypeError, ValueError):
            level_int = 0

        days.append({"date": date_str, "level": level_int})

    return days


def compute_stats(days: list[dict]) -> dict:
    days_sorted = sorted(days, key=lambda d: d["date"])

    current_streak = 0
    longest_streak = 0
    running = 0
    for day in days_sorted:
        if day["level"] > 0:
            running += 1
            longest_streak = max(longest_streak, running)
        else:
            running = 0

    for day in reversed(days_sorted):
        if day["level"] > 0:
            current_streak += 1
        else:
            break

    weekday_totals = [0] * 7
    for day in days_sorted:
        dt = datetime.strptime(day["date"], "%Y-%m-%d")
        weekday_totals[dt.weekday()] += day["level"]

    weekday_names = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    busiest_day = weekday_names[weekday_totals.index(max(weekday_totals))] if days_sorted else None

    return {
        "current_streak": current_streak,
        "longest_streak": longest_streak,
        "busiest_day": busiest_day,
        "total_active_days": sum(1 for d in days_sorted if d["level"] > 0),
    }


def main():
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    print(f"Fetching contributions for {USERNAME}...")
    days = fetch_contributions()

    if not days:
        print("No contribution cells found — GitHub markup may have changed.")

    stats = compute_stats(days)

    payload = {
        "username": USERNAME,
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "days": days,
        "stats": stats,
    }

    OUTPUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved: {OUTPUT_PATH} ({len(days)} days)")


if __name__ == "__main__":
    main()
