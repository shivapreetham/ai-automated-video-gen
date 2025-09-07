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
                           width: int = 1024, height: int = 576, fps: int = 24) -> Dict[str, Any]:
    """
    Create video from multiple images and audio using MoviePy (preferred) or FFmpeg fallback
    Enhanced version ported from local_functions
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
            return create_video_with_moviepy(images, audio_file, video_path, audio_duration, duration_per_image, width, height, fps)
        else:
            return create_video_with_ffmpeg(images, audio_file, video_path, audio_duration, duration_per_image, width, height, fps)
    
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_video_with_moviepy(images: List[Dict], audio_file: str, video_path: str, 
                             audio_duration: float, duration_per_image: float, 
                             width: int, height: int, fps: int) -> Dict[str, Any]:
    """
    Create video using MoviePy - ported from local_functions advanced logic
    """
    try:
        print(f"[VIDEO] Using MoviePy for high-quality video creation...")
        
        # Create video clips from images
        clips = []
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
                
                clips.append(clip)
                
            except Exception as clip_error:
                print(f"[WARNING] Error processing image {i+1}: {clip_error}")
                continue
        
        if not clips:
            raise Exception("No valid images could be processed into clips")
        
        # Concatenate all image clips
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
            fps=fps,
            temp_audiofile=temp_audio_path,
            remove_temp=True,
            verbose=False,
            logger=None
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
    Fallback video creation using FFmpeg only
    """
    try:
        print(f"[VIDEO] Using FFmpeg for video creation...")
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
        
        print(f"[VIDEO] Running FFmpeg video creation...")
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
            "method": "ffmpeg"
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

if __name__ == "__main__":
    # Test FFmpeg availability
    if check_ffmpeg_available():
        print("FFmpeg is available")
    else:
        print("FFmpeg is not available - please install FFmpeg")