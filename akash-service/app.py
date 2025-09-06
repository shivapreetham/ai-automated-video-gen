"""
Simple Story Generation Service for Akash Deployment
Handles story creation using Gemini API
"""

import os
import json
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

@app.route("/", methods=["GET"])
def home():
    return jsonify({
        "service": "Akash Story Generation Service",
        "version": "1.0",
        "status": "running",
        "gemini_configured": bool(GEMINI_API_KEY),
        "endpoints": {
            "story": "/generate-story",
            "script": "/generate-script",
            "health": "/health"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "gemini_api": "configured" if GEMINI_API_KEY else "missing",
        "timestamp": datetime.now().isoformat()
    })

@app.route("/generate-story", methods=["POST"])
def generate_story():
    """Generate a simple story using Gemini"""
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        topic = data.get("topic")
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        genre = data.get("genre", "general")
        length = data.get("length", "short")
        style = data.get("style", "engaging")
        
        # Generate story using Gemini
        story_result = generate_simple_story(topic, genre, length, style)
        
        return jsonify({
            "success": True,
            "story": story_result["story"],
            "title": story_result["title"],
            "topic": topic,
            "genre": genre,
            "length": length,
            "style": style,
            "generated_by": "gemini",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def generate_simple_story(topic: str, genre: str, length: str, style: str) -> Dict[str, Any]:
    """Generate a simple story using Gemini API"""
    
    if not GEMINI_API_KEY:
        return {
            "title": f"The Tale of {topic}",
            "story": f"This is a {style} {genre} story about {topic}. Once upon a time, there was something fascinating about {topic} that captured everyone's attention. The story unfolded with unexpected twists and turns, revealing the deeper meaning behind {topic}. In the end, everyone learned something valuable about {topic} and how it connects to our daily lives.",
            "generated_by": "fallback"
        }
    
    # Define length specifications
    length_specs = {
        "short": "300-500 words",
        "medium": "500-800 words", 
        "long": "800-1200 words"
    }
    
    word_count = length_specs.get(length, "300-500 words")
    
    prompt = f"""
Create an {style} {genre} story about "{topic}".

Requirements:
- Length: {word_count}
- Genre: {genre}
- Style: {style}
- Make it engaging and well-written
- Include a compelling title
- Have a clear beginning, middle, and end

Format the response as a JSON object with:
- "title": a compelling title for the story
- "story": the complete story text

Example format:
{{
  "title": "Your Story Title Here",
  "story": "The complete story text goes here..."
}}
"""
    
    try:
        model = genai.GenerativeModel('gemini-pro')
        response = model.generate_content(prompt)
        
        # Parse JSON response
        response_text = response.text.strip()
        
        # Clean up response if it has markdown formatting
        if response_text.startswith('```json'):
            response_text = response_text[7:]  # Remove ```json
        if response_text.endswith('```'):
            response_text = response_text[:-3]  # Remove ```
        
        story_data = json.loads(response_text)
        
        return {
            "title": story_data.get("title", f"A Story About {topic}"),
            "story": story_data.get("story", "Story generation failed."),
            "generated_by": "gemini"
        }
        
    except json.JSONDecodeError as e:
        # Fallback if JSON parsing fails - just return the raw response
        print(f"JSON parse error: {e}")
        return {
            "title": f"A {genre} Story About {topic}",
            "story": response.text if 'response' in locals() else f"A {style} {genre} story about {topic} would be generated here.",
            "generated_by": "gemini_raw"
        }
        
    except Exception as e:
        print(f"Gemini API error: {e}")
        # Simple fallback story
        return {
            "title": f"The Tale of {topic}",
            "story": f"This is a {style} {genre} story about {topic}. Once upon a time, there was something interesting about {topic} that captured everyone's attention. The story unfolded with unexpected twists and turns, revealing the deeper meaning behind {topic}. In the end, everyone learned something valuable about {topic} and how it connects to our daily lives.",
            "generated_by": "fallback"
        }

@app.route("/generate-script", methods=["POST"])
def generate_script():
    """Generate video script using Gemini AI"""
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        topic = data.get("topic")
        if not topic:
            return jsonify({"error": "Topic is required"}), 400
        
        style = data.get("style", "informative")
        num_segments = data.get("num_segments", 5)
        duration_per_segment = data.get("duration_per_segment", 4.0)
        
        script_result = generate_video_script(topic, style, num_segments, duration_per_segment)
        
        return jsonify({
            "success": True,
            "text": script_result["text"],
            "sentences": script_result["sentences"],
            "topic": topic,
            "style": style,
            "num_segments": num_segments,
            "generated_by": "akash_gemini",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

def generate_video_script(topic: str, style: str, num_segments: int, duration_per_segment: float) -> Dict[str, Any]:
    """Generate structured video script with sentences and timing"""
    
    if not GEMINI_API_KEY:
        # Fallback response
        sentences = []
        text_parts = []
        
        for i in range(num_segments):
            sentence = f"This is segment {i+1} about {topic}. We explore important aspects and provide valuable insights."
            sentences.append({
                "sentence": sentence,
                "start_time": i * 40000000,
                "end_time": (i+1) * 40000000,
                "duration": 40000000
            })
            text_parts.append(sentence)
        
        return {
            "text": " ".join(text_parts),
            "sentences": sentences
        }
    
    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        
        prompt = f"""Create a {style} video script about "{topic}" with exactly {num_segments} segments.

Requirements:
- Each segment should be 1-2 sentences
- Target speaking time: {duration_per_segment} seconds per segment
- Style: {style}
- Make it engaging and informative
- Each segment should flow naturally to the next
- Include specific facts or insights about {topic}

Format your response as JSON:
{{
    "segments": [
        {{"text": "Segment 1 text here"}},
        {{"text": "Segment 2 text here"}},
        ...
    ]
}}"""
        
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # Clean up response
        if response_text.startswith("```json"):
            response_text = response_text[7:]
        if response_text.endswith("```"):
            response_text = response_text[:-3]
        
        script_data = json.loads(response_text)
        
        # Convert to expected format
        sentences = []
        text_parts = []
        
        for i, segment in enumerate(script_data.get("segments", [])):
            sentence = segment.get("text", f"Segment {i+1} about {topic}")
            sentences.append({
                "sentence": sentence,
                "start_time": i * int(duration_per_segment * 10000000),
                "end_time": (i+1) * int(duration_per_segment * 10000000),
                "duration": int(duration_per_segment * 10000000)
            })
            text_parts.append(sentence)
        
        return {
            "text": " ".join(text_parts),
            "sentences": sentences
        }
        
    except Exception as e:
        print(f"Script generation error: {e}")
        # Fallback on error
        sentences = []
        text_parts = []
        
        for i in range(num_segments):
            sentence = f"This is segment {i+1} about {topic}. We explore important aspects and provide valuable insights about this fascinating topic."
            sentences.append({
                "sentence": sentence,
                "start_time": i * 40000000,
                "end_time": (i+1) * 40000000,
                "duration": 40000000
            })
            text_parts.append(sentence)
        
        return {
            "text": " ".join(text_parts),
            "sentences": sentences
        }

if __name__ == "__main__":
    print("Starting Story Generation Service...")
    print(f"Gemini API: {'Configured' if GEMINI_API_KEY else 'Not Configured'}")
    
    app.run(host="0.0.0.0", port=8080, debug=False)