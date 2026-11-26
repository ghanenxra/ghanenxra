import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

USERNAME = "ghanenxra"
API_HEADERS = {"User-Agent": "terminal-stats-updater"}


def fetch_json(url, token=None):
    headers = API_HEADERS.copy()
    headers["Accept"] = "application/vnd.github+json" if "api.github.com" in url else "application/json"
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = Request(url, headers=headers)
    with urlopen(request, timeout=30) as response:
        return json.load(response)


def get_year_contributions(year):
    url = f"https://github-contributions-api.jogruber.de/v4/{USERNAME}?y={year}"
    data = fetch_json(url)
    contributions = data.get("contributions")
    if not isinstance(contributions, list):
        raise ValueError("Contribution API response did not contain a contributions list")
    return sum(day["count"] for day in contributions)


def get_year_commits(year, today, token):
    query = f"author:{USERNAME} author-date:{year}-01-01..{today.isoformat()}"
    url = "https://api.github.com/search/commits?" + urlencode({"q": query, "per_page": 1})
    data = fetch_json(url, token)
    if "total_count" not in data:
        raise ValueError("GitHub commit search response did not contain total_count")
    return data["total_count"]


def replace_metric(svg, y, label, value):
    pattern = re.compile(
        rf'(<text x="16" y="{y}" class="key">)[^<]*(</text>\s*'
        rf'<text x="200" y="{y}" class="val-bright">)[^<]*(</text>)'
    )
    updated, count = pattern.subn(rf"\g<1>{label} :\g<2>{value}\g<3>", svg, count=1)
    if count != 1:
        raise ValueError(f"Could not find the expected metric at y={y}")
    return updated


def main():
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN is required to query commit statistics")

    today = datetime.now(timezone.utc).date()
    year_contributions = get_year_contributions(today.year)
    year_commits = get_year_commits(today.year, today, token)

    svg_path = Path(__file__).resolve().parents[1] / "terminal_stats.svg"
    svg = svg_path.read_text(encoding="utf-8")
    svg = replace_metric(svg, 60, "YTD Contributions", year_contributions)
    svg = replace_metric(svg, 88, "Annual Commits", year_commits)
    svg_path.write_text(svg, encoding="utf-8")


if __name__ == "__main__":
    main()
