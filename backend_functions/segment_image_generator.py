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

# Pollinations API configuration (use path-based prompt like tests)
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"

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
    
    # Clean and simply enhance the prompt to avoid over-complexity
    from .pollinations_images import clean_and_enhance_prompt
    enhanced_prompt = clean_and_enhance_prompt(image_prompt)
    
    # Generate filename
    timestamp = int(time.time())
    filename = f'seg_{segment_number:02d}_img_{image_number:02d}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg'
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Make request to Pollinations
        print(f"[IMAGE {segment_number}-{image_number}] Generating: {enhanced_prompt[:100]}...")

        import random
        import hashlib
        import urllib.parse

        # Generate unique seed for each image
        unique_string = f"{enhanced_prompt}_{segment_number}_{image_number}_{time.time()}_{uuid.uuid4().hex}"
        seed_hash = hashlib.md5(unique_string.encode()).hexdigest()
        unique_seed = int(seed_hash[:8], 16)

        # Model fallback list (aligned with tests and other module)
        models_to_try = ['flux', 'flux-realism', 'flux-anime', 'turbo']

        # Encode prompt into path (Pollinations expects path-based prompt)
        encoded_prompt = urllib.parse.quote(enhanced_prompt)

        response = None
        last_error = None
        for model_attempt in models_to_try:
            try:
                print(f"[IMAGE {segment_number}-{image_number}] Trying model: {model_attempt}")

                params = {
                    "width": 1024,
                    "height": 576,
                    "seed": unique_seed + models_to_try.index(model_attempt) * 1000,
                    "model": model_attempt,
                    "enhance": "true" if model_attempt in ['flux', 'flux-realism'] else "false",
                    "nologo": "true",
                    "nofeed": "true",
                    "safe": "true"
                }

                param_string = "&".join([f"{k}={v}" for k, v in params.items()])
                full_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}?{param_string}"

                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Cache-Control': 'no-cache',
                    'X-Request-ID': f"{uuid.uuid4().hex}_{model_attempt}",
                    'Accept': 'image/*,*/*;q=0.8'
                }

                response = requests.get(full_url, timeout=60, headers=headers)

                if response.status_code != 200:
                    last_error = f"HTTP {response.status_code}"
                    print(f"[IMAGE {segment_number}-{image_number}] {model_attempt} failed: {last_error}")
                    continue

                # Validate response content
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type and 'octet-stream' not in content_type:
                    last_error = f"Invalid content type: {content_type}"
                    print(f"[IMAGE {segment_number}-{image_number}] {model_attempt} failed: {last_error}")
                    continue

                content_length = len(response.content)
                if content_length < 1024:
                    last_error = f"Image too small: {content_length} bytes"
                    print(f"[IMAGE {segment_number}-{image_number}] {model_attempt} failed: {last_error}")
                    continue

                # If we got here, we have a valid response
                print(f"[IMAGE {segment_number}-{image_number}] Success with {model_attempt}")
                break

            except Exception as e:
                last_error = str(e)
                print(f"[IMAGE {segment_number}-{image_number}] {model_attempt} error: {last_error}")
                continue

        # If no successful response
        if not response or response.status_code != 200:
            return {"success": False, "error": f"All models failed. Last error: {last_error or 'unknown'}"}

        # Save image (use .png for consistency)
        filename = f'seg_{segment_number:02d}_img_{image_number:02d}_{timestamp}_{uuid.uuid4().hex[:8]}.png'
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'wb') as f:
            f.write(response.content)

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
    """Enhance image prompt with additional context and style, avoiding over-enhancement"""
    
    # Start with clean base prompt
    enhanced_prompt = base_prompt.strip()
    
    # Check if prompt already contains style elements to avoid duplication
    prompt_lower = enhanced_prompt.lower()
    
    # Only add emotional tone if not already present
    tone_modifiers = {
        "happy": "bright, joyful lighting",
        "sad": "soft, melancholy lighting", 
        "excited": "dynamic, energetic",
        "suspenseful": "dramatic shadows",
        "peaceful": "serene, calm lighting",
        "dramatic": "high contrast lighting",
        "romantic": "soft, warm lighting",
        "anger": "harsh, dramatic lighting",
        "defiance": "bold, determined lighting",
        "tragic": "dark, somber mood",
        "despair": "muted, sorrowful atmosphere"
    }
    
    # Add emotional tone only if not already described
    if emotional_tone in tone_modifiers and not any(word in prompt_lower for word in ["lighting", "mood", "atmosphere"]):
        enhanced_prompt += f", {tone_modifiers[emotional_tone]}"
    
    # Add minimal technical quality only if not already present
    if not any(word in prompt_lower for word in ["quality", "detailed", "professional", "resolution"]):
        enhanced_prompt += ", high quality, detailed"
    
    # Avoid adding style_prompt if it's already in base_prompt or if it would create duplicates
    if style_prompt and style_prompt.lower() not in prompt_lower:
        # Check for duplicates before adding
        style_parts = [part.strip() for part in style_prompt.split(',')]
        unique_parts = []
        for part in style_parts:
            if part.lower() not in prompt_lower and part not in unique_parts:
                unique_parts.append(part)
        
        if unique_parts:
            enhanced_prompt += f", {', '.join(unique_parts)}"
    
    return enhanced_prompt

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
