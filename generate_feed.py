"""Generate a small RSS 2.0 feed from a list of item dicts.

This module exposes generate_rss(items, ..., dedupe_by_title=False).
It conservatively deduplicates by link and optionally by a normalized
title form (lowercased, punctuation removed, whitespace collapsed).
"""
from datetime import datetime
import xml.etree.ElementTree as ET
import re
import string


def _normalize_title(t: str) -> str:
    if not t:
        return ""
    s = t.lower()
    s = s.translate(str.maketrans('', '', string.punctuation))
    s = re.sub(r"\s+", " ", s).strip()
    return s


def generate_rss(items, feed_title="Folkborsen Microcap News", feed_link="https://folkborsen.se", feed_desc="Fast RSS feed of Swedish small-cap IR press releases", dedupe_by_title=False):
    """Create an RSS XML string from items.

    items: iterable of dicts with at least 'title' and 'link' (and optional 'date','summary','source').
    dedupe_by_title: if True, drop later items whose normalized title matches an earlier one.
    """
    if not items:
        return "<rss version='2.0'><channel><title>No items</title></channel></rss>"

    # Deduplicate by link first (preserve first occurrence)
    seen_links = set()
    unique_items = []
    for it in items:
        link = (it.get('link') or it.get('url') or '').strip()
        if not link:
            unique_items.append(it)
            continue
        if link in seen_links:
            continue
        seen_links.add(link)
        unique_items.append(it)

    # Optional dedupe by normalized title
    if dedupe_by_title:
        seen_titles = set()
        filtered = []
        for it in unique_items:
            title = it.get('title', '')
            norm = _normalize_title(title)
            if norm and norm in seen_titles:
                # skip duplicates by normalized title
                continue
            if norm:
                seen_titles.add(norm)
            filtered.append(it)
        unique_items = filtered

    items = unique_items

    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = feed_title
    ET.SubElement(channel, 'link').text = feed_link
    ET.SubElement(channel, 'description').text = feed_desc
    ET.SubElement(channel, 'language').text = 'sv'

    # channel pubDate from latest item date when possible
    try:
        latest_dates = [x.get('date') for x in items if x.get('date')]
        if latest_dates:
            latest_date = max(latest_dates)
            m = re.search(r"(\d{4}-\d{2}-\d{2})", latest_date)
            channel_pub = datetime.strptime(m.group(1), '%Y-%m-%d') if m else datetime.now()
        else:
            channel_pub = datetime.now()
        ET.SubElement(channel, 'pubDate').text = channel_pub.strftime('%a, %d %b %Y %H:%M:%S %z')
    except Exception:
        ET.SubElement(channel, 'pubDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')

    # Emit up to 20 items (preserve order)
    for item in items[-20:]:
        entry = ET.SubElement(channel, 'item')
        ET.SubElement(entry, 'title').text = item.get('title', '')
        ET.SubElement(entry, 'link').text = item.get('link', '')
        summary = item.get('summary') or f"Source: {item.get('source', '')} | Date: {item.get('date', '')}"
        ET.SubElement(entry, 'description').text = summary
        date_str = item.get('date', '')
        try:
            m = re.search(r"(\d{4}-\d{2}-\d{2})", date_str)
            date_obj = datetime.strptime(m.group(1), '%Y-%m-%d') if m else datetime.now()
        except Exception:
            date_obj = datetime.now()
        ET.SubElement(entry, 'pubDate').text = date_obj.strftime('%a, %d %b %Y %H:%M:%S %z')
        ET.SubElement(entry, 'guid').text = item.get('link', '')
        ET.SubElement(entry, 'category').text = 'Microcap IR'

    return ET.tostring(rss, encoding='unicode', method='xml')


if __name__ == '__main__':
    # quick smoke test when executed directly
    sample = [
        {'title': 'A', 'link': 'https://example.com/1', 'date': '2025-10-01'},
        {'title': 'A', 'link': 'https://example.com/2', 'date': '2025-10-02'},
    ]
    print(generate_rss(sample, dedupe_by_title=True))
