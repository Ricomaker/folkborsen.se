import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime
import time  # For rate limiting

def scrape_press_releases(sources=None):
    """
    Scrape press releases from microcap IR sources.
    sources: List of dicts like [{'name': 'OTC Markets', 'url': 'https://www.otcmarkets.com/search/press-releases'}]
    Returns: List of dicts with title, link, date, source.
    """
    if sources is None:
        sources = [
            {
                'name': 'OTC Markets Microcaps',
                'url': 'https://www.otcmarkets.com/search/press-releases?query=microcap&sortBy=Most%20Recent'  # Filter for recent microcap news
            },
            # Add more: e.g., {'name': 'GlobeNewswire Small Caps', 'url': 'https://www.globenewswire.com/Search?keywords=small+cap&t=pr'}
        ]
    
    items = []
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}  # Polite scraping
    
    for source in sources:
        try:
            resp = requests.get(source['url'], headers=headers)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # OTC-specific selectors (inspect the page to adapt for other sites)
            articles = soup.select('.press-release-item')  # Adjust: e.g., '.search-result-item' or similar
            for article in articles[:10]:  # Limit to top 10 per source
                title_elem = article.select_one('h3 a') or article.select_one('.title')
                link_elem = article.select_one('a')
                date_elem = article.select_one('.date')
                
                if title_elem and link_elem:
                    title = title_elem.get_text(strip=True)
                    link = link_elem.get('href')
                    if link.startswith('/'):
                        link = 'https://www.otcmarkets.com' + link  # Absolute URL
                    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime('%Y-%m-%d')
                    
                    items.append({
                        'title': title,
                        'link': link,
                        'date': date_str,
                        'source': source['name']
                    })
            
            time.sleep(2)  # Rate limit: 2s between requests
        except Exception as e:
            print(f"Error scraping {source['name']}: {e}")
    
    return items

# Generate JSON output (for debugging or API)
if __name__ == '__main__':
    news_items = scrape_press_releases()
    print(json.dumps(news_items, indent=2))
