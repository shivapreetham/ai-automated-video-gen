#!/usr/bin/env python3
"""
ElevenLabs API Minimal Test Script
Tests text-to-speech with default voice without requiring voice permissions
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
    print("ELEVENLABS MINIMAL TEST - TEXT TO SPEECH")
    print("=" * 60)
    
    # Check API key
    api_key = os.getenv('ELEVENLABS_API_KEY')
    if not api_key:
        print("ERROR: ELEVENLABS_API_KEY not found in environment")
        return False
    
    print(f"API KEY: Found key starting with {api_key[:8]}...")
    
    # Test import
    try:
        from elevenlabs.client import ElevenLabs
        print("IMPORT: ElevenLabs SDK imported successfully")
    except ImportError as e:
        print(f"ERROR: Cannot import ElevenLabs: {e}")
        return False
    
    # Create client
    try:
        client = ElevenLabs(api_key=api_key)
        print("CLIENT: ElevenLabs client created")
    except Exception as e:
        print(f"ERROR: Failed to create client: {e}")
        return False
    
    # Test basic TTS with known voice ID (Rachel - a common default voice)
    known_voice_ids = [
        "21m00Tcm4TlvDq8ikWAM",  # Rachel
        "AZnzlk1XvdvUeBnXmlld",  # Domi
        "EXAVITQu4vr4xnSDxMaL",  # Bella
        "ErXwobaYiN019PkySvjV",  # Antoni
        "MF3mGyEYCl7XYWbV9V6O",  # Elli
        "TxGEqnHWrfWFTfGW9XjX",  # Josh
        "VR6AewLTigWG4xSOukaG",  # Arnold
        "pNInz6obpgDQGcFmaJgB",  # Adam
        "yoZ06aMxZJJ28mfd3POQ",  # Sam
    ]
    
    test_text = "Hello! This is a test of ElevenLabs text to speech integration. The API key is working correctly."
    
    success = False
    for i, voice_id in enumerate(known_voice_ids):
        try:
            print(f"\nTEST {i+1}: Trying voice ID: {voice_id}")
            
            start_time = time.time()
            audio = client.text_to_speech.convert(
                text=test_text,
                voice_id=voice_id,
                model_id="eleven_multilingual_v2",
                output_format="mp3_44100_128"
            )
            generation_time = time.time() - start_time
            
            # Save audio
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"test_elevenlabs_working_{timestamp}.mp3"
            
            with open(output_file, "wb") as f:
                f.write(audio)
            
            file_size = len(audio) / 1024
            
            print(f"SUCCESS: Text-to-speech working!")
            print(f"VOICE: {voice_id}")
            print(f"TIME: {generation_time:.2f} seconds")
            print(f"FILE: {output_file}")
            print(f"SIZE: {file_size:.2f} KB")
            
            success = True
            break
            
        except Exception as e:
            print(f"FAILED: Voice {voice_id} - {str(e)[:100]}...")
            continue
    
    if success:
        print(f"\n{'='*60}")
        print("RESULT: SUCCESS - ElevenLabs integration is working!")
        print("INFO: Your API key has text-to-speech permissions")
        print("READY: You can integrate ElevenLabs into your video generator")
        
        # Test video segment simulation
        print(f"\n{'='*60}")
        print("BONUS TEST: Video Segment Simulation")
        print("="*60)
        
        segments = [
            "Welcome to our AI generated video.",
            "This is segment two of our story.",
            "Here is the third and final segment."
        ]
        
        working_voice = voice_id  # Use the voice that worked
        
        try:
            total_time = 0
            for i, segment in enumerate(segments, 1):
                start_time = time.time()
                audio = client.text_to_speech.convert(
                    text=segment,
                    voice_id=working_voice,
                    model_id="eleven_multilingual_v2",
                    output_format="mp3_44100_128"
                )
                gen_time = time.time() - start_time
                total_time += gen_time
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                segment_file = f"test_segment_{i:02d}_{timestamp}.mp3"
                
                with open(segment_file, "wb") as f:
                    f.write(audio)
                
                print(f"SEGMENT {i}: Generated in {gen_time:.2f}s -> {segment_file}")
            
            print(f"\nVIDEO TEST: Successfully generated {len(segments)} segments")
            print(f"TOTAL TIME: {total_time:.2f} seconds")
            print(f"AVERAGE: {total_time/len(segments):.2f} seconds per segment")
            print("INTEGRATION: Ready for video generator!")
            
        except Exception as e:
            print(f"VIDEO TEST: Failed - {e}")
    
    else:
        print(f"\n{'='*60}")
        print("RESULT: FAILED - Could not generate audio with any voice")
        print("ISSUE: Check your API key permissions or account status")
        print("HELP: Visit https://elevenlabs.io/account to check your API key")
    
    # Cleanup option
    print(f"\n{'='*60}")
    import glob
    test_files = glob.glob("test_*.mp3")
    if test_files:
        print(f"CLEANUP: Found {len(test_files)} test files:")
        for f in test_files:
            print(f"   - {f}")
        
        response = input("Delete test files? (y/n): ").lower().strip()
        if response in ['y', 'yes']:
            for f in test_files:
                try:
                    os.remove(f)
                    print(f"DELETED: {f}")
                except Exception as e:
                    print(f"ERROR: Could not delete {f}: {e}")
        else:
            print("KEPT: Test files preserved for your review")
    
    return success

if __name__ == "__main__":
    try:
        success = main()
        print(f"\nFINAL: Test {'PASSED' if success else 'FAILED'}")
    except Exception as e:
        print(f"\nCRASH: {e}")
        import traceback
        traceback.print_exc()