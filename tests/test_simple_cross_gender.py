#!/usr/bin/env python3
"""
Simple Cross-Gender Voice Assignment Test
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend_functions')

def main():
    print("=" * 60)
    print("CROSS-GENDER VOICE ASSIGNMENT TEST")
    print("=" * 60)
    
    try:
        from segment_audio_generator import generate_segment_audios, SMART_CHARACTER_VOICES, VOICE_CHARACTERISTICS
        
        print("VOICE CHARACTERISTICS:")
        print("-" * 30)
        for voice, chars in VOICE_CHARACTERISTICS.items():
            print(f"{voice}: {chars['gender']} voice, {chars['tone']} tone")
        
        print("\nCROSS-GENDER EXAMPLES:")
        print("-" * 30)
        cross_gender_examples = {
            "wise_woman": "Professional male voice for authoritative female",
            "female_warrior": "Deep male voice for strong female character", 
            "young_prince": "Female voice for young male character",
            "gentle_sage": "Warm female voice for gentle male character"
        }
        
        for char, description in cross_gender_examples.items():
            if char in SMART_CHARACTER_VOICES:
                voice = SMART_CHARACTER_VOICES[char]
                voice_gender = VOICE_CHARACTERISTICS.get(voice, {}).get('gender', 'unknown')
                print(f"{char} -> {voice} ({voice_gender}): {description}")
        
        # Test one cross-gender assignment
        print(f"\nTESTING CROSS-GENDER ASSIGNMENT:")
        print("=" * 40)
        
        test_script = {
            "story_title": "Cross-Gender Test",
            "segments": [
                {
                    "segment_number": 1,
                    "text": "The wise woman spoke with deep authority and commanded respect from all who heard her.",
                    "character_speaking": "wise_woman",
                    "segment_type": "dialog"
                }
            ],
            "characters": ["wise_woman"]
        }
        
        os.makedirs("simple_cross_test", exist_ok=True)
        
        result = generate_segment_audios(
            script_data=test_script,
            voice="rachel",
            output_dir="simple_cross_test", 
            use_different_voices=True
        )
        
        if result.get('success'):
            print("SUCCESS: Cross-gender voice assignment working!")
            audio_files = result.get('audio_files', [])
            if audio_files:
                print(f"Generated audio files: {len(audio_files)}")
                # Check what files were created
                import glob
                files = glob.glob("simple_cross_test/*.mp3")
                for f in files:
                    size = os.path.getsize(f) / 1024
                    print(f"  - {os.path.basename(f)} ({size:.1f} KB)")
        else:
            print(f"FAILED: {result.get('error')}")
    
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()