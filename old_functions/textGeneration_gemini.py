"""
AI-powered text generation using Google Gemini
Generates dynamic, contextual video scripts
"""

import os
import datetime
import json
from typing import Dict, Any, List
import google.generativeai as genai

# Configure Gemini API
GEMINI_API_KEY = "AIzaSyAk_L6R68hAXep7rYhQbBE87S5wIfoF76o"
genai.configure(api_key=GEMINI_API_KEY)

def generate_video_script(topic: str, style: str = "informative", num_segments: int = 5, duration_per_segment: float = 4.0, source_content: str = None, humor_type: str = None) -> Dict[str, Any]:
    """
    Generate dynamic video script using Gemini AI
    
    Args:
        topic: Video topic
        style: Video style (informative, educational, promotional, entertaining)
        num_segments: Number of script segments
        duration_per_segment: Target duration per segment in seconds
        source_content: Original satirical content for context (optional)
        humor_type: Type of humor (absurdist, social_satire, etc.) (optional)
    """
    
    try:
        # Initialize Gemini model
        model = genai.GenerativeModel('gemini-1.5-flash')
        
        # Create dynamic prompt based on style and requirements
        if source_content and humor_type:
            # Enhanced prompt for satirical content
            humor_guidance = {
                'absurdist': 'Focus on absurd situations, pseudo-scientific observations, and ridiculous research findings. Use exaggerated logic and unexpected connections.',
                'social_satire': 'Highlight social contradictions, cultural observations, and modern life absurdities. Use wit and observational humor.',
                'political_satire': 'Focus on political absurdities and governance quirks while keeping it accessible and entertaining.',
                'celebrity_satire': 'Explore fame culture, public personas, and entertainment industry humor.',
                'everyday_life': 'Focus on relatable daily situations with humorous observations everyone can identify with.',
                'general': 'Use general satirical observations with wit and humor.'
            }
            
            style_guidance = humor_guidance.get(humor_type, humor_guidance['general'])
            
            prompt = f"""
Create an {style} video script based on this satirical content with exactly {num_segments} segments.

ORIGINAL SATIRICAL CONTENT:
Title: "{topic}"
Humor Type: {humor_type}
Content Summary: {source_content[:500]}...

STYLE GUIDANCE: {style_guidance}

Requirements:
- Each segment should be 1-2 sentences
- Target speaking time: {duration_per_segment} seconds per segment
- Style: {style} with {humor_type} humor
- Make it entertaining and engaging
- Capture the satirical spirit of the original content
- Each segment should flow naturally to the next
- Include the humor and wit from the original piece
- Make it accessible for a general audience
- Avoid generic phrases like "Welcome" or "Thank you"

Format your response as a JSON object with this structure:
{{
    "title": "Engaging video title based on the satirical content",
    "segments": [
        {{
            "text": "Segment text here with satirical insights",
            "focus": "What this segment covers"
        }}
    ],
    "total_estimated_duration": {num_segments * duration_per_segment}
}}

Create content that transforms the satirical observations into engaging video segments that capture the humor and wit of the original piece.
"""
        else:
            # Original prompt for general content
            prompt = f"""
Create a {style} video script about "{topic}" with exactly {num_segments} segments.

Requirements:
- Each segment should be 1-2 sentences
- Target speaking time: {duration_per_segment} seconds per segment
- Style: {style}
- Make it engaging and informative
- Each segment should flow naturally to the next
- Include specific facts or insights about {topic}
- Avoid generic phrases like "Welcome" or "Thank you"

Format your response as a JSON object with this structure:
{{
    "title": "Video title",
    "segments": [
        {{
            "text": "Segment text here",
            "focus": "What this segment covers"
        }}
    ],
    "total_estimated_duration": {num_segments * duration_per_segment}
}}

Topic: {topic}
Style: {style}
"""
        
        print(f"[AI] Generating script with Gemini for: {topic}")
        
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
                "title": f"{style.title()} Guide to {topic}",
                "segments": segments,
                "total_estimated_duration": num_segments * duration_per_segment
            }
        
        # Process segments and add timing
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
        
        # Create final script structure
        final_script = {
            "Text": " ".join([seg["sentence"] for seg in processed_segments]),
            "title": script_data.get("title", f"{style.title()} Video: {topic}"),
            "sentences": processed_segments,
            "topic": topic,
            "style": style,
            "total_duration": total_duration,
            "segment_count": len(processed_segments),
            "generated_at": datetime.datetime.now().isoformat(),
            "generated_by": "gemini-pro",
            "api_usage": {
                "model": "gemini-pro",
                "prompt_tokens": len(prompt.split()),
                "response_tokens": len(response.text.split())
            }
        }
        
        print(f"[OK] AI script generated: {len(processed_segments)} segments, {total_duration:.1f}s total")
        print(f"[OK] Title: {final_script['title']}")
        
        return final_script
        
    except Exception as e:
        print(f"[ERROR] Gemini script generation failed: {e}")
        
        # Fallback to satirical script generation
        print("[FALLBACK] Using satirical template generation")
        return generate_satirical_fallback_script(topic, style, num_segments, duration_per_segment, source_content, humor_type)

