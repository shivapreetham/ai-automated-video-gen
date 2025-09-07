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

# Pollinations API configuration (correct URL format with trailing slash)
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"

def generate_segment_images(script_data: Dict[str, Any], output_dir: str = ".", 
                          img_style_prompt: str = "cinematic, professional") -> Dict[str, Any]:
    """
    Generate ONE image per segment for consistent video generation
    
    Args:
        script_data: Script data with segments
        output_dir: Directory to save image files
        img_style_prompt: Style prompt to append to all images
    
    Returns:
        Dictionary with image files and metadata for each segment
    """
    
    segments = script_data.get("segments", [])
    if not segments:
        return {"success": False, "error": "No segments found in script data"}
    
    print(f"[SEGMENT IMAGES] Generating ONE image per segment for {len(segments)} segments...")
    
    # Generate images sequentially (no concurrency to avoid conflicts)
    image_results = []
    
    for segment in segments:
        segment_number = segment.get("segment_number", 1)
        
        # Use the first image prompt or create one from segment text
        if segment.get("images") and len(segment["images"]) > 0:
            image_prompt = segment["images"][0].get("image_prompt", "")
        else:
            # Fallback to segment text if no image prompt
            image_prompt = segment.get("text", f"Scene for segment {segment_number}")
        
        print(f"[SEGMENT {segment_number}] Generating single image...")
        
        try:
            result = generate_single_image_simplified(
                segment,
                image_prompt,
                output_dir,
                img_style_prompt,
                script_data.get("visual_theme", "cinematic storytelling")
            )
            result["segment_number"] = segment_number
            result["image_number"] = 1  # Always 1 since we only generate one per segment
            image_results.append(result)
            
            if result.get("success"):
                print(f"[SEGMENT {segment_number}] Success: {result.get('filename', 'unknown')}")
            else:
                print(f"[SEGMENT {segment_number}] Failed: {result.get('error', 'unknown error')}")
                
        except Exception as e:
            print(f"[SEGMENT {segment_number}] Exception: {e}")
            image_results.append({
                "segment_number": segment_number,
                "image_number": 1,
                "success": False,
                "error": str(e)
            })
    
    # Group results by segment (simplified since each segment has only one image)
    segments_with_images = group_images_by_segment_simplified(segments, image_results)
    
    # Calculate statistics
    successful_images = [r for r in image_results if r.get("success")]
    total_file_size = sum(r.get("file_size", 0) for r in successful_images)
    
    return {
        "success": len(successful_images) > 0,
        "images_generated": len(successful_images),
        "images_failed": len(image_results) - len(successful_images),
        "total_images_requested": len(segments),
        "segments_with_images": segments_with_images,
        "total_file_size": total_file_size,
        "image_results": image_results,
        "generation_method": "single_image_per_segment"
    }

