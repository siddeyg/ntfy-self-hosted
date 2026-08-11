import requests
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.base_url = "https://www.the-autopilot.com"
        # Since RSS is blocked, we crawl the homepage directly with browser headers
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36"
        }

    def extract_article_content(self, url):
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Target beehiiv's article content container
            content_div = soup.find('div', class_='post-content')
            if content_div:
                paragraphs = content_div.find_all('p')
                text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
                return text
            return ""
        except Exception as e:
            print(f"[{self.site_name}] Error scraping {url}: {e}")
            return ""

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Crawling homepage: {self.base_url}")
        try:
            response = requests.get(self.base_url, headers=self.headers, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            articles = []
            # Beehiiv structure: find post links (this selector may need adjustment if structure varies)
            posts = soup.find_all('a', href=True)
            for post in posts:
                # Basic filter for post links, typical beehiiv structure /p/slug
                if '/p/' in post['href']:
                    full_url = self.base_url + str(post['href'])
                    title = post.get_text(strip=True)
                    if not title or len(title) < 5:
                        continue
                    
                    articles.append({
                        'url': full_url,
                        'title': title,
                        'content': self.extract_article_content(full_url),
                        'published_at': ''
                    })
            return articles
        except Exception as e:
            print(f"[{self.site_name}] Error fetching articles: {e}")
            return []
