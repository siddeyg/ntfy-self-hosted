import imaplib
import email
from email.header import decode_header
from core.base_scraper import BaseScraper
from bs4 import BeautifulSoup
import re

class Scraper(BaseScraper):
    def __init__(self, config, site_config):
        super().__init__(config, site_config)
        self.imap_config = site_config.get("imap", {})

    def _decode_str(self, s):
        if not s:
            return ""
        decoded_parts = decode_header(s)
        text_parts = []
        for content, encoding in decoded_parts:
            if isinstance(content, bytes):
                try:
                    text_parts.append(content.decode(encoding or 'utf-8', errors='replace'))
                except LookupError: # Handle unknown encodings like "unknown-8bit"
                    text_parts.append(content.decode('utf-8', errors='replace'))
            else:
                text_parts.append(content)
        return "".join(text_parts)

    def fetch_new_articles(self):
        host = self.imap_config.get("host")
        user = self.imap_config.get("user")
        password = self.imap_config.get("password")
        folder = self.imap_config.get("folder", "INBOX")
        search_criteria = self.imap_config.get("search_criteria", "UNSEEN")

        if not all([host, user, password]):
            print(f"[{self.site_name}] Missing IMAP configuration.")
            return []

        print(f"[{self.site_name}] Connecting to IMAP server {host}...")
        try:
            # Enforce timeout to prevent hanging cron jobs
            mail = imaplib.IMAP4_SSL(host, self.imap_config.get("port", 993), timeout=30)
            mail.login(user, password)
            mail.select(folder)

            # Use UID search so we don't rely on volatile sequence numbers
            if isinstance(search_criteria, list):
                status, messages = mail.uid('SEARCH', None, *search_criteria)
            else:
                status, messages = mail.uid('SEARCH', None, search_criteria)
                
            if status != "OK" or not messages[0]:
                mail.logout()
                return []

            email_uids = messages[0].split()
            found_emails = []

            for uid in email_uids:
                # Use BODY.PEEK[] instead of RFC822 to avoid marking the email as '\Seen'
                res, msg_data = mail.uid('FETCH', uid, "(BODY.PEEK[])")
                if res != "OK":
                    continue

                for response_part in msg_data:
                    if isinstance(response_part, tuple):
                        msg = email.message_from_bytes(response_part[1])
                        
                        subject = self._decode_str(msg.get("Subject"))
                        sender = self._decode_str(msg.get("From"))
                        date_str = msg.get("Date")
                        
                        # Use Message-ID or UID as unique identifier
                        message_id = msg.get("Message-ID", f"uid-{uid.decode()}")

                        # Extract text body (handle multipart and HTML fallback)
                        body = ""
                        html_body = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                content_type = part.get_content_type()
                                if content_type == "text/plain":
                                    body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                                elif content_type == "text/html":
                                    html_body = part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8', errors='replace')
                        else:
                            content_type = msg.get_content_type()
                            payload = msg.get_payload(decode=True).decode(msg.get_content_charset() or 'utf-8', errors='replace')
                            if content_type == "text/html":
                                html_body = payload
                            else:
                                body = payload

                        if not body and html_body:
                            # Strip HTML tags if only HTML is available
                            body = BeautifulSoup(html_body, "html.parser").get_text(separator=" ", strip=True)

                        # Clean up body snippet
                        body_snippet = re.sub(r'\s+', ' ', body).strip()

                        actions = [
                            {
                                "action": "view",
                                "label": "📧 Open Mail App",
                                "url": "mailto:" # Opens default mail client
                            }
                        ]

                        found_emails.append({
                            'url': message_id,
                            'title': f"Email: {subject}",
                            'content': body_snippet,
                            'published_at': date_str,
                            'custom_title': f"New Email from {sender}",
                            'custom_message': f"Subject: {subject}\n\n{body_snippet[:250]}...",
                            'tags': ["email", "envelope"],
                            'actions': actions
                        })

            mail.logout()
            return found_emails

        except Exception as e:
            print(f"[{self.site_name}] IMAP Fetch Error: {e}")
            return []
