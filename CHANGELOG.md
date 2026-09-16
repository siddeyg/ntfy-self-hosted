# Changelog

All notable changes to the `ntfy-self-hosted` project will be documented in this file.

## [1.4.0] - 2026-09-16

### Added
- **Netzpolitik.org Scraper** (`scrapers/netzpolitik.py`):
  - Monitors `https://netzpolitik.org/feed/` for new article publications.
  - Pushes alerts to topic `netzpolitik` on self-hosted ntfy server (`http://5.252.227.183`).
  - Cleans teaser text from RSS summary while removing figure/caption markup.
  - Extracts article thumbnail URL and passes it as `attach` for inline image preview in ntfy clients.
  - Extracts topic tags and adds interactive action button (`Artikel lesen`).
  - Full fallback article extraction from `div.entry-content` into `articles.db`.
  - Initial run seeding: automatically seeds existing 25 articles into SQLite on first deployment and sends a single startup confirmation alert to prevent push spam.
  - Scheduled via `setup_cron.py` on `powersrv-small` with 10-minute offset (`40 9-21/2 * * *`).
- **ntfy Image Attachment Support** (`core/base_scraper.py`):
  - Added support for `attach` field in `BaseScraper.send_ntfy_alert` payload for inline preview of article thumbnails.

### Changed
- **Execution Schedule for netzpolitik.org** (`config.json`):
  - Configured custom schedule `"cron_schedule": "40 8,20 * * *"` to run twice daily at 08:40 and 20:40 instead of every 2 hours.

## [1.3.0] - 2026-09-15

### Added
- **DDoSecrets Scraper** (`scrapers/ddosecrets.py`):
  - Monitors `https://ddosecrets.org/all_articles/recent` for new leak publications.
  - Pushes alerts to topic `ddossecret` on self-hosted ntfy server (`http://5.252.227.183`).
  - Rich metadata extraction: download size, tags/types, countries, publication date, and description snippet.
  - Interactive Action buttons for direct magnet link and article website.
  - Initial run seeding protection: seeds existing leaks into SQLite to avoid push spam, and sends a single startup notification.
  - Configured in `config.json` and scheduled on `powersrv-small` via staggered cron (offset 30 min, `30 9-21/2 * * *`).

### Changed
- **Deactivated Legacy ntfy in Standalone Project**: Disabled direct alerts to `mondo-srv-k9x4` in `/home/cy/ddosecrets/check_new_leaks.py` (both locally and on `powersrv-small`) to eliminate duplicate push notifications while preserving the automated CSV/JSON index generation.

## [Unreleased] - 2026-08-22

### Added
- **Calendar Import Feature for Grüne Bonn Termine** (`scrapers/gruene_bonn.py`):
  - 1-click Google Calendar import button (`📅 In Kalender eintragen`) with pre-filled title, Europe/Berlin timezone-aware start/end datetimes (converted to UTC ISO format `YYYYMMDDTHHMMSSZ`), location, and description link.
  - Interactive Action button to open the event website (`🌐 Webseite öffnen`).
  - Automatic venue & street address scraping from event detail pages with fallback to listing location.
  - SQLite database caching to skip detail page requests for already-processed events.
- **ntfy JSON API & Action Buttons Support** (`core/base_scraper.py`):
  - Migrated `BaseScraper.send_ntfy_alert` to ntfy's native JSON publishing API, enabling full UTF-8 emojis and structured interactive action buttons without Latin-1 header encoding constraints.
  - Added support for custom titles, custom formatted message bodies, custom tag lists, and action buttons per scraper while maintaining 100% backward compatibility.

## [1.2.0] - 2026-08-11

### Added
- **Google Alerts Scraper** (`scrapers/google_alerts.py`): Monitors a Google Alerts RSS feed for a specific ISBN, pushing alerts to `google-alerts-isbn`.
- **Grüne Bonn Fraktion Scraper** (`scrapers/gruene_bonn_fraktion.py`): Monitors `https://gruene-bonn.de/fraktion/` for new press releases and posts, pushing alerts to `gruene-bonn-fraktion`.
- **Grüne Bonn Termine Scraper** (`scrapers/gruene_bonn.py`): Monitors `https://gruene-bonn.de/partei/termine/` for new event entries, pushing alerts to `gruene-bonn-termine`.
- **`CHANGELOG.md`**: Created changelog to track feature additions, fixes, and server updates.

### Fixed
- **RFC 2047 HTTP Header Encoding** (`core/base_scraper.py`): Fixed corrupted character display (e.g. `ü` rendered as replacement characters) in ntfy header titles by encoding non-ASCII headers with RFC 2047 (`=?utf-8?B?...?=`).

## [1.1.0] - 2026-08-09

### Added
- **`GEMINI.md` Guidelines**: Core instruction set and architectural rules for AI agents working on this project.
- **WebSocket Documentation** (`docs/nginx_reverse_proxy_setup.md`): Added documentation for WebSocket configuration in Nginx.

### Server & Infrastructure
- **Nginx WebSocket Upgrade Support**: Updated `/etc/nginx/sites-available/ntfy_default.conf` on `powersrv-small` with `Upgrade` and `Connection` headers and 24h timeouts (`proxy_read_timeout 86400s`) to resolve `SocketTimeoutException` errors in the ntfy Android app.
