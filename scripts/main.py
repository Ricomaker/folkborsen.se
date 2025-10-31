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
            # placeholders for article-level fields filled later if requested
            "article_title": None,
            "article_excerpt": None,
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


def _allowed_by_robots(url: str, session: requests.Session) -> bool:
    """Simple robots.txt check for the given URL's origin."""
    from urllib.parse import urlparse, urlunparse
    from urllib.robotparser import RobotFileParser

    parsed = urlparse(url)
    base = urlunparse((parsed.scheme, parsed.netloc, '', '', '', ''))
    robots_url = base + '/robots.txt'

    # Cache parser on session to avoid repeated downloads
    rp_key = f'robots::{parsed.netloc}'
    rp = getattr(session, rp_key, None)
    if rp is None:
        rp = RobotFileParser()
        try:
            resp = session.get(robots_url, headers=HEADERS, timeout=8)
            if resp.status_code == 200:
                rp.parse(resp.text.splitlines())
            else:
                # If robots.txt missing, assume allowed
                rp = None
        except Exception:
            rp = None
        setattr(session, rp_key, rp)

    if rp is None:
        return True
    return rp.can_fetch(HEADERS.get('User-Agent', '*'), url)


def _fetch_article_fields(url: str, session: requests.Session, timeout: int = 15) -> Dict[str, Optional[str]]:
    """Fetch article page and extract <h1> and first meaningful <p>.

    Returns dict with keys: article_title, article_excerpt
    """
    try:
        if not _allowed_by_robots(url, session):
            return {"article_title": None, "article_excerpt": None}
        r = session.get(url, headers=HEADERS, timeout=timeout)
        r.raise_for_status()
        s = BeautifulSoup(r.text, 'html.parser')
        # Try typical article title selectors
        h1 = s.find('h1')
        article_title = h1.get_text(' ', strip=True) if h1 else None

        # Find first paragraph with some length
        article_excerpt = None
        for p in s.find_all('p'):
            text = p.get_text(' ', strip=True)
            if text and len(text) > 30:
                article_excerpt = text
                break

        return {"article_title": article_title, "article_excerpt": article_excerpt}
    except Exception:
        return {"article_title": None, "article_excerpt": None}


def enrich_with_articles(items: List[Dict], session: Optional[requests.Session] = None, delay: float = 0.5, max_fetch: Optional[int] = None) -> List[Dict]:
    """Optionally fetch each article and fill article_title/article_excerpt.

    - delay: seconds to wait between requests (politeness)
    - max_fetch: if set, limit number of articles to fetch
    """
    s = session or requests.Session()
    count = 0
    for it in items:
        if max_fetch is not None and count >= max_fetch:
            break
        url = it.get('link')
        if not url:
            continue
        fields = _fetch_article_fields(url, s)
        it['article_title'] = fields.get('article_title')
        it['article_excerpt'] = fields.get('article_excerpt')
        # If article_title found, use it as the canonical title
        if it['article_title']:
            it['title'] = it['article_title']
        # Use excerpt if available to populate summary
        if it['article_excerpt']:
            it['summary'] = it['article_excerpt']
        count += 1
        time.sleep(delay)
    return items


if __name__ == "__main__":
    for i, it in enumerate(scrape_press_releases()[:20], start=1):
        print(i, it["date"], it["title"], it["link"])
        time.sleep(0.05)
