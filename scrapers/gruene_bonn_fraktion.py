import requests
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.url = "https://gruene-bonn.de/fraktion/"
        self.base_url = "https://gruene-bonn.de"

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Fetching posts from {self.url}")
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
        posts_data = []

        articles = soup.find_all('article', class_='type-post')
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

            time_div = article.find('div', class_='article-time')
            date_str = time_div.get_text(strip=True) if time_div else ""

            content_sec = article.find('section', class_='entry-content')
            content = content_sec.get_text(strip=True) if content_sec else ""

            posts_data.append({
                'url': link,
                'title': title,
                'content': content,
                'published_at': date_str
            })

        return posts_data
