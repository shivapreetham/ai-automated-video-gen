"""
Enhanced AI-powered text generation using Google Gemini with research context
Generates dynamic, contextual video scripts based on recent research headlines
"""

import os
import datetime
import json
from typing import Dict, Any, List
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyB2VLzqQbnSy0KloCMlk4IRXD6L9Qwgc8Y"
genai.configure(api_key=GEMINI_API_KEY)

def generate_video_script_with_research(
    topic: str, 
    research_headlines: List[str] = None,
    style: str = "informative", 
    num_segments: int = 5, 
    duration_per_segment: float = 4.0
) -> Dict[str, Any]:
    """
    Generate dynamic video script using Gemini AI with research context
    
    Args:
        topic: Video topic
        research_headlines: List of recent headlines about the topic
        style: Video style (informative, educational, promotional)
        num_segments: Number of script segments
        duration_per_segment: Target duration per segment in seconds
    """
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Build enhanced prompt with research context
        research_context = ""
        if research_headlines and len(research_headlines) > 0:
            research_context = f"""

RECENT RESEARCH CONTEXT:
Based on these recent headlines, create a current and relevant script:
{chr(10).join([f"- {headline}" for headline in research_headlines[:5]])}

Use this context to make the script current, relevant, and engaging. Add creative storytelling elements and make it feel like recent news.
"""
        
        # Create dynamic prompt based on style and requirements
        prompt = f"""
Create a creative, engaging {style} video script about "{topic}" with exactly {num_segments} segments.{research_context}

Requirements:
- Each segment should be 1-2 sentences
- Target speaking time: {duration_per_segment} seconds per segment
- Style: {style}
- Make it highly engaging with creative storytelling
- Add narrative elements, metaphors, and human interest angles
- Include current, relevant information
- Each segment should flow naturally to the next
- Avoid generic phrases like "Welcome" or "Thank you"
- Add creative hooks and compelling transitions

Format your response as a JSON object with this structure:
{{
    "title": "Creative video title",
    "segments": [
        {{
            "text": "Engaging segment text with storytelling elements",
            "focus": "What this segment covers"
        }}
    ],
    "total_estimated_duration": {num_segments * duration_per_segment}
}}

Topic: {topic}
Style: {style}
"""
        
        print(f"[AI] Generating enhanced script with research context for: {topic}")
        
        # Generate content
        response = model.generate_content(prompt)
        
        # Parse JSON response
        try:
            # Clean the response text to extract JSON
            response_text = response.text.strip()
            if response_text.startswith('```json'):
                response_text = response_text[7:]
            if response_text.endswith('```'):
                response_text = response_text[:-3]
            
            script_data = json.loads(response_text)
            
            # Validate structure
            if not isinstance(script_data.get('segments'), list):
                raise ValueError("Invalid segments format")
            
            if len(script_data['segments']) != num_segments:
                print(f"[WARNING] Expected {num_segments} segments, got {len(script_data['segments'])}")
            
        except (json.JSONDecodeError, ValueError) as parse_error:
            print(f"[WARNING] Failed to parse JSON response: {parse_error}")
            # Fallback: split raw response into segments
            segments = []
            lines = response.text.strip().split('\n')
            clean_lines = [line.strip() for line in lines if line.strip() and not line.strip().startswith(('#', '-', '*'))]
            
            for i, line in enumerate(clean_lines[:num_segments]):
                segments.append({
                    "text": line,
                    "focus": f"Segment {i+1} content"
                })
            
            script_data = {
                "title": f"Enhanced Guide to {topic}",
                "segments": segments,
                "total_estimated_duration": num_segments * duration_per_segment
            }
        
        # Process segments and add timing (same format as original)
        azure_time_unit = 10000000  # For compatibility
        processed_segments = []
        current_time = 0
        
        for i, segment in enumerate(script_data['segments']):
            text = segment['text']
            
            # Estimate duration based on text
            words = len(text.split())
            chars = len(text)
            
            # More accurate duration estimation
            word_duration = (words / 150) * 60  # 150 WPM in seconds
            char_duration = chars * 0.05  # Character-based estimation
            
            # Use the longer of the two estimates, with minimum duration
            estimated_seconds = max(word_duration, char_duration, duration_per_segment * 0.7)
            estimated_duration = int(estimated_seconds * azure_time_unit)
            
            processed_segments.append({
                "sentence": text,
                "start_time": current_time,
                "end_time": current_time + estimated_duration,
                "duration": estimated_duration,
                "word_count": words,
                "char_count": chars,
                "focus": segment.get('focus', f"Segment {i+1}"),
                "segment_number": i + 1
            })
            current_time += estimated_duration
        
        total_duration = current_time / azure_time_unit
        
        # Create final script structure (same format as original)
        final_script = {
            "Text": " ".join([seg["sentence"] for seg in processed_segments]),
            "title": script_data.get("title", f"Enhanced Video: {topic}"),
            "sentences": processed_segments,
            "topic": topic,
            "style": style,
            "total_duration": total_duration,
            "segment_count": len(processed_segments),
            "generated_at": datetime.datetime.now().isoformat(),
            "generated_by": "gemini-enhanced-with-research",
            "research_context": len(research_headlines) if research_headlines else 0,
            "api_usage": {
                "model": "gemini-1.5-flash",
                "prompt_tokens": len(prompt.split()),
                "response_tokens": len(response.text.split())
            }
        }
        
        print(f"[OK] Enhanced AI script generated: {len(processed_segments)} segments, {total_duration:.1f}s total")
        print(f"[OK] Title: {final_script['title']}")
        
        return final_script
        
    except Exception as e:
        print(f"[ERROR] Enhanced Gemini script generation failed: {e}")
        
        # Fallback to basic script generation (same as original)
        print("[FALLBACK] Using basic template generation")
        return generate_fallback_script(topic, style, num_segments, duration_per_segment)

