import requests
from bs4 import BeautifulSoup
import time
import re
from datetime import datetime
import json
import xml.etree.ElementTree as ET

def scrape_press_releases(sources=None):
    if sources is None:
        sources = [
            {'name': 'Midsummer', 'url': 'https://midsummer.se/investerare/', 'selector': '.mfn_news'},
            {'name': 'Railway Metrics', 'url': 'https://railwaymetrics.com/investor/pressreleases/', 'selector': 'table tr'},
            {'name': 'Odinwell', 'url': 'https://odinwell.com/investors-media/pressreleaser/', 'selector': 'a[href*="?news_id="]'},
            {'name': 'Freemelt', 'url': 'https://freemelt.com/investors/press-releases/', 'selector': '.investor-blocks-content-inner-press-releases-item'}
        ]
    
    items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
    }
    
    for source in sources:
        try:
            print(f"Fetching {source['url']}...")
            resp = requests.get(source['url'], headers=headers)
            resp.raise_for_status()
            print(f"Status code: {resp.status_code}")
            soup = BeautifulSoup(resp.text, 'html.parser')
            print(f"Found {len(soup.select(source['selector']))} elements with {source['selector']}")
            
            articles = soup.select(source['selector'])[:5]
            for article in articles:
                if source['name'] == 'Railway Metrics':
                    title_elem = article.select_one('td:nth-child(2)')
                    link_elem = article.select_one('td:nth-child(3) a')
                    date_elem = article.select_one('td:nth-child(1)')
                    
                    if title_elem and link_elem and date_elem:
                        title = title_elem.get_text(strip=True)
                        link = link_elem.get('href')
                        date_str = date_elem.get_text(strip=True)
                        date = f"20{date_str[:2]}-{date_str[2:4]}-{date_str[4:]}" if len(date_str) == 6 else datetime.now().strftime('%Y-%m-%d')
                        items.append({'title': title, 'link': link, 'date': date, 'source': source['name']})
                elif source['name'] == 'Odinwell':
                    parent_text = article.find_parent().get_text(strip=True) if article.find_parent() else soup.get_text(strip=True)
                    match = re.search(r'$$ (\d{4}-\d{2}-\d{2}\s\d{2}:\d{2}) $$\s(.*?)\s\[](https://[^\)]+)\)', parent_text)
                    if match:
                        date = match.group(1)
                        title = match.group(2).rstrip('.')
                        link = match.group(3)
                        items.append({'title': title, 'link': link, 'date': date, 'source': source['name']})
                elif source['name'] == 'Freemelt':
                    link_elem = article.select_one('a')
                    date_elem = article.select_one('.upper .pre-title')
                    title_elem = article.select_one('p')
                    
                    if link_elem and date_elem and title_elem:
                        link = link_elem.get('href')
                        date_str = date_elem.get_text(strip=True).replace('Oct', '10').replace('Sep', '09').replace('Aug', '08').replace('Jul', '07').replace('Jun', '06').replace('May', '05').replace('Apr', '04').replace('Mar', '03').replace('Feb', '02').replace('Jan', '01')
                        date = f"2025-{date_str.split()[1]}-{date_str.split()[0]}" if '2025' in article.get('class', []) else f"2024-{date_str.split()[1]}-{date_str.split()[0]}"
                        title = title_elem.get_text(strip=True)
                        items.append({'title': title, 'link': link, 'date': date, 'source': source['name']})
                else:
                    title_elem = article.select_one('h3 a, .title a, a') or article
                    link_elem = article.select_one('a')
                    date_elem = article.select_one('.date, time')
                    
                    if title_elem:
                        title = title_elem.get_text(strip=True) or (link_elem.get_text(strip=True) if link_elem else 'Untitled')
                        link = link_elem.get('href') if link_elem else source['url']
                        if link and link.startswith('/'):
                            link = source['url'].rpartition('/')[0] + link
                        date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
                        date = re.search(r'(\d{4}-\d{2}-\d{2})', date_str).group(1) if re.search(r'(\d{4}-\d{2}-\d{2})', date_str) else date_str
                        items.append({'title': title, 'link': link, 'date': date, 'source': source['name']})
            
            print(f"Scraped {len(articles)} items from {source['name']}")
            time.sleep(2)
        except Exception as e:
            print(f"Error scraping {source['name']}: {e}")
    
    items.sort(key=lambda x: x['date'], reverse=True)
    return items

def generate_rss(items, feed_title="Folkborsen Microcap News", feed_link="https://folkborsen.se", feed_desc="Fast RSS feed of Swedish small-cap IR press releases"):
    if not items:
        return "<rss version='2.0'><channel><title>No items</title></channel></rss>"
    
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = feed_title
    ET.SubElement(channel, 'link').text = feed_link
    ET.SubElement(channel, 'description').text = feed_desc
    ET.SubElement(channel, 'language').text = 'sv'
    ET.SubElement(channel, 'pubDate').text = datetime.strptime(max(items, key=lambda x: x['date'])['date'], '%Y-%m-%d').strftime('%a, %d %b %Y %H:%M:%S %z')
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    
    for item in items[-20:]:
        entry = ET.SubElement(channel, 'item')
        ET.SubElement(entry, 'title').text = item['title']
        ET.SubElement(entry, 'link').text = item['link']
        ET.SubElement(entry, 'description').text = f"Source: {item['source']} | Date: {item['date']}"
        ET.SubElement(entry, 'pubDate').text = item['date']
        ET.SubElement(entry, 'guid').text = item['link']
        ET.SubElement(entry, 'category').text = 'Microcap IR'
    
    rough_string = ET.tostring(rss, 'unicode')
    reparsed = ET.fromstring(rough_string)
    return ET.tostring(reparsed, encoding='unicode', method='xml')

def handler(event, context):
    items = scrape_press_releases()
    rss_xml = generate_rss(items)
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/xml; charset=utf-8'},
        'body': rss_xml
    }

if __name__ == "__main__":
    items = scrape_press_releases()
    print(json.dumps(items, indent=2))