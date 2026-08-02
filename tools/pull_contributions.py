"""
Pulls the public contribution calendar HTML fragment GitHub serves for a
profile page (no OAuth / token required) and saves the parsed daily
counts, plus a few derived stats, as JSON.

Uses only httpx + the standard library (re) — no lxml/BeautifulSoup, so
there's nothing here that needs a C++ compiler to install on Windows.

Usage:
    python tools/pull_contributions.py
    # writes assets/contributions.json
"""

import json
import os
import re
from datetime import datetime
from pathlib import Path

import httpx

USERNAME = os.environ.get("GITHUB_USERNAME", "devanubhav01")
URL = f"https://github.com/users/{USERNAME}/contributions"
OUTPUT_PATH = Path("assets/contributions.json")

TD_TAG_RE = re.compile(r"<td\b[^>]*>", re.IGNORECASE)
DATE_ATTR_RE = re.compile(r'data-date="([\d-]+)"')
LEVEL_ATTR_RE = re.compile(r'data-level="(\d+)"')


def fetch_contributions() -> list[dict]:
    resp = httpx.get(URL, timeout=20, headers={"User-Agent": "profile-readme-bot"})
    resp.raise_for_status()
    html_text = resp.text

    days = []
    for tag in TD_TAG_RE.findall(html_text):
        date_match = DATE_ATTR_RE.search(tag)
        if not date_match:
            continue
        level_match = LEVEL_ATTR_RE.search(tag)
        level = int(level_match.group(1)) if level_match else 0
        days.append({"date": date_match.group(1), "level": level})

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
