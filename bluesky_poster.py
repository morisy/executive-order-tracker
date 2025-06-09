from atproto import Client
from typing import Optional, Dict
import re

class BlueskyPoster:
    """Post executive order announcements to Bluesky"""
    
    def __init__(self, handle: str, password: str):
        """Initialize Bluesky client"""
        self.handle = handle
        self.password = password
        self.client = None
        self.authenticated = False
    
    def authenticate(self) -> bool:
        """Authenticate with Bluesky"""
        try:
            self.client = Client()
            self.client.login(self.handle, self.password)
            self.authenticated = True
            return True
        except Exception as e:
            print(f"Failed to authenticate with Bluesky: {e}")
            self.authenticated = False
            return False
    
    def create_post_text(self, order_data: Dict, doc_url: str) -> str:
        """Create the post text for an executive order"""
        # Extract key information
        title = order_data.get('title', 'New Executive Order')
        order_number = order_data.get('order_number')
        original_url = order_data.get('url', '')
        
        # Create post text
        post_lines = [
            "🆕 Executive Order: " + self._truncate_title(title, 100)
        ]
        
        if order_number:
            post_lines.append(f"📄 EO-{order_number}")
        
        post_lines.extend([
            "",
            "Full text archived:",
            f"🔗 DocumentCloud: {doc_url}",
            f"🔗 Original: {original_url}" if original_url else "",
            "",
            "#ExecutiveOrder #WhiteHouse #GovDocs #Transparency"
        ])
        
        # Join and ensure we're under character limit
        post_text = '\n'.join(line for line in post_lines if line)
        
        # Bluesky has a 300 character limit
        if len(post_text) > 300:
            # Truncate the title more aggressively
            short_title = self._truncate_title(title, 50)
            post_lines[0] = "🆕 Executive Order: " + short_title
            post_text = '\n'.join(line for line in post_lines if line)
            
            # If still too long, remove hashtags
            if len(post_text) > 300:
                post_text = post_text.replace("#ExecutiveOrder #WhiteHouse #GovDocs #Transparency", "#ExecutiveOrder")
        
        return post_text[:300]  # Ensure we don't exceed limit
    
    def _truncate_title(self, title: str, max_length: int) -> str:
        """Truncate title intelligently"""
        if len(title) <= max_length:
            return title
        
        # Try to truncate at a word boundary
        truncated = title[:max_length-3]
        last_space = truncated.rfind(' ')
        if last_space > max_length * 0.7:  # Only use word boundary if it's not too short
            truncated = truncated[:last_space]
        
        return truncated + "..."
    
    def post_order(self, order_data: Dict, doc_url: str) -> Optional[Dict]:
        """Post an executive order announcement to Bluesky"""
        if not self.authenticated:
            if not self.authenticate():
                return None
        
        try:
            post_text = self.create_post_text(order_data, doc_url)
            
            # Create the post
            response = self.client.com.atproto.repo.create_record(
                repo=self.client.me.did,
                collection='app.bsky.feed.post',
                record={
                    'text': post_text,
                    'createdAt': self.client.get_current_time_iso(),
                    '$type': 'app.bsky.feed.post'
                }
            )
            
            return {
                'success': True,
                'uri': response.uri,
                'cid': response.cid,
                'post_text': post_text
            }
            
        except Exception as e:
            print(f"Failed to post to Bluesky: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_thread(self, order_data: Dict, doc_url: str, additional_info: str = None) -> Optional[Dict]:
        """Create a thread with more detailed information"""
        if not self.authenticated:
            if not self.authenticate():
                return None
        
        try:
            # First post
            main_post = self.post_order(order_data, doc_url)
            if not main_post or not main_post.get('success'):
                return main_post
            
            # Additional post with more details if provided
            if additional_info:
                reply_text = additional_info[:300]
                
                reply_response = self.client.com.atproto.repo.create_record(
                    repo=self.client.me.did,
                    collection='app.bsky.feed.post',
                    record={
                        'text': reply_text,
                        'createdAt': self.client.get_current_time_iso(),
                        'reply': {
                            'root': {
                                'uri': main_post['uri'],
                                'cid': main_post['cid']
                            },
                            'parent': {
                                'uri': main_post['uri'],
                                'cid': main_post['cid']
                            }
                        },
                        '$type': 'app.bsky.feed.post'
                    }
                )
                
                return {
                    'success': True,
                    'main_post': main_post,
                    'reply_post': {
                        'uri': reply_response.uri,
                        'cid': reply_response.cid
                    }
                }
            
            return main_post
            
        except Exception as e:
            print(f"Failed to create thread on Bluesky: {e}")
            return {
                'success': False,
                'error': str(e)
            }