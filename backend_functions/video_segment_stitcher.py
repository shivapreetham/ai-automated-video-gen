"""
Video Segment Stitching System
Combines individual segment videos into a cohesive final story video with proper transitions and captions
"""

import os
import json
import uuid
import subprocess
import time
from typing import Dict, List, Any, Optional

# Try to import MoviePy for advanced video processing
try:
    from moviepy.editor import VideoFileClip, concatenate_videoclips, CompositeVideoClip
    from moviepy.video.fx import fadeout, fadein
    MOVIEPY_AVAILABLE = True
    print("[STITCHER] MoviePy available for advanced stitching")
except ImportError:
    MOVIEPY_AVAILABLE = False
    print("[STITCHER] MoviePy not available, using FFmpeg only")

def stitch_segment_videos(script_data: Dict[str, Any], video_results: Dict[str, Any],
                         output_dir: str = ".", add_captions: bool = True,
                         add_title_card: bool = True, add_end_card: bool = True) -> Dict[str, Any]:
    """
    Stitch individual segment videos into final cohesive story video
    
    Args:
        script_data: Original script data with story information
        video_results: Results from segment video creation
        output_dir: Directory for final video
        add_captions: Whether to add subtitle overlay
        add_title_card: Whether to add opening title card
        add_end_card: Whether to add closing end card
    
    Returns:
        Dictionary with final video information
    """
    
    segment_videos = video_results.get("segment_videos", [])
    successful_videos = [v for v in segment_videos if v.get("success")]
    
    if not successful_videos:
        return {"success": False, "error": "No successful segment videos to stitch"}
    
    print(f"[STITCHER] Stitching {len(successful_videos)} segment videos...")
    
    # Sort by segment number
    successful_videos.sort(key=lambda x: x["segment_number"])
    
    # Generate final video filename
    timestamp = int(time.time())
    story_title = script_data.get("story_title", "AI Generated Story").replace(" ", "_")
    final_video_name = f'{story_title}_{timestamp}_{uuid.uuid4().hex[:8]}.mp4'
    final_video_path = os.path.join(output_dir, final_video_name)
    
    try:
        # Create video list for stitching
        video_files = [v["video_file"] for v in successful_videos if os.path.exists(v["video_file"])]
        
        if not video_files:
            return {"success": False, "error": "No valid video files found"}
        
        # Choose stitching method
        if MOVIEPY_AVAILABLE:
            result = stitch_with_moviepy(
                video_files, final_video_path, script_data, successful_videos,
                add_title_card, add_end_card
            )
        else:
            result = stitch_with_ffmpeg(
                video_files, final_video_path, script_data, successful_videos,
                add_title_card, add_end_card
            )
        
        if not result.get("success"):
            return result
        
        # Add captions if requested
        if add_captions:
            result = add_story_captions(result, script_data, successful_videos, output_dir)
        
        return result
        
    except Exception as e:
        return {"success": False, "error": f"Stitching failed: {e}"}

