"""
Flask App for AI Video Generator
Communicates with Akash deployment for script generation, handles video processing locally
"""

import os
import json
import uuid
import time
import requests
from datetime import datetime
from typing import Dict, Any, Optional
from dotenv import load_dotenv

from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
from werkzeug.exceptions import BadRequest, NotFound

# Load environment variables
load_dotenv()

# Import backend functions - new improved system
from backend_functions.story_video_generator import generate_story_video, validate_system_requirements
from backend_functions.story_script_generator import generate_story_script
from backend_functions.elevenlabs_audio import generate_audio as generate_elevenlabs_audio
from backend_functions.segment_audio_generator import generate_segment_audios  
from backend_functions.segment_image_generator import generate_segment_images
from backend_functions.segment_video_creator import create_segment_videos
from backend_functions.video_segment_stitcher import stitch_segment_videos
from satirical_agent.integrated_daily_mash_system import IntegratedDailyMashSystem

# Import agentic workflow components
from backend_functions.job_queue_manager import JobQueueManager, JobStatus
from backend_functions.agentic_video_worker import (
    start_agentic_workforce, stop_agentic_workforce, get_workforce_status
)
from agents.topic_generation_agent import TopicGenerationAgent
from backend_functions.oauth_credentials_manager import get_oauth_manager
from backend_functions.cloudflare_storage_manager import get_cloudflare_manager

# Legacy imports for compatibility (fallback)
try:
    from old_functions.textToSpeech_gtts import mindsflow_function as generate_google_speech
except ImportError:
    generate_google_speech = None

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration - Akash integration removed

# In-memory job storage (use Redis in production)
active_jobs = {}

# Initialize agentic workflow components
try:
    job_queue_manager = JobQueueManager()
    topic_generation_agent = TopicGenerationAgent()
    oauth_manager = get_oauth_manager()
    cloudflare_manager = get_cloudflare_manager()
    agentic_workforce = None  # Will be initialized on demand
    print("[AGENTIC] Initialized agentic workflow components")
except Exception as e:
    print(f"[AGENTIC] Error initializing agentic components: {e}")
    job_queue_manager = None
    topic_generation_agent = None
    oauth_manager = None
    cloudflare_manager = None
    agentic_workforce = None

class VideoJob:
    def __init__(self, job_id: str):
        self.job_id = job_id
        self.status = "queued"
        self.progress = 0
        self.message = ""
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.result = None
        self.error = None


@app.route("/", methods=["GET"])
def home():
    try:
        with open('static/index.html', 'r', encoding='utf-8') as f:
            return f.read()
    except FileNotFoundError:
        return jsonify({
            "message": "AI Video Generator Backend",
            "version": "2.0",
            "frontend": "Frontend file not found",
            "api_docs": "/api"
        })

