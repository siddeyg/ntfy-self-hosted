import sqlite3
import requests
import time
import base64

def encode_rfc2047(text):
    if not text:
        return text
    try:
        text.encode('ascii')
        return text
    except UnicodeEncodeError:
        b64 = base64.b64encode(text.encode('utf-8')).decode('ascii')
        return f"=?utf-8?B?{b64}?="

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

    def send_ntfy_alert(self, title, url, snippet, article=None):
        if article is None:
            article = {}

        ntfy_base = self.site_config.get('ntfy_url', self.config['ntfy']['url'])
        
        auth = None
        if 'ntfy_username' in self.site_config and 'ntfy_password' in self.site_config:
            auth = (self.site_config['ntfy_username'], self.site_config['ntfy_password'])
        elif 'ntfy_url' not in self.site_config and 'username' in self.config['ntfy'] and 'password' in self.config['ntfy']:
            auth = (self.config['ntfy']['username'], self.config['ntfy']['password'])
        
        message = article.get('custom_message') or f"{title}\n\n{snippet}...\n\nLink: {url}"
        raw_title = article.get('custom_title') or f"New Article: {self.site_name}"
        click_url = article.get('click_url') or url
        raw_tags = article.get('tags') or "newspaper"

        if isinstance(raw_tags, str):
            tags = [t.strip() for t in raw_tags.split(",") if t.strip()]
        elif isinstance(raw_tags, list):
            tags = raw_tags
        else:
            tags = ["newspaper"]

        payload = {
            "topic": self.topic,
            "title": raw_title,
            "message": message,
            "click": click_url,
            "tags": tags
        }

        if 'attach' in article and article['attach']:
            payload['attach'] = article['attach']

        # Process actions if provided (structured dicts or string format)
        if 'actions' in article and article['actions']:
            actions_list = []
            for act in article['actions']:
                if isinstance(act, dict):
                    actions_list.append(act)
                elif isinstance(act, str):
                    parts = [p.strip() for p in act.split(',', 2)]
                    if len(parts) >= 3:
                        actions_list.append({
                            "action": parts[0],
                            "label": parts[1],
                            "url": parts[2]
                        })
            if actions_list:
                payload["actions"] = actions_list

        try:
            response = requests.post(
                ntfy_base.rstrip('/'),
                json=payload,
                auth=auth,
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
                self.send_ntfy_alert(article['title'], article['url'], snippet, article=article)
                
                time.sleep(2) # Avoid hammering ntfy API
                
            conn.close()
            print(f"--- Finished scraper for {self.site_name} ---")
        except Exception as e:
            print(f"[{self.site_name}] Error running scraper: {e}")
