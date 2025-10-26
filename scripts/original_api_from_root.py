from main import scrape_press_releases
from generate_feed import generate_rss

def handler(request):
    items = scrape_press_releases()
    rss_xml = generate_rss(items)
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/xml; charset=utf-8'},
        'body': rss_xml
    }