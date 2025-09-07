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
    
    # Create detailed prompt for Gemini
    prompt = f"""
    Create a {script_size} educational script about "{topic}" with exactly {config['segments']} segments.
    
    Requirements:
    - Each segment should be exactly {config['words_per_segment']} words
    - Each segment should be informative and engaging
    - Create vivid image prompts for each segment
    - Return ONLY valid JSON in this format:
    
    {{
        "segments": [
            {{
                "segment_number": 1,
                "text": "First segment text here ({config['words_per_segment']} words)",
                "image_prompt": "Detailed visual description for this segment",
                "focus": "Main topic of this segment"
            }},
            ...
        ]
    }}
    
    Topic: {topic}
    Script size: {script_size}
    Number of segments: {config['segments']}
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
        
        for i, segment in enumerate(segments):
            segment_text = segment["text"]
            image_prompt = segment["image_prompt"]
            
            processed_segment = {
                "segment_number": i + 1,
                "text": segment_text,
                "image_prompt": f"{topic}, {image_prompt}",  # Enhance with topic context
                "focus": segment.get("focus", f"Segment {i+1}"),
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
            "generated_at": datetime.now().isoformat(),
            "generator": "gemini"
        }
        
        print(f"[GEMINI] Generated {len(processed_segments)} segments for '{topic}' ({script_size})")
        return result
        
    except Exception as e:
        print(f"[GEMINI ERROR] {e}")
        # Fallback generation
        return generate_fallback_script(topic, script_size, config)

def generate_fallback_script(topic: str, script_size: str, config: Dict) -> Dict[str, Any]:
    """Fallback script generation if Gemini fails"""
    
    segments = []
    for i in range(config['segments']):
        segment_text = f"This is segment {i+1} about {topic}. " * (config['words_per_segment'] // 10)
        
        segment = {
            "segment_number": i + 1,
            "text": segment_text.strip(),
            "image_prompt": f"{topic}, detailed illustration of segment {i+1}",
            "focus": f"Aspect {i+1} of {topic}",
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
        "generated_at": datetime.now().isoformat(),
        "generator": "fallback"
    }

if __name__ == "__main__":
    # Test
    result = generate_script("artificial intelligence basics", "medium")
    print(json.dumps(result, indent=2))