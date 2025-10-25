import xml.etree.ElementTree as ET
from io import StringIO
from datetime import datetime
import re

def generate_rss(items, feed_title="Folkborsen Microcap News", feed_link="https://folkborsen.se", feed_desc="Fast RSS feed of Swedish small-cap IR press releases"):
    if not items:
        return "<rss version='2.0'><channel><title>No items</title></channel></rss>"
    
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = feed_title
    ET.SubElement(channel, 'link').text = feed_link
    ET.SubElement(channel, 'description').text = feed_desc
    ET.SubElement(channel, 'language').text = 'sv'  # Swedish content hint
    ET.SubElement(channel, 'pubDate').text = datetime.strptime(max(items, key=lambda x: x['date'])['date'], '%Y-%m-%d').strftime('%a, %d %b %Y %H:%M:%S %z')  # Latest item date
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    
    for item in items[-20:]:  # Last 20 items
        entry = ET.SubElement(channel, 'item')
        ET.SubElement(entry, 'title').text = item['title']
        ET.SubElement(entry, 'link').text = item['link']
        ET.SubElement(entry, 'description').text = f"Source: {item['source']} | Date: {item['date']}"  # Dynamic teaser
        # Parse and format date flexibly
        date_str = item['date']
        date_obj = datetime.strptime(re.search(r'(\d{4}-\d{2}-\d{2})', date_str).group(1), '%Y-%m-%d') if re.search(r'(\d{4}-\d{2}-\d{2})', date_str) else datetime.now()
        ET.SubElement(entry, 'pubDate').text = date_obj.strftime('%a, %d %b %Y %H:%M:%S %z')
        ET.SubElement(entry, 'guid').text = item['link']
        ET.SubElement(entry, 'category').text = 'Microcap IR'  # Optional category
    
    rough_string = ET.tostring(rss, 'unicode')
    reparsed = ET.fromstring(rough_string)
    return ET.tostring(reparsed, encoding='unicode', method='xml')

# Example usage (uncomment to test locally)
# from main import scrape_press_releases
# items = scrape_press_releases()
# rss_xml = generate_rss(items)
# with open('folkborsen_feed.xml', 'w', encoding='utf-8') as f:
#     f.write(rss_xml)
# print(rss_xml)
