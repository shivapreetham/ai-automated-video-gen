"""
Pollinations Image Generation - Independent Backend Function
Generates multiple images based on script segments
"""

import os
import requests
import urllib.parse
import uuid
import time
import random
from typing import List, Dict, Any
from PIL import Image

# Always use query-param `prompt` (no path embedding)
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt"

def generate_images(segments: List[Dict], width: int = 1024, height: int = 576, output_dir: str = ".", model: str = 'flux') -> Dict[str, Any]:
    """
    Generate multiple images for script segments
    
    Args:
        segments: List of segments with image_prompt field
        width, height: Image dimensions
        output_dir: Where to save images
    
    Returns:
    {
        "success": True,
        "images": [
            {"segment": 1, "image_file": "/path/to/image1.png", "prompt": "..."},
            {"segment": 2, "image_file": "/path/to/image2.png", "prompt": "..."},
        ],
        "total_generated": 5,
        "failed_generations": 0
    }
    """
    
    print(f"[IMAGES] Generating {len(segments)} images...")
    
    generated_images = []
    failed_count = 0
    
    for i, segment in enumerate(segments):
        segment_num = segment.get("segment_number", i + 1)
        prompt = segment.get("image_prompt", f"Image for segment {segment_num}")
        
        print(f"[IMAGE {segment_num}/{len(segments)}] Generating: {prompt[:50]}...")
        
        try:
            image_file = generate_single_image(prompt, width, height, output_dir, segment_num, model)
            
            if image_file:
                generated_images.append({
                    "segment": segment_num,
                    "image_file": image_file,
                    "prompt": prompt,
                    "text": segment.get("text", ""),
                    "caption_text": segment.get("caption_text", ""),
                    "focus": segment.get("focus", ""),
                    "success": True
                })
                print(f"[IMAGE {segment_num}] Generated: {os.path.basename(image_file)}")
            else:
                raise Exception("Image generation returned None")
                
        except Exception as e:
            print(f"[IMAGE {segment_num}] Failed: {e}")
            failed_count += 1
            
            # Create fallback image
            fallback_file = create_fallback_image(prompt, width, height, output_dir, segment_num)
            generated_images.append({
                "segment": segment_num,
                "image_file": fallback_file,
                "prompt": prompt,
                "text": segment.get("text", ""),
                "caption_text": segment.get("caption_text", ""),
                "focus": segment.get("focus", ""),
                "success": False,
                "error": str(e)
            })
    
    return {
        "success": len(generated_images) > 0,
        "images": generated_images,
        "total_generated": len(generated_images),
        "failed_generations": failed_count,
        "success_rate": f"{((len(generated_images) - failed_count) / len(segments)) * 100:.1f}%"
    }

def generate_single_image(prompt: str, width: int, height: int, output_dir: str, segment_num: int, model: str = 'flux') -> str:
    """Generate a single image using Pollinations API with model fallback"""
    
    # Generate a unique seed based on prompt, segment number and timestamp
    import hashlib
    unique_string = f"{prompt}_{segment_num}_{time.time()}_{uuid.uuid4().hex}_{random.randint(1000000, 9999999)}"
    seed_hash = hashlib.md5(unique_string.encode()).hexdigest()
    seed = int(seed_hash[:8], 16)  # Use first 8 hex chars as seed
    
    # Ensure seed is in valid range (avoid very small numbers)
    seed = max(seed, 100000)
    
    # Model fallback list (rotate starting from requested model)
    model_fallbacks = ['flux', 'flux-realism', 'flux-anime', 'flux-3d', 'turbo']
    if model not in model_fallbacks:
        model = 'flux'

    start_idx = model_fallbacks.index(model)
    models_to_try = model_fallbacks[start_idx:] + model_fallbacks[:start_idx]

    # Allow raw prompt via env to avoid meddling
    use_raw = str(os.getenv("POLLINATIONS_USE_RAW_PROMPT", "")).lower() in ("1", "true", "yes")
    enhanced_prompt = prompt.strip() if use_raw else clean_and_enhance_prompt(prompt)
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    
    # Force query-param mode
    use_query = True
    
    # Try each model in fallback order
    for current_model in models_to_try:
        
        # Build URL with parameters
        params = {
            'width': min(max(width, 512), 1920),
            'height': min(max(height, 512), 1920), 
            'model': current_model,
            'seed': seed + model_fallbacks.index(current_model) * 1000,  # Different seed per model
            'nologo': 'true',
            'enhance': 'true' if current_model in ['flux', 'flux-realism'] else 'false',
            'nofeed': 'true',  # Prevent caching issues
            'safe': 'true'
        }
    
        if use_query:
            full_url = POLLINATIONS_BASE_URL.rstrip('/')
            request_kwargs = {"params": {**params, "prompt": enhanced_prompt}}
        else:
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}?{param_string}"
            request_kwargs = {}
        
        print(f"[MODEL] Trying {current_model} with seed {params['seed']}...")
        
        # Make request with retries for this model
        for attempt in range(2):  # Reduced retries per model
            try:
                # Randomize user agent to prevent caching
                user_agents = [
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0'
                ]
                headers = {
                    'User-Agent': random.choice(user_agents),
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache',
                    'X-Request-ID': f"{uuid.uuid4().hex}_{current_model}_{attempt}",
                    'Accept': 'image/*,*/*;q=0.8'
                }
                
                if use_query:
                    response = requests.get(full_url, timeout=45, headers=headers, **request_kwargs)
                else:
                    response = requests.get(full_url, timeout=45, headers=headers)
                response.raise_for_status()
                
                # Check content type
                content_type = response.headers.get('content-type', '').lower()
                if 'image' not in content_type and 'octet-stream' not in content_type:
                    raise Exception(f"Invalid content type: {content_type}")
                
                # Check content length
                content_length = len(response.content)
                if content_length < 1024:  # Less than 1KB
                    raise Exception(f"Image too small: {content_length} bytes")
                
                # Save image
                filename = f"segment_{segment_num:02d}_{current_model}_{uuid.uuid4().hex[:8]}.png"
                filepath = os.path.join(output_dir, filename)
                
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Validate image
                if validate_image(filepath, width, height):
                    print(f"[SUCCESS] Image generated with {current_model}")
                    return filepath
                else:
                    if os.path.exists(filepath):
                        os.remove(filepath)
                    raise Exception("Image validation failed")
                    
            except Exception as e:
                print(f"[WARNING] {current_model} attempt {attempt + 1} failed: {e}")
                if attempt < 1:  # Not the last attempt for this model
                    time.sleep(2 + attempt)
                continue
        
        print(f"[FAILED] Model {current_model} failed after all attempts")
    
    # All models failed, raise final exception
    raise Exception(f"All models failed for segment {segment_num}")

