"""
ElevenLabs Audio Generation - Independent Backend Function
With gTTS fallback when ElevenLabs fails
"""

import os
import requests
import datetime
import uuid
from typing import Dict, Tuple

# Load environment variables
try:
    from dotenv import load_dotenv
    # Load from parent directory (where .env is located)
    env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
    load_dotenv(env_path)
except ImportError:
    pass  # dotenv not required

# ElevenLabs configuration with multiple API key fallbacks
ELEVENLABS_API_KEYS = [
    os.getenv('ELEVENLABS_API_KEY'),
    os.getenv('ELEVENLABS_API_KEY_2'),
    os.getenv('ELEVENLABS_API_KEY_3')
]

# Remove None values and invalid keys
ELEVENLABS_API_KEYS = [key for key in ELEVENLABS_API_KEYS if key and key != 'sk_fallback_key']

ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"
print(f"[AUDIO] Loaded {len(ELEVENLABS_API_KEYS)} ElevenLabs API keys for fallback system")

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

def generate_audio_gtts_fallback(text: str, output_dir: str = ".") -> Dict[str, any]:
    """
    Fallback audio generation using gTTS when ElevenLabs fails
    """
    try:
        from gtts import gTTS
        import io
        
        print("[AUDIO] ElevenLabs failed, using gTTS fallback...")
        
        # Generate filename
        timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f'audio_gtts_{timestamp}_{uuid.uuid4().hex[:8]}.mp3'
        filepath = os.path.join(output_dir, filename)
        
        # Generate TTS
        tts = gTTS(text=text, lang='en', slow=False)
        tts.save(filepath)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        # Estimate duration
        words = len(text.split())
        estimated_duration = (words / 150) * 60  # 150 WPM
        
        print(f"[AUDIO] gTTS Generated: {filename} ({file_size/1024:.1f} KB, ~{estimated_duration:.1f}s)")
        
        return {
            "success": True,
            "audio_file": filepath,
            "duration_seconds": estimated_duration,
            "file_size": file_size,
            "voice_used": "gtts_fallback",
            "text_length": len(text),
            "word_count": words
        }
        
    except ImportError:
        return {"success": False, "error": "gTTS not available (pip install gtts)"}
    except Exception as e:
        return {"success": False, "error": f"gTTS fallback failed: {e}"}

def try_elevenlabs_with_api_key(text: str, voice_id: str, api_key: str, output_dir: str, voice: str, speed: float = 1.0) -> Dict[str, any]:
    """
    Try generating audio with a specific API key
    """
    # Generate filename
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    filename = f'audio_{timestamp}_{uuid.uuid4().hex[:8]}.mp3'
    filepath = os.path.join(output_dir, filename)
    
    try:
        # Prepare request
        url = f"{ELEVENLABS_BASE_URL}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": api_key
        }
        
        data = {
            "text": text,
            "model_id": "eleven_multilingual_v2",
            "voice_settings": {
                "stability": 0.75,
                "similarity_boost": 0.85,
                "style": 0.4,
                "use_speaker_boost": True
            }
        }
        
        print(f"[AUDIO] Trying API key: {api_key[:12]}...{api_key[-4:]}")
        response = requests.post(url, json=data, headers=headers, stream=True, timeout=30)
        
        if response.status_code == 200:
            # Save audio file
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            # Get file info
            file_size = os.path.getsize(filepath)
            
            # Estimate duration
            words = len(text.split())
            estimated_duration = (words / 150) * 60 / speed
            
            print(f"[AUDIO] SUCCESS with API key {api_key[:12]}...{api_key[-4:]}: {filename} ({file_size/1024:.1f} KB, ~{estimated_duration:.1f}s)")
            
            return {
                "success": True,
                "audio_file": filepath,
                "duration_seconds": estimated_duration,
                "file_size": file_size,
                "voice_used": voice,
                "text_length": len(text),
                "word_count": words,
                "api_key_used": f"{api_key[:12]}...{api_key[-4:]}"
            }
        else:
            print(f"[AUDIO] API key {api_key[:12]}...{api_key[-4:]} failed with status {response.status_code}: {response.text}")
            if os.path.exists(filepath):
                os.remove(filepath)
            return {"success": False, "error": f"HTTP {response.status_code}: {response.text}"}
            
    except Exception as e:
        print(f"[AUDIO] API key {api_key[:12]}...{api_key[-4:]} exception: {e}")
        if os.path.exists(filepath):
            os.remove(filepath)
        return {"success": False, "error": str(e)}

def generate_audio(text: str, voice: str = "nova", speed: float = 1.0, output_dir: str = ".") -> Dict[str, any]:
    """
    Generate audio using ElevenLabs API with multiple API key fallbacks
    
    Returns:
    {
        "success": True,
        "audio_file": "/path/to/audio.mp3",
        "duration_seconds": 25.3,
        "file_size": 1024000,
        "voice_used": "nova",
        "api_key_used": "sk_xxx...xxxx"
    }
    """
    
    if not text or not text.strip():
        return {"success": False, "error": "Text cannot be empty"}
    
    # Get voice ID
    voice_id = VOICE_MAP.get(voice, VOICE_MAP['alloy'])  # Default to Rachel (high quality)
    
    # Check if we have any API keys
    if not ELEVENLABS_API_KEYS:
        print("[AUDIO] WARNING: No ElevenLabs API keys configured, using gTTS fallback")
        return generate_audio_gtts_fallback(text, output_dir)
    
    print(f"[AUDIO] Attempting ElevenLabs with {len(ELEVENLABS_API_KEYS)} API key fallbacks for {voice} voice...")
    
    # Try each API key in sequence
    for i, api_key in enumerate(ELEVENLABS_API_KEYS):
        print(f"[AUDIO] Trying API key {i+1}/{len(ELEVENLABS_API_KEYS)}")
        
        result = try_elevenlabs_with_api_key(text, voice_id, api_key, output_dir, voice, speed)
        
        if result.get("success"):
            print(f"[AUDIO] SUCCESS: ElevenLabs working with API key {i+1}")
            return result
        else:
            print(f"[AUDIO] API key {i+1} failed: {result.get('error', 'Unknown error')}")
            
            # Common error handling for rate limits and quotas
            error_message = result.get('error', '').lower()
            if 'quota' in error_message or 'limit' in error_message or 'usage' in error_message:
                print(f"[AUDIO] API key {i+1} appears to have reached quota/limit, trying next key...")
                continue
            elif '401' in str(result.get('error', '')):
                print(f"[AUDIO] API key {i+1} appears invalid (401), trying next key...")
                continue
            elif i < len(ELEVENLABS_API_KEYS) - 1:
                print(f"[AUDIO] API key {i+1} failed, trying next key...")
                continue
    
    # All API keys failed, fallback to gTTS
    print(f"[AUDIO] All {len(ELEVENLABS_API_KEYS)} ElevenLabs API keys failed, using gTTS fallback...")
    return generate_audio_gtts_fallback(text, output_dir)

if __name__ == "__main__":
    # Test
    result = generate_audio("This is a test of the ElevenLabs audio generation system.", "nova", 1.0, ".")
    print(result)