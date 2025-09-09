"""
Main Story Video Generation Orchestrator
Coordinates all components of the new segment-based video generation system
"""

import os
import json
import uuid
import time
from typing import Dict, List, Any
from datetime import datetime

# Import all the new backend modules
try:
    from .story_script_generator import generate_story_script
    from .segment_audio_generator import generate_segment_audios
    from .segment_image_generator import generate_segment_images
    from .segment_video_creator import create_segment_videos
    from .video_segment_stitcher import stitch_segment_videos
    from .cleanup_utils import auto_cleanup_after_upload, scheduled_cleanup
    from .caption_metadata_generator import get_caption_generator
except ImportError:
    # Fallback to absolute imports
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from story_script_generator import generate_story_script
    from segment_audio_generator import generate_segment_audios
    from segment_image_generator import generate_segment_images
    from segment_video_creator import create_segment_videos
    from video_segment_stitcher import stitch_segment_videos
    from cleanup_utils import auto_cleanup_after_upload, scheduled_cleanup
    from caption_metadata_generator import get_caption_generator

def generate_story_video(topic: str, script_length: str = "medium", voice: str = "alloy",
                        width: int = 1024, height: int = 576, fps: int = 24,
                        img_style_prompt: str = "cinematic, professional",
                        include_dialogs: bool = True, use_different_voices: bool = True,
                        add_captions: bool = True, add_title_card: bool = True,
                        add_end_card: bool = True, auto_cleanup: bool = False) -> Dict[str, Any]:
    """
    Generate a complete story video using the new segment-based approach
    
    Args:
        topic: Main topic/theme for the story
        script_length: "short", "medium", or "long"
        voice: Primary voice for narration
        width, height: Video dimensions
        fps: Frames per second
        img_style_prompt: Style prompt for image generation
        include_dialogs: Include character dialogs
        use_different_voices: Use different voices for different characters
        add_captions: Add subtitle overlay
        add_title_card: Add opening title card
        add_end_card: Add closing end card
    
    Returns:
        Complete results including final video and all intermediate files
    """
    
    start_time = time.time()
    generation_id = uuid.uuid4().hex[:12]
    
    print(f"[STORY VIDEO] Starting generation for '{topic}' (ID: {generation_id})")
    
    # Create output directory
    output_dir = os.path.join("results", generation_id)
    os.makedirs(output_dir, exist_ok=True)
    
    # Initialize results structure
    results = {
        "generation_id": generation_id,
        "topic": topic,
        "parameters": {
            "script_length": script_length,
            "voice": voice,
            "width": width,
            "height": height,
            "fps": fps,
            "img_style_prompt": img_style_prompt,
            "include_dialogs": include_dialogs,
            "use_different_voices": use_different_voices,
            "add_captions": add_captions,
            "add_title_card": add_title_card,
            "add_end_card": add_end_card
        },
        "output_dir": output_dir,
        "started_at": datetime.now().isoformat(),
        "stages": {},
        "success": False,
        "error": None
    }
    
    try:
        # Stage 1: Generate Story Script
        print(f"[STORY VIDEO] Stage 1: Generating story script...")
        stage_start = time.time()
        
        script_result = generate_story_script(topic, script_length, include_dialogs)
        
        if not script_result:
            raise Exception("Script generation failed")
        
        # Save script
        script_path = os.path.join(output_dir, "story_script.json")
        with open(script_path, 'w', encoding='utf-8') as f:
            json.dump(script_result, f, indent=2, ensure_ascii=False)
        
        results["stages"]["script_generation"] = {
            "success": True,
            "duration": time.time() - stage_start,
            "script_file": script_path,
            "story_title": script_result.get("story_title", ""),
            "segments_count": script_result.get("total_segments", 0),
            "estimated_duration": script_result.get("estimated_duration", 0),
            "has_dialogs": script_result.get("has_dialogs", False),
            "character_count": len(script_result.get("characters", []))
        }
        
        print(f"[STORY VIDEO] Script: '{script_result.get('story_title')}' with {script_result.get('total_segments')} segments")
        
        # Stage 2: Generate Audio for Each Segment
        print(f"[STORY VIDEO] Stage 2: Generating segment audio files...")
        stage_start = time.time()
        
        audio_result = generate_segment_audios(
            script_result, voice, output_dir, use_different_voices
        )
        
        if not audio_result.get("success") or audio_result.get("segments_generated", 0) == 0:
            raise Exception(f"Audio generation failed: {audio_result.get('error', 'Unknown error')}")
        
        # Save audio results
        audio_results_path = os.path.join(output_dir, "audio_results.json")
        with open(audio_results_path, 'w', encoding='utf-8') as f:
            json.dump(audio_result, f, indent=2)
        
        results["stages"]["audio_generation"] = {
            "success": True,
            "duration": time.time() - stage_start,
            "results_file": audio_results_path,
            "segments_generated": audio_result.get("segments_generated", 0),
            "segments_failed": audio_result.get("segments_failed", 0),
            "total_duration": audio_result.get("total_duration", 0),
            "total_file_size": audio_result.get("total_file_size", 0),
            "character_voices": audio_result.get("character_voices", {})
        }
        
        print(f"[STORY VIDEO] Audio: {audio_result.get('segments_generated')} segments ({audio_result.get('total_duration', 0):.1f}s total)")
        
        # Stage 3: Generate Images for Each Segment
        print(f"[STORY VIDEO] Stage 3: Generating segment images...")
        stage_start = time.time()
        
        image_result = generate_segment_images(script_result, output_dir, img_style_prompt)
        
        if not image_result.get("success") or image_result.get("images_generated", 0) == 0:
            raise Exception(f"Image generation failed: {image_result.get('error', 'Unknown error')}")
        
        # Save image results
        image_results_path = os.path.join(output_dir, "image_results.json")
        with open(image_results_path, 'w', encoding='utf-8') as f:
            json.dump(image_result, f, indent=2)
        
        results["stages"]["image_generation"] = {
            "success": True,
            "duration": time.time() - stage_start,
            "results_file": image_results_path,
            "images_generated": image_result.get("images_generated", 0),
            "images_failed": image_result.get("images_failed", 0),
            "total_file_size": image_result.get("total_file_size", 0)
        }
        
        print(f"[STORY VIDEO] Images: {image_result.get('images_generated')} images generated")
        
        # Stage 4: Create Individual Segment Videos
        print(f"[STORY VIDEO] Stage 4: Creating segment videos...")
        stage_start = time.time()
        
        video_result = create_segment_videos(
            script_result, audio_result, image_result, output_dir, width, height, fps
        )
        
        if not video_result.get("success") or video_result.get("videos_created", 0) == 0:
            raise Exception(f"Segment video creation failed: {video_result.get('error', 'Unknown error')}")
        
        # Save video results
        video_results_path = os.path.join(output_dir, "segment_video_results.json")
        with open(video_results_path, 'w', encoding='utf-8') as f:
            json.dump(video_result, f, indent=2)
        
        results["stages"]["segment_video_creation"] = {
            "success": True,
            "duration": time.time() - stage_start,
            "results_file": video_results_path,
            "videos_created": video_result.get("videos_created", 0),
            "videos_failed": video_result.get("videos_failed", 0),
            "total_duration": video_result.get("total_duration", 0),
            "total_file_size": video_result.get("total_file_size", 0)
        }
        
        print(f"[STORY VIDEO] Segment Videos: {video_result.get('videos_created')} videos created")
        
        # Stage 5: Stitch All Segments into Final Video
        print(f"[STORY VIDEO] Stage 5: Stitching final video...")
        stage_start = time.time()
        
        final_result = stitch_segment_videos(
            script_result, video_result, output_dir, add_captions, add_title_card, add_end_card
        )
        
        if not final_result.get("success"):
            raise Exception(f"Video stitching failed: {final_result.get('error', 'Unknown error')}")
        
        # Save final results
        final_results_path = os.path.join(output_dir, "final_video_results.json")
        with open(final_results_path, 'w', encoding='utf-8') as f:
            json.dump(final_result, f, indent=2)
        
        results["stages"]["final_video_stitching"] = {
            "success": True,
            "duration": time.time() - stage_start,
            "results_file": final_results_path,
            "final_video_file": final_result.get("final_video_file"),
            "filename": final_result.get("filename"),
            "duration_seconds": final_result.get("duration_seconds", 0),
            "file_size": final_result.get("file_size", 0),
            "segments_included": final_result.get("segments_included", 0),
            "captions_added": final_result.get("captions_added", False),
            "has_title_card": final_result.get("has_title_card", False),
            "has_end_card": final_result.get("has_end_card", False)
        }
        
        print(f"[STORY VIDEO] Final Video: {final_result.get('filename')} ({final_result.get('duration_seconds', 0):.1f}s)")
        
        # Stage 6: Generate Captions and Metadata
        print(f"[STORY VIDEO] Stage 6: Generating captions and platform metadata...")
        stage_start = time.time()
        
        try:
            caption_generator = get_caption_generator()
            
            # Prepare story info for metadata generation
            story_metadata_input = {
                "title": script_result.get("story_title", topic),
                "summary": script_result.get("story_summary", ""),
                "characters": script_result.get("characters", []),
                "segments": script_result.get("segments", []),
                "domain": topic.split()[0].lower() if " " in topic else "general"  # Simple domain detection
            }
            
            # Generate comprehensive metadata
            video_metadata = caption_generator.generate_video_metadata(
                story_metadata_input, 
                story_metadata_input["domain"],
                platforms=["youtube", "instagram", "tiktok"]
            )
            
            # Save metadata to output directory
            metadata_file = caption_generator.save_metadata_to_file(video_metadata, output_dir)
            
            results["stages"]["metadata_generation"] = {
                "success": True,
                "duration": time.time() - stage_start,
                "metadata_file": metadata_file,
                "platforms_generated": list(video_metadata.get("platform_metadata", {}).keys()),
                "captions_available": bool(video_metadata.get("captions", {}).get("srt_format")),
                "seo_keywords": len(video_metadata.get("seo_data", {}).get("primary_keywords", []))
            }
            
            print(f"[STORY VIDEO] Metadata: Generated for {len(video_metadata.get('platform_metadata', {}))} platforms")
            
        except Exception as e:
            print(f"[STORY VIDEO] Warning: Metadata generation failed: {e}")
            video_metadata = {}
            results["stages"]["metadata_generation"] = {
                "success": False,
                "duration": time.time() - stage_start,
                "error": str(e)
            }
        
        # Complete results
        total_duration = time.time() - start_time
        
        results.update({
            "success": True,
            "completed_at": datetime.now().isoformat(),
            "total_generation_time": total_duration,
            "final_video": {
                "file_path": final_result.get("final_video_file"),
                "filename": final_result.get("filename"),
                "duration_seconds": final_result.get("duration_seconds", 0),
                "file_size_mb": final_result.get("file_size", 0) / (1024 * 1024),
                "width": width,
                "height": height,
                "fps": fps
            },
            "story_info": {
                "title": script_result.get("story_title", ""),
                "summary": script_result.get("story_summary", ""),
                "characters": script_result.get("characters", []),
                "total_segments": script_result.get("total_segments", 0),
                "has_dialogs": script_result.get("has_dialogs", False)
            },
            "video_metadata": video_metadata
        })
        
        # Save complete results
        complete_results_path = os.path.join(output_dir, "complete_generation_results.json")
        with open(complete_results_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        
        print(f"[STORY VIDEO] COMPLETED: '{script_result.get('story_title')}' in {total_duration:.1f}s")
        print(f"[STORY VIDEO] Final video: {final_result.get('filename')}")
        print(f"[STORY VIDEO] Results saved to: {output_dir}")
        
        # Add cleanup flag to results
        results["cleanup_available"] = True
        results["output_directory"] = output_dir
        
        # Perform automatic cleanup if requested
        if auto_cleanup:
            print(f"[STORY VIDEO] Auto-cleanup enabled, cleaning intermediate files...")
            try:
                from .cleanup_utils import cleanup_result_folder
                cleanup_result_folder(output_dir, keep_final_video=True)
                results["auto_cleanup_performed"] = True
                print(f"[STORY VIDEO] Auto-cleanup completed")
            except Exception as cleanup_error:
                print(f"[STORY VIDEO] Auto-cleanup failed: {cleanup_error}")
                results["auto_cleanup_performed"] = False
                results["cleanup_error"] = str(cleanup_error)
        
        return results
        
    except Exception as e:
        error_msg = str(e)
        print(f"[STORY VIDEO] FAILED: {error_msg}")
        
        results.update({
            "success": False,
            "error": error_msg,
            "failed_at": datetime.now().isoformat(),
            "total_generation_time": time.time() - start_time
        })
        
        # Save error results
        try:
            error_results_path = os.path.join(output_dir, "error_results.json")
            with open(error_results_path, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
        except:
            pass
        
        return results

def validate_system_requirements() -> Dict[str, Any]:
    """Validate that all required components are available"""
    
    validation = {
        "system_ready": True,
        "issues": [],
        "warnings": []
    }
    
    # Check FFmpeg (try imageio-ffmpeg first, then system ffmpeg)
    ffmpeg_available = False
    try:
        import imageio_ffmpeg as iio
        import subprocess
        ffmpeg_exe = iio.get_ffmpeg_exe()
        result = subprocess.run([ffmpeg_exe, '-version'], capture_output=True, timeout=10)
        if result.returncode == 0:
            ffmpeg_available = True
    except:
        try:
            import subprocess
            result = subprocess.run(['ffmpeg', '-version'], capture_output=True, timeout=10)
            if result.returncode == 0:
                ffmpeg_available = True
        except:
            pass
    
    if not ffmpeg_available:
        validation["issues"].append("FFmpeg not available")
        validation["system_ready"] = False
    
    # Check MoviePy (optional)
    try:
        import moviepy
        validation["moviepy_available"] = True
    except ImportError:
        validation["moviepy_available"] = False
        validation["warnings"].append("MoviePy not available - will use FFmpeg only")
    
    # Check gTTS (fallback)
    try:
        import gtts
        validation["gtts_available"] = True
    except ImportError:
        validation["gtts_available"] = False
        validation["warnings"].append("gTTS not available - audio fallback limited")
    
    return validation

if __name__ == "__main__":
    # Test system validation
    validation = validate_system_requirements()
    print("System validation:", json.dumps(validation, indent=2))
    
    if validation["system_ready"]:
        print("\n[TEST] Running test generation...")
        result = generate_story_video(
            "cat and dog friendship", 
            "short", 
            "alloy",
            1024, 576, 24,
            "heartwarming, cinematic",
            True, True, True, True, True
        )
        
        if result["success"]:
            print(f"Test completed successfully!")
            print(f"Final video: {result['final_video']['filename']}")
        else:
            print(f"Test failed: {result['error']}")
    else:
        print("System not ready:", validation["issues"])