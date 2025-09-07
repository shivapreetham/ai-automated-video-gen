"""
ElevenLabs Audio Generation - Independent Backend Function
With gTTS fallback when ElevenLabs fails
"""

import os
import requests
import datetime
import uuid
from typing import Dict, Tuple

# ElevenLabs configuration
ELEVENLABS_API_KEY = "sk_199c37d214698f1395b5ce8145696498acb2e1acaa777d30"
ELEVENLABS_BASE_URL = "https://api.elevenlabs.io/v1"

VOICE_MAP = {
    'nova': 'pNInz6obpgDQGcFmaJgB',     # Adam
    'alloy': 'EXAVITQu4vr4xnSDxMaL',   # Bella
    'echo': 'N2lVS1w4EtoT3dr4eOWO',    # Callum
    'fable': 'pNInz6obpgDQGcFmaJgB',   # Adam (fallback)
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

def generate_audio(text: str, voice: str = "nova", speed: float = 1.0, output_dir: str = ".") -> Dict[str, any]:
    """
    Generate audio using ElevenLabs API
    
    Returns:
    {
        "success": True,
        "audio_file": "/path/to/audio.mp3",
        "duration_seconds": 25.3,
        "file_size": 1024000,
        "voice_used": "nova"
    }
    """
    
    if not text or not text.strip():
        return {"success": False, "error": "Text cannot be empty"}
    
    # Get voice ID
    voice_id = VOICE_MAP.get(voice, VOICE_MAP['nova'])
    
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
            "xi-api-key": ELEVENLABS_API_KEY
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75,
                "speed": max(0.25, min(4.0, speed)),
                "style": 0.0,
                "use_speaker_boost": True
            }
        }
        
        print(f"[AUDIO] Generating speech with {voice} voice...")
        response = requests.post(url, json=data, headers=headers, stream=True)
        
        if response.status_code != 200:
            print(f"[AUDIO] ElevenLabs failed with status {response.status_code}, trying gTTS fallback...")
            return generate_audio_gtts_fallback(text, output_dir)
        
        # Save audio file
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Get file info
        file_size = os.path.getsize(filepath)
        
        # Estimate duration (rough calculation based on file size and speech speed)
        words = len(text.split())
        estimated_duration = (words / 150) * 60 / speed  # 150 WPM adjusted for speed
        
        print(f"[AUDIO] Generated: {filename} ({file_size/1024:.1f} KB, ~{estimated_duration:.1f}s)")
        
        return {
            "success": True,
            "audio_file": filepath,
            "duration_seconds": estimated_duration,
            "file_size": file_size,
            "voice_used": voice,
            "text_length": len(text),
            "word_count": words
        }
        
    except Exception as e:
        if os.path.exists(filepath):
            os.remove(filepath)
        print(f"[AUDIO] ElevenLabs exception: {e}, trying gTTS fallback...")
        return generate_audio_gtts_fallback(text, output_dir)

if __name__ == "__main__":
    # Test
    result = generate_audio("This is a test of the ElevenLabs audio generation system.", "nova", 1.0, ".")
    print(result)