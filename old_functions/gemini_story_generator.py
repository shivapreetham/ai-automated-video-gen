#!/usr/bin/env python3
"""
Gemini-powered story generator for dynamic video content
"""

import os
import json
import requests
from typing import Dict, List, Any
from datetime import datetime

class GeminiStoryGenerator:
    def __init__(self, api_key: str = None):
        """Initialize with Gemini API key"""
        # Load environment variables from .env file
        self._load_env_file()
        
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash-latest:generateContent"
        
        if self.api_key:
            print(f"Gemini API key loaded: {self.api_key[:10]}...{self.api_key[-4:]}")
        else:
            print("No Gemini API key found in environment")
    
    def _load_env_file(self):
        """Load environment variables from .env file"""
        try:
            # Get the project root directory (go up from local_functions)
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            env_file = os.path.join(project_root, '.env')
            
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            os.environ[key.strip()] = value.strip()
                print(f"Loaded environment from: {env_file}")
            else:
                print(f"No .env file found at: {env_file}")
        except Exception as e:
            print(f"Error loading .env file: {e}")
        
    def generate_story_segments(self, topic: str, num_segments: int = 3, style: str = "informative") -> Dict[str, Any]:
        """
        Generate dynamic story segments using Gemini API
        """
        try:
            # Create the prompt based on style
            prompts = {
                'informative': f"""Create an informative video script about "{topic}" with exactly {num_segments} segments.
                
Requirements:
- Each segment should be 1-2 sentences
- Keep each segment under 25 words
- Make it educational and engaging
- Focus on key facts and insights
- Start with an introduction, provide main content, end with conclusion

Format your response as a JSON object with this structure:
{{
    "segments": [
        {{"text": "segment 1 text", "focus": "introduction"}},
        {{"text": "segment 2 text", "focus": "main_content"}},
        {{"text": "segment 3 text", "focus": "conclusion"}}
    ]
}}""",

                'educational': f"""Create an educational video script about "{topic}" with exactly {num_segments} segments.

Requirements:
- Each segment should be 1-2 sentences
- Keep each segment under 25 words
- Use clear, teaching language
- Build knowledge progressively
- Include practical insights

Format your response as a JSON object with this structure:
{{
    "segments": [
        {{"text": "segment 1 text", "focus": "introduction"}},
        {{"text": "segment 2 text", "focus": "main_content"}},
        {{"text": "segment 3 text", "focus": "conclusion"}}
    ]
}}""",

                'promotional': f"""Create a promotional video script about "{topic}" with exactly {num_segments} segments.

Requirements:
- Each segment should be 1-2 sentences
- Keep each segment under 25 words
- Make it engaging and persuasive
- Highlight benefits and value
- Include call to action

Format your response as a JSON object with this structure:
{{
    "segments": [
        {{"text": "segment 1 text", "focus": "hook"}},
        {{"text": "segment 2 text", "focus": "benefits"}},
        {{"text": "segment 3 text", "focus": "call_to_action"}}
    ]
}}"""
            }
            
            prompt = prompts.get(style, prompts['informative'])
            
            # Make request to Gemini API
            if not self.api_key:
                print("WARNING: No Gemini API key found. Using fallback content.")
                return self._generate_fallback_content(topic, num_segments, style)
            
            headers = {
                'Content-Type': 'application/json',
            }
            
            payload = {
                "contents": [
                    {
                        "parts": [
                            {
                                "text": prompt
                            }
                        ]
                    }
                ],
                "generationConfig": {
                    "temperature": 0.7,
                    "topK": 1,
                    "topP": 1,
                    "maxOutputTokens": 1024,
                }
            }
            
            url = f"{self.base_url}?key={self.api_key}"
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                content = result['candidates'][0]['content']['parts'][0]['text']
                
                # Try to extract JSON from the response
                try:
                    # Find JSON in the response
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_content = content[start:end]
                    
                    story_data = json.loads(json_content)
                    
                    # Validate the structure
                    if 'segments' in story_data and len(story_data['segments']) >= num_segments:
                        return self._format_story_response(story_data, topic, style)
                    else:
                        print("WARNING: Invalid Gemini response structure. Using fallback.")
                        return self._generate_fallback_content(topic, num_segments, style)
                        
                except json.JSONDecodeError:
                    print("WARNING: Could not parse Gemini JSON response. Using fallback.")
                    return self._generate_fallback_content(topic, num_segments, style)
            else:
                print(f"WARNING: Gemini API error {response.status_code}. Using fallback.")
                return self._generate_fallback_content(topic, num_segments, style)
                
        except Exception as e:
            print(f"WARNING: Error calling Gemini API: {e}. Using fallback.")
            return self._generate_fallback_content(topic, num_segments, style)
    
    def _format_story_response(self, story_data: Dict, topic: str, style: str) -> Dict[str, Any]:
        """Format the Gemini response into our expected structure"""
        segments = story_data['segments'][:3]  # Limit to requested number
        
        # Calculate timing for each segment
        azure_time_unit = 10000000
        sentence_data = []
        current_time = 0
        all_text = []
        
        for i, segment in enumerate(segments):
            text = segment['text']
            all_text.append(text)
            
            # Estimate duration based on text length and speech
            words = len(text.split())
            chars = len(text)
            
            # Estimate based on reading speed (140 words per minute for TTS)
            word_duration = (words / 140) * 60 * azure_time_unit
            
            # Add buffer time for pacing
            buffer_time = min(20000000, max(10000000, chars * 40000))  # 1-2 seconds buffer
            
            estimated_duration = int(word_duration + buffer_time)
            
            sentence_data.append({
                "sentence": text,
                "start_time": current_time,
                "end_time": current_time + estimated_duration,
                "duration": estimated_duration,
                "word_count": words,
                "char_count": chars,
                "focus": segment.get('focus', 'content')
            })
            current_time += estimated_duration
        
        total_duration = current_time / azure_time_unit
        
        return {
            "Text": " ".join(all_text),
            "sentences": sentence_data,
            "topic": topic,
            "style": style,
            "total_duration": total_duration,
            "segment_count": len(segments),
            "generated_at": datetime.now().isoformat(),
            "source": "gemini_generated"
        }
    
    def _generate_fallback_content(self, topic: str, num_segments: int, style: str) -> Dict[str, Any]:
        """Generate fallback content when Gemini is not available"""
        fallback_templates = {
            'informative': [
                f"Learn about {topic} and its key concepts.",
                f"Discover the important aspects of {topic}.",
                f"Understanding {topic} provides valuable insights."
            ],
            'educational': [
                f"Today we explore {topic} step by step.",
                f"Here are the essential facts about {topic}.",
                f"Apply these {topic} concepts in practice."
            ],
            'promotional': [
                f"Discover the benefits of {topic} today.",
                f"See why {topic} matters for you.",
                f"Take action with {topic} now."
            ]
        }
        
        templates = fallback_templates.get(style, fallback_templates['informative'])
        segments = templates[:num_segments]
        
        # Create timing data
        azure_time_unit = 10000000
        sentence_data = []
        current_time = 0
        
        for text in segments:
            words = len(text.split())
            word_duration = (words / 140) * 60 * azure_time_unit
            buffer_time = 15000000  # 1.5 seconds buffer
            estimated_duration = int(word_duration + buffer_time)
            
            sentence_data.append({
                "sentence": text,
                "start_time": current_time,
                "end_time": current_time + estimated_duration,
                "duration": estimated_duration,
                "word_count": words,
                "char_count": len(text)
            })
            current_time += estimated_duration
        
        return {
            "Text": " ".join(segments),
            "sentences": sentence_data,
            "topic": topic,
            "style": style,
            "total_duration": current_time / azure_time_unit,
            "segment_count": len(segments),
            "generated_at": datetime.now().isoformat(),
            "source": "fallback_template"
        }

def test_gemini_generator():
    """Test the Gemini story generator"""
    generator = GeminiStoryGenerator()
    result = generator.generate_story_segments("artificial intelligence", 3, "informative")
    
    print("Generated Story:")
    print(f"Topic: {result['topic']}")
    print(f"Duration: {result['total_duration']:.1f}s")
    print(f"Source: {result['source']}")
    print("\nSegments:")
    for i, segment in enumerate(result['sentences'], 1):
        print(f"{i}. {segment['sentence']} ({segment['word_count']} words)")
    
    return result

if __name__ == "__main__":
    test_gemini_generator()