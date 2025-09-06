#!/usr/bin/env python3
"""
Simple test to check if audio generation works
"""

import sys
import os

# Add local_functions to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'local_functions'))

def test_audio_generation():
    """Test just the audio generation part"""
    print("Testing audio generation...")
    
    try:
        from textToSpeech_gtts import generate_speech_local
        
        # Test with a simple message
        test_text = "This is a test of the AI video generator's audio system. The audio should be properly synchronized with the video."
        
        print(f"Generating speech for: {test_text}")
        filename, duration = generate_speech_local(test_text, "en")
        
        if os.path.exists(filename):
            file_size = os.path.getsize(filename)
            print(f"SUCCESS: Audio generated!")
            print(f"  File: {filename}")
            print(f"  Duration: {duration:.2f} seconds")
            print(f"  Size: {file_size} bytes")
            
            # Basic validation
            if file_size > 1000:  # At least 1KB
                print("Audio file appears to be valid size")
                return True
            else:
                print("WARNING: Audio file seems too small")
                return False
        else:
            print("ERROR: Audio file not created")
            return False
            
    except Exception as e:
        print(f"ERROR: Audio generation failed: {e}")
        return False

def test_dependencies():
    """Check if critical dependencies are available"""
    print("\nChecking dependencies...")
    
    dependencies = [
        ('gtts', 'Google Text-to-Speech'),
        ('pydub', 'Audio processing'),
        ('PIL', 'Image processing'),  
        ('requests', 'HTTP requests'),
        ('numpy', 'Numerical computing')
    ]
    
    results = []
    for module, description in dependencies:
        try:
            __import__(module)
            print(f"  {module}: OK ({description})")
            results.append(True)
        except ImportError:
            print(f"  {module}: MISSING ({description})")
            results.append(False)
    
    return all(results)

def main():
    print("Simple Audio System Test")
    print("=" * 40)
    
    # Test dependencies first
    deps_ok = test_dependencies()
    
    if not deps_ok:
        print("\nSome dependencies are missing. Please install with:")
        print("pip install gtts pydub pillow requests numpy")
        return False
    
    # Test audio generation
    audio_ok = test_audio_generation()
    
    if audio_ok:
        print("\nAUDIO TEST PASSED!")
        print("The audio system is working correctly.")
        print("Your videos should now have audio!")
        return True
    else:
        print("\nAUDIO TEST FAILED!")
        print("There are still issues with audio generation.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)