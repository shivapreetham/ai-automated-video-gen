"""
Intelligent Per-Segment Image Generation System
Generates contextually appropriate images for each story segment with proper timing
"""

import os
import json
import uuid
import requests
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Pollinations API configuration
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"

def generate_segment_images(script_data: Dict[str, Any], output_dir: str = ".", 
                          img_style_prompt: str = "cinematic, professional") -> Dict[str, Any]:
    """
    Generate contextually appropriate images for each script segment
    
    Args:
        script_data: Script data with segments and image specifications
        output_dir: Directory to save image files
        img_style_prompt: Style prompt to append to all images
    
    Returns:
        Dictionary with image files and metadata for each segment
    """
    
    segments = script_data.get("segments", [])
    if not segments:
        return {"success": False, "error": "No segments found in script data"}
    
    print(f"[SEGMENT IMAGES] Generating images for {len(segments)} segments...")
    
    # Calculate total images needed
    total_images = sum(len(segment.get("images", [])) for segment in segments)
    print(f"[SEGMENT IMAGES] Total images to generate: {total_images}")
    
    # Generate images for all segments
    image_results = []
    
    # Use ThreadPoolExecutor for concurrent generation
    with ThreadPoolExecutor(max_workers=4) as executor:
        future_to_info = {}
        
        for segment in segments:
            segment_images = segment.get("images", [])
            if not segment_images:
                continue
                
            for image_spec in segment_images:
                future = executor.submit(
                    generate_single_image,
                    segment,
                    image_spec,
                    output_dir,
                    img_style_prompt,
                    script_data.get("visual_theme", "cinematic storytelling")
                )
                future_to_info[future] = {
                    "segment_number": segment["segment_number"],
                    "image_number": image_spec["image_number"]
                }
        
        # Collect results as they complete
        for future in as_completed(future_to_info):
            info = future_to_info[future]
            try:
                result = future.result()
                result.update(info)
                image_results.append(result)
                print(f"[SEGMENT IMAGES] Completed segment {info['segment_number']}, image {info['image_number']}")
            except Exception as e:
                print(f"[SEGMENT IMAGES] Failed segment {info['segment_number']}, image {info['image_number']}: {e}")
                image_results.append({
                    **info,
                    "success": False,
                    "error": str(e)
                })
    
    # Sort results by segment and image number
    image_results.sort(key=lambda x: (x["segment_number"], x["image_number"]))
    
    # Group results by segment
    segments_with_images = group_images_by_segment(segments, image_results)
    
    # Calculate statistics
    successful_images = [r for r in image_results if r.get("success")]
    total_file_size = sum(r.get("file_size", 0) for r in successful_images)
    
    return {
        "success": len(successful_images) > 0,
        "images_generated": len(successful_images),
        "images_failed": len(image_results) - len(successful_images),
        "total_images_requested": total_images,
        "segments_with_images": segments_with_images,
        "total_file_size": total_file_size,
        "image_results": image_results,
        "generation_method": "pollinations_segments"
    }

def generate_single_image(segment: Dict[str, Any], image_spec: Dict[str, Any], 
                         output_dir: str, style_prompt: str, visual_theme: str) -> Dict[str, Any]:
    """Generate a single image for a segment"""
    
    segment_number = segment.get("segment_number", 1)
    image_number = image_spec.get("image_number", 1)
    image_prompt = image_spec.get("image_prompt", "")
    
    if not image_prompt:
        return {"success": False, "error": "Empty image prompt"}
    
    # Enhance prompt with context
    enhanced_prompt = enhance_image_prompt(
        image_prompt, 
        style_prompt, 
        visual_theme, 
        segment.get("emotional_tone", "neutral"),
        segment.get("segment_type", "narrative")
    )
    
    # Generate filename
    timestamp = int(time.time())
    filename = f'seg_{segment_number:02d}_img_{image_number:02d}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg'
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Make request to Pollinations
        print(f"[IMAGE {segment_number}-{image_number}] Generating: {enhanced_prompt[:100]}...")
        
        response = requests.get(
            POLLINATIONS_BASE_URL,
            params={
                "prompt": enhanced_prompt,
                "width": 1024,
                "height": 576,
                "seed": -1,  # Random seed
                "model": "flux",
                "enhance": "true"
            },
            timeout=60,
            stream=True
        )
        
        if response.status_code != 200:
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
        
        # Save image
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify image was saved
        if not os.path.exists(filepath):
            return {"success": False, "error": "Image file was not created"}
        
        file_size = os.path.getsize(filepath)
        if file_size < 1000:  # Less than 1KB likely means error
            return {"success": False, "error": f"Generated image too small ({file_size} bytes)"}
        
        print(f"[IMAGE {segment_number}-{image_number}] Generated: {filename} ({file_size/1024:.1f} KB)")
        
        return {
            "success": True,
            "image_file": filepath,
            "filename": filename,
            "file_size": file_size,
            "original_prompt": image_prompt,
            "enhanced_prompt": enhanced_prompt,
            "image_duration": image_spec.get("image_duration", 5.0),
            "start_time": image_spec.get("start_time", 0),
            "end_time": image_spec.get("end_time", 5.0),
            "visual_focus": image_spec.get("visual_focus", ""),
            "generation_time": time.time() - timestamp
        }
        
    except requests.exceptions.RequestException as e:
        return {"success": False, "error": f"Network error: {e}"}
    except Exception as e:
        return {"success": False, "error": f"Generation error: {e}"}

