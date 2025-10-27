import pytest
from pathlib import Path
import importlib.util


def load_fixture(name: str) -> str:
    p = Path(__file__).parent / 'fixtures' / name
    return p.read_text(encoding='utf-8')


def load_module_from_path(path: Path):
    spec = importlib.util.spec_from_file_location('scripts_main', str(path))
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


@pytest.fixture(scope='module')
def scraper_module():
    p = Path(__file__).parent.parent / 'scripts' / 'main.py'
    return load_module_from_path(p)


def test_scrape_listing_default_skips_hidden(scraper_module):
    html = load_fixture('sample_listing.html')
    items = scraper_module.scrape_press_releases(html=html)
    # default should skip the hidden (display:none) entry, so expect 2
    assert len(items) == 2
    assert items[0]['link'] == 'https://freemelt.com/mfn_news_en/press-release-1/'
    assert items[0]['title'].startswith('Press release from')


def test_scrape_listing_include_hidden(scraper_module):
    html = load_fixture('sample_listing.html')
    items = scraper_module.scrape_press_releases(html=html, include_hidden=True)
    # should include the hidden entry now
    assert len(items) == 3
    links = [i['link'] for i in items]
    assert 'https://freemelt.com/mfn_news_en/press-release-archived/' in links
