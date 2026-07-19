# Workflow and Architecture Summary

## Project Overview
This project monitors configured websites for new articles and sends real-time push notifications using a self-hosted `ntfy` server. It has been refactored into a modular "plug-and-play" architecture to easily accommodate new websites with minimal code duplication.

## Architecture
1. **`config.json`**: The central configuration hub. Stores `ntfy` credentials, database settings, and a list of monitored websites. Each website can be toggled on/off (`enabled`) and routed to a specific `ntfy` topic.
2. **`core/base_scraper.py`**: The engine of the project. It handles database initialization, deduplication (checking if an article was already sent), and the API request to the `ntfy` server.
3. **`scrapers/` Directory**: Contains site-specific scraping modules (e.g., `the_decoder.py`). Each module inherits from `BaseScraper` and is only responsible for extracting the URL, title, content, and publish date from the specific website.
4. **`main.py`**: The runner script. It accepts an optional `--site` argument to run a specific scraper, or loops through all enabled sites in `config.json`.
5. **`setup_cron.py`**: A utility script that dynamically calculates a 10-minute offset for each website and generates the appropriate cron jobs, preventing server resource spikes.
6. **`install.sh`**: The deployment script that sets up the Python virtual environment, installs dependencies, and runs `setup_cron.py`.

## Development & Deployment Workflow
1. **Local Development**: Add new websites locally by creating a new Python module in the `scrapers/` folder and adding the entry to `config.json`.
2. **Local Testing**: Run the scraper locally (`python main.py --site site_name`) to verify content extraction and notification delivery.
3. **Server Deployment**: Copy the updated project files to the target server (e.g., `powersrv-small`).
4. **Cron Setup**: Run `./install.sh` on the server. This automatically applies the new configuration and cleanly updates the staggered cron schedules without manual intervention.
