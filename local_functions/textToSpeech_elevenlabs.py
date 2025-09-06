"""
High-quality Text-to-Speech using ElevenLabs API
Replacement for Google TTS with better quality and performance
"""

import os
import datetime
import requests
import tempfile
import uuid
import time
from typing import Dict, Any, Optional

# ElevenLabs configuration
ELEVENLABS_API_KEY = "sk_8d237fdd4440012cba813bef44f660f27f4f633ddd0782b7"
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

# Available voices (you can get more via API)
VOICE_MAP = {
    'en': 'pNInz6obpgDQGcFmaJgB',  # Adam (default English)
    'en-female': 'EXAVITQu4vr4xnSDxMaL',  # Bella
    'en-male': 'pNInz6obpgDQGcFmaJgB',   # Adam
    'en-british': 'N2lVS1w4EtoT3dr4eOWO',  # Callum
    'default': 'pNInz6obpgDQGcFmaJgB'     # Adam
}

class ElevenLabsError(Exception):
    """Custom exception for ElevenLabs API errors"""
    pass

def get_available_voices() -> Dict[str, Any]:
    """Get available voices from ElevenLabs API"""
    try:
        headers = {
            "Accept": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        response = requests.get(f"{ELEVENLABS_BASE_URL}/voices", headers=headers)
        response.raise_for_status()
        
        voices_data = response.json()
        return voices_data.get('voices', [])
        
    except Exception as e:
        print(f"[WARNING] Could not fetch voices: {e}")
        return []

def select_voice(lang: str = 'en', speaker: str = None) -> str:
    """Select appropriate voice ID based on language and speaker preference"""
    
    if speaker and speaker in VOICE_MAP:
        return VOICE_MAP[speaker]
    
    # Language-based selection
    lang_lower = lang.lower()
    if lang_lower in VOICE_MAP:
        return VOICE_MAP[lang_lower]
    
    # Default fallback
    return VOICE_MAP['default']

def generate_audio(text: str, lang: str = 'en', voice_speed: float = 1.0, speaker: str = None) -> tuple:
    """
    Generate audio using ElevenLabs Text-to-Speech API
    
    Args:
        text: Text to convert to speech
        lang: Language code (used for voice selection)
        voice_speed: Speech speed multiplier (0.25 to 4.0)
        speaker: Specific speaker/voice preference
        
    Returns:
        tuple: (filename, duration)
    """
    
    if not text or not text.strip():
        raise ElevenLabsError("Text cannot be empty")
    
    # Generate unique filename
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S")
    filename = f'elevenlabs_audio_{timestamp}.mp3'
    
    try:
        # Select voice
        voice_id = select_voice(lang, speaker)
        print(f"[ELEVENLABS] Using voice: {voice_id} for language: {lang}")
        
        # Prepare request
        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        # Voice settings for quality and speed
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",  # Fast, good quality
            "voice_settings": {
                "stability": 0.5,          # Voice consistency
                "similarity_boost": 0.75,  # Voice similarity
                "speed": max(0.25, min(4.0, voice_speed)),  # Speed control
                "style": 0.0,              # Style exaggeration
                "use_speaker_boost": True   # Enhanced clarity
            }
        }
        
        print(f"[ELEVENLABS] Generating speech... (Speed: {data['voice_settings']['speed']}x)")
        start_time = time.time()
        
        # Make API request
        response = requests.post(url, json=data, headers=headers, stream=True)
        
        # Handle API errors
        if response.status_code == 401:
            raise ElevenLabsError("Invalid API key")
        elif response.status_code == 402:
            raise ElevenLabsError("Insufficient credits")
        elif response.status_code == 429:
            raise ElevenLabsError("Rate limit exceeded")
        elif response.status_code != 200:
            error_text = response.text
            raise ElevenLabsError(f"API error {response.status_code}: {error_text}")
        
        # Save audio file
        with open(filename, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        generation_time = time.time() - start_time
        
        # Verify file was created and has content
        if not os.path.exists(filename):
            raise ElevenLabsError("Audio file was not created")
        
        file_size = os.path.getsize(filename)
        if file_size < 1024:  # Less than 1KB suggests error
            raise ElevenLabsError(f"Audio file too small ({file_size} bytes)")
        
        # Estimate duration (rough calculation)
        # ElevenLabs typically generates ~1KB per 0.1 seconds of audio
        estimated_duration = file_size / 10000  # Rough estimate
        
        # Better duration estimation based on text
        words = len(text.split())
        word_based_duration = (words / 150) * 60 / voice_speed  # 150 WPM adjusted for speed
        
        # Use the more conservative estimate
        duration = max(estimated_duration, word_based_duration, 1.0)
        
        print(f"[OK] ElevenLabs audio generated in {generation_time:.1f}s")
        print(f"[OK] File: {filename} ({file_size/1024:.1f} KB, ~{duration:.1f}s)")
        
        return filename, duration
        
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Network error: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        raise ElevenLabsError(f"Network error: {e}")
        
    except ElevenLabsError:
        if os.path.exists(filename):
            os.remove(filename)
        raise
        
    except Exception as e:
        print(f"[ERROR] Unexpected error: {e}")
        if os.path.exists(filename):
            os.remove(filename)
        raise ElevenLabsError(f"Unexpected error: {e}")

def convert_to_wav(mp3_file: str) -> str:
    """Convert MP3 to WAV if needed"""
    try:
        # Try using pydub for conversion
        from pydub import AudioSegment
        
        audio = AudioSegment.from_mp3(mp3_file)
        wav_file = mp3_file.replace('.mp3', '.wav')
        audio.export(wav_file, format="wav")
        
        # Remove original MP3
        os.remove(mp3_file)
        
        print(f"[OK] Converted to WAV: {wav_file}")
        return wav_file
        
    except ImportError:
        print("[WARNING] pydub not available, keeping MP3 format")
        return mp3_file
    except Exception as e:
        print(f"[WARNING] Conversion failed: {e}, keeping MP3 format")
        return mp3_file

def upload_to_local_storage(filename: str) -> str:
    """For local development, return absolute file path"""
    return os.path.abspath(filename)

def mindsflow_function(event, context) -> dict:
    """
    Mindsflow-compatible wrapper function
    """
    try:
        # Extract parameters
        text = event.get("text")
        lang = event.get("language", "en")
        voice_speed = event.get("voice_speed", 1.0)
        speaker = event.get("speaker", None)
        output_format = event.get("format", "mp3")  # mp3 or wav
        
        if not text:
            return {
                'success': False,
                'error': 'Text parameter is required'
            }
        
        # Generate audio
        filename, duration = generate_audio(text, lang, voice_speed, speaker)
        
        # Convert to WAV if requested
        if output_format.lower() == 'wav':
            filename = convert_to_wav(filename)
        
        # Get file URL/path
        audio_url = upload_to_local_storage(filename)
        
        # Return result
        result = {
            'success': True,
            'audio_url': audio_url,
            'audio_file': filename,
            'duration': duration,
            'voice_provider': 'elevenlabs',
            'format': output_format,
            'file_size_mb': os.path.getsize(filename) / 1024 / 1024
        }
        
        return result
        
    except ElevenLabsError as e:
        return {
            'success': False,
            'error': str(e),
            'error_type': 'ElevenLabsError'
        }
    except Exception as e:
        return {
            'success': False,
            'error': f'Unexpected error: {e}',
            'error_type': type(e).__name__
        }

def generate_speech_local(text: str, lang: str = 'en', output_file: str = None, voice_speed: float = 1.0) -> tuple:
    """
    Simple function for local testing
    """
    if output_file is None:
        output_file = f"elevenlabs_speech_{uuid.uuid4().hex[:8]}.mp3"
    
    filename, duration = generate_audio(text, lang, voice_speed)
    
    # Rename to desired output file
    if filename != output_file:
        os.rename(filename, output_file)
        filename = output_file
    
    print(f"Generated ElevenLabs speech: {filename} (Duration: {duration:.2f}s)")
    return filename, duration

def test_api_connection() -> bool:
    """Test ElevenLabs API connection"""
    try:
        voices = get_available_voices()
        if voices:
            print(f"[OK] ElevenLabs API connected. Available voices: {len(voices)}")
            return True
        else:
            print("[WARNING] ElevenLabs API connected but no voices available")
            return False
    except Exception as e:
        print(f"[ERROR] ElevenLabs API connection failed: {e}")
        return False

if __name__ == "__main__":
    # Test the function
    print("Testing ElevenLabs integration...")
    
    # Test API connection
    if test_api_connection():
        # Test speech generation
        test_text = "Hello, this is a test of the ElevenLabs Text-to-Speech system. The quality should be significantly better than Google TTS."
        try:
            filename, duration = generate_speech_local(test_text, "en")
            print(f"Test completed successfully: {filename}")
        except Exception as e:
            print(f"Test failed: {e}")
    else:
        print("API connection test failed. Please check your API key.")