def validate_image(filepath: str, target_width: int, target_height: int) -> bool:
    """Validate generated image"""
    try:
        with Image.open(filepath) as img:
            width, height = img.size
            
            # Check minimum size
            if width < 256 or height < 256:
                return False
            
            # Check if not corrupted
            img.verify()
            
        return True
    except:
        return False

def clean_overly_complex_prompt(prompt: str) -> str:
    """Clean up overly complex prompts that confuse the AI"""
    
    # Remove excessive whitespace and normalize
    clean_prompt = ' '.join(prompt.split())
    
    # Remove duplicate phrases (common issue)
    parts = [part.strip() for part in clean_prompt.split(',')]
    seen = set()
    unique_parts = []
    
    for part in parts:
        part_lower = part.lower()
        if part_lower not in seen and part.strip():
            seen.add(part_lower)
            unique_parts.append(part.strip())
    
    # Limit to most important parts (first 4-5 concepts)
    if len(unique_parts) > 5:
        # Keep the main subject (first part) and most important modifiers
        main_subject = unique_parts[0]
        important_modifiers = [part for part in unique_parts[1:] if any(key in part.lower() for key in 
                             ['lighting', 'shot', 'view', 'close-up', 'wide', 'medium'])][:2]
        quality_terms = [part for part in unique_parts[1:] if any(key in part.lower() for key in 
                        ['quality', 'professional', 'detailed', 'resolution'])][:1]
        
        unique_parts = [main_subject] + important_modifiers + quality_terms
    
    return ', '.join(unique_parts)

def clean_and_enhance_prompt(prompt: str) -> str:
    """Simple, clean prompt enhancement without over-complication"""
    
    # First clean up overly complex prompts
    clean_prompt = clean_overly_complex_prompt(prompt)
    
    # Check if already has quality descriptors
    prompt_lower = clean_prompt.lower()
    has_quality = any(word in prompt_lower for word in 
                     ['professional', 'quality', 'detailed', 'resolution', '4k', '8k', 'hd'])
    has_lighting = any(word in prompt_lower for word in 
                      ['lighting', 'light', 'illuminated', 'glow', 'bright', 'dark'])
    
    enhancements = []
    
    # Add minimal quality enhancement if needed
    if not has_quality:
        enhancements.append("high quality")
    
    # Add simple lighting if needed  
    if not has_lighting and len(clean_prompt.split(',')) < 4:  # Only if prompt isn't already complex
        simple_lighting = ["natural lighting", "good lighting", "cinematic lighting"]
        enhancements.append(random.choice(simple_lighting))
    
    # Combine cleanly
    if enhancements:
        return f"{clean_prompt}, {', '.join(enhancements)}"
    else:
        return clean_prompt

def create_fallback_image(prompt: str, width: int, height: int, output_dir: str, segment_num: int) -> str:
    """Create a fallback image if generation fails"""
    from PIL import ImageDraw, ImageFont
    
    # Create colored background
    colors = [(70, 130, 180), (60, 179, 113), (205, 92, 92), (238, 130, 238), (255, 165, 0)]
    color = random.choice(colors)
    
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        font_size = min(width, height) // 15
        font = ImageFont.truetype("arial.ttf", size=font_size)
    except:
        font = ImageFont.load_default()
    
    text = f"Segment {segment_num}\n{prompt[:60]}..."
    
    # Draw text with background
    lines = text.split('\n')
    line_height = font_size + 5
    total_height = len(lines) * line_height
    
    y_start = (height - total_height) // 2
    
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        text_width = bbox[2] - bbox[0]
        x = (width - text_width) // 2
        y = y_start + i * line_height
        
        # Draw text with outline
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            draw.text((x + dx, y + dy), line, fill="black", font=font)
        draw.text((x, y), line, fill="white", font=font)
    
    # Save fallback image
    filename = f"fallback_segment_{segment_num:02d}_{uuid.uuid4().hex[:8]}.png"
    filepath = os.path.join(output_dir, filename)
    img.save(filepath)
    
    return filepath

if __name__ == "__main__":
    # Test
    test_segments = [
        {"segment_number": 1, "image_prompt": "A beautiful sunset over mountains"},
        {"segment_number": 2, "image_prompt": "A modern city skyline at night"}
    ]
    
    result = generate_images(test_segments, 512, 512, ".")
    print(result)
