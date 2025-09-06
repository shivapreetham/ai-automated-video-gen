#!/usr/bin/env python3
"""
Basic test of MoviePy functionality
"""

import sys
import os

# Add local_functions to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'local_functions'))

def test_moviepy_imports():
    """Test if MoviePy imports work"""
    print("Testing MoviePy imports...")
    
    try:
        import moviepy.editor as mpy
        print("  moviepy.editor: OK")
        
        # Test basic classes
        video_clip = getattr(mpy, 'VideoFileClip', None)
        audio_clip = getattr(mpy, 'AudioFileClip', None)
        image_clip = getattr(mpy, 'ImageClip', None)
        
        print(f"  VideoFileClip: {'OK' if video_clip else 'MISSING'}")
        print(f"  AudioFileClip: {'OK' if audio_clip else 'MISSING'}")
        print(f"  ImageClip: {'OK' if image_clip else 'MISSING'}")
        
        return True
    except Exception as e:
        print(f"  ERROR: {e}")
        return False

def test_basic_video_creation():
    """Test creating a basic video clip"""
    print("\nTesting basic video creation...")
    
    try:
        import moviepy.editor as mpy
        from PIL import Image
        import numpy as np
        
        # Create a simple colored image
        width, height = 640, 480
        color_image = np.full((height, width, 3), [100, 150, 200], dtype=np.uint8)
        
        # Save as temporary image
        temp_img = "test_temp_image.png"
        Image.fromarray(color_image).save(temp_img)
        
        # Create an ImageClip
        clip = mpy.ImageClip(temp_img).set_duration(3)  # 3 second clip
        
        print(f"  Image clip created: {clip.duration}s, {clip.size}")
        
        # Clean up
        if os.path.exists(temp_img):
            os.remove(temp_img)
        
        return True
        
    except Exception as e:
        print(f"  ERROR: {e}")
        # Clean up on error
        if 'temp_img' in locals() and os.path.exists(temp_img):
            os.remove(temp_img)
        return False

def main():
    print("Basic MoviePy Test")
    print("=" * 30)
    
    # Test imports
    imports_ok = test_moviepy_imports()
    
    if not imports_ok:
        print("\nImports failed - MoviePy not working properly")
        return False
    
    # Test basic functionality
    basic_ok = test_basic_video_creation()
    
    if basic_ok:
        print("\nMOVIEPY TEST PASSED!")
        print("Basic MoviePy functionality is working.")
        return True
    else:
        print("\nMOVIEPY TEST FAILED!")
        print("There are issues with basic MoviePy operations.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)