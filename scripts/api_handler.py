from main import scrape_press_releases
from generate_feed import generate_rss

def handler(request=None):
    # This script was previously the root file named `api`.
    # Keep it as a callable helper in scripts/ so it can be used by Python-based workflows.
    items = scrape_press_releases()
    rss_xml = generate_rss(items)
    return {
        'statusCode': 200,
        'headers': {'Content-Type': 'application/xml; charset=utf-8'},
        'body': rss_xml
    }

if __name__ == '__main__':
    # simple local test
    result = handler()
    with open('folkborsen_feed.xml', 'w', encoding='utf-8') as f:
        f.write(result['body'])
    print('Wrote folkborsen_feed.xml (from scripts/api_handler.py)')
