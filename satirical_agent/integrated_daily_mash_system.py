#!/usr/bin/env python3
"""
Integrated Daily Mash System - Connects satirical content to video generation
"""

import os
import sys
import json
import requests
import feedparser
from bs4 import BeautifulSoup
import html
from datetime import datetime, timedelta
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path
import google.generativeai as genai

class IntegratedDailyMashSystem:
    """
    Main integration class that connects Daily Mash scraping to video generation
    """
    
    def __init__(self, gemini_api_key: str = None):
        self.setup_logging()
        
        # Configure Gemini
        self.gemini_api_key = gemini_api_key or "AIzaSyAk_L6R68hAXep7rYhQbBE87S5wIfoF76o"
        genai.configure(api_key=self.gemini_api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Daily Mash configuration
        self.feed_url = "https://www.thedailymash.co.uk/feed"
        
        # Data directories
        self.content_dir = Path("satirical_content")
        self.generated_dir = Path("generated_satirical_videos")
        self.content_dir.mkdir(exist_ok=True)
        self.generated_dir.mkdir(exist_ok=True)
        
    def setup_logging(self):
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
    
    def fetch_daily_mash_content(self, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Fetch and parse content from The Daily Mash
        """
        self.logger.info("Fetching content from The Daily Mash...")
        
        try:
            # Increase timeout and add retry logic
            response = requests.get(
                self.feed_url, 
                timeout=30,  # Increased from 15 to 30 seconds
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
            response.raise_for_status()
            
            feed = feedparser.parse(response.content)
            content_items = []
            
            for entry in feed.entries[:limit]:
                title = entry.get('title', '').strip()
                if not title:
                    continue
                
                # Extract full content
                full_content = self._extract_full_content(entry)
                if not full_content or len(full_content) < 100:
                    continue
                
                content_item = {
                    'title': html.unescape(title),
                    'link': entry.get('link', ''),
                    'published': entry.get('published', ''),
                    'full_content': full_content,
                    'word_count': len(full_content.split()),
                    'category': self._extract_category(entry.get('link', '')),
                    'humor_type': self._detect_humor_type(title, full_content),
                    'scraped_at': datetime.now().isoformat(),
                    'video_ready': True  # Mark as ready for video generation
                }
                
                content_items.append(content_item)
            
            self.logger.info(f"Successfully fetched {len(content_items)} satirical articles")
            return content_items
            
        except Exception as e:
            self.logger.error(f"Failed to fetch Daily Mash content: {e}")
            return []
    
    def _extract_full_content(self, entry) -> str:
        """Extract full article content from RSS entry"""
        full_content = ''
        
        # Try content blocks first
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
            # Clean HTML and format
            soup = BeautifulSoup(full_content, 'html.parser')
            clean_text = soup.get_text()
            clean_text = html.unescape(clean_text)
            
            # Format into paragraphs
            paragraphs = [p.strip() for p in clean_text.split('\n') if p.strip()]
            return '\n\n'.join(paragraphs)
        
        return ''
    
    def _extract_category(self, link: str) -> str:
        """Extract category from URL"""
        if '/politics/' in link:
            return 'politics'
        elif '/society/' in link:
            return 'society'
        elif '/celebrity/' in link:
            return 'celebrity'
        elif '/arts-entertainment/' in link:
            return 'entertainment'
        elif '/sport/' in link:
            return 'sport'
        else:
            return 'general'
    
    def _detect_humor_type(self, title: str, content: str) -> str:
        """Detect humor type for better script generation"""
        text = (title + ' ' + content).lower()
        
        if any(word in text for word in ['research', 'study', 'institute', 'professor']):
            return 'absurdist'
        elif any(word in text for word in ['party', 'social', 'british', 'middle class']):
            return 'social_satire'
        elif any(word in text for word in ['minister', 'government', 'political']):
            return 'political_satire'
        elif any(word in text for word in ['celebrity', 'famous', 'star']):
            return 'celebrity_satire'
        else:
            return 'everyday_life'
    
    def generate_enhanced_video_script(self, source_content: Dict[str, Any], 
                                     num_segments: int = 4, 
                                     duration_per_segment: float = 5.0) -> Dict[str, Any]:
        """
        Generate enhanced video script using satirical source content
        """
        self.logger.info(f"Generating enhanced script for: {source_content['title']}")
        
        try:
            # Create rich, contextual prompt
            prompt = self._build_enhanced_prompt(source_content, num_segments, duration_per_segment)
            
            # Generate with Gemini
            response = self.model.generate_content(prompt)
            
            # Parse and format response
            script_data = self._parse_gemini_response(response.text, source_content, num_segments, duration_per_segment)
            
            return script_data
            
        except Exception as e:
            self.logger.error(f"Enhanced script generation failed: {e}")
            return self._generate_satirical_fallback(source_content, num_segments, duration_per_segment)
    
    def _build_enhanced_prompt(self, source_content: Dict[str, Any], num_segments: int, duration_per_segment: float) -> str:
        """Build rich, contextual prompt for Gemini"""
        
        title = source_content['title']
        content = source_content['full_content']
        humor_type = source_content['humor_type']
        category = source_content['category']
        
        # Humor-specific guidance
        humor_guidance = {
            'absurdist': "Create absurd, pseudo-scientific observations with ridiculous 'research findings' and exaggerated logic.",
            'social_satire': "Focus on social contradictions, cultural observations, and modern British life absurdities.",
            'political_satire': "Highlight political absurdities and governance quirks while keeping it accessible and funny.",
            'celebrity_satire': "Explore fame culture, public personas, and entertainment industry humor.",
            'everyday_life': "Focus on relatable daily situations with humorous observations everyone can identify with."
        }
        
        guidance = humor_guidance.get(humor_type, humor_guidance['everyday_life'])
        
        prompt = f"""
Create an engaging video script based on this satirical content from The Daily Mash.

ORIGINAL SATIRICAL ARTICLE:
Title: "{title}"
Category: {category}
Humor Type: {humor_type}
Content: {content[:800]}...

SCRIPT REQUIREMENTS:
- Create exactly {num_segments} segments
- Each segment should be {duration_per_segment} seconds of speaking time
- Target: 20-30 words per segment for natural speech
- Style: Satirical and witty like the original
- Make it video-friendly and engaging

HUMOR GUIDANCE: {guidance}

FORMAT REQUIREMENTS:
Respond with a JSON object containing:
{{
    "video_title": "Catchy video title based on the satirical content",
    "segments": [
        {{
            "text": "Segment text here - witty and satirical",
            "visual_suggestion": "What should be shown visually",
            "tone": "delivery tone (e.g. deadpan, surprised, etc.)"
        }}
    ],
    "overall_theme": "Main satirical theme of the video",
    "target_audience": "Who this content appeals to"
}}

EXAMPLES OF GOOD SATIRICAL VIDEO SEGMENTS:
- "Research has proven that arriving early to parties makes you 47% more likely to be avoided."
- "Scientists have discovered the exact moment when small talk becomes unbearably awkward."
- "New studies show that checking your phone reduces boredom by 3% but increases social anxiety by 94%."

Create content that captures the satirical spirit while being perfect for video format.
"""
        
        return prompt.strip()
    
    def _parse_gemini_response(self, response_text: str, source_content: Dict[str, Any], 
                             num_segments: int, duration_per_segment: float) -> Dict[str, Any]:
        """Parse and format Gemini's JSON response"""
        
        try:
            # Extract JSON from response
            response_text = response_text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            script_data = json.loads(response_text)
            
            # Validate structure
            if 'segments' not in script_data or not isinstance(script_data['segments'], list):
                raise ValueError("Invalid response structure")
            
            # Process segments with timing
            processed_segments = self._add_timing_to_segments(
                script_data['segments'], duration_per_segment
            )
            
            # Create final script structure
            final_script = {
                "Text": " ".join([seg["sentence"] for seg in processed_segments]),
                "title": script_data.get("video_title", f"Satirical Take: {source_content['title']}"),
                "sentences": processed_segments,
                "source_content": {
                    "original_title": source_content['title'],
                    "original_link": source_content['link'],
                    "humor_type": source_content['humor_type'],
                    "category": source_content['category']
                },
                "style": "satirical",
                "total_duration": len(processed_segments) * duration_per_segment,
                "segment_count": len(processed_segments),
                "overall_theme": script_data.get("overall_theme", "Satirical commentary"),
                "target_audience": script_data.get("target_audience", "General audience"),
                "generated_at": datetime.now().isoformat(),
                "generated_by": "gemini_enhanced_satirical"
            }
            
            return final_script
            
        except Exception as e:
            self.logger.warning(f"Failed to parse Gemini response: {e}")
            return self._generate_satirical_fallback(source_content, num_segments, duration_per_segment)
    
    def _add_timing_to_segments(self, segments: List[Dict], duration_per_segment: float) -> List[Dict]:
        """Add timing information to segments"""
        
        azure_time_unit = 10000000  # For compatibility
        processed_segments = []
        current_time = 0
        
        for i, segment in enumerate(segments):
            text = segment['text']
            estimated_duration = int(duration_per_segment * azure_time_unit)
            
            processed_segment = {
                "sentence": text,
                "start_time": current_time,
                "end_time": current_time + estimated_duration,
                "duration": estimated_duration,
                "word_count": len(text.split()),
                "char_count": len(text),
                "visual_suggestion": segment.get('visual_suggestion', 'General satirical imagery'),
                "tone": segment.get('tone', 'witty'),
                "segment_number": i + 1
            }
            
            processed_segments.append(processed_segment)
            current_time += estimated_duration
        
        return processed_segments
    
    def _generate_satirical_fallback(self, source_content: Dict[str, Any], 
                                   num_segments: int, duration_per_segment: float) -> Dict[str, Any]:
        """Generate fallback satirical script"""
        
        title = source_content['title']
        humor_type = source_content['humor_type']
        
        # Create humor-specific templates
        templates = {
            'absurdist': [
                f"Research has finally proven what we all suspected about {title.lower()}.",
                f"Scientists have discovered the shocking truth behind everyday situations.",
                f"New studies reveal the mathematical probability of social awkwardness.",
                f"This groundbreaking research explains why life is so predictably absurd."
            ],
            'social_satire': [
                f"Modern society has created a new problem: {title.lower()}.",
                f"This perfectly illustrates everything wrong with contemporary life.",
                f"It's a classic example of how we've engineered our own social disasters.",
                f"Welcome to the 21st century, where this behavior is completely normal."
            ],
            'political_satire': [
                f"Politicians have found a way to make {title.lower()} even worse.",
                f"This situation reveals the true absurdity of modern governance.",
                f"It's political theater at its most predictably ridiculous.",
                f"Democracy in action: creating problems that didn't exist before."
            ],
            'celebrity_satire': [
                f"Celebrities have turned {title.lower()} into a lifestyle brand.",
                f"Fame culture has made this behavior socially acceptable.",
                f"This proves that money can't buy self-awareness.",
                f"In Hollywood, this would be considered perfectly normal behavior."
            ],
            'everyday_life': [
                f"We've all experienced the truth about {title.lower()}.",
                f"It's one of those universal experiences nobody talks about.",
                f"This perfectly captures the awkwardness of modern life.",
                f"Everyone recognizes this situation but pretends it doesn't happen."
            ]
        }
        
        sentences = templates.get(humor_type, templates['everyday_life'])[:num_segments]
        
        # Add timing
        processed_segments = self._add_timing_to_segments(
            [{"text": text} for text in sentences], 
            duration_per_segment
        )
        
        return {
            "Text": " ".join(sentences),
            "title": f"Satirical Take: {title}",
            "sentences": processed_segments,
            "source_content": {
                "original_title": title,
                "humor_type": humor_type,
                "category": source_content['category']
            },
            "style": "satirical_fallback",
            "total_duration": len(sentences) * duration_per_segment,
            "segment_count": len(sentences),
            "generated_at": datetime.now().isoformat(),
            "generated_by": "satirical_fallback_template"
        }
    
    def create_video_generation_request(self, script_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a request compatible with the existing Flask video generation system
        """
        
        # Extract source content info
        source_content = script_data.get('source_content', {})
        
        video_request = {
            "topic": script_data['title'],
            "style": "satirical",
            "num_segments": script_data['segment_count'],
            "duration_per_segment": script_data['total_duration'] / script_data['segment_count'],
            
            # Enhanced fields for satirical content
            "source_type": "daily_mash",
            "humor_type": source_content.get('humor_type', 'general'),
            "original_title": source_content.get('original_title', ''),
            "original_link": source_content.get('original_link', ''),
            "satirical_context": True,
            
            # Video generation parameters
            "width": 1024,
            "height": 576,
            "fps": 24,
            "image_model": "flux",
            
            # Pre-generated script data
            "pregenerated_script": script_data
        }
        
        return video_request
    
    def process_daily_content_to_videos(self, max_videos: int = 3) -> List[Dict[str, Any]]:
        """
        Complete pipeline: fetch content → generate scripts → prepare for video generation
        """
        self.logger.info(f"Processing Daily Mash content into {max_videos} video scripts...")
        
        try:
            # 1. Fetch satirical content with retry
            content_items = []
            max_retries = 2
            
            for attempt in range(max_retries + 1):
                try:
                    content_items = self.fetch_daily_mash_content(limit=max_videos * 2)
                    if content_items:
                        break
                    else:
                        self.logger.warning(f"Attempt {attempt + 1}: No content fetched")
                except Exception as fetch_error:
                    self.logger.warning(f"Attempt {attempt + 1} failed: {fetch_error}")
                    if attempt < max_retries:
                        import time
                        time.sleep(3)  # Wait 3 seconds before retry
                        continue
                    else:
                        raise fetch_error
            
            if not content_items:
                self.logger.warning("No content fetched after all retries")
                return []
            
            # 2. Select best content for videos
            selected_content = self._select_best_content_for_videos(content_items, max_videos)
            
            # 3. Generate enhanced scripts
            video_requests = []
            
            for content in selected_content:
                self.logger.info(f"Processing: {content['title']}")
                
                # Generate script
                script_data = self.generate_enhanced_video_script(content)
                
                # Create video generation request
                video_request = self.create_video_generation_request(script_data)
                
                video_requests.append({
                    'request': video_request,
                    'script_data': script_data,
                    'source_content': content
                })
            
            self.logger.info(f"Successfully created {len(video_requests)} video generation requests")
            return video_requests
            
        except Exception as e:
            self.logger.error(f"Failed to process Daily Mash content: {e}")
            return []
    
    def _select_best_content_for_videos(self, content_items: List[Dict[str, Any]], 
                                      max_videos: int) -> List[Dict[str, Any]]:
        """Select the best content for video generation"""
        
        # Score content based on various factors
        for item in content_items:
            score = 0
            
            # Prefer certain humor types
            humor_type = item['humor_type']
            if humor_type in ['absurdist', 'social_satire', 'everyday_life']:
                score += 3
            elif humor_type in ['political_satire', 'celebrity_satire']:
                score += 2
            else:
                score += 1
            
            # Prefer reasonable length content
            word_count = item['word_count']
            if 100 <= word_count <= 400:
                score += 2
            elif word_count > 400:
                score += 1
            
            # Prefer recent content
            try:
                pub_date = datetime.strptime(item['published'], '%a, %d %b %Y %H:%M:%S %z')
                age_hours = (datetime.now(pub_date.tzinfo) - pub_date).total_seconds() / 3600
                if age_hours < 24:
                    score += 2
                elif age_hours < 72:
                    score += 1
            except:
                pass
            
            item['video_score'] = score
        
        # Sort by score and return top items
        content_items.sort(key=lambda x: x['video_score'], reverse=True)
        return content_items[:max_videos]


def integrate_with_flask_system():
    """
    Function to integrate with the existing Flask system
    Call this from flask_app.py to get satirical content
    """
    
    integrated_system = IntegratedDailyMashSystem()
    
    # Process content and return video requests
    video_requests = integrated_system.process_daily_content_to_videos(max_videos=5)
    
    return video_requests


if __name__ == "__main__":
    # Test the integrated system
    system = IntegratedDailyMashSystem()
    
    print("Testing Daily Mash Integration...")
    
    # Test content fetching
    content = system.fetch_daily_mash_content(limit=2)
    
    if content:
        print(f"✓ Fetched {len(content)} articles")
        
        # Test script generation
        first_article = content[0]
        print(f"\nTesting script generation for: {first_article['title']}")
        
        script = system.generate_enhanced_video_script(first_article)
        
        print(f"✓ Generated script: {script['title']}")
        print(f"  Segments: {script['segment_count']}")
        print(f"  Duration: {script['total_duration']:.1f}s")
        
        # Test video request creation
        video_request = system.create_video_generation_request(script)
        print(f"✓ Created video request for Flask system")
        
    else:
        print("✗ No content fetched")