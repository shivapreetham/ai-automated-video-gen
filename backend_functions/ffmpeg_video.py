"""
FFmpeg Video Creation - Enhanced Backend Function
Creates video from multiple images and audio using both FFmpeg and MoviePy
Ported advanced video stitching logic from local_functions
"""

import os
import subprocess
import uuid
import json
import time
from typing import List, Dict, Any

# Try to import MoviePy for advanced video processing
try:
    from moviepy.editor import ImageClip, AudioFileClip, concatenate_videoclips
    from moviepy.video.fx import resize
    MOVIEPY_AVAILABLE = True
    print("[VIDEO] MoviePy available for advanced video processing")
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("[VIDEO] MoviePy not available, using FFmpeg only")

def create_video_with_audio(images: List[Dict], audio_file: str, output_dir: str, 
                           width: int = 1024, height: int = 576, fps: int = 24, 
                           add_captions: bool = True) -> Dict[str, Any]:
    """
    Create video from multiple images and audio using MoviePy (preferred) or FFmpeg fallback
    Enhanced version with caption support
    """
    
    print(f"[VIDEO] Creating video from {len(images)} images + audio...")
    
    try:
        # Get audio duration first
        audio_duration = get_audio_duration(audio_file)
        print(f"[VIDEO] Audio duration: {audio_duration:.1f}s")
        
        # Calculate duration per image
        duration_per_image = audio_duration / len(images)
        print(f"[VIDEO] Duration per image: {duration_per_image:.1f}s")
        
        # Create video filename
        video_filename = f"final_video_{uuid.uuid4().hex[:8]}.mp4"
        video_path = os.path.join(output_dir, video_filename)
        
        # Try MoviePy first (better quality)
        if MOVIEPY_AVAILABLE:
            result = create_video_with_moviepy(images, audio_file, video_path, audio_duration, duration_per_image, width, height, fps)
        else:
            result = create_video_with_ffmpeg(images, audio_file, video_path, audio_duration, duration_per_image, width, height, fps)
        
        # Add captions if requested and video creation was successful
        if add_captions and result.get("success") and has_caption_data(images):
            print(f"[VIDEO] Adding captions to video...")
            result = add_captions_to_video(result, images, output_dir, width, height)
        
        return result
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_video_with_moviepy(images: List[Dict], audio_file: str, video_path: str, 
                             audio_duration: float, duration_per_image: float, 
                             width: int, height: int, fps: int) -> Dict[str, Any]:
    """
    Create video using MoviePy with transitions - enhanced for better visual flow
    """
    try:
        print(f"[VIDEO] Using MoviePy for high-quality video creation with transitions...")
        
        # Import additional MoviePy modules for transitions
        try:
            from moviepy.video.fx import fadeout, fadein, crossfadein, crossfadeout
            from moviepy.video.compositing.transitions import crossfadein as crossfade_transition
            TRANSITIONS_AVAILABLE = True
            print("[VIDEO] Transition effects available")
        except ImportError:
            TRANSITIONS_AVAILABLE = False
            print("[VIDEO] Advanced transitions not available, using basic concatenation")
        
        # Create video clips from images with transitions
        clips = []
        transition_duration = min(0.5, duration_per_image * 0.2)  # 20% of segment duration, max 0.5s
        
        for i, image_data in enumerate(images):
            image_file = image_data['image_file']
            
            if not os.path.exists(image_file):
                print(f"[WARNING] Image not found: {image_file}, skipping...")
                continue
            
            print(f"[VIDEO] Processing image {i+1}/{len(images)}: {os.path.basename(image_file)}")
            
            # Create image clip with duration
            try:
                clip = ImageClip(image_file, duration=duration_per_image)
                
                # Resize to match target dimensions
                clip = clip.resize((width, height))
                
                # Add subtle zoom effect (Ken Burns effect) - simple and fast
                try:
                    # Simple zoom using MoviePy's resize function with time-based scaling
                    def make_zoom(clip_duration):
                        # Zoom from 100% to 110% over the clip duration
                        def zoom_func(t):
                            zoom_factor = 1.0 + 0.1 * (t / clip_duration)  # 1.0 to 1.1
                            return zoom_factor
                        return zoom_func
                    
                    zoom_function = make_zoom(duration_per_image)
                    clip = clip.resize(lambda t: zoom_function(t))
                    
                except Exception as zoom_error:
                    print(f"[WARNING] Zoom effect failed: {zoom_error}, using original clip")
                    # Continue without zoom if it fails
                
                # Add transitions if available
                if TRANSITIONS_AVAILABLE and len(images) > 1:
                    if i == 0:
                        # First clip: fade in from black
                        clip = clip.fadein(transition_duration)
                    elif i == len(images) - 1:
                        # Last clip: fade out to black
                        clip = clip.fadeout(transition_duration)
                    else:
                        # Middle clips: crossfade transitions
                        clip = clip.fadein(transition_duration).fadeout(transition_duration)
                
                clips.append(clip)
                
            except Exception as clip_error:
                print(f"[WARNING] Error processing image {i+1}: {clip_error}")
                continue
        
        if not clips:
            raise Exception("No valid images could be processed into clips")
        
        # Concatenate clips with crossfade transitions if available
        if TRANSITIONS_AVAILABLE and len(clips) > 1:
            print(f"[VIDEO] Creating video with smooth crossfade transitions...")
            
            # Adjust clip durations to account for overlaps
            adjusted_clips = []
            for i, clip in enumerate(clips):
                if i == 0:
                    # First clip: no overlap at start
                    adjusted_clips.append(clip)
                elif i == len(clips) - 1:
                    # Last clip: start earlier to create overlap
                    adjusted_clips.append(clip.set_start((i * duration_per_image) - transition_duration))
                else:
                    # Middle clips: both start earlier and end later for smooth transitions
                    adjusted_clips.append(clip.set_start((i * duration_per_image) - transition_duration))
            
            # Use CompositeVideoClip for overlapping transitions
            from moviepy.editor import CompositeVideoClip
            video_clip = CompositeVideoClip(adjusted_clips, size=(width, height))
            
        else:
            print(f"[VIDEO] Concatenating {len(clips)} clips...")
            video_clip = concatenate_videoclips(clips, method="compose")
        
        # Ensure video matches audio duration
        if video_clip.duration > audio_duration:
            video_clip = video_clip.subclip(0, audio_duration)
        elif video_clip.duration < audio_duration:
            # Extend last frame to match audio
            last_clip = clips[-1].set_duration(duration_per_image + (audio_duration - video_clip.duration))
            clips[-1] = last_clip
            video_clip = concatenate_videoclips(clips, method="compose")
        
        # Load and attach audio
        audio_clip = AudioFileClip(audio_file)
        final_video = video_clip.set_audio(audio_clip)
        
        # Write final video
        print(f"[VIDEO] Writing final video with MoviePy...")
        temp_audio_path = os.path.join(os.path.dirname(video_path), 'temp-audio.m4a')
        
        final_video.write_videofile(
            video_path,
            codec='libx264',
            audio_codec='aac',
            fps=min(fps, 24),  # Cap FPS for faster encoding
            temp_audiofile=temp_audio_path,
            remove_temp=True,
            verbose=False,
            logger=None,
            # Speed optimizations
            preset='ultrafast',  # Fastest H.264 preset
            threads=4,           # Use multiple CPU cores
            bitrate='2000k'      # Good quality but fast encoding
        )
        
        # Cleanup clips
        for clip in clips:
            clip.close()
        video_clip.close()
        audio_clip.close()
        final_video.close()
        
        # Get final file info
        file_size = os.path.getsize(video_path)
        final_duration = get_video_duration(video_path)
        
        print(f"[VIDEO] MoviePy video created successfully!")
        
        return {
            "success": True,
            "video_file": video_path,
            "duration": final_duration,
            "file_size": file_size,
            "width": width,
            "height": height,
            "fps": fps,
            "images_used": len(clips),
            "audio_attached": True,
            "method": "moviepy"
        }
        
    except Exception as e:
        print(f"[ERROR] MoviePy video creation failed: {e}")
        raise e

