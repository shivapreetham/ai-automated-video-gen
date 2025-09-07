"""
Gemini Script Generation - Independent Backend Function
Generates script with segments based on script_size
"""

import os
import json
import uuid
import google.generativeai as genai
from typing import Dict, List, Any
from datetime import datetime

# Configure Gemini
GEMINI_API_KEY = "AIzaSyB2VLzqQbnSy0KloCMlk4IRXD6L9Qwgc8Y"
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_script(topic: str, script_size: str = "medium") -> Dict[str, Any]:
    """
    Generate script with variable segments based on script_size
    
    Returns:
    {
        "text": "full script text",
        "segments": [
            {"text": "segment text", "image_prompt": "image prompt", "duration_seconds": 5.0},
            ...
        ],
        "total_segments": 5,
        "estimated_duration": 25.0
    }
    """
    
    # Define script size parameters
    size_config = {
        "short": {"segments": 3, "words_per_segment": 25, "duration_per_segment": 4.0},
        "medium": {"segments": 5, "words_per_segment": 35, "duration_per_segment": 5.0},
        "long": {"segments": 8, "words_per_segment": 50, "duration_per_segment": 6.0}
    }
    
    config = size_config.get(script_size, size_config["medium"])
    
    # Create comprehensive prompt for Gemini
    prompt = f"""
    Create a comprehensive, engaging educational script about "{topic}" with exactly {config['segments']} segments.
    This will be converted to video with AI-generated images, professional voiceover, and captions.
    
    Requirements:
    - Each segment should be exactly {config['words_per_segment']} words
    - Write in an engaging, documentary-style narrative voice
    - Create vivid, detailed image prompts that will produce stunning AI-generated visuals
    - Include caption text for accessibility and engagement
    - Each segment should flow naturally into the next
    - Use descriptive language that paints visual scenes
    - Make content both educational and captivating
    
    Return ONLY valid JSON in this exact format:
    
    {{
        "segments": [
            {{
                "segment_number": 1,
                "text": "Engaging narrative text for segment 1 ({config['words_per_segment']} words)",
                "image_prompt": "Cinematic, detailed visual description - photorealistic, high-quality, professional photography style",
                "caption_text": "Key caption text for this segment",
                "visual_style": "Suggested visual style (e.g., cinematic, documentary, artistic)",
                "focus": "Main topic focus of this segment",
                "transition_hint": "Suggested transition to next segment"
            }},
            ...
        ],
        "overall_theme": "Overall visual theme for the entire video",
        "target_audience": "Target audience description",
        "video_style": "Recommended video style and mood"
    }}
    
    Topic: {topic}
    Script size: {script_size}
    Number of segments: {config['segments']}
    
    Make each image prompt highly detailed with specific visual elements, lighting, composition, and style that will create compelling AI-generated images. Think cinematically!
    """
    
    try:
        # Generate with Gemini
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean JSON response
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        script_data = json.loads(response_text)
        segments = script_data["segments"]
        
        # Process segments and calculate durations
        processed_segments = []
        full_text_parts = []
        
        # Extract additional metadata if present
        overall_theme = script_data.get("overall_theme", f"Educational content about {topic}")
        target_audience = script_data.get("target_audience", "General audience")
        video_style = script_data.get("video_style", "Professional documentary style")
        
        for i, segment in enumerate(segments):
            segment_text = segment["text"]
            image_prompt = segment["image_prompt"]
            
            processed_segment = {
                "segment_number": i + 1,
                "text": segment_text,
                "image_prompt": f"{image_prompt}, {overall_theme}, professional quality",
                "caption_text": segment.get("caption_text", segment_text[:50] + "..." if len(segment_text) > 50 else segment_text),
                "visual_style": segment.get("visual_style", "cinematic"),
                "focus": segment.get("focus", f"Segment {i+1}"),
                "transition_hint": segment.get("transition_hint", "smooth transition"),
                "duration_seconds": config['duration_per_segment'],
                "start_time": i * config['duration_per_segment'],
                "end_time": (i + 1) * config['duration_per_segment']
            }
            
            processed_segments.append(processed_segment)
            full_text_parts.append(segment_text)
        
        result = {
            "text": " ".join(full_text_parts),
            "segments": processed_segments,
            "total_segments": len(processed_segments),
            "estimated_duration": len(processed_segments) * config['duration_per_segment'],
            "script_size": script_size,
            "topic": topic,
            "overall_theme": overall_theme,
            "target_audience": target_audience,
            "video_style": video_style,
            "generated_at": datetime.now().isoformat(),
            "generator": "gemini_enhanced"
        }
        
        print(f"[GEMINI] Generated {len(processed_segments)} segments for '{topic}' ({script_size})")
        return result
        
    except Exception as e:
        print(f"[GEMINI ERROR] {e}")
        # Fallback generation
        return generate_fallback_script(topic, script_size, config)

def generate_fallback_script(topic: str, script_size: str, config: Dict) -> Dict[str, Any]:
    """Enhanced fallback script generation if Gemini fails"""
    
    segments = []
    for i in range(config['segments']):
        segment_text = f"This is segment {i+1} exploring {topic}. " * (config['words_per_segment'] // 10)
        
        segment = {
            "segment_number": i + 1,
            "text": segment_text.strip(),
            "image_prompt": f"{topic}, cinematic detailed illustration of segment {i+1}, professional quality, photorealistic",
            "caption_text": f"Exploring {topic} - Part {i+1}",
            "visual_style": "cinematic",
            "focus": f"Aspect {i+1} of {topic}",
            "transition_hint": "smooth fade transition",
            "duration_seconds": config['duration_per_segment'],
            "start_time": i * config['duration_per_segment'],
            "end_time": (i + 1) * config['duration_per_segment']
        }
        segments.append(segment)
    
    return {
        "text": " ".join([s["text"] for s in segments]),
        "segments": segments,
        "total_segments": len(segments),
        "estimated_duration": len(segments) * config['duration_per_segment'],
        "script_size": script_size,
        "topic": topic,
        "overall_theme": f"Educational exploration of {topic}",
        "target_audience": "General audience",
        "video_style": "Documentary style presentation",
        "generated_at": datetime.now().isoformat(),
        "generator": "fallback_enhanced"
    }

if __name__ == "__main__":
    # Test
    result = generate_script("artificial intelligence basics", "medium")
    print(json.dumps(result, indent=2))