#!/usr/bin/env python3
"""
Daily Mash Uploader - Scrapes satirical news from The Daily Mash for creative story generation
"""

import os
import sys
import json
import requests
import feedparser
from bs4 import BeautifulSoup
import html
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Any
import schedule
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(__file__))

class DailyMashScraper:
    """
    Scrapes satirical/humorous content from The Daily Mash for creative story generation
    """
    
    def __init__(self):
        self.feed_url = "https://www.thedailymash.co.uk/feed"
        self.setup_logging()
        self.data_dir = Path("daily_mash_data")
        self.data_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('daily_mash_uploader.log'),
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
                # Extract basic info
                title = entry.get('title', '').strip()
                
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
        # Decode HTML entities
        title = html.unescape(title)
        
        # Clean up spacing and formatting
        title = ' '.join(title.split())
        title = title.strip()
        
        return title
    
    def clean_description(self, description: str) -> str:
        """Clean description text"""
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
        filename = self.data_dir / f"daily_mash_{today}.json"
        
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


class CreativeContentGenerator:
    """
    Enhanced content generator for creative storytelling with satirical source material
    """
    
    def __init__(self):
        self.setup_logging()
        self.output_dir = Path("generated_satirical_content")
        self.output_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        """Setup logging"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def generate_creative_story(self, source_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate creative content based on satirical source material
        
        This is where you would integrate with Gemini or your preferred generation model
        """
        self.logger.info(f"Generating creative story from: {source_content['title']}")
        
        try:
            # Prepare generation input with rich context
            generation_input = self.prepare_creative_input(source_content)
            
            # Call your actual generation method (replace with Gemini integration)
            generated_content = self.call_creative_generation_method(generation_input)
            
            # Save the generated content
            output_file = self.save_creative_content(source_content, generated_content)
            
            result = {
                'status': 'success',
                'original_title': source_content['title'],
                'original_content_preview': source_content['full_content'][:200] + "...",
                'generated_story': generated_content,
                'output_file': str(output_file),
                'source': 'The Daily Mash',
                'humor_type': source_content['humor_type'],
                'category': source_content['category'],
                'generated_at': datetime.now().isoformat()
            }
            
            self.logger.info(f"Successfully generated creative story from: {source_content['title']}")
            return result
            
        except Exception as e:
            self.logger.error(f"Failed to generate story for '{source_content['title']}': {e}")
            return {
                'status': 'error',
                'original_title': source_content['title'],
                'error': str(e),
                'generated_at': datetime.now().isoformat()
            }
    
    def prepare_creative_input(self, source_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare rich input for creative generation
        """
        return {
            'source_title': source_content['title'],
            'source_content': source_content['full_content'],
            'humor_type': source_content['humor_type'],
            'category': source_content['category'],
            'word_count': source_content['word_count'],
            'generation_type': 'creative_story',
            'style_instructions': self.get_style_instructions(source_content['humor_type']),
            'creative_prompt': self.build_creative_prompt(source_content),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_style_instructions(self, humor_type: str) -> str:
        """Get generation instructions based on humor type"""
        instructions = {
            'absurdist': "Create an absurdist story with unexpected twists, pseudo-scientific explanations, and ridiculous research findings.",
            'social_satire': "Write a satirical take on modern society, focusing on social norms, class differences, and cultural observations.",
            'political_satire': "Develop a political satire with witty commentary on current affairs, but keep it accessible and entertaining.",
            'celebrity_satire': "Create a celebrity-focused story with exaggerated personalities and entertainment industry commentary.",
            'everyday_life': "Write about relatable everyday situations with humorous exaggeration and observational comedy.",
            'technology': "Create a tech-focused story highlighting the absurdities of modern digital life and gadget culture.",
            'general': "Write an entertaining story with wit, humor, and unexpected developments."
        }
        
        return instructions.get(humor_type, instructions['general'])
    
    def build_creative_prompt(self, source_content: Dict[str, Any]) -> str:
        """Build a creative prompt for story generation"""
        
        title = source_content['title']
        content_preview = source_content['full_content'][:500]
        humor_type = source_content['humor_type']
        
        prompt = f"""
Create an original, creative story inspired by this satirical article:

Title: "{title}"
Humor Style: {humor_type}
Source Material Preview: {content_preview}

Instructions:
1. Use the source as inspiration but create completely original content
2. Maintain the satirical/humorous tone but add your own creative twists
3. Expand on the concept with new characters, situations, or perspectives
4. Make it engaging and entertaining for modern audiences
5. Keep the story between 300-600 words
6. Add unexpected plot developments or humorous observations
7. Create memorable characters or scenarios that readers will enjoy

Write a complete story that captures the spirit of the original while being entirely new and creative.
"""
        
        return prompt.strip()
    
    def call_creative_generation_method(self, generation_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call your creative generation method (integrate with Gemini here)
        
        REPLACE THIS WITH YOUR ACTUAL GEMINI/AI INTEGRATION
        """
        
        # TODO: Integrate with Gemini API
        # Example integration structure:
        # 
        # import google.generativeai as genai
        # 
        # genai.configure(api_key="YOUR_API_KEY")
        # model = genai.GenerativeModel('gemini-pro')
        # 
        # response = model.generate_content(generation_input['creative_prompt'])
        # return {
        #     'story': response.text,
        #     'title': f"Creative Story: {generation_input['source_title']}",
        #     'word_count': len(response.text.split()),
        #     'style': generation_input['humor_type']
        # }
        
        # Mock generation for now (replace with Gemini integration)
        self.logger.info("Using mock creative generation (replace with Gemini integration)")
        
        source_title = generation_input['source_title']
        humor_type = generation_input['humor_type']
        
        mock_story = f"""
**Creative Story: {source_title}**

Inspired by the satirical insights of The Daily Mash, here's an original creative story that explores the absurdities of modern life.

{self.generate_mock_creative_story(generation_input)}

This {humor_type} story takes the original concept and spins it into new territory, creating fresh entertainment while maintaining the satirical spirit that makes such observations so memorable.

The beauty of satirical source material is how it reveals universal truths through exaggeration, giving us endless material for creative storytelling that resonates with audiences.

---
Generated with Creative AI Enhancement
Style: {humor_type}
Source inspiration: The Daily Mash
Generated at: {generation_input['timestamp']}
"""
        
        return {
            'story': mock_story.strip(),
            'title': f"Creative Story: {source_title}",
            'word_count': len(mock_story.split()),
            'style': humor_type,
            'preview': f"A {humor_type} story inspired by: {source_title}"
        }
    
    def generate_mock_creative_story(self, generation_input: Dict[str, Any]) -> str:
        """Generate a mock creative story (replace with real generation)"""
        
        humor_type = generation_input['humor_type']
        source_content = generation_input['source_content'][:200]
        
        if humor_type == 'absurdist':
            return f"""
In a groundbreaking study conducted by the Institute of Obvious Conclusions, researchers discovered that {source_content.lower()}

Dr. Nigel Obviousworth, lead researcher, explained: "Our findings confirm what everyone already suspected, but now we have graphs to prove it. The implications are staggering, particularly for people who enjoy having their assumptions validated by science."

The study, which cost £2.3 million and took four years to complete, surveyed 12 people in a car park in Milton Keynes. The results were so predictable that the research team fell asleep halfway through analyzing them.
"""
        elif humor_type == 'social_satire':
            return f"""
In middle-class Britain today, the social dynamics observed in {source_content[:100]}... have become the defining characteristic of an entire generation's relationship with social expectations.

Marketing executive Sarah Middleton-Smythe, 34, from Clapham, represents this phenomenon perfectly. "I've spent years perfecting the art of appearing spontaneous while meticulously planning every aspect of my allegedly carefree lifestyle," she explains, checking her phone for Instagram likes.

This behavior pattern, now endemic among the aspiring middle classes, has created an entire economy based on the pursuit of authentic experiences that are anything but authentic.
"""
        else:
            return f"""
The situation described in the original piece - {source_content[:150]}... - reveals something profound about human nature and our collective relationship with the absurd.

Consider how this scenario plays out in real life: we all recognize the truth in it, yet we continue to participate in the very behaviors being satirized. It's as if we're all complicit in a grand joke that we simultaneously understand and refuse to acknowledge.

This is the genius of satirical observation - it holds up a mirror to our collective foolishness while making us laugh at our own reflection.
"""
    
    def save_creative_content(self, source_content: Dict[str, Any], generated_content: Dict[str, Any]) -> Path:
        """Save generated creative content"""
        
        # Create safe filename from original title
        safe_title = "".join(c for c in source_content['title'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_title = safe_title[:50]  # Limit length
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{safe_title}_{timestamp}.json"
        
        output_file = self.output_dir / filename
        
        # Save complete creative content data
        creative_data = {
            'source_article': {
                'title': source_content['title'],
                'original_content': source_content['full_content'],
                'humor_type': source_content['humor_type'],
                'category': source_content['category'],
                'published': source_content['published'],
                'link': source_content['link']
            },
            'generated_content': generated_content,
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'filename': filename,
                'generation_method': 'creative_ai_enhanced'
            }
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(creative_data, f, indent=2, ensure_ascii=False)
        
        # Also save readable text version
        text_file = output_file.with_suffix('.txt')
        with open(text_file, 'w', encoding='utf-8') as f:
            f.write("ORIGINAL SOURCE:\n")
            f.write("=" * 50 + "\n")
            f.write(f"Title: {source_content['title']}\n")
            f.write(f"Category: {source_content['category']} ({source_content['humor_type']})\n")
            f.write(f"Published: {source_content['published']}\n")
            f.write(f"Link: {source_content['link']}\n\n")
            f.write(source_content['full_content'])
            f.write("\n\n" + "=" * 50 + "\n")
            f.write("GENERATED CREATIVE STORY:\n")
            f.write("=" * 50 + "\n\n")
            f.write(generated_content.get('story', 'No content generated'))
            f.write("\n\n" + "=" * 50 + "\n")
            f.write(f"Generated at: {datetime.now()}\n")
        
        self.logger.info(f"Saved creative content to: {output_file}")
        return output_file


class DailyMashUploader:
    """
    Main class for The Daily Mash content uploading and creative generation
    """
    
    def __init__(self):
        self.scraper = DailyMashScraper()
        self.generator = CreativeContentGenerator()
        self.logger = logging.getLogger(__name__)
        
    def run_daily_upload(self) -> None:
        """Run the daily satirical content upload and generation process"""
        self.logger.info("=" * 60)
        self.logger.info("Starting Daily Mash content processing")
        self.logger.info("=" * 60)
        
        try:
            # 1. Fetch satirical content
            content_items = self.scraper.fetch_satirical_content()
            
            if not content_items:
                self.logger.warning("No content items fetched, skipping processing")
                return
            
            # 2. Save daily data
            data_file = self.scraper.save_daily_data(content_items)
            
            # 3. Get content for creative generation
            generation_content = self.scraper.get_content_for_generation(limit=5)
            
            if not generation_content:
                self.logger.warning("No suitable content for generation")
                return
            
            self.logger.info(f"Selected {len(generation_content)} articles for creative generation:")
            for i, item in enumerate(generation_content, 1):
                self.logger.info(f"  {i}. {item['title']} ({item['humor_type']})")
            
            # 4. Generate creative stories
            self.generate_creative_stories(generation_content)
            
            self.logger.info("Daily Mash content processing completed successfully")
            
        except Exception as e:
            self.logger.error(f"Error in daily Mash processing: {e}")
            raise
    
    def generate_creative_stories(self, content_items: List[Dict[str, Any]], max_items: int = 3) -> None:
        """Generate creative stories from satirical content"""
        self.logger.info("Starting creative story generation...")
        
        for i, item in enumerate(content_items[:max_items], 1):
            self.logger.info(f"Generating story {i}/{min(len(content_items), max_items)}: {item['title']}")
            
            result = self.generator.generate_creative_story(item)
            
            if result['status'] == 'success':
                self.logger.info(f"✓ Generated: {result['generated_story']['title']}")
            else:
                self.logger.error(f"✗ Failed: {result.get('error', 'Unknown error')}")
            
            # Small delay between generations
            time.sleep(2)
    
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
        
        self.logger.info("Daily Mash uploader started. Press Ctrl+C to stop.")
        
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
    parser.add_argument('--generate-only', action='store_true', help='Only generate from latest content')
    parser.add_argument('--max-items', type=int, default=3, help='Max items to generate (default: 3)')
    
    args = parser.parse_args()
    
    uploader = DailyMashUploader()
    
    if args.generate_only:
        content_items = uploader.scraper.get_content_for_generation(limit=args.max_items)
        if content_items:
            uploader.generate_creative_stories(content_items, args.max_items)
        else:
            print("No content available for generation")
    elif args.run_once:
        uploader.run_daily_upload()
    else:
        uploader.run_scheduler()


if __name__ == "__main__":
    main()