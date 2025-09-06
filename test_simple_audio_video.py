#!/usr/bin/env python3
"""
Simple test to verify what MoviePy methods are available
"""

import os
import sys

def test_moviepy_methods():
    """Check what methods are available in MoviePy"""
    try:
        print("Testing MoviePy imports and methods...")
        
        import moviepy.editor as mpy
        print("MoviePy editor imported successfully")
        
        # Test ImageClip
        from PIL import Image
        import numpy as np
        
        # Create simple image
        color_image = np.full((100, 100, 3), [255, 0, 0], dtype=np.uint8)
        Image.fromarray(color_image).save("test_simple.png")
        
        # Test ImageClip
        img_clip = mpy.ImageClip("test_simple.png").set_duration(2)
        print(f"ImageClip methods: {[m for m in dir(img_clip) if not m.startswith('_')][:10]}")
        
        # Test VideoFileClip
        img_clip.write_videofile("test_simple.mp4", fps=12)
        video_clip = mpy.VideoFileClip("test_simple.mp4")
        print(f"VideoFileClip methods: {[m for m in dir(video_clip) if 'audio' in m.lower()]}")
        
        # Test if we can add audio differently
        if hasattr(video_clip, 'with_audio'):
            print("Found with_audio method")
        if hasattr(video_clip, 'set_audio'):
            print("Found set_audio method")  
        if hasattr(video_clip, 'audio'):
            print("Found audio property")
            
        # Cleanup
        video_clip.close()
        img_clip.close()
        
        # Clean up files
        for f in ["test_simple.png", "test_simple.mp4"]:
            if os.path.exists(f):
                os.remove(f)
                
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        return False

if __name__ == "__main__":
    test_moviepy_methods()