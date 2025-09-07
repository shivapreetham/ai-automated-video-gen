"""
Per-Segment Video Creation System
Creates individual video clips for each segment with proper audio-visual synchronization
"""

import os
import json
import uuid
import subprocess
import time
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Try to import MoviePy for advanced video processing
try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips, CompositeVideoClip
    from moviepy.video.fx import fadeout, fadein
    MOVIEPY_AVAILABLE = True
    print("[SEGMENT VIDEO] MoviePy available for advanced processing")
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("[SEGMENT VIDEO] MoviePy not available, using FFmpeg only")

def create_segment_videos(script_data: Dict[str, Any], audio_results: Dict[str, Any], 
                         image_results: Dict[str, Any], output_dir: str = ".",
                         width: int = 1024, height: int = 576, fps: int = 24) -> Dict[str, Any]:
    """
    Create individual video clips for each segment with proper synchronization
    
    Args:
        script_data: Script data with segments
        audio_results: Results from segment audio generation
        image_results: Results from segment image generation  
        output_dir: Directory to save video files
        width, height: Video dimensions
        fps: Frames per second
    
    Returns:
        Dictionary with video files and metadata for each segment
    """
    
    segments = script_data.get("segments", [])
    if not segments:
        return {"success": False, "error": "No segments found in script data"}
    
    audio_files = {r["segment_number"]: r for r in audio_results.get("audio_files", []) if r.get("success")}
    segments_with_images = {s["segment_number"]: s for s in image_results.get("segments_with_images", [])}
    
    print(f"[SEGMENT VIDEO] Creating videos for {len(segments)} segments...")
    
    # Create videos for all segments
    video_results = []
    
    # Use ThreadPoolExecutor for concurrent generation
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_segment = {}
        
        for segment in segments:
            segment_number = segment["segment_number"]
            
            # Get audio and images for this segment
            audio_data = audio_files.get(segment_number)
            image_data = segments_with_images.get(segment_number)
            
            if not audio_data:
                print(f"[SEGMENT VIDEO] No audio for segment {segment_number}, skipping")
                continue
            
            if not image_data or image_data.get("successful_images", 0) == 0:
                print(f"[SEGMENT VIDEO] No images for segment {segment_number}, skipping")
                continue
            
            future = executor.submit(
                create_single_segment_video,
                segment,
                audio_data,
                image_data,
                output_dir,
                width,
                height,
                fps
            )
            future_to_segment[future] = segment
        
        # Collect results as they complete
        for future in as_completed(future_to_segment):
            segment = future_to_segment[future]
            try:
                result = future.result()
                result["segment_number"] = segment["segment_number"]
                video_results.append(result)
                print(f"[SEGMENT VIDEO] Completed segment {segment['segment_number']}")
            except Exception as e:
                print(f"[SEGMENT VIDEO] Failed segment {segment['segment_number']}: {e}")
                video_results.append({
                    "segment_number": segment["segment_number"],
                    "success": False,
                    "error": str(e)
                })
    
    # Sort results by segment number
    video_results.sort(key=lambda x: x["segment_number"])
    
    # Calculate statistics
    successful_videos = [r for r in video_results if r.get("success")]
    total_duration = sum(r.get("duration_seconds", 0) for r in successful_videos)
    total_file_size = sum(r.get("file_size", 0) for r in successful_videos)
    
    return {
        "success": len(successful_videos) > 0,
        "videos_created": len(successful_videos),
        "videos_failed": len(video_results) - len(successful_videos),
        "total_segments": len(segments),
        "segment_videos": video_results,
        "total_duration": total_duration,
        "total_file_size": total_file_size,
        "creation_method": "moviepy" if MOVIEPY_AVAILABLE else "ffmpeg"
    }

def create_single_segment_video(segment: Dict[str, Any], audio_data: Dict[str, Any],
                               image_data: Dict[str, Any], output_dir: str,
                               width: int, height: int, fps: int) -> Dict[str, Any]:
    """Create video for a single segment with proper audio-visual sync"""
    
    segment_number = segment.get("segment_number", 1)
    audio_file = audio_data.get("audio_file")
    audio_duration = audio_data.get("duration_seconds", 5.0)
    
    # Get successful images for this segment
    successful_images = [img for img in image_data.get("images", []) if img.get("success")]
    
    if not successful_images:
        return {"success": False, "error": "No successful images for segment"}
    
    if not audio_file or not os.path.exists(audio_file):
        return {"success": False, "error": "Audio file not found"}
    
    # Generate output filename
    timestamp = int(time.time())
    video_filename = f'segment_{segment_number:02d}_video_{timestamp}_{uuid.uuid4().hex[:8]}.mp4'
    video_path = os.path.join(output_dir, video_filename)
    
    try:
        if MOVIEPY_AVAILABLE:
            return create_segment_video_moviepy(
                segment_number, successful_images, audio_file, audio_duration,
                video_path, width, height, fps
            )
        else:
            return create_segment_video_ffmpeg(
                segment_number, successful_images, audio_file, audio_duration,
                video_path, width, height, fps
            )
    
    except Exception as e:
        return {"success": False, "error": f"Video creation failed: {e}"}

