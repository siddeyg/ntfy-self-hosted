import requests
import feedparser
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.rss_url = "https://www.occrp.org/en/feed"

    def extract_article_content(self, url):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the main article body based on common classes or fallback to all paragraphs
            content_div = soup.find('div', class_='article-body') or soup.find('article')
            if content_div:
                paragraphs = content_div.find_all('p')
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
            
            content = self.extract_article_content(url)
            
            if not content:
                content = entry.get('description', '')
                
            articles.append({
                'url': url,
                'title': title,
                'content': content,
                'published_at': published_at
            })
        return articles
