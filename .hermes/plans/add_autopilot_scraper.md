# Plan: Add "The Autopilot" to ntfy scraper system

## Phase 1: Analysis
- Fetch `https://www.the-autopilot.com/` to identify how it structures its articles.
- Check if an RSS feed exists (typically at `/rss`, `/feed`, or `/posts/rss`).
- If no RSS, determine the CSS selectors for article lists and individual post content.

## Phase 2: Configuration
- Add a new site entry to `config.json` for "The Autopilot".
- Choose a unique module name, e.g., `the_autopilot`.
- Define an appropriate topic for the ntfy alert.

## Phase 3: Implementation
- Create `scrapers/the_autopilot.py` following the pattern of `scrapers/the_decoder.py`.
- Implement `fetch_new_articles()`:
    - If RSS exists, use `feedparser`.
    - If no RSS, use `BeautifulSoup` to crawl the home page for article links and extract content.
- Inherit from `core.base_scraper.BaseScraper`.

## Phase 4: Verification
- Execute `python3 main.py --site the_autopilot`.
- Check `articles.db` to ensure the new site entries are saved.
- Confirm an ntfy notification is sent (or check the stdout log if live sending is simulated/active).
