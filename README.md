# Folkborsen (deployed on Vercel)

This repository contains a small static site and an API endpoint that serves an RSS feed.

What's here
- `index.html` — placeholder homepage
- `folkborsen_feed.xml` — current RSS feed file
- `api/generate-feed.js` — Node handler that returns the feed (with CORS)
- `generate_feed.py` — Python helper that can turn scraped items into RSS XML
- `scripts/run_generator_for_ci.py` — helper used by the GitHub Actions workflow to regenerate the feed
- `.github/workflows/regenerate-feed.yml` — scheduled workflow that regenerates the feed every 6 hours

How to run locally
1. Start the local feed server (Node):
   ```bash
   node api/generate-feed.js
   # then open http://localhost:3000/api/generate-feed
   ```
2. Run the Python generator helper to produce `folkborsen_feed.xml`:
   ```bash
   python3 scripts/run_generator_for_ci.py
   ```

Automation
- The repo includes a GitHub Actions workflow that runs `scripts/run_generator_for_ci.py` every 6 hours and commits `folkborsen_feed.xml` if it changed. That triggers a Vercel redeploy.

Notes
- If your real scraping logic requires network access or credentials, add any secrets to GitHub Actions and update `scripts/run_generator_for_ci.py` accordingly.
# folkborsen.se
Automated microcap IR news scraper and feed generator.
