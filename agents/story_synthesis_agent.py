"""
Story Synthesis Agent
Transforms research headlines into creative, engaging video narratives using AI
Adds creativity, context, and storytelling elements to raw news data
"""

import os
import json
import random
from datetime import datetime
from typing import List, Dict, Any, Optional
import google.generativeai as genai

# Configure Gemini
GEMINI_API_KEY = "AIzaSyB2VLzqQbnSy0KloCMlk4IRXD6L9Qwgc8Y"
genai.configure(api_key=GEMINI_API_KEY)

class StoryStyle:
    """Define different storytelling styles and approaches"""
    
    DOCUMENTARY = {
        'name': 'documentary',
        'tone': 'authoritative and informative',
        'structure': 'chronological with expert insights',
        'language': 'clear, factual, engaging',
        'creativity_level': 'moderate',
        'human_interest': 'medium'
    }
    
    NARRATIVE = {
        'name': 'narrative', 
        'tone': 'engaging and story-driven',
        'structure': 'beginning, middle, end with character focus',
        'language': 'vivid, descriptive, compelling',
        'creativity_level': 'high',
        'human_interest': 'high'
    }
    
    ANALYTICAL = {
        'name': 'analytical',
        'tone': 'thoughtful and investigative', 
        'structure': 'problem-analysis-implications',
        'language': 'precise, insightful, nuanced',
        'creativity_level': 'moderate',
        'human_interest': 'low'
    }
    
    CONVERSATIONAL = {
        'name': 'conversational',
        'tone': 'friendly and accessible',
        'structure': 'question-answer flow',
        'language': 'casual, relatable, clear',
        'creativity_level': 'high', 
        'human_interest': 'high'
    }

