#!/usr/bin/env python3
"""
Daily News Uploader - Scrapes satirical content from The Daily Mash and feeds to creative story generation
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

class DailyMashNewsScraper:
    """
    Scrapes satirical content from The Daily Mash for creative story generation
    """
    
    def __init__(self):
        self.feed_url = "https://www.thedailymash.co.uk/feed"
        self.setup_logging()
        self.data_dir = Path("daily_mash_news_data")
        self.data_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daily_mash_news_uploader.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_satirical_content(self) -> List[Dict[str, Any]]:
        """
        Fetch satirical content from The Daily Mash feed
        """
        self.logger.info("Fetching satirical content from The Daily Mash...")
        
        try:
            response = requests.get(self.feed_url, timeout=15)
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                self.logger.warning("No entries found in Daily Mash feed")
                return []
            
            content_items = []
            
            for entry in feed.entries:
                # Extract and clean title
                title = entry.get('title', '').strip()
                
                # Skip if no title
                if not title:
                    continue
                
                # Extract full content
                full_content = self.extract_full_content(entry)
                
                if not full_content or len(full_content) < 100:  # Skip very short content
                    continue
                
                content_item = {
                    'title': self.clean_title(title),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'published_parsed': entry.get('published_parsed'),
                    'description': self.clean_description(entry.get('description', '')),
                    'full_content': full_content,
                    'word_count': len(full_content.split()),
                    'category': self.extract_category_from_link(entry.get('link', '')),
                    'humor_type': self.detect_humor_type(title, full_content),
                    'scraped_at': datetime.now().isoformat()
                }
                
                content_items.append(content_item)
            
            self.logger.info(f"Successfully fetched {len(content_items)} satirical articles")
            return content_items
            
        except requests.RequestException as e:
            self.logger.error(f"Failed to fetch Daily Mash feed: {e}")
            return []
        except Exception as e:
            self.logger.error(f"Error parsing Daily Mash feed: {e}")
            return []
    
    def extract_full_content(self, entry) -> str:
        """Extract the full article content"""
        import html
        from bs4 import BeautifulSoup
        
        full_content = ''
        
        # Try to get content from content blocks
        content_blocks = entry.get('content', [])
        if content_blocks:
            for content_block in content_blocks:
                if hasattr(content_block, 'value'):
                    full_content = content_block.value
                elif isinstance(content_block, dict) and 'value' in content_block:
                    full_content = content_block['value']
                else:
                    full_content = str(content_block)
                break
        
        # Fallback to description
        if not full_content:
            full_content = entry.get('description', '')
        
        if full_content:
            # Clean HTML
            soup = BeautifulSoup(full_content, 'html.parser')
            clean_text = soup.get_text()
            
            # Decode HTML entities
            clean_text = html.unescape(clean_text)
            
            # Format nicely
            paragraphs = [p.strip() for p in clean_text.split('\n') if p.strip()]
            formatted_content = '\n\n'.join(paragraphs)
            
            return formatted_content
        
        return ''
    
    def clean_title(self, title: str) -> str:
        """Clean and format article title"""
        import html
        
        # Decode HTML entities
        title = html.unescape(title)
        
        # Clean up spacing and formatting
        title = ' '.join(title.split())
        title = title.strip()
        
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
        
        return text[:300] + "..." if len(text) > 300 else text
    
    def extract_category_from_link(self, link: str) -> str:
        """Extract category from the article URL"""
        if not link:
            return 'general'
        
        # The Daily Mash categories from URL structure
        if '/politics/' in link:
            return 'politics'
        elif '/news/society/' in link:
            return 'society'
        elif '/news/celebrity/' in link:
            return 'celebrity'
        elif '/news/arts-entertainment/' in link:
            return 'arts-entertainment'
        elif '/news/sport/' in link:
            return 'sport'
        elif '/news/technology/' in link:
            return 'technology'
        else:
            return 'general'
    
    def detect_humor_type(self, title: str, content: str) -> str:
        """Detect the type of humor/satire"""
        text = (title + ' ' + content).lower()
        
        humor_types = {
            'absurdist': ['research has shown', 'institute for studies', 'professor', 'study finds'],
            'social_satire': ['british values', 'middle class', 'generation', 'society'],
            'political_satire': ['minister', 'government', 'parliament', 'policy', 'brexit'],
            'celebrity_satire': ['celebrity', 'famous', 'star', 'hollywood', 'fashion'],
            'everyday_life': ['party', 'work', 'office', 'relationship', 'family', 'friends'],
            'technology': ['app', 'social media', 'internet', 'smartphone', 'digital'],
        }
        
        for humor_type, keywords in humor_types.items():
            if any(keyword in text for keyword in keywords):
                return humor_type
        
        return 'general'
    
    def save_daily_data(self, content_items: List[Dict[str, Any]]) -> str:
        """Save content data to daily file"""
        today = datetime.now().strftime('%Y-%m-%d')
        filename = self.data_dir / f"daily_mash_news_{today}.json"
        
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
        new_items = [item for item in content_items if item['title'] not in existing_titles]
        
        all_data = existing_data + new_items
        
        # Save updated data
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(all_data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Saved {len(new_items)} new items to {filename}")
        self.logger.info(f"Total items for today: {len(all_data)}")
        
        return str(filename)
    
    def get_content_for_generation(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get content suitable for creative story generation
        """
        content_items = self.fetch_satirical_content()
        
        if not content_items:
            return []
        
        # Filter and rank content for generation
        suitable_content = []
        
        for item in content_items:
            # Quality filters
            if item['word_count'] < 50 or item['word_count'] > 1000:
                continue
            
            # Prefer certain humor types for generation
            humor_type = item['humor_type']
            priority = 0
            
            if humor_type in ['absurdist', 'social_satire', 'everyday_life']:
                priority = 3  # High priority
            elif humor_type in ['political_satire', 'celebrity_satire']:
                priority = 2  # Medium priority
            else:
                priority = 1  # Lower priority
            
            item['generation_priority'] = priority
            suitable_content.append(item)
        
        # Sort by priority and recency
        suitable_content.sort(key=lambda x: (
            x['generation_priority'],
            x['published_parsed'] if x['published_parsed'] else (0,)
        ), reverse=True)
        
        return suitable_content[:limit]


