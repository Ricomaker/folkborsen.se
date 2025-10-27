"""Scraper for Freemelt press releases.

Exposes: scrape_press_releases() -> List[dict]

Each item dict shape (used by generate_feed.generate_rss):
  - title: str
  - link: str
  - date: YYYY-MM-DD (or None)
  - summary: short description
  - source: origin domain

This file is intentionally small and dependency-light. It fetches the listing
page and extracts the containers using the `.investor-blocks-content-inner-press-releases-item`
selector discovered in the page HTML.
"""
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time

HEADERS = {"User-Agent": "folkborsen-scraper/1.0 (+https://folkborsen.se)"}
LISTING_URL = "https://freemelt.com/investors/press-releases/"


def _parse_date(text: str) -> Optional[str]:
    if not text:
        return None
    text = text.strip()
    # Try ISO first
    try:
        dt = datetime.fromisoformat(text)
        return dt.date().isoformat()
    except Exception:
        pass
    # Very small, local parsing for formats like '8 Oct 2025' or '24 Sep 2025'
    try:
        dt = datetime.strptime(text, "%d %b %Y")
        return dt.date().isoformat()
    except Exception:
        pass
    try:
        dt = datetime.strptime(text, "%d %B %Y")
        return dt.date().isoformat()
    except Exception:
        pass
    # Last resort: try to extract a 4-digit year and return a partial date
    import re
    m = re.search(r"(\d{4})", text)
    if m:
        return f"{m.group(1)}-01-01"
    return None


def scrape_press_releases(include_hidden: bool = False, session: Optional[requests.Session] = None, html: Optional[str] = None) -> List[Dict]:
    """Scrape the Freemelt press release listing and return items.

    include_hidden: whether to include nodes with `style="display: none"`.
    session: optional requests.Session to use.
    html: optional raw HTML string to parse (used for unit tests) — when
          provided, the function will parse html instead of performing a
          network request.
    """
    s = session or requests.Session()
    if html is None:
        r = s.get(LISTING_URL, headers=HEADERS, timeout=20)
        r.raise_for_status()
        doc = r.text
    else:
        doc = html

    soup = BeautifulSoup(doc, "html.parser")

    nodes = soup.select(".investor-blocks-content-inner-press-releases-item")
    out: List[Dict] = []
    for node in nodes:
        style = (node.get("style") or "").lower()
        if not include_hidden and "display: none" in style:
            continue

        a = node.find("a")
        if not a or not a.get("href"):
            continue
        link = a["href"].strip()

        # date is usually the first .pre-title inside .upper
        date_span = node.select_one("div.upper span.pre-title")
        date_text = date_span.get_text(" ", strip=True) if date_span else ""
        date_iso = _parse_date(date_text)

        p = node.find("p")
        summary = p.get_text(" ", strip=True) if p else ""

        title = summary

        out.append({
            "title": title,
            "link": link,
            "date": date_iso or datetime.utcnow().date().isoformat(),
            "summary": summary,
            "source": "freemelt.com",
        })

    # Deduplicate by link preserving order
    seen = set()
    dedup = []
    for it in out:
        if it["link"] in seen:
            continue
        seen.add(it["link"])
        dedup.append(it)

    return dedup


if __name__ == "__main__":
    for i, it in enumerate(scrape_press_releases()[:20], start=1):
        print(i, it["date"], it["title"], it["link"])
        time.sleep(0.05)