class StorySynthesisAgent:
    """
    Agent that creates engaging stories from research headlines
    Uses AI to add creativity, context, and narrative structure
    """
    
    def __init__(self, model_name: str = "gemini-1.5-flash"):
        """
        Initialize the story synthesis agent
        
        Args:
            model_name: Gemini model to use for story generation
        """
        self.model = genai.GenerativeModel(model_name)
        self.story_styles = {
            'documentary': StoryStyle.DOCUMENTARY,
            'narrative': StoryStyle.NARRATIVE, 
            'analytical': StoryStyle.ANALYTICAL,
            'conversational': StoryStyle.CONVERSATIONAL
        }
        
        print(f"[STORY AGENT] Initialized with {model_name}")
    
    def analyze_research_context(self, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze research data to extract key themes, trends, and story elements
        """
        headlines = research_data.get('key_headlines', [])
        items = research_data.get('items', [])
        
        if not headlines:
            return {'themes': [], 'key_players': [], 'timeline': [], 'implications': []}
        
        # Extract themes using dynamic analysis
        themes = []
        timeline_events = []
        
        # Analyze headlines for themes
        all_text = ' '.join(headlines + [item.get('title', '') for item in items]).lower()
        
        # Use AI to extract themes instead of hard-coding
        themes = self._extract_themes_from_text(all_text)
        
        # Extract key players using dynamic entity recognition
        key_players = self._extract_entities_from_text(all_text)
        
        # Timeline from dates
        for item in items:
            if item.get('published_date'):
                timeline_events.append({
                    'date': item['published_date'],
                    'event': item['title']
                })
        
        timeline_events.sort(key=lambda x: x['date'])
        
        return {
            'themes': list(set(themes)),
            'key_players': list(set(key_players)),
            'timeline': timeline_events[-3:],  # Last 3 events
            'implications': self._extract_implications_from_text(all_text),
            'sentiment': self._analyze_sentiment_from_text(all_text),
            'complexity_level': len(themes) + len(key_players)
        }
    
    def _extract_themes_from_text(self, text: str) -> List[str]:
        """Use AI to extract themes from text instead of hard-coded keywords"""
        try:
            prompt = f"""
Analyze this text and extract the main themes/topics. Return only the theme names, one per line.
Focus on the most important themes that would be relevant for creating a video story.

Text: {text[:1000]}...

Return just the theme names, each on a new line. Maximum 5 themes.
"""
            
            response = self.model.generate_content(prompt)
            themes = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            return themes[:5]  # Limit to 5 themes
            
        except Exception as e:
            print(f"[STORY AGENT] AI theme extraction failed: {e}, using fallback")
            # Simple fallback
            return ['general_topic']
    
    def _extract_entities_from_text(self, text: str) -> List[str]:
        """Use AI to extract key entities/players from text"""
        try:
            prompt = f"""
Extract the key entities, people, organizations, and countries mentioned in this text.
Return only the entity names, one per line.

Text: {text[:1000]}...

Return just the entity names (people, countries, organizations), each on a new line. Maximum 8 entities.
"""
            
            response = self.model.generate_content(prompt)
            entities = [line.strip().lower() for line in response.text.strip().split('\n') if line.strip()]
            return entities[:8]  # Limit to 8 entities
            
        except Exception as e:
            print(f"[STORY AGENT] AI entity extraction failed: {e}, using fallback")
            # Simple fallback
            return ['unknown_entity']
    
    def _extract_implications_from_text(self, text: str) -> List[str]:
        """Use AI to extract potential implications"""
        try:
            prompt = f"""
Based on this text, what are the potential implications or consequences?
Focus on economic, political, social, or global implications.

Text: {text[:1000]}...

Return just the implication categories, each on a new line. Maximum 4 implications.
Examples: economic_impact, diplomatic_consequences, global_effects, consumer_impact
"""
            
            response = self.model.generate_content(prompt)
            implications = [line.strip() for line in response.text.strip().split('\n') if line.strip()]
            return implications[:4]  # Limit to 4 implications
            
        except Exception as e:
            print(f"[STORY AGENT] AI implications extraction failed: {e}, using fallback")
            return ['general_impact']
    
    def _analyze_sentiment_from_text(self, text: str) -> str:
        """Use AI to analyze sentiment"""
        try:
            prompt = f"""
Analyze the overall sentiment/tone of this text. 
Respond with exactly one word: positive, negative, neutral, tense, optimistic, or concerned

Text: {text[:500]}...
"""
            
            response = self.model.generate_content(prompt)
            sentiment = response.text.strip().lower()
            
            # Validate response
            valid_sentiments = ['positive', 'negative', 'neutral', 'tense', 'optimistic', 'concerned']
            if sentiment in valid_sentiments:
                return sentiment
            else:
                return 'neutral'
                
        except Exception as e:
            print(f"[STORY AGENT] AI sentiment analysis failed: {e}, using fallback")
            return 'neutral'
    
    def create_story_outline(self, 
                           context: Dict[str, Any], 
                           research_data: Dict[str, Any],
                           style: str = 'narrative',
                           target_duration: int = 60) -> Dict[str, Any]:
        """
        Create a story outline based on research context and desired style
        """
        story_style = self.story_styles.get(style, StoryStyle.NARRATIVE)
        
        # Calculate segments based on duration
        num_segments = max(3, min(8, target_duration // 10))
        
        try:
            prompt = f"""
Create a compelling story outline for a {target_duration}-second video about: "{research_data['query']}"

RESEARCH CONTEXT:
- Key Headlines: {research_data['key_headlines'][:3]}
- Main Themes: {context['themes']}
- Key Players: {context['key_players']}
- Sentiment: {context['sentiment']}
- Recent Timeline: {[event['event'] for event in context['timeline']]}

STYLE REQUIREMENTS:
- Style: {story_style['name']}
- Tone: {story_style['tone']}
- Structure: {story_style['structure']}
- Language: {story_style['language']}
- Creativity Level: {story_style['creativity_level']}

CREATIVE REQUIREMENTS:
1. Add compelling narrative hooks and transitions
2. Include human interest angles where possible
3. Create curiosity gaps to maintain engagement
4. Use storytelling techniques (setup, conflict, resolution)
5. Add creative metaphors or analogies to explain complex concepts
6. Include "why this matters" elements for the audience

Create a {num_segments}-segment story outline. For each segment, provide:
1. Hook/Opening line
2. Main content/story beat
3. Creative angle or unique perspective
4. Transition to next segment
5. Key visual suggestions

Format as JSON:
{{
    "story_title": "Compelling video title",
    "story_hook": "Opening hook that grabs attention",
    "narrative_arc": "Brief description of story progression",
    "segments": [
        {{
            "segment_number": 1,
            "hook": "Attention-grabbing opening",
            "main_content": "Core information with story elements",
            "creative_angle": "Unique perspective or metaphor", 
            "transition": "Bridge to next segment",
            "visual_suggestion": "Recommended visual approach",
            "duration_seconds": 8
        }}
    ],
    "conclusion": "Satisfying ending that ties everything together",
    "call_to_action": "What viewers should think/do after watching"
}}
"""
            
            print(f"[STORY AGENT] Creating story outline for: {research_data['query']}")
            
            response = self.model.generate_content(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            story_outline = json.loads(response_text)
            
            # Validate and enhance outline
            story_outline['created_at'] = datetime.now().isoformat()
            story_outline['style_used'] = style
            story_outline['based_on_research'] = research_data['query']
            story_outline['creativity_level'] = story_style['creativity_level']
            
            print(f"[STORY AGENT] Story outline created: '{story_outline.get('story_title', 'Untitled')}'")
            return story_outline
            
        except Exception as e:
            print(f"[STORY AGENT] Error creating outline: {e}")
            return self._create_fallback_outline(research_data, style, num_segments)
    
    def _create_fallback_outline(self, research_data: Dict[str, Any], style: str, num_segments: int) -> Dict[str, Any]:
        """Create a basic outline if AI generation fails"""
        headlines = research_data.get('key_headlines', [])
        
        segments = []
        for i in range(num_segments):
            if i < len(headlines):
                headline = headlines[i]
            else:
                headline = f"Additional context about {research_data['query']}"
            
            segments.append({
                'segment_number': i + 1,
                'hook': f"Segment {i + 1} about the topic",
                'main_content': headline,
                'creative_angle': 'Direct reporting approach',
                'transition': 'Moving to the next important point',
                'visual_suggestion': 'News-style visuals',
                'duration_seconds': 60 // num_segments
            })
        
        return {
            'story_title': f"Understanding {research_data['query']}",
            'story_hook': 'Let\'s explore this important topic',
            'narrative_arc': 'Informational progression',
            'segments': segments,
            'conclusion': 'These developments are worth watching',
            'call_to_action': 'Stay informed about these changes',
            'created_at': datetime.now().isoformat(),
            'style_used': style,
            'based_on_research': research_data['query'],
            'creativity_level': 'fallback'
        }
    
    def generate_creative_script(self, 
                               story_outline: Dict[str, Any],
                               research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform story outline into a full creative script
        """
        try:
            prompt = f"""
Transform this story outline into a compelling, creative video script.

STORY OUTLINE:
Title: {story_outline['story_title']}
Hook: {story_outline['story_hook']}
Arc: {story_outline['narrative_arc']}

SEGMENTS:
{json.dumps(story_outline['segments'], indent=2)}

ORIGINAL RESEARCH:
Query: {research_data['query']}
Headlines: {research_data['key_headlines'][:3]}

CREATIVE SCRIPT REQUIREMENTS:
1. Write engaging narration that tells a story, not just reports facts
2. Use storytelling techniques: setup, tension, payoff
3. Include creative metaphors and analogies
4. Add emotional hooks and human interest angles  
5. Create smooth transitions between segments
6. Use varied sentence structures and pacing
7. Include rhetorical questions to engage viewers
8. Add surprising insights or "plot twists" where appropriate
9. End with a memorable conclusion and clear takeaway

Format as JSON:
{{
    "script_title": "Final video title",
    "full_script_text": "Complete narration text for the entire video",
    "segments": [
        {{
            "segment_number": 1,
            "text": "Narration for this segment with creative storytelling",
            "creative_elements": ["metaphors used", "storytelling techniques"],
            "estimated_duration": 8
        }}
    ],
    "total_estimated_duration": 60,
    "creative_highlights": ["List of creative elements added"],
    "story_structure": "How the narrative flows"
}}
"""
            
            print(f"[STORY AGENT] Generating creative script...")
            
            response = self.model.generate_content(prompt)
            
            # Parse response
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            creative_script = json.loads(response_text)
            
            # Enhance with metadata
            creative_script['generated_at'] = datetime.now().isoformat()
            creative_script['based_on_research'] = research_data['query']
            creative_script['source_headlines'] = research_data['key_headlines'][:3]
            creative_script['research_timestamp'] = research_data.get('research_timestamp')
            
            print(f"[STORY AGENT] Creative script generated: {creative_script.get('total_estimated_duration', 0)}s")
            return creative_script
            
        except Exception as e:
            print(f"[STORY AGENT] Error generating script: {e}")
            return self._create_fallback_script(story_outline, research_data)
    
    def _create_fallback_script(self, story_outline: Dict[str, Any], research_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create basic script if AI generation fails"""
        segments = []
        full_text_parts = []
        
        for segment in story_outline.get('segments', []):
            text = f"{segment.get('main_content', '')} {segment.get('creative_angle', '')}"
            segments.append({
                'segment_number': segment.get('segment_number', 1),
                'text': text,
                'creative_elements': ['basic narrative structure'],
                'estimated_duration': segment.get('duration_seconds', 10)
            })
            full_text_parts.append(text)
        
        return {
            'script_title': story_outline.get('story_title', 'Video Script'),
            'full_script_text': ' '.join(full_text_parts),
            'segments': segments,
            'total_estimated_duration': sum(s.get('estimated_duration', 10) for s in segments),
            'creative_highlights': ['basic storytelling structure'],
            'story_structure': 'linear progression',
            'generated_at': datetime.now().isoformat(),
            'based_on_research': research_data['query'],
            'fallback_mode': True
        }
    
    def synthesize_story(self, 
                        research_data: Dict[str, Any],
                        style: str = 'narrative',
                        target_duration: int = 60,
                        creativity_level: str = 'high') -> Dict[str, Any]:
        """
        Main method: Transform research data into creative video story
        
        Args:
            research_data: Output from ResearchAgent
            style: Storytelling style (narrative, documentary, analytical, conversational)
            target_duration: Target video duration in seconds
            creativity_level: How creative to be (low, moderate, high)
            
        Returns:
            Complete story with creative script ready for video generation
        """
        print(f"[STORY AGENT] Starting story synthesis...")
        print(f"   Query: {research_data['query']}")
        print(f"   Headlines: {len(research_data.get('key_headlines', []))}")
        print(f"   Style: {style}")
        print(f"   Duration: {target_duration}s")
        
        try:
            # Step 1: Analyze research context
            context = self.analyze_research_context(research_data)
            print(f"[STORY AGENT] Context analyzed: {len(context['themes'])} themes, {context['sentiment']} sentiment")
            
            # Step 2: Create story outline
            story_outline = self.create_story_outline(
                context, research_data, style, target_duration
            )
            
            # Step 3: Generate creative script
            creative_script = self.generate_creative_script(story_outline, research_data)
            
            # Step 4: Combine everything into final result
            story_result = {
                'success': True,
                'research_query': research_data['query'],
                'story_style': style,
                'target_duration': target_duration,
                'creativity_level': creativity_level,
                
                # Context Analysis
                'context_analysis': context,
                
                # Story Structure
                'story_outline': story_outline,
                
                # Final Script
                'creative_script': creative_script,
                
                # Ready-to-use data for video generator
                'video_script': {
                    'title': creative_script.get('script_title'),
                    'text': creative_script.get('full_script_text'),
                    'segments': creative_script.get('segments', []),
                    'duration': creative_script.get('total_estimated_duration', target_duration)
                },
                
                # Metadata
                'source_research': {
                    'headlines_count': len(research_data.get('key_headlines', [])),
                    'sources': research_data.get('sources', []),
                    'research_timestamp': research_data.get('research_timestamp')
                },
                
                'processing_metadata': {
                    'generated_at': datetime.now().isoformat(),
                    'model_used': self.model.model_name if hasattr(self.model, 'model_name') else 'gemini',
                    'story_agent_version': '1.0'
                }
            }
            
            print(f"[STORY AGENT] Story synthesis completed successfully!")
            print(f"   Title: {story_result['video_script']['title']}")
            print(f"   Script length: {len(story_result['video_script']['text'])} characters")
            print(f"   Segments: {len(story_result['video_script']['segments'])}")
            
            return story_result
            
        except Exception as e:
            print(f"[STORY AGENT] Error during story synthesis: {e}")
            
            return {
                'success': False,
                'error': str(e),
                'research_query': research_data.get('query', 'Unknown'),
                'fallback_message': 'Story synthesis failed, but research data is available',
                'research_data': research_data,
                'generated_at': datetime.now().isoformat()
            }
    
    def save_story(self, story_result: Dict[str, Any], output_dir: str = "story_cache") -> str:
        """Save generated story to file"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            query_clean = "".join(c for c in story_result['research_query'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            query_clean = query_clean.replace(' ', '_')[:50]
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"story_{query_clean}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(story_result, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[STORY AGENT] Story saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[STORY AGENT] Error saving story: {e}")
            return None