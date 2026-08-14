import urllib.request
import xml.etree.ElementTree as ET
from bs4 import BeautifulSoup
from core.base_scraper import BaseScraper

class Scraper(BaseScraper):
    def fetch_new_articles(self):
        feed_url = self.site_config.get("url")
        if not feed_url:
            print(f"[{self.site_name}] No feed URL provided in config.")
            return []

        try:
            req = urllib.request.Request(feed_url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req) as response:
                xml_data = response.read()

            root = ET.fromstring(xml_data)
            
            # Atom namespace
            ns = {'atom': 'http://www.w3.org/2005/Atom'}
            
            articles = []
            for entry in root.findall('atom:entry', ns):
                title_elem = entry.find('atom:title', ns)
                link_elem = entry.find('atom:link', ns)
                content_elem = entry.find('atom:content', ns)
                updated_elem = entry.find('atom:updated', ns)
                
                if title_elem is None or link_elem is None:
                    continue
                    
                title = BeautifulSoup(title_elem.text or "", "html.parser").get_text()
                url = link_elem.get('href', '')
                
                content = ""
                if content_elem is not None and content_elem.text:
                    content = BeautifulSoup(content_elem.text, "html.parser").get_text()
                    
                published_at = updated_elem.text if updated_elem is not None else ""
                
                articles.append({
                    'url': url,
                    'title': title,
                    'content': content,
                    'published_at': published_at
                })
                
            return articles
        except Exception as e:
            print(f"[{self.site_name}] Error fetching Google Alerts RSS: {e}")
            return []
