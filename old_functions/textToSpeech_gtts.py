"""
Free Text-to-Speech using Google Text-to-Speech (gTTS)
Replacement for Azure TTS
"""

import os
import datetime
import requests
from gtts import gTTS
import tempfile
import uuid

# Configure ffmpeg for pydub
try:
    import imageio_ffmpeg as iio
    ffmpeg_path = iio.get_ffmpeg_exe()
    
    # Set environment variable for pydub to find ffmpeg
    os.environ["PATH"] = os.path.dirname(ffmpeg_path) + os.pathsep + os.environ.get("PATH", "")
    
    # Import pydub after setting path
    from pydub import AudioSegment
    from pydub.utils import which
    import pydub
    
    print(f"Configured pydub to use ffmpeg from: {ffmpeg_path}")
except Exception as e:
    print(f"Warning: Could not configure ffmpeg for pydub: {e}")
    from pydub import AudioSegment
    import pydub

def download_file(url, save_path):
    response = requests.get(url)
    with open(save_path, 'wb') as file:
        file.write(response.content)
    file_extension = url.split(".")[-1].lower()
    if file_extension == "mp3":  # Convert the MP3 file to WAV
        audio = AudioSegment.from_mp3(save_path)
        audio.export(save_path, format="wav")
        return save_path
    elif file_extension == "wav":
        return save_path
    else:
        raise Exception("Unsupported file format. Only MP3 and WAV files are supported.")

# Language mapping for gTTS
lang_dict = {
    'en': 'en',
    'ch': 'zh',
    'zh': 'zh',
    'it': 'it',
    'de': 'de',
    'fr': 'fr',
    'es': 'es',
    'hi': 'hi',
    'ja': 'ja',
    'ko': 'ko',
    'pt': 'pt',
    'ru': 'ru',
    'ar': 'ar'
}

def generate_audio(text: str, lang: str = 'en', voice_speed: float = 1.0, speaker: str = None):
    """
    Generate audio using Google Text-to-Speech (gTTS)
    
    Args:
        text: Text to convert to speech
        lang: Language code
        voice_speed: Speed multiplier (simplified implementation)
        speaker: Ignored in gTTS (doesn't support different speakers)
    """
    if lang in lang_dict.keys():
        lang = lang_dict[lang]
    print(f'Setting lang: {lang}')
    
    current_time = datetime.datetime.now()
    timestamp = current_time.strftime("%Y%m%d%H%M%S")
    filename = f'audio_{timestamp}.wav'
    temp_mp3 = f'temp_audio_{timestamp}.mp3'
    
    try:
        # Generate speech using gTTS
        tts = gTTS(text=text, lang=lang, slow=(voice_speed < 1.0))
        tts.save(temp_mp3)
        
        # Try to convert using pydub, fallback to simple rename
        try:
            audio = AudioSegment.from_mp3(temp_mp3)
            
            # Apply voice speed by changing playback rate
            if voice_speed != 1.0 and voice_speed != 1:
                # Speed up or slow down audio
                audio = audio.speedup(playback_speed=voice_speed)
            
            # Export as WAV
            audio.export(filename, format="wav")
            
            # Get the duration of the audio file
            duration = audio.duration_seconds
            
        except Exception as pydub_error:
            print(f"Pydub conversion failed: {pydub_error}")
            print("Using simple file copy approach (audio will be in MP3 format)")
            
            # Simple fallback: copy the file with a small delay
            import time
            time.sleep(0.1)  # Small delay to ensure file is released
            
            try:
                # Try copying instead of renaming
                import shutil
                shutil.copy2(temp_mp3, filename)
            except Exception as copy_error:
                print(f"Copy failed too: {copy_error}")
                # Last resort: just use the MP3 file
                filename = temp_mp3
                temp_mp3 = None  # Prevent deletion
            
            # Estimate duration based on text length (rough approximation)
            # Typical speech rate is about 150 words per minute
            words = len(text.split())
            duration = max(words / 2.5, 2.0)  # At least 2 seconds
        
        # Clean up temporary MP3 file
        if temp_mp3 and os.path.exists(temp_mp3):
            os.remove(temp_mp3)
        
        return filename, duration
    
    except Exception as e:
        print(f"Error generating audio: {e}")
        # Clean up on error
        if temp_mp3 and os.path.exists(temp_mp3):
            try:
                os.remove(temp_mp3)
            except:
                pass
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except:
                pass
        raise e

def upload_to_local_storage(filename: str) -> str:
    """
    For local development, just return the local file path
    Replace this with S3 upload if needed
    """
    return os.path.abspath(filename)

def mindsflow_function(event, context) -> dict:
    # get the text and parameters from the event
    text = event.get("text")
    lang = event.get("language", "en")
    voice_speed = event.get("voice_speed", 1.0)
    speaker = event.get("speaker", None)  # Ignored in gTTS
    
    # generate the audio file
    filename, duration = generate_audio(text, lang, voice_speed, speaker)
    
    # For local setup, return local file path
    # For production, you can implement S3 upload
    audio_url = upload_to_local_storage(filename)
    
    # define result
    result = {
        'audio_url': audio_url,
        'audio_file': filename,  # Local file reference
        'duration': duration
    }
    
    return result

# Standalone function for local testing
def generate_speech_local(text: str, lang: str = 'en', output_file: str = None):
    """
    Simple function to generate speech locally without the mindsflow wrapper
    """
    if output_file is None:
        output_file = f"speech_{uuid.uuid4().hex[:8]}.wav"
    
    filename, duration = generate_audio(text, lang)
    
    # Rename to desired output file
    if filename != output_file:
        os.rename(filename, output_file)
        filename = output_file
    
    print(f"Generated speech: {filename} (Duration: {duration:.2f}s)")
    return filename, duration

if __name__ == "__main__":
    # Test the function
    test_text = "Hello, this is a test of the Google Text-to-Speech system."
    filename, duration = generate_speech_local(test_text, "en")
    print(f"Test completed: {filename}")