def generate_single_image_simplified(segment: Dict[str, Any], image_prompt: str,
                                   output_dir: str, style_prompt: str, visual_theme: str) -> Dict[str, Any]:
    """Generate a single image for a segment - using correct URL format"""
    
    segment_number = segment.get("segment_number", 1)
    
    if not image_prompt.strip():
        return {"success": False, "error": "Empty image prompt"}
    
    enhanced_prompt = clean_prompt_simple(image_prompt)
    print(f"[SEGMENT {segment_number}] Generating: {enhanced_prompt[:100]}...")
    
    # Generate filename
    timestamp = int(time.time())
    filename = f'segment_{segment_number:02d}_{timestamp}_{uuid.uuid4().hex[:8]}.png'
    filepath = os.path.join(output_dir, filename)
    
    try:
        import random
        import hashlib
        import urllib.parse
        
        # Generate unique seed like the working test
        unique_string = f"{enhanced_prompt}_{segment_number}_{time.time()}_{uuid.uuid4().hex}"
        seed_hash = hashlib.md5(unique_string.encode()).hexdigest()
        seed = int(seed_hash[:8], 16)
        
        # Build parameters like the working test
        params = {
            'width': 1024,
            'height': 576,
            'model': 'flux',
            'seed': seed,
            'nologo': 'true',
            'nofeed': 'true',
            'safe': 'true',
            'enhance': 'true'  # Enable enhancement for flux model
        }
        
        # Encode prompt for URL path (like working test)
        encoded_prompt = urllib.parse.quote(enhanced_prompt)
        param_string = "&".join([f"{k}={v}" for k, v in params.items()])
        full_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}?{param_string}"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Cache-Control': 'no-cache',
            'X-Request-ID': f"{uuid.uuid4().hex}_segment_{segment_number}"
        }
        
        response = requests.get(full_url, timeout=60, headers=headers)
        
        if response.status_code != 200:
            raise Exception(f"HTTP {response.status_code}")
        
        # Check content type
        content_type = response.headers.get('content-type', '').lower()
        if 'image' not in content_type and 'octet-stream' not in content_type:
            raise Exception(f"Invalid content type: {content_type}")
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        # Validate image
        if not os.path.exists(filepath):
            raise Exception("Image file was not created")
        
        file_size = os.path.getsize(filepath)
        if file_size < 1024:  # Less than 1KB likely means error
            raise Exception(f"Generated image too small ({file_size} bytes)")
        
        print(f"[SEGMENT {segment_number}] SUCCESS: {filename} ({file_size/1024:.1f}KB)")
        
        return {
            "success": True,
            "image_file": filepath,
            "filename": filename,
            "file_size": file_size,
            "original_prompt": image_prompt,
            "enhanced_prompt": enhanced_prompt,
            "image_duration": segment.get("duration_seconds", 5.0),  # Video creator expects this field
            "segment_duration": segment.get("duration_seconds", 5.0),
            "generation_time": time.time() - timestamp
        }
        
    except Exception as e:
        print(f"[SEGMENT {segment_number}] Generation failed: {e}, creating fallback...")
        return generate_fallback_image_simple(segment_number, image_prompt, output_dir)

def clean_prompt_simple(prompt: str) -> str:
    """Simple prompt cleaning without over-complication"""
    clean_prompt = ' '.join(prompt.strip().split())
    
    # Only add minimal quality if prompt is very short
    if len(clean_prompt) < 30 and 'quality' not in clean_prompt.lower():
        clean_prompt += ", high quality"
    
    return clean_prompt

def generate_fallback_image_simple(segment_number: int, image_prompt: str, output_dir: str) -> Dict[str, Any]:
    """Generate simple fallback image"""
    try:
        from PIL import Image, ImageDraw, ImageFont
        
        width, height = 1024, 576
        img = Image.new('RGB', (width, height), color=(40, 40, 40))
        draw = ImageDraw.Draw(img)
        
        text = f"Segment {segment_number}\n{image_prompt[:60]}..."
        
        try:
            font = ImageFont.truetype("arial.ttf", size=24)
        except:
            font = ImageFont.load_default()
        
        # Calculate text position
        text_bbox = draw.multiline_textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        
        x = (width - text_width) // 2
        y = (height - text_height) // 2
        
        draw.multiline_text((x, y), text, fill=(200, 200, 200), font=font, align="center")
        
        filename = f"fallback_segment_{segment_number:02d}_{uuid.uuid4().hex[:8]}.png"
        filepath = os.path.join(output_dir, filename)
        img.save(filepath)
        
        return {
            "success": True,
            "image_file": filepath,
            "filename": filename,
            "file_size": os.path.getsize(filepath),
            "original_prompt": image_prompt,
            "enhanced_prompt": image_prompt,
            "image_duration": 5.0,  # Video creator expects this field
            "segment_duration": 5.0,
            "generation_time": 0.0,
            "is_fallback": True
        }
        
    except Exception as e:
        return {"success": False, "error": f"Fallback creation failed: {e}"}

