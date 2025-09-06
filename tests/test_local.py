#!/usr/bin/env python3
"""
Quick test script for local video generator
"""

import sys
import os

# Add local_functions to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'local_functions'))

def test_speech():
    """Test text-to-speech generation"""
    print("Testing speech generation...")
    
    try:
        from textToSpeech_gtts import generate_speech_local
        filename, duration = generate_speech_local("Hello, this is a test of the local video generator.", "en")
        print(f"Speech test passed: {filename} ({duration:.2f}s)")
        return True
    except Exception as e:
        print(f"Speech test failed: {e}")
        return False

def test_image():
    """Test image generation"""
    print("Testing image generation...")
    
    try:
        from PromptImagesToVideo_pollinations import generate_image_pollinations
        img_path = generate_image_pollinations("A beautiful mountain landscape", 512, 512)
        if os.path.exists(img_path):
            print(f"Image test passed: {img_path}")
            os.remove(img_path)  # Clean up
            return True
        else:
            print("Image test failed: No image file created")
            return False
    except Exception as e:
        print(f"Image test failed: {e}")
        return False

def test_full_pipeline():
    """Test the full video generation pipeline"""
    print("Testing full video generation...")
    
    try:
        from local_video_generator import LocalVideoGenerator
        
        generator = LocalVideoGenerator(output_dir="local_video_results")
        result = generator.generate_video(
            topic="Testing the video generator",
            width=512,
            height=512,
            fps=16,
            video_duration=8
        )
        
        if result['success']:
            print(f"Full pipeline test passed!")
            print(f"Output: {result['session_dir']}")
            print(f"Video: {result['final_video']}")
            return True
        else:
            print(f"Full pipeline test failed: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"Full pipeline test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Running Local Video Generator Tests\n")
    
    tests = [
        ("Speech Generation", test_speech),
        ("Image Generation", test_image),
        ("Full Pipeline", test_full_pipeline)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        print(f"\n{'='*50}")
        print(f"Running: {test_name}")
        print('='*50)
        
        success = test_func()
        results.append((test_name, success))
    
    # Print summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY")
    print('='*50)
    
    all_passed = True
    for test_name, success in results:
        status = "PASSED" if success else "FAILED"
        print(f"{test_name:<20} {status}")
        if not success:
            all_passed = False
    
    if all_passed:
        print(f"\nAll tests passed! Your local setup is working correctly.")
        print(f"You can now run: python local_functions/local_video_generator.py \"your topic\"")
    else:
        print(f"\nSome tests failed. Check the error messages above.")
    
    return all_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)