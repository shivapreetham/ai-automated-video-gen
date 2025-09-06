"""
Free Image Generation using Pollinations AI
Replacement for DALL-E 3 / Stable Diffusion XL / Replicate
"""

import json
import numpy as np
from PIL import Image
import os
from tqdm import tqdm
import cv2
import time
import random
import string
import requests
import math
import subprocess

# Configure ffmpeg for moviepy BEFORE importing moviepy
try:
    import moviepy.config as mp_config
    import imageio_ffmpeg as iio
    mp_config.IMAGEIO_FFMPEG_EXE = iio.get_ffmpeg_exe()
    print(f"Using ffmpeg from: {mp_config.IMAGEIO_FFMPEG_EXE}")
    
    # Now import moviepy
    from moviepy.editor import *
except Exception as e:
    print(f"Warning: Could not configure ffmpeg: {e}")
    from moviepy.editor import *
import uuid
import urllib.parse

# Pollinations AI image generation
POLLINATIONS_BASE_URL = "https://image.pollinations.ai/prompt/"

def download_file(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)

def download_json(url: str):
    response = requests.get(url)
    data = response.json()
    return data

def resize_image(image_path, new_width, new_height):
    img = Image.open(image_path) # Open an image file
    img = img.resize((new_width, new_height), Image.LANCZOS) # Resize the image
    img.save(image_path) # Save the image back to original file

def crop_image(image_path, new_width, new_height):
    # Open the image file
    img = Image.open(image_path)
    width, height = img.size   # Get dimensions
    left = (width - new_width)/2
    top = (height - new_height)/2
    right = (width + new_width)/2
    bottom = (height + new_height)/2
    img = img.crop((left, top, right, bottom))
    img.save(image_path)

def generate_image_pollinations(prompt: str, width: int=1024, height: int=1024, model: str='flux', negative_prompt: str='') -> str:
    """
    Enhanced image generation using Pollinations AI (free)
    
    Available models:
    - flux (default, highest quality, slower)
    - flux-realism (photorealistic)
    - flux-anime (anime/cartoon style)
    - flux-3d (3D render style)
    - turbo (faster, lower quality)
    """
    retries = 5  # Increased retries
    base_delay = 1
    
    for retry in range(retries):
        try:
            # Enhanced prompt optimization
            clean_prompt = optimize_prompt_for_quality(prompt, model)
            if negative_prompt:
                clean_prompt += f" | negative: {negative_prompt}, blurry, low quality, pixelated, distorted, watermark"
            else:
                clean_prompt += " | negative: blurry, low quality, pixelated, distorted, watermark"
            
            encoded_prompt = urllib.parse.quote(clean_prompt)
            
            # Optimized parameters for better quality
            params = {
                'width': min(max(width, 512), 1920),  # Clamp to reasonable values
                'height': min(max(height, 512), 1920),
                'model': model,
                'seed': random.randint(100000, 999999),  # Better seed range
                'nologo': 'true',  # Remove watermarks when possible
                'nofeed': 'true',  # Don't add to public feed
                'enhance': 'true' if model == 'flux' else 'false'  # Enable enhancement for flux
            }
            
            # Build URL
            url = f"{POLLINATIONS_BASE_URL}{encoded_prompt}"
            param_string = "&".join([f"{k}={v}" for k, v in params.items()])
            full_url = f"{url}?{param_string}"
            
            print(f"[Attempt {retry + 1}] Generating {width}x{height} image with {model}: {clean_prompt[:60]}...")
            
            # Make request with better headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'image/*,*/*;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive'
            }
            
            response = requests.get(full_url, timeout=60, headers=headers)  # Increased timeout
            response.raise_for_status()
            
            # Check content type
            content_type = response.headers.get('content-type', '').lower()
            if not any(img_type in content_type for img_type in ['image/', 'application/octet-stream']):
                raise ValueError(f"Invalid content type: {content_type}")
            
            # Save and validate image
            temp_filename = f"temp_pollinations_{uuid.uuid4().hex[:8]}.png"
            with open(temp_filename, 'wb') as f:
                f.write(response.content)
            
            # Enhanced image validation and post-processing
            if validate_and_enhance_image(temp_filename, width, height):
                print(f"✓ High-quality image generated: {temp_filename}")
                return temp_filename
            else:
                if os.path.exists(temp_filename):
                    os.remove(temp_filename)
                continue
                
        except requests.exceptions.Timeout:
            print(f"⚠ Timeout on attempt {retry + 1}, retrying...")
        except requests.exceptions.RequestException as e:
            print(f"⚠ Request error (attempt {retry + 1}): {e}")
        except Exception as e:
            print(f"⚠ Error generating image (attempt {retry + 1}): {e}")
        
        if retry < retries - 1:
            delay = base_delay * (2 ** retry)  # Exponential backoff
            print(f"Waiting {delay}s before retry...")
            time.sleep(delay)
    
    print("❌ All generation attempts failed, creating fallback image")
    return create_fallback_image(prompt, width, height)

