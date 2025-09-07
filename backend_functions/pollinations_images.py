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

POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"

def generate_images(segments: List[Dict], width: int = 1024, height: int = 576, output_dir: str = ".") -> Dict[str, Any]:
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
            image_file = generate_single_image(prompt, width, height, output_dir, segment_num)
            
            if image_file:
                generated_images.append({
                    "segment": segment_num,
                    "image_file": image_file,
                    "prompt": prompt,
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

def generate_single_image(prompt: str, width: int, height: int, output_dir: str, segment_num: int) -> str:
    """Generate a single image using Pollinations API"""
    
    # Enhance prompt for better quality
    enhanced_prompt = f"{prompt}, high quality, detailed, professional, 8K resolution"
    encoded_prompt = urllib.parse.quote(enhanced_prompt)
    
    # Build URL with parameters
    params = {
        'width': width,
        'height': height,
        'model': 'flux',
        'seed': random.randint(100000, 999999),
        'nologo': 'true',
        'enhance': 'true'
    }
    
    param_string = "&".join([f"{k}={v}" for k, v in params.items()])
    full_url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}?{param_string}"
    
    # Make request with retries
    for attempt in range(3):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            response = requests.get(full_url, timeout=30, headers=headers)
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if 'image' not in content_type and 'octet-stream' not in content_type:
                raise Exception(f"Invalid content type: {content_type}")
            
            # Save image
            filename = f"segment_{segment_num:02d}_{uuid.uuid4().hex[:8]}.png"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            # Validate image
            if validate_image(filepath, width, height):
                return filepath
            else:
                os.remove(filepath)
                raise Exception("Image validation failed")
                
        except Exception as e:
            if attempt < 2:  # Not the last attempt
                wait_time = (attempt + 1) * 2
                print(f"[IMAGE] Attempt {attempt + 1} failed, retrying in {wait_time}s...")
                time.sleep(wait_time)
            else:
                raise e

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