import requests
from bs4 import BeautifulSoup
from datetime import datetime
import time
import re
from typing import List, Dict, Optional
from urllib.parse import urljoin, urlparse

class WhiteHouseScraper:
    """Scraper for White House Presidential Actions page"""
    
    BASE_URL = "https://www.whitehouse.gov"
    ACTIONS_URL = f"{BASE_URL}/presidential-actions/"
    USER_AGENT = "DocumentCloud Executive Orders Monitor (+https://www.documentcloud.org)"
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': self.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def fetch_page(self, url: str, retries: int = 3) -> Optional[str]:
        """Fetch a page with retry logic"""
        for attempt in range(retries):
            try:
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                if attempt == retries - 1:
                    raise e
                time.sleep(2 ** attempt)  # Exponential backoff
        return None
    
    def parse_actions_page(self, html: str, include_proclamations: bool = False) -> List[Dict]:
        """Parse the presidential actions page to extract orders"""
        soup = BeautifulSoup(html, 'lxml')
        actions = []
        
        # Find all action items - adjust selectors based on actual page structure
        # These selectors may need to be updated based on the actual HTML
        action_items = soup.find_all('article', class_='presidential-actions-listing__item')
        
        if not action_items:
            # Try alternative selectors
            action_items = soup.find_all('div', class_='view-content')
            if action_items:
                action_items = action_items[0].find_all('article')
        
        for item in action_items:
            try:
                # Extract title
                title_elem = item.find(['h2', 'h3', 'h4'], class_=re.compile('title|heading'))
                if not title_elem:
                    title_elem = item.find('a')
                
                if not title_elem:
                    continue
                
                title = title_elem.get_text(strip=True)
                
                # Filter by type
                if not include_proclamations and 'proclamation' in title.lower():
                    continue
                
                if 'executive order' not in title.lower() and not include_proclamations:
                    continue
                
                # Extract URL
                link_elem = item.find('a', href=True)
                if not link_elem:
                    continue
                
                url = urljoin(self.BASE_URL, link_elem['href'])
                
                # Extract date
                date_elem = item.find('time') or item.find(class_=re.compile('date|time'))
                date_str = date_elem.get_text(strip=True) if date_elem else None
                
                # Extract order number if present
                order_match = re.search(r'Executive Order (\d+)', title, re.IGNORECASE)
                order_number = order_match.group(1) if order_match else None
                
                # Create unique ID
                order_id = self._generate_order_id(url, title)
                
                actions.append({
                    'id': order_id,
                    'title': title,
                    'url': url,
                    'date_str': date_str,
                    'order_number': order_number,
                    'type': 'proclamation' if 'proclamation' in title.lower() else 'executive_order'
                })
                
            except Exception as e:
                print(f"Error parsing action item: {e}")
                continue
        
        return actions
    
    def fetch_order_content(self, url: str) -> Dict:
        """Fetch the full content of an executive order"""
        html = self.fetch_page(url)
        if not html:
            return {}
        
        soup = BeautifulSoup(html, 'lxml')
        
        # Extract the main content
        content_elem = soup.find('div', class_='body-content') or \
                      soup.find('div', class_='presidential-action-content') or \
                      soup.find('main') or \
                      soup.find('article')
        
        if not content_elem:
            return {}
        
        # Extract text content
        full_text = content_elem.get_text(separator='\n', strip=True)
        
        # Extract any additional metadata
        metadata = {}
        
        # Try to find issue date
        date_elem = soup.find('div', class_='presidential-action-date') or \
                   soup.find('time')
        if date_elem:
            metadata['issue_date'] = date_elem.get_text(strip=True)
        
        # Try to find categories/topics
        categories = []
        category_elems = soup.find_all('a', class_='category') or \
                        soup.find_all('span', class_='topic')
        for cat in category_elems:
            categories.append(cat.get_text(strip=True))
        if categories:
            metadata['categories'] = categories
        
        return {
            'full_text': full_text,
            'html_content': str(content_elem),
            'metadata': metadata
        }
    
    def scrape_recent_orders(self, include_proclamations: bool = False) -> List[Dict]:
        """Scrape recent executive orders from the White House website"""
        try:
            html = self.fetch_page(self.ACTIONS_URL)
            if not html:
                raise Exception("Failed to fetch presidential actions page")
            
            orders = self.parse_actions_page(html, include_proclamations)
            
            # Fetch full content for each order
            for order in orders:
                time.sleep(1)  # Rate limiting
                content_data = self.fetch_order_content(order['url'])
                order.update(content_data)
            
            return orders
            
        except Exception as e:
            print(f"Error scraping orders: {e}")
            raise
    
    def _generate_order_id(self, url: str, title: str) -> str:
        """Generate a unique ID for an order"""
        # Use URL path as primary identifier
        path = urlparse(url).path.strip('/')
        if path:
            return path.replace('/', '-')
        
        # Fallback to title-based ID
        clean_title = re.sub(r'[^\w\s-]', '', title.lower())
        clean_title = re.sub(r'[-\s]+', '-', clean_title)
        return clean_title[:100]  # Limit length