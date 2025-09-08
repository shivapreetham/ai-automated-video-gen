"""
Per-Segment Audio Generation System
Generates individual audio files for each story segment with proper timing
"""

import os
import json
import uuid
import requests
import datetime
from typing import Dict, List, Any, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading

# Load environment variables
try:
    from dotenv import load_dotenv
    # Load from parent directory (where .env is located)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not required

# ElevenLabs configuration - now uses environment variable
ELEVENLABS_API_KEY = os.getenv('ELEVENLABS_API_KEY', 'sk_fallback_key')
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Updated voice mappings with tested working voices
VOICE_MAP = {
    'nova': 'pNInz6obpgDQGcFmaJgB',     # Adam - tested working
    'alloy': '21m00Tcm4TlvDq8ikWAM',    # Rachel - tested working (high quality)
    'echo': 'ErXwobaYiN019PkySvjV',     # Antoni - tested working
    'fable': 'EXAVITQu4vr4xnSDxMaL',   # Bella - tested working
    'rachel': '21m00Tcm4TlvDq8ikWAM',   # Rachel - recommended for video
    'adam': 'pNInz6obpgDQGcFmaJgB',     # Adam - male voice
    'bella': 'EXAVITQu4vr4xnSDxMaL',   # Bella - female voice
    'antoni': 'ErXwobaYiN019PkySvjV',   # Antoni - male voice
    'domi': 'AZnzlk1XvdvUeBnXmlld',    # Domi - female voice
}

def generate_segment_audios(script_data: Dict[str, Any], voice: str = "alloy", 
                          output_dir: str = ".", use_different_voices: bool = True) -> Dict[str, Any]:
    """
    Generate individual audio files for each script segment
    
    Args:
        script_data: Script data with segments
        voice: Primary voice to use
        output_dir: Directory to save audio files
        use_different_voices: Use different voices for different characters
    
    Returns:
        Dictionary with audio files and metadata for each segment
    """
    
    segments = script_data.get("segments", [])
    if not segments:
        return {"success": False, "error": "No segments found in script data"}
    
    print(f"[SEGMENT AUDIO] Generating audio for {len(segments)} segments...")
    
    # Assign voices to characters if we have dialogs
    character_voices = assign_character_voices(script_data, voice, use_different_voices)
    
    # Generate audio files concurrently
    audio_results = []
    
    # Use ThreadPoolExecutor for concurrent generation
    with ThreadPoolExecutor(max_workers=3) as executor:
        future_to_segment = {}
        
        for segment in segments:
            future = executor.submit(
                generate_single_segment_audio,
                segment,
                character_voices,
                output_dir
            )
            future_to_segment[future] = segment
        
        # Collect results as they complete
        for future in as_completed(future_to_segment):
            segment = future_to_segment[future]
            try:
                result = future.result()
                result["segment_number"] = segment["segment_number"]
                audio_results.append(result)
                print(f"[SEGMENT AUDIO] Completed segment {segment['segment_number']}")
            except Exception as e:
                print(f"[SEGMENT AUDIO] Failed segment {segment['segment_number']}: {e}")
                audio_results.append({
                    "segment_number": segment["segment_number"],
                    "success": False,
                    "error": str(e)
                })
    
    # Sort results by segment number
    audio_results.sort(key=lambda x: x["segment_number"])
    
    # Calculate totals
    successful_audios = [r for r in audio_results if r.get("success")]
    total_duration = sum(r.get("duration_seconds", 0) for r in successful_audios)
    total_size = sum(r.get("file_size", 0) for r in successful_audios)
    
    return {
        "success": len(successful_audios) > 0,
        "segments_generated": len(successful_audios),
        "segments_failed": len(audio_results) - len(successful_audios),
        "total_segments": len(segments),
        "audio_files": audio_results,
        "total_duration": total_duration,
        "total_file_size": total_size,
        "character_voices": character_voices,
        "generation_method": "elevenlabs_segments"
    }

