import sqlite3
import requests
import time

class BaseScraper:
    def __init__(self, config, site_config):
        self.config = config
        self.site_config = site_config
        self.db_path = config.get("database", "articles.db")
        self.site_name = site_config.get("name")
        self.topic = site_config.get("topic")

    def init_db(self, conn):
        cursor = conn.cursor()
        # Added source_site column to handle multiple websites in one table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS articles (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_site TEXT NOT NULL,
                url TEXT UNIQUE NOT NULL,
                title TEXT NOT NULL,
                content TEXT,
                published_at TEXT,
                scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

    def article_exists(self, cursor, url):
        cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
        return cursor.fetchone() is not None

    def save_article(self, conn, url, title, content, published_at):
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO articles (source_site, url, title, content, published_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (self.site_name, url, title, content, published_at))
        conn.commit()

    def send_ntfy_alert(self, title, url, snippet):
        ntfy_url = f"{self.config['ntfy']['url'].rstrip('/')}/{self.topic}"
        auth = (self.config['ntfy']['username'], self.config['ntfy']['password'])
        
        message = f"{title}\n\n{snippet}...\n\nLink: {url}"
        
        headers = {
            "Title": f"New Article: {self.site_name}",
            "Click": url,
            "Tags": "newspaper"
        }
        
        try:
            response = requests.post(
                ntfy_url,
                auth=auth,
                data=message.encode('utf-8'),
                headers=headers,
                timeout=10
            )
            if response.status_code == 200:
                print(f"[{self.site_name}] Successfully sent alert for: {title}")
            else:
                print(f"[{self.site_name}] Failed to send alert. Status Code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"[{self.site_name}] Error sending ntfy alert: {e}")

    def fetch_new_articles(self):
        """
        To be implemented by child classes. 
        Should return a list of dictionaries:
        [{'url': '...', 'title': '...', 'content': '...', 'published_at': '...'}, ...]
        """
        raise NotImplementedError("fetch_new_articles must be implemented by the specific site scraper.")

    def run(self):
        print(f"--- Starting scraper for {self.site_name} ---")
        try:
            conn = sqlite3.connect(self.db_path)
            self.init_db(conn)
            cursor = conn.cursor()
            
            articles = self.fetch_new_articles()
            # Process oldest first to keep chronological alerts
            for article in reversed(articles):
                if self.article_exists(cursor, article['url']):
                    continue
                
                print(f"[{self.site_name}] New article found: {article['title']}")
                
                self.save_article(
                    conn, 
                    article['url'], 
                    article['title'], 
                    article['content'], 
                    article['published_at']
                )
                
                snippet = article['content'][:150] if article.get('content') else ""
                self.send_ntfy_alert(article['title'], article['url'], snippet)
                
                time.sleep(2) # Avoid hammering ntfy API
                
            conn.close()
            print(f"--- Finished scraper for {self.site_name} ---")
        except Exception as e:
            print(f"[{self.site_name}] Error running scraper: {e}")
