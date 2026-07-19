# Roadmap: Refactoring & Deployment

## Phase 1: Architectural Refactoring (The "Plug-in" System)
To make adding new websites (like `byte.to`) effortless, we need to move away from a single, hardcoded script and adopt a modular architecture.
1. **Configuration File**: Move all hardcoded variables (ntfy credentials, base URLs, topics) into a `config.json` or `.env` file.
2. **Database Update**: Modify the SQLite database schema to add a `source_site` column. This allows all scraped articles from multiple websites to live safely in the same database table without colliding.
3. **Base Scraper Class**: Create a `BaseScraper` Python class that handles the universal logic (checking the database for duplicates, connecting to the database, pushing to ntfy).
4. **Site-Specific Modules**: Create a `scrapers/` folder. Adding a new site will simply mean creating a short script (e.g., `scrapers/byte_to.py`) that inherits from `BaseScraper` and only contains the site-specific parsing logic (e.g., which HTML `<div>` to look for).
5. **Main Runner (`main.py`)**: A centralized script that iterates through all active scrapers in the `scrapers/` folder and executes them sequentially.

## Phase 2: Notification Flexibility
1. **Dynamic Ntfy Routing**: Update the ntfy function to accept dynamic parameters. We can configure it so that different websites can either share a single master topic or send alerts to their own separate topics (e.g., `/byte-to-updates` vs `/the-decoder-updates`).

## Phase 3: Server Deployment & Scheduling
1. **Environment Preparation**: Ensure `requirements.txt` is up-to-date and generate a setup script (`setup.sh`) to easily clone the repo and initialize the database on the server.
2. **Cron Scheduling**: Since you want very specific times (7:00, 12:30, 18:30), Linux `cron` is the best, most reliable tool for the job. We will prepare the following cron expressions to run on the server:
   * `0 7 * * * cd /path/to/project && venv/bin/python main.py` (Runs at 07:00)
   * `30 12,18 * * * cd /path/to/project && venv/bin/python main.py` (Runs at 12:30 and 18:30)

---

## Open Questions for Implementation

1. **Scraping vs RSS**: Will future sites like `byte.to` primarily be scraped via raw HTML, or do they usually have RSS feeds we can utilize?
2. **Notification Topics**: Do you want alerts from all websites to go to the **same** ntfy topic on your phone, or should each website have its **own** separate topic?
3. **Database**: SQLite is perfect for this, but just to be sure—do you expect to store tens of thousands of articles long-term, or is this primarily just to keep track of what has already been sent? 
4. **Deployment Target**: Assuming we deploy to `powersrv-small`, shall I write an automated bash script that sets up the virtual environment and installs the cron jobs automatically?
