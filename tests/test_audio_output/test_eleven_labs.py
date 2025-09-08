#!/usr/bin/env python3
"""
ElevenLabs API Test Script
Tests the ElevenLabs text-to-speech integration with comprehensive features
"""

import os
import time
import asyncio
from dotenv import load_dotenv
from datetime import datetime
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

def test_installation():
    """Test if ElevenLabs SDK is properly installed"""
    print("Testing ElevenLabs SDK Installation...")
    try:
        import elevenlabs
        from elevenlabs.client import ElevenLabs
        print(f"ElevenLabs SDK installed successfully (version: {elevenlabs.__version__ if hasattr(elevenlabs, '__version__') else 'unknown'})")
        return True
    except ImportError as e:
        print(f"ElevenLabs SDK not installed: {e}")
        print("Install with: pip install elevenlabs")
        return False

def test_api_key():
    """Test if API key is properly configured"""
    print("\n🔑 Testing API Key Configuration...")
    
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("❌ ELEVENLABS_API_KEY not found in environment variables")
        return False
    
    if not api_key.startswith('sk_'):
        print("❌ Invalid API key format (should start with 'sk_')")
        return False
    
    print(f"✅ API key found: {api_key[:8]}...{api_key[-4:]}")
    return True

def test_client_connection():
    """Test connection to ElevenLabs API"""
    print("\n🌐 Testing API Connection...")
    
    try:
        from elevenlabs.client import ElevenLabs
        
        client = ElevenLabs(
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )
        
        # Test connection by getting user info or models
        models = client.models.get_all()
        print(f"✅ Successfully connected to ElevenLabs API")
        print(f"📊 Available models: {len(models)}")
        
        # Print first few models
        for i, model in enumerate(models[:3]):
            print(f"   • {model.name} (ID: {model.model_id})")
        
        return client
    except Exception as e:
        print(f"❌ Failed to connect to API: {e}")
        return None

def test_get_voices(client: 'ElevenLabs'):
    """Test getting available voices"""
    print("\n🎤 Testing Voice Retrieval...")
    
    try:
        voices_response = client.voices.get_all()
        voices = voices_response.voices
        
        print(f"✅ Retrieved {len(voices)} voices")
        
        # Display first 5 voices with details
        print("\n🗣️  Available Voices:")
        for i, voice in enumerate(voices[:5]):
            print(f"   {i+1}. {voice.name}")
            print(f"      ID: {voice.voice_id}")
            print(f"      Category: {getattr(voice, 'category', 'N/A')}")
            print(f"      Labels: {getattr(voice, 'labels', {})}")
            print()
        
        return voices
    except Exception as e:
        print(f"❌ Failed to get voices: {e}")
        return []

def test_basic_tts(client: 'ElevenLabs', voices: List[Any]):
    """Test basic text-to-speech conversion"""
    print("\n🔊 Testing Basic Text-to-Speech...")
    
    if not voices:
        print("❌ No voices available for testing")
        return None
    
    try:
        # Use first available voice
        test_voice = voices[0]
        test_text = "Hello! This is a test of ElevenLabs text-to-speech integration with the AI Video Generator."
        
        print(f"📝 Converting text: '{test_text[:50]}...'")
        print(f"🎤 Using voice: {test_voice.name} ({test_voice.voice_id})")
        
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
        
        print(f"✅ Text-to-speech conversion successful!")
        print(f"⏱️  Generation time: {generation_time:.2f}s")
        print(f"📁 Output file: {output_file}")
        print(f"📊 File size: {file_size:.2f} KB")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Text-to-speech conversion failed: {e}")
        return None

def test_voice_settings(client: 'ElevenLabs', voices: List[Any]):
    """Test custom voice settings"""
    print("\n⚙️  Testing Voice Settings...")
    
    if not voices:
        print("❌ No voices available for testing")
        return None
    
    try:
        test_voice = voices[0]
        test_text = "This is a test with custom voice settings for stability and similarity boost."
        
        # Custom voice settings
        voice_settings = {
            "stability": 0.75,
            "similarity_boost": 0.85,
            "style": 0.5,
            "use_speaker_boost": True
        }
        
        print(f"🎛️  Voice settings: {voice_settings}")
        
        audio = client.text_to_speech.convert(
            text=test_text,
            voice_id=test_voice.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128",
            voice_settings=voice_settings
        )
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_elevenlabs_settings_{timestamp}.mp3"
        
        with open(output_file, "wb") as f:
            f.write(audio)
        
        print(f"✅ Voice settings test successful!")
        print(f"📁 Output file: {output_file}")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Voice settings test failed: {e}")
        return None

