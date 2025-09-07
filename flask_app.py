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
from integrated_daily_mash_system import IntegratedDailyMashSystem

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

if __name__ == "__main__":
    print("Starting AI Video Generator Flask App...")
    print("Local Mode: Script generation using Gemini AI")
    
    app.run(host="0.0.0.0", port=8000, debug=True)