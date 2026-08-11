# Gemini Guidelines for `ntfy-self-hosted`

This document serves as the core instruction set for any AI agent or Gemini instance working on the `ntfy-self-hosted` project. Read these guidelines carefully before making modifications.

## 1. Project Architecture (Plug-and-Play Scrapers)

This project has been modularized. DO NOT create single, monolithic scripts. Follow this structure:
- **`config.json`**: All credentials, toggles, and monitored websites live here. Do not hardcode credentials in Python files.
- **`core/base_scraper.py`**: Contains the engine (Database initialization using a local SQLite database `articles.db`, deduplication, and sending requests to the `ntfy` server). 
- **`scrapers/`**: Contains site-specific scripts (e.g., `the_decoder.py`, `heise_ki.py`). 
  - *Rule*: Any new website monitor must be added here as a separate class that inherits from `BaseScraper`.
- **`main.py`**: The runner. It can execute all enabled sites or a specific one using `--site`.

## 2. Notification System (`ntfy`)

**CRITICAL:** ALWAYS use the self-hosted ntfy server. NEVER use the public `ntfy.sh`.
- **Base URL**: `http://5.252.227.183` (Port 80)
- **Auth**: Basic Auth is required (`admin`:`goonline4M`).
- **Nginx Architecture**: On the server (`powersrv-small`), Nginx listens on port 80 and reverse-proxies default traffic to the `ntfy` service running on local port `8002`. This means external client scripts don't need to specify port 8002; simply hit port 80.

## 3. Deployment & Cron

- Do not manually edit cron jobs on the server; `install.sh` manages them and manual edits (via `crontab -e`) will be overwritten.
- **`setup_cron.py`**: Dynamically calculates a 10-minute offset for each website in `config.json` and generates cron jobs. This prevents server spikes.
- **Deployment Commands** (see [`docs/deployment_guide.md`](file:///home/cy/AI/simple%20gemini%20tasks/ntfy-self-hosted/docs/deployment_guide.md) for full details):
  ```bash
  # 1. Sync code to server
  rsync -avz --exclude 'venv' --exclude 'articles.db' --exclude '.git' --exclude 'combined.log' ./ powersrv-small:/home/cy/ntfy-self-hosted/

  # 2. Run install script on server
  ssh powersrv-small "cd /home/cy/ntfy-self-hosted && ./install.sh"
  ```

## 4. Development Workflow

When the user asks you to add a new website to monitor:
1. Create a new file in `scrapers/` (e.g., `scrapers/byte_to.py`).
2. Inherit from `BaseScraper` and implement the extraction logic (URL, title, content, date).
3. Add the site configuration to `config.json` (ensure `enabled` is `true` and define the `topic`, which can be shared across multiple sites or unique to one site).
4. Test locally using `source venv/bin/activate && python main.py --site <site_name>`.
5. Upon successful testing, the code can be synced to `powersrv-small` and `./install.sh` executed.

## 5. Known Guidelines / Resolutions
- **Android App SocketTimeoutExceptions**: Solved on August 9, 2026. The Nginx reverse proxy on `powersrv-small` has been updated with WebSocket upgrade headers. Users connecting via the Android app should ensure their connection protocol is set to **WebSockets** rather than "JSON Stream" to prevent battery drain and random disconnects.
