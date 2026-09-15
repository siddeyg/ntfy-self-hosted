import requests
import re
import time
import sqlite3
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.base_url = "https://ddosecrets.org"
        self.recent_articles_url = f"{self.base_url}/all_articles/recent"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }

    def fetch_article_list(self):
        try:
            resp = requests.get(self.recent_articles_url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            html = resp.text
            
            entries = re.findall(r'<h4[^>]*>.*?<a href="(/article/[^"]+)"[^>]*>(.*?)</a>', html, re.DOTALL)
            articles = []
            for path, title in entries:
                clean_title = re.sub(r'<[^>]+>', '', title).strip()
                articles.append({
                    'url': f"{self.base_url}{path}",
                    'title': clean_title
                })
            return articles
        except Exception as e:
            print(f"[{self.site_name}] Error fetching article list from {self.recent_articles_url}: {e}")
            return []

    def fetch_article_details(self, url, fallback_title=""):
        try:
            resp = requests.get(url, headers=self.headers, timeout=15)
            resp.raise_for_status()
            html = resp.text

            title = fallback_title
            content_block = re.search(r'<div class="content">(.*?)</div>', html, re.DOTALL)
            if content_block:
                m = re.search(r'<h1>(.*?)</h1>', content_block.group(1))
                if m:
                    title = re.sub(r'<[^>]+>', '', m.group(1)).strip()

            published = ""
            m = re.search(r'Published on\s*([\d]{4}-[\d]{2}-[\d]{2})', html)
            if m:
                published = m.group(1)

            countries = ""
            types = ""
            metadata_m = re.search(r'<div class="metadata">(.*?)</div>', html, re.DOTALL)
            if metadata_m:
                meta_html = metadata_m.group(1)
                c_matches = re.findall(r'href="/country/[^"]*">([^<]+)<', meta_html)
                if c_matches:
                    countries = ', '.join(c.strip() for c in c_matches)
                t_matches = re.findall(r'href="/type/[^"]*">([^<]+)<', meta_html)
                if t_matches:
                    types = ', '.join(t.strip() for t in t_matches)

            size = ""
            m = re.search(r'Download Size:</span>\s*([\d.,]+\s*(?:GB|MB|TB|KB|bytes?))', html, re.IGNORECASE)
            if m:
                size = m.group(1).strip()

            magnet = ""
            m = re.search(r'(magnet:\?[^\s"\'<>&]+(?:&amp;[^\s"\'<>&]+)*)', html)
            if m:
                magnet = m.group(1).replace('&amp;', '&')

            description = ""
            content_m = re.search(r'<div class="article-content">(.*?)(?:</div>\s*</div>|<h2>Reference)', html, re.DOTALL)
            if content_m:
                body = content_m.group(1)
                body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL)
                body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL)
                paras = re.findall(r'<p[^>]*>(.*?)</p>', body, re.DOTALL)
                desc_parts = [re.sub(r'<[^>]+>', '', p).strip() for p in paras if re.sub(r'<[^>]+>', '', p).strip()]
                description = ' '.join(desc_parts)[:1000]

            return {
                'title': title,
                'published': published,
                'countries': countries,
                'types': types,
                'size': size,
                'magnet': magnet,
                'description': description
            }
        except Exception as e:
            print(f"[{self.site_name}] Error scraping article details for {url}: {e}")
            return {
                'title': fallback_title,
                'published': '',
                'countries': '',
                'types': '',
                'size': '',
                'magnet': '',
                'description': ''
            }

    def fetch_new_articles(self):
        print(f"[{self.site_name}] Checking for recent articles...")
        article_list = self.fetch_article_list()
        if not article_list:
            print(f"[{self.site_name}] No articles retrieved.")
            return []

        conn = sqlite3.connect(self.db_path)
        self.init_db(conn)
        cursor = conn.cursor()

        # Check existing count for this site
        cursor.execute("SELECT count(*) FROM articles WHERE source_site = ?", (self.site_name,))
        count = cursor.fetchone()[0]

        # Initial seed if database is empty for DDoSecrets
        if count == 0:
            print(f"[{self.site_name}] Initial run detected. Seeding {len(article_list)} existing articles to avoid alert spam...")
            for art in article_list:
                self.save_article(conn, art['url'], art['title'], "", "")
            conn.close()

            # Send a single initial notification announcing the scraper is active
            initial_article = {
                'url': self.base_url,
                'title': 'DDoSecrets Monitor Initialisiert',
                'custom_title': '[DDoSecrets] Monitor Gestartet',
                'custom_message': f"DDoSecrets Scraper erfolgreich eingerichtet.\n{len(article_list)} bestehende Leaks indexiert.\nZukünftige Neuveröffentlichungen werden hier gemeldet.",
                'tags': ["white_check_mark", "unlock"],
                'published_at': '',
                'content': f'{len(article_list)} Leaks indexiert.'
            }
            return [initial_article]

        new_articles = []
        consecutive_known = 0

        for art in article_list:
            if self.article_exists(cursor, art['url']):
                consecutive_known += 1
                if consecutive_known >= 5:
                    # Articles are ordered newest first; once we hit 5 known articles, stop checking
                    break
                continue

            consecutive_known = 0
            print(f"[{self.site_name}] New leak found: {art['title']} -> Fetching details...")
            details = self.fetch_article_details(art['url'], fallback_title=art['title'])
            time.sleep(0.5)

            final_title = details['title'] or art['title']
            published = details['published']
            size = details['size']
            types = details['types']
            countries = details['countries']
            desc = details['description']
            magnet = details['magnet']

            meta_lines = []
            if size:
                meta_lines.append(f"📦 Größe: {size}")
            if types:
                meta_lines.append(f"🏷️ Typ: {types}")
            if countries:
                meta_lines.append(f"🌍 Land: {countries}")
            if published:
                meta_lines.append(f"📅 Datum: {published}")

            meta_text = " | ".join(meta_lines) if meta_lines else ""
            custom_msg = f"{final_title}\n\n"
            if meta_text:
                custom_msg += f"{meta_text}\n\n"
            if desc:
                custom_msg += f"{desc[:400]}...\n\n"
            custom_msg += f"🔗 {art['url']}"

            actions = []
            if magnet:
                actions.append({
                    "action": "view",
                    "label": "Magnet Link",
                    "url": magnet
                })
            actions.append({
                "action": "view",
                "label": "DDoSecrets Artikel",
                "url": art['url']
            })

            new_articles.append({
                'url': art['url'],
                'title': final_title,
                'content': desc,
                'published_at': published,
                'custom_title': f"[DDoSecrets] {final_title}",
                'custom_message': custom_msg,
                'tags': ["newspaper", "mag", "unlock"],
                'actions': actions
            })

        conn.close()
        print(f"[{self.site_name}] Found {len(new_articles)} new article(s).")
        return new_articles