def stitch_with_moviepy(video_files: List[str], final_video_path: str, 
                       script_data: Dict[str, Any], segment_videos: List[Dict[str, Any]],
                       add_title_card: bool, add_end_card: bool) -> Dict[str, Any]:
    """Stitch videos using MoviePy with advanced transitions"""
    
    try:
        print("[STITCHER] Using MoviePy for high-quality stitching...")
        
        # Load all video clips
        clips = []
        total_duration = 0
        
        # Add title card if requested
        if add_title_card:
            title_clip = create_title_card_moviepy(script_data)
            if title_clip:
                clips.append(title_clip)
                total_duration += title_clip.duration
        
        # Load segment videos
        for i, video_file in enumerate(video_files):
            if not os.path.exists(video_file):
                print(f"[WARNING] Video file not found: {video_file}")
                continue
            
            print(f"[STITCHER] Loading segment video {i+1}: {os.path.basename(video_file)}")
            clip = VideoFileClip(video_file)
            
            # Add smooth transitions between segments
            if len(clips) > 0:
                # Add crossfade transition
                transition_duration = min(0.5, clip.duration * 0.1)
                clip = clip.fadein(transition_duration)
                if clips[-1]:
                    clips[-1] = clips[-1].fadeout(transition_duration)
            
            clips.append(clip)
            total_duration += clip.duration
        
        # Add end card if requested
        if add_end_card:
            end_clip = create_end_card_moviepy(script_data)
            if end_clip:
                if clips:
                    end_clip = end_clip.fadein(0.5)
                clips.append(end_clip)
                total_duration += end_clip.duration
        
        if not clips:
            return {"success": False, "error": "No valid clips to stitch"}
        
        # Concatenate all clips
        print("[STITCHER] Concatenating clips with transitions...")
        final_video = concatenate_videoclips(clips, method="compose")
        
        # Write final video
        temp_audio_path = os.path.join(os.path.dirname(final_video_path), 'temp_final_audio.m4a')
        
        final_video.write_videofile(
            final_video_path,
            codec='libx264',
            audio_codec='aac',
            fps=24,
            temp_audiofile=temp_audio_path,
            remove_temp=True,
            verbose=False,
            logger=None
        )
        
        # Cleanup
        for clip in clips:
            clip.close()
        final_video.close()
        
        # Get final file information
        file_size = os.path.getsize(final_video_path)
        actual_duration = get_video_duration(final_video_path)
        
        print(f"[STITCHER] Final video created: {os.path.basename(final_video_path)} ({actual_duration:.1f}s)")
        
        return {
            "success": True,
            "final_video_file": final_video_path,
            "filename": os.path.basename(final_video_path),
            "duration_seconds": actual_duration,
            "file_size": file_size,
            "segments_included": len([v for v in segment_videos if v.get("success")]),
            "has_title_card": add_title_card,
            "has_end_card": add_end_card,
            "has_transitions": True,
            "stitching_method": "moviepy"
        }
        
    except Exception as e:
        print(f"[ERROR] MoviePy stitching failed: {e}")
        raise e

def stitch_with_ffmpeg(video_files: List[str], final_video_path: str,
                      script_data: Dict[str, Any], segment_videos: List[Dict[str, Any]],
                      add_title_card: bool, add_end_card: bool) -> Dict[str, Any]:
    """Stitch videos using FFmpeg"""
    
    try:
        print("[STITCHER] Using FFmpeg for video stitching...")
        
        # Create temporary file list for concatenation
        temp_dir = os.path.dirname(final_video_path)
        file_list_path = os.path.join(temp_dir, f'stitch_list_{uuid.uuid4().hex[:8]}.txt')
        
        all_files = []
        
        # Add title card if requested
        if add_title_card:
            title_card_path = create_title_card_ffmpeg(script_data, temp_dir)
            if title_card_path:
                all_files.append(title_card_path)
        
        # Add segment videos
        all_files.extend(video_files)
        
        # Add end card if requested
        if add_end_card:
            end_card_path = create_end_card_ffmpeg(script_data, temp_dir)
            if end_card_path:
                all_files.append(end_card_path)
        
        # Create file list for FFmpeg
        with open(file_list_path, 'w') as f:
            for video_file in all_files:
                f.write(f"file '{os.path.abspath(video_file)}'\n")
        
        # FFmpeg concatenation command
        cmd = [
            'ffmpeg', '-y',
            '-f', 'concat',
            '-safe', '0',
            '-i', file_list_path,
            '-c', 'copy',  # Copy streams without re-encoding for speed
            final_video_path
        ]
        
        print("[STITCHER] Running FFmpeg concatenation...")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            # Fallback: re-encode if copy fails
            print("[STITCHER] Copy method failed, trying with re-encoding...")
            cmd[-2] = 'libx264'  # Replace 'copy' with 'libx264'
            cmd.insert(-1, '-crf')
            cmd.insert(-1, '23')
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            
            if result.returncode != 0:
                raise Exception(f"FFmpeg failed: {result.stderr}")
        
        # Cleanup temporary files
        try:
            os.remove(file_list_path)
            if add_title_card and title_card_path and os.path.exists(title_card_path):
                os.remove(title_card_path)
            if add_end_card and end_card_path and os.path.exists(end_card_path):
                os.remove(end_card_path)
        except:
            pass
        
        # Get final file information
        file_size = os.path.getsize(final_video_path)
        actual_duration = get_video_duration(final_video_path)
        
        print(f"[STITCHER] Final video created: {os.path.basename(final_video_path)} ({actual_duration:.1f}s)")
        
        return {
            "success": True,
            "final_video_file": final_video_path,
            "filename": os.path.basename(final_video_path),
            "duration_seconds": actual_duration,
            "file_size": file_size,
            "segments_included": len([v for v in segment_videos if v.get("success")]),
            "has_title_card": add_title_card,
            "has_end_card": add_end_card,
            "has_transitions": False,
            "stitching_method": "ffmpeg"
        }
        
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "FFmpeg stitching timed out"}
    except Exception as e:
        return {"success": False, "error": str(e)}

