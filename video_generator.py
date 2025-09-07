"""
Main Video Generator - Backend Orchestrator
Coordinates the full video generation pipeline
"""

import os
import json
import uuid
import shutil
from datetime import datetime
from typing import Dict, Any

# Import our backend functions
from backend_functions.gemini_script import generate_script
from backend_functions.elevenlabs_audio import generate_audio
from backend_functions.pollinations_images import generate_images
from backend_functions.ffmpeg_video import create_video_with_audio, check_ffmpeg_available

class VideoGenerationError(Exception):
    pass

def generate_video_complete(job_id: str, topic: str, width: int = 1024, height: int = 576, 
                          script_size: str = "medium") -> Dict[str, Any]:
    """
    Complete video generation pipeline:
    1. Generate script with segments (Gemini)
    2. Generate audio from script (ElevenLabs) 
    3. Generate images for each segment (Pollinations)
    4. Create video combining images + audio (FFmpeg)
    
    All files organized by job_id
    """
    
    print(f"\\n{'='*60}")
    print(f"STARTING VIDEO GENERATION")
    print(f"Job ID: {job_id}")
    print(f"Topic: {topic}")
    print(f"Dimensions: {width}x{height}")
    print(f"Script Size: {script_size}")
    print(f"{'='*60}\\n")
    
    # Create job directory - single folder contains all job files
    job_dir = os.path.join("results", job_id)
    os.makedirs(job_dir, exist_ok=True)
    
    try:
        # Step 1: Generate Script
        print("STEP 1: Generating script with Gemini...")
        script_result = generate_script(topic, script_size)
        
        if not script_result.get("segments"):
            raise VideoGenerationError("No segments generated in script")
        
        # Save script in job folder
        script_file = os.path.join(job_dir, "script.json")
        with open(script_file, 'w', encoding='utf-8') as f:
            json.dump(script_result, f, indent=2)
        
        segments = script_result["segments"]
        full_text = script_result["text"]
        
        print(f"Generated script with {len(segments)} segments")
        print(f"   Estimated duration: {script_result['estimated_duration']:.1f}s")
        
        # Step 2: Generate Audio
        print(f"\\nSTEP 2: Generating audio with ElevenLabs...")
        audio_result = generate_audio(full_text, voice="nova", speed=1.0, output_dir=job_dir)
        
        if not audio_result.get("success"):
            raise VideoGenerationError(f"Audio generation failed: {audio_result.get('error')}")
        
        audio_file = audio_result["audio_file"]
        audio_duration = audio_result["duration_seconds"]
        
        print(f"Generated audio: {os.path.basename(audio_file)}")
        print(f"   Duration: {audio_duration:.1f}s")
        print(f"   File size: {audio_result['file_size']/1024:.1f} KB")
        
        # Step 3: Generate Images
        print(f"\\nSTEP 3: Generating {len(segments)} images with Pollinations...")
        images_result = generate_images(segments, width, height, job_dir)
        
        if not images_result.get("success"):
            raise VideoGenerationError("Image generation completely failed")
        
        images_data = images_result["images"]
        print(f"Generated {len(images_data)} images")
        print(f"   Success rate: {images_result['success_rate']}")
        
        # Step 4: Create Video with Audio
        print(f"\\nSTEP 4: Creating video with FFmpeg...")
        
        if not check_ffmpeg_available():
            raise VideoGenerationError("FFmpeg is not available - please install FFmpeg")
        
        video_result = create_video_with_audio(
            images_data, audio_file, job_dir, width, height, fps=24
        )
        
        if not video_result.get("success"):
            raise VideoGenerationError(f"Video creation failed: {video_result.get('error')}")
        
        final_video = video_result["video_file"]
        video_duration = video_result["duration"]
        
        print(f"Created final video: {os.path.basename(final_video)}")
        print(f"   Duration: {video_duration:.1f}s")
        print(f"   File size: {video_result['file_size']/1024/1024:.1f} MB")
        print(f"   Images used: {video_result['images_used']}")
        
        # Create summary file
        summary = {
            "job_id": job_id,
            "topic": topic,
            "script_size": script_size,
            "dimensions": f"{width}x{height}",
            "generated_at": datetime.now().isoformat(),
            "processing_summary": {
                "script_segments": len(segments),
                "audio_duration": audio_duration,
                "images_generated": len(images_data),
                "video_duration": video_duration,
                "final_file_size_mb": video_result['file_size'] / 1024 / 1024
            },
            "files": {
                "script": script_file,
                "audio": audio_file,
                "video": final_video,
                "images": [img["image_file"] for img in images_data]
            },
            "success": True
        }
        
        summary_file = os.path.join(job_dir, "summary.json")
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2)
        
        print(f"\\n{'='*60}")
        print(f"VIDEO GENERATION COMPLETED SUCCESSFULLY!")
        print(f"Job folder: {job_dir}")
        print(f"Final video: {final_video}")
        print(f"Total duration: {video_duration:.1f}s")
        print(f"{'='*60}\\n")
        
        return summary
        
    except Exception as e:
        error_summary = {
            "job_id": job_id,
            "topic": topic,
            "success": False,
            "error": str(e),
            "generated_at": datetime.now().isoformat()
        }
        
        error_file = os.path.join(job_dir, "error.json")
        with open(error_file, 'w') as f:
            json.dump(error_summary, f, indent=2)
        
        print(f"\\nVIDEO GENERATION FAILED: {e}")
        raise VideoGenerationError(str(e))

if __name__ == "__main__":
    # Test the complete pipeline
    test_job_id = f"test_{uuid.uuid4().hex[:8]}"
    
    try:
        result = generate_video_complete(
            job_id=test_job_id,
            topic="artificial intelligence basics",
            width=1024,
            height=576,
            script_size="short"
        )
        print("Test completed successfully!")
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"Test failed: {e}")