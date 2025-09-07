#!/usr/bin/env python3
"""
Daily News Uploader - Scrapes trending news from ABP Live and feeds to content generation
"""

import os
import sys
import json
import requests
import feedparser
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Any
import schedule
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

class ABPLiveNewsScraper:
    """
    Scrapes trending news from ABP Live short video feed
    """
    
    def __init__(self):
        self.feed_url = "https://news.abplive.com/short-video/feed"
        self.setup_logging()
        self.data_dir = Path("daily_news_data")
        self.data_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daily_news_uploader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_trending_news(self) -> List[Dict[str, Any]]:
        """
        Fetch trending news from ABP Live feed
        """
        self.logger.info("Fetching trending news from ABP Live...")
        
        try:
            response = requests.get(self.feed_url, timeout=15)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                self.logger.warning("No entries found in feed")
                return []
            
            news_items = []
            
            for entry in feed.entries:
                # Extract and clean title
                title = entry.get('title', '').strip()
                
                # Skip if no title
                if not title:
                    continue
                
                # Clean title (remove HTML entities, extra spaces)
                title = self.clean_title(title)
                
                news_item = {
                    'title': title,
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed'),
                    'description': self.clean_description(entry.get('description', '')),
                    'category': self.extract_category(title),
                    'scraped_at': datetime.now().isoformat()
                }
                
                news_items.append(news_item)
            
            self.logger.info(f"Successfully fetched {len(news_items)} news items")
            return news_items
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch news feed: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing news feed: {e}")
            return []
    
    def clean_title(self, title: str) -> str:
        """Clean and format news title"""
        import html
        
        # Decode HTML entities
        title = html.unescape(title)
        
        # Remove common prefixes
        prefixes_to_remove = [
            'Breaking News: ',
            'Breaking: ',
            'LIVE: ',
            'ABP NEWS: ',
            '| ABP NEWS',
            '| ABP News'
        ]
        
        for prefix in prefixes_to_remove:
            if title.startswith(prefix):
                title = title[len(prefix):]
            if title.endswith(prefix):
                title = title[:-len(prefix)]
        
        # Clean up spacing and formatting
        title = ' '.join(title.split())
        title = title.strip(' |')
        
        return title
    
    def clean_description(self, description: str) -> str:
        """Clean description text"""
        import html
        from bs4 import BeautifulSoup
        
        if not description:
            return ""
        
        # Remove HTML tags
        soup = BeautifulSoup(description, 'html.parser')
        text = soup.get_text()
        
        # Decode HTML entities
        text = html.unescape(text)
        
        # Clean up spacing
        text = ' '.join(text.split())
        
        return text[:200] + "..." if len(text) > 200 else text
    
    def extract_category(self, title: str) -> str:
        """Extract news category based on title keywords"""
        title_lower = title.lower()
        
        categories = {
            'politics': ['parliament', 'minister', 'government', 'election', 'political', 'congress', 'bjp', 'opposition'],
            'religion': ['temple', 'devotee', 'sawan', 'yatra', 'religious', 'worship', 'pilgrimage', 'festival'],
            'breaking': ['breaking', 'urgent', 'alert', 'developing'],
            'security': ['security', 'terrorism', 'attack', 'threat', 'border', 'military'],
            'sports': ['cricket', 'football', 'olympics', 'match', 'tournament', 'player'],
            'business': ['market', 'stock', 'economy', 'business', 'finance', 'trade'],
            'international': ['pakistan', 'china', 'usa', 'international', 'global', 'world']
        }
        
        for category, keywords in categories.items():
            if any(keyword in title_lower for keyword in keywords):
                return category
        
        return 'general'
    
    def save_daily_data(self, news_items: List[Dict[str, Any]]) -> str:
        """Save news data to daily file"""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = self.data_dir / f"abp_news_{today}.json"
        
        # Load existing data if file exists
        existing_data = []
        if filename.exists():
            try:
                with open(filename, 'r', encoding='utf-8') as f:
                    existing_data = json.load(f)
            except:
                pass
        
        # Combine with new data (avoid duplicates by title)
        existing_titles = {item.get('title', '') for item in existing_data}
        new_items = [item for item in news_items if item['title'] not in existing_titles]
        
        all_data = existing_data + new_items
        
        # Save updated data
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(new_items)} new items to {filename}")
        self.logger.info(f"Total items for today: {len(all_data)}")
        
        return str(filename)
    
    def get_trending_titles_for_generation(self, limit: int = 10) -> List[str]:
        """
        Get clean titles suitable for content generation
        """
        news_items = self.fetch_trending_news()
        
        if not news_items:
            return []
        
        # Select most interesting titles for content generation
        suitable_titles = []
        
        for item in news_items[:limit * 2]:  # Get extra to filter
            title = item['title']
            
            # Skip titles that are too short or generic
            if len(title) < 20 or len(title) > 150:
                continue
            
            # Skip titles with too many special characters
            if title.count('|') > 2 or title.count(':') > 2:
                continue
            
            # Prefer certain categories
            category = item['category']
            if category in ['breaking', 'politics', 'international']:
                suitable_titles.insert(0, title)  # Prioritize these
            else:
                suitable_titles.append(title)
        
        return suitable_titles[:limit]