def generate_fallback_script(topic: str, style: str, num_segments: int, duration_per_segment: float) -> Dict[str, Any]:
    """Fallback script generation if Gemini fails (same as original)"""
    
    templates = {
        'informative': [
            f"{topic} is a fascinating subject with many important aspects to explore.",
            f"Understanding the key principles of {topic} provides valuable insights.",
            f"There are several critical factors that make {topic} significant today.",
            f"The impact of {topic} extends far beyond what most people realize.",
            f"These insights about {topic} can help you make better informed decisions."
        ],
        'educational': [
            f"Let's learn about the fundamental concepts of {topic}.",
            f"The science behind {topic} reveals some interesting discoveries.",
            f"Researchers have found that {topic} plays a crucial role in many areas.",
            f"By understanding {topic}, we can better appreciate its applications.",
            f"This knowledge about {topic} opens up new possibilities for learning."
        ],
        'promotional': [
            f"Discover why {topic} is becoming increasingly important.",
            f"Here's what experts are saying about the benefits of {topic}.",
            f"Don't miss out on understanding how {topic} can make a difference.",
            f"Take advantage of these insights about {topic} to stay ahead.",
            f"Join thousands who are already benefiting from knowledge about {topic}."
        ]
    }
    
    sentences = templates.get(style, templates['informative'])[:num_segments]
    
    # Create timing structure
    azure_time_unit = 10000000
    processed_segments = []
    current_time = 0
    
    for i, sentence in enumerate(sentences):
        words = len(sentence.split())
        estimated_duration = int(duration_per_segment * azure_time_unit)
        
        processed_segments.append({
            "sentence": sentence,
            "start_time": current_time,
            "end_time": current_time + estimated_duration,
            "duration": estimated_duration,
            "word_count": words,
            "char_count": len(sentence),
            "focus": f"Key point {i+1}",
            "segment_number": i + 1
        })
        current_time += estimated_duration
    
    return {
        "Text": " ".join(sentences),
        "title": f"Enhanced Overview: {topic}",
        "sentences": processed_segments,
        "topic": topic,
        "style": style,
        "total_duration": current_time / azure_time_unit,
        "segment_count": len(processed_segments),
        "generated_at": datetime.datetime.now().isoformat(),
        "generated_by": "fallback_template"
    }

def mindsflow_function(event, context) -> dict:
    """
    Mindsflow-compatible function wrapper (same as original)
    """
    topic = event.get("topic", "")
    style = event.get("style", "informative")
    num_segments = event.get("num_segments", 5)
    duration_per_segment = event.get("duration_per_segment", 4.0)
    research_headlines = event.get("research_headlines", [])
    
    if not topic:
        return {
            "success": False,
            "error": "Topic is required"
        }
    
    try:
        script_data = generate_video_script_with_research(
            topic, research_headlines, style, num_segments, duration_per_segment
        )
        return {
            "success": True,
            "script_data": script_data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    # Test the function
    test_headlines = [
        "Trump announces new 50% tariff on Indian goods",
        "India considers retaliation against US trade measures", 
        "Global markets react to escalating trade tensions"
    ]
    
    result = generate_video_script_with_research(
        topic="Donald Trump tariff on India",
        research_headlines=test_headlines,
        style="narrative",
        num_segments=5
    )
    
    print(f"\nTest Results:")
    print(f"Title: {result['title']}")
    print(f"Duration: {result['total_duration']:.1f}s")
    print(f"Segments: {result['segment_count']}")
    print(f"Research context: {result.get('research_context', 0)} headlines")
    for i, seg in enumerate(result['sentences'][:3]):  # Show first 3
        print(f"  {i+1}: {seg['sentence'][:80]}...")