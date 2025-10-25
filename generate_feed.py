import xml.etree.ElementTree as ET
from io import StringIO
from datetime import datetime

def generate_rss(items, feed_title="Folkborsen Microcap News", feed_link="https://folkborsen.se", feed_desc="Fast RSS feed of small-cap IR press releases"):
    if not items:
        return "<rss version='2.0'><channel><title>No items</title></channel></rss>"
    
    rss = ET.Element('rss', version='2.0')
    channel = ET.SubElement(rss, 'channel')
    ET.SubElement(channel, 'title').text = feed_title
    ET.SubElement(channel, 'link').text = feed_link
    ET.SubElement(channel, 'description').text = feed_desc
    ET.SubElement(channel, 'pubDate').text = datetime.strptime(items[0]['date'], '%Y-%m-%d').strftime('%a, %d %b %Y %H:%M:%S %z')  # Use latest item date
    ET.SubElement(channel, 'lastBuildDate').text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z')
    
    for item in items[-20:]:  # Last 20 items for feed
        entry = ET.SubElement(channel, 'item')
        ET.SubElement(entry, 'title').text = item['title']
        ET.SubElement(entry, 'link').text = item['link']
        ET.SubElement(entry, 'description').text = f"Source: {item['source']} | Date: {item['date']}"  # Dynamic teaser
        ET.SubElement(entry, 'pubDate').text = item['date']  # Use item date
        ET.SubElement(entry, 'guid').text = item['link']
    
    # Pretty XML output
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