class ContentGenerationIntegrator:
    """
    Integrates scraped satirical content with creative story generation system
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.generation_queue_file = Path("content_generation_queue.json")
        
    def add_to_generation_queue(self, content_items: List[Dict[str, Any]]) -> None:
        """Add satirical content to creative generation queue"""
        
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
        for content_item in content_items:
            queue_item = {
                'title': content_item['title'],
                'full_content': content_item['full_content'],
                'humor_type': content_item['humor_type'],
                'category': content_item['category'],
                'source': 'The Daily Mash',
                'added_at': timestamp,
                'status': 'pending',
                'type': 'satirical_story'
            }
            queue.append(queue_item)
        
        # Save updated queue
        with open(self.generation_queue_file, 'w', encoding='utf-8') as f:
            json.dump(queue, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Added {len(content_items)} satirical articles to creative generation queue")
    
    def call_generation_script(self, content_item: Dict[str, Any]) -> bool:
        """
        Call the creative generation script with satirical content
        """
        try:
            # Option 1: Use the integrated content generator
            try:
                from content_generator_integration import ContentGenerator
                generator = ContentGenerator()
                result = generator.generate_creative_story(
                    content_item['title'], 
                    content_item['full_content'],
                    'The Daily Mash',
                    content_item['humor_type']
                )
                
                if result['status'] == 'success':
                    self.logger.info(f"Successfully generated creative story for: {content_item['title']}")
                    return True
                else:
                    self.logger.error(f"Generation failed for {content_item['title']}: {result.get('error', 'Unknown error')}")
                    return False
                    
            except ImportError:
                self.logger.warning("ContentGenerator not available, trying command line approach")
            
            # Option 2: Command line fallback
            import subprocess
            
            cmd = [
                sys.executable, 
                'content_generator_integration.py',
                '--title', content_item['title'],
                '--content', content_item['full_content'],
                '--source', 'The Daily Mash',
                '--humor-type', content_item['humor_type']
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.returncode == 0:
                self.logger.info(f"Successfully generated creative story for: {content_item['title']}")
                return True
            else:
                self.logger.error(f"Generation failed for {content_item['title']}: {result.stderr}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error calling generation script for '{content_item['title']}': {e}")
            return False


class DailyNewsUploader:
    """
    Main class that orchestrates daily satirical content uploading for creative story generation
    """
    
    def __init__(self):
        self.scraper = DailyMashNewsScraper()
        self.integrator = ContentGenerationIntegrator()
        self.logger = logging.getLogger(__name__)
        
    def run_daily_upload(self) -> None:
        """Run the daily satirical content upload process"""
        self.logger.info("=" * 60)
        self.logger.info("Starting Daily Mash satirical content processing")
        self.logger.info("=" * 60)
        
        try:
            # 1. Fetch satirical content
            content_items = self.scraper.fetch_satirical_content()
            
            if not content_items:
                self.logger.warning("No satirical content items fetched, skipping processing")
                return
            
            # 2. Save daily data
            data_file = self.scraper.save_daily_data(content_items)
            
            # 3. Get content for creative generation (only one item for video)
            generation_content = self.scraper.get_content_for_generation(limit=1)
            
            if not generation_content:
                self.logger.warning("No suitable content for creative generation")
                return
            
            selected_content = generation_content[0]
            self.logger.info(f"Selected article for video generation:")
            self.logger.info(f"  Title: {selected_content['title']} ({selected_content['humor_type']})")
            self.logger.info(f"  Word count: {selected_content['word_count']}")
            self.logger.info(f"  Category: {selected_content['category']}")
            
            # 4. Generate video directly with this content
            self.generate_video_from_content(selected_content)
            
            self.logger.info("Daily Mash satirical content processing completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in daily satirical content processing: {e}")
            raise
    
    def generate_video_from_content(self, content_item: Dict[str, Any]) -> None:
        """Generate video directly from Daily Mash content"""
        self.logger.info("Starting video generation from satirical content...")
        
        try:
            # Import the video generator
            sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'local_functions'))
            from local_video_generator import LocalVideoGenerator
            
            # Create a creative prompt based on the satirical content
            creative_prompt = self.create_creative_prompt(content_item)
            
            self.logger.info(f"Generated creative prompt: {creative_prompt[:100]}...")
            
            # Generate video using the existing pipeline
            generator = LocalVideoGenerator()
            
            # Create custom title for the video based on the content
            video_title = self.create_video_title(content_item)
            
            result = generator.generate_video_with_content(
                topic=creative_prompt,
                style="entertaining", 
                segments=4,
                quality="medium",
                source_content=content_item['full_content'],
                humor_type=content_item['humor_type'],
                original_title=content_item['title']
            )
            
            if result['success']:
                self.logger.info(f"✓ Video generated successfully!")
                self.logger.info(f"  Output folder: {result['session_dir']}")
                self.logger.info(f"  Video file: {result.get('final_video', 'N/A')}")
                self.logger.info(f"  Video title: {video_title}")
                self.logger.info(f"  Duration: {result.get('duration', 'Unknown')} seconds")
                
                # Save metadata for potential YouTube upload
                metadata_file = self.save_video_metadata(content_item, video_title, result)
                
                # Optionally upload to YouTube (uncomment when ready)
                # self.upload_to_youtube(metadata_file)
                
            else:
                self.logger.error(f"✗ Video generation failed: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            self.logger.error(f"Error in video generation: {e}")
            import traceback
            self.logger.error(traceback.format_exc())
    
    def create_creative_prompt(self, content_item: Dict[str, Any]) -> str:
        """Create a creative video prompt based on Daily Mash satirical content"""
        title = content_item['title']
        content = content_item['full_content']
        humor_type = content_item['humor_type']
        
        # Extract key themes and create an engaging prompt
        if humor_type == 'absurdist':
            prompt = f"Create an entertaining video about the absurd reality of {title.lower()}. This satirical piece reveals the ridiculous nature of everyday situations through exaggerated research findings and pseudo-scientific observations. Focus on the humor in human behavior and social quirks."
        elif humor_type == 'social_satire':
            prompt = f"Explore the social commentary behind '{title}'. This satirical take on modern society highlights the contradictions and hypocrisies in our daily lives. Present the insights with wit and observational humor about contemporary culture."
        elif humor_type == 'political_satire':
            prompt = f"Create content inspired by the political satire '{title}'. Focus on the absurdities of modern politics and governance, presenting the humor in political situations while keeping it accessible and entertaining."
        elif humor_type == 'celebrity_satire':
            prompt = f"Develop entertaining content around the celebrity culture themes from '{title}'. Explore the humorous aspects of fame, public personas, and entertainment industry dynamics."
        elif humor_type == 'everyday_life':
            prompt = f"Create relatable content about '{title}'. Focus on the humorous observations about daily life, relationships, and common human experiences that everyone can identify with."
        else:
            prompt = f"Create entertaining content inspired by the satirical piece '{title}'. Focus on the humor and wit in the original content while making it engaging for a broader audience."
        
        return prompt
    
    def create_video_title(self, content_item: Dict[str, Any]) -> str:
        """Create an engaging video title based on the satirical content"""
        original_title = content_item['title']
        humor_type = content_item['humor_type']
        
        # Create engaging titles based on humor type
        if humor_type == 'absurdist':
            if 'research' in original_title.lower() or 'study' in original_title.lower():
                return f"Ridiculous Research: {original_title}"
            else:
                return f"The Absurd Truth: {original_title}"
        elif humor_type == 'social_satire':
            return f"Society Check: {original_title}"
        elif humor_type == 'everyday_life':
            return f"Daily Reality: {original_title}"
        elif humor_type == 'celebrity_satire':
            return f"Celebrity Watch: {original_title}"
        elif humor_type == 'political_satire':
            return f"Political Comedy: {original_title}"
        else:
            return f"Satirical Take: {original_title}"
    
    def save_video_metadata(self, content_item: Dict[str, Any], video_title: str, video_result: Dict[str, Any]) -> None:
        """Save video metadata for potential YouTube upload"""
        metadata = {
            'video_title': video_title,
            'original_content': {
                'title': content_item['title'],
                'humor_type': content_item['humor_type'],
                'category': content_item['category'],
                'source': 'The Daily Mash',
                'word_count': content_item['word_count']
            },
            'video_info': {
                'session_dir': video_result.get('session_dir'),
                'final_video': video_result.get('final_video'),
                'duration': video_result.get('duration'),
                'generated_at': datetime.now().isoformat()
            },
            'youtube_ready': True,
            'description': self.create_video_description(content_item)
        }
        
        # Save to metadata file
        metadata_dir = Path("video_metadata")
        metadata_dir.mkdir(exist_ok=True)
        
        safe_title = "".join(c for c in video_title if c.isalnum() or c in (' ', '-', '_')).strip()[:50]
        metadata_file = metadata_dir / f"{safe_title}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"Video metadata saved to: {metadata_file}")
        return metadata_file
    
    def create_video_description(self, content_item: Dict[str, Any]) -> str:
        """Create YouTube description based on content"""
        humor_type = content_item['humor_type'].replace('_', ' ').title()
        
        description = f"""
