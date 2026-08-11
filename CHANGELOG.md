# Changelog

All notable changes to the `ntfy-self-hosted` project will be documented in this file.

## [Unreleased] - 2026-08-11

### Added
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
