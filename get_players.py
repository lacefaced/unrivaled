"""Build players.js from Unrivaled's official players page.

Unrivaled has no public API, so this reads the player table on
https://www.unrivaled.basketball/players. Players without an Unrivaled photo
borrow their ESPN headshot from the sibling WNBA site's players.js.
"""
import html
import json
import re
import sys
import unicodedata
import urllib.parse
from html.parser import HTMLParser

import requests

PLAYERS_URL = "https://www.unrivaled.basketball/players"
WNBA_DATA_URL = "https://raw.githubusercontent.com/lacefaced/wnba-guessing-game/main/players.js"
SITE_ROOT = "https://www.unrivaled.basketball"


def fetch(url):
    resp = requests.get(url, headers={"User-Agent": "Mozilla/5.0 (unrivaled-guessing-game)"}, timeout=30)
    resp.raise_for_status()
    return resp.text


class PlayersTable(HTMLParser):
    """Collects each <tbody> row as {cells: [text...], href, img_alt, img_src}."""

    def __init__(self):
        super().__init__()
        self.rows, self.row, self.cell = [], None, None
        self.in_body = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "tbody":
            self.in_body = True
        elif tag == "tr" and self.in_body:
            self.row = {"cells": [], "href": "", "img_alt": "", "img_src": ""}
        elif self.row is not None:
            if tag == "td":
                self.cell = []
            elif tag == "a" and not self.row["href"]:
                self.row["href"] = a.get("href", "")
            elif tag == "img" and not self.row["img_alt"]:
                self.row["img_alt"] = a.get("alt", "")
                self.row["img_src"] = a.get("srcset") or a.get("src") or ""

    def handle_endtag(self, tag):
        if tag == "tbody":
            self.in_body = False
        elif tag == "td" and self.row is not None and self.cell is not None:
            self.row["cells"].append(" ".join("".join(self.cell).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None

    def handle_data(self, data):
        if self.cell is not None:
            self.cell.append(data)


def headshot_from_srcset(srcset):
    """Pull the original image URL out of a Next.js /_next/image srcset."""
    match = re.search(r"url=([^&\s]+)", html.unescape(srcset))
    return urllib.parse.unquote(match.group(1)) if match else ""


def name_key(name):
    folded = unicodedata.normalize("NFKD", name)
    folded = "".join(c for c in folded if not unicodedata.combining(c))
    folded = re.sub(r"-smith$", "", folded.lower().replace("’", "'"))
    return re.sub(r"[^a-z' ]", "", folded).strip()


def load_wnba_players():
    try:
        text = fetch(WNBA_DATA_URL)
        body = text[text.index("["): text.rindex("]") + 1]
        return {name_key(p["name"]): p for p in json.loads(body)}
    except Exception as e:
        print(f"Warning: could not load WNBA data for photo fallback: {e}")
        return {}


def clean(value):
    return "" if value in ("", "—", "-", "TBD") else value


def fetch_unrivaled_players():
    parser = PlayersTable()
    parser.feed(fetch(PLAYERS_URL))
    wnba = load_wnba_players()

    players = []
    for row in parser.rows:
        cells = row["cells"] + [""] * 5
        name = row["img_alt"] or cells[0]
        if not name:
            continue
        headshot = headshot_from_srcset(row["img_src"]) if "_next/image" in row["img_src"] else ""
        wnba_match = wnba.get(name_key(name), {})
        players.append({
            "id": row["href"].rstrip("/").split("/")[-1] or name_key(name).replace(" ", "-"),
            "name": name,
            "team": clean(cells[1]),
            "position": clean(cells[2]),
            "height": clean(cells[3]),
            "jersey": clean(cells[4]),
            "wnbaTeam": wnba_match.get("team", ""),
            "profile": SITE_ROOT + row["href"] if row["href"] else "",
            "headshot": headshot or wnba_match.get("headshot", ""),
        })

    print(f"Found {len(players)} players; {sum(1 for p in players if p['headshot'])} with photos.")
    return players


def save_to_js(players, filename="players.js"):
    players_sorted = sorted(players, key=lambda p: p["name"].split()[-1].lower())
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"const allPlayers = {json.dumps(players_sorted, indent=2, ensure_ascii=False)};\n")
    print(f"Saved player data to {filename}")


if __name__ == "__main__":
    try:
        players = fetch_unrivaled_players()
    except Exception as e:
        print(f"Error fetching data: {e}")
        sys.exit(1)
    # Guard against a page redesign silently wiping the roster.
    if len(players) < 20:
        print(f"Warning: only {len(players)} players found; leaving players.js unchanged.")
        sys.exit(1)
    save_to_js(players)