def generate_satirical_fallback_script(topic: str, style: str, num_segments: int, duration_per_segment: float, source_content: str = None, humor_type: str = None) -> Dict[str, Any]:
    """Enhanced fallback script generation for satirical content"""
    
    # Extract the actual title from the topic if it's a long prompt
    if source_content and len(topic) > 200:
        # Try to extract the original title from the prompt
        lines = topic.split('. ')
        original_title = None
        for line in lines:
            if 'first guest' in line.lower() or any(word in line.lower() for word in ['party', 'worst', 'research', 'study']):
                # This looks like it might contain the original title
                words = line.split()
                if len(words) < 15:  # Reasonable title length
                    original_title = line
                    break
        
        if not original_title:
            # Fallback: use first few words
            original_title = ' '.join(topic.split()[:8]) + "..."
    else:
        original_title = topic
    
    # Create satirical templates based on humor type
    if humor_type == 'absurdist':
        sentences = [
            f"Research has revealed the shocking truth about {original_title.lower()}.",
            f"Scientists at the Institute for Obvious Studies have confirmed what we all suspected.",
            f"The findings show a direct correlation between early arrival and social awkwardness.",
            f"This groundbreaking research explains why party dynamics follow predictable patterns."
        ]
        script_title = f"Ridiculous Research: {original_title}"
    elif humor_type == 'social_satire':
        sentences = [
            f"Modern society has a problem, and it's called {original_title.lower()}.",
            f"This phenomenon reveals everything wrong with our social expectations.",
            f"It's a perfect example of how we've created our own social nightmares.",
            f"The real question is: why do we keep repeating these social patterns?"
        ]
        script_title = f"Society Check: {original_title}"
    elif humor_type == 'everyday_life':
        sentences = [
            f"We've all experienced this: {original_title.lower()}.",
            f"It's one of those universal truths nobody talks about.",
            f"This situation perfectly captures the awkwardness of social gatherings.",
            f"The reality is, we're all just trying to navigate these social minefields."
        ]
        script_title = f"Daily Reality: {original_title}"
    elif humor_type == 'celebrity_satire':
        sentences = [
            f"Even celebrities can't escape the truth about {original_title.lower()}.",
            f"Fame doesn't protect you from basic social awkwardness.",
            f"This proves that some human behaviors transcend social status.",
            f"Whether you're famous or not, we all face these social situations."
        ]
        script_title = f"Celebrity Watch: {original_title}"
    elif humor_type == 'political_satire':
        sentences = [
            f"Politicians have turned {original_title.lower()} into an art form.",
            f"This perfectly illustrates the absurdity of modern political behavior.",
            f"It's like watching political theater, but somehow more predictable.",
            f"The real comedy is how seriously everyone takes these situations."
        ]
        script_title = f"Political Comedy: {original_title}"
    else:
        # General satirical content
        sentences = [
            f"The satirical truth about {original_title.lower()} has been revealed.",
            f"This observation perfectly captures the absurdity of modern life.",
            f"It's the kind of insight that makes you laugh and cringe simultaneously.",
            f"These moments remind us that reality is often stranger than fiction."
        ]
        script_title = f"Satirical Take: {original_title}"
    
    # Limit to requested number of segments
    sentences = sentences[:num_segments]
    
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
            "focus": f"Satirical point {i+1}",
            "segment_number": i + 1
        })
        current_time += estimated_duration
    
    return {
        "Text": " ".join(sentences),
        "title": script_title,
        "sentences": processed_segments,
        "topic": original_title,
        "style": style,
        "total_duration": current_time / azure_time_unit,
        "segment_count": len(processed_segments),
        "generated_at": datetime.datetime.now().isoformat(),
        "generated_by": "satirical_fallback_template",
        "humor_type": humor_type
    }

def generate_fallback_script(topic: str, style: str, num_segments: int, duration_per_segment: float) -> Dict[str, Any]:
    """Fallback script generation if Gemini fails"""
    
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
        "title": f"{style.title()} Overview: {topic}",
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
    Mindsflow-compatible function wrapper
    """
    topic = event.get("topic", "")
    style = event.get("style", "informative")
    num_segments = event.get("num_segments", 5)
    duration_per_segment = event.get("duration_per_segment", 4.0)
    
    if not topic:
        return {
            "success": False,
            "error": "Topic is required"
        }
    
    try:
        script_data = generate_video_script(topic, style, num_segments, duration_per_segment)
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
    test_topic = "Artificial Intelligence"
    result = generate_video_script(test_topic, "educational", 5)
    print(f"\nTest Results:")
    print(f"Title: {result['title']}")
    print(f"Duration: {result['total_duration']:.1f}s")
    print(f"Segments: {result['segment_count']}")
    for i, seg in enumerate(result['sentences'][:3]):  # Show first 3
        print(f"  {i+1}: {seg['sentence']}")