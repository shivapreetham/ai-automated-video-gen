"""
Backend Flask App - Independent from local_functions
Uses job-wise organization with proper workflow
"""

import os
import sys
import uuid
import threading
import time
from datetime import datetime
from typing import Dict, Any

from flask import Flask, request, jsonify, send_file
from werkzeug.exceptions import BadRequest, NotFound

# Import both old and new video generation systems
from video_generator import generate_video_complete, VideoGenerationError
from backend_functions.story_video_generator import generate_story_video, validate_system_requirements

app = Flask(__name__, static_folder='static')

# In-memory job storage
active_jobs = {}

class VideoJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "queued"  # queued, processing, completed, failed
        self.progress = 0
        self.message = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.result = None
        self.error = None
        self.current_step = ""

# API Endpoints

@app.route("/", methods=["GET", "POST"])
def home():
    """Serve the frontend HTML"""
    try:
        with open('static/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            "service": "AI Video Generator Backend",
            "version": "2.0 - Independent Backend",
            "status": "running",
            "api_docs": "/api"
        })

@app.route("/api", methods=["GET"])
def api_info():
    return jsonify({
        "service": "AI Video Generator Backend",
        "version": "2.0 - Independent Backend",
        "status": "running",
        "workflow": {
            "legacy": [
                "1. Generate script with Gemini (segments based on script_size)",
                "2. Generate audio with ElevenLabs (get actual duration)",
                "3. Generate multiple images with Pollinations (one per segment)", 
                "4. Create video with FFmpeg (images + audio combined)"
            ],
            "story_mode": [
                "1. Generate story script with characters & dialogs",
                "2. Generate per-segment audio with voice variety",
                "3. Generate contextual images per segment (1-3 per segment)",
                "4. Create per-segment videos with proper sync",
                "5. Stitch segments into final story with captions"
            ]
        },
        "parameters": {
            "required": {"topic": "string"},
            "optional": {
                "width": "integer (default: 1024)",
                "height": "integer (default: 576)", 
                "script_length": "string: short/medium/long (default: medium)",
                "voice": "string: nova/alloy/echo/fable (default: alloy)",
                "img_style_prompt": "string (default: 'cinematic, professional')",
                "story_mode": "boolean: use new story-driven system (default: false)",
                "include_dialogs": "boolean: include character dialogs (default: true)",
                "use_different_voices": "boolean: different voices for characters (default: true)",
                "add_captions": "boolean: add subtitle overlay (default: true)"
            }
        },
        "endpoints": {
            "POST /generate-video": "Start video generation",
            "GET /jobs/<job_id>/status": "Check job status", 
            "GET /jobs/<job_id>/download": "Download completed video",
            "GET /jobs/<job_id>/files": "List all job files",
            "GET /jobs": "List all jobs",
            "POST /cleanup": "Clean all job data",
            "GET /system-check": "Validate system requirements"
        }
    })

@app.route("/generate-video", methods=["POST"])
def generate_video():
    """Start video generation with proper workflow"""
    
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        topic = data.get("topic")
        if not topic or not topic.strip():
            raise BadRequest("Topic is required and cannot be empty")
        
        # Get parameters with defaults
        width = int(data.get("width", 1024))
        height = int(data.get("height", 576))
        script_length = data.get("script_length", data.get("script_size", "medium"))  # backward compatibility
        voice = data.get("voice", "alloy")
        img_style_prompt = data.get("img_style_prompt", "cinematic, professional")
        story_mode = bool(data.get("story_mode", False))
        include_dialogs = bool(data.get("include_dialogs", True))
        use_different_voices = bool(data.get("use_different_voices", True))
        add_captions = bool(data.get("add_captions", True))
        
        # Validate parameters
        if script_length not in ["short", "medium", "long"]:
            script_length = "medium"
        if voice not in ["nova", "alloy", "echo", "fable"]:
            voice = "alloy"
        
        if width < 256 or width > 2048:
            width = 1024
        if height < 256 or height > 2048:
            height = 576
        
        # Create job
        job_id = str(uuid.uuid4())
        job = VideoJob(job_id)
        job.message = "Video generation queued"
        active_jobs[job_id] = job
        
        # Start background processing
        params = {
            "job_id": job_id,
            "topic": topic.strip(),
            "width": width,
            "height": height,
            "script_length": script_length,
            "voice": voice,
            "img_style_prompt": img_style_prompt,
            "story_mode": story_mode,
            "include_dialogs": include_dialogs,
            "use_different_voices": use_different_voices,
            "add_captions": add_captions
        }
        
        thread = threading.Thread(target=process_video_job, args=(params,))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "success": True,
            "job_id": job_id,
            "status": "queued",
            "message": "Video generation started",
            "parameters": params,
            "check_status": f"/jobs/{job_id}/status",
            "workflow": "Story Mode: Script → Segment Audio → Segment Images → Segment Videos → Stitch Final" if story_mode else "Legacy: Script → Audio → Images → Video+Audio (FFmpeg)",
            "mode": "story" if story_mode else "legacy"
        })
        
    except BadRequest as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {e}"}), 500

