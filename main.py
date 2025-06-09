from documentcloud.addon import AddOn
from documentcloud.exceptions import APIError
from datetime import datetime, timedelta
import os
import tempfile
from typing import List, Dict, Optional

from scraper import WhiteHouseScraper
from pdf_generator import PDFGenerator
from storage import StateManager
from bluesky_poster import BlueskyPoster


class ExecutiveOrdersMonitor(AddOn):
    """Monitor White House website for new Executive Orders and archive them"""
    
    def main(self):
        """Main execution method"""
        self.set_message("Starting Executive Orders Monitor...")
        
        # Initialize components
        self.state_manager = StateManager(self)
        self.scraper = WhiteHouseScraper()
        self.pdf_generator = PDFGenerator()
        
        # Check if this is a scheduled run or manual trigger
        if self._should_skip_check():
            self.set_message("Skipping check - not enough time since last run")
            return
        
        # Get configuration
        include_proclamations = self.data.get('include_proclamations', False)
        archive_to_ia = self.data.get('archive_to_ia', True)
        
        # Initialize Bluesky if credentials provided
        bluesky_client = None
        if self.data.get('bluesky_handle') and self.data.get('bluesky_password'):
            bluesky_client = BlueskyPoster(
                self.data['bluesky_handle'],
                self.data['bluesky_password']
            )
        
        try:
            # Scrape current orders
            self.set_message("Scraping White House Presidential Actions page...")
            all_orders = self.scraper.scrape_recent_orders(include_proclamations)
            
            # Filter to only new orders
            new_orders = self.state_manager.get_new_orders(all_orders)
            
            if not new_orders:
                self.set_message("No new executive orders found")
                self.state_manager.save_state()
                return
            
            self.set_message(f"Found {len(new_orders)} new executive order(s)")
            
            # Process each new order
            processed_count = 0
            for i, order in enumerate(new_orders):
                try:
                    self.set_message(f"Processing order {i+1}/{len(new_orders)}: {order['title']}")
                    
                    # Generate PDF
                    with tempfile.NamedTemporaryFile(suffix='.pdf', delete=False) as tmp_file:
                        pdf_path = tmp_file.name
                        self.pdf_generator.generate_pdf(order, pdf_path)
                    
                    # Upload to DocumentCloud
                    doc = self._upload_to_documentcloud(order, pdf_path)
                    
                    # Clean up temp file
                    os.unlink(pdf_path)
                    
                    if doc:
                        # Archive to Internet Archive if enabled
                        if archive_to_ia:
                            self._archive_to_internet_archive(doc)
                        
                        # Post to Bluesky if configured
                        if bluesky_client and not self.state_manager.is_posted_to_bluesky(order['id']):
                            doc_url = doc.canonical_url
                            post_result = bluesky_client.post_order(order, doc_url)
                            if post_result and post_result.get('success'):
                                self.state_manager.mark_posted_to_bluesky(order['id'])
                                print(f"Posted to Bluesky: {post_result.get('uri')}")
                        
                        # Mark as processed
                        self.state_manager.mark_order_processed(order['id'])
                        processed_count += 1
                    
                except Exception as e:
                    print(f"Error processing order {order['id']}: {e}")
                    self.set_message(f"Error processing order: {str(e)}")
                    continue
            
            # Save state
            self.state_manager.save_state()
            
            # Generate summary
            stats = self.state_manager.get_stats()
            summary = (
                f"Processed {processed_count} new executive order(s). "
                f"Total processed: {stats['total_processed']}"
            )
            if bluesky_client:
                summary += f", Posted to Bluesky: {stats['total_posted']}"
            
            self.set_message(summary)
            
        except Exception as e:
            self.set_message(f"Error: {str(e)}")
            raise
    
    def _should_skip_check(self) -> bool:
        """Check if we should skip this run based on configured interval"""
        last_check = self.state_manager.get_last_check()
        if not last_check:
            return False
        
        check_interval_hours = self.data.get('check_interval_hours', 24)
        min_interval = timedelta(hours=check_interval_hours)
        
        return (datetime.utcnow() - last_check) < min_interval
    
    def _upload_to_documentcloud(self, order: Dict, pdf_path: str) -> Optional[object]:
        """Upload PDF to DocumentCloud"""
        try:
            # Prepare document data
            title = order.get('title', 'Executive Order')
            if order.get('order_number'):
                title = f"EO {order['order_number']}: {title}"
            
            # Create source string
            source = "White House"
            if order.get('date_str'):
                source += f" - {order['date_str']}"
            
            # Prepare data for upload
            doc_data = {
                'title': title,
                'source': source,
                'description': f"Executive Order scraped from {order.get('url', 'whitehouse.gov')}",
                'language': 'eng',
                'data': {
                    'order_id': order['id'],
                    'order_number': order.get('order_number'),
                    'original_url': order.get('url'),
                    'scrape_date': datetime.utcnow().isoformat(),
                    'order_type': order.get('type', 'executive_order')
                }
            }
            
            # Upload the document
            with open(pdf_path, 'rb') as pdf_file:
                doc = self.client.documents.upload(
                    pdf_file,
                    **doc_data
                )
            
            print(f"Uploaded document: {doc.id} - {doc.title}")
            return doc
            
        except Exception as e:
            print(f"Error uploading to DocumentCloud: {e}")
            return None
    
    def _archive_to_internet_archive(self, doc):
        """Trigger Internet Archive Export add-on for the document"""
        try:
            # Prepare the data for the Internet Archive Export add-on
            ia_addon_data = {
                'item_name': f"executive-order-{doc.data.get('order_id', doc.id)}",
                'filecoin': self.data.get('upload_to_ipfs', True),  # Enable IPFS/Filecoin upload
                'documents': [doc.id]
            }
            
            # Note: In production, you would trigger the Internet Archive Export add-on
            # using DocumentCloud's API. The addon would be identified by its repository
            # name (MuckRock/Internet-Archive-Export-Add-On)
            
            print(f"Document {doc.id} ready for Internet Archive export")
            print(f"  Item name: {ia_addon_data['item_name']}")
            print(f"  IPFS/Filecoin upload: {ia_addon_data['filecoin']}")
            
            # Example of how to trigger in production:
            # self.client.post('/api/addon_runs/', json={
            #     'addon': 'MuckRock/Internet-Archive-Export-Add-On',
            #     'parameters': ia_addon_data
            # })
            
        except Exception as e:
            print(f"Error triggering Internet Archive export: {e}")


if __name__ == "__main__":
    ExecutiveOrdersMonitor().main()