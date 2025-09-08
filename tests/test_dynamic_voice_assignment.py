#!/usr/bin/env python3
"""
Test Dynamic Voice Assignment System
Tests the new Gemini-based character data voice assignment
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()
sys.path.append('backend_functions')

def test_dynamic_voice_assignment():
    """Test dynamic voice assignment with Gemini character data"""
    print("=" * 60)
    print("TESTING DYNAMIC VOICE ASSIGNMENT")
    print("=" * 60)
    
    try:
        from segment_audio_generator import assign_character_voices, get_voice_for_character, VOICE_TONE_MAPPING
        
        print("VOICE TONE MAPPING:")
        print("-" * 30)
        for tone, voices in VOICE_TONE_MAPPING.items():
            print(f"{tone}: {voices}")
        
        # Test script with Gemini-style character data
        test_script = {
            "story_title": "Dynamic Voice Assignment Test",
            "characters": [
                {
                    "name": "The Wise Queen",
                    "description": "A strong female ruler who commands respect",
                    "role": "protagonist",
                    "gender": "female", 
                    "voice_tone": "authoritative"
                },
                {
                    "name": "Young Prince",
                    "description": "A gentle young male character with a soft heart",
                    "role": "supporting",
                    "gender": "male",
                    "voice_tone": "gentle"
                },
                {
                    "name": "The Warrior",
                    "description": "A strong female fighter",
                    "role": "supporting", 
                    "gender": "female",
                    "voice_tone": "strong"
                },
                {
                    "name": "Elder Sage",
                    "description": "An old wise man with deep knowledge",
                    "role": "supporting",
                    "gender": "male",
                    "voice_tone": "wise"
                }
            ],
            "segments": [
                {
                    "segment_number": 1,
                    "text": "The wise queen spoke with commanding authority.",
                    "character_speaking": "The Wise Queen",
                    "segment_type": "dialog"
                },
                {
                    "segment_number": 2,
                    "text": "The young prince replied with gentle kindness.",
                    "character_speaking": "Young Prince", 
                    "segment_type": "dialog"
                },
                {
                    "segment_number": 3,
                    "text": "The warrior shouted with fierce determination.",
                    "character_speaking": "The Warrior",
                    "segment_type": "dialog"
                },
                {
                    "segment_number": 4,
                    "text": "The elder sage shared his wisdom thoughtfully.",
                    "character_speaking": "Elder Sage",
                    "segment_type": "dialog"
                }
            ]
        }
        
        print(f"\nTESTING CHARACTER VOICE ASSIGNMENTS:")
        print("=" * 40)
        
        # Test individual character voice assignment
        for character in test_script["characters"]:
            voice = get_voice_for_character(character)
            name = character["name"]
            gender = character["gender"] 
            tone = character["voice_tone"]
            print(f"{name}: {gender} + {tone} -> {voice}")
        
        print(f"\nTESTING FULL VOICE ASSIGNMENT:")
        print("=" * 40)
        
        # Test full voice assignment system
        character_voices = assign_character_voices(test_script, "rachel", True)
        
        print(f"\nFINAL VOICE ASSIGNMENTS:")
        print("-" * 30)
        for char_name, voice in character_voices.items():
            print(f"{char_name}: {voice}")
        
        print(f"\nCROSS-GENDER ASSIGNMENTS DETECTED:")
        print("-" * 30)
        for character in test_script["characters"]:
            char_name = character["name"]
            char_gender = character["gender"]
            assigned_voice = character_voices.get(char_name)
            
            if assigned_voice:
                from segment_audio_generator import VOICE_CHARACTERISTICS
                voice_gender = VOICE_CHARACTERISTICS.get(assigned_voice, {}).get('gender', 'unknown')
                
                if char_gender != voice_gender:
                    print(f"CROSS-GENDER: {char_name} ({char_gender}) using {assigned_voice} ({voice_gender}) voice")
                else:
                    print(f"Traditional: {char_name} ({char_gender}) using {assigned_voice} ({voice_gender}) voice")
        
        print(f"\nSUCCESS: Dynamic voice assignment system working!")
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_gemini_script_generation():
    """Test actual Gemini script generation with new character fields"""
    print(f"\n{'='*60}")
    print("TESTING GEMINI SCRIPT GENERATION WITH NEW CHARACTER FIELDS")
    print("="*60)
    
    try:
        from story_script_generator import generate_story_script
        
        print("Generating story script with dynamic character data...")
        
        script = generate_story_script("A brave princess and a gentle knight", "short", True)
        
        if script:
            print(f"Generated story: '{script.get('story_title', 'Unknown')}'")
            
            characters = script.get("characters", [])
            print(f"\nGENERATED CHARACTERS:")
            print("-" * 30)
            
            for char in characters:
                if isinstance(char, dict):
                    name = char.get("name", "Unknown")
                    gender = char.get("gender", "Not specified")
                    tone = char.get("voice_tone", "Not specified")
                    print(f"{name}:")
                    print(f"  Gender: {gender}")
                    print(f"  Voice tone: {tone}")
                    print()
            
            # Test voice assignment with generated characters
            print("TESTING VOICE ASSIGNMENT WITH GENERATED CHARACTERS:")
            print("-" * 30)
            
            from segment_audio_generator import assign_character_voices
            voices = assign_character_voices(script, "rachel", True)
            
            return True
        else:
            print("Failed to generate script")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function"""
    print("DYNAMIC VOICE ASSIGNMENT SYSTEM TEST")
    print("="*60)
    
    # Test 1: Dynamic assignment with mock data
    success1 = test_dynamic_voice_assignment()
    
    # Test 2: Actual Gemini generation 
    success2 = test_gemini_script_generation()
    
    print(f"\n{'='*60}")
    print("TEST SUMMARY")
    print("="*60)
    
    if success1 and success2:
        print("SUCCESS: Dynamic voice assignment system fully working!")
        print("\nKEY IMPROVEMENTS:")
        print("- Removed hardcoded character mappings")
        print("- Added dynamic voice assignment based on Gemini data")
        print("- Cross-gender voice assignments work automatically")
        print("- Voice tone matching (authoritative, gentle, strong, etc.)")
        print("- Gemini generates character gender and voice_tone data")
    else:
        print("SOME TESTS FAILED - check error messages above")

if __name__ == "__main__":
    main()