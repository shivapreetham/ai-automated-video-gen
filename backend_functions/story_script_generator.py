"""
Enhanced Story-Driven Script Generation
Creates engaging narratives with variable-length segments and dialog integration
"""

import os
import json
import uuid
import google.generativeai as genai
from typing import Dict, List, Any
from datetime import datetime

# Configure Gemini
import os
from dotenv import load_dotenv
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "AIzaSyB2VLzqQbnSy0KloCMlk4IRXD6L9Qwgc8Y")
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_story_script(topic: str, script_length: str = "medium", include_dialogs: bool = True) -> Dict[str, Any]:
    """
    Generate an engaging story-driven script with variable-length segments
    
    Args:
        topic: Main topic/theme for the story
        script_length: "short" (3-4 segments), "medium" (5-7 segments), "long" (8-12 segments)
        include_dialogs: Whether to include character dialogs in the narrative
    
    Returns:
        Enhanced script data with story elements and flexible segment timing
    """
    
    # Define story parameters based on length
    length_config = {
        "short": {
            "segments": (3, 4),
            "total_duration": (20, 35),
            "story_complexity": "simple",
            "character_count": 2
        },
        "medium": {
            "segments": (5, 7), 
            "total_duration": (45, 70),
            "story_complexity": "moderate",
            "character_count": 3
        },
        "long": {
            "segments": (8, 12),
            "total_duration": (80, 120),
            "story_complexity": "complex",
            "character_count": 4
        }
    }
    
    config = length_config.get(script_length, length_config["medium"])
    
    # Create comprehensive story prompt
    dialog_instruction = """
    - Include natural character dialogs that advance the story
    - Mix narrative and dialog segments for variety
    - Use dialogs to show character personality and relationships
    """ if include_dialogs else """
    - Focus on rich narrative storytelling
    - Use descriptive language that paints vivid scenes
    - Create emotional connection through narration
    """
    
    prompt = f"""
    Create an engaging, cinematic story about "{topic}" with {config['segments'][0]}-{config['segments'][1]} segments.
    This will be a professional video with AI visuals, voiceover, and captions.
    
    STORY REQUIREMENTS:
    - Write a compelling narrative with clear story arc (beginning, development, climax, resolution)
    - Create {config['character_count']} distinct characters with personality
    - Each segment should vary in length naturally based on story pacing
    - Story complexity: {config['story_complexity']}
    - Total estimated duration: {config['total_duration'][0]}-{config['total_duration'][1]} seconds
    {dialog_instruction}
    
    SEGMENT REQUIREMENTS:
    - Variable word count per segment (20-80 words based on story needs)
    - Each segment should have 1-3 images depending on content complexity
    - Include smooth story transitions between segments
    - Create vivid, cinematic image descriptions
    - Write engaging captions that enhance the story
    
    VISUAL STYLE:
    - Cinematic, high-quality visual prompts
    - Consistent character and environment descriptions
    - Emotional storytelling through visuals
    - Professional cinematography style descriptions
    
    Return ONLY valid JSON in this exact format:
    
    {{
        "story_title": "Engaging title for the story",
        "story_summary": "Brief 2-sentence summary of the story",
        "characters": [
            {{"name": "Character Name", "description": "Brief character description", "role": "protagonist/supporting/etc"}}
        ],
        "segments": [
            {{
                "segment_number": 1,
                "segment_type": "narrative" | "dialog" | "mixed",
                "text": "Segment text with natural length based on story pacing",
                "character_speaking": "Character name if dialog, null if narrative",
                "images": [
                    {{
                        "image_number": 1,
                        "image_prompt": "Detailed cinematic visual description",
                        "image_duration_seconds": 3.5,
                        "visual_focus": "What this image emphasizes in the story"
                    }}
                ],
                "caption_text": "Engaging caption for this segment",
                "story_purpose": "What this segment accomplishes in the story",
                "emotional_tone": "happy/sad/suspenseful/etc",
                "transition_to_next": "How this segment leads to the next"
            }}
        ],
        "visual_theme": "Overall visual style for the entire story",
        "target_emotion": "Primary emotion this story should evoke",
        "video_style": "Recommended cinematographic style"
    }}
    
    Topic: {topic}
    Length: {script_length}
    Include dialogs: {include_dialogs}
    
    Make this a truly engaging story that viewers will remember! Focus on emotional connection and visual storytelling.
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
        
        story_data = json.loads(response_text)
        
        # Process and enhance the story data
        processed_script = process_story_segments(story_data, topic, script_length)
        
        print(f"[STORY] Generated '{processed_script['story_title']}' with {len(processed_script['segments'])} segments")
        return processed_script
        
    except Exception as e:
        print(f"[STORY ERROR] Gemini API failed: {e}")
        print(f"[STORY ERROR] Using enhanced fallback story generation...")
        return generate_fallback_story(topic, script_length, config, include_dialogs)

def process_story_segments(story_data: Dict[str, Any], topic: str, script_length: str) -> Dict[str, Any]:
    """Process and enhance the generated story segments"""
    
    segments = story_data.get("segments", [])
    processed_segments = []
    full_text_parts = []
    total_duration = 0
    
    for i, segment in enumerate(segments):
        segment_text = segment.get("text", "")
        images = segment.get("images", [])
        
        # Calculate segment timing based on text length and image count
        word_count = len(segment_text.split())
        base_duration = (word_count / 120) * 60  # 120 WPM speech rate
        
        # Adjust for images and story pacing
        image_count = len(images) if images else 1
        segment_duration = max(3.0, base_duration + (image_count * 1.5))  # Minimum 3 seconds
        
        # Process images for this segment
        processed_images = []
        if images:
            cumulative_time = 0
            for img_idx, image in enumerate(images):
                img_duration = image.get("image_duration_seconds", segment_duration / len(images))
                processed_images.append({
                    "image_number": img_idx + 1,
                    "image_prompt": f"{image.get('image_prompt', '')}, {story_data.get('visual_theme', 'cinematic storytelling')}, professional quality",
                    "image_duration": img_duration,
                    "start_time": cumulative_time,
                    "end_time": cumulative_time + img_duration,
                    "visual_focus": image.get("visual_focus", "story element")
                })
                cumulative_time += img_duration
        else:
            # Default single image for segment
            processed_images = [{
                "image_number": 1,
                "image_prompt": f"{topic}, {segment.get('emotional_tone', 'narrative')}, cinematic storytelling, professional quality",
                "image_duration": segment_duration,
                "start_time": 0,
                "end_time": segment_duration,
                "visual_focus": "main story element"
            }]
        
        processed_segment = {
            "segment_number": i + 1,
            "segment_type": segment.get("segment_type", "narrative"),
            "text": segment_text,
            "character_speaking": segment.get("character_speaking"),
            "images": processed_images,
            "caption_text": segment.get("caption_text", segment_text[:60] + "..." if len(segment_text) > 60 else segment_text),
            "story_purpose": segment.get("story_purpose", f"Story development segment {i+1}"),
            "emotional_tone": segment.get("emotional_tone", "neutral"),
            "transition_to_next": segment.get("transition_to_next", "smooth transition"),
            "duration_seconds": segment_duration,
            "start_time": total_duration,
            "end_time": total_duration + segment_duration,
            "word_count": len(segment_text.split()),
            "image_count": len(processed_images)
        }
        
        processed_segments.append(processed_segment)
        full_text_parts.append(segment_text)
        total_duration += segment_duration
    
    return {
        "story_title": story_data.get("story_title", f"The Story of {topic.title()}"),
        "story_summary": story_data.get("story_summary", f"An engaging story about {topic}"),
        "characters": story_data.get("characters", []),
        "full_text": " ".join(full_text_parts),
        "segments": processed_segments,
        "total_segments": len(processed_segments),
        "estimated_duration": total_duration,
        "script_length": script_length,
        "topic": topic,
        "visual_theme": story_data.get("visual_theme", "cinematic storytelling"),
        "target_emotion": story_data.get("target_emotion", "engagement"),
        "video_style": story_data.get("video_style", "cinematic narrative"),
        "total_images": sum(len(s["images"]) for s in processed_segments),
        "has_dialogs": any(s.get("character_speaking") for s in processed_segments),
        "generated_at": datetime.now().isoformat(),
        "generator": "story_enhanced"
    }

def generate_fallback_story(topic: str, script_length: str, config: Dict, include_dialogs: bool) -> Dict[str, Any]:
    """Generate an enhanced fallback story with creative content when Gemini fails"""
    
    print(f"[FALLBACK] Creating enhanced story for '{topic}'...")
    
    segments = []
    total_duration = 0
    segment_count = config['segments'][0]
    
    # Create topic-specific creative stories
    creative_stories = create_topic_specific_story(topic, segment_count, include_dialogs)
    
    characters = [{"name": "Narrator", "description": "Story narrator", "role": "narrator"}]
    if include_dialogs and topic in ["cat and dog friendship", "friendship", "animals"]:
        characters.extend([
            {"name": "Cat", "description": "Curious and independent feline", "role": "protagonist"},
            {"name": "Dog", "description": "Loyal and energetic canine", "role": "protagonist"}
        ])
    
    for i in range(segment_count):
        story_info = creative_stories[i] if i < len(creative_stories) else creative_stories[-1]
        
        duration = 6.0 + (i * 2)  # Variable durations: 6s, 8s, 10s, etc.
        
        segment = {
            "segment_number": i + 1,
            "segment_type": story_info.get("type", "narrative"),
            "text": story_info["text"],
            "character_speaking": story_info.get("character"),
            "images": [{
                "image_number": 1,
                "image_prompt": story_info["image_prompt"],
                "image_duration": duration,
                "start_time": 0,
                "end_time": duration,
                "visual_focus": story_info["visual_focus"]
            }],
            "caption_text": story_info["caption"],
            "story_purpose": story_info["purpose"],
            "emotional_tone": story_info["emotion"],
            "transition_to_next": "smooth cinematic transition",
            "duration_seconds": duration,
            "start_time": total_duration,
            "end_time": total_duration + duration,
            "word_count": len(story_info["text"].split()),
            "image_count": 1
        }
        
        segments.append(segment)
        total_duration += duration
    
    return {
        "story_title": f"The Heartwarming Tale of {topic.title()}",
        "story_summary": f"A touching story that explores the beautiful world of {topic}, filled with emotion and wonder.",
        "characters": characters,
        "full_text": " ".join([s["text"] for s in segments]),
        "segments": segments,
        "total_segments": len(segments),
        "estimated_duration": total_duration,
        "script_length": script_length,
        "topic": topic,
        "visual_theme": "heartwarming cinematic storytelling",
        "target_emotion": "warmth and connection",
        "video_style": "cinematic narrative with emotional depth",
        "total_images": sum(s["image_count"] for s in segments),
        "has_dialogs": include_dialogs and any(s.get("character_speaking") for s in segments),
        "generated_at": datetime.now().isoformat(),
        "generator": "enhanced_fallback"
    }

def create_topic_specific_story(topic: str, segment_count: int, include_dialogs: bool) -> List[Dict[str, Any]]:
    """Create creative, topic-specific story content"""
    
    # Father and son relationship story
    if ("father" in topic.lower() and "son" in topic.lower()) or ("dad" in topic.lower() and "son" in topic.lower()):
        stories = [
            {
                "text": "Every Saturday morning, young Michael would wake up early, excited to spend the day with his father. Today was special - they were going to build a treehouse together in the backyard oak tree.",
                "image_prompt": "A warm scene of a father and young son looking at blueprints together at a kitchen table, morning sunlight streaming through windows, heartwarming family moment, professional photography",
                "visual_focus": "Father and son planning together",
                "caption": "Weekend Plans",
                "purpose": "Introduction of father-son bond",
                "emotion": "anticipation",
                "type": "narrative"
            },
            {
                "text": "As they worked side by side, hammering nails and measuring boards, Michael's father patiently taught him each step. 'Measure twice, cut once,' he said with a gentle smile, his hands guiding his son's small fingers.",
                "image_prompt": "Close-up of a father's hands gently guiding his young son's hands while using tools, focused concentration, warm lighting, touching moment of teaching and learning",
                "visual_focus": "Teaching moment between generations",
                "caption": "Learning Together",
                "purpose": "Showing the teaching relationship",
                "emotion": "patient",
                "type": "narrative"
            },
            {
                "text": "When Michael made a mistake and felt discouraged, his father sat beside him on the wooden planks. 'You know what?' his dad said, 'Some of my best lessons came from my mistakes. That's how we grow stronger together.'",
                "image_prompt": "A touching scene of father and son sitting together on wooden planks, father's arm around son's shoulder, encouraging conversation, golden hour lighting, emotional depth",
                "visual_focus": "Comfort and encouragement",
                "caption": "Growing Stronger",
                "purpose": "Showing emotional support and wisdom",
                "emotion": "comforting",
                "type": "narrative"
            },
            {
                "text": "As the sun set, they stood back to admire their treehouse. It wasn't perfect, but it was theirs. Michael looked up at his father with pride, knowing that the memories they'd built today were even more precious than the wooden walls around them.",
                "image_prompt": "Father and son standing together admiring their completed treehouse at sunset, proud smiles, warm golden light, beautiful family moment, sense of accomplishment and love",
                "visual_focus": "Shared accomplishment and pride",
                "caption": "Built with Love",
                "purpose": "Resolution showing lasting bond",
                "emotion": "proud",
                "type": "narrative"
            }
        ]
    
    # Cat and dog friendship story  
    elif "cat" in topic.lower() and "dog" in topic.lower():
        stories = [
            {
                "text": "In a cozy suburban neighborhood, a curious orange tabby cat named Whiskers peered through the fence at the new neighbors. A golden retriever puppy had just moved in next door, wagging his tail enthusiastically.",
                "image_prompt": "A beautiful orange tabby cat looking through a white picket fence at a golden retriever puppy in a sunny suburban backyard, warm afternoon lighting, heartwarming scene, professional photography",
                "visual_focus": "First meeting between cat and dog",
                "caption": "New Neighbors",
                "purpose": "Introduction of main characters",
                "emotion": "curious",
                "type": "narrative"
            },
            {
                "text": "At first, Whiskers was cautious. Cats and dogs weren't supposed to be friends, right? But something about this puppy's gentle eyes and playful spirit made the cat pause and wonder. Maybe things could be different.",
                "image_prompt": "Close-up of a contemplative orange cat's expressive green eyes, with a blurred golden retriever in the background, soft focus, emotional depth, cinematic portrait",
                "visual_focus": "Cat's inner contemplation",
                "caption": "A Moment of Wonder",
                "purpose": "Character development and internal conflict",
                "emotion": "contemplative",
                "type": "narrative"
            },
            {
                "text": "One sunny morning, both animals found themselves in the garden chasing the same colorful butterfly. Their eyes met, and instead of conflict, they found joy in the shared moment of play and discovery.",
                "image_prompt": "A cat and dog playing together in a lush garden, both looking up at a colorful butterfly, golden sunlight filtering through trees, magical realism, joyful atmosphere",
                "visual_focus": "The breakthrough moment of connection",
                "caption": "Shared Joy",
                "purpose": "The turning point of friendship",
                "emotion": "joyful",
                "type": "narrative"
            },
            {
                "text": "From that day forward, Whiskers and the puppy, now called Buddy, became inseparable. They proved that friendship knows no boundaries, and that the most beautiful connections often come from the most unexpected places.",
                "image_prompt": "A heartwarming scene of an orange cat and golden retriever sleeping peacefully together under a large oak tree, sunset lighting, touching friendship, professional pet photography",
                "visual_focus": "Perfect friendship harmony",
                "caption": "Unbreakable Bond",
                "purpose": "Resolution and message about friendship",
                "emotion": "heartwarming",
                "type": "narrative"
            }
        ]
    
    # Space exploration story
    elif "space" in topic.lower():
        stories = [
            {
                "text": "Commander Sarah looked out of the spacecraft window at the vast expanse of stars, each one a distant sun with possibly worlds of its own. This was humanity's furthest journey into the cosmic unknown.",
                "image_prompt": "An astronaut looking out of a spacecraft window at a breathtaking view of stars and nebulae, cosmic beauty, science fiction realism, awe-inspiring vista",
                "visual_focus": "The wonder of space exploration",
                "caption": "Into the Unknown",
                "purpose": "Setting the scene for space adventure",
                "emotion": "awe",
                "type": "narrative"
            }
        ]
    
    # Default creative story structure
    else:
        stories = [
            {
                "text": f"In a world where {topic} held the key to extraordinary adventures, our story begins with a moment that would change everything. The morning sun cast long shadows as destiny prepared to unfold.",
                "image_prompt": f"A cinematic opening scene related to {topic}, dramatic lighting, wide establishing shot, film-quality composition, professional cinematography",
                "visual_focus": "Epic story beginning",
                "caption": "The Beginning",
                "purpose": "Epic story opening",
                "emotion": "anticipation",
                "type": "narrative"
            },
            {
                "text": f"As our journey into the realm of {topic} deepened, unexpected challenges and beautiful discoveries awaited around every corner. Each step forward revealed new mysteries and wonders.",
                "image_prompt": f"A detailed scene showcasing the beauty and complexity of {topic}, rich colors, emotional depth, artistic composition",
                "visual_focus": "Journey and discovery",
                "caption": "The Journey",
                "purpose": "Development and exploration",
                "emotion": "wonder",
                "type": "narrative"
            },
            {
                "text": f"In the end, our exploration of {topic} taught us that the most profound truths often lie in the simplest moments. What began as curiosity became a celebration of life's endless possibilities.",
                "image_prompt": f"A peaceful, conclusive scene related to {topic}, warm golden light, hopeful atmosphere, inspirational composition, uplifting mood",
                "visual_focus": "Resolution and wisdom",
                "caption": "The Truth",
                "purpose": "Meaningful conclusion",
                "emotion": "peaceful",
                "type": "narrative"
            }
        ]
    
    # Extend or trim to match segment count
    while len(stories) < segment_count:
        stories.append(stories[-1])  # Repeat last story if needed
    
    return stories[:segment_count]

if __name__ == "__main__":
    # Test with cat and dog friendship story
    result = generate_story_script("cat and dog friendship", "medium", True)
    print(json.dumps(result, indent=2))