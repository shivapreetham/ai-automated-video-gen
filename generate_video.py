#!/usr/bin/env python3
"""
Local AI Video Generator - Main Entry Point
Generates videos using Pollinations AI and gTTS without paid APIs
"""

import sys
import os

# Add local_functions to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'local_functions'))

from local_video_generator import LocalVideoGenerator

def main():
    """Simple interface for video generation"""
    
    if len(sys.argv) < 2:
        print("Usage: python generate_video.py \"Your video topic\"")
        print("Example: python generate_video.py \"The history of artificial intelligence\"")
        sys.exit(1)
    
    topic = sys.argv[1]
    print(f"Generating video about: {topic}")
    
    # Create generator with default settings
    generator = LocalVideoGenerator()
    
    # Generate video
    result = generator.generate_video(topic=topic)
    
    if result['success']:
        print(f"\n✅ Success! Video generated:")
        print(f"📁 Output folder: {result['session_dir']}")
        print(f"🎥 Video file: {result['final_video']}")
        print(f"⏱️ Duration: {result.get('duration', 'Unknown')} seconds")
    else:
        print(f"\n❌ Failed: {result.get('error', 'Unknown error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()