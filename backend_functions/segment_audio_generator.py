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

# ElevenLabs configuration with multiple API key fallbacks
ELEVENLABS_API_KEYS = [
    os.getenv('ELEVENLABS_API_KEY'),
    os.getenv('ELEVENLABS_API_KEY_2'), 
    os.getenv('ELEVENLABS_API_KEY_3')
]

# Remove None values and invalid keys
ELEVENLABS_API_KEYS = [key for key in ELEVENLABS_API_KEYS if key and key != 'sk_fallback_key']
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

# Voice characteristics mapped to Gemini's voice_tone options
# Dynamic mapping based on character's gender and tone from Gemini
VOICE_TONE_MAPPING = {
    'authoritative': ['adam', 'antoni'],      # Deep, commanding voices
    'gentle': ['rachel', 'bella'],           # Soft, kind voices  
    'youthful': ['bella', 'domi'],          # Young-sounding voices
    'wise': ['antoni', 'rachel'],            # Mature, experienced voices
    'strong': ['adam', 'nova'],             # Powerful, confident voices
    'warm': ['rachel', 'domi'],             # Caring, friendly voices
    'deep': ['adam', 'antoni'],             # Serious, dramatic voices
    'soft': ['bella', 'rachel'],            # Delicate, vulnerable voices
}

# Voice characteristics for reference
VOICE_CHARACTERISTICS = {
    'rachel': {'gender': 'female', 'tone': 'warm', 'quality': 'premium'},
    'adam': {'gender': 'male', 'tone': 'authoritative', 'quality': 'good'},
    'bella': {'gender': 'female', 'tone': 'clear', 'quality': 'good'},
    'antoni': {'gender': 'male', 'tone': 'professional', 'quality': 'good'},
    'domi': {'gender': 'female', 'tone': 'expressive', 'quality': 'good'},
    'nova': {'gender': 'male', 'tone': 'friendly', 'quality': 'good'},
}

def get_voice_for_character(character_data: Dict[str, Any], used_voices: List[str] = None) -> str:
    """
    Dynamically assign voice based on Gemini's character gender and tone data
    
    Args:
        character_data: Character object with gender and voice_tone from Gemini
        used_voices: List of already assigned voices to avoid duplicates
        
    Returns:
        Voice name that best matches the character's tone and gender
    """
    if used_voices is None:
        used_voices = []
    
    voice_tone = character_data.get('voice_tone', 'warm')
    character_gender = character_data.get('gender', 'neutral')
    
    # Get potential voices for this tone
    potential_voices = VOICE_TONE_MAPPING.get(voice_tone, ['rachel', 'adam'])
    
    # Try to find an unused voice first
    for voice in potential_voices:
        if voice not in used_voices:
            return voice
    
    # If all preferred voices are used, still return the best match
    return potential_voices[0] if potential_voices else 'rachel'

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
    """
    Assign voices to characters based on Gemini's gender and voice_tone data
    
    Priority order:
    1. Dynamic assignment based on Gemini's voice_tone and gender
    2. Character-specific preferred_voice in script data
    3. Fallback to available voices
    """
    
    character_voices = {"narrator": primary_voice}
    
    if not use_different_voices:
        return character_voices
    
    characters = script_data.get("characters", [])
    used_voices = [primary_voice]  # Track used voices to avoid duplicates
    
    # Assign voices to characters
    for i, character in enumerate(characters):
        # Handle both string names and character objects
        if isinstance(character, dict):
            char_name = character.get("name", f"character_{i}")
        else:
            char_name = str(character)  # Character is already a string name
            character = {"name": char_name}  # Convert to dict for processing
            
        if char_name != "narrator":
            assigned_voice = None
            
            # Priority 1: Dynamic assignment based on Gemini's character data
            if isinstance(character, dict) and character.get("voice_tone"):
                assigned_voice = get_voice_for_character(character, used_voices)
                character_voices[char_name] = assigned_voice
                used_voices.append(assigned_voice)
                
                voice_tone = character.get("voice_tone", "")
                char_gender = character.get("gender", "")
                print(f"[DYNAMIC VOICE] {char_name} ({char_gender}, {voice_tone}) -> {assigned_voice}")
            
            # Priority 2: Check if character has voice preference in script data  
            elif isinstance(character, dict) and character.get("preferred_voice"):
                preferred = character.get("preferred_voice")
                if preferred in VOICE_MAP:
                    character_voices[char_name] = preferred
                    used_voices.append(preferred)
                    print(f"[CUSTOM VOICE] {char_name} -> {preferred} (script preference)")
                else:
                    # Fallback 
                    fallback_voice = get_voice_for_character({"voice_tone": "warm"}, used_voices)
                    character_voices[char_name] = fallback_voice
                    used_voices.append(fallback_voice)
                    print(f"[FALLBACK VOICE] {char_name} -> {fallback_voice} (invalid preference)")
            
            # Priority 3: Fallback assignment
            else:
                fallback_voice = get_voice_for_character({"voice_tone": "warm"}, used_voices)
                character_voices[char_name] = fallback_voice
                used_voices.append(fallback_voice)
                print(f"[DEFAULT VOICE] {char_name} -> {fallback_voice} (no tone data)")
    
    print(f"[VOICE ASSIGNMENT COMPLETE] {character_voices}")
    return character_voices

def generate_single_segment_audio(segment: Dict[str, Any], character_voices: Dict[str, str], 
                                output_dir: str) -> Dict[str, Any]:
    """Generate audio for a single segment using the improved ElevenLabs module with API key fallback"""
    
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
    
    print(f"[SEGMENT {segment_number}] Generating with {voice_to_use} voice...")
    
    # Use the improved elevenlabs_audio module with API key fallback
    import sys
    import os
    current_dir = os.path.dirname(__file__)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    
    from elevenlabs_audio import generate_audio
    
    result = generate_audio(text, voice_to_use, 1.0, output_dir)
    
    if result.get("success"):
        # Get actual audio duration if possible
        filepath = result["audio_file"]
        actual_duration = get_actual_audio_duration(filepath)
        
        print(f"[SEGMENT {segment_number}] SUCCESS: {os.path.basename(filepath)} ({result['file_size']/1024:.1f} KB, {actual_duration:.1f}s)")
        print(f"[SEGMENT {segment_number}] API key used: {result.get('api_key_used', 'Unknown')}")
        
        # Add segment-specific metadata
        result.update({
            "filename": os.path.basename(filepath),
            "duration_seconds": actual_duration,
            "character": character,
            "segment_type": segment.get("segment_type", "narrative"),
            "emotional_tone": segment.get("emotional_tone", "neutral"),
        })
        
        return result
    else:
        print(f"[SEGMENT {segment_number}] FAILED: {result.get('error', 'Unknown error')}")
        return result

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