def process_video_job(params: Dict[str, Any]):
    """Background video generation process - supports both legacy and story modes"""
    
    job_id = params["job_id"]
    job = active_jobs[job_id]
    story_mode = params.get("story_mode", False)
    
    try:
        job.status = "processing"
        job.progress = 10
        job.message = "Starting video generation pipeline..."
        job.current_step = "Initializing"
        job.updated_at = datetime.now()
        
        start_time = time.time()
        
        if story_mode:
            # New story-driven system
            job.progress = 15
            job.message = "Using enhanced story generation system..."
            job.current_step = "Story Mode Initialization"
            job.updated_at = datetime.now()
            
            result = generate_story_video(
                topic=params["topic"],
                script_length=params["script_length"],
                voice=params["voice"],
                width=params["width"],
                height=params["height"],
                fps=24,
                img_style_prompt=params["img_style_prompt"],
                include_dialogs=params["include_dialogs"],
                use_different_voices=params["use_different_voices"],
                add_captions=params["add_captions"],
                add_title_card=True,
                add_end_card=True
            )
            
            if not result.get("success"):
                raise VideoGenerationError(result.get("error", "Story generation failed"))
            
            # Map story results to job result format
            job_result = {
                "job_folder": result["output_dir"],
                "video_file": result["final_video"]["file_path"],
                "story_title": result["story_info"]["title"],
                "story_summary": result["story_info"]["summary"],
                "characters": result["story_info"]["characters"],
                "total_segments": result["story_info"]["total_segments"],
                "has_dialogs": result["story_info"]["has_dialogs"],
                "generation_stages": result["stages"],
                "processing_time": result["total_generation_time"],
                "mode": "story"
            }
            
        else:
            # Legacy system
            job.progress = 20
            job.message = "Generating script with Gemini AI..."
            job.current_step = "Script Generation"
            job.updated_at = datetime.now()
            
            job.progress = 40
            job.message = "Generating audio with ElevenLabs..."
            job.current_step = "Audio Generation"
            job.updated_at = datetime.now()
            
            job.progress = 60
            job.message = "Generating images with Pollinations AI..."
            job.current_step = "Image Generation" 
            job.updated_at = datetime.now()
            
            job.progress = 80
            job.message = "Creating video with FFmpeg..."
            job.current_step = "Video Creation"
            job.updated_at = datetime.now()
            
            # Use legacy system
            result = generate_video_complete(
                job_id=job_id,
                topic=params["topic"],
                width=params["width"],
                height=params["height"],
                script_size=params["script_length"]  # Convert parameter name
            )
            
            job_result = {
                "job_folder": f"results/{job_id}",
                "video_file": result["files"]["video"],
                "audio_file": result["files"]["audio"],
                "script_file": result["files"]["script"],
                "images": result["files"]["images"],
                "summary": result["processing_summary"],
                "processing_time": time.time() - start_time,
                "mode": "legacy"
            }
        
        processing_time = time.time() - start_time
        
        # Success!
        job.status = "completed"
        job.progress = 100
        job.message = "Video generation completed successfully"
        job.current_step = "Completed"
        job.updated_at = datetime.now()
        job.result = job_result
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Video generation failed: {e}"
        job.current_step = "Failed"
        job.updated_at = datetime.now()
        print(f"[JOB {job_id}] ERROR: {e}")