def create_title_card_moviepy(script_data: Dict[str, Any]) -> Optional[object]:
    """Create a title card using MoviePy"""
    
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
        
        story_title = script_data.get("story_title", "AI Generated Story")
        story_summary = script_data.get("story_summary", "")
        
        # Create background
        background = ColorClip(size=(1024, 576), color=(0, 20, 40), duration=3.0)
        
        # Create title text
        title_clip = TextClip(
            story_title,
            fontsize=48,
            color='white',
            font='Arial-Bold'
        ).set_position('center').set_duration(3.0)
        
        # Create subtitle if available
        clips = [background, title_clip]
        
        if story_summary:
            subtitle_clip = TextClip(
                story_summary[:100] + "..." if len(story_summary) > 100 else story_summary,
                fontsize=24,
                color='lightblue',
                font='Arial'
            ).set_position(('center', 'bottom')).set_duration(3.0)
            clips.append(subtitle_clip)
        
        title_card = CompositeVideoClip(clips, size=(1024, 576))
        return title_card
        
    except Exception as e:
        print(f"[WARNING] Could not create title card: {e}")
        return None

def create_end_card_moviepy(script_data: Dict[str, Any]) -> Optional[object]:
    """Create an end card using MoviePy"""
    
    try:
        from moviepy.editor import ColorClip, TextClip, CompositeVideoClip
        
        # Create background
        background = ColorClip(size=(1024, 576), color=(20, 20, 20), duration=2.0)
        
        # Create end text
        end_text = TextClip(
            "Thank you for watching!",
            fontsize=36,
            color='white',
            font='Arial'
        ).set_position('center').set_duration(2.0)
        
        end_card = CompositeVideoClip([background, end_text], size=(1024, 576))
        return end_card
        
    except Exception as e:
        print(f"[WARNING] Could not create end card: {e}")
        return None

def create_title_card_ffmpeg(script_data: Dict[str, Any], temp_dir: str) -> Optional[str]:
    """Create a title card using FFmpeg"""
    
    try:
        title_card_path = os.path.join(temp_dir, f'title_card_{uuid.uuid4().hex[:8]}.mp4')
        story_title = script_data.get("story_title", "AI Generated Story")
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', f'color=c=0x001428:size=1024x576:duration=3',
            '-vf', f'drawtext=text=\'{story_title}\':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            title_card_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return title_card_path
        else:
            print(f"[WARNING] Could not create title card: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[WARNING] Title card creation failed: {e}")
        return None