def create_video_with_ffmpeg(images: List[Dict], audio_file: str, video_path: str, 
                           audio_duration: float, duration_per_image: float, 
                           width: int, height: int, fps: int) -> Dict[str, Any]:
    """
    Enhanced video creation using FFmpeg with basic transitions
    """
    try:
        print(f"[VIDEO] Using FFmpeg for video creation with crossfade transitions...")
        output_dir = os.path.dirname(video_path)
        
        # Create individual video clips with crossfade transitions
        temp_clips = []
        transition_duration = min(0.5, duration_per_image * 0.2)  # 20% of segment duration, max 0.5s
        
        # First, create individual video clips from each image
        for i, image_data in enumerate(images):
            image_file = image_data['image_file']
            clip_path = os.path.join(output_dir, f"temp_clip_{i}.mp4")
            
            # Create a short video from the image
            cmd_clip = [
                'ffmpeg', '-y',
                '-loop', '1',
                '-i', image_file,
                '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}',
                '-c:v', 'libx264',
                '-t', str(duration_per_image),
                '-pix_fmt', 'yuv420p',
                clip_path
            ]
            
            result = subprocess.run(cmd_clip, capture_output=True, text=True, timeout=60)
            if result.returncode == 0:
                temp_clips.append(clip_path)
            else:
                print(f"[WARNING] Failed to create clip for image {i+1}: {result.stderr}")
        
        if not temp_clips:
            raise Exception("No video clips could be created from images")
        
        # Now combine clips with crossfade transitions
        if len(temp_clips) > 1:
            print(f"[VIDEO] Combining {len(temp_clips)} clips with crossfade transitions...")
            
            # Build complex filter for crossfade transitions
            filter_complex = ""
            video_inputs = []
            
            for i, clip in enumerate(temp_clips):
                video_inputs.extend(['-i', clip])
            
            # Build crossfade filter chain
            if len(temp_clips) == 2:
                filter_complex = f"[0:v][1:v]xfade=transition=fade:duration={transition_duration}:offset={duration_per_image-transition_duration}[v]"
            else:
                # Multiple clips - chain crossfades
                filter_parts = []
                for i in range(len(temp_clips) - 1):
                    if i == 0:
                        filter_parts.append(f"[{i}:v][{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset={duration_per_image-transition_duration}[v{i+1}]")
                    else:
                        filter_parts.append(f"[v{i}][{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset={(i+1)*duration_per_image-transition_duration}[v{i+1}]")
                filter_complex = ";".join(filter_parts)
            
            # FFmpeg command with crossfade
            cmd_video = [
                'ffmpeg', '-y'
            ] + video_inputs + [
                '-filter_complex', filter_complex,
                '-map', f'[v{len(temp_clips)-1}]' if len(temp_clips) > 2 else '[v]',
                '-c:v', 'libx264',
                '-pix_fmt', 'yuv420p',
                '-t', str(audio_duration),
                video_path
            ]
        else:
            # Single clip - just copy
            cmd_video = [
                'ffmpeg', '-y',
                '-i', temp_clips[0],
                '-c:v', 'libx264',
                '-t', str(audio_duration),
                video_path
            ]
        
        print(f"[VIDEO] Running FFmpeg video creation with transitions...")
        result = subprocess.run(cmd_video, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"[WARNING] Crossfade failed, falling back to simple concatenation: {result.stderr}")
            # Fallback to simple concatenation
            return create_video_with_ffmpeg_simple(images, audio_file, video_path, audio_duration, duration_per_image, width, height, fps)
        
        # Clean up temporary clips
        for clip in temp_clips:
            try:
                os.remove(clip)
            except:
                pass
        
        print(f"[VIDEO] Created video with transitions: {os.path.basename(video_path)}")
        
        # Now combine video with audio - use the original video_path as final path
        temp_video_path = video_path.replace('.mp4', '_temp.mp4')
        os.rename(video_path, temp_video_path)
        
        cmd_final = [
            'ffmpeg', '-y',
            '-i', temp_video_path,
            '-i', audio_file,
            '-c:v', 'copy',  # Don't re-encode video
            '-c:a', 'aac',   # Encode audio as AAC
            '-shortest',     # Match shortest stream (should be same duration)
            video_path  # Use original path as final output
        ]
        
        print(f"[VIDEO] Combining video with audio...")
        result = subprocess.run(cmd_final, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg audio combination failed: {result.stderr}")
        
        print(f"[VIDEO] Final video created: {os.path.basename(video_path)}")
        
        # Clean up temporary files
        try:
            os.remove(file_list_path)
            os.remove(temp_video_path)  # Remove intermediate video
        except:
            pass
        
        # Get final file info
        file_size = os.path.getsize(video_path)
        final_duration = get_video_duration(video_path)
        
        return {
            "success": True,
            "video_file": video_path,
            "duration": final_duration,
            "file_size": file_size,
            "width": width,
            "height": height,
            "fps": fps,
            "images_used": len(images),
            "audio_attached": True,
            "method": "ffmpeg"
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg operation timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_video_with_ffmpeg_simple(images: List[Dict], audio_file: str, video_path: str, 
                                   audio_duration: float, duration_per_image: float, 
                                   width: int, height: int, fps: int) -> Dict[str, Any]:
    """
    Simple video creation using FFmpeg without transitions - fallback method
    """
    try:
        print(f"[VIDEO] Using simple FFmpeg concatenation (fallback)...")
        output_dir = os.path.dirname(video_path)
        
        # Create temporary file list for FFmpeg
        file_list_path = os.path.join(output_dir, f"files_{uuid.uuid4().hex[:8]}.txt")
        
        with open(file_list_path, 'w') as f:
            for image_data in images:
                image_file = image_data['image_file']
                # Each image should be shown for duration_per_image seconds
                f.write(f"file '{os.path.abspath(image_file)}'\n")
                f.write(f"duration {duration_per_image}\n")
            
            # Add last image again to prevent FFmpeg from shortening the video
            if images:
                last_image = images[-1]['image_file']
                f.write(f"file '{os.path.abspath(last_image)}'\n")
        
        print(f"[VIDEO] Created file list: {file_list_path}")
        
        # FFmpeg command to create video from images
        cmd_video = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path,
            '-vf', f'scale={width}:{height}:force_original_aspect_ratio=decrease,pad={width}:{height}:(ow-iw)/2:(oh-ih)/2,fps={fps}',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            '-t', str(audio_duration),  # Match audio duration exactly
            video_path
        ]
        
        print(f"[VIDEO] Running simple FFmpeg video creation...")
        result = subprocess.run(cmd_video, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg video creation failed: {result.stderr}")
        
        print(f"[VIDEO] Created video: {os.path.basename(video_path)}")
        
        # Now combine video with audio - use the original video_path as final path
        temp_video_path = video_path.replace('.mp4', '_temp.mp4')
        os.rename(video_path, temp_video_path)
        
        cmd_final = [
            'ffmpeg', '-y',
            '-i', temp_video_path,
            '-i', audio_file,
            '-c:v', 'copy',  # Don't re-encode video
            '-c:a', 'aac',   # Encode audio as AAC
            '-shortest',     # Match shortest stream (should be same duration)
            video_path  # Use original path as final output
        ]
        
        print(f"[VIDEO] Combining video with audio...")
        result = subprocess.run(cmd_final, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            raise Exception(f"FFmpeg audio combination failed: {result.stderr}")
        
        print(f"[VIDEO] Final video created: {os.path.basename(video_path)}")
        
        # Clean up temporary files
        try:
            os.remove(file_list_path)
            os.remove(temp_video_path)  # Remove intermediate video
        except:
            pass
        
        # Get final file info
        file_size = os.path.getsize(video_path)
        final_duration = get_video_duration(video_path)
        
        return {
            "success": True,
            "video_file": video_path,
            "duration": final_duration,
            "file_size": file_size,
            "width": width,
            "height": height,
            "fps": fps,
            "images_used": len(images),
            "audio_attached": True,
            "method": "ffmpeg_simple"
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg operation timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

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
        else:
            raise Exception("FFprobe failed")
    except:
        # Fallback estimation based on file size (very rough)
        file_size = os.path.getsize(audio_file)
        estimated_duration = file_size / 16000  # Rough estimation
        print(f"[WARNING] Could not get exact audio duration, estimating: {estimated_duration:.1f}s")
        return estimated_duration

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

def check_ffmpeg_available() -> bool:
    """Check if FFmpeg is available via imageio-ffmpeg or system"""
    try:
        # First try imageio-ffmpeg (comes with MoviePy)
        import imageio_ffmpeg as iio
        ffmpeg_exe = iio.get_ffmpeg_exe()
        result = subprocess.run([ffmpeg_exe, '-version'], capture_output=True, timeout=10)
        if result.returncode == 0:
            print(f"[FFMPEG] Found imageio-ffmpeg at: {ffmpeg_exe}")
            return True
    except Exception as e:
        print(f"[FFMPEG] imageio-ffmpeg not available: {e}")
    
    try:
        # Fallback to system FFmpeg
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
        if result.returncode == 0:
            print("[FFMPEG] Found system FFmpeg")
            return True
    except Exception as e:
        print(f"[FFMPEG] System FFmpeg not available: {e}")
    
    return False

def has_caption_data(images: List[Dict]) -> bool:
    """Check if any images have caption text data"""
    for image_data in images:
        if image_data.get("caption_text") or image_data.get("text"):
            return True
    return False

def add_captions_to_video(video_result: Dict[str, Any], images: List[Dict], 
                         output_dir: str, width: int, height: int) -> Dict[str, Any]:
    """
    Add captions to existing video using FFmpeg
    """
    try:
        if not video_result.get("success") or not video_result.get("video_file"):
            return video_result
        
        original_video = video_result["video_file"]
        captioned_video = original_video.replace(".mp4", "_with_captions.mp4")
        
        # Create subtitle file (SRT format)
        srt_file = os.path.join(output_dir, "captions.srt")
        duration_per_segment = video_result.get("duration", 0) / len(images) if images else 0
        
        with open(srt_file, 'w', encoding='utf-8') as f:
            for i, image_data in enumerate(images):
                caption_text = image_data.get("caption_text") or image_data.get("text", "")
                if not caption_text:
                    continue
                
                # Calculate timing
                start_time = i * duration_per_segment
                end_time = (i + 1) * duration_per_segment
                
                # Format SRT timing
                start_srt = format_srt_time(start_time)
                end_srt = format_srt_time(end_time)
                
                f.write(f"{i + 1}\n")
                f.write(f"{start_srt} --> {end_srt}\n")
                f.write(f"{caption_text}\n\n")
        
        # FFmpeg command to burn subtitles into video
        cmd_captions = [
            'ffmpeg', '-y',
            '-i', original_video,
            '-vf', f"subtitles={srt_file}:force_style='FontSize=24,PrimaryColour=&Hffffff,BackColour=&H80000000,Bold=1,Alignment=2'",
            '-c:a', 'copy',  # Copy audio without re-encoding
            captioned_video
        ]
        
        print(f"[CAPTIONS] Adding captions to video...")
        result = subprocess.run(cmd_captions, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"[WARNING] Caption overlay failed: {result.stderr}")
            return video_result  # Return original video if caption fails
        
        # Update result to point to captioned video
        captioned_size = os.path.getsize(captioned_video)
        video_result.update({
            "video_file": captioned_video,
            "file_size": captioned_size,
            "captions_added": True,
            "subtitle_file": srt_file
        })
        
        print(f"[CAPTIONS] Successfully added captions to video")
        
        # Optionally remove original video to save space
        try:
            os.remove(original_video)
        except:
            pass
        
        return video_result
        
    except Exception as e:
        print(f"[ERROR] Caption generation failed: {e}")
        return video_result  # Return original video if caption fails

def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

if __name__ == "__main__":
    # Test FFmpeg availability
    if check_ffmpeg_available():
        print("FFmpeg is available")
    else:
        print("FFmpeg is not available - please install FFmpeg")