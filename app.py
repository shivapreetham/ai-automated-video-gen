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

from video_generator import generate_video_complete, VideoGenerationError

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
        "workflow": [
            "1. Generate script with Gemini (segments based on script_size)",
            "2. Generate audio with ElevenLabs (get actual duration)",
            "3. Generate multiple images with Pollinations (one per segment)", 
            "4. Create video with FFmpeg (images + audio combined)"
        ],
        "parameters": {
            "required": {"topic": "string"},
            "optional": {
                "width": "integer (default: 1024)",
                "height": "integer (default: 576)", 
                "script_size": "string: short/medium/long (default: medium)"
            }
        },
        "endpoints": {
            "POST /generate-video": "Start video generation",
            "GET /jobs/<job_id>/status": "Check job status", 
            "GET /jobs/<job_id>/download": "Download completed video",
            "GET /jobs/<job_id>/files": "List all job files",
            "GET /jobs": "List all jobs",
            "POST /cleanup": "Clean all job data"
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
        script_size = data.get("script_size", "medium")
        
        # Validate parameters
        if script_size not in ["short", "medium", "long"]:
            script_size = "medium"
        
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
            "script_size": script_size
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
            "workflow": "Script → Audio → Images → Video+Audio (FFmpeg)"
        })
        
    except BadRequest as e:
        return jsonify({"success": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"success": False, "error": f"Server error: {e}"}), 500

def process_video_job(params: Dict[str, Any]):
    """Background video generation process"""
    
    job_id = params["job_id"]
    job = active_jobs[job_id]
    
    try:
        job.status = "processing"
        job.progress = 10
        job.message = "Starting video generation pipeline..."
        job.current_step = "Initializing"
        job.updated_at = datetime.now()
        
        # Step 1: Script Generation
        job.progress = 20
        job.message = "Generating script with Gemini AI..."
        job.current_step = "Script Generation"
        job.updated_at = datetime.now()
        
        # Step 2: Audio Generation  
        job.progress = 40
        job.message = "Generating audio with ElevenLabs..."
        job.current_step = "Audio Generation"
        job.updated_at = datetime.now()
        
        # Step 3: Image Generation
        job.progress = 60
        job.message = "Generating images with Pollinations AI..."
        job.current_step = "Image Generation" 
        job.updated_at = datetime.now()
        
        # Step 4: Video Creation
        job.progress = 80
        job.message = "Creating video with FFmpeg..."
        job.current_step = "Video Creation"
        job.updated_at = datetime.now()
        
        # Actually run the complete pipeline
        start_time = time.time()
        result = generate_video_complete(
            job_id=job_id,
            topic=params["topic"],
            width=params["width"],
            height=params["height"],
            script_size=params["script_size"]
        )
        
        processing_time = time.time() - start_time
        
        # Success!
        job.status = "completed"
        job.progress = 100
        job.message = "Video generation completed successfully"
        job.current_step = "Completed"
        job.updated_at = datetime.now()
        job.result = {
            "job_folder": f"results/{job_id}",
            "video_file": result["files"]["video"],
            "audio_file": result["files"]["audio"],
            "script_file": result["files"]["script"],
            "images": result["files"]["images"],
            "summary": result["processing_summary"],
            "processing_time": processing_time
        }
        
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

if __name__ == "__main__":
    print("Starting AI Video Generator Backend...")
    print("Results will be organized by job ID in results/")
    print("Workflow: Script -> Audio -> Images -> Video+Audio")
    print("Independent backend with no local_functions dependency")
    
    app.run(host="0.0.0.0", port=8001, debug=True)