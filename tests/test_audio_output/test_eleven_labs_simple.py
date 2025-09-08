#!/usr/bin/env python3
"""
ElevenLabs API Simple Test Script
Tests the ElevenLabs text-to-speech integration without emojis
"""

import os
import time
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

def test_installation():
    """Test if ElevenLabs SDK is properly installed"""
    print("Testing ElevenLabs SDK Installation...")
    try:
        import elevenlabs
        from elevenlabs.client import ElevenLabs
        print(f"SUCCESS: ElevenLabs SDK installed successfully")
        return True
    except ImportError as e:
        print(f"ERROR: ElevenLabs SDK not installed: {e}")
        print("SOLUTION: Install with: pip install elevenlabs")
        return False

def test_api_key():
    """Test if API key is properly configured"""
    print("\nTesting API Key Configuration...")
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not found in environment variables")
        return False
    
    if not api_key.startswith('sk_'):
        print("ERROR: Invalid API key format (should start with 'sk_')")
        return False
    
    print(f"SUCCESS: API key found: {api_key[:8]}...{api_key[-4:]}")
    return True

def test_client_connection():
    """Test connection to ElevenLabs API"""
    print("\nTesting API Connection...")
    
    try:
        from elevenlabs.client import ElevenLabs
        
        client = ElevenLabs(
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )
        
        # Test connection by getting voices (simpler test)
        voices_response = client.voices.get_all()
        print(f"SUCCESS: Connected to ElevenLabs API")
        print(f"INFO: API connection verified")
        
        return client
    except Exception as e:
        print(f"ERROR: Failed to connect to API: {e}")
        return None

def test_get_voices(client):
    """Test getting available voices"""
    print("\nTesting Voice Retrieval...")
    
    try:
        voices_response = client.voices.get_all()
        voices = voices_response.voices
        
        print(f"SUCCESS: Retrieved {len(voices)} voices")
        
        # Display first 5 voices with details
        print("\nAvailable Voices:")
        for i, voice in enumerate(voices[:5]):
            print(f"   {i+1}. {voice.name}")
            print(f"      ID: {voice.voice_id}")
            print(f"      Category: {getattr(voice, 'category', 'N/A')}")
            print()
        
        return voices
    except Exception as e:
        print(f"ERROR: Failed to get voices: {e}")
        return []

