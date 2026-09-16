import requests
import re
import time
import sqlite3
import feedparser
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.rss_url = "https://netzpolitik.org/feed/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def extract_full_content(self, url):
        """Extract full article text from netzpolitik.org page if possible."""
        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            content_div = soup.find('div', class_='entry-content')
            if content_div:
                paras = content_div.find_all('p')
                text = "\n\n".join([p.get_text(strip=True) for p in paras if p.get_text(strip=True)])
                return text
        except Exception as e:
            print(f"[{self.site_name}] Warning: Failed to extract full content for {url}: {e}")
        return ""

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Fetching RSS feed from {self.rss_url}")
        feed = feedparser.parse(self.rss_url)
        
        if not feed.entries:
            print(f"[{self.site_name}] No entries found in RSS feed.")
            return []

        conn = sqlite3.connect(self.db_path)
        self.init_db(conn)
        cursor = conn.cursor()

        # Check existing count for this site
        cursor.execute("SELECT count(*) FROM articles WHERE source_site = ?", (self.site_name,))
        count = cursor.fetchone()[0]

        # Initial seed if database is empty for this scraper
        if count == 0:
            print(f"[{self.site_name}] Initial run detected. Seeding {len(feed.entries)} existing articles to avoid notification spam...")
            for entry in feed.entries:
                self.save_article(conn, entry.link, entry.title, "", entry.get('published', ''))
            conn.close()

            initial_article = {
                'url': "https://netzpolitik.org",
                'title': 'netzpolitik.org Monitor Initialisiert',
                'custom_title': '[netzpolitik.org] Monitor Gestartet',
                'custom_message': f"netzpolitik.org Scraper erfolgreich eingerichtet.\n{len(feed.entries)} aktuelle Artikel indexiert.\nZukünftige Neuveröffentlichungen werden hier gemeldet.",
                'tags': ["white_check_mark", "newspaper"],
                'published_at': '',
                'content': f'{len(feed.entries)} Artikel indexiert.'
            }
            return [initial_article]

        new_articles = []
        consecutive_known = 0

        for entry in feed.entries:
            url = entry.link
            title = entry.title
            published_at = entry.get('published', '')

            if self.article_exists(cursor, url):
                consecutive_known += 1
                if consecutive_known >= 5:
                    break
                continue

            consecutive_known = 0
            print(f"[{self.site_name}] New article found: {title}")

            # Extract teaser and thumbnail from summary
            teaser = ""
            thumbnail_url = ""
            summary_raw = entry.get('summary', '')
            if summary_raw:
                soup = BeautifulSoup(summary_raw, 'html.parser')
                img_tag = soup.find('img')
                if img_tag and img_tag.get('src'):
                    thumbnail_url = img_tag['src']
                
                # Remove figures/captions to get clean teaser text
                for fig in soup.find_all('figure'):
                    fig.decompose()
                teaser = soup.get_text(strip=True)

            # Extract tags/categories
            tags_list = [t.term for t in entry.get('tags', []) if hasattr(t, 'term')]
            tags_str = ", ".join(tags_list[:5]) if tags_list else ""

            # Fetch full content for DB storage (fallback to teaser)
            full_content = self.extract_full_content(url)
            if not full_content:
                full_content = teaser

            # Format push notification message
            msg_parts = [title]
            if teaser:
                msg_parts.append(teaser)
            if tags_str:
                msg_parts.append(f"🏷️ {tags_str}")
            msg_parts.append(f"🔗 {url}")

            custom_msg = "\n\n".join(msg_parts)

            actions = [{
                "action": "view",
                "label": "Artikel lesen",
                "url": url
            }]

            article_data = {
                'url': url,
                'title': title,
                'content': full_content,
                'published_at': published_at,
                'custom_title': f"[netzpolitik.org] {title}",
                'custom_message': custom_msg,
                'tags': ["newspaper", "globe"],
                'actions': actions
            }

            if thumbnail_url:
                article_data['attach'] = thumbnail_url

            new_articles.append(article_data)

        conn.close()
        print(f"[{self.site_name}] Found {len(new_articles)} new article(s).")
        return new_articles
