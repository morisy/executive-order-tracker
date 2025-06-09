import json
from datetime import datetime
from typing import Dict, List, Optional, Set

class StateManager:
    """Manage state for tracking processed executive orders"""
    
    def __init__(self, addon):
        """Initialize with DocumentCloud addon instance"""
        self.addon = addon
        self.state = self._load_state()
    
    def _load_state(self) -> Dict:
        """Load state from DocumentCloud addon storage"""
        try:
            # DocumentCloud addons store state in the 'data' attribute
            stored_state = self.addon.data.get('state', {})
            
            # Ensure all required fields exist
            default_state = {
                'last_check': None,
                'processed_orders': [],
                'posted_to_bluesky': [],
                'last_order_date': None,
                'version': '1.0'
            }
            
            # Merge stored state with defaults
            for key, value in default_state.items():
                if key not in stored_state:
                    stored_state[key] = value
            
            return stored_state
            
        except Exception as e:
            print(f"Error loading state: {e}")
            return {
                'last_check': None,
                'processed_orders': [],
                'posted_to_bluesky': [],
                'last_order_date': None,
                'version': '1.0'
            }
    
    def save_state(self):
        """Save state to DocumentCloud addon storage"""
        try:
            # Update last check time
            self.state['last_check'] = datetime.utcnow().isoformat()
            
            # Store state in addon data
            self.addon.data['state'] = self.state
            
            # Persist to DocumentCloud
            self.addon.save()
            
        except Exception as e:
            print(f"Error saving state: {e}")
            raise
    
    def is_order_processed(self, order_id: str) -> bool:
        """Check if an order has already been processed"""
        return order_id in self.state.get('processed_orders', [])
    
    def mark_order_processed(self, order_id: str):
        """Mark an order as processed"""
        if 'processed_orders' not in self.state:
            self.state['processed_orders'] = []
        
        if order_id not in self.state['processed_orders']:
            self.state['processed_orders'].append(order_id)
    
    def is_posted_to_bluesky(self, order_id: str) -> bool:
        """Check if an order has been posted to Bluesky"""
        return order_id in self.state.get('posted_to_bluesky', [])
    
    def mark_posted_to_bluesky(self, order_id: str):
        """Mark an order as posted to Bluesky"""
        if 'posted_to_bluesky' not in self.state:
            self.state['posted_to_bluesky'] = []
        
        if order_id not in self.state['posted_to_bluesky']:
            self.state['posted_to_bluesky'].append(order_id)
    
    def get_new_orders(self, orders: List[Dict]) -> List[Dict]:
        """Filter orders to only return new ones"""
        processed_ids = set(self.state.get('processed_orders', []))
        new_orders = []
        
        for order in orders:
            if order['id'] not in processed_ids:
                new_orders.append(order)
        
        # Sort by date if available (newest first)
        new_orders.sort(key=lambda x: x.get('date_str', ''), reverse=True)
        
        return new_orders
    
    def update_last_order_date(self, date_str: str):
        """Update the date of the most recent order processed"""
        self.state['last_order_date'] = date_str
    
    def get_last_check(self) -> Optional[datetime]:
        """Get the last check timestamp"""
        last_check = self.state.get('last_check')
        if last_check:
            try:
                return datetime.fromisoformat(last_check)
            except:
                return None
        return None
    
    def cleanup_old_entries(self, days_to_keep: int = 90):
        """Clean up old entries to prevent state from growing too large"""
        # For now, we'll keep all entries as they're just IDs
        # In the future, we might want to implement a more sophisticated cleanup
        pass
    
    def get_stats(self) -> Dict:
        """Get statistics about processed orders"""
        return {
            'total_processed': len(self.state.get('processed_orders', [])),
            'total_posted': len(self.state.get('posted_to_bluesky', [])),
            'last_check': self.state.get('last_check'),
            'last_order_date': self.state.get('last_order_date')
        }