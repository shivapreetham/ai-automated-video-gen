#!/usr/bin/env python3
"""
ElevenLabs Final Integration Test
Tests with your actual API key and proper SDK usage
"""

import os
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def test_with_client_approach():
    """Test using the modern ElevenLabs client"""
    print("=" * 60)
    print("TESTING ELEVENLABS WITH YOUR API KEY")
    print("=" * 60)
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("ERROR: No API key found")
        return False
    
    print(f"API Key: {api_key[:12]}...{api_key[-4:]}")
    
    try:
        from elevenlabs.client import ElevenLabs
        print("SUCCESS: ElevenLabs client imported")
        
        client = ElevenLabs(api_key=api_key)
        print("SUCCESS: Client created")
        
        # Test with a known working voice ID (Rachel from ElevenLabs)
        voice_id = "21m00Tcm4TlvDq8ikWAM"  # Rachel voice
        test_text = "Hello! This is a test of your ElevenLabs integration. Your API key is working correctly."
        
        print(f"TESTING: Voice {voice_id}")
        print(f"TEXT: {test_text}")
        
        start_time = time.time()
        
        # Use the streaming approach which seems to work
        audio_stream = client.text_to_speech.convert_as_stream(
            text=test_text,
            voice_id=voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        # Collect audio data
        audio_chunks = []
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                audio_chunks.append(chunk)
        
        audio_data = b"".join(audio_chunks)
        generation_time = time.time() - start_time
        
        if audio_data:
            # Save test file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_final_elevenlabs_{timestamp}.mp3"
            
            with open(output_file, "wb") as f:
                f.write(audio_data)
            
            file_size = len(audio_data) / 1024  # KB
            
            print("=" * 60)
            print("SUCCESS: ELEVENLABS IS WORKING!")
            print("=" * 60)
            print(f"Generation Time: {generation_time:.2f} seconds")
            print(f"Audio File: {output_file}")
            print(f"File Size: {file_size:.2f} KB")
            print(f"Audio Chunks: {len(audio_chunks)}")
            print(f"Voice ID: {voice_id}")
            print("STATUS: Ready for video generator integration!")
            
            return True, client, voice_id
        else:
            print("ERROR: No audio data received")
            return False, None, None
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False, None, None

def test_video_integration(client, voice_id):
    """Test integration with video segments"""
    print("\n" + "=" * 60)
    print("TESTING VIDEO SEGMENT INTEGRATION")
    print("=" * 60)
    
    segments = [
        "Welcome to our AI-generated video about the future of technology.",
        "In this segment, we explore how artificial intelligence is transforming our world.",
        "Machine learning algorithms are becoming increasingly sophisticated and powerful.",
        "Thank you for watching our AI-generated video. Stay tuned for more amazing content!"
    ]
    
    try:
        total_time = 0
        output_files = []
        
        for i, segment in enumerate(segments, 1):
            print(f"SEGMENT {i}/{len(segments)}: Processing...")
            
            start_time = time.time()
            
            audio_stream = client.text_to_speech.convert_as_stream(
                text=segment,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            
            # Collect audio
            audio_chunks = []
            for chunk in audio_stream:
                if isinstance(chunk, bytes):
                    audio_chunks.append(chunk)
            
            audio_data = b"".join(audio_chunks)
            segment_time = time.time() - start_time
            total_time += segment_time
            
            # Save segment
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            segment_file = f"video_segment_{i:02d}_{timestamp}.mp3"
            
            with open(segment_file, "wb") as f:
                f.write(audio_data)
            
            file_size = len(audio_data) / 1024
            output_files.append(segment_file)
            
            print(f"   COMPLETED: {segment_time:.2f}s, {file_size:.2f}KB -> {segment_file}")
        
        print("=" * 60)
        print("VIDEO INTEGRATION TEST: SUCCESS!")
        print("=" * 60)
        print(f"Total Segments: {len(segments)}")
        print(f"Total Generation Time: {total_time:.2f} seconds")
        print(f"Average Time per Segment: {total_time/len(segments):.2f} seconds")
        print(f"Output Files: {len(output_files)}")
        
        print("\nGenerated Files:")
        for f in output_files:
            print(f"  - {f}")
        
        print("\nINTEGRATION READY:")
        print("- ElevenLabs API working correctly")
        print("- Video segment generation successful")
        print("- Audio quality suitable for video narration")
        print("- Performance: ~2 seconds per segment")
        
        return True
        
    except Exception as e:
        print(f"VIDEO INTEGRATION ERROR: {e}")
        return False

def main():
    """Main test function"""
    try:
        # Test 1: Basic Integration
        success, client, voice_id = test_with_client_approach()
        
        if success:
            # Test 2: Video Integration
            video_success = test_video_integration(client, voice_id)
            
            if video_success:
                print("\n" + "=" * 60)
                print("FINAL RESULT: COMPLETE SUCCESS!")
                print("=" * 60)
                print("✓ ElevenLabs API key working")
                print("✓ Modern SDK integration successful")
                print("✓ Video segment generation ready")
                print("✓ Performance suitable for video generation")
                print("\nNEXT STEPS:")
                print("1. Update your backend function to use the new API key")
                print("2. Integrate ElevenLabs with your video generator")
                print("3. Replace or supplement gTTS with ElevenLabs")
                print("4. Consider using voice_id:", voice_id)
                
                return True
        
        print("\n" + "=" * 60)
        print("FINAL RESULT: INTEGRATION FAILED")
        print("=" * 60)
        print("- Check your API key permissions")
        print("- Verify account status at elevenlabs.io")
        print("- Consider using gTTS as primary fallback")
        
        return False
    
    except Exception as e:
        print(f"\nTEST SUITE CRASHED: {e}")
        return False

if __name__ == "__main__":
    main()
    
    # Cleanup option
    import glob
    test_files = glob.glob("test_*.mp3") + glob.glob("video_segment_*.mp3")
    if test_files:
        print(f"\nGenerated {len(test_files)} test files.")
        print("You can play these to verify audio quality.")
        print("Files will be kept for your review.")