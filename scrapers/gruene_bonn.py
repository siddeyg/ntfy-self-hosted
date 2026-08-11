import requests
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.url = "https://gruene-bonn.de/partei/termine/"
        self.base_url = "https://gruene-bonn.de"

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Fetching events from {self.url}")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        try:
            response = requests.get(self.url, headers=headers, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"[{self.site_name}] Error fetching {self.url}: {e}")
            return []

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
            place_str = place_div.get_text(" ", strip=True) if place_div else ""

            content_parts = [p for p in [date_str, time_str, place_str] if p]
            content = " | ".join(content_parts)

            events_data.append({
                'url': link,
                'title': title,
                'content': content,
                'published_at': date_str
            })

        return events_data
