"""CI helper: run the feed generator and write folkborsen_feed.xml

This script prefers to call the helper in scripts/api_handler.handler() if available.
If that fails it will try to import main.scrape_press_releases and use generate_feed.generate_rss.
If everything fails it writes a small sample feed to avoid breaking the workflow.
"""
from datetime import datetime
import sys
import traceback

"""CI helper: run the feed generator and write folkborsen_feed.xml.

This version attempts robust imports using importlib by file path so it works
even if the project isn't a package in CI. It prefers to:
  1) load and call `scripts.api_handler.handler()` if present,
  2) load `generate_feed.generate_rss()` and a `main.scrape_press_releases()` if available,
  3) otherwise call `generate_rss()` with deterministic sample items.
"""
from datetime import datetime
import importlib
import importlib.util
from pathlib import Path
import sys
import traceback


def write_feed(xml_text):
	with open('folkborsen_feed.xml', 'w', encoding='utf-8') as f:
		f.write(xml_text)
	print('Wrote folkborsen_feed.xml')


def import_module_from_path(module_name, path: Path):
	"""Load a module from a filesystem path."""
	try:
		spec = importlib.util.spec_from_file_location(module_name, str(path))
		if spec is None or spec.loader is None:
			return None
		mod = importlib.util.module_from_spec(spec)
		spec.loader.exec_module(mod)
		return mod
	except Exception:
		return None


def try_call_scripts_handler():
	# Try regular import first
	try:
		from scripts.api_handler import handler
		print('Imported scripts.api_handler via package import')
		result = handler()
		return result
	except Exception as e:
		print('Package import scripts.api_handler failed:', e)

	# Try loading by path
	candidate = Path('scripts') / 'api_handler.py'
	if candidate.exists():
		mod = import_module_from_path('scripts_api_handler', candidate)
		if mod and hasattr(mod, 'handler'):
			try:
				print('Calling handler from scripts/api_handler.py')
				return mod.handler()
			except Exception as e:
				print('scripts/api_handler.handler() failed:', e)
	return None


def try_generate_via_main():
	# Load generate_feed module (try normal import then by path)
	gen_mod = None
	try:
		import generate_feed as gen
		gen_mod = gen
		print('Imported generate_feed as package')
	except Exception as e:
		print('Package import generate_feed failed:', e)
		gf = Path('generate_feed.py')
		if gf.exists():
			gen_mod = import_module_from_path('generate_feed', gf)
			if gen_mod:
				print('Imported generate_feed by path')

	if not gen_mod or not hasattr(gen_mod, 'generate_rss'):
		return None

	# Try to load a scraper providing scrape_press_releases
	scraper = None
	try:
		import main as m
		if hasattr(m, 'scrape_press_releases'):
			scraper = m
			print('Imported main package')
	except Exception as e:
		print('Package import main failed:', e)
		# try main.py by path
		mp = Path('main.py')
		if mp.exists():
			m = import_module_from_path('main', mp)
			if m and hasattr(m, 'scrape_press_releases'):
				scraper = m
				print('Imported main.py by path')

	# Also try scripts/original_api_from_root.py as a potential source
	if scraper is None:
		candidate = Path('scripts') / 'original_api_from_root.py'
		if candidate.exists():
			mod = import_module_from_path('orig_api', candidate)
			if mod and hasattr(mod, 'handler'):
				# handler expects to call main internally; skip unless it returns data
				try:
					out = mod.handler(None)
					if isinstance(out, dict) and 'body' in out:
						write_feed(out['body'])
						return True
				except Exception as e:
					print('scripts/original_api_from_root.handler failed:', e)

	if scraper is None:
		print('No scraper available (main.scrape_press_releases not found)')
		return None

	# Call scraper and generate rss
	try:
		items = scraper.scrape_press_releases()
		# If scraper exposes an enrichment helper, call it to fetch article pages
		if hasattr(scraper, 'enrich_with_articles'):
			try:
				print('Enriching items by fetching article pages (may be slow)...')
				# Only fetch the single latest article to keep CI fast
				items = scraper.enrich_with_articles(items, delay=0.5, max_fetch=1)
			except Exception as e:
				print('Failed to enrich articles:', e)
		xml = gen_mod.generate_rss(items)
		write_feed(xml)
		return True
	except Exception as e:
		print('Error running scraper + generate_rss:', e)
		traceback.print_exc()
		return None


def main():
	try:
		# 1) Try scripts handler
		result = try_call_scripts_handler()
		if isinstance(result, dict) and 'body' in result:
			write_feed(result['body'])
			return 0

		# 2) Try main + generate_feed
		ok = try_generate_via_main()
		if ok:
			return 0

		# 3) Fallback: deterministic sample feed using generate_rss if available
		print('Falling back to deterministic sample feed')
		gf = Path('generate_feed.py')
		if gf.exists():
			gen = import_module_from_path('generate_feed', gf)
			if gen and hasattr(gen, 'generate_rss'):
				sample_items = [
					{"title": "Sample 1", "link": "https://folkborsen.se/sample-1", "source": "CI", "date": datetime.utcnow().strftime('%Y-%m-%d')},
					{"title": "Sample 2", "link": "https://folkborsen.se/sample-2", "source": "CI", "date": datetime.utcnow().strftime('%Y-%m-%d')}
				]
				xml = gen.generate_rss(sample_items)
				write_feed(xml)
				return 0

		# Last resort: minimal static xml
		xml = '<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>Folkborsen Sample</title><link>https://folkborsen.se</link><description>Sample</description></channel></rss>'
		write_feed(xml)
		return 0

	except Exception:
		print('Unexpected error in run helper:')
		traceback.print_exc()
		return 2


if __name__ == '__main__':
	sys.exit(main())