def test_basic_tts(client, voices):
    """Test basic text-to-speech conversion"""
    print("\nTesting Basic Text-to-Speech...")
    
    if not voices:
        print("ERROR: No voices available for testing")
        return None
    
    try:
        # Use first available voice
        test_voice = voices[0]
        test_text = "Hello! This is a test of ElevenLabs text-to-speech integration with the AI Video Generator."
        
        print(f"TEXT: Converting '{test_text[:50]}...'")
        print(f"VOICE: Using {test_voice.name} ({test_voice.voice_id})")
        
        # Generate audio
        start_time = time.time()
        audio = client.text_to_speech.convert(
            text=test_text,
            voice_id=test_voice.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        generation_time = time.time() - start_time
        
        # Save audio to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_elevenlabs_{timestamp}.mp3"
        
        with open(output_file, "wb") as f:
            f.write(audio)
        
        file_size = os.path.getsize(output_file) / 1024  # KB
        
        print(f"SUCCESS: Text-to-speech conversion successful!")
        print(f"TIME: Generation time: {generation_time:.2f}s")
        print(f"FILE: Output file: {output_file}")
        print(f"SIZE: File size: {file_size:.2f} KB")
        
        return output_file
        
    except Exception as e:
        print(f"ERROR: Text-to-speech conversion failed: {e}")
        return None

def test_different_voices(client, voices):
    """Test different voices"""
    print("\nTesting Different Voices...")
    
    if len(voices) < 2:
        print("WARNING: Less than 2 voices available, skipping voice comparison")
        return []
    
    test_text = "This is a test to compare different voice qualities."
    output_files = []
    
    # Test first 3 voices
    for i, voice in enumerate(voices[:3]):
        try:
            print(f"TESTING: Voice {i+1}: {voice.name}")
            
            start_time = time.time()
            audio = client.text_to_speech.convert(
                text=test_text,
                voice_id=voice.voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            generation_time = time.time() - start_time
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_voice_{voice.name.replace(' ', '_')}_{timestamp}.mp3"
            
            with open(output_file, "wb") as f:
                f.write(audio)
            
            file_size = len(audio) / 1024
            print(f"   SUCCESS: {generation_time:.2f}s, {file_size:.2f} KB")
            output_files.append(output_file)
            
        except Exception as e:
            print(f"   ERROR: Voice {voice.name} failed: {e}")
    
    return output_files

def test_video_segments(client, voices):
    """Test video segment generation"""
    print("\nTesting Video Segment Generation...")
    
    if not voices:
        print("ERROR: No voices available for segment testing")
        return []
    
    # Simulate video segments
    segments = [
        "Welcome to our AI generated video story about the future of technology.",
        "In this first segment, we explore artificial intelligence and machine learning.",
        "The second part discusses how AI is transforming various industries.",
        "Finally, we look at the exciting possibilities that lie ahead for humanity."
    ]
    
    try:
        output_files = []
        total_duration = 0
        
        for i, segment in enumerate(segments, 1):
            print(f"SEGMENT {i}/{len(segments)}: Processing...")
            
            start_time = time.time()
            audio = client.text_to_speech.convert(
                text=segment,
                voice_id=voices[0].voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            generation_time = time.time() - start_time
            total_duration += generation_time
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_segment_{i:02d}_{timestamp}.mp3"
            
            with open(output_file, "wb") as f:
                f.write(audio)
            
            output_files.append(output_file)
            print(f"   SUCCESS: Segment {i} completed in {generation_time:.2f}s")
        
        print(f"\nSUCCESS: All segments completed!")
        print(f"TOTAL TIME: {total_duration:.2f}s for {len(segments)} segments")
        print(f"AVERAGE: {total_duration/len(segments):.2f}s per segment")
        
        return output_files
        
    except Exception as e:
        print(f"ERROR: Video segment test failed: {e}")
        return []

def cleanup_test_files():
    """Clean up test audio files"""
    print("\nCleaning up test files...")
    
    import glob
    test_files = glob.glob("test_*.mp3")
    
    if not test_files:
        print("INFO: No test files to clean up")
        return
    
    print(f"FOUND: {len(test_files)} test files")
    response = input("Delete test files? (y/n): ").lower().strip()
    
    if response in ['y', 'yes']:
        cleaned_count = 0
        for file in test_files:
            try:
                os.remove(file)
                cleaned_count += 1
                print(f"   DELETED: {file}")
            except Exception as e:
                print(f"   ERROR: Could not remove {file}: {e}")
        
        print(f"CLEANUP: Removed {cleaned_count} test files")
    else:
        print("KEPT: Test files preserved")

def main():
    """Main test function"""
    print("=" * 60)
    print("ELEVENLABS API INTEGRATION TEST SUITE")
    print("=" * 60)
    
    # Test 1: Installation
    if not test_installation():
        return False
    
    # Test 2: API Key
    if not test_api_key():
        return False
    
    # Test 3: Connection
    client = test_client_connection()
    if not client:
        return False
    
    # Test 4: Get Voices
    voices = test_get_voices(client)
    if not voices:
        return False
    
    # Test 5: Basic TTS
    basic_result = test_basic_tts(client, voices)
    
    # Test 6: Different Voices
    voice_results = test_different_voices(client, voices)
    
    # Test 7: Video Segments
    segment_results = test_video_segments(client, voices)
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 3
    
    if basic_result:
        tests_passed += 1
        print("PASS: Basic TTS")
    else:
        print("FAIL: Basic TTS")
    
    if voice_results:
        tests_passed += 1
        print("PASS: Voice Testing")
    else:
        print("FAIL: Voice Testing")
    
    if segment_results:
        tests_passed += 1
        print("PASS: Video Segments")
    else:
        print("FAIL: Video Segments")
    
    print(f"\nRESULTS: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("STATUS: All tests passed! ElevenLabs integration is ready.")
        success = True
    elif tests_passed >= 2:
        print("STATUS: Most tests passed. ElevenLabs integration is working.")
        success = True
    else:
        print("STATUS: Tests failed. Check your API key and configuration.")
        success = False
    
    # Cleanup
    cleanup_test_files()
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        print(f"\nCOMPLETED: Test suite finished {'successfully' if success else 'with issues'}")
    except KeyboardInterrupt:
        print("\nINTERRUPTED: Test stopped by user")
    except Exception as e:
        print(f"\nCRASHED: Test suite error: {e}")
        import traceback
        traceback.print_exc()