def enhance_image_prompt(base_prompt: str, style_prompt: str, visual_theme: str, 
                        emotional_tone: str, segment_type: str) -> str:
    """Enhance image prompt with additional context and style"""
    
    # Emotional tone modifiers
    tone_modifiers = {
        "happy": "bright, joyful, warm lighting, vibrant colors",
        "sad": "soft lighting, muted colors, melancholy atmosphere", 
        "excited": "dynamic, energetic, bright colors, motion blur",
        "suspenseful": "dramatic lighting, shadows, tense atmosphere",
        "peaceful": "serene, calm, soft lighting, harmonious colors",
        "dramatic": "high contrast, cinematic lighting, intense mood",
        "neutral": "balanced lighting, natural colors"
    }
    
    # Segment type modifiers
    type_modifiers = {
        "narrative": "wide shot, establishing scene, detailed environment",
        "dialog": "medium shot, character focus, expressive lighting",
        "mixed": "dynamic composition, balanced framing"
    }
    
    # Build enhanced prompt
    prompt_parts = [base_prompt]
    
    # Add visual theme
    if visual_theme:
        prompt_parts.append(visual_theme)
    
    # Add style prompt
    if style_prompt:
        prompt_parts.append(style_prompt)
    
    # Add emotional tone modifier
    if emotional_tone in tone_modifiers:
        prompt_parts.append(tone_modifiers[emotional_tone])
    
    # Add segment type modifier
    if segment_type in type_modifiers:
        prompt_parts.append(type_modifiers[segment_type])
    
    # Add technical quality markers
    prompt_parts.extend([
        "high quality",
        "detailed",
        "4k resolution",
        "professional photography"
    ])
    
    return ", ".join(prompt_parts)

def group_images_by_segment(segments: List[Dict[str, Any]], 
                           image_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group image results back by segment"""
    
    segments_with_images = []
    
    for segment in segments:
        segment_number = segment["segment_number"]
        segment_images = [r for r in image_results if r["segment_number"] == segment_number]
        
        # Sort by image number
        segment_images.sort(key=lambda x: x["image_number"])
        
        segment_data = {
            "segment_number": segment_number,
            "segment_text": segment.get("text", ""),
            "segment_type": segment.get("segment_type", "narrative"),
            "emotional_tone": segment.get("emotional_tone", "neutral"),
            "duration_seconds": segment.get("duration_seconds", 5.0),
            "images": segment_images,
            "image_count": len(segment_images),
            "successful_images": len([r for r in segment_images if r.get("success")]),
            "failed_images": len([r for r in segment_images if not r.get("success")])
        }
        
        segments_with_images.append(segment_data)
    
    return segments_with_images

def generate_fallback_image(segment: Dict[str, Any], image_spec: Dict[str, Any], 
                           output_dir: str) -> Dict[str, Any]:
    """Generate a simple fallback image if main generation fails"""
    
    # This could be implemented to generate a simple colored background
    # or use a local image generation fallback
    return {"success": False, "error": "Fallback image generation not implemented"}

def validate_generated_images(segments_with_images: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Validate that all segments have at least one successful image"""
    
    validation_results = {
        "all_segments_have_images": True,
        "segments_without_images": [],
        "total_segments": len(segments_with_images),
        "segments_with_all_images": 0,
        "segments_with_partial_images": 0
    }
    
    for segment_data in segments_with_images:
        segment_number = segment_data["segment_number"]
        successful_count = segment_data["successful_images"]
        total_count = segment_data["image_count"]
        
        if successful_count == 0:
            validation_results["all_segments_have_images"] = False
            validation_results["segments_without_images"].append(segment_number)
        elif successful_count == total_count:
            validation_results["segments_with_all_images"] += 1
        else:
            validation_results["segments_with_partial_images"] += 1
    
    return validation_results

if __name__ == "__main__":
    # Test with sample script data
    sample_script = {
        "visual_theme": "heartwarming friendship story",
        "segments": [
            {
                "segment_number": 1,
                "text": "In a sunny backyard, a playful golden retriever named Buddy discovers a small orange kitten hiding under a bush.",
                "segment_type": "narrative",
                "emotional_tone": "curious",
                "duration_seconds": 8.0,
                "images": [
                    {
                        "image_number": 1,
                        "image_prompt": "A sunny backyard with a golden retriever looking curiously at a small orange kitten under a green bush",
                        "image_duration": 4.0,
                        "start_time": 0,
                        "end_time": 4.0,
                        "visual_focus": "First meeting between dog and cat"
                    },
                    {
                        "image_number": 2,
                        "image_prompt": "Close-up of the orange kitten's expressive eyes looking cautiously at the friendly dog",
                        "image_duration": 4.0,
                        "start_time": 4.0,
                        "end_time": 8.0,
                        "visual_focus": "Kitten's cautious reaction"
                    }
                ]
            }
        ]
    }
    
    result = generate_segment_images(sample_script, ".", "cinematic, professional")
    print(json.dumps(result, indent=2))