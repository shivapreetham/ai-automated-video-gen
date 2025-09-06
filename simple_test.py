#!/usr/bin/env python3
"""
Simple test script without FFmpeg dependency
"""

import sys
import os

# Add local_functions to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'local_functions'))

def test_speech_simple():
    """Test gTTS speech generation"""
    print("Testing gTTS speech generation...")
    
    try:
        from gtts import gTTS
        import tempfile
        
        # Test basic gTTS functionality
        text = "Hello, this is a test."
        tts = gTTS(text=text, lang='en', slow=False)
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        temp_path = temp_file.name
        temp_file.close()
        
        tts.save(temp_path)
        
        if os.path.exists(temp_path):
            file_size = os.path.getsize(temp_path)
            print(f"SUCCESS: Speech file created ({file_size} bytes)")
            os.remove(temp_path)
            return True
        else:
            print("FAILED: No speech file created")
            return False
            
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_image_simple():
    """Test Pollinations AI image generation"""
    print("Testing Pollinations AI image generation...")
    
    try:
        import requests
        import urllib.parse
        
        # Test basic image generation
        prompt = "A simple test image"
        encoded_prompt = urllib.parse.quote(prompt)
        url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=256&height=256&model=flux"
        
        print(f"Testing URL: {url}")
        response = requests.get(url, timeout=30)
        
        if response.status_code == 200 and len(response.content) > 1000:
            print(f"SUCCESS: Image generated ({len(response.content)} bytes)")
            return True
        else:
            print(f"FAILED: Bad response (status: {response.status_code}, size: {len(response.content)})")
            return False
            
    except Exception as e:
        print(f"FAILED: {e}")
        return False

def test_basic_dependencies():
    """Test if all basic dependencies are available"""
    print("Testing basic dependencies...")
    
    missing = []
    
    try:
        import gtts
        print("  gtts: OK")
    except ImportError:
        missing.append("gtts")
        print("  gtts: MISSING")
    
    try:
        import requests
        print("  requests: OK")
    except ImportError:
        missing.append("requests")
        print("  requests: MISSING")
    
    try:
        from PIL import Image
        print("  Pillow (PIL): OK")
    except ImportError:
        missing.append("Pillow")
        print("  Pillow (PIL): MISSING")
    
    try:
        import numpy
        print("  numpy: OK")
    except ImportError:
        missing.append("numpy")
        print("  numpy: MISSING")
    
    try:
        import moviepy
        print("  moviepy: OK")
    except ImportError:
        missing.append("moviepy")
        print("  moviepy: MISSING")
    
    if missing:
        print(f"MISSING PACKAGES: {', '.join(missing)}")
        print(f"Install with: pip install {' '.join(missing)}")
        return False
    else:
        print("All basic dependencies are available!")
        return True

def main():
    """Run simple tests"""
    print("Simple Local Video Generator Test")
    print("=" * 40)
    
    tests = [
        ("Dependencies", test_basic_dependencies),
        ("Speech (gTTS)", test_speech_simple),
        ("Image (Pollinations)", test_image_simple)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        print("-" * 20)
        success = test_func()
        results.append((test_name, success))
    
    # Summary
    print(f"\n{'='*40}")
    print("RESULTS:")
    
    all_passed = True
    for test_name, success in results:
        status = "PASS" if success else "FAIL"
        print(f"  {test_name:<20} {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print(f"\nAll basic tests passed!")
        print(f"Next step: Install FFmpeg for full video functionality")
        print(f"Download from: https://ffmpeg.org/download.html")
    else:
        print(f"\nSome tests failed. Install missing dependencies.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    input("\nPress Enter to exit...")  # Keep window open on Windows
    sys.exit(0 if success else 1)