"""Build trivia.js from Unrivaled's official stats and standings pages.

Collects the top-5 stat leaders (per game and season totals) for every season
that has data, plus the regular-season standings once a season is finished.
The trivia page turns these into multiple-choice questions.
"""
import json
import re
import sys
from html.parser import HTMLParser

import requests

SITE_ROOT = "https://www.unrivaled.basketball"
FIRST_SEASON = 2025
# Leader categories as they appear on /stats: abbreviation -> label on the page
CATEGORIES = {"PTS": "Points", "AST": "Assists", "3PM": "3-Pointers Made", "GW": "Game Winners",
              "REB": "Rebounds", "BLK": "Blocks", "STL": "Steals", "MIN": "Minutes"}


def fetch(url):
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (unrivaled-guessing-game)"}, timeout=30)
    resp.raise_for_status()
    return resp.text


class PageText(HTMLParser):
    """Visible text of a page as a flat list of tokens (scripts and styles skipped)."""

    def __init__(self):
        super().__init__()
        self.tokens, self.skip = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in ("script", "style", "svg"):
            self.skip += 1

    def handle_endtag(self, tag):
        if tag in ("script", "style", "svg"):
            self.skip -= 1

    def handle_data(self, data):
        if not self.skip and data.strip():
            self.tokens.append(" ".join(data.split()))


class TableRows(HTMLParser):
    """Collects each <tbody> row as a list of cell texts."""

    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell, self.in_body = [], None, None, False

    def handle_starttag(self, tag, attrs):
        if tag == "tbody":
            self.in_body = True
        elif tag == "tr" and self.in_body:
            self.row = []
        elif tag == "td" and self.row is not None:
            self.cell = []

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_body = False
        elif tag == "td" and self.cell is not None:
            self.row.append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def page_tokens(url):
    parser = PageText()
    parser.feed(fetch(url))
    return parser.tokens


def parse_leaders(tokens):
    """Read each category's ranked list: label, abbr, then (rank, name, club, value) groups."""
    leaders = {}
    for i in range(len(tokens) - 1):
        abbr = tokens[i + 1]
        if abbr not in CATEGORIES or tokens[i] != CATEGORIES[abbr]:
            continue
        entries, j = [], i + 2
        while j + 3 < len(tokens) and tokens[j].isdigit() and re.fullmatch(r"[\d.]+", tokens[j + 3]):
            entries.append({"rank": int(tokens[j]), "name": tokens[j + 1], "team": tokens[j + 2], "value": tokens[j + 3]})
            j += 4
        if entries:
            leaders[abbr] = entries
    return leaders


def fetch_leaders():
    seasons = []
    for season in range(FIRST_SEASON, 2100):
        per_game = parse_leaders(page_tokens(f"{SITE_ROOT}/stats?season={season}"))
        if not per_game:
            break  # first season without stats yet (or not created on the site)
        totals = parse_leaders(page_tokens(f"{SITE_ROOT}/stats?season={season}&perMode=Total"))
        seasons.append({"season": season, "perGame": per_game, "total": totals})
        print(f"{season}: {len(per_game)} per-game and {len(totals)} total categories")
    return seasons


def fetch_standings():
    """Current standings page. Only kept once every club has a clinch/elimination mark (season over)."""
    tokens = page_tokens(f"{SITE_ROOT}/standings")
    title = next((t for t in tokens if re.fullmatch(r"\d{4} Standings", t)), "")
    parser = TableRows()
    parser.feed(fetch(f"{SITE_ROOT}/standings"))
    teams = []
    for row in parser.rows:
        # Cells: rank+club+clinch mark run together (e.g. "1PhantomX"), W, L, PCT, GB, PF, PA, DIFF, STRK
        if len(row) < 9:
            continue
        match = re.fullmatch(r"(\d+)\s*(.+?)\s*([XYZE]?)", row[0])
        if not match:
            continue
        teams.append({"team": match.group(2), "mark": match.group(3), "w": int(row[1]), "l": int(row[2]),
                      "pf": int(row[5]), "pa": int(row[6]), "diff": int(row[7].replace(" ", "").replace("+", ""))})
    if not title or not teams or not all(t["mark"] for t in teams):
        print("Standings: season not finished yet, skipping.")
        return []
    for t in teams:
        del t["mark"]
    print(f"Standings: {title} with {len(teams)} clubs")
    return [{"season": int(title[:4]), "teams": teams}]


if __name__ == "__main__":
    try:
        data = {"leaders": fetch_leaders(), "standings": fetch_standings()}
    except Exception as e:
        print(f"Error fetching trivia data: {e}")
        sys.exit(1)
    # Guard against a page redesign silently wiping the question bank.
    if not data["leaders"]:
        print("Warning: no stat leaders found; leaving trivia.js unchanged.")
        sys.exit(1)
    with open("trivia.js", "w", encoding="utf-8") as f:
        f.write(f"const triviaData = {json.dumps(data, indent=2, ensure_ascii=False)};\n")
    print("Saved trivia data to trivia.js")
