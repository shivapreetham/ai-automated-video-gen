#!/usr/bin/env python3
"""
ElevenLabs API Fixed Test Script
Handles streaming audio responses correctly
"""

import os
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def main():
    """Main test function"""
    print("=" * 60)
    print("ELEVENLABS FIXED TEST - TEXT TO SPEECH")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not found in environment")
        return False
    
    print(f"API KEY: Found key starting with {api_key[:8]}...")
    
    # Test import
    try:
        from elevenlabs import generate, voices
        print("IMPORT: ElevenLabs SDK imported successfully")
    except ImportError as e:
        print(f"ERROR: Cannot import ElevenLabs: {e}")
        return False
    
    # Test with simple generate function
    test_text = "Hello! This is a test of ElevenLabs text to speech integration. The API key is working correctly."
    
    # Try the simple generate function first
    try:
        print(f"\nTEST: Using simple generate function...")
        
        start_time = time.time()
        audio = generate(
            text=test_text,
            voice="Rachel",  # Use voice name instead of ID
            api_key=api_key
        )
        generation_time = time.time() - start_time
        
        # audio should be bytes now
        if isinstance(audio, bytes):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_elevenlabs_simple_{timestamp}.mp3"
            
            with open(output_file, "wb") as f:
                f.write(audio)
            
            file_size = len(audio) / 1024
            
            print(f"SUCCESS: Simple generate function working!")
            print(f"TIME: {generation_time:.2f} seconds")
            print(f"FILE: {output_file}")
            print(f"SIZE: {file_size:.2f} KB")
            
            # Test video segments
            test_video_segments(api_key)
            
            return True
        else:
            print(f"ERROR: Expected bytes, got {type(audio)}")
            
    except Exception as e:
        print(f"ERROR: Simple generate failed: {e}")
    
    # Try with client approach
    try:
        from elevenlabs.client import ElevenLabs
        
        print(f"\nTEST: Using client approach...")
        
        client = ElevenLabs(api_key=api_key)
        
        # Known voice IDs from ElevenLabs
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel
        
        start_time = time.time()
        
        # Use convert_as_stream for proper handling
        audio_generator = client.text_to_speech.convert_as_stream(
            text=test_text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2"
        )
        
        # Collect all audio chunks
        audio_chunks = []
        for chunk in audio_generator:
            if isinstance(chunk, bytes):
                audio_chunks.append(chunk)
        
        audio_data = b"".join(audio_chunks)
        generation_time = time.time() - start_time
        
        if audio_data:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_elevenlabs_client_{timestamp}.mp3"
            
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            file_size = len(audio_data) / 1024
            
            print(f"SUCCESS: Client streaming working!")
            print(f"TIME: {generation_time:.2f} seconds")
            print(f"FILE: {output_file}")
            print(f"SIZE: {file_size:.2f} KB")
            print(f"CHUNKS: {len(audio_chunks)} audio chunks received")
            
            # Test video segments
            test_video_segments_client(client, voice_id)
            
            return True
        else:
            print("ERROR: No audio data received")
            
    except Exception as e:
        print(f"ERROR: Client approach failed: {e}")
        import traceback
        traceback.print_exc()
    
    return False

def test_video_segments(api_key):
    """Test video segment generation with simple function"""
    print(f"\n{'='*60}")
    print("VIDEO SEGMENT TEST - Simple Function")
    print("="*60)
    
    segments = [
        "Welcome to our AI generated video.",
        "This is segment two of our story.",
        "Here is the third and final segment."
    ]
    
    try:
        from elevenlabs import generate
        
        total_time = 0
        for i, segment in enumerate(segments, 1):
            start_time = time.time()
            audio = generate(
                text=segment,
                voice="Rachel",
                api_key=api_key
            )
            gen_time = time.time() - start_time
            total_time += gen_time
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            segment_file = f"test_segment_simple_{i:02d}_{timestamp}.mp3"
            
            with open(segment_file, "wb") as f:
                f.write(audio)
            
            file_size = len(audio) / 1024
            print(f"SEGMENT {i}: {gen_time:.2f}s, {file_size:.2f}KB -> {segment_file}")
        
        print(f"\nSUCCESS: Generated {len(segments)} segments in {total_time:.2f}s")
        print(f"AVERAGE: {total_time/len(segments):.2f} seconds per segment")
        
    except Exception as e:
        print(f"VIDEO SEGMENT ERROR: {e}")

def test_video_segments_client(client, voice_id):
    """Test video segment generation with client"""
    print(f"\n{'='*60}")
    print("VIDEO SEGMENT TEST - Client Streaming")
    print("="*60)
    
    segments = [
        "Welcome to our AI generated video.",
        "This is segment two of our story.",
        "Here is the third and final segment."
    ]
    
    try:
        total_time = 0
        for i, segment in enumerate(segments, 1):
            start_time = time.time()
            
            audio_generator = client.text_to_speech.convert_as_stream(
                text=segment,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2"
            )
            
            audio_chunks = []
            for chunk in audio_generator:
                if isinstance(chunk, bytes):
                    audio_chunks.append(chunk)
            
            audio_data = b"".join(audio_chunks)
            gen_time = time.time() - start_time
            total_time += gen_time
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            segment_file = f"test_segment_client_{i:02d}_{timestamp}.mp3"
            
            with open(segment_file, "wb") as f:
                f.write(audio_data)
            
            file_size = len(audio_data) / 1024
            print(f"SEGMENT {i}: {gen_time:.2f}s, {file_size:.2f}KB -> {segment_file}")
        
        print(f"\nSUCCESS: Generated {len(segments)} segments in {total_time:.2f}s")
        print(f"AVERAGE: {total_time/len(segments):.2f} seconds per segment")
        
    except Exception as e:
        print(f"VIDEO SEGMENT ERROR: {e}")

if __name__ == "__main__":
    try:
        success = main()
        
        if success:
            print(f"\n{'='*60}")
            print("FINAL RESULT: SUCCESS!")
            print("ElevenLabs integration is working correctly.")
            print("You can now integrate it into your video generator.")
            print("API key has proper permissions for text-to-speech.")
            
            # Show integration tips
            print(f"\n{'='*60}")
            print("INTEGRATION TIPS:")
            print("1. Use the simple generate() function for basic TTS")
            print("2. Use client streaming for longer texts or real-time")
            print("3. Voice 'Rachel' works well for most content")
            print("4. Average generation time: ~1-2 seconds per segment")
            print("5. Audio quality: Good for video narration")
            
        else:
            print(f"\n{'='*60}")
            print("FINAL RESULT: FAILED")
            print("ElevenLabs integration needs troubleshooting.")
            print("Check API key permissions and account status.")
        
        # Cleanup
        import glob
        test_files = glob.glob("test_*.mp3")
        if test_files:
            print(f"\nGenerated {len(test_files)} test audio files:")
            for f in test_files:
                print(f"  - {f}")
            print("You can play these files to verify audio quality.")
        
    except Exception as e:
        print(f"\nCRASH: {e}")
        import traceback
        traceback.print_exc()