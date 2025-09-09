"""
Caption and Metadata Generator
Generates platform-specific captions, descriptions, and metadata during video creation
"""

import os
import json
import time
from typing import Dict, Any, List, Optional
from datetime import datetime

class CaptionMetadataGenerator:
    """
    Generates captions and metadata for different platforms during video creation
    """
    
    def __init__(self):
        self.platform_configs = {
            "youtube": {
                "max_title_length": 100,
                "max_description_length": 5000,
                "recommended_tags": 10,
                "hashtag_limit": None
            },
            "instagram": {
                "max_title_length": 2200,  # Caption length
                "max_description_length": 2200,
                "recommended_tags": None,
                "hashtag_limit": 30
            },
            "tiktok": {
                "max_title_length": 150,
                "max_description_length": 150,
                "recommended_tags": None,
                "hashtag_limit": 100
            }
        }
        
        print("[CAPTIONS] Initialized caption and metadata generator")
    
    def generate_video_metadata(self, story_info: Dict[str, Any], 
                               domain: str, 
                               platforms: List[str] = ["youtube", "instagram"]) -> Dict[str, Any]:
        """Generate comprehensive metadata for video during creation"""
        
        try:
            topic = story_info.get("title", "AI Generated Story")
            summary = story_info.get("summary", "")
            characters = story_info.get("characters", [])
            segments = story_info.get("segments", [])
            
            # Generate base content
            base_metadata = self._generate_base_metadata(topic, summary, domain, characters)
            
            # Generate platform-specific content
            platform_metadata = {}
            
            for platform in platforms:
                platform_metadata[platform] = self._generate_platform_specific_metadata(
                    base_metadata, platform, domain
                )
            
            # Generate captions/subtitles for accessibility
            captions = self._generate_captions_from_segments(segments)
            
            # Generate SEO tags and keywords
            seo_data = self._generate_seo_data(topic, domain, summary)
            
            metadata = {
                "generated_at": datetime.now().isoformat(),
                "topic": topic,
                "domain": domain,
                "base_metadata": base_metadata,
                "platform_metadata": platform_metadata,
                "captions": captions,
                "seo_data": seo_data,
                "story_info": story_info
            }
            
            return metadata
            
        except Exception as e:
            print(f"[CAPTIONS] Error generating metadata: {e}")
            return self._generate_fallback_metadata(story_info, domain)
    
    def _generate_base_metadata(self, topic: str, summary: str, domain: str, characters: List[str]) -> Dict[str, Any]:
        """Generate base metadata that can be adapted for each platform"""
        
        # Create engaging titles
        title_variations = self._generate_title_variations(topic, domain)
        
        # Create descriptions
        descriptions = self._generate_descriptions(topic, summary, domain, characters)
        
        # Generate tags and keywords
        tags = self._generate_tags(topic, domain, characters)
        
        return {
            "title_variations": title_variations,
            "descriptions": descriptions,
            "tags": tags,
            "characters": characters,
            "domain": domain,
            "engagement_hooks": self._generate_engagement_hooks(topic, domain)
        }
    
    def _generate_title_variations(self, topic: str, domain: str) -> List[str]:
        """Generate multiple title variations for A/B testing"""
        
        domain_prefixes = {
            "indian_mythology": ["🕉️", "📿", "⚡", "🏛️"],
            "technology": ["🚀", "🤖", "💡", "⚡"],
            "science": ["🔬", "🧪", "⭐", "🌌"],
            "history": ["📜", "🏛️", "⚔️", "👑"],
            "health": ["🌱", "💪", "🧠", "❤️"],
            "business": ["💼", "📈", "💡", "🎯"]
        }
        
        emojis = domain_prefixes.get(domain, ["✨", "🎬", "📺"])
        
        variations = [
            f"{topic}",
            f"{emojis[0]} {topic}",
            f"The TRUTH About {topic}",
            f"Why {topic} Will BLOW Your Mind!",
            f"SHOCKING: {topic} Revealed",
            f"{topic} - You Won't Believe This!",
            f"The Secret of {topic}",
            f"{emojis[1]} {topic} Explained"
        ]
        
        return variations[:5]  # Return top 5 variations
    
    def _generate_descriptions(self, topic: str, summary: str, domain: str, characters: List[str]) -> Dict[str, str]:
        """Generate different description styles"""
        
        character_text = f"\n\n🎭 Featured: {', '.join(characters)}" if characters else ""
        
        descriptions = {
            "engaging": f"🎬 Dive deep into the fascinating world of {topic}!\n\n{summary}\n\nThis AI-generated video takes you on an incredible journey through {domain}, revealing insights you've never heard before!{character_text}\n\n💫 What you'll discover:\n✨ Hidden truths and amazing facts\n🔍 Expert insights and analysis\n🎯 Everything you need to know\n\nDon't miss this epic story! Like and subscribe for more amazing content! 🚀",
            
            "educational": f"📚 Educational Deep Dive: {topic}\n\n{summary}\n\nIn this comprehensive exploration of {domain}, we uncover the essential knowledge about {topic}. Perfect for students, enthusiasts, and anyone curious about this fascinating subject.{character_text}\n\n📖 Topics covered:\n• Historical context and background\n• Key concepts and principles\n• Modern relevance and applications\n\n🎓 Learn something new today!",
            
            "storytelling": f"🌟 An Epic Tale: {topic}\n\n{summary}\n\nJoin us as we unfold this incredible story from the world of {domain}. Every detail has been carefully crafted to bring you an immersive experience that will captivate and inspire.{character_text}\n\n✨ Get ready for:\n🎭 Compelling characters and narratives\n🏛️ Rich cultural and historical context\n💫 Unforgettable moments and revelations\n\n#AIGenerated #Storytelling",
            
            "casual": f"Hey everyone! 👋\n\nToday we're talking about {topic} - and trust me, this is going to be interesting!\n\n{summary}{character_text}\n\nI've been diving deep into {domain} lately, and there's so much cool stuff to share. Whether you're new to this topic or already know a bit, I think you'll find something valuable here.\n\nLet me know what you think in the comments! And if you enjoyed this, don't forget to hit that like button! 🔥"
        }
        
        return descriptions
    
    def _generate_tags(self, topic: str, domain: str, characters: List[str]) -> List[str]:
        """Generate comprehensive tags for SEO and discovery"""
        
        # Base tags
        base_tags = ["AI generated", "educational", "story", "learning"]
        
        # Domain-specific tags
        domain_tags = {
            "indian_mythology": ["mythology", "hinduism", "ancient india", "vedic", "puranas", "epic", "spiritual", "culture"],
            "technology": ["tech", "innovation", "future", "AI", "digital", "startup", "programming", "gadgets"],
            "science": ["science", "research", "discovery", "education", "facts", "physics", "biology", "chemistry"],
            "history": ["history", "ancient", "civilization", "historical", "past", "timeline", "documentary"],
            "health": ["health", "wellness", "fitness", "nutrition", "medical", "lifestyle", "tips"],
            "business": ["business", "entrepreneur", "success", "marketing", "finance", "strategy", "leadership"]
        }
        
        # Topic-specific tags (extract keywords from topic)
        topic_words = [word.lower() for word in topic.split() if len(word) > 3]
        
        # Character tags
        character_tags = [char.lower().replace(" ", "") for char in characters]
        
        # Combine all tags
        all_tags = (base_tags + 
                   domain_tags.get(domain, []) + 
                   topic_words + 
                   character_tags + 
                   [domain])
        
        # Remove duplicates and return
        return list(set(all_tags))[:15]  # Limit to 15 tags
    
    def _generate_engagement_hooks(self, topic: str, domain: str) -> List[str]:
        """Generate engagement hooks for social media"""
        
        hooks = [
            f"Did you know about {topic}? 🤔",
            f"This {domain} fact will blow your mind! 🤯",
            f"Everyone should know about {topic}! 📢",
            f"The story of {topic} is incredible! ✨",
            f"You won't believe what I learned about {topic}! 😱"
        ]
        
        return hooks
    
    def _generate_platform_specific_metadata(self, base_metadata: Dict[str, Any], 
                                           platform: str, domain: str) -> Dict[str, Any]:
        """Generate platform-specific optimized metadata"""
        
        config = self.platform_configs.get(platform, {})
        
        if platform == "youtube":
            return self._generate_youtube_metadata(base_metadata, config)
        elif platform == "instagram":
            return self._generate_instagram_metadata(base_metadata, config)
        elif platform == "tiktok":
            return self._generate_tiktok_metadata(base_metadata, config)
        else:
            return self._generate_generic_metadata(base_metadata, config)
    
    def _generate_youtube_metadata(self, base_metadata: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate YouTube-optimized metadata"""
        
        # Choose best title for YouTube
        title = base_metadata["title_variations"][0]
        if len(title) > config["max_title_length"]:
            title = title[:config["max_title_length"]-3] + "..."
        
        # Use engaging description
        description = base_metadata["descriptions"]["engaging"]
        if len(description) > config["max_description_length"]:
            description = description[:config["max_description_length"]-3] + "..."
        
        # Optimize tags for YouTube
        tags = base_metadata["tags"][:config["recommended_tags"]]
        
        return {
            "title": title,
            "description": description,
            "tags": tags,
            "privacy_status": "private",  # Default
            "category": "22",  # People & Blogs
            "thumbnail_keywords": self._generate_thumbnail_keywords(base_metadata),
            "end_screen_elements": ["subscribe", "suggested_videos"],
            "optimization_tips": [
                "Add custom thumbnail",
                "Create end screen with subscribe button",
                "Add chapters in description",
                "Pin a comment asking for engagement"
            ]
        }
    
    def _generate_instagram_metadata(self, base_metadata: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Instagram-optimized metadata"""
        
        # Instagram uses caption as title
        caption_parts = []
        
        # Add hook
        caption_parts.append(base_metadata["engagement_hooks"][0])
        caption_parts.append("")
        
        # Add description (shortened)
        short_desc = base_metadata["descriptions"]["casual"][:800] + "..." if len(base_metadata["descriptions"]["casual"]) > 800 else base_metadata["descriptions"]["casual"]
        caption_parts.append(short_desc)
        caption_parts.append("")
        
        # Add hashtags (limit to 30)
        hashtags = ["#" + tag.replace(" ", "").lower() for tag in base_metadata["tags"][:25]]
        hashtags.extend(["#AI", "#educational", "#story", "#viral", "#fyp"])
        caption_parts.append(" ".join(hashtags[:30]))
        
        caption = "\n".join(caption_parts)
        
        return {
            "caption": caption[:config["max_title_length"]],
            "hashtags": hashtags[:30],
            "story_content": self._generate_instagram_story_content(base_metadata),
            "reel_keywords": base_metadata["tags"][:10],
            "engagement_strategies": [
                "Ask question in caption",
                "Use trending audio",
                "Add text overlay with key points",
                "Create carousel post with highlights"
            ]
        }
    
    def _generate_tiktok_metadata(self, base_metadata: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate TikTok-optimized metadata"""
        
        # TikTok caption (short and engaging)
        hook = base_metadata["engagement_hooks"][0]
        short_desc = base_metadata["descriptions"]["casual"][:100]
        
        hashtags = ["#" + tag.replace(" ", "").lower() for tag in base_metadata["tags"][:10]]
        hashtags.extend(["#fyp", "#viral", "#AI", "#story", "#educational"])
        
        caption = f"{hook}\n\n{short_desc}...\n\n{' '.join(hashtags[:15])}"
        
        return {
            "caption": caption[:config["max_title_length"]],
            "hashtags": hashtags[:15],
            "trending_sounds": ["original_audio", "trending_bg_music"],
            "video_effects": ["text_overlay", "transitions", "zoom_effects"],
            "optimization_tips": [
                "Hook viewers in first 3 seconds",
                "Use trending hashtags",
                "Add captions/text overlay",
                "Keep it under 60 seconds"
            ]
        }
    
    def _generate_generic_metadata(self, base_metadata: Dict[str, Any], config: Dict[str, Any]) -> Dict[str, Any]:
        """Generate generic metadata for other platforms"""
        
        return {
            "title": base_metadata["title_variations"][0],
            "description": base_metadata["descriptions"]["educational"],
            "tags": base_metadata["tags"][:10],
            "hashtags": ["#" + tag.replace(" ", "").lower() for tag in base_metadata["tags"][:10]]
        }
    
    def _generate_captions_from_segments(self, segments: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate captions/subtitles from video segments"""
        
        try:
            srt_captions = []
            vtt_captions = ["WEBVTT", ""]
            
            for i, segment in enumerate(segments):
                text = segment.get("text", f"Segment {i+1}")
                start_time = segment.get("start_time", i * 5)  # Default 5 sec per segment
                duration = segment.get("duration", 5)
                end_time = start_time + duration
                
                # SRT format
                srt_captions.extend([
                    str(i + 1),
                    f"{self._seconds_to_srt_time(start_time)} --> {self._seconds_to_srt_time(end_time)}",
                    text,
                    ""
                ])
                
                # VTT format
                vtt_captions.extend([
                    f"{self._seconds_to_vtt_time(start_time)} --> {self._seconds_to_vtt_time(end_time)}",
                    text,
                    ""
                ])
            
            return {
                "srt_format": "\n".join(srt_captions),
                "vtt_format": "\n".join(vtt_captions),
                "segments_count": len(segments),
                "total_duration": sum(s.get("duration", 5) for s in segments)
            }
            
        except Exception as e:
            print(f"[CAPTIONS] Error generating captions: {e}")
            return {"srt_format": "", "vtt_format": "", "segments_count": 0}
    
    def _seconds_to_srt_time(self, seconds: float) -> str:
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _seconds_to_vtt_time(self, seconds: float) -> str:
        """Convert seconds to VTT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d}.{millisecs:03d}"
    
    def _generate_seo_data(self, topic: str, domain: str, summary: str) -> Dict[str, Any]:
        """Generate SEO-optimized data"""
        
        keywords = []
        
        # Extract keywords from topic
        topic_keywords = [word.lower() for word in topic.split() if len(word) > 3]
        keywords.extend(topic_keywords)
        
        # Domain keywords
        domain_keywords = {
            "indian_mythology": ["mythology", "hinduism", "vedic", "ancient india"],
            "technology": ["tech", "innovation", "artificial intelligence", "digital"],
            "science": ["science", "research", "discovery", "educational"],
            "history": ["history", "historical", "ancient", "civilization"],
            "health": ["health", "wellness", "fitness", "medical"],
            "business": ["business", "entrepreneurship", "success", "leadership"]
        }
        
        keywords.extend(domain_keywords.get(domain, []))
        
        return {
            "primary_keywords": list(set(keywords))[:10],
            "search_terms": [
                f"{topic} explained",
                f"learn about {topic}",
                f"{domain} stories",
                f"{topic} documentary"
            ],
            "meta_description": f"Discover the fascinating story of {topic} in this AI-generated educational video about {domain}. {summary[:100]}...",
            "schema_markup": {
                "@type": "VideoObject",
                "name": topic,
                "description": summary[:200],
                "genre": domain,
                "contentRating": "G"
            }
        }
    
    def _generate_thumbnail_keywords(self, base_metadata: Dict[str, Any]) -> List[str]:
        """Generate keywords for thumbnail creation"""
        
        return [
            "high contrast text",
            "emotional expression",
            "bright colors",
            "clear focal point",
            "minimal text overlay",
            base_metadata["domain"] + " themed"
        ]
    
    def _generate_instagram_story_content(self, base_metadata: Dict[str, Any]) -> List[str]:
        """Generate Instagram story content ideas"""
        
        return [
            f"Behind the scenes: Creating {base_metadata['title_variations'][0]}",
            "Poll: Did you know this fact?",
            f"Swipe up to learn more about {base_metadata['domain']}",
            "Quiz: Test your knowledge!",
            "Share if you found this interesting!"
        ]
    
    def _generate_fallback_metadata(self, story_info: Dict[str, Any], domain: str) -> Dict[str, Any]:
        """Generate simple fallback metadata if main generation fails"""
        
        topic = story_info.get("title", "AI Generated Story")
        
        return {
            "generated_at": datetime.now().isoformat(),
            "topic": topic,
            "domain": domain,
            "base_metadata": {
                "title_variations": [topic],
                "descriptions": {"simple": f"An AI-generated story about {topic} in the {domain} domain."},
                "tags": ["AI", "generated", domain, "story"],
                "engagement_hooks": [f"Check out this story about {topic}!"]
            },
            "platform_metadata": {
                "youtube": {
                    "title": topic,
                    "description": f"AI-generated video about {topic}",
                    "tags": ["AI", domain, "story"]
                }
            },
            "captions": {"srt_format": "", "vtt_format": ""},
            "seo_data": {"primary_keywords": [topic, domain, "AI"]}
        }
    
    def save_metadata_to_file(self, metadata: Dict[str, Any], output_dir: str) -> str:
        """Save generated metadata to file"""
        
        try:
            os.makedirs(output_dir, exist_ok=True)
            metadata_file = os.path.join(output_dir, "video_metadata.json")
            
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            # Save captions as separate files
            if metadata.get("captions", {}).get("srt_format"):
                srt_file = os.path.join(output_dir, "captions.srt")
                with open(srt_file, 'w', encoding='utf-8') as f:
                    f.write(metadata["captions"]["srt_format"])
            
            if metadata.get("captions", {}).get("vtt_format"):
                vtt_file = os.path.join(output_dir, "captions.vtt")
                with open(vtt_file, 'w', encoding='utf-8') as f:
                    f.write(metadata["captions"]["vtt_format"])
            
            print(f"[CAPTIONS] Saved metadata to: {metadata_file}")
            return metadata_file
            
        except Exception as e:
            print(f"[CAPTIONS] Error saving metadata: {e}")
            return ""

# Global instance
_caption_generator: Optional[CaptionMetadataGenerator] = None

def get_caption_generator() -> CaptionMetadataGenerator:
    """Get global caption generator instance"""
    global _caption_generator
    
    if _caption_generator is None:
        _caption_generator = CaptionMetadataGenerator()
    
    return _caption_generator

if __name__ == "__main__":
    # Test the caption generator
    generator = CaptionMetadataGenerator()
    
    # Test story info
    test_story = {
        "title": "The Epic Journey of Hanuman",
        "summary": "A fascinating tale of courage, devotion, and supernatural powers in ancient India.",
        "characters": ["Hanuman", "Rama", "Sita"],
        "segments": [
            {"text": "In ancient times, there lived a mighty warrior named Hanuman.", "start_time": 0, "duration": 5},
            {"text": "His devotion to Lord Rama was unmatched in all the worlds.", "start_time": 5, "duration": 5},
            {"text": "With his incredible powers, he helped rescue Sita from Lanka.", "start_time": 10, "duration": 5}
        ]
    }
    
    print("Testing Caption Generator...")
    
    # Generate metadata
    metadata = generator.generate_video_metadata(test_story, "indian_mythology", ["youtube", "instagram"])
    
    print(f"\nGenerated metadata for: {metadata['topic']}")
    print(f"Platforms: {list(metadata['platform_metadata'].keys())}")
    print(f"Title variations: {len(metadata['base_metadata']['title_variations'])}")
    print(f"Captions segments: {metadata['captions']['segments_count']}")
    
    # Show YouTube metadata
    yt_meta = metadata['platform_metadata']['youtube']
    print(f"\nYouTube Title: {yt_meta['title']}")
    print(f"YouTube Tags: {', '.join(yt_meta['tags'][:5])}...")
    
    # Show Instagram metadata
    ig_meta = metadata['platform_metadata']['instagram']
    print(f"\nInstagram Caption: {ig_meta['caption'][:100]}...")
    print(f"Instagram Hashtags: {len(ig_meta['hashtags'])} hashtags")