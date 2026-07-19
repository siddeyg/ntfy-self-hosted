import os
import sqlite3
import time
import requests
import feedparser
from bs4 import BeautifulSoup

# Configuration
NTFY_URL = "http://5.252.227.183/the-decoder-updates"
NTFY_USER = "admin"
NTFY_PASS = "goonline4M"
DB_PATH = "articles.db"
RSS_FEED_URL = "https://the-decoder.de/feed/"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS articles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            url TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            content TEXT,
            published_at TEXT,
            scraped_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def extract_article_content(url):
    """Fetches the URL and extracts the main article paragraphs."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # the-decoder.de usually puts content in <article> or .entry-content
        content_div = soup.find('div', class_='entry-content') or soup.find('article')
        if content_div:
            paragraphs = content_div.find_all('p')
            text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if p.get_text(strip=True)])
            return text
        else:
            # Fallback to getting all paragraphs if specific container isn't found
            paragraphs = soup.find_all('p')
            text = "\n\n".join([p.get_text(strip=True) for p in paragraphs if len(p.get_text(strip=True)) > 30])
            return text
    except Exception as e:
        print(f"Error scraping {url}: {e}")
        return ""

def send_ntfy_alert(title, url, snippet):
    """Sends a notification to the self-hosted ntfy server."""
    # We include the URL in the message body and use the Click header so clicking the notification opens it
    message = f"{title}\n\n{snippet}...\n\nLink: {url}"
    
    headers = {
        "Title": "New Article: The Decoder",
        "Click": url,
        "Tags": "newspaper"
    }
    
    try:
        response = requests.post(
            NTFY_URL,
            auth=(NTFY_USER, NTFY_PASS),
            data=message.encode('utf-8'),
            headers=headers
        )
        if response.status_code == 200:
            print(f"Successfully sent alert for: {title}")
        else:
            print(f"Failed to send alert. Status Code: {response.status_code}, Response: {response.text}")
    except Exception as e:
        print(f"Error sending ntfy alert: {e}")

def main():
    print("Starting Website Article Monitor...")
    conn = init_db()
    cursor = conn.cursor()
    
    # Parse the RSS Feed
    print(f"Fetching RSS feed from {RSS_FEED_URL}")
    feed = feedparser.parse(RSS_FEED_URL)
    
    # Process from oldest to newest (by reversing the list) so alerts come in order if there are multiple
    for entry in reversed(feed.entries):
        url = entry.link
        title = entry.title
        published_at = entry.published if hasattr(entry, 'published') else ""
        
        # Check if already in DB
        cursor.execute("SELECT id FROM articles WHERE url = ?", (url,))
        if cursor.fetchone():
            continue  # Already processed
        
        print(f"New article found: {title}")
        
        # Scrape full content
        print(f"Scraping content from: {url}")
        content = extract_article_content(url)
        
        # Create a short snippet for the notification (first ~150 chars)
        snippet = content[:150] if content else entry.get('description', '')[:150]
        
        # Save to DB
        cursor.execute('''
            INSERT INTO articles (url, title, content, published_at)
            VALUES (?, ?, ?, ?)
        ''', (url, title, content, published_at))
        conn.commit()
        
        # Send Notification
        send_ntfy_alert(title, url, snippet)
        
        # Small delay to avoid hammering the server and ntfy API if there are multiple new articles
        time.sleep(2)
        
    conn.close()
    print("Monitor finished successfully.")

if __name__ == "__main__":
    main()
