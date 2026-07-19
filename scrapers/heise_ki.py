import requests
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.url = "https://www.heise.de/thema/Kuenstliche-Intelligenz"
        self.base_url = "https://www.heise.de"

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Fetching articles from {self.url}")
        try:
            response = requests.get(self.url, timeout=10)
            response.raise_for_status()
        except Exception as e:
            print(f"[{self.site_name}] Error fetching {self.url}: {e}")
            return []

        soup = BeautifulSoup(response.text, 'html.parser')
        articles_data = []

        # Find all article containers
        articles = soup.find_all('article')
        
        for article in articles:
            # Extract link
            a_tag = article.find('a', href=True)
            if not a_tag:
                continue
            
            link = a_tag['href']
            if link.startswith('/'):
                link = self.base_url + link
                
            # If it's an external link or doesn't look right, skip it or keep it as is
            
            # Extract title
            title_span = article.find('span', {'data-component': 'TeaserHeadline'})
            if not title_span:
                continue
            title = title_span.get_text(strip=True)
            
            # Extract snippet
            snippet_p = article.find('p', {'data-component': 'TeaserSynopsis'})
            snippet = snippet_p.get_text(strip=True) if snippet_p else ""
            
            # Extract datetime
            time_tag = article.find('time', datetime=True)
            published_at = time_tag['datetime'] if time_tag else ""
            
            articles_data.append({
                'url': link,
                'title': title,
                'content': snippet,  # We use the synopsis as the content
                'published_at': published_at
            })
            
        return articles_data
