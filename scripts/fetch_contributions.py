"""Scrape the public contribution calendar (no token needed) into data/contributions.json.

    python scripts/fetch_contributions.py            # user from $GH_USER, default brenorlt
"""

import json
import os
import re
from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "contributions.json"
USER = os.environ.get("GH_USER", "brenorlt")


def fetch_days() -> tuple[list[dict], int | None]:
    resp = requests.get(
        f"https://github.com/users/{USER}/contributions",
        headers={"User-Agent": "profile-readme-bot", "Accept": "text/html"},
        timeout=30,
    )
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")

    # counts live in <tool-tip for="contribution-day-component-..."> labels
    counts = {}
    for tip in soup.find_all("tool-tip"):
        m = re.match(r"(\d[\d,]*) contributions? on", tip.get_text(strip=True))
        counts[tip.get("for")] = int(m.group(1).replace(",", "")) if m else 0

    days = []
    for td in soup.select("td.ContributionCalendar-day[data-date]"):
        days.append({
            "date": td["data-date"],
            "count": counts.get(td.get("id"), 0),
            "level": int(td.get("data-level", 0)),
        })
    days.sort(key=lambda d: d["date"])
    if not days:
        raise SystemExit("no contribution cells found; GitHub markup may have changed")

    heading = soup.find(id="js-contribution-activity-description")
    total = None
    if heading and (m := re.search(r"([\d,]+)\s+contributions?", heading.get_text())):
        total = int(m.group(1).replace(",", ""))
    return days, total


def stats(days: list[dict]) -> dict:
    longest = run = 0
    for d in days:
        run = run + 1 if d["count"] else 0
        longest = max(longest, run)

    # today may simply not have activity yet, so the streak can end yesterday
    today = date.fromisoformat(days[-1]["date"])
    by_date = {d["date"]: d["count"] for d in days}
    cursor = today if by_date.get(today.isoformat()) else today - timedelta(days=1)
    current = 0
    while by_date.get(cursor.isoformat()):
        current += 1
        cursor -= timedelta(days=1)

    best = max(days, key=lambda d: d["count"])
    monthly = defaultdict(int)
    for d in days:
        monthly[d["date"][:7]] += d["count"]

    return {
        "current_streak": current,
        "longest_streak": longest,
        "best_day": {"date": best["date"], "count": best["count"]},
        "active_days": sum(1 for d in days if d["count"]),
        "monthly": dict(monthly),
    }


def main() -> None:
    days, total = fetch_days()
    data = {
        "user": USER,
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "total": total if total is not None else sum(d["count"] for d in days),
        "stats": stats(days),
        "days": days,
    }
    OUT.parent.mkdir(exist_ok=True)
    OUT.write_text(json.dumps(data, indent=1) + "\n")
    s = data["stats"]
    print(
        f"{USER}: {data['total']} contributions, {len(days)} days, "
        f"streak {s['current_streak']} (longest {s['longest_streak']})"
    )


if __name__ == "__main__":
    main()