def assign_character_voices(script_data: Dict[str, Any], primary_voice: str, 
                          use_different_voices: bool) -> Dict[str, str]:
    """Assign different voices to different characters"""
    
    character_voices = {"narrator": primary_voice}
    
    if not use_different_voices:
        return character_voices
    
    characters = script_data.get("characters", [])
    available_voices = list(VOICE_MAP.keys())
    
    # Remove primary voice from available voices for characters
    if primary_voice in available_voices:
        available_voices.remove(primary_voice)
    
    # Assign voices to characters
    for i, character in enumerate(characters):
        # Handle both string names and character objects
        if isinstance(character, dict):
            char_name = character.get("name", f"character_{i}")
        else:
            char_name = str(character)  # Character is already a string name
            
        if char_name != "narrator":
            if available_voices:
                character_voices[char_name] = available_voices[i % len(available_voices)]
            else:
                character_voices[char_name] = primary_voice
    
    print(f"[VOICE ASSIGNMENT] {character_voices}")
    return character_voices

def generate_single_segment_audio(segment: Dict[str, Any], character_voices: Dict[str, str], 
                                output_dir: str) -> Dict[str, Any]:
    """Generate audio for a single segment"""
    
    segment_number = segment.get("segment_number", 1)
    text = segment.get("text", "").strip()
    character = segment.get("character_speaking")
    
    if not text:
        return {"success": False, "error": "Empty text"}
    
    # Determine voice to use
    if character and character in character_voices:
        voice_to_use = character_voices[character]
    else:
        voice_to_use = character_voices.get("narrator", "alloy")
    
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'segment_{segment_number:02d}_{timestamp}_{uuid.uuid4().hex[:8]}.mp3'
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Get voice ID
        voice_id = VOICE_MAP.get(voice_to_use, VOICE_MAP['alloy'])
        
        # Prepare request
        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        # Adjust voice settings based on segment type
        segment_type = segment.get("segment_type", "narrative")
        emotional_tone = segment.get("emotional_tone", "neutral")
        
        # Voice settings based on emotion and type
        stability, similarity_boost, speed = get_voice_settings(segment_type, emotional_tone)
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",  # Updated to tested model
            "voice_settings": {
                "stability": 0.75,  # Use tested optimal settings
                "similarity_boost": 0.85,  # Use tested optimal settings
                "style": 0.4 if segment_type == "dialog" else 0.3,  # Improved style
                "use_speaker_boost": True
            }
        }
        
        # Check API key before making request
        if not ELEVENLABS_API_KEY or ELEVENLABS_API_KEY == 'sk_fallback_key':
            print(f"[SEGMENT {segment_number}] WARNING: ElevenLabs API key not configured, using gTTS fallback")
            return generate_segment_audio_gtts_fallback(text, filepath, segment_number)
        
        print(f"[SEGMENT {segment_number}] Generating with {voice_to_use} voice using ElevenLabs...")
        print(f"[SEGMENT {segment_number}] API Key: {ELEVENLABS_API_KEY[:12]}...{ELEVENLABS_API_KEY[-4:]}")
        
        response = requests.post(url, json=data, headers=headers, stream=True, timeout=60)
        
        if response.status_code != 200:
            print(f"[SEGMENT {segment_number}] ElevenLabs failed with status {response.status_code}: {response.text[:100]}")
            # Fallback to gTTS
            return generate_segment_audio_gtts_fallback(text, filepath, segment_number)
        
        # Save audio file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Get file info and actual duration
        file_size = os.path.getsize(filepath)
        actual_duration = get_actual_audio_duration(filepath)
        
        print(f"[SEGMENT {segment_number}] Generated: {filename} ({file_size/1024:.1f} KB, {actual_duration:.1f}s)")
        
        return {
            "success": True,
            "audio_file": filepath,
            "filename": filename,
            "duration_seconds": actual_duration,
            "file_size": file_size,
            "voice_used": voice_to_use,
            "character": character,
            "segment_type": segment_type,
            "emotional_tone": emotional_tone,
            "text_length": len(text),
            "word_count": len(text.split())
        }
        
    except Exception as e:
        print(f"[SEGMENT {segment_number}] ElevenLabs failed: {e}")
        return generate_segment_audio_gtts_fallback(text, filepath, segment_number)