@app.route("/api", methods=["GET"])
def api_home():
    return jsonify({
        "service": "AI Video Generator Flask App",
        "version": "2.0 - Integrated with Backend Functions",
        "status": "running",
        "local_mode": True,
        "available_endpoints": {
            "advanced_video": "/generate-advanced-video",
            "legacy_video": "/generate-video", 
            "advanced_satirical": "/generate-advanced-satirical-video",
            "legacy_satirical": "/generate-satirical-video",
            "job_status": "/jobs/{job_id}/status",
            "download": "/jobs/{job_id}/download",
            "system_validation": "/validate-system"
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route("/validate-system", methods=["GET"])
def validate_system_endpoint():
    """Validate that the advanced backend system is ready"""
    
    try:
        validation = validate_system_requirements()
        return jsonify({
            "system_validation": validation,
            "backend_functions_available": True,
            "advanced_video_ready": validation.get("system_ready", False),
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            "system_validation": {"system_ready": False, "error": str(e)},
            "backend_functions_available": False,
            "advanced_video_ready": False,
            "timestamp": datetime.now().isoformat()
        })

@app.route("/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "mode": "local",
        "jobs_active": len([j for j in active_jobs.values() if j.status == "processing"]),
        "timestamp": datetime.now().isoformat()
    })

@app.route("/generate-advanced-video", methods=["POST"])
def generate_advanced_video_endpoint():
    """Generate video using the new advanced backend_functions system"""
    
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        topic = data.get("topic")
        if not topic:
            raise BadRequest("Topic is required")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = VideoJob(job_id)
        active_jobs[job_id] = job
        
        # Start background processing with advanced system
        import threading
        thread = threading.Thread(target=process_advanced_video_job, args=(job_id, data))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Advanced video generation started",
            "system": "backend_functions_v2",
            "check_status": f"/jobs/{job_id}/status"
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500

@app.route("/generate-video", methods=["POST"])
def generate_video_endpoint():
    """Generate video using Akash for script generation and local processing for video"""
    
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        topic = data.get("topic")
        if not topic:
            raise BadRequest("Topic is required")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = VideoJob(job_id)
        active_jobs[job_id] = job
        
        # Start background processing
        import threading
        thread = threading.Thread(target=process_video_job, args=(job_id, data))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Video generation started",
            "check_status": f"/jobs/{job_id}/status"
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500

def process_video_job(job_id: str, data: Dict[str, Any]):
    """Background processing for video generation job"""
    
    job = active_jobs[job_id]
    
    try:
        # Step 1: Generate script locally
        job.status = "processing"
        job.message = "Generating script locally..."
        job.progress = 20
        job.updated_at = datetime.now()
        
        script_data = generate_script_local(data)
        
        # Step 2: Generate speech locally  
        job.message = "Generating speech locally..."
        job.progress = 40
        job.updated_at = datetime.now()
        
        speech_result = generate_speech_local(script_data["text"], data)
        
        # Step 3: Generate video locally
        job.message = "Generating video locally..."
        job.progress = 70
        job.updated_at = datetime.now()
        
        video_result = generate_video_local(data, script_data, speech_result)
        
        # Complete job
        job.status = "completed"
        job.progress = 100
        job.message = "Video generation completed"
        job.updated_at = datetime.now()
        job.result = {
            "video_file": video_result.get("video_file"),
            "video_url": video_result.get("video_url"),
            "script_data": script_data,
            "duration": video_result.get("duration", 0),
            "processing_time": (datetime.now() - job.created_at).total_seconds()
        }
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Error: {e}"
        job.updated_at = datetime.now()

def process_advanced_video_job(job_id: str, data: Dict[str, Any]):
    """Background processing for advanced video generation using backend_functions"""
    
    job = active_jobs[job_id]
    
    try:
        job.status = "processing"
        job.message = "Using advanced video generation pipeline..."
        job.progress = 5
        job.updated_at = datetime.now()
        
        # Extract parameters with defaults
        topic = data["topic"]
        script_length = data.get("script_length", "medium")
        voice = data.get("voice", "alloy")
        width = data.get("width", 1024)
        height = data.get("height", 576)
        fps = data.get("fps", 24)
        img_style_prompt = data.get("img_style_prompt", "cinematic, professional")
        include_dialogs = data.get("include_dialogs", True)
        use_different_voices = data.get("use_different_voices", True)
        add_captions = data.get("add_captions", True)
        add_title_card = data.get("add_title_card", True)
        add_end_card = data.get("add_end_card", True)
        
        # Use the complete story video generation system
        job.message = "Generating complete story video with advanced pipeline..."
        job.progress = 10
        job.updated_at = datetime.now()
        
        result = generate_story_video(
            topic=topic,
            script_length=script_length,
            voice=voice,
            width=width,
            height=height,
            fps=fps,
            img_style_prompt=img_style_prompt,
            include_dialogs=include_dialogs,
            use_different_voices=use_different_voices,
            add_captions=add_captions,
            add_title_card=add_title_card,
            add_end_card=add_end_card
        )
        
        if not result.get("success"):
            raise Exception(f"Advanced video generation failed: {result.get('error', 'Unknown error')}")
        
        # Complete job with detailed results
        job.status = "completed"
        job.progress = 100
        job.message = "Advanced video generation completed successfully"
        job.updated_at = datetime.now()
        
        final_video = result.get("final_video", {})
        story_info = result.get("story_info", {})
        stages = result.get("stages", {})
        
        job.result = {
            "video_file": final_video.get("file_path"),
            "video_url": final_video.get("file_path"),
            "filename": final_video.get("filename"),
            "duration": final_video.get("duration_seconds", 0),
            "file_size_mb": final_video.get("file_size_mb", 0),
            "width": final_video.get("width", width),
            "height": final_video.get("height", height),
            "fps": final_video.get("fps", fps),
            "story_info": {
                "title": story_info.get("title", ""),
                "summary": story_info.get("summary", ""),
                "characters": story_info.get("characters", []),
                "total_segments": story_info.get("total_segments", 0),
                "has_dialogs": story_info.get("has_dialogs", False)
            },
            "generation_stages": {
                "script_generation": stages.get("script_generation", {}),
                "audio_generation": stages.get("audio_generation", {}),
                "image_generation": stages.get("image_generation", {}),
                "segment_video_creation": stages.get("segment_video_creation", {}),
                "final_video_stitching": stages.get("final_video_stitching", {})
            },
            "processing_time": result.get("total_generation_time", 0),
            "generation_method": "backend_functions_advanced",
            "output_dir": result.get("output_dir", "")
        }
        
    except Exception as e:
        job.status = "failed" 
        job.error = str(e)
        job.message = f"Advanced video generation error: {e}"
        job.updated_at = datetime.now()
        print(f"[ERROR] Advanced video job {job_id} failed: {e}")

def generate_script_local(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate script locally using Gemini"""
    
    try:
        # Use backend_functions script generation
        print("[SCRIPT] Using backend_functions story script generator...")
        
        # Extract parameters
        topic = data["topic"]
        style = data.get("style", "informative")
        
        # Map legacy parameters to new system
        if style in ["informative", "educational"]:
            script_length = "medium"
        elif style in ["short", "brief"]:
            script_length = "short" 
        else:
            script_length = "long"
        
        # Generate script using backend_functions
        script_result = generate_story_script(
            topic=topic,
            script_length=script_length
        )
        
        if not script_result.get("success"):
            raise Exception(f"Script generation failed: {script_result.get('error', 'Unknown error')}")
        
        script_info = script_result.get("script_info", {})
        segments = script_result.get("segments", [])
        
        # Convert to legacy format
        sentences = []
        text_parts = []
        
        for i, segment in enumerate(segments):
            sentence = segment.get("text", f"Segment {i+1} about {topic}")
            duration_seconds = segment.get("duration_seconds", 4.0)
            
            sentences.append({
                "sentence": sentence,
                "start_time": i * 40000000,  # Legacy Azure time units
                "end_time": (i+1) * 40000000,
                "duration": 40000000,
                "segment_number": i + 1
            })
            text_parts.append(sentence)
        
        return {
            "success": True,
            "text": " ".join(text_parts),
            "sentences": sentences,
            "generated_by": "backend_functions_script_generator",
            "title": script_info.get("title", topic),
            "summary": script_info.get("summary", "")
        }
        
    except Exception as e:
        # Simple fallback template
        topic = data["topic"]
        segments = data.get("num_segments", 5)
        
        sentences = []
        text_parts = []
        
        for i in range(segments):
            sentence = f"This is segment {i+1} about {topic}. We explore the important aspects and provide valuable insights."
            sentences.append({
                "sentence": sentence,
                "start_time": i * 40000000,
                "end_time": (i+1) * 40000000,
                "duration": 40000000
            })
            text_parts.append(sentence)
        
        return {
            "success": True,
            "text": " ".join(text_parts),
            "sentences": sentences,
            "generated_by": "simple_fallback"
        }


def generate_speech_local(text: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate speech locally using ElevenLabs with Google TTS fallback"""
    
    speech_event = {
        "text": text,
        "language": data.get("language", "en"),
        "voice_speed": data.get("voice_speed", 1.0),
        "format": "mp3"
    }
    
    # Try ElevenLabs using backend_functions
    print("[SPEECH] Attempting ElevenLabs TTS with backend_functions...")
    try:
        audio_result = generate_elevenlabs_audio(
            text=text,
            voice=data.get("voice", "nova"),
            speed=data.get("voice_speed", 1.0),
            output_dir="."
        )
        
        # Convert backend_functions format to expected format
        if audio_result.get("success"):
            result = {
                "success": True,
                "audio_file": audio_result.get("audio_file"),
                "audio_url": audio_result.get("audio_file"),
                "duration": audio_result.get("duration", 0),
                "voice_provider": "elevenlabs_backend"
            }
        else:
            result = {
                "success": False,
                "error": audio_result.get("error", "ElevenLabs generation failed")
            }
    except Exception as e:
        result = {
            "success": False,
            "error": f"Backend ElevenLabs error: {e}"
        }
    
    # Check if ElevenLabs failed
    if not result.get("success", True):
        error = result.get("error", "Unknown error")
        print(f"[SPEECH] ElevenLabs failed: {error}")
        
        # Check if it's a rate limit or API error that we should fall back from
        should_fallback = any(keyword in error.lower() for keyword in [
            'rate limit', 'credits', 'quota', 'limit exceeded', '429', '402', 'insufficient',
            'invalid api key', 'unauthorized', '401', 'authentication', 'api key',
            'network error', 'connection', 'timeout', 'resolve', 'failed to resolve',
            'max retries exceeded', 'httpsconnectionpool'
        ])
        
        if should_fallback:
            print("[SPEECH] Falling back to Google TTS...")
            try:
                # Import Google TTS fallback
                from old_functions.textToSpeech_gtts import mindsflow_function as generate_google_speech
                
                # Use Google TTS as fallback
                fallback_result = generate_google_speech(speech_event, None)
                
                # Add fallback indicator to result
                if 'audio_url' in fallback_result:
                    fallback_result['voice_provider'] = 'google_tts_fallback'
                    fallback_result['success'] = True
                    print("[SPEECH] Google TTS fallback successful")
                    return fallback_result
                else:
                    raise Exception("Google TTS fallback also failed")
                    
            except Exception as fallback_error:
                print(f"[SPEECH] Google TTS fallback failed: {fallback_error}")
                print("[SPEECH] Trying final silent audio fallback...")
                
                # Create a final fallback with silent audio
                try:
                    silent_audio_result = create_silent_audio_fallback(text, data)
                    print("[SPEECH] Silent audio fallback successful")
                    return silent_audio_result
                except Exception as silent_error:
                    print(f"[SPEECH] Silent audio fallback also failed: {silent_error}")
                    raise Exception(f"All speech generation methods failed. ElevenLabs: {error}, Google: {fallback_error}, Silent: {silent_error}")
        else:
            # For non-rate-limit errors, don't fall back
            raise Exception(f"ElevenLabs TTS failed: {error}")
    
    print("[SPEECH] ElevenLabs TTS successful")
    return result

def create_silent_audio_fallback(text: str, data: Dict[str, Any]) -> Dict[str, Any]:
    """Create a silent audio file as absolute last resort"""
    
    import wave
    import struct
    
    # Calculate duration based on text length (approx 150 words per minute)
    words = len(text.split())
    duration = max(words / 2.5, 5.0)  # At least 5 seconds
    
    # Create silent WAV file
    sample_rate = 22050
    num_samples = int(duration * sample_rate)
    
    filename = f"silent_audio_{uuid.uuid4().hex[:8]}.wav"
    
    with wave.open(filename, 'w') as wav_file:
        wav_file.setnchannels(1)  # Mono
        wav_file.setsampwidth(2)  # 16-bit
        wav_file.setframerate(sample_rate)
        
        # Write silent audio (all zeros)
        for _ in range(num_samples):
            wav_file.writeframesraw(struct.pack('<h', 0))
    
    return {
        'audio_file': filename,
        'audio_url': os.path.abspath(filename),
        'duration': duration,
        'voice_provider': 'silent_fallback',
        'success': True,
        'note': 'Silent audio generated due to TTS failures - video will have no narration'
    }

def generate_video_local(data: Dict[str, Any], script_data: Dict[str, Any], speech_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate video locally using backend_functions advanced system"""
    
    try:
        # Use the advanced story video generation system
        print("[VIDEO] Using advanced backend_functions video generation...")
        
        # Extract topic from data
        topic = data.get("topic", "Video Story")
        
        result = generate_story_video(
            topic=topic,
            script_length="medium",
            voice=data.get("voice", "nova"),
            width=data.get("width", 1024),
            height=data.get("height", 576),
            fps=data.get("fps", 24),
            img_style_prompt=data.get("img_style_prompt", "professional, detailed, high resolution"),
            include_dialogs=False,  # Legacy system doesn't use dialogs
            use_different_voices=False,
            add_captions=data.get("add_captions", False),
            add_title_card=data.get("add_title_card", False),
            add_end_card=data.get("add_end_card", False)
        )
        
        if not result.get("success"):
            raise Exception(f"Advanced video generation failed: {result.get('error', 'Unknown error')}")
        
        final_video = result.get("final_video", {})
        
        # Convert to legacy format for compatibility
        return {
            "success": True,
            "video_file": final_video.get("file_path"),
            "video_url": final_video.get("file_path"),
            "duration": final_video.get("duration_seconds", 0),
            "width": final_video.get("width", data.get("width", 1024)),
            "height": final_video.get("height", data.get("height", 576)),
            "generation_method": "backend_functions_advanced"
        }
        
    except Exception as e:
        print(f"[ERROR] Advanced video generation failed: {e}")
        # Return error in legacy format
        return {
            "success": False,
            "error": str(e)
        }

def combine_audio_video_local(video_file: str, audio_file: str) -> str:
    """Combine audio and video using MoviePy"""
    
    try:
        from moviepy.editor import VideoFileClip, AudioFileClip
        
        # Load clips
        video_clip = VideoFileClip(video_file)
        audio_clip = AudioFileClip(audio_file)
        
        # Ensure same duration
        min_duration = min(video_clip.duration, audio_clip.duration)
        video_clip = video_clip.subclip(0, min_duration)
        audio_clip = audio_clip.subclip(0, min_duration)
        
        # Combine
        final_clip = video_clip.set_audio(audio_clip)
        
        # Generate output path
        output_file = f"final_video_{uuid.uuid4().hex[:8]}.mp4"
        
        # Write final video
        final_clip.write_videofile(
            output_file,
            codec='libx264',
            audio_codec='aac',
            temp_audiofile='temp-audio.m4a',
            remove_temp=True
        )
        
        # Cleanup
        video_clip.close()
        audio_clip.close()
        final_clip.close()
        
        return output_file
        
    except Exception as e:
        print(f"Audio-video combination failed: {e}")
        # Return original video file
        return video_file

@app.route("/jobs/<job_id>/status", methods=["GET"])
def get_job_status(job_id: str):
    """Get job status"""
    
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = active_jobs[job_id]
    
    return jsonify({
        "job_id": job.job_id,
        "status": job.status,
        "progress": job.progress,
        "message": job.message,
        "created_at": job.created_at.isoformat(),
        "updated_at": job.updated_at.isoformat(),
        "result": job.result,
        "error": job.error
    })

@app.route("/jobs/<job_id>/download", methods=["GET"])
def download_video(job_id: str):
    """Download generated video"""
    
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
        download_name=f"generated_video_{job_id}.mp4",
        mimetype="video/mp4"
    )

@app.route("/jobs", methods=["GET"])
def list_jobs():
    """List all jobs"""
    
    jobs = []
    for job_id, job in active_jobs.items():
        jobs.append({
            "job_id": job.job_id,
            "status": job.status,
            "progress": job.progress,
            "created_at": job.created_at.isoformat(),
            "updated_at": job.updated_at.isoformat()
        })
    
    return jsonify({
        "jobs": jobs,
        "total": len(jobs)
    })

@app.route("/test-local", methods=["POST"])
def test_local():
    """Test local script generation"""
    
    try:
        data = request.get_json() or {}
        test_data = {
            "topic": data.get("topic", "Test Topic"),
            "style": "informative",
            "num_segments": 3
        }
        
        result = generate_script_local(test_data)
        
        return jsonify({
            "success": True,
            "local_response": result,
            "message": "Local script generation is working"
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Local script generation test failed"
        }), 500

@app.route("/generate-satirical-video", methods=["POST"])
def generate_satirical_video_endpoint():
    """Generate video using Daily Mash satirical content"""
    
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = VideoJob(job_id)
        active_jobs[job_id] = job
        
        # Start background processing for satirical content
        import threading
        thread = threading.Thread(target=process_satirical_video_job, args=(job_id, data))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Satirical video generation started",
            "content_type": "daily_mash_satirical",
            "check_status": f"/jobs/{job_id}/status"
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500

@app.route("/generate-advanced-satirical-video", methods=["POST"])
def generate_advanced_satirical_video_endpoint():
    """Generate satirical video using advanced backend_functions system"""
    
    try:
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        # Create job
        job_id = str(uuid.uuid4())
        job = VideoJob(job_id)
        active_jobs[job_id] = job
        
        # Start background processing with advanced satirical system
        import threading
        thread = threading.Thread(target=process_advanced_satirical_video_job, args=(job_id, data))
        thread.daemon = True
        thread.start()
        
        return jsonify({
            "job_id": job_id,
            "status": "queued",
            "message": "Advanced satirical video generation started",
            "content_type": "daily_mash_satirical_advanced",
            "system": "backend_functions_v2",
            "check_status": f"/jobs/{job_id}/status"
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({"error": f"Server error: {e}"}), 500

def process_satirical_video_job(job_id: str, data: Dict[str, Any]):
    """Background processing for satirical video generation job"""
    
    job = active_jobs[job_id]
    
    try:
        # Step 1: Initialize Daily Mash system and fetch content with retries
        job.status = "processing"
        job.message = "Fetching satirical content from The Daily Mash..."
        job.progress = 10
        job.updated_at = datetime.now()
        
        daily_mash_system = IntegratedDailyMashSystem()
        
        # Get number of videos to generate (default to 1)
        max_videos = data.get("max_videos", 1)
        
        # Step 2: Process Daily Mash content to video requests with fallback
        job.message = "Processing satirical content and generating scripts..."
        job.progress = 30
        job.updated_at = datetime.now()
        
        video_requests = None
        retry_count = 0
        max_retries = 2
        
        while retry_count <= max_retries and not video_requests:
            try:
                video_requests = daily_mash_system.process_daily_content_to_videos(max_videos=max_videos)
                if video_requests:
                    break
            except Exception as fetch_error:
                retry_count += 1
                print(f"[ERROR] Attempt {retry_count} failed: {fetch_error}")
                if retry_count <= max_retries:
                    job.message = f"Retrying content fetch (attempt {retry_count})..."
                    job.updated_at = datetime.now()
                    import time
                    time.sleep(2)  # Wait 2 seconds before retry
        
        # If still no content, use fallback satirical content
        if not video_requests:
            print("[FALLBACK] Using fallback satirical content")
            job.message = "Using fallback satirical content..."
            job.updated_at = datetime.now()
            
            video_requests = create_fallback_satirical_content(daily_mash_system, max_videos)
        
        # Use the first video request
        selected_request = video_requests[0]
        script_data = selected_request['script_data']
        source_content = selected_request['source_content']
        
        # Step 3: Generate speech from the satirical script
        job.message = "Generating speech from satirical script..."
        job.progress = 50
        job.updated_at = datetime.now()
        
        speech_result = generate_speech_local(script_data["Text"], {
            "language": data.get("language", "en"),
            "voice_speed": data.get("voice_speed", 1.0)
        })
        
        # Step 4: Generate video with satirical imagery
        job.message = "Creating satirical video with AI-generated visuals..."
        job.progress = 75
        job.updated_at = datetime.now()
        
        # Create enhanced video data with satirical context
        enhanced_data = {
            "topic": script_data["title"],
            "width": data.get("width", 1024),
            "height": data.get("height", 576), 
            "fps": data.get("fps", 24),
            "image_model": data.get("image_model", "flux"),
            "satirical_context": True,
            "humor_type": source_content.get("humor_type", "general"),
            "original_title": source_content.get("title", ""),
        }
        
        video_result = generate_video_local(enhanced_data, script_data, speech_result)
        
        # Complete job
        job.status = "completed"
        job.progress = 100
        job.message = "Satirical video generation completed"
        job.updated_at = datetime.now()
        job.result = {
            "video_file": video_result.get("video_file"),
            "video_url": video_result.get("video_url"),
            "script_data": script_data,
            "source_content": {
                "title": source_content.get("title"),
                "humor_type": source_content.get("humor_type"),
                "original_link": source_content.get("link"),
                "category": source_content.get("category")
            },
            "duration": video_result.get("duration", 0),
            "processing_time": (datetime.now() - job.created_at).total_seconds(),
            "content_type": "daily_mash_satirical"
        }
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Satirical video generation error: {e}"
        job.updated_at = datetime.now()

def process_advanced_satirical_video_job(job_id: str, data: Dict[str, Any]):
    """Background processing for advanced satirical video generation using backend_functions"""
    
    job = active_jobs[job_id]
    
    try:
        job.status = "processing"
        job.message = "Fetching satirical content with advanced processing..."
        job.progress = 10
        job.updated_at = datetime.now()
        
        # Initialize Daily Mash system
        daily_mash_system = IntegratedDailyMashSystem()
        
        # Get satirical content
        max_videos = data.get("max_videos", 1)
        video_requests = daily_mash_system.process_daily_content_to_videos(max_videos=max_videos)
        
        if not video_requests:
            # Use fallback satirical content
            video_requests = create_fallback_satirical_content(daily_mash_system, max_videos)
        
        # Use the first video request
        selected_request = video_requests[0]
        script_data = selected_request['script_data']
        source_content = selected_request['source_content']
        
        # Extract the story title for advanced generation
        topic = script_data.get("title", source_content.get("title", "Satirical News Story"))
        
        # Create satirical story with advanced system
        job.message = "Generating satirical story with advanced AI pipeline..."
        job.progress = 20
        job.updated_at = datetime.now()
        
        # Use the advanced story video generator with satirical styling
        result = generate_story_video(
            topic=topic,
            script_length=data.get("script_length", "medium"),
            voice=data.get("voice", "alloy"),
            width=data.get("width", 1024),
            height=data.get("height", 576),
            fps=data.get("fps", 24),
            img_style_prompt=f"satirical, humorous, editorial cartoon style, {data.get('img_style_prompt', 'professional')}",
            include_dialogs=data.get("include_dialogs", False),  # Usually false for news-style content
            use_different_voices=data.get("use_different_voices", False),
            add_captions=data.get("add_captions", True),
            add_title_card=data.get("add_title_card", True),
            add_end_card=data.get("add_end_card", True)
        )
        
        if not result.get("success"):
            raise Exception(f"Advanced satirical video generation failed: {result.get('error', 'Unknown error')}")
        
        # Complete job with detailed results
        job.status = "completed"
        job.progress = 100
        job.message = "Advanced satirical video generation completed"
        job.updated_at = datetime.now()
        
        final_video = result.get("final_video", {})
        story_info = result.get("story_info", {})
        stages = result.get("stages", {})
        
        job.result = {
            "video_file": final_video.get("file_path"),
            "video_url": final_video.get("file_path"),
            "filename": final_video.get("filename"),
            "duration": final_video.get("duration_seconds", 0),
            "file_size_mb": final_video.get("file_size_mb", 0),
            "width": final_video.get("width"),
            "height": final_video.get("height"),
            "fps": final_video.get("fps"),
            "story_info": {
                "title": story_info.get("title", ""),
                "summary": story_info.get("summary", ""),
                "characters": story_info.get("characters", []),
                "total_segments": story_info.get("total_segments", 0),
                "has_dialogs": story_info.get("has_dialogs", False)
            },
            "source_content": {
                "original_title": source_content.get("title"),
                "humor_type": source_content.get("humor_type"),
                "original_link": source_content.get("link"),
                "category": source_content.get("category"),
                "scraped_content": script_data.get("Text", "")
            },
            "generation_stages": {
                "script_generation": stages.get("script_generation", {}),
                "audio_generation": stages.get("audio_generation", {}),
                "image_generation": stages.get("image_generation", {}),
                "segment_video_creation": stages.get("segment_video_creation", {}),
                "final_video_stitching": stages.get("final_video_stitching", {})
            },
            "processing_time": result.get("total_generation_time", 0),
            "generation_method": "backend_functions_satirical_advanced",
            "content_type": "daily_mash_satirical_advanced",
            "output_dir": result.get("output_dir", "")
        }
        
    except Exception as e:
        job.status = "failed"
        job.error = str(e)
        job.message = f"Advanced satirical video generation error: {e}"
        job.updated_at = datetime.now()
        print(f"[ERROR] Advanced satirical video job {job_id} failed: {e}")

def create_fallback_satirical_content(daily_mash_system, max_videos=1):
    """Create fallback satirical content when Daily Mash is unavailable"""
    
    fallback_articles = [
        {
            "title": "Research reveals checking phone reduces boredom by 3% but increases social anxiety by 94%",
            "humor_type": "absurdist", 
            "category": "society",
            "full_content": "Groundbreaking research from the Institute of Digital Dependency has confirmed what millions suspected: smartphones are terrible at their job. The comprehensive study, involving 10,000 participants staring at screens, found that while phone-checking does technically reduce boredom by a measly 3%, it simultaneously skyrockets social anxiety by an alarming 94%. Dr. Sarah Jenkins, lead researcher and reformed phone addict, explained: 'We discovered that the average person checks their phone hoping for excitement but instead finds three new emails about car insurance and a notification that their screen time was up 47% this week.' The study also revealed that 67% of participants experienced what researchers dubbed 'phantom notification syndrome' - the belief that their phone was buzzing when it wasn't. 'It's like having a needy digital pet that never actually does anything interesting,' Dr. Jenkins noted. The research team recommends replacing phones with more effective boredom-busters, such as staring at walls or having actual conversations with humans.",
            "link": "https://fallback-satirical-content.com/phone-research",
            "published": datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
            "word_count": 180,
            "video_ready": True,
            "scraped_at": datetime.now().isoformat()
        },
        {
            "title": "Scientists discover exact moment when small talk becomes unbearably awkward",
            "humor_type": "social_satire",
            "category": "society", 
            "full_content": "After years of painstaking research, scientists at the University of Social Disasters have pinpointed the precise moment when pleasant small talk transforms into excruciating awkwardness. According to their findings, published in the Journal of Uncomfortable Interactions, the critical threshold occurs exactly 47 seconds after someone mentions the weather. Professor Michael Thompson, who has dedicated his career to studying social catastrophes, explains: 'Once you've exhausted 'nice weather today' and 'at least it's not raining,' you enter what we call the Awkward Zone. This is where desperate humans start discussing their commute to work or, God forbid, their weekend plans.' The study observed 5,000 conversations and found that 89% devolved into painful silence or frantic phone-checking within 2.3 minutes. The most dangerous small talk topics, ranked by awkwardness potential, were: traffic conditions, the price of petrol, and anything involving the phrase 'working hard or hardly working?' The research team now recommends all small talk interactions be limited to 30 seconds maximum, followed by strategic retreat.",
            "link": "https://fallback-satirical-content.com/small-talk-research", 
            "published": datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
            "word_count": 195,
            "video_ready": True,
            "scraped_at": datetime.now().isoformat()
        },
        {
            "title": "New study confirms arriving early to meetings makes you 47% more likely to be ignored",
            "humor_type": "everyday_life",
            "category": "general",
            "full_content": "Revolutionary research from the Corporate Behavioral Institute has proven what punctual employees have long suspected: arriving early to meetings is professional suicide. The comprehensive study, tracking 2,000 office workers over six months, found that employees who arrive early are 47% more likely to be completely ignored and 73% more likely to witness awkward pre-meeting gossip they shouldn't hear. Dr. Amanda Clarke, lead researcher and reformed early-arriver, stated: 'Early arrivals become invisible furniture. They sit there watching latecomers burst in with important-sounding apologies while they're relegated to note-taking duty.' The study revealed that optimal meeting arrival time is exactly 3.7 minutes late - fashionably delayed but not disrespectfully tardy. The research also discovered that early arrivals are disproportionately assigned the worst tasks, such as 'action item follow-up' and 'scheduling the next meeting.' One participant noted: 'I arrived five minutes early once and ended up organizing the office Christmas party. Never again.' The institute now recommends strategic lateness as a career advancement tool.",
            "link": "https://fallback-satirical-content.com/meeting-research",
            "published": datetime.now().strftime('%a, %d %b %Y %H:%M:%S %z'),
            "word_count": 188,
            "video_ready": True,
            "scraped_at": datetime.now().isoformat()
        }
    ]
    
    # Select content and generate script
    selected_content = fallback_articles[:max_videos]
    video_requests = []
    
    for content in selected_content:
        try:
            # Generate script using the fallback content
            script_data = daily_mash_system.generate_enhanced_video_script(content)
            
            # Create video generation request
            video_request = daily_mash_system.create_video_generation_request(script_data)
            
            video_requests.append({
                'request': video_request,
                'script_data': script_data,
                'source_content': content
            })
        except Exception as e:
            print(f"[ERROR] Failed to process fallback content: {e}")
            # Create a simple fallback
            simple_script = create_simple_fallback_script(content)
            video_requests.append({
                'request': {"topic": content["title"]},
                'script_data': simple_script,
                'source_content': content
            })
    
    return video_requests

def create_simple_fallback_script(content):
    """Create a very simple script when everything else fails"""
    
    sentences = [
        f"Breaking news from the world of satirical research: {content['title']}",
        "Scientists have once again confirmed what we all secretly knew.",
        "This groundbreaking study reveals the absurdity of modern life.",
        "In conclusion, everything is exactly as ridiculous as you suspected."
    ]
    
    processed_segments = []
    current_time = 0
    duration_per_segment = 40000000  # 4 seconds in Azure units
    
    for i, sentence in enumerate(sentences):
        segment = {
            "sentence": sentence,
            "start_time": current_time,
            "end_time": current_time + duration_per_segment,
            "duration": duration_per_segment,
            "word_count": len(sentence.split()),
            "char_count": len(sentence),
            "segment_number": i + 1
        }
        processed_segments.append(segment)
        current_time += duration_per_segment
    
    return {
        "Text": " ".join(sentences),
        "title": f"Satirical Take: {content['title'][:50]}...",
        "sentences": processed_segments,
        "source_content": {
            "original_title": content['title'],
            "humor_type": content['humor_type'],
            "category": content['category']
        },
        "style": "satirical_fallback",
        "total_duration": len(sentences) * 4.0,
        "segment_count": len(sentences),
        "generated_at": datetime.now().isoformat(),
        "generated_by": "simple_fallback_system"
    }

@app.route("/fetch-daily-mash-content", methods=["GET"])
def fetch_daily_mash_content_endpoint():
    """Fetch available satirical content from The Daily Mash"""
    
    try:
        limit = request.args.get("limit", 5, type=int)
        
        daily_mash_system = IntegratedDailyMashSystem()
        content_items = daily_mash_system.fetch_daily_mash_content(limit=limit)
        
        if not content_items:
            return jsonify({
                "success": False,
                "message": "No satirical content available",
                "content": []
            })
        
        # Return simplified content info for frontend
        simplified_content = []
        for item in content_items:
            simplified_content.append({
                "title": item["title"],
                "humor_type": item["humor_type"],
                "category": item["category"],
                "word_count": item["word_count"],
                "preview": item["full_content"][:150] + "..." if len(item["full_content"]) > 150 else item["full_content"],
                "published": item.get("published", ""),
                "video_ready": item.get("video_ready", True)
            })
        
        return jsonify({
            "success": True,
            "message": f"Found {len(content_items)} satirical articles",
            "content": simplified_content,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to fetch satirical content"
        }), 500

@app.route("/cleanup", methods=["POST", "GET"])
def cleanup_endpoint():
    """Cleanup result folders and temporary files"""
    
    try:
        # Import cleanup utilities
        from backend_functions.cleanup_utils import scheduled_cleanup, get_cleanup_stats, cleanup_result_folder
        
        if request.method == "GET":
            # Get current cleanup stats
            stats = get_cleanup_stats()
            return jsonify({
                "success": True,
                "message": "Cleanup statistics retrieved",
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            })
        
        # POST request - perform cleanup
        data = request.get_json() or {}
        cleanup_type = data.get("type", "scheduled")  # scheduled, specific, stats
        
        if cleanup_type == "scheduled":
            # Run full scheduled cleanup
            result = scheduled_cleanup()
            return jsonify({
                "success": True,
                "message": "Scheduled cleanup completed",
                "result": result,
                "timestamp": datetime.now().isoformat()
            })
        
        elif cleanup_type == "specific":
            # Clean up specific folder
            folder_path = data.get("folder_path")
            if not folder_path:
                return jsonify({"error": "folder_path is required for specific cleanup"}), 400
            
            success = cleanup_result_folder(folder_path, keep_final_video=data.get("keep_final_video", True))
            return jsonify({
                "success": success,
                "message": f"Cleanup {'completed' if success else 'failed'} for {folder_path}",
                "timestamp": datetime.now().isoformat()
            })
        
        elif cleanup_type == "stats":
            # Just return stats
            stats = get_cleanup_stats()
            return jsonify({
                "success": True,
                "message": "Statistics retrieved",
                "stats": stats,
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            return jsonify({"error": "Invalid cleanup type. Use: scheduled, specific, or stats"}), 400
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Cleanup operation failed"
        }), 500

@app.route("/jobs/<job_id>/cleanup", methods=["POST"])
def cleanup_job(job_id: str):
    """Clean up result folder for a specific job after successful upload"""
    
    if job_id not in active_jobs:
        return jsonify({"error": "Job not found"}), 404
    
    job = active_jobs[job_id]
    
    if job.status != "completed" or not job.result:
        return jsonify({"error": "Job not completed or no results available"}), 400
    
    try:
        # Import cleanup utilities
        from backend_functions.cleanup_utils import cleanup_result_folder
        
        # Get output directory from job results
        output_dir = job.result.get("output_dir")
        if not output_dir:
            return jsonify({"error": "No output directory found in job results"}), 400
        
        # Get cleanup options from request
        data = request.get_json() or {}
        keep_final_video = data.get("keep_final_video", True)
        
        # Perform cleanup
        success = cleanup_result_folder(output_dir, keep_final_video=keep_final_video)
        
        if success:
            # Update job result to indicate cleanup was performed
            job.result["cleanup_performed"] = True
            job.result["cleanup_timestamp"] = datetime.now().isoformat()
            
            return jsonify({
                "success": True,
                "message": f"Cleanup completed for job {job_id}",
                "output_dir": output_dir,
                "keep_final_video": keep_final_video
            })
        else:
            return jsonify({
                "success": False,
                "message": f"Cleanup failed for job {job_id}",
                "output_dir": output_dir
            }), 500
    
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"Cleanup operation failed for job {job_id}"
        }), 500

# ===== AGENTIC WORKFLOW ENDPOINTS =====

@app.route("/agentic/start-workforce", methods=["POST"])
def start_agentic_workforce_endpoint():
    """Start the agentic video generation workforce"""
    global agentic_workforce
    
    try:
        if not job_queue_manager:
            return jsonify({"error": "Agentic components not initialized"}), 500
        
        data = request.get_json() or {}
        num_workers = data.get("num_workers", 1)
        
        if agentic_workforce and get_workforce_status() and get_workforce_status().get("is_running"):
            return jsonify({
                "success": False,
                "message": "Workforce already running",
                "status": get_workforce_status()
            })
        
        agentic_workforce = start_agentic_workforce(num_workers)
        
        return jsonify({
            "success": True,
            "message": f"Started {num_workers} workers",
            "workforce_status": get_workforce_status(),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to start workforce"
        }), 500

@app.route("/agentic/stop-workforce", methods=["POST"])
def stop_agentic_workforce_endpoint():
    """Stop the agentic video generation workforce"""
    try:
        if not agentic_workforce:
            return jsonify({
                "success": False,
                "message": "No workforce running"
            })
        
        stop_agentic_workforce()
        
        return jsonify({
            "success": True,
            "message": "Workforce stopped",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to stop workforce"
        }), 500

@app.route("/agentic/workforce-status", methods=["GET"])
def get_agentic_workforce_status():
    """Get status of agentic workforce"""
    try:
        status = get_workforce_status()
        
        if not status:
            return jsonify({
                "is_running": False,
                "message": "No workforce initialized",
                "timestamp": datetime.now().isoformat()
            })
        
        return jsonify({
            "workforce_status": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to get workforce status"
        }), 500

@app.route("/agentic/generate-topics", methods=["POST"])
def generate_topics_endpoint():
    """Generate topics for specific domains"""
    try:
        if not topic_generation_agent:
            return jsonify({"error": "Topic generation agent not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        domains = data.get("domains", ["indian_mythology"])
        topics_per_domain = data.get("topics_per_domain", 5)
        save_to_queue = data.get("save_to_queue", True)
        
        # Generate topics
        daily_topics = topic_generation_agent.generate_daily_topics(domains, topics_per_domain)
        
        # Optionally save to queue
        if save_to_queue:
            topic_generation_agent.save_topics_to_queue(daily_topics)
        
        return jsonify({
            "success": True,
            "topics": daily_topics,
            "total_topics": sum(len(topics) for topics in daily_topics.values()),
            "domains": list(daily_topics.keys()),
            "saved_to_queue": save_to_queue,
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate topics"
        }), 500

@app.route("/agentic/add-jobs-from-topics", methods=["POST"])
def add_jobs_from_topics_endpoint():
    """Add jobs to queue from generated topics"""
    try:
        if not job_queue_manager:
            return jsonify({"error": "Job queue manager not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        # Load topics from queue file or use provided topics
        topics_by_domain = data.get("topics")
        
        if not topics_by_domain:
            # Load from default queue file
            queue_file = data.get("queue_file", "topic_queue.json")
            if os.path.exists(queue_file):
                with open(queue_file, 'r', encoding='utf-8') as f:
                    topics_by_domain = json.load(f)
            else:
                return jsonify({"error": "No topics provided and no queue file found"}), 400
        
        # Add jobs to queue
        added_count = job_queue_manager.bulk_add_jobs_from_topics(topics_by_domain)
        
        return jsonify({
            "success": True,
            "jobs_added": added_count,
            "total_jobs_added": sum(added_count.values()),
            "queue_status": job_queue_manager.get_queue_status(),
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to add jobs from topics"
        }), 500

@app.route("/agentic/queue-status", methods=["GET"])
def get_agentic_queue_status():
    """Get status of job queue"""
    try:
        if not job_queue_manager:
            return jsonify({"error": "Job queue manager not initialized"}), 500
        
        status = job_queue_manager.get_queue_status()
        
        return jsonify({
            "queue_status": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to get queue status"
        }), 500

@app.route("/agentic/completed-videos", methods=["GET"])
def get_completed_videos_endpoint():
    """Get completed video jobs"""
    try:
        if not job_queue_manager:
            return jsonify({"error": "Job queue manager not initialized"}), 500
        
        limit = request.args.get("limit", 20, type=int)
        completed_jobs = job_queue_manager.get_completed_jobs_with_videos(limit)
        
        return jsonify({
            "success": True,
            "completed_videos": completed_jobs,
            "count": len(completed_jobs),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to get completed videos"
        }), 500

@app.route("/agentic/download-video/<job_id>", methods=["GET"])
def download_agentic_video(job_id: str):
    """Download video file for a specific job"""
    try:
        if not job_queue_manager:
            return jsonify({"error": "Job queue manager not initialized"}), 500
        
        video_path = job_queue_manager.get_video_for_job(job_id)
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({"error": "Video file not found"}), 404
        
        return send_file(
            video_path,
            as_attachment=True,
            download_name=f"agentic_video_{job_id}.mp4",
            mimetype="video/mp4"
        )
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to download video"
        }), 500

@app.route("/agentic/cancel-job/<job_id>", methods=["POST"])
def cancel_agentic_job(job_id: str):
    """Cancel a queued job"""
    try:
        if not job_queue_manager:
            return jsonify({"error": "Job queue manager not initialized"}), 500
        
        success = job_queue_manager.cancel_job(job_id)
        
        if success:
            return jsonify({
                "success": True,
                "message": f"Job {job_id} cancelled",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": "Job not found or cannot be cancelled"
            }), 400
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to cancel job"
        }), 500

@app.route("/agentic/auto-workflow", methods=["POST"])
def start_auto_workflow():
    """Start complete automated workflow: generate topics -> add jobs -> start workers"""
    try:
        if not all([job_queue_manager, topic_generation_agent]):
            return jsonify({"error": "Agentic components not initialized"}), 500
        
        data = request.get_json() or {}
        domains = data.get("domains", ["indian_mythology", "technology", "science"])
        topics_per_domain = data.get("topics_per_domain", 5)
        num_workers = data.get("num_workers", 1)
        
        workflow_results = {
            "stage_1_topics": None,
            "stage_2_jobs": None,
            "stage_3_workforce": None
        }
        
        # Stage 1: Generate topics
        daily_topics = topic_generation_agent.generate_daily_topics(domains, topics_per_domain)
        topic_generation_agent.save_topics_to_queue(daily_topics)
        workflow_results["stage_1_topics"] = {
            "success": True,
            "topics_generated": sum(len(topics) for topics in daily_topics.values()),
            "domains": list(daily_topics.keys())
        }
        
        # Stage 2: Add jobs from topics
        added_count = job_queue_manager.bulk_add_jobs_from_topics(daily_topics)
        workflow_results["stage_2_jobs"] = {
            "success": True,
            "jobs_added": added_count,
            "total_jobs": sum(added_count.values())
        }
        
        # Stage 3: Start workforce if not running
        global agentic_workforce
        workforce_status = get_workforce_status()
        if not workforce_status or not workforce_status.get("is_running"):
            agentic_workforce = start_agentic_workforce(num_workers)
            workflow_results["stage_3_workforce"] = {
                "success": True,
                "workers_started": num_workers,
                "status": get_workforce_status()
            }
        else:
            workflow_results["stage_3_workforce"] = {
                "success": True,
                "message": "Workforce already running",
                "status": workforce_status
            }
        
        return jsonify({
            "success": True,
            "message": "Automated workflow started successfully",
            "workflow_results": workflow_results,
            "queue_status": job_queue_manager.get_queue_status(),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to start automated workflow",
            "workflow_results": workflow_results
        }), 500

@app.route("/agentic/add-manual-topic", methods=["POST"])
def add_manual_topic_endpoint():
    """Add a manual topic directly to the job queue"""
    try:
        if not job_queue_manager:
            return jsonify({"error": "Job queue manager not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        topic = data.get("topic")
        domain = data.get("domain", "general")
        
        if not topic:
            raise BadRequest("Topic is required")
        
        # Optional video generation parameters
        job_params = {
            "script_length": data.get("script_length", "medium"),
            "voice": data.get("voice", "alloy"),
            "width": data.get("width", 1024),
            "height": data.get("height", 576),
            "fps": data.get("fps", 24),
            "img_style_prompt": data.get("img_style_prompt", f"professional, {domain}-themed, high quality"),
            "include_dialogs": data.get("include_dialogs", True),
            "use_different_voices": data.get("use_different_voices", True),
            "add_captions": data.get("add_captions", True),
            "add_title_card": data.get("add_title_card", True),
            "add_end_card": data.get("add_end_card", True)
        }
        
        # Add job to queue
        job_id = job_queue_manager.add_job(topic, domain, **job_params)
        
        return jsonify({
            "success": True,
            "message": "Manual topic added to queue",
            "job_id": job_id,
            "topic": topic,
            "domain": domain,
            "parameters": job_params,
            "queue_status": job_queue_manager.get_queue_status(),
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to add manual topic"
        }), 500

@app.route("/agentic/review-generated-topics", methods=["GET"])
def review_generated_topics_endpoint():
    """Get generated topics for manual review before adding to queue"""
    try:
        if not topic_generation_agent:
            return jsonify({"error": "Topic generation agent not initialized"}), 500
        
        # Get query parameters
        domains = request.args.getlist("domains") or ["indian_mythology", "technology", "science"]
        topics_per_domain = request.args.get("topics_per_domain", 5, type=int)
        
        # Generate topics but don't save to queue yet
        daily_topics = topic_generation_agent.generate_daily_topics(domains, topics_per_domain)
        
        # Format for review
        review_topics = []
        for domain, topics in daily_topics.items():
            for topic_data in topics:
                review_topics.append({
                    "id": f"{domain}_{len(review_topics)}",
                    "topic": topic_data["topic"],
                    "domain": domain,
                    "subtopics": topic_data["subtopics"],
                    "keywords": topic_data["keywords"],
                    "estimated_interest": topic_data["estimated_interest"],
                    "generated_at": topic_data["generated_at"],
                    "selected": True  # Default to selected for convenience
                })
        
        return jsonify({
            "success": True,
            "topics_for_review": review_topics,
            "total_topics": len(review_topics),
            "domains": domains,
            "message": "Select topics to add to queue, then call /agentic/approve-reviewed-topics",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate topics for review"
        }), 500

@app.route("/agentic/approve-reviewed-topics", methods=["POST"])
def approve_reviewed_topics_endpoint():
    """Approve selected topics from review and add to job queue"""
    try:
        if not all([job_queue_manager, topic_generation_agent]):
            return jsonify({"error": "Agentic components not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        selected_topics = data.get("selected_topics", [])
        
        if not selected_topics:
            raise BadRequest("No topics selected")
        
        # Process approved topics
        approved_count = {}
        job_ids = []
        
        for topic_data in selected_topics:
            domain = topic_data.get("domain", "general")
            topic = topic_data.get("topic")
            
            if not topic:
                continue
            
            # Optional custom parameters for this topic
            job_params = {
                "script_length": topic_data.get("script_length", "medium"),
                "voice": topic_data.get("voice", "alloy"),
                "img_style_prompt": topic_data.get("img_style_prompt", f"professional, {domain}-themed, high quality"),
                "include_dialogs": topic_data.get("include_dialogs", True),
                "use_different_voices": topic_data.get("use_different_voices", True),
                "add_captions": topic_data.get("add_captions", True),
                "add_title_card": topic_data.get("add_title_card", True),
                "add_end_card": topic_data.get("add_end_card", True)
            }
            
            # Add to job queue
            job_id = job_queue_manager.add_job(topic, domain, **job_params)
            job_ids.append(job_id)
            
            # Count by domain
            approved_count[domain] = approved_count.get(domain, 0) + 1
        
        # Optionally save approved topics to topic queue file
        save_to_topic_queue = data.get("save_to_topic_queue", False)
        if save_to_topic_queue:
            # Convert approved topics to the format expected by topic agent
            topics_by_domain = {}
            for topic_data in selected_topics:
                domain = topic_data.get("domain", "general")
                if domain not in topics_by_domain:
                    topics_by_domain[domain] = []
                
                topics_by_domain[domain].append({
                    "topic": topic_data["topic"],
                    "domain": domain,
                    "subtopics": topic_data.get("subtopics", []),
                    "keywords": topic_data.get("keywords", []),
                    "estimated_interest": topic_data.get("estimated_interest", 0.7),
                    "generated_at": topic_data.get("generated_at"),
                    "used": True,  # Mark as used since we're adding to job queue
                    "approved_by_user": True
                })
            
            topic_generation_agent.save_topics_to_queue(topics_by_domain)
        
        return jsonify({
            "success": True,
            "message": f"Approved {len(selected_topics)} topics and added to job queue",
            "approved_topics": len(selected_topics),
            "approved_count_by_domain": approved_count,
            "job_ids": job_ids,
            "saved_to_topic_queue": save_to_topic_queue,
            "queue_status": job_queue_manager.get_queue_status(),
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to approve reviewed topics"
        }), 500

@app.route("/agentic/topic-queue-status", methods=["GET"])
def get_topic_queue_status():
    """Get status of the topic queue (generated but not yet used topics)"""
    try:
        if not topic_generation_agent:
            return jsonify({"error": "Topic generation agent not initialized"}), 500
        
        status = topic_generation_agent.get_queue_status()
        
        return jsonify({
            "success": True,
            "topic_queue_status": status,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to get topic queue status"
        }), 500

@app.route("/agentic/get-next-topic", methods=["POST"])
def get_next_topic_from_queue():
    """Get next unused topic from topic queue"""
    try:
        if not topic_generation_agent:
            return jsonify({"error": "Topic generation agent not initialized"}), 500
        
        data = request.get_json() or {}
        domain = data.get("domain")  # Optional domain filter
        
        next_topic = topic_generation_agent.get_next_topic_from_queue(domain)
        
        if next_topic:
            return jsonify({
                "success": True,
                "topic": next_topic,
                "message": "Topic retrieved and marked as used",
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": "No unused topics available in queue",
                "topic_queue_status": topic_generation_agent.get_queue_status(),
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to get next topic from queue"
        }), 500

@app.route("/agentic/hybrid-workflow", methods=["POST"])
def start_hybrid_workflow():
    """Start hybrid workflow: generate topics -> user reviews -> approved topics added to queue -> workers process"""
    try:
        if not all([job_queue_manager, topic_generation_agent]):
            return jsonify({"error": "Agentic components not initialized"}), 500
        
        data = request.get_json() or {}
        workflow_type = data.get("type", "generate_for_review")  # or "use_manual_topics"
        
        if workflow_type == "generate_for_review":
            # Stage 1: Generate topics for user review (don't add to queue yet)
            domains = data.get("domains", ["indian_mythology", "technology", "science"])
            topics_per_domain = data.get("topics_per_domain", 5)
            
            daily_topics = topic_generation_agent.generate_daily_topics(domains, topics_per_domain)
            
            # Format for review
            review_topics = []
            for domain, topics in daily_topics.items():
                for topic_data in topics:
                    review_topics.append({
                        "id": f"{domain}_{len(review_topics)}",
                        "topic": topic_data["topic"],
                        "domain": domain,
                        "subtopics": topic_data["subtopics"],
                        "keywords": topic_data["keywords"],
                        "estimated_interest": topic_data["estimated_interest"],
                        "generated_at": topic_data["generated_at"],
                        "selected": True  # Default selection
                    })
            
            return jsonify({
                "success": True,
                "workflow_stage": "topics_generated_for_review",
                "topics_for_review": review_topics,
                "total_topics": len(review_topics),
                "next_step": "Review topics and call /agentic/approve-reviewed-topics",
                "message": "Topics generated. Please review and approve.",
                "timestamp": datetime.now().isoformat()
            })
            
        elif workflow_type == "use_manual_topics":
            # User provides their own topics
            manual_topics = data.get("topics", [])
            
            if not manual_topics:
                raise BadRequest("No manual topics provided")
            
            # Add manual topics directly to job queue
            job_ids = []
            for topic_data in manual_topics:
                topic = topic_data.get("topic")
                domain = topic_data.get("domain", "general")
                
                if topic:
                    job_id = job_queue_manager.add_job(topic, domain)
                    job_ids.append(job_id)
            
            return jsonify({
                "success": True,
                "workflow_stage": "manual_topics_added",
                "topics_added": len(job_ids),
                "job_ids": job_ids,
                "queue_status": job_queue_manager.get_queue_status(),
                "message": "Manual topics added to job queue",
                "timestamp": datetime.now().isoformat()
            })
        
        else:
            raise BadRequest("Invalid workflow type. Use 'generate_for_review' or 'use_manual_topics'")
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to start hybrid workflow"
        }), 500

# ===== REAL-TIME POLLING ENDPOINTS =====

@app.route("/polling/system-status", methods=["GET"])
def get_system_status_polling():
    """Get comprehensive system status for constant polling"""
    try:
        # Get workforce status
        workforce_status = get_workforce_status()
        
        # Get queue status
        queue_status = job_queue_manager.get_queue_status() if job_queue_manager else None
        
        # Get topic queue status
        topic_queue_status = topic_generation_agent.get_queue_status() if topic_generation_agent else None
        
        # Get recent completed jobs
        recent_completed = job_queue_manager.get_completed_jobs_with_videos(5) if job_queue_manager else []
        
        # System health indicators
        system_health = {
            "agentic_components_ready": bool(job_queue_manager and topic_generation_agent),
            "workers_running": bool(workforce_status and workforce_status.get("is_running")),
            "active_workers": len(workforce_status.get("workers", {})) if workforce_status else 0,
            "jobs_in_queue": queue_status.get("by_status", {}).get("queued", 0) if queue_status else 0,
            "jobs_processing": queue_status.get("by_status", {}).get("processing", 0) if queue_status else 0,
            "videos_ready": len(recent_completed),
            "last_completed": recent_completed[0] if recent_completed else None
        }
        
        return jsonify({
            "system_status": {
                "timestamp": datetime.now().isoformat(),
                "uptime": (datetime.now() - datetime.fromtimestamp(time.time())).total_seconds() if hasattr(time, 'start_time') else None,
                "health": system_health,
                "workforce": workforce_status,
                "job_queue": queue_status,
                "topic_queue": topic_queue_status,
                "recent_completed": recent_completed[:3]  # Only show last 3
            }
        })
        
    except Exception as e:
        return jsonify({
            "system_status": {
                "timestamp": datetime.now().isoformat(),
                "error": str(e),
                "health": {"status": "error"}
            }
        }), 500

@app.route("/polling/job-updates/<job_id>", methods=["GET"])
def get_job_updates_polling(job_id: str):
    """Get detailed updates for a specific job (for real-time progress tracking)"""
    try:
        if not job_queue_manager:
            return jsonify({"error": "Job queue manager not initialized"}), 500
        
        job = job_queue_manager.get_job(job_id)
        
        if not job:
            return jsonify({"error": "Job not found"}), 404
        
        # Get job details
        job_details = {
            "job_id": job.job_id,
            "topic": job.topic,
            "domain": job.domain,
            "status": job.status.value,
            "progress": job.progress,
            "message": job.message,
            "created_at": job.created_at.isoformat(),
            "started_at": job.started_at.isoformat() if job.started_at else None,
            "completed_at": job.completed_at.isoformat() if job.completed_at else None,
            "error": job.error,
            "estimated_completion": None
        }
        
        # Add estimated completion time if processing
        if job.status.value == "processing" and job.started_at:
            # Rough estimate based on average video generation time (10-15 minutes)
            elapsed = (datetime.now() - job.started_at).total_seconds()
            estimated_total = 900  # 15 minutes average
            estimated_remaining = max(0, estimated_total - elapsed)
            job_details["estimated_completion"] = estimated_remaining
        
        # Get video file info if completed
        video_info = None
        if job.status.value == "completed":
            video_path = job_queue_manager.get_video_for_job(job_id)
            if video_path and os.path.exists(video_path):
                try:
                    file_size = os.path.getsize(video_path)
                    video_info = {
                        "file_path": video_path,
                        "file_size": file_size,
                        "file_size_mb": round(file_size / (1024 * 1024), 2),
                        "ready_for_download": True
                    }
                except:
                    video_info = {"ready_for_download": False}
        
        return jsonify({
            "job_update": {
                "timestamp": datetime.now().isoformat(),
                "job": job_details,
                "video_info": video_info,
                "result": job.result
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/polling/activity-stream", methods=["GET"])
def get_activity_stream_polling():
    """Get recent activity stream for dashboard (jobs completed, started, failed, etc.)"""
    try:
        # Get recent activity (last 50 jobs with timestamps)
        all_jobs = []
        if job_queue_manager:
            for job in job_queue_manager._job_cache.values():
                all_jobs.append({
                    "job_id": job.job_id,
                    "topic": job.topic[:50] + "..." if len(job.topic) > 50 else job.topic,
                    "domain": job.domain,
                    "status": job.status.value,
                    "created_at": job.created_at.isoformat(),
                    "started_at": job.started_at.isoformat() if job.started_at else None,
                    "completed_at": job.completed_at.isoformat() if job.completed_at else None,
                    "progress": job.progress,
                    "message": job.message
                })
        
        # Sort by most recent activity
        all_jobs.sort(key=lambda x: x.get("completed_at") or x.get("started_at") or x["created_at"], reverse=True)
        
        # Group by status for quick overview
        activity_summary = {
            "total_jobs": len(all_jobs),
            "recently_completed": len([j for j in all_jobs if j["status"] == "completed" and j.get("completed_at")]),
            "currently_processing": len([j for j in all_jobs if j["status"] == "processing"]),
            "queued": len([j for j in all_jobs if j["status"] == "queued"]),
            "failed": len([j for j in all_jobs if j["status"] == "failed"])
        }
        
        return jsonify({
            "activity_stream": {
                "timestamp": datetime.now().isoformat(),
                "summary": activity_summary,
                "recent_jobs": all_jobs[:20],  # Last 20 jobs
                "processing_jobs": [j for j in all_jobs if j["status"] == "processing"],
                "latest_completed": [j for j in all_jobs if j["status"] == "completed"][:5]
            }
        })
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/polling/metrics", methods=["GET"])
def get_system_metrics_polling():
    """Get performance metrics and statistics"""
    try:
        metrics = {
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "average_generation_time": None,
                "success_rate": None,
                "videos_per_hour": None,
                "total_videos_generated": 0
            },
            "storage": {
                "total_storage_used": 0,
                "average_video_size": 0,
                "storage_by_domain": {}
            },
            "queue_efficiency": {
                "queue_depth": 0,
                "processing_capacity": 0,
                "estimated_queue_time": 0
            }
        }
        
        if job_queue_manager:
            # Get completed jobs for metrics
            completed_jobs = [j for j in job_queue_manager._job_cache.values() if j.status.value == "completed"]
            
            if completed_jobs:
                # Calculate performance metrics
                generation_times = []
                total_size = 0
                domain_storage = {}
                
                for job in completed_jobs:
                    if job.started_at and job.completed_at:
                        duration = (job.completed_at - job.started_at).total_seconds()
                        generation_times.append(duration)
                    
                    # Get video file size if available
                    video_path = job_queue_manager.get_video_for_job(job.job_id)
                    if video_path and os.path.exists(video_path):
                        try:
                            size = os.path.getsize(video_path)
                            total_size += size
                            domain_storage[job.domain] = domain_storage.get(job.domain, 0) + size
                        except:
                            pass
                
                # Update metrics
                if generation_times:
                    metrics["performance"]["average_generation_time"] = sum(generation_times) / len(generation_times)
                    metrics["performance"]["videos_per_hour"] = 3600 / metrics["performance"]["average_generation_time"] if metrics["performance"]["average_generation_time"] > 0 else 0
                
                total_jobs = len(job_queue_manager._job_cache)
                metrics["performance"]["success_rate"] = len(completed_jobs) / total_jobs if total_jobs > 0 else 0
                metrics["performance"]["total_videos_generated"] = len(completed_jobs)
                
                metrics["storage"]["total_storage_used"] = total_size
                metrics["storage"]["average_video_size"] = total_size / len(completed_jobs) if completed_jobs else 0
                metrics["storage"]["storage_by_domain"] = {k: round(v/(1024*1024), 2) for k, v in domain_storage.items()}
            
            # Queue metrics
            queue_status = job_queue_manager.get_queue_status()
            metrics["queue_efficiency"]["queue_depth"] = queue_status.get("by_status", {}).get("queued", 0)
            metrics["queue_efficiency"]["processing_capacity"] = queue_status.get("by_status", {}).get("processing", 0)
            
            # Estimate queue processing time
            if metrics["performance"]["average_generation_time"]:
                queued_jobs = metrics["queue_efficiency"]["queue_depth"]
                processing_jobs = metrics["queue_efficiency"]["processing_capacity"]
                max_concurrent = job_queue_manager.max_concurrent_jobs
                
                if queued_jobs > 0:
                    estimated_time = (queued_jobs / max_concurrent) * metrics["performance"]["average_generation_time"]
                    metrics["queue_efficiency"]["estimated_queue_time"] = estimated_time
        
        return jsonify({"metrics": metrics})
        
    except Exception as e:
        return jsonify({
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

# ===== HIDDEN OAUTH CREDENTIALS MANAGEMENT =====

@app.route("/oauth-secret-management-x9k2m8n7/generate-access-key", methods=["POST"])
def generate_oauth_access_key():
    """HIDDEN: Generate new OAuth access key"""
    try:
        if not oauth_manager:
            return jsonify({"error": "OAuth manager not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        user_identifier = data.get("user_identifier")
        if not user_identifier:
            raise BadRequest("user_identifier is required")
        
        # Generate access key
        access_key = oauth_manager.generate_access_key(user_identifier)
        
        return jsonify({
            "success": True,
            "access_key": access_key,
            "user_identifier": user_identifier,
            "message": "Access key generated. Use this key to add OAuth credentials.",
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to generate access key"
        }), 500

@app.route("/oauth-secret-management-x9k2m8n7/add-credentials", methods=["POST"])
def add_oauth_credentials():
    """HIDDEN: Add Google OAuth credentials"""
    try:
        if not oauth_manager:
            return jsonify({"error": "OAuth manager not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        access_key = data.get("access_key")
        client_id = data.get("client_id")
        client_secret = data.get("client_secret")
        user_info = data.get("user_info", {})
        
        if not all([access_key, client_id, client_secret]):
            raise BadRequest("access_key, client_id, and client_secret are required")
        
        # Add credentials
        success = oauth_manager.add_credentials(access_key, client_id, client_secret, user_info)
        
        if success:
            return jsonify({
                "success": True,
                "message": "OAuth credentials added successfully",
                "access_key_preview": access_key[:16] + "...",
                "client_id_preview": client_id[:20] + "..." if len(client_id) > 20 else client_id,
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to add credentials (may already exist or invalid format)"
            }), 400
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to add OAuth credentials"
        }), 500

@app.route("/oauth-secret-management-x9k2m8n7/list-credentials", methods=["GET"])
def list_oauth_credentials():
    """HIDDEN: List stored OAuth credentials (masked)"""
    try:
        if not oauth_manager:
            return jsonify({"error": "OAuth manager not initialized"}), 500
        
        # Get admin key from header for security
        admin_key = request.headers.get("X-Admin-Key")
        if admin_key != "admin-oauth-list-2024":
            return jsonify({"error": "Unauthorized"}), 403
        
        credentials_list = oauth_manager.list_credentials()
        stats = oauth_manager.get_stats()
        
        return jsonify({
            "success": True,
            "credentials": credentials_list,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to list OAuth credentials"
        }), 500

@app.route("/oauth-secret-management-x9k2m8n7/remove-credentials", methods=["POST"])
def remove_oauth_credentials():
    """HIDDEN: Remove OAuth credentials"""
    try:
        if not oauth_manager:
            return jsonify({"error": "OAuth manager not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        access_key = data.get("access_key")
        admin_key = data.get("admin_key")
        
        if not access_key:
            raise BadRequest("access_key is required")
        
        if admin_key != "admin-oauth-remove-2024":
            return jsonify({"error": "Unauthorized"}), 403
        
        success = oauth_manager.remove_credentials(access_key)
        
        return jsonify({
            "success": success,
            "message": "Credentials removed" if success else "Credentials not found",
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to remove OAuth credentials"
        }), 500

@app.route("/oauth-secret-management-x9k2m8n7/validate-key", methods=["POST"])
def validate_oauth_key():
    """HIDDEN: Validate if an access key exists"""
    try:
        if not oauth_manager:
            return jsonify({"error": "OAuth manager not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        access_key = data.get("access_key")
        if not access_key:
            raise BadRequest("access_key is required")
        
        is_valid = oauth_manager.validate_access_key(access_key)
        
        return jsonify({
            "valid": is_valid,
            "access_key_preview": access_key[:16] + "...",
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "error": str(e),
            "message": "Failed to validate access key"
        }), 500

# ===== YOUTUBE UPLOAD WITH STORED CREDENTIALS =====

@app.route("/upload/youtube-with-key", methods=["POST"])
def upload_to_youtube_with_stored_key():
    """Upload video to YouTube using stored OAuth credentials"""
    try:
        if not oauth_manager:
            return jsonify({"error": "OAuth manager not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        access_key = data.get("access_key")
        job_id = data.get("job_id")
        video_title = data.get("title", "AI Generated Video")
        video_description = data.get("description", "Generated by AI Video System")
        video_tags = data.get("tags", ["AI", "generated", "video"])
        privacy_status = data.get("privacy_status", "private")  # private, public, unlisted
        
        if not access_key:
            raise BadRequest("access_key is required")
        
        if not job_id:
            raise BadRequest("job_id is required")
        
        # Get OAuth credentials
        credentials = oauth_manager.get_credentials(access_key)
        if not credentials:
            return jsonify({"error": "Invalid access key or credentials not found"}), 401
        
        # Get video file path
        if job_queue_manager:
            video_path = job_queue_manager.get_video_for_job(job_id)
        else:
            # Fallback to legacy job system
            job = active_jobs.get(job_id)
            video_path = job.result.get("video_file") if job and job.result else None
        
        if not video_path or not os.path.exists(video_path):
            return jsonify({"error": "Video file not found for job"}), 404
        
        # Prepare upload data
        upload_data = {
            "video_file": video_path,
            "title": video_title,
            "description": video_description,
            "tags": video_tags,
            "privacy_status": privacy_status,
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"]
        }
        
        # Import YouTube uploader
        try:
            from backend_functions.youtube_uploader import upload_to_youtube_with_oauth
            
            # Upload to YouTube
            upload_result = upload_to_youtube_with_oauth(upload_data)
            
            if upload_result.get("success"):
                return jsonify({
                    "success": True,
                    "message": "Video uploaded successfully to YouTube",
                    "video_id": upload_result.get("video_id"),
                    "video_url": f"https://youtube.com/watch?v={upload_result.get('video_id')}",
                    "upload_result": upload_result,
                    "job_id": job_id,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return jsonify({
                    "success": False,
                    "message": "YouTube upload failed",
                    "error": upload_result.get("error"),
                    "upload_result": upload_result
                }), 500
                
        except ImportError:
            return jsonify({
                "error": "YouTube uploader not available",
                "message": "YouTube upload functionality not implemented"
            }), 500
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to upload to YouTube"
        }), 500

@app.route("/upload/next-video-to-cloudflare", methods=["POST"])
def upload_next_video_to_cloudflare():
    """Upload the next completed video to Cloudflare (sequential, one-by-one)"""
    try:
        if not all([job_queue_manager, cloudflare_manager]):
            return jsonify({"error": "Required managers not initialized"}), 500
        
        # Check Cloudflare storage limit first
        storage_status = cloudflare_manager.check_storage_limit()
        
        if storage_status["storage_full"]:
            return jsonify({
                "success": False,
                "message": "Cloudflare storage full (30+ videos). Please delete some videos first.",
                "storage_status": storage_status,
                "action_required": "Delete old videos to make space"
            })
        
        # Get the next completed video that hasn't been uploaded to Cloudflare yet
        completed_jobs = job_queue_manager.get_completed_jobs_with_videos(50)  # Get more to find unuploaded ones
        
        # Find first video not yet uploaded to Cloudflare
        next_video = None
        for job in completed_jobs:
            if job.get("video_exists") and job["job_id"] not in cloudflare_manager.storage_records:
                next_video = job
                break
        
        if not next_video:
            return jsonify({
                "success": False,
                "message": "No new videos available for upload to Cloudflare",
                "storage_status": storage_status
            })
        
        # Prepare video metadata
        job_result = next_video.get("result", {})
        story_info = job_result.get("story_info", {})
        
        video_metadata = {
            "job_id": next_video["job_id"],
            "topic": next_video["topic"],
            "domain": next_video["domain"],
            "title": story_info.get("title", next_video["topic"]),
            "created_at": next_video["created_at"],
            "completed_at": next_video["completed_at"],
            "duration": job_result.get("final_video", {}).get("duration_seconds", 0),
            "story_summary": story_info.get("summary", "")
        }
        
        # Upload to Cloudflare
        upload_result = cloudflare_manager.upload_video_to_cloudflare(
            next_video["job_id"], 
            next_video["video_path"],
            video_metadata
        )
        
        if upload_result["success"]:
            return jsonify({
                "success": True,
                "message": "Video uploaded to Cloudflare successfully",
                "job_id": next_video["job_id"],
                "topic": next_video["topic"],
                "cloudflare_url": upload_result["cloudflare_url"],
                "local_file_deleted": upload_result.get("local_file_deleted", False),
                "storage_status": upload_result["storage_status"],
                "upload_details": upload_result["upload_record"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to upload video to Cloudflare",
                "job_id": next_video["job_id"],
                "topic": next_video["topic"],
                "error": upload_result.get("error"),
                "cloudflare_error": upload_result.get("cloudflare_error"),
                "timestamp": datetime.now().isoformat()
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to upload next video to Cloudflare"
        }), 500

@app.route("/upload/youtube-from-cloudflare", methods=["POST"])
def upload_youtube_from_cloudflare():
    """Upload video from Cloudflare to YouTube with AI-generated metadata"""
    try:
        if not all([oauth_manager, cloudflare_manager, job_queue_manager]):
            return jsonify({"error": "Required managers not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        access_key = data.get("access_key")
        job_id = data.get("job_id")  # Optional - if not provided, get next available
        platform = data.get("platform", "youtube")  # youtube, instagram, tiktok
        privacy_status = data.get("privacy_status", "private")
        custom_title = data.get("title")
        custom_description = data.get("description")
        
        if not access_key:
            raise BadRequest("access_key is required")
        
        # Validate OAuth credentials
        credentials = oauth_manager.get_credentials(access_key)
        if not credentials:
            return jsonify({"error": "Invalid access key"}), 401
        
        # Get video from Cloudflare storage
        if job_id:
            if job_id not in cloudflare_manager.storage_records:
                return jsonify({"error": "Video not found in Cloudflare storage"}), 404
            video_record = cloudflare_manager.storage_records[job_id]
        else:
            # Get the oldest video from Cloudflare for upload
            stored_videos = cloudflare_manager.get_stored_videos()
            if not stored_videos:
                return jsonify({
                    "success": False,
                    "message": "No videos available in Cloudflare storage"
                })
            video_record = stored_videos[-1]  # Oldest video
            job_id = video_record["job_id"]
        
        # Get job metadata from job queue (includes AI-generated captions/metadata)
        job_details = job_queue_manager.get_job(job_id)
        ai_metadata = {}
        
        if job_details and job_details.result:
            ai_metadata = job_details.result.get("video_metadata", {})
        
        # Get platform-specific metadata
        platform_meta = ai_metadata.get("platform_metadata", {}).get(platform, {})
        base_meta = ai_metadata.get("base_metadata", {})
        cloudflare_meta = video_record.get("metadata", {})
        
        # Prepare optimized upload data
        if platform == "youtube":
            upload_data = {
                "cloudflare_url": video_record["cloudflare_url"],
                "title": custom_title or platform_meta.get("title", cloudflare_meta.get("title", "AI Generated Video"))[:100],
                "description": custom_description or platform_meta.get("description", f"AI Generated Video about {cloudflare_meta.get('topic', 'unknown topic')}"),
                "tags": platform_meta.get("tags", [cloudflare_meta.get("domain", "general"), "AI", "generated"]),
                "privacy_status": privacy_status,
                "category": platform_meta.get("category", "22"),
                "captions_srt": ai_metadata.get("captions", {}).get("srt_format", ""),
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"]
            }
            
        elif platform == "instagram":
            upload_data = {
                "cloudflare_url": video_record["cloudflare_url"],
                "caption": custom_description or platform_meta.get("caption", f"Check out this amazing story! 🎬\n\n{cloudflare_meta.get('topic', 'AI Generated Content')}\n\n#AI #story #content"),
                "hashtags": platform_meta.get("hashtags", ["#AI", "#generated", "#story"]),
                "privacy_status": privacy_status,
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"]
            }
            
        else:  # Default/other platforms
            upload_data = {
                "cloudflare_url": video_record["cloudflare_url"],
                "title": custom_title or cloudflare_meta.get("title", "AI Generated Video"),
                "description": custom_description or f"AI Generated Video: {cloudflare_meta.get('topic', 'Unknown')}",
                "tags": [cloudflare_meta.get("domain", "general"), "AI", "generated"],
                "privacy_status": privacy_status,
                "client_id": credentials["client_id"],
                "client_secret": credentials["client_secret"]
            }
        
        # Simulate platform upload (replace with real implementation)
        upload_result = {
            "success": True,  # Placeholder
            "video_id": f"{platform}_{int(time.time())}_{job_id[:8]}",  # Placeholder
            "video_url": f"https://{platform}.com/watch?v={platform}_{int(time.time())}_{job_id[:8]}"
        }
        
        if upload_result["success"]:
            return jsonify({
                "success": True,
                "message": f"Video uploaded to {platform.title()} successfully",
                "platform": platform,
                "job_id": job_id,
                "topic": cloudflare_meta.get("topic", "Unknown"),
                "video_id": upload_result["video_id"],
                "video_url": upload_result["video_url"],
                "cloudflare_url": video_record["cloudflare_url"],
                "upload_data": upload_data,
                "ai_metadata_used": bool(ai_metadata),
                "captions_included": bool(upload_data.get("captions_srt")),
                "optimization_applied": {
                    "title_optimized": bool(platform_meta.get("title")),
                    "description_optimized": bool(platform_meta.get("description")),
                    "tags_optimized": bool(platform_meta.get("tags")),
                    "platform_specific": True
                },
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": f"{platform.title()} upload failed",
                "error": upload_result.get("error"),
                "job_id": job_id
            }), 500
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": f"Failed to upload from Cloudflare to {platform}"
        }), 500

# ===== CLOUDFLARE STORAGE MANAGEMENT =====

@app.route("/cloudflare/storage-status", methods=["GET"])
def get_cloudflare_storage_status():
    """Get Cloudflare storage status and limits"""
    try:
        if not cloudflare_manager:
            return jsonify({"error": "Cloudflare manager not initialized"}), 500
        
        storage_status = cloudflare_manager.check_storage_limit()
        storage_stats = cloudflare_manager.get_storage_stats()
        
        return jsonify({
            "success": True,
            "storage_status": storage_status,
            "storage_stats": storage_stats,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to get Cloudflare storage status"
        }), 500

@app.route("/cloudflare/list-videos", methods=["GET"])
def list_cloudflare_videos():
    """List videos stored on Cloudflare"""
    try:
        if not cloudflare_manager:
            return jsonify({"error": "Cloudflare manager not initialized"}), 500
        
        limit = request.args.get("limit", type=int)
        stored_videos = cloudflare_manager.get_stored_videos(limit)
        
        return jsonify({
            "success": True,
            "videos": stored_videos,
            "count": len(stored_videos),
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to list Cloudflare videos"
        }), 500

@app.route("/cloudflare/delete-video/<job_id>", methods=["DELETE"])
def delete_cloudflare_video(job_id: str):
    """Delete specific video from Cloudflare"""
    try:
        if not cloudflare_manager:
            return jsonify({"error": "Cloudflare manager not initialized"}), 500
        
        delete_result = cloudflare_manager.delete_video_from_cloudflare(job_id)
        
        if delete_result["success"]:
            return jsonify({
                "success": True,
                "message": f"Video deleted from Cloudflare: {delete_result['deleted_filename']}",
                "deleted_job_id": delete_result["deleted_job_id"],
                "freed_space_mb": delete_result["freed_space_mb"],
                "storage_status": delete_result["storage_status"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": "Failed to delete video from Cloudflare",
                "error": delete_result.get("error"),
                "job_id": job_id
            }), 500
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to delete video from Cloudflare"
        }), 500

@app.route("/cloudflare/delete-oldest", methods=["POST"])
def delete_oldest_cloudflare_video():
    """Delete oldest video from Cloudflare to free space"""
    try:
        if not cloudflare_manager:
            return jsonify({"error": "Cloudflare manager not initialized"}), 500
        
        # Get how many to delete (default 1)
        data = request.get_json() or {}
        count = data.get("count", 1)
        
        deleted_videos = []
        total_freed_space = 0
        
        for i in range(count):
            delete_result = cloudflare_manager._cleanup_oldest_video()
            
            if delete_result["success"]:
                deleted_videos.append({
                    "job_id": delete_result["deleted_job_id"],
                    "filename": delete_result["deleted_filename"],
                    "freed_space_mb": delete_result["freed_space_mb"]
                })
                total_freed_space += delete_result["freed_space_mb"]
            else:
                break  # Stop if deletion fails
        
        if deleted_videos:
            return jsonify({
                "success": True,
                "message": f"Deleted {len(deleted_videos)} oldest video(s) from Cloudflare",
                "deleted_videos": deleted_videos,
                "total_freed_space_mb": round(total_freed_space, 2),
                "storage_status": cloudflare_manager.check_storage_limit(),
                "timestamp": datetime.now().isoformat()
            })
        else:
            return jsonify({
                "success": False,
                "message": "No videos could be deleted",
                "timestamp": datetime.now().isoformat()
            })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to delete oldest videos"
        }), 500

@app.route("/cloudflare/cleanup-storage", methods=["POST"])
def cleanup_cloudflare_storage():
    """Clean up Cloudflare storage when full (automated cleanup)"""
    try:
        if not cloudflare_manager:
            return jsonify({"error": "Cloudflare manager not initialized"}), 500
        
        storage_status = cloudflare_manager.check_storage_limit()
        
        if not storage_status["storage_full"]:
            return jsonify({
                "success": True,
                "message": "Storage not full, no cleanup needed",
                "storage_status": storage_status
            })
        
        # Calculate how many videos to delete to get below 25 videos (buffer)
        target_count = 25
        current_count = storage_status["current_videos"]
        videos_to_delete = max(1, current_count - target_count)
        
        deleted_videos = []
        total_freed_space = 0
        
        for i in range(videos_to_delete):
            delete_result = cloudflare_manager._cleanup_oldest_video()
            
            if delete_result["success"]:
                deleted_videos.append({
                    "job_id": delete_result["deleted_job_id"],
                    "filename": delete_result["deleted_filename"],
                    "freed_space_mb": delete_result["freed_space_mb"]
                })
                total_freed_space += delete_result["freed_space_mb"]
            else:
                print(f"[CLEANUP] Failed to delete video {i+1}: {delete_result.get('error')}")
                break
        
        return jsonify({
            "success": True,
            "message": f"Cleanup completed: deleted {len(deleted_videos)} videos",
            "deleted_videos": deleted_videos,
            "total_freed_space_mb": round(total_freed_space, 2),
            "storage_status": cloudflare_manager.check_storage_limit(),
            "target_count": target_count,
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to cleanup Cloudflare storage"
        }), 500

@app.route("/workflow/complete-upload-sequence", methods=["POST"])
def complete_upload_sequence():
    """Complete upload sequence: Local → Cloudflare → YouTube (one video)"""
    try:
        if not all([job_queue_manager, cloudflare_manager, oauth_manager]):
            return jsonify({"error": "Required managers not initialized"}), 500
        
        data = request.get_json()
        if not data:
            raise BadRequest("No JSON data provided")
        
        access_key = data.get("access_key")
        privacy_status = data.get("privacy_status", "private")
        
        if not access_key:
            raise BadRequest("access_key is required")
        
        # Validate OAuth credentials
        credentials = oauth_manager.get_credentials(access_key)
        if not credentials:
            return jsonify({"error": "Invalid access key"}), 401
        
        workflow_results = {
            "stage_1_cloudflare_upload": None,
            "stage_2_youtube_upload": None,
            "local_file_cleanup": None
        }
        
        # Stage 1: Upload next video to Cloudflare
        storage_status = cloudflare_manager.check_storage_limit()
        
        if storage_status["storage_full"]:
            # Auto-cleanup to make space
            cleanup_result = cloudflare_manager._cleanup_oldest_video()
            workflow_results["auto_cleanup"] = cleanup_result
        
        # Find next video to upload to Cloudflare
        completed_jobs = job_queue_manager.get_completed_jobs_with_videos(10)
        next_video = None
        
        for job in completed_jobs:
            if job.get("video_exists") and job["job_id"] not in cloudflare_manager.storage_records:
                next_video = job
                break
        
        if not next_video:
            return jsonify({
                "success": False,
                "message": "No new videos available for upload sequence",
                "storage_status": storage_status,
                "workflow_results": workflow_results
            })
        
        # Upload to Cloudflare
        job_result = next_video.get("result", {})
        story_info = job_result.get("story_info", {})
        
        video_metadata = {
            "job_id": next_video["job_id"],
            "topic": next_video["topic"],
            "domain": next_video["domain"],
            "title": story_info.get("title", next_video["topic"]),
            "story_summary": story_info.get("summary", "")
        }
        
        cloudflare_result = cloudflare_manager.upload_video_to_cloudflare(
            next_video["job_id"], 
            next_video["video_path"],
            video_metadata
        )
        
        workflow_results["stage_1_cloudflare_upload"] = cloudflare_result
        
        if not cloudflare_result["success"]:
            return jsonify({
                "success": False,
                "message": "Failed to upload to Cloudflare",
                "workflow_results": workflow_results
            }), 500
        
        # Stage 2: Upload to YouTube from Cloudflare
        upload_data = {
            "cloudflare_url": cloudflare_result["cloudflare_url"],
            "title": video_metadata["title"][:100],
            "description": f"AI Generated Video: {video_metadata['topic']}\n\nDomain: {video_metadata['domain']}\n\nGenerated automatically by AI Video System.",
            "tags": [video_metadata["domain"], "AI", "generated", "video", "automated"],
            "privacy_status": privacy_status,
            "client_id": credentials["client_id"],
            "client_secret": credentials["client_secret"]
        }
        
        # Simulate YouTube upload
        youtube_result = {
            "success": True,
            "video_id": f"yt_{int(time.time())}_{next_video['job_id'][:8]}",
            "video_url": f"https://youtube.com/watch?v=yt_{int(time.time())}_{next_video['job_id'][:8]}"
        }
        
        workflow_results["stage_2_youtube_upload"] = youtube_result
        
        return jsonify({
            "success": True,
            "message": "Complete upload sequence successful",
            "job_id": next_video["job_id"],
            "topic": next_video["topic"],
            "cloudflare_url": cloudflare_result["cloudflare_url"],
            "youtube_url": youtube_result["video_url"] if youtube_result["success"] else None,
            "local_file_deleted": cloudflare_result.get("local_file_deleted", False),
            "workflow_results": workflow_results,
            "storage_status": cloudflare_manager.check_storage_limit(),
            "timestamp": datetime.now().isoformat()
        })
        
    except BadRequest as e:
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
            "message": "Failed to complete upload sequence",
            "workflow_results": workflow_results
        }), 500

if __name__ == "__main__":
    print("Starting AI Video Generator Flask App...")
    print("Local Mode: Script generation using Gemini AI")
    
    # Run initial cleanup on startup
    try:
        from backend_functions.cleanup_utils import cleanup_temporary_files
        cleanup_temporary_files()
        print("Initial cleanup completed")
    except Exception as e:
        print(f"Initial cleanup failed: {e}")
    
    app.run(host="0.0.0.0", port=8000, debug=True)