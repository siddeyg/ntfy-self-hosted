import requests
import feedparser
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.rss_url = "https://the-decoder.de/feed/"

    def extract_article_content(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            content_div = soup.find('div', class_='entry-content') or soup.find('article')
            if content_div:
                paragraphs = content_div.find_all('p')
                text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                return text
            else:
                paragraphs = soup.find_all('p')
                text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
                return text
        except Exception as e:
            print(f"[{self.site_name}] Error scraping {url}: {e}")
            return ""

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Fetching RSS feed from {self.rss_url}")
        feed = feedparser.parse(self.rss_url)
        
        articles = []
        for entry in feed.entries:
            url = entry.link
            title = entry.title
            published_at = entry.published if hasattr(entry, 'published') else ""
            
            # For RSS, we fetch content right away. 
            # In a more advanced setup we could only fetch content if it's not in DB yet, 
            # but to keep it simple and match original script behavior we fetch first.
            # (Note: In run() it will check DB first if we moved logic, but this is fine for now).
            
            # Let's optimize: We only extract content here, but we could skip if we passed DB cursor.
            # For now, we mimic the original behavior.
            content = self.extract_article_content(url)
            
            # Fallback to RSS description if content extraction failed
            if not content:
                content = entry.get('description', '')
                
            articles.append({
                'url': url,
                'title': title,
                'content': content,
                'published_at': published_at
            })
        return articles
