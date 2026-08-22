import re
import urllib.parse
from datetime import datetime, timedelta
import zoneinfo
import sqlite3
import os
import requests
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

BERLIN_TZ = zoneinfo.ZoneInfo("Europe/Berlin")
UTC_TZ = zoneinfo.ZoneInfo("UTC")

def parse_event_datetime(date_str, time_str):
    """
    Parses German date (DD.MM.YYYY) and time ('von 19:00 bis 21:00 Uhr', 'um 19:00 Uhr')
    into Europe/Berlin timezone-aware start and end datetime objects.
    """
    if not date_str:
        return None, None
    
    date_match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', date_str)
    if not date_match:
        return None, None

    day, month, year = [int(x) for x in date_match.groups()]

    # Check for range: 'von 19:00 bis 21:00 Uhr' or '19:00 - 21:00' or '19.00 - 21.00'
    range_match = re.search(r'(\d{1,2})[:.](\d{2})\s*(?:bis|-)\s*(\d{1,2})[:.](\d{2})', time_str or '')
    if range_match:
        sh, sm, eh, em = [int(x) for x in range_match.groups()]
        start_dt = datetime(year, month, day, sh, sm, tzinfo=BERLIN_TZ)
        end_dt = datetime(year, month, day, eh, em, tzinfo=BERLIN_TZ)
        if end_dt <= start_dt:
            end_dt += timedelta(days=1)
        return start_dt, end_dt

    # Check for single time: 'um 19:00 Uhr' or '19:00' or '19.00'
    single_match = re.search(r'(\d{1,2})[:.](\d{2})', time_str or '')
    if single_match:
        sh, sm = [int(x) for x in single_match.groups()]
        start_dt = datetime(year, month, day, sh, sm, tzinfo=BERLIN_TZ)
        end_dt = start_dt + timedelta(hours=1)
        return start_dt, end_dt

    # Fallback for all-day / date-only events
    start_dt = datetime(year, month, day, 9, 0, tzinfo=BERLIN_TZ)
    end_dt = datetime(year, month, day, 10, 0, tzinfo=BERLIN_TZ)
    return start_dt, end_dt

def generate_google_calendar_url(title, start_dt, end_dt, location, details_url):
    """
    Generates a Google Calendar 1-click web intent URL.
    """
    base_url = "https://calendar.google.com/calendar/render"
    
    if start_dt and end_dt:
        start_utc = start_dt.astimezone(UTC_TZ).strftime("%Y%m%dT%H%M%SZ")
        end_utc = end_dt.astimezone(UTC_TZ).strftime("%Y%m%dT%H%M%SZ")
        dates_str = f"{start_utc}/{end_utc}"
    else:
        dates_str = ""

    details_text = f"Termin von Grüne Bonn:\n{details_url}"
    
    params = {
        "action": "TEMPLATE",
        "text": title,
        "details": details_text,
        "location": location or "Bonn",
        "ctz": "Europe/Berlin"
    }
    if dates_str:
        params["dates"] = dates_str

    return f"{base_url}?{urllib.parse.urlencode(params)}"

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.url = "https://gruene-bonn.de/partei/termine/"
        self.base_url = "https://gruene-bonn.de"

    def _get_existing_urls(self):
        """Helper to quickly check existing URLs to avoid subpage HTTP requests on known events."""
        if not os.path.exists(self.db_path):
            return set()
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT url FROM articles WHERE source_site = ?", (self.site_name,))
            rows = cursor.fetchall()
            conn.close()
            return {r[0] for r in rows}
        except Exception:
            return set()

    def fetch_event_details(self, session, event_url, default_place):
        """
        Attempts to fetch full address / venue from the event detail page.
        Gracefully falls back to default_place if fetch fails.
        """
        try:
            resp = session.get(event_url, timeout=5)
            if resp.status_code == 200:
                detail_soup = BeautifulSoup(resp.text, 'html.parser')
                venue_div = detail_soup.find('div', class_='entry-content-meta-veranstaltungsort')
                if venue_div:
                    venue_text = venue_div.get_text(", ", strip=True)
                    if venue_text:
                        return venue_text
        except Exception:
            pass
        return default_place

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Fetching events from {self.url}")
        session = requests.Session()
        session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        })
        try:
            response = session.get(self.url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"[{self.site_name}] Error fetching {self.url}: {e}")
            return []

        existing_urls = self._get_existing_urls()
        soup = BeautifulSoup(response.text, 'html.parser')
        events_data = []

        articles = soup.find_all('article', class_='type-event')
        for article in articles:
            heading = article.find('h3', class_='article-heading')
            if not heading:
                continue

            a_tag = heading.find('a', href=True)
            if not a_tag:
                continue

            title = a_tag.get_text(strip=True)
            link = a_tag['href']
            if link.startswith('/'):
                link = self.base_url + link

            date_span = article.find('span', class_='meta-time-date')
            time_span = article.find('span', class_='meta-time-time')
            place_div = article.find('div', class_='meta-place')

            date_str = date_span.get_text(strip=True) if date_span else ""
            time_str = time_span.get_text(strip=True) if time_span else ""
            place_raw = place_div.get_text(" ", strip=True) if place_div else ""
            place_str = place_raw.replace("Ort:", "").strip()

            # If already processed previously, skip fetching subpage to preserve bandwidth and time
            if link in existing_urls:
                location = place_str or "Bonn"
            else:
                location = self.fetch_event_details(session, link, place_str) or "Bonn"

            # Parse event datetimes with Europe/Berlin timezone
            start_dt, end_dt = parse_event_datetime(date_str, time_str)
            
            # Generate calendar link
            gcal_url = generate_google_calendar_url(title, start_dt, end_dt, location, link)

            # Build formatted notification message
            msg_lines = [title, ""]
            if date_str:
                msg_lines.append(f"📅 Datum: {date_str}")
            if time_str:
                msg_lines.append(f"⏰ Zeit: {time_str}")
            if location:
                msg_lines.append(f"📍 Ort: {location}")
            msg_lines.append(f"\nWebseite: {link}")
            custom_message = "\n".join(msg_lines)

            content_parts = [p for p in [date_str, time_str, location] if p]
            content = " | ".join(content_parts)

            # ntfy action buttons: 1. Add to calendar, 2. Open website
            actions = [
                {
                    "action": "view",
                    "label": "📅 In Kalender eintragen",
                    "url": gcal_url
                },
                {
                    "action": "view",
                    "label": "🌐 Webseite öffnen",
                    "url": link
                }
            ]

            events_data.append({
                'url': link,
                'title': title,
                'content': content,
                'published_at': date_str,
                'custom_title': f"Neuer Termin: Grüne Bonn",
                'custom_message': custom_message,
                'tags': ["calendar", "green_circle"],
                'actions': actions
            })

        return events_data