def test_streaming_tts(client: 'ElevenLabs', voices: List[Any]):
    """Test streaming text-to-speech"""
    print("\n🌊 Testing Streaming Text-to-Speech...")
    
    if not voices:
        print("❌ No voices available for testing")
        return None
    
    try:
        test_voice = voices[0]
        test_text = "This is a streaming test. The audio should be generated and received in chunks rather than all at once."
        
        print(f"📡 Starting streaming conversion...")
        
        start_time = time.time()
        audio_stream = client.text_to_speech.convert_as_stream(
            text=test_text,
            voice_id=test_voice.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        
        # Collect audio chunks
        audio_data = b""
        chunk_count = 0
        
        for chunk in audio_stream:
            if isinstance(chunk, bytes):
                audio_data += chunk
                chunk_count += 1
        
        generation_time = time.time() - start_time
        
        # Save streamed audio
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_elevenlabs_stream_{timestamp}.mp3"
        
        with open(output_file, "wb") as f:
            f.write(audio_data)
        
        file_size = len(audio_data) / 1024  # KB
        
        print(f"✅ Streaming test successful!")
        print(f"📊 Received {chunk_count} audio chunks")
        print(f"⏱️  Total generation time: {generation_time:.2f}s")
        print(f"📁 Output file: {output_file}")
        print(f"📊 File size: {file_size:.2f} KB")
        
        return output_file
        
    except Exception as e:
        print(f"❌ Streaming test failed: {e}")
        return None

def test_different_models(client: 'ElevenLabs', voices: List[Any]):
    """Test different ElevenLabs models"""
    print("\n🤖 Testing Different Models...")
    
    if not voices:
        print("❌ No voices available for testing")
        return []
    
    models_to_test = [
        "eleven_multilingual_v2",
        "eleven_monolingual_v1", 
        "eleven_turbo_v2"
    ]
    
    test_text = "Testing different ElevenLabs models for quality comparison."
    test_voice = voices[0]
    output_files = []
    
    for model_id in models_to_test:
        try:
            print(f"🧠 Testing model: {model_id}")
            
            start_time = time.time()
            audio = client.text_to_speech.convert(
                text=test_text,
                voice_id=test_voice.voice_id,
                model_id=model_id,
                output_format="mp3_44100_128"
            )
            generation_time = time.time() - start_time
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_elevenlabs_{model_id}_{timestamp}.mp3"
            
            with open(output_file, "wb") as f:
                f.write(audio)
            
            file_size = len(audio) / 1024
            
            print(f"   ✅ {model_id}: {generation_time:.2f}s, {file_size:.2f} KB")
            output_files.append(output_file)
            
        except Exception as e:
            print(f"   ❌ {model_id} failed: {e}")
    
    return output_files

async def test_async_tts():
    """Test asynchronous text-to-speech"""
    print("\n⚡ Testing Async Text-to-Speech...")
    
    try:
        from elevenlabs.client import AsyncElevenLabs
        
        client = AsyncElevenLabs(
            api_key=os.getenv('ELEVENLABS_API_KEY')
        )
        
        # Get voices async
        voices_response = await client.voices.get_all()
        voices = voices_response.voices
        
        if not voices:
            print("❌ No voices available for async testing")
            return None
        
        test_voice = voices[0]
        test_text = "This is an asynchronous text-to-speech conversion test."
        
        print(f"🔄 Converting text asynchronously...")
        
        start_time = time.time()
        audio = await client.text_to_speech.convert(
            text=test_text,
            voice_id=test_voice.voice_id,
            model_id="eleven_multilingual_v2",
            output_format="mp3_44100_128"
        )
        generation_time = time.time() - start_time
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"test_elevenlabs_async_{timestamp}.mp3"
        
        with open(output_file, "wb") as f:
            f.write(audio)
        
        file_size = len(audio) / 1024
        
        print(f"✅ Async TTS successful!")
        print(f"⏱️  Generation time: {generation_time:.2f}s")
        print(f"📁 Output file: {output_file}")
        print(f"📊 File size: {file_size:.2f} KB")
        
        await client.aclose()
        return output_file
        
    except Exception as e:
        print(f"❌ Async TTS failed: {e}")
        return None

def test_integration_with_video_generator(client: 'ElevenLabs', voices: List[Any]):
    """Test integration patterns for video generator"""
    print("\n🎬 Testing Video Generator Integration Patterns...")
    
    if not voices:
        print("❌ No voices available for integration testing")
        return None
    
    # Simulate video generator segments
    segments = [
        "Welcome to our AI generated video story.",
        "In this first segment, we explore the fascinating world of artificial intelligence.",
        "The second part delves into machine learning applications.",
        "Finally, we conclude with future possibilities and innovations."
    ]
    
    try:
        output_files = []
        total_duration = 0
        
        for i, segment in enumerate(segments, 1):
            print(f"🎭 Processing segment {i}/{len(segments)}")
            
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
            print(f"   ✅ Segment {i}: {generation_time:.2f}s")
        
        print(f"\n✅ Video integration test successful!")
        print(f"📊 Total segments: {len(segments)}")
        print(f"⏱️  Total generation time: {total_duration:.2f}s")
        print(f"📁 Output files: {len(output_files)}")
        
        return output_files
        
    except Exception as e:
        print(f"❌ Video integration test failed: {e}")
        return []

def cleanup_test_files():
    """Clean up test audio files"""
    print("\n🧹 Cleaning up test files...")
    
    import glob
    test_files = glob.glob("test_*.mp3")
    
    cleaned_count = 0
    for file in test_files:
        try:
            os.remove(file)
            cleaned_count += 1
        except Exception as e:
            print(f"⚠️  Could not remove {file}: {e}")
    
    print(f"🗑️  Cleaned up {cleaned_count} test files")

def main():
    """Main test function"""
    print("=" * 60)
    print("🎙️  ElevenLabs API Integration Test Suite")
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
    
    # Test 6: Voice Settings
    settings_result = test_voice_settings(client, voices)
    
    # Test 7: Streaming
    streaming_result = test_streaming_tts(client, voices)
    
    # Test 8: Different Models
    model_results = test_different_models(client, voices)
    
    # Test 9: Video Integration
    integration_results = test_integration_with_video_generator(client, voices)
    
    # Test 10: Async (separate function)
    print("\n🔄 Running async tests...")
    try:
        async_result = asyncio.run(test_async_tts())
    except Exception as e:
        print(f"❌ Async test setup failed: {e}")
        async_result = None
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    tests_passed = 0
    total_tests = 6
    
    if basic_result:
        tests_passed += 1
        print("✅ Basic TTS: PASSED")
    else:
        print("❌ Basic TTS: FAILED")
    
    if settings_result:
        tests_passed += 1
        print("✅ Voice Settings: PASSED")
    else:
        print("❌ Voice Settings: FAILED")
    
    if streaming_result:
        tests_passed += 1
        print("✅ Streaming TTS: PASSED")
    else:
        print("❌ Streaming TTS: FAILED")
    
    if model_results:
        tests_passed += 1
        print("✅ Multiple Models: PASSED")
    else:
        print("❌ Multiple Models: FAILED")
    
    if integration_results:
        tests_passed += 1
        print("✅ Video Integration: PASSED")
    else:
        print("❌ Video Integration: FAILED")
    
    if async_result:
        tests_passed += 1
        print("✅ Async TTS: PASSED")
    else:
        print("❌ Async TTS: FAILED")
    
    print(f"\n📊 Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! ElevenLabs integration is ready.")
    elif tests_passed >= total_tests * 0.7:
        print("⚠️  Most tests passed. ElevenLabs integration is mostly working.")
    else:
        print("❌ Many tests failed. Check your API key and configuration.")
    
    # Optional cleanup
    response = input("\n🗑️  Clean up test audio files? (y/n): ").lower().strip()
    if response in ['y', 'yes']:
        cleanup_test_files()
    
    return tests_passed >= total_tests * 0.7

if __name__ == "__main__":
    try:
        success = main()
        print(f"\n🏁 Test suite completed {'successfully' if success else 'with issues'}")
    except KeyboardInterrupt:
        print("\n⏹️  Test interrupted by user")
    except Exception as e:
        print(f"\n💥 Test suite crashed: {e}")