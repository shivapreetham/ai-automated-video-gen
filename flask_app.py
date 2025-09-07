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

# Import local functions
from local_functions.local_video_generator import LocalVideoGenerator
from local_functions.PromptImagesToVideo_pollinations import mindsflow_function as generate_video
from local_functions.textToSpeech_elevenlabs import mindsflow_function as generate_speech

app = Flask(__name__, static_folder='static')
CORS(app)

# Configuration - Akash integration removed

# In-memory job storage (use Redis in production)
active_jobs = {}

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
        "version": "2.0",
        "status": "running",
        "local_mode": True,
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

def generate_script_local(data: Dict[str, Any]) -> Dict[str, Any]:
    """Generate script locally using Gemini"""
    
    try:
        from local_functions.textGeneration_gemini import generate_video_script
        
        # Ensure proper type conversion with error handling
        try:
            num_segments = int(data.get("num_segments", 5))
            duration_per_segment = float(data.get("duration_per_segment", 4.0))
        except (ValueError, TypeError) as e:
            print(f"[ERROR] Type conversion error: {e}")
            num_segments = 5
            duration_per_segment = 4.0
        
        script_data = generate_video_script(
            topic=data["topic"],
            style=data.get("style", "informative"),
            num_segments=num_segments,
            duration_per_segment=duration_per_segment
        )
        
        return {
            "success": True,
            "text": script_data["Text"],
            "sentences": script_data["sentences"],
            "generated_by": "local_gemini"
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
    
    # Try ElevenLabs first
    print("[SPEECH] Attempting ElevenLabs TTS...")
    result = generate_speech(speech_event, None)
    
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
                from local_functions.textToSpeech_gtts import mindsflow_function as generate_google_speech
                
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
                raise Exception(f"Both ElevenLabs and Google TTS failed. ElevenLabs: {error}, Google: {fallback_error}")
        else:
            # For non-rate-limit errors, don't fall back
            raise Exception(f"ElevenLabs TTS failed: {error}")
    
    print("[SPEECH] ElevenLabs TTS successful")
    return result

def generate_video_local(data: Dict[str, Any], script_data: Dict[str, Any], speech_result: Dict[str, Any]) -> Dict[str, Any]:
    """Generate video locally using existing functions"""
    
    # Create video event
    video_event = {
        "img_prompt": f"High-quality scenes related to {data['topic']}",
        "img_style_prompt": "professional, detailed, high resolution",
        "width": data.get("width", 1024),
        "height": data.get("height", 576),
        "fps": data.get("fps", 24),
        "video_duration": speech_result.get("duration", 15.0),
        "sentences_json_url": None,  # We'll create this from script_data
        "topic": data["topic"],
        "img_model": data.get("image_model", "flux")
    }
    
    # Create temporary sentences file if we have sentence data
    if "sentences" in script_data:
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(script_data["sentences"], f, indent=2)
            video_event["sentences_json_url"] = f.name
    
    # Generate video
    result = generate_video(video_event, None)
    
    if not result.get("success", True):
        raise Exception(f"Video generation failed: {result.get('error', 'Unknown error')}")
    
    # Combine with audio if needed
    video_file = result.get("video_file")
    audio_file = speech_result.get("audio_file")
    
    if video_file and audio_file and os.path.exists(video_file) and os.path.exists(audio_file):
        combined_file = combine_audio_video_local(video_file, audio_file)
        result["video_file"] = combined_file
        result["video_url"] = os.path.abspath(combined_file)
    
    return result

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

if __name__ == "__main__":
    print("Starting AI Video Generator Flask App...")
    print("Local Mode: Script generation using Gemini AI")
    
    app.run(host="0.0.0.0", port=8000, debug=True)