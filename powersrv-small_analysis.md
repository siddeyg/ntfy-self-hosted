# powersrv-small: Current Services & Projects

This document summarizes the existing projects and services running on the `powersrv-small` server as of May 29, 2026.

## Running Services (systemd)

| Service Name | Description | Status |
|--------------|-------------|--------|
| `nginx.service` | Nginx Web/Proxy Server | Running (Ports 80, 443) |
| `ntfy.service` | ntfy notification server | Running (Port 8002, behind Nginx) |
| `klimacamp.service` | Klimacamp Hamm Aggregator | Running |
| `klimacamp-web.service` | Klimacamp Hamm Ticker Web Dashboard | Running (Port 8080) |
| `ssh.service` | OpenBSD Secure Shell server | Running (Port 22) |
| `cron.service` | Regular background program processing | Running |

## Network Ports

| Port | Protocol | Service / Process |
|------|----------|-------------------|
| 22   | TCP      | SSHD |
| 80   | TCP      | Nginx (Proxies default to ntfy, and specific domains) |
| 443  | TCP      | Nginx (SSL for specific domains like bonn-gerichte) |
| 8001 | TCP      | bonn-gerichte app (Local only) |
| 8002 | TCP      | ntfy (Local only) |
| 8080 | TCP      | Gunicorn (Klimacamp Web Dashboard) |

## Project Directories (`/home/cy/`)

The following directories suggest additional projects (potentially inactive or run via cron):

*   **`klimacamp-infos/`**: Active project (Python/Gunicorn).
*   **`ga.de/`**: Likely a scraper or web project related to ga.de.
*   **`bonn-gerichte/`**: Likely a scraper or project related to Bonn courts.
*   **`discord-monitor/`**: Discord monitoring bot/script.
*   **`zoll-auktion/`**: Likely a scraper for zoll-auktion.de.
*   **`klimacamp-infos/`**: Source for the active Klimacamp services.
*   **`backups/`**: System or project backups.
*   **`ddosecrets/`**: Likely related to Distributed Denial of Secrets (data dumps).

## Scheduled Tasks (Cron)

Several scrapers and monitors run via cron jobs:

| Schedule | Command / Project |
|----------|-------------------|
| 0 6,11,16 * * * | `ddosecrets/check_new_leaks.py` |
| 0 8,12,16,20 * * * | `discord-monitor/monitor.py` |
| 0 7,13,21 * * * | `/home/cy/backups/leakforensics/backup.sh` |
| 0 */4 * * * | `zoll-auktion/main_vps.py` |
| 5 11,16 * * * | `bonn-gerichte/scrape.py` |

## Resource Usage

*   **CPU Load**: Extremely low (0.00 average).
*   **RAM**: ~960MiB total, ~430MiB available.
*   **Disk**: 29G total, ~8.8G available on `/`.

## Observations

*   **Web Servers**: Nginx is now installed and serves as a reverse proxy on ports 80/443. It proxies traffic to `ntfy` (port 8002) as the default catch-all, and handles specific domains (e.g., `gerichte.bonngiesst.de` proxying to `bonn-gerichte` on port 8001). Gunicorn still serves `klimacamp-web` directly on port 8080.
*   **Docker**: Not installed.
*   **Environment**: Primarily Python-based projects using virtual environments (`venv`).