A satirical take inspired by The Daily Mash's hilarious observations about modern life.

Original inspiration: "{content_item['title']}"
Style: {humor_type}
Category: {content_item['category'].title()}

This video transforms satirical content into entertaining visual storytelling, highlighting the absurdities and humor in everyday situations.

#Comedy #Satire #Entertainment #DailyLife #Humor #SocialCommentary

Content inspired by The Daily Mash - bringing you satirical insights about the world around us.
Generated with AI assistance for creative storytelling.
"""
        return description.strip()
    
    def upload_to_youtube(self, metadata_file: str) -> None:
        """Upload video to YouTube using the metadata file"""
        try:
            self.logger.info("Starting YouTube upload...")
            
            # Import YouTube uploader
            from youtube_uploader import YouTubeUploader
            
            uploader = YouTubeUploader()
            result = uploader.upload_video_from_metadata(metadata_file)
            
            if result['success']:
                self.logger.info(f"✓ YouTube upload successful!")
                self.logger.info(f"  Video URL: {result.get('video_url', 'N/A')}")
                self.logger.info(f"  Video ID: {result.get('video_id', 'N/A')}")
            else:
                self.logger.error(f"✗ YouTube upload failed: {result['error']}")
                
        except ImportError:
            self.logger.warning("YouTube uploader not available - install google-api-python-client and google-auth-oauthlib")
        except Exception as e:
            self.logger.error(f"YouTube upload error: {e}")
    
    def setup_scheduler(self) -> None:
        """Setup daily scheduling"""
        self.logger.info("Setting up Daily Mash content scheduler...")
        
        # Schedule runs twice daily - morning and evening
        schedule.every().day.at("09:00").do(self.run_daily_upload)
        schedule.every().day.at("18:00").do(self.run_daily_upload)
        
        self.logger.info("Scheduler configured for 9 AM and 6 PM daily")
    
    def run_scheduler(self) -> None:
        """Run the scheduler (blocking)"""
        self.setup_scheduler()
        
        self.logger.info("Daily Mash creative uploader started. Press Ctrl+C to stop.")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)  # Check every minute
        except KeyboardInterrupt:
            self.logger.info("Scheduler stopped by user")


def main():
    """Main function"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Daily Mash Creative Content Uploader")
    parser.add_argument('--run-once', action='store_true', help='Run once instead of scheduling')
    parser.add_argument('--video-only', action='store_true', help='Only generate video from latest content')
    
    args = parser.parse_args()
    
    uploader = DailyNewsUploader()
    
    if args.video_only:
        # Get the latest content and generate video
        content_items = uploader.scraper.get_content_for_generation(limit=1)
        if content_items:
            uploader.generate_video_from_content(content_items[0])
        else:
            print("No content available for video generation")
    elif args.run_once:
        uploader.run_daily_upload()
    else:
        uploader.run_scheduler()


if __name__ == "__main__":
    main()