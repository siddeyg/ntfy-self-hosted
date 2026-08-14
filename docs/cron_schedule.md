# Scraper Cron Schedule

The scheduling system for the scrapers (`setup_cron.py`) is designed to run the scraping jobs every 2 hours throughout the day, while staggering the execution times to prevent CPU spikes and rate limits. 

## Schedule Generation

The script runs on the production server (`powersrv-small`) during deployment and calculates the exact cron times dynamically based on the number of sites enabled in `config.json`. 

- **Frequency:** Every 2 hours
- **Time Window:** From roughly `08:10` to `21:10`
- **Offset:** Each scraper starts exactly 10 minutes after the previous one. 

## Current Execution Times

Based on the current enabled sites, the resulting execution schedule looks like this (server local time):

| Site Name | Minute Offset | Scheduled Times |
|-----------|---------------|-----------------|
| **The Decoder** | `10` | 8:10, 10:10, 12:10, 14:10, 16:10, 18:10, 20:10 |
| **Heise KI** | `20` | 8:20, 10:20, 12:20, 14:20, 16:20, 18:20, 20:20 |
| **OCCRP** | `30` | 8:30, 10:30, 12:30, 14:30, 16:30, 18:30, 20:30 |
| **Grüne Bonn** | `40` | 8:40, 10:40, 12:40, 14:40, 16:40, 18:40, 20:40 |
| **Grüne Bonn Fraktion** | `50` | 8:50, 10:50, 12:50, 14:50, 16:50, 18:50, 20:50 |
| **The Autopilot** | `60` (Wraps) | 9:00, 11:00, 13:00, 15:00, 17:00, 19:00, 21:00 |
| **Google Alerts** | `70` (Wraps) | 9:10, 11:10, 13:10, 15:10, 17:10, 19:10, 21:10 |

> **Note:** If more sites are added to `config.json`, the script will automatically continue this staggering pattern (e.g., the 8th site will run at 9:20, 11:20, etc.).