def get_voice_settings(segment_type: str, emotional_tone: str) -> Tuple[float, float, float]:
    """Get voice settings based on segment type and emotional tone"""
    
    # Base settings
    stability = 0.5
    similarity_boost = 0.75
    speed = 1.0
    
    # Adjust for segment type
    if segment_type == "dialog":
        stability = 0.4  # More expressive
        similarity_boost = 0.8
        speed = 1.1  # Slightly faster for dialog
    elif segment_type == "narrative":
        stability = 0.6  # More stable for narration
        similarity_boost = 0.7
        speed = 0.9  # Slightly slower for narration
    
    # Adjust for emotional tone
    if emotional_tone in ["happy", "excited"]:
        stability = max(0.3, stability - 0.1)
        speed = min(1.3, speed + 0.1)
    elif emotional_tone in ["sad", "melancholy"]:
        stability = min(0.7, stability + 0.1)
        speed = max(0.7, speed - 0.1)
    elif emotional_tone in ["suspenseful", "dramatic"]:
        stability = max(0.3, stability - 0.2)
        similarity_boost = min(0.9, similarity_boost + 0.1)
    
    return stability, similarity_boost, speed

def generate_segment_audio_gtts_fallback(text: str, filepath: str, segment_number: int) -> Dict[str, Any]:
    """Fallback audio generation using gTTS for a single segment"""
    
    try:
        from gtts import gTTS
        
        print(f"[SEGMENT {segment_number}] Using gTTS fallback...")
        
        # Generate TTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        actual_duration = get_actual_audio_duration(filepath)
        
        return {
            "success": True,
            "audio_file": filepath,
            "filename": os.path.basename(filepath),
            "duration_seconds": actual_duration,
            "file_size": file_size,
            "voice_used": "gtts_fallback",
            "character": None,
            "segment_type": "narrative",
            "emotional_tone": "neutral",
            "text_length": len(text),
            "word_count": len(text.split())
        }
        
    except ImportError:
        return {"success": False, "error": "gTTS not available"}
    except Exception as e:
        return {"success": False, "error": f"gTTS failed: {e}"}

def get_actual_audio_duration(audio_file: str) -> float:
    """Get actual audio duration using FFprobe"""
    
    try:
        import subprocess
        cmd = [
            'ffprobe', '-v', 'quiet',
            '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1',
            audio_file
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return float(result.stdout.strip())
    except:
        pass
    
    # Fallback: estimate based on file size
    try:
        file_size = os.path.getsize(audio_file)
        estimated_duration = file_size / 16000  # Rough estimation for MP3
        return estimated_duration
    except:
        return 5.0  # Default fallback

if __name__ == "__main__":
    # Test with sample script data
    sample_script = {
        "segments": [
            {
                "segment_number": 1,
                "text": "Once upon a time, in a small village, there lived a curious cat named Whiskers.",
                "character_speaking": None,
                "segment_type": "narrative",
                "emotional_tone": "neutral"
            },
            {
                "segment_number": 2,
                "text": "Hello there! I'm looking for adventure today.",
                "character_speaking": "Whiskers",
                "segment_type": "dialog",
                "emotional_tone": "excited"
            }
        ],
        "characters": [
            {"name": "Whiskers", "description": "Curious cat", "role": "protagonist"}
        ]
    }
    
    result = generate_segment_audios(sample_script, "alloy", ".", True)
    print(json.dumps(result, indent=2))