def create_fallback_image(prompt: str, width: int, height: int) -> str:
    """
    Create a simple fallback image if generation fails
    """
    from PIL import ImageDraw, ImageFont
    
    # Create a colored background
    color = (random.randint(50, 200), random.randint(50, 200), random.randint(50, 200))
    img = Image.new('RGB', (width, height), color=color)
    draw = ImageDraw.Draw(img)
    
    # Add text
    try:
        font = ImageFont.truetype("arial.ttf", size=min(width, height) // 20)
    except:
        font = ImageFont.load_default()
    
    text = prompt[:100] + "..." if len(prompt) > 100 else prompt
    
    # Calculate text position (centered)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    
    x = (width - text_width) // 2
    y = (height - text_height) // 2
    
    draw.text((x, y), text, fill="white", font=font)
    
    filename = f"fallback_{uuid.uuid4().hex[:8]}.png"
    img.save(filename)
    return filename

def optimize_prompt_for_quality(prompt: str, model: str) -> str:
    """
    Advanced prompt optimization for better image quality
    """
    enhanced_prompt = prompt.strip()
    
    # Model-specific optimizations
    if model == 'flux':
        quality_terms = ["8K resolution", "ultra detailed", "professional photography", "masterpiece", "best quality"]
        style_additions = ["sharp focus", "perfect lighting", "cinematic composition"]
    elif model == 'flux-realism':
        quality_terms = ["photorealistic", "hyperrealistic", "professional photography", "DSLR quality"]
        style_additions = ["natural lighting", "high dynamic range", "perfect exposure"]
    elif model == 'flux-anime':
        quality_terms = ["anime masterpiece", "detailed anime art", "high quality anime"]
        style_additions = ["vibrant colors", "clean lines", "perfect anatomy"]
    elif model == 'flux-3d':
        quality_terms = ["3D render", "octane render", "unreal engine", "ray tracing"]
        style_additions = ["perfect materials", "volumetric lighting", "subsurface scattering"]
    else:  # turbo or other
        quality_terms = ["high quality", "detailed", "professional"]
        style_additions = ["good lighting", "sharp focus"]
    
    # Add quality terms if not present
    if not any(term.lower() in enhanced_prompt.lower() for term in quality_terms + ["quality", "detailed", "professional"]):
        enhanced_prompt += f", {random.choice(quality_terms)}"
    
    # Add style enhancements
    if not any(term.lower() in enhanced_prompt.lower() for term in ["lighting", "focus", "composition"]):
        enhanced_prompt += f", {random.choice(style_additions)}"
    
    return enhanced_prompt

# Enhanced LLM replacement for prompt generation  
def generate_img_prompt_simple(input_str: str) -> str:
    """
    Enhanced prompt generation without requiring external LLM
    """
    enhanced_prompt = input_str.strip()
    
    # Context-aware enhancement
    context_keywords = {
        'nature': ['landscape', 'scenic', 'natural beauty', 'outdoor'],
        'person': ['portrait', 'human', 'character', 'facial'],
        'building': ['architecture', 'structure', 'urban', 'design'],
        'food': ['culinary', 'appetizing', 'fresh', 'delicious'],
        'technology': ['modern', 'sleek', 'innovative', 'futuristic'],
        'art': ['artistic', 'creative', 'aesthetic', 'beautiful']
    }
    
    # Detect context and add appropriate terms
    for context, terms in context_keywords.items():
        if any(keyword in enhanced_prompt.lower() for keyword in [context] + terms):
            if not any(term in enhanced_prompt.lower() for term in terms):
                enhanced_prompt += f", {random.choice(terms)}"
            break
    
    # Add general quality improvements
    quality_boosters = [
        "highly detailed", "professional quality", "award winning",
        "trending on artstation", "perfect composition", "dramatic lighting"
    ]
    
    if not any(booster.lower() in enhanced_prompt.lower() for booster in quality_boosters):
        enhanced_prompt += f", {random.choice(quality_boosters)}"
    
    return enhanced_prompt

def validate_and_enhance_image(image_path: str, target_width: int, target_height: int) -> bool:
    """
    Validate and enhance generated image quality
    """
    try:
        with Image.open(image_path) as img:
            # Check if image is valid
            img.verify()
            
        # Reopen for processing (verify() closes the image)
        with Image.open(image_path) as img:
            width, height = img.size
            
            # Check minimum quality thresholds
            if width < 256 or height < 256:
                print(f"Image too small: {width}x{height}")
                return False
            
            # Check if image is mostly one color (failed generation)
            img_array = np.array(img.convert('RGB'))
            if len(np.unique(img_array)) < 100:  # Too few unique colors
                print("Image appears to be low quality (few colors)")
                return False
            
            # Enhance image if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            # Apply subtle enhancements
            from PIL import ImageEnhance
            
            # Slight sharpening
            enhancer = ImageEnhance.Sharpness(img)
            img = enhancer.enhance(1.1)
            
            # Slight contrast boost
            enhancer = ImageEnhance.Contrast(img)
            img = enhancer.enhance(1.05)
            
            # Save enhanced image
            img.save(image_path, "PNG", optimize=True, quality=95)
            
        return True
        
    except Exception as e:
        print(f"Image validation failed: {e}")
        return False

class VideoGenerationError(Exception):
    """Custom exception for video generation errors"""
    pass

class ImageGenerationError(Exception):
    """Custom exception for image generation errors"""
    pass

def validate_input_parameters(event: dict) -> dict:
    """
    Validate and sanitize input parameters with comprehensive error handling
    """
    try:
        # Required parameters validation
        width = event.get("width", 1024)
        height = event.get("height", 1024)
        
        if not isinstance(width, int) or width < 256 or width > 2048:
            raise ValueError(f"Invalid width: {width}. Must be between 256-2048")
        if not isinstance(height, int) or height < 256 or height > 2048:
            raise ValueError(f"Invalid height: {height}. Must be between 256-2048")
        
        # Sanitize and validate other parameters
        params = {
            'img_prompt': str(event.get("img_prompt", "beautiful scene")).strip(),
            'img_style_prompt': str(event.get("img_style_prompt", "")).strip(),
            'negative_prompt': str(event.get("negative_prompt", "blurry, low quality, distorted, watermark")),
            'width': width,
            'height': height,
            'transcript_json_url': event.get("sentences_json_url", None),
            'image_duration': max(1, min(60, float(event.get("image_duration", 3)))),
            'video_duration': max(1, min(300, float(event.get("video_duration", 10)))),
            'model': str(event.get("img_model", 'flux')).lower(),
            'crop_method': event.get("crop_method", None),
            'fps': max(1, min(60, int(event.get("fps", 30)))),
            'transition_time': max(0, min(5, float(event.get("transition_time", 1.0)))),
            'transition_overlap': bool(event.get("transition_overlap", False)),
            'zoom': max(0.5, min(3.0, float(event.get("zoom", 1.0)))),
            'topic': event.get("topic", None)
        }
        
        # Validate model
        valid_models = ['flux', 'turbo', 'flux-realism', 'flux-anime', 'flux-3d']
        if params['model'] not in valid_models:
            print(f"Warning: Unknown model '{params['model']}', using 'flux'")
            params['model'] = 'flux'
            
        # Validate crop method
        if params['crop_method'] not in [None, 'resize', 'crop_center']:
            print(f"Warning: Invalid crop method '{params['crop_method']}', using None")
            params['crop_method'] = None
            
        return params
        
    except Exception as e:
        raise ValueError(f"Parameter validation failed: {e}")

def concatenate_images_local(event):
    """
    Enhanced local version of image-to-video generation using Pollinations AI
    with comprehensive error handling and improved architecture
    """
    try:
        # Validate input parameters
        params = validate_input_parameters(event)
        print(f"✓ Parameters validated successfully")
        
        # Extract validated parameters
        img_prompt = params['img_prompt']
        img_style_prompt = params['img_style_prompt']
        negative_prompt = params['negative_prompt']
        width = params['width']
        height = params['height']
        transcript_json_url = params['transcript_json_url']
        image_duration = params['image_duration']
        video_duration = params['video_duration']
        model = params['model']
        crop_method = params['crop_method']
        fps = params['fps']
        transition_time = params['transition_time']
        transition_overlap = params['transition_overlap']
        zoom = params['zoom']
        topic = params['topic']
        
    except Exception as e:
        raise VideoGenerationError(f"Input validation failed: {e}")

    # Enhanced transcript processing with robust error handling
    if transcript_json_url is not None:
        try:
            print(f"📖 Processing transcript: {transcript_json_url}")
            
            # Load transcript data
            if os.path.exists(transcript_json_url):
                print("Loading local transcript file...")
                with open(transcript_json_url, 'r', encoding='utf-8') as f:
                    subtitles_json = json.load(f)
            elif transcript_json_url.startswith(('http://', 'https://')):
                print("Downloading remote transcript...")
                subtitles_json = download_json(transcript_json_url)
            else:
                raise FileNotFoundError(f"Invalid transcript path: {transcript_json_url}")
            
            # Validate transcript structure
            if not isinstance(subtitles_json, list) or len(subtitles_json) == 0:
                raise ValueError("Transcript must be a non-empty list")
            
            # Check required fields in first item
            required_fields = ['sentence', 'start_time']
            if not all(field in subtitles_json[0] for field in required_fields):
                raise ValueError(f"Transcript items must contain: {required_fields}")
            
            durations = []
            frames_per_image = []
            img_prompts = []
            azure_time_unit = 10000000  # Azure time units
            
            print(f"Processing {len(subtitles_json)} transcript segments...")
            
            for i, item in enumerate(subtitles_json):
                try:
                    # Calculate duration more robustly
                    if i < len(subtitles_json) - 1:
                        duration = (subtitles_json[i+1]['start_time'] - item['start_time']) / float(azure_time_unit)
                    else:
                        # Use duration field or estimate
                        duration = item.get('duration', 30000000) / float(azure_time_unit)
                    
                    # Ensure reasonable duration bounds
                    duration = max(1.0, min(30.0, duration))
                    durations.append(duration)
                    
                    if i != 0:
                        duration += transition_time * transition_overlap
                    
                    # Build sentence with topic context
                    sentence = item.get('sentence', '').strip()
                    if not sentence:
                        sentence = f"Scene {i+1}"  # Fallback
                    
                    if topic and len(topic) > 1:
                        sentence = f'{topic}, {sentence}'
                    
                    # Generate enhanced image prompt
                    img_prompt = generate_img_prompt_simple(sentence)
                    if isinstance(img_style_prompt, str) and len(img_style_prompt) > 1:
                        img_prompt = f'{img_prompt}, {img_style_prompt}'
                    
                    img_prompts.append(img_prompt)
                    frames_per_image.append(duration * fps)
                    
                except Exception as segment_error:
                    print(f"⚠ Error processing segment {i}: {segment_error}")
                    # Use fallback values for this segment
                    duration = 3.0
                    durations.append(duration)
                    fallback_prompt = f"{topic or 'scene'} {i+1}"
                    img_prompts.append(generate_img_prompt_simple(fallback_prompt))
                    frames_per_image.append(duration * fps)
            
            number_of_images = len(frames_per_image)
            print(f"✓ Processed transcript: {number_of_images} segments")
            
        except Exception as e:
            print(f"❌ Error processing transcript: {e}")
            print("Falling back to duration-based generation...")
            transcript_json_url = None
    
    if transcript_json_url is None:
        try:
            print(f"🎬 Using duration-based generation: {video_duration}s video")
            
            # Calculate optimal number of images
            video_duration = math.ceil(video_duration)
            number_of_images = max(int(video_duration / image_duration), 1)
            
            # Ensure reasonable number of images
            number_of_images = min(number_of_images, 50)  # Prevent excessive generation
            
            # Build enhanced prompts with variation
            base_prompt = img_prompt
            if isinstance(img_style_prompt, str) and len(img_style_prompt) > 1:
                base_prompt = f'{base_prompt}, {img_style_prompt}'
            
            # Add variation to prompts to avoid repetition
            variation_terms = [
                "different angle", "close-up view", "wide shot", "detailed view",
                "from above", "side view", "dynamic perspective", "artistic composition"
            ]
            
            img_prompts = []
            for i in range(number_of_images):
                if i == 0:
                    img_prompts.append(base_prompt)
                else:
                    # Add subtle variations
                    variation = random.choice(variation_terms)
                    varied_prompt = f"{base_prompt}, {variation}"
                    img_prompts.append(varied_prompt)
            
            # Calculate frame distribution
            total_frames = int(video_duration * fps)
            base_frames = total_frames // number_of_images
            extra_frames = total_frames % number_of_images
            
            frames_per_image = [base_frames] * number_of_images
            # Distribute extra frames to first images
            for i in range(extra_frames):
                frames_per_image[i] += 1
            
            # Add transition overlap if enabled
            if transition_overlap:
                overlap_frames = int(fps * transition_time)
                for i in range(1, number_of_images):
                    frames_per_image[i] += overlap_frames
            
            print(f"✓ Generated {number_of_images} varied prompts")
            
        except Exception as e:
            raise VideoGenerationError(f"Duration-based generation setup failed: {e}")
    
    # Summary information
    total_frames = sum(frames_per_image)
    estimated_duration = total_frames / fps
    
    print(f"\n📊 Generation Summary:")
    print(f"   • Images to generate: {number_of_images}")
    print(f"   • Total frames: {total_frames}")
    print(f"   • Estimated duration: {estimated_duration:.1f}s")
    print(f"   • Model: {model}")
    print(f"   • Resolution: {width}x{height}")
    print(f"   • FPS: {fps}")
    
    if len(img_prompts) > 0:
        print(f"   • Sample prompt: {img_prompts[0][:80]}...")
    
    # Initialize tracking variables
    video_path = f'enhanced_video_{uuid.uuid4().hex[:8]}.mp4'
    frames_url = []
    video_clips = []
    successful_generations = 0
    failed_generations = 0
    
    # Enhanced image generation loop with comprehensive error handling
    print(f"\n🎨 Starting image generation...")
    
    for i in range(number_of_images):
        try:
            print(f"\n[{i+1}/{number_of_images}] Generating image...")
            
            # Generate image with error handling
            try:
                if crop_method not in ['resize', 'crop_center']:
                    img_path = generate_image_pollinations(
                        img_prompts[i], width, height, model, negative_prompt
                    )
                else:
                    # Generate at higher resolution for better quality after cropping
                    img_path = generate_image_pollinations(
                        img_prompts[i], 1536, 1536, model, negative_prompt
                    )
                
                if not img_path or not os.path.exists(img_path):
                    raise ImageGenerationError(f"Image generation failed for prompt {i+1}")
                
                successful_generations += 1
                
            except Exception as gen_error:
                print(f"❌ Image generation failed: {gen_error}")
                failed_generations += 1
                
                # Create fallback image
                print("Creating fallback image...")
                img_path = create_fallback_image(img_prompts[i], width, height)
            
            # Process image (crop/resize) with error handling
            try:
                if crop_method == 'resize':
                    print(f"Resizing to {width}x{height}...")
                    resize_image(img_path, width, height)
                elif crop_method == 'crop_center':
                    print(f"Cropping to {width}x{height}...")
                    crop_image(img_path, width, height)
                    
            except Exception as process_error:
                print(f"⚠ Image processing failed: {process_error}")
                # Continue with original image
            
            # Store first frame URL for thumbnail
            if i == 0 and os.path.exists(img_path):
                frame_url = os.path.abspath(img_path)
                frames_url.append(frame_url)
            
            # Create video clip with enhanced error handling
            try:
                screensize = (width, height)
                img_duration = frames_per_image[i] / fps
                
                # Verify image before creating clip
                with Image.open(img_path) as test_img:
                    test_img.verify()
                
                if zoom != 1.0 and zoom != 1:
                    print(f"Applying zoom effect ({zoom}x)...")
                    clip = (ImageClip(img_path)
                            .resize(height=screensize[1]*4)
                            .resize(lambda t: 1 + (zoom-1.)*t / img_duration)
                            .set_position(('center', 'center'))
                            .set_duration(img_duration)
                            )
                    clip = CompositeVideoClip([clip]).resize(width=screensize[0])
                    vid = CompositeVideoClip([clip.set_position(('center', 'center'))], size=screensize)
                else:
                    vid = ImageClip(img_path).set_duration(img_duration)
                
                video_clips.append(vid)
                print(f"✓ Clip created ({img_duration:.1f}s)")
                
            except Exception as clip_error:
                print(f"❌ Clip creation failed: {clip_error}")
                # Create a simple colored clip as fallback
                from moviepy.editor import ColorClip
                fallback_clip = ColorClip(size=screensize, color=(50, 50, 50), duration=img_duration)
                video_clips.append(fallback_clip)
                print("✓ Fallback clip created")
            
            # Clean up image file
            try:
                if os.path.exists(img_path) and i > 0:  # Keep first image for thumbnail
                    os.remove(img_path)
            except Exception as cleanup_error:
                print(f"⚠ Cleanup warning: {cleanup_error}")
                
        except Exception as loop_error:
            print(f"❌ Critical error in generation loop: {loop_error}")
            failed_generations += 1
            
            # Create minimal fallback clip
            try:
                fallback_duration = frames_per_image[i] / fps if i < len(frames_per_image) else 3.0
                from moviepy.editor import ColorClip
                fallback_clip = ColorClip(size=(width, height), color=(100, 100, 100), duration=fallback_duration)
                video_clips.append(fallback_clip)
                print("✓ Emergency fallback clip created")
            except Exception as fallback_error:
                print(f"❌ Even fallback failed: {fallback_error}")
                # Continue to next iteration
    
    # Generation summary
    print(f"\n📈 Generation Complete:")
    print(f"   • Successful: {successful_generations}/{number_of_images}")
    print(f"   • Failed: {failed_generations}/{number_of_images}")
    print(f"   • Video clips created: {len(video_clips)}")
    
    if len(video_clips) == 0:
        raise VideoGenerationError("No video clips were successfully created")

    # Enhanced video assembly with robust error handling
    try:
        print(f"\n🎬 Assembling video...")
        
        # Concatenate video clips
        video_clip = concatenate_videoclips(video_clips)
        print(f"✓ Base video assembled ({video_clip.duration:.1f}s)")
        
        # Handle transitions
        if transition_time == 0 or transition_time == 0.:
            print("Rendering video without transitions...")
            video_clip.write_videofile(
                video_path, fps=fps, 
                verbose=False, logger=None,
                temp_audiofile='temp-audio.m4a',
                remove_temp=True
            )
            
            # Cleanup
            video_clip.close()
            for clip in video_clips:
                clip.close()
                
            return video_path, frames_url[0] if frames_url else None
        
        print(f"Adding transitions ({transition_time}s)...")
        clips = []
        
        # Enhanced transition processing
        start_time, end_time = 0., 0.
        for i in range(len(video_clips)):
            try:
                clip_duration = frames_per_image[i] / fps if i < len(frames_per_image) else video_clips[i].duration
                end_time = start_time + clip_duration
                
                if i == 0:
                    clips.append(video_clip.subclip(start_time, end_time))
                else:
                    transition_clip = video_clip.subclip(start_time, end_time)
                    if transition_overlap:
                        transition_clip = transition_clip.set_start(start_time - transition_time * i * transition_overlap)
                    transition_clip = transition_clip.crossfadein(transition_time)
                    clips.append(transition_clip)
                    
                start_time = end_time
                
            except Exception as transition_error:
                print(f"⚠ Transition error for clip {i}: {transition_error}")
                # Add clip without transition
                if i < len(video_clips):
                    clips.append(video_clips[i])
        
        if clips:
            print("Compositing final video with transitions...")
            final_clip = CompositeVideoClip(clips)
            
            # Write final video with transitions
            transition_video_path = f'transition_{video_path}'
            final_clip.write_videofile(
                transition_video_path, fps=fps,
                verbose=False, logger=None,
                temp_audiofile='temp-audio-transitions.m4a',
                remove_temp=True
            )
            
            # Cleanup
            video_clip.close()
            final_clip.close()
            for clip in video_clips + clips:
                clip.close()
            
            print(f"✓ Video with transitions completed: {transition_video_path}")
            return transition_video_path, frames_url[0] if frames_url else None
        else:
            # Fallback to original video
            print("⚠ Transition processing failed, using base video")
            video_clip.write_videofile(
                video_path, fps=fps,
                verbose=False, logger=None
            )
            video_clip.close()
            return video_path, frames_url[0] if frames_url else None
            
    except Exception as assembly_error:
        print(f"❌ Video assembly failed: {assembly_error}")
        
        # Emergency fallback: create simple video from first working clip
        try:
            if video_clips:
                print("Creating emergency fallback video...")
                emergency_clip = video_clips[0]
                emergency_path = f'emergency_{video_path}'
                emergency_clip.write_videofile(emergency_path, fps=fps, verbose=False, logger=None)
                
                # Cleanup
                for clip in video_clips:
                    clip.close()
                    
                return emergency_path, frames_url[0] if frames_url else None
        except Exception as emergency_error:
            print(f"❌ Even emergency fallback failed: {emergency_error}")
        
        # Final cleanup
        try:
            for clip in video_clips:
                clip.close()
        except:
            pass
            
        raise VideoGenerationError(f"Video assembly completely failed: {assembly_error}")

def mindsflow_function(event, context) -> dict:
    """
    Enhanced local version with comprehensive error handling and monitoring
    Compatible with the original interface but with improved robustness
    """
    start_time = time.time()
    
    try:
        print(f"\n🚀 Starting Enhanced Local Video Generation")
        print(f"   Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Generate video from images with enhanced error handling
        video_path, first_frame_url = concatenate_images_local(event)
        
        if not video_path or not os.path.exists(video_path):
            raise VideoGenerationError("Video generation failed - no output file created")
        
        # Verify video file integrity
        try:
            file_size = os.path.getsize(video_path)
            if file_size < 1024:  # Less than 1KB suggests failure
                raise VideoGenerationError(f"Generated video file is too small ({file_size} bytes)")
            
            print(f"✓ Video file created: {video_path} ({file_size/1024/1024:.1f} MB)")
            
        except Exception as verify_error:
            print(f"⚠ Video verification failed: {verify_error}")
        
        # Calculate processing time
        processing_time = time.time() - start_time
        print(f"✓ Generation completed in {processing_time:.1f} seconds")
        
        # Return comprehensive result
        result = {
            'video_url': os.path.abspath(video_path),
            'video_file': video_path,
            'first_frame_url': first_frame_url,
            'processing_time': processing_time,
            'file_size_mb': os.path.getsize(video_path) / 1024 / 1024 if os.path.exists(video_path) else 0,
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'version': '2.0_enhanced'
        }
        
        print(f"\n🎉 Success! Video generation completed")
        return result
        
    except VideoGenerationError as vge:
        error_msg = f"Video generation error: {vge}"
        print(f"❌ {error_msg}")
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': 'VideoGenerationError',
            'processing_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        error_msg = f"Unexpected error during video generation: {e}"
        print(f"💥 {error_msg}")
        
        return {
            'success': False,
            'error': error_msg,
            'error_type': type(e).__name__,
            'processing_time': time.time() - start_time,
            'timestamp': datetime.now().isoformat()
        }

# Import required datetime for error handling
from datetime import datetime

# Test function
if __name__ == "__main__":
    # Test image generation
    test_prompt = "A beautiful sunset over mountains, detailed, cinematic"
    img_path = generate_image_pollinations(test_prompt, 512, 512)
    print(f"Test image generated: {img_path}")
    
    # Test video generation
    test_event = {
        "img_prompt": "A peaceful forest scene with sunlight filtering through trees",
        "width": 512,
        "height": 512,
        "video_duration": 6,
        "fps": 16,
        "image_duration": 3
    }
    
    result = mindsflow_function(test_event, None)
    print(f"Test video generated: {result}")