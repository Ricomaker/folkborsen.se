import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time  # For rate limiting
import re  # For date parsing

def scrape_press_releases(sources=None):
    """
    Scrape press releases from Swedish microcap IR sites.
    sources: List of dicts with 'name', 'url', and optional 'selector' for custom parsing.
    Returns: List of dicts with title, link, date, source.
    """
    if sources is None:
        sources = [
            {
                'name': 'Midsummer',
                'url': 'https://midsummer.se/investerare/',
                'selector': '.mfn_news'  # MFN news list items
            },
            {
                'name': 'Railway Metrics',
                'url': 'https://railwaymetrics.com/investor/pressreleases/',
                'selector': '.news-item a'  # Cision-style links
            },
            {
                'name': 'Odinwell',
                'url': 'https://odinwell.com/investors-media/pressreleaser/',
                'selector': '.press-item h3 a'  # Custom press list
            },
            {
                'name': 'Freemelt',
                'url': 'https://freemelt.com/investors/press-releases/',
                'selector': '.mfn_news_en'  # English MFN items
            }
            # Add Smoltek later if we find a better URL, e.g., their actual press page
        ]
    
    items = []
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }  # Avoid blocks
    
    for source in sources:
        try:
            resp = requests.get(source['url'], headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Find articles (site-specific)
            if 'selector' in source:
                articles = soup.select(source['selector'])
            else:
                articles = soup.select('.news-item, .press-release, article')  # Fallback
            
            for article in articles[:5]:  # Top 5 per source
                title_elem = article.select_one('h3 a, .title a, a') or article
                link_elem = article.select_one('a')
                date_elem = article.select_one('.date, time')
                
                if title_elem:
                    title = title_elem.get_text(strip=True)
                    if not title:  # Fallback to link text
                        title = link_elem.get_text(strip=True) if link_elem else 'Untitled'
                    
                    link = link_elem.get('href') if link_elem else None
                    if link and link.startswith('/'):
                        link = source['url'].rpartition('/')[0] + link  # Base URL fix
                    elif not link:
                        link = source['url']
                    
                    # Parse date (flexible: YYYY-MM-DD or extract from text)
                    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
                    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
                    date = date_match.group(1) if date_match else date_str
                    
                    items.append({
                        'title': title,
                        'link': link,
                        'date': date,
                        'source': source['name']
                    })
            
            time.sleep(2)  # Polite pause
            print(f"Scraped {len(articles[:5])} items from {source['name']}")
        except Exception as e:
            print(f"Error scraping {source['name']}: {e}")
    
    # Sort by date descending (newest first)
    items.sort(key=lambda x: x['date'], reverse=True)
    return items

# Generate JSON output
if __name__ == '__main__':
    news_items = scrape_press_releases()
    print(json.dumps(news_items, indent=2))