def group_images_by_segment_simplified(segments: List[Dict[str, Any]], 
                                     image_results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Group image results by segment - compatible with video creator"""
    
    segments_with_images = []
    
    for segment in segments:
        segment_number = segment["segment_number"]
        segment_result = next((r for r in image_results if r["segment_number"] == segment_number), None)
        
        # Convert single image result to list format for compatibility
        if segment_result and segment_result.get("success"):
            images_list = [segment_result]  # Put single image in a list
            successful_images = 1
            failed_images = 0
        else:
            images_list = []
            successful_images = 0
            failed_images = 1 if segment_result else 0
        
        segment_data = {
            "segment_number": segment_number,
            "segment_text": segment.get("text", ""),
            "segment_type": segment.get("segment_type", "narrative"),
            "emotional_tone": segment.get("emotional_tone", "neutral"),
            "duration_seconds": segment.get("duration_seconds", 5.0),
            "images": images_list,  # List format for video creator compatibility
            "image_count": len(images_list),
            "successful_images": successful_images,
            "failed_images": failed_images
        }
        
        segments_with_images.append(segment_data)
    
    return segments_with_images

def generate_single_image(segment: Dict[str, Any], image_spec: Dict[str, Any], 
                         output_dir: str, style_prompt: str, visual_theme: str) -> Dict[str, Any]:
    """Generate a single image for a segment"""
    
    segment_number = segment.get("segment_number", 1)
    image_number = image_spec.get("image_number", 1)
    image_prompt = image_spec.get("image_prompt", "")
    
    if not image_prompt:
        return {"success": False, "error": "Empty image prompt"}
    
    # Clean/enhance can be disabled via env to avoid meddling
    use_raw = str(os.getenv("POLLINATIONS_USE_RAW_PROMPT", "")).lower() in ("1", "true", "yes")
    if use_raw:
        enhanced_prompt = image_prompt.strip()
    else:
        # Clean and simply enhance the prompt to avoid over-complexity
        from .pollinations_images import clean_and_enhance_prompt
        enhanced_prompt = clean_and_enhance_prompt(image_prompt)
    print(f"[IMAGE {segment_number}-{image_number}] Using prompt: {enhanced_prompt[:120]}")
    
    # Generate filename
    timestamp = int(time.time())
    filename = f'seg_{segment_number:02d}_img_{image_number:02d}_{timestamp}_{uuid.uuid4().hex[:8]}.jpg'
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Make request to Pollinations
        print(f"[IMAGE {segment_number}-{image_number}] Generating: {enhanced_prompt[:100]}...")

        import random
        import hashlib

        # Generate unique seed for each image
        unique_string = f"{enhanced_prompt}_{segment_number}_{image_number}_{time.time()}_{uuid.uuid4().hex}"
        seed_hash = hashlib.md5(unique_string.encode()).hexdigest()
        unique_seed = int(seed_hash[:8], 16)

        # Model fallback list
        models_to_try = ['flux', 'flux-realism', 'turbo']

        response = None
        last_error = None
        for model_attempt in models_to_try:
            try:
                print(f"[IMAGE {segment_number}-{image_number}] Trying model: {model_attempt}")

                response = requests.get(
                    POLLINATIONS_BASE_URL,
                    params={
                        "prompt": enhanced_prompt,
                        "width": 1024,
                        "height": 576,
                        "seed": unique_seed + models_to_try.index(model_attempt) * 1000,
                        "model": model_attempt,
                        "enhance": "true" if model_attempt in ['flux', 'flux-realism'] else "false",
                        "nologo": "true",
                        "nofeed": "true"
                    },
                    timeout=60,
                    headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                        'Cache-Control': 'no-cache',
                        'X-Request-ID': f"{uuid.uuid4().hex}_{model_attempt}"
                    },
                    stream=True
                )

                if response.status_code == 200:
                    print(f"[IMAGE {segment_number}-{image_number}] Success with {model_attempt}")
                    break
                else:
                    last_error = f"HTTP {response.status_code}"
                    print(f"[IMAGE {segment_number}-{image_number}] {model_attempt} failed: {last_error}")
                    continue

            except Exception as e:
                last_error = str(e)
                print(f"[IMAGE {segment_number}-{image_number}] {model_attempt} error: {last_error}")
                continue

        # If no successful response – create fallback image and continue
        if not response or response.status_code != 200:
            fallback_info = generate_fallback_image(
                segment,
                image_spec,
                output_dir
            )
            if fallback_info.get("success"):
                fallback_info.update({
                    "original_prompt": image_prompt,
                    "enhanced_prompt": enhanced_prompt,
                    "is_fallback": True,
                })
                return fallback_info
            return {"success": False, "error": f"All models failed. Last error: {last_error or 'unknown'}"}

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
        # Create fallback on network error
        print(f"[IMAGE {segment_number}-{image_number}] Network error, using fallback: {e}")
        fallback_info = generate_fallback_image(segment, image_spec, output_dir)
        if fallback_info.get("success"):
            fallback_info.update({
                "original_prompt": image_prompt,
                "enhanced_prompt": enhanced_prompt,
                "is_fallback": True,
            })
            return fallback_info
        return {"success": False, "error": f"Network error: {e}"}
    except Exception as e:
        # Create fallback on generic error
        print(f"[IMAGE {segment_number}-{image_number}] Error, using fallback: {e}")
        fallback_info = generate_fallback_image(segment, image_spec, output_dir)
        if fallback_info.get("success"):
            fallback_info.update({
                "original_prompt": image_prompt,
                "enhanced_prompt": enhanced_prompt,
                "is_fallback": True,
            })
            return fallback_info
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
    try:
        from .pollinations_images import create_fallback_image
    except Exception:
        create_fallback_image = None

    segment_number = segment.get("segment_number", 1)
    image_number = image_spec.get("image_number", 1)
    image_prompt = image_spec.get("image_prompt", "")

    width = 1024
    height = 576

    try:
        if create_fallback_image:
            path = create_fallback_image(image_prompt, width, height, output_dir, segment_number)
        else:
            # Local minimal fallback
            from PIL import Image, ImageDraw, ImageFont
            img = Image.new('RGB', (width, height), color=(60, 60, 60))
            draw = ImageDraw.Draw(img)
            text = f"Seg {segment_number} Img {image_number}\n{image_prompt[:70]}" if image_prompt else f"Seg {segment_number} Img {image_number}"
            try:
                font = ImageFont.truetype("arial.ttf", size=22)
            except:
                font = ImageFont.load_default()
            # Center text
            w, h = draw.multiline_textbbox((0, 0), text, font=font)[2:]
            draw.multiline_text(((width - w)//2, (height - h)//2), text, fill=(230, 230, 230), font=font, align="center")
            filename = f"fallback_seg_{segment_number:02d}_img_{image_number:02d}_{uuid.uuid4().hex[:8]}.png"
            path = os.path.join(output_dir, filename)
            img.save(path)

        if not os.path.exists(path):
            return {"success": False, "error": "Fallback image could not be created"}

        size = os.path.getsize(path)
        print(f"[IMAGE {segment_number}-{image_number}] Fallback image created: {os.path.basename(path)} ({size/1024:.1f} KB)")
        return {
            "success": True,
            "image_file": path,
            "filename": os.path.basename(path),
            "file_size": size,
            "image_duration": image_spec.get("image_duration", 5.0),
            "start_time": image_spec.get("start_time", 0),
            "end_time": image_spec.get("end_time", 5.0),
            "visual_focus": image_spec.get("visual_focus", ""),
            "generation_time": 0.0
        }
    except Exception as e:
        return {"success": False, "error": f"Fallback generation error: {e}"}

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