@app.route("/jobs/<job_id>/status", methods=["GET"])
def get_job_status(job_id: str):
    """Get detailed job status"""
    
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = active_jobs[job_id]
    
    response = {
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "current_step": job.current_step,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "error": job.error
    }
    
    if job.result:
        response["result"] = job.result
    
    return jsonify(response)

@app.route("/jobs/<job_id>/download", methods=["GET"])
def download_video(job_id: str):
    """Download the final video"""
    
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = active_jobs[job_id]
    
    if job.status != "completed" or not job.result:
        return jsonify({"error": "Video not ready"}), 400
    
    video_file = job.result.get("video_file")
    if not video_file or not os.path.exists(video_file):
        return jsonify({"error": "Video file not found"}), 404
    
    return send_file(
        video_file,
        as_attachment=True,
        download_name=f"video_{job_id}.mp4",
        mimetype="video/mp4"
    )

@app.route("/jobs/<job_id>/files", methods=["GET"])
def list_job_files(job_id: str):
    """List all files for a specific job"""
    
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = active_jobs[job_id]
    
    if job.status != "completed" or not job.result:
        return jsonify({"error": "Job not completed"}), 400
    
    job_folder = f"results/{job_id}"
    
    files = {
        "video": job.result.get("video_file"),
        "audio": job.result.get("audio_file"), 
        "script": job.result.get("script_file"),
        "images": job.result.get("images", []),
        "job_folder": job_folder
    }
    
    return jsonify({
        "job_id": job_id,
        "files": files,
        "summary": job.result.get("summary", {})
    })

@app.route("/jobs", methods=["GET"])
def list_jobs():
    """List all jobs"""
    
    jobs = []
    for job_id, job in active_jobs.items():
        job_info = {
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "message": job.message,
            "current_step": job.current_step,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat()
        }
        
        if job.result and "summary" in job.result:
            job_info["summary"] = job.result["summary"]
        
        jobs.append(job_info)
    
    return jsonify({
        "total_jobs": len(jobs),
        "jobs": jobs
    })

@app.route("/cleanup", methods=["POST"])
def cleanup():
    """Clean up all job data"""
    
    try:
        import shutil
        
        # Clear active jobs
        job_count = len(active_jobs)
        active_jobs.clear()
        
        # Remove results folder
        results_dir = "results"
        if os.path.exists(results_dir):
            shutil.rmtree(results_dir)
            os.makedirs(results_dir, exist_ok=True)
        
        return jsonify({
            "success": True,
            "message": "Cleanup completed",
            "jobs_cleared": job_count,
            "results_folder_reset": True
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route("/system-check", methods=["GET"])
def system_check():
    """Check system requirements and readiness"""
    
    try:
        validation = validate_system_requirements()
        
        return jsonify({
            "system_ready": validation["system_ready"],
            "issues": validation.get("issues", []),
            "warnings": validation.get("warnings", []),
            "components": {
                "ffmpeg_available": len(validation.get("issues", [])) == 0,
                "moviepy_available": validation.get("moviepy_available", False),
                "gtts_available": validation.get("gtts_available", False)
            },
            "recommendation": "All systems ready for video generation!" if validation["system_ready"] else "Please install missing components"
        })
        
    except Exception as e:
        return jsonify({
            "system_ready": False,
            "error": str(e),
            "recommendation": "System check failed - please verify installation"
        }), 500

if __name__ == "__main__":
    print("Starting AI Video Generator Backend...")
    print("Results will be organized by job ID in results/")
    print("Modes: Legacy (simple) + Story Mode (enhanced with characters & dialogs)")
    print("Story Mode: Script -> Segment Audio -> Segment Images -> Segment Videos -> Final Stitch")
    print("Independent backend with enhanced storytelling capabilities")
    
    app.run(host="0.0.0.0", port=8001, debug=True)