class ContentGenerationIntegrator:
    """
    Integrates scraped news with content generation system
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.generation_queue_file = Path("content_generation_queue.json")
        
    def add_to_generation_queue(self, titles: List[str]) -> None:
        """Add news titles to content generation queue"""
        
        # Load existing queue
        queue = []
        if self.generation_queue_file.exists():
            try:
                with open(self.generation_queue_file, 'r', encoding='utf-8') as f:
                    queue = json.load(f)
            except:
                pass
        
        # Add new items with metadata
        timestamp = datetime.now().isoformat()
        for title in titles:
            queue_item = {
                'title': title,
                'source': 'ABP Live',
                'added_at': timestamp,
                'status': 'pending',
                'type': 'news_story'
            }
            queue.append(queue_item)
        
        # Save updated queue
        with open(self.generation_queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Added {len(titles)} titles to content generation queue")
    
    def call_generation_script(self, title: str) -> bool:
        """
        Call the content generation script with a news title
        """
        try:
            # Option 1: Use the integrated content generator
            try:
                from content_generator_integration import ContentGenerator
                generator = ContentGenerator()
                result = generator.generate_content(title, 'ABP Live')
                
                if result['status'] == 'success':
                    self.logger.info(f"Successfully generated content for: {title}")
                    return True
                else:
                    self.logger.error(f"Generation failed for {title}: {result.get('error', 'Unknown error')}")
                    return False
                    
            except ImportError:
                self.logger.warning("ContentGenerator not available, trying command line approach")
            
            # Option 2: Command line fallback
            import subprocess
            
            cmd = [
                sys.executable, 
                'content_generator_integration.py',
                '--title', title,
                '--source', 'ABP Live'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully generated content for: {title}")
                return True
            else:
                self.logger.error(f"Generation failed for {title}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error calling generation script for '{title}': {e}")
            return False


class DailyNewsUploader:
    """
    Main class that orchestrates daily news uploading
    """
    
    def __init__(self):
        self.scraper = ABPLiveNewsScraper()
        self.integrator = ContentGenerationIntegrator()
        self.logger = logging.getLogger(__name__)
        
    def run_daily_upload(self) -> None:
        """Run the daily news upload process"""
        self.logger.info("=" * 50)
        self.logger.info("Starting daily news upload process")
        self.logger.info("=" * 50)
        
        try:
            # 1. Fetch trending news
            news_items = self.scraper.fetch_trending_news()
            
            if not news_items:
                self.logger.warning("No news items fetched, skipping upload")
                return
            
            # 2. Save daily data
            data_file = self.scraper.save_daily_data(news_items)
            
            # 3. Get titles for content generation
            titles = self.scraper.get_trending_titles_for_generation(limit=10)
            
            if not titles:
                self.logger.warning("No suitable titles for content generation")
                return
            
            self.logger.info(f"Selected {len(titles)} titles for content generation:")
            for i, title in enumerate(titles, 1):
                self.logger.info(f"  {i}. {title}")
            
            # 4. Add to generation queue
            self.integrator.add_to_generation_queue(titles)
            
            # 5. Generate content (optional - you can run this separately)
            self.generate_content_from_queue()
            
            self.logger.info("Daily news upload process completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in daily upload process: {e}")
            raise
    
    def generate_content_from_queue(self, max_items: int = 3) -> None:
        """Generate content for items in queue"""
        self.logger.info("Starting content generation from queue...")
        
        if not self.integrator.generation_queue_file.exists():
            self.logger.info("No generation queue file found")
            return
        
        try:
            with open(self.integrator.generation_queue_file, 'r', encoding='utf-8') as f:
                queue = json.load(f)
        except:
            self.logger.error("Failed to load generation queue")
            return
        
        # Process pending items
        pending_items = [item for item in queue if item.get('status') == 'pending']
        
        self.logger.info(f"Processing {min(len(pending_items), max_items)} items from queue")
        
        for item in pending_items[:max_items]:
            title = item['title']
            
            # Call generation script
            success = self.integrator.call_generation_script(title)
            
            # Update status
            item['status'] = 'completed' if success else 'failed'
            item['processed_at'] = datetime.now().isoformat()
            
            # Small delay between generations
            time.sleep(2)
        
        # Save updated queue
        try:
            with open(self.integrator.generation_queue_file, 'w', encoding='utf-8') as f:
                json.dump(queue, f, indent=2, ensure_ascii=False)
        except:
            self.logger.error("Failed to save updated queue")
    
    def setup_scheduler(self) -> None:
        """Setup daily scheduling"""
        self.logger.info("Setting up daily news upload scheduler...")
        
        # Schedule daily runs at 8 AM, 2 PM, and 8 PM
        schedule.every().day.at("08:00").do(self.run_daily_upload)
        schedule.every().day.at("14:00").do(self.run_daily_upload)
        schedule.every().day.at("20:00").do(self.run_daily_upload)
        
        self.logger.info("Scheduler configured for 8 AM, 2 PM, and 8 PM daily")
    
    def run_scheduler(self) -> None:
        """Run the scheduler (blocking)"""
        self.setup_scheduler()
        
        self.logger.info("Daily news uploader started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily News Uploader")
    parser.add_argument('--run-once', action='store_true', help='Run once instead of scheduling')
    parser.add_argument('--generate-only', action='store_true', help='Only generate content from existing queue')
    parser.add_argument('--max-items', type=int, default=3, help='Max items to generate (default: 3)')
    
    args = parser.parse_args()
    
    uploader = DailyNewsUploader()
    
    if args.generate_only:
        uploader.generate_content_from_queue(args.max_items)
    elif args.run_once:
        uploader.run_daily_upload()
    else:
        uploader.run_scheduler()


if __name__ == "__main__":
    main()