def create_segment_video_moviepy(segment_number: int, images: List[Dict[str, Any]],
                                audio_file: str, audio_duration: float, video_path: str,
                                width: int, height: int, fps: int) -> Dict[str, Any]:
    """Create segment video using MoviePy with smooth transitions"""
    
    try:
        print(f"[SEGMENT {segment_number}] Creating video with MoviePy...")
        
        # Load audio
        audio_clip = AudioFileClip(audio_file)
        actual_audio_duration = audio_clip.duration
        
        # Create image clips with proper timing
        image_clips = []
        total_image_duration = sum(img.get("image_duration", 0) for img in images)
        
        # If images don't match audio duration, adjust proportionally
        if total_image_duration != actual_audio_duration:
            duration_ratio = actual_audio_duration / total_image_duration
            print(f"[SEGMENT {segment_number}] Adjusting image timing by factor {duration_ratio:.2f}")
        else:
            duration_ratio = 1.0
        
        cumulative_time = 0
        for i, image_info in enumerate(images):
            image_file = image_info.get("image_file")
            if not os.path.exists(image_file):
                print(f"[WARNING] Image not found: {image_file}")
                continue
            
            # Calculate adjusted duration
            original_duration = image_info.get("image_duration", 3.0)
            adjusted_duration = original_duration * duration_ratio
            
            # Create image clip
            clip = ImageClip(image_file, duration=adjusted_duration)
            clip = clip.resize((width, height))
            
            # Add transitions for smooth flow
            if len(images) > 1:
                transition_duration = min(0.5, adjusted_duration * 0.2)
                
                if i == 0:
                    # First clip: fade in
                    clip = clip.fadein(transition_duration)
                elif i == len(images) - 1:
                    # Last clip: fade out
                    clip = clip.fadeout(transition_duration)
                else:
                    # Middle clips: crossfade
                    clip = clip.fadein(transition_duration).fadeout(transition_duration)
            
            # Set start time for overlapping transitions
            if i > 0:
                overlap = min(0.3, adjusted_duration * 0.15)
                clip = clip.set_start(cumulative_time - overlap)
            else:
                clip = clip.set_start(cumulative_time)
            
            image_clips.append(clip)
            cumulative_time += adjusted_duration
        
        if not image_clips:
            raise Exception("No valid image clips created")
        
        # Create composite video or concatenate
        if len(image_clips) > 1 and any(clip.start > 0 for clip in image_clips):
            # Use composite for overlapping clips
            video_clip = CompositeVideoClip(image_clips, size=(width, height))
        else:
            # Simple concatenation
            video_clip = concatenate_videoclips(image_clips, method="compose")
        
        # Ensure video matches audio duration exactly
        if video_clip.duration > actual_audio_duration:
            video_clip = video_clip.subclip(0, actual_audio_duration)
        elif video_clip.duration < actual_audio_duration:
            # Extend the last frame
            last_frame = video_clip.to_ImageClip(t=video_clip.duration-0.1)
            extension = last_frame.set_duration(actual_audio_duration - video_clip.duration)
            video_clip = concatenate_videoclips([video_clip, extension])
        
        # Combine with audio
        final_video = video_clip.set_audio(audio_clip)
        
        # Write video file
        temp_audio_path = os.path.join(os.path.dirname(video_path), f'temp_audio_{segment_number}.m4a')
        
        final_video.write_videofile(
            video_path,
            codec='libx264',
            audio_codec='aac',
            fps=fps,
            temp_audiofile=temp_audio_path,
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # Cleanup
        for clip in image_clips:
            clip.close()
        video_clip.close()
        audio_clip.close()
        final_video.close()
        
        # Get final file info
        file_size = os.path.getsize(video_path)
        final_duration = get_video_duration(video_path)
        
        print(f"[SEGMENT {segment_number}] Created video: {os.path.basename(video_path)} ({final_duration:.1f}s)")
        
        return {
            "success": True,
            "video_file": video_path,
            "filename": os.path.basename(video_path),
            "duration_seconds": final_duration,
            "file_size": file_size,
            "width": width,
            "height": height,
            "fps": fps,
            "images_used": len(image_clips),
            "has_transitions": len(image_clips) > 1,
            "creation_method": "moviepy"
        }
        
    except Exception as e:
        print(f"[ERROR] MoviePy failed for segment {segment_number}: {e}")
        raise e

def create_segment_video_ffmpeg(segment_number: int, images: List[Dict[str, Any]],
                               audio_file: str, audio_duration: float, video_path: str,
                               width: int, height: int, fps: int) -> Dict[str, Any]:
    """Create segment video using FFmpeg"""
    
    try:
        print(f"[SEGMENT {segment_number}] Creating video with FFmpeg...")
        
        # Get actual audio duration
        actual_audio_duration = get_audio_duration(audio_file)
        
        if len(images) == 1:
            # Single image - create simple video
            image_file = images[0].get("image_file")
            
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', image_file,
                '-i', audio_file,
                '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                '-pix_fmt', 'yuv420p',
                video_path
            ]
        else:
            # Multiple images - create with crossfades
            return create_multi_image_video_ffmpeg(
                segment_number, images, audio_file, actual_audio_duration,
                video_path, width, height, fps
            )
        
        print(f"[SEGMENT {segment_number}] Running FFmpeg...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg failed: {result.stderr}")
        
        # Get final file info
        file_size = os.path.getsize(video_path)
        final_duration = get_video_duration(video_path)
        
        print(f"[SEGMENT {segment_number}] Created video: {os.path.basename(video_path)} ({final_duration:.1f}s)")
        
        return {
            "success": True,
            "video_file": video_path,
            "filename": os.path.basename(video_path),
            "duration_seconds": final_duration,
            "file_size": file_size,
            "width": width,
            "height": height,
            "fps": fps,
            "images_used": len(images),
            "has_transitions": len(images) > 1,
            "creation_method": "ffmpeg"
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_multi_image_video_ffmpeg(segment_number: int, images: List[Dict[str, Any]],
                                   audio_file: str, audio_duration: float, video_path: str,
                                   width: int, height: int, fps: int) -> Dict[str, Any]:
    """Create video with multiple images using FFmpeg crossfades"""
    
    # Calculate timing for each image
    total_image_duration = sum(img.get("image_duration", 0) for img in images)
    duration_ratio = audio_duration / total_image_duration if total_image_duration > 0 else 1.0
    
    # Create temporary clips for each image
    temp_clips = []
    temp_dir = os.path.dirname(video_path)
    
    try:
        for i, image_info in enumerate(images):
            image_file = image_info.get("image_file")
            if not os.path.exists(image_file):
                continue
            
            adjusted_duration = image_info.get("image_duration", 3.0) * duration_ratio
            clip_path = os.path.join(temp_dir, f'temp_seg_{segment_number}_clip_{i}.mp4')
            
            # Create individual clip
            cmd_clip = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', image_file,
                '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}',
                '-c:v', 'libx264',
                '-t', str(adjusted_duration),
                '-pix_fmt', 'yuv420p',
                clip_path
            ]
            
            result = subprocess.run(cmd_clip, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                temp_clips.append(clip_path)
        
        if not temp_clips:
            raise Exception("No temporary clips created")
        
        # Combine clips with crossfade transitions
        if len(temp_clips) == 1:
            # Single clip - just add audio
            cmd_final = [
                'ffmpeg', '-y',
                '-i', temp_clips[0],
                '-i', audio_file,
                '-c:v', 'copy',
                '-c:a', 'aac',
                '-shortest',
                video_path
            ]
        else:
            # Multiple clips - create crossfade chain
            transition_duration = 0.5
            filter_complex = build_crossfade_filter(len(temp_clips), transition_duration)
            
            cmd_final = [
                'ffmpeg', '-y'
            ]
            
            # Add input files
            for clip in temp_clips:
                cmd_final.extend(['-i', clip])
            
            cmd_final.extend([
                '-i', audio_file,
                '-filter_complex', filter_complex,
                '-map', f'[v{len(temp_clips)-1}]',
                '-map', f'{len(temp_clips)}:a',
                '-c:v', 'libx264',
                '-c:a', 'aac',
                '-shortest',
                video_path
            ])
        
        result = subprocess.run(cmd_final, capture_output=True, text=True, timeout=180)
        
        if result.returncode != 0:
            raise Exception(f"Final FFmpeg command failed: {result.stderr}")
        
        return {
            "success": True,
            "video_file": video_path,
            "filename": os.path.basename(video_path),
            "duration_seconds": get_video_duration(video_path),
            "file_size": os.path.getsize(video_path),
            "width": width,
            "height": height,
            "fps": fps,
            "images_used": len(images),
            "has_transitions": True,
            "creation_method": "ffmpeg_crossfade"
        }
        
    finally:
        # Clean up temporary clips
        for clip_path in temp_clips:
            try:
                os.remove(clip_path)
            except:
                pass

def build_crossfade_filter(clip_count: int, transition_duration: float) -> str:
    """Build FFmpeg filter chain for crossfade transitions"""
    
    if clip_count <= 1:
        return "[0:v]"
    
    filter_parts = []
    
    for i in range(clip_count - 1):
        if i == 0:
            # First transition
            filter_parts.append(f"[0:v][1:v]xfade=transition=fade:duration={transition_duration}:offset=2[v1]")
        else:
            # Subsequent transitions
            offset = 2 + (i * 2)  # Approximate offset
            filter_parts.append(f"[v{i}][{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset={offset}[v{i+1}]")
    
    return ";".join(filter_parts)

def get_audio_duration(audio_file: str) -> float:
    """Get audio duration using FFprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    return 5.0  # Default fallback

def get_video_duration(video_file: str) -> float:
    """Get video duration using FFprobe"""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            video_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    return 0.0

if __name__ == "__main__":
    print("[SEGMENT VIDEO] Per-segment video creation system ready")