def create_end_card_ffmpeg(script_data: Dict[str, Any], temp_dir: str) -> Optional[str]:
    """Create an end card using FFmpeg"""
    
    try:
        end_card_path = os.path.join(temp_dir, f'end_card_{uuid.uuid4().hex[:8]}.mp4')
        
        cmd = [
            'ffmpeg', '-y',
            '-f', 'lavfi',
            '-i', 'color=c=0x141414:size=1024x576:duration=2',
            '-vf', 'drawtext=text=\'Thank you for watching!\':fontcolor=white:fontsize=36:x=(w-text_w)/2:y=(h-text_h)/2',
            '-c:v', 'libx264',
            '-pix_fmt', 'yuv420p',
            end_card_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            return end_card_path
        else:
            print(f"[WARNING] Could not create end card: {result.stderr}")
            return None
            
    except Exception as e:
        print(f"[WARNING] End card creation failed: {e}")
        return None

def add_story_captions(video_result: Dict[str, Any], script_data: Dict[str, Any],
                      segment_videos: List[Dict[str, Any]], output_dir: str) -> Dict[str, Any]:
    """Add captions to the final stitched video"""
    
    try:
        if not video_result.get("success") or not video_result.get("final_video_file"):
            return video_result
        
        original_video = video_result["final_video_file"]
        captioned_video = original_video.replace(".mp4", "_with_captions.mp4")
        
        # Create comprehensive subtitle file
        srt_file = os.path.join(output_dir, "story_captions.srt")
        
        with open(srt_file, 'w', encoding='utf-8') as f:
            subtitle_number = 1
            current_time = 0
            
            # Add title card caption if present
            if video_result.get("has_title_card"):
                story_title = script_data.get("story_title", "AI Generated Story")
                f.write(f"{subtitle_number}\n")
                f.write(f"00:00:00,000 --> 00:00:03,000\n")
                f.write(f"{story_title}\n\n")
                subtitle_number += 1
                current_time = 3.0
            
            # Add captions for each segment
            segments = script_data.get("segments", [])
            for segment in segments:
                segment_number = segment.get("segment_number")
                segment_video = next((v for v in segment_videos if v["segment_number"] == segment_number), None)
                
                if not segment_video or not segment_video.get("success"):
                    continue
                
                segment_duration = segment_video.get("duration_seconds", 5.0)
                caption_text = segment.get("caption_text", segment.get("text", ""))[:100]
                
                # Format timing
                start_time = format_srt_time(current_time)
                end_time = format_srt_time(current_time + segment_duration)
                
                f.write(f"{subtitle_number}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{caption_text}\n\n")
                
                subtitle_number += 1
                current_time += segment_duration
        
        # Apply captions using FFmpeg
        cmd_captions = [
            'ffmpeg', '-y',
            '-i', original_video,
            '-vf', f"subtitles={srt_file}:force_style='FontSize=20,PrimaryColour=&Hffffff,BackColour=&H80000000,Bold=1,Alignment=2'",
            '-c:a', 'copy',
            captioned_video
        ]
        
        print("[STITCHER] Adding captions to final video...")
        result = subprocess.run(cmd_captions, capture_output=True, text=True, timeout=300)
        
        if result.returncode != 0:
            print(f"[WARNING] Caption overlay failed: {result.stderr}")
            return video_result
        
        # Update result
        captioned_size = os.path.getsize(captioned_video)
        video_result.update({
            "final_video_file": captioned_video,
            "filename": os.path.basename(captioned_video),
            "file_size": captioned_size,
            "captions_added": True,
            "subtitle_file": srt_file
        })
        
        # Remove original if captions successful
        try:
            os.remove(original_video)
        except:
            pass
        
        print("[STITCHER] Captions added successfully")
        return video_result
        
    except Exception as e:
        print(f"[ERROR] Caption addition failed: {e}")
        return video_result

def format_srt_time(seconds: float) -> str:
    """Convert seconds to SRT time format (HH:MM:SS,mmm)"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    millis = int((seconds % 1) * 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"

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
    print("[STITCHER] Video segment stitching system ready")