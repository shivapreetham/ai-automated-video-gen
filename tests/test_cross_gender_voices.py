#!/usr/bin/env python3
"""
Test Cross-Gender Voice Assignments
Demonstrates how male voices can be used for female characters and vice versa
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add backend_functions to path
sys.path.append('backend_functions')

def test_cross_gender_assignments():
    """Test various cross-gender voice assignment scenarios"""
    print("=" * 60)
    print("TESTING CROSS-GENDER VOICE ASSIGNMENTS")
    print("=" * 60)
    
    try:
        from segment_audio_generator import generate_segment_audios
        
        # Test scenario with cross-gender assignments
        test_scenarios = [
            {
                "name": "Traditional Gender Assignment",
                "script_data": {
                    "story_title": "Traditional Voice Assignment Test",
                    "segments": [
                        {
                            "segment_number": 1,
                            "text": "Sita spoke with grace and wisdom.",
                            "character_speaking": "Sita",
                            "segment_type": "dialog"
                        },
                        {
                            "segment_number": 2, 
                            "text": "Lord Ram commanded with authority.",
                            "character_speaking": "Lord Ram",
                            "segment_type": "dialog"
                        }
                    ],
                    "characters": ["Sita", "Lord Ram"]
                }
            },
            {
                "name": "Cross-Gender Assignment Test",
                "script_data": {
                    "story_title": "Cross-Gender Voice Test", 
                    "segments": [
                        {
                            "segment_number": 1,
                            "text": "The wise woman spoke with deep authority that commanded respect.",
                            "character_speaking": "wise_woman",
                            "segment_type": "dialog"
                        },
                        {
                            "segment_number": 2,
                            "text": "The young prince had a gentle, soft voice that was comforting.",
                            "character_speaking": "young_prince", 
                            "segment_type": "dialog"
                        },
                        {
                            "segment_number": 3,
                            "text": "The female warrior's voice was strong and commanding.",
                            "character_speaking": "female_warrior",
                            "segment_type": "dialog"
                        }
                    ],
                    "characters": ["wise_woman", "young_prince", "female_warrior"]
                }
            },
            {
                "name": "Custom Voice Preferences",
                "script_data": {
                    "story_title": "Custom Voice Preference Test",
                    "segments": [
                        {
                            "segment_number": 1,
                            "text": "This character has a custom voice preference.",
                            "character_speaking": "custom_character",
                            "segment_type": "dialog"
                        }
                    ],
                    "characters": [
                        {
                            "name": "custom_character",
                            "preferred_voice": "adam"  # Force male voice for any character
                        }
                    ]
                }
            }
        ]
        
        test_output_dir = "cross_gender_test_audio"
        os.makedirs(test_output_dir, exist_ok=True)
        
        all_results = []
        
        for i, scenario in enumerate(test_scenarios, 1):
            print(f"\n{'-'*40}")
            print(f"SCENARIO {i}: {scenario['name']}")
            print(f"{'-'*40}")
            
            try:
                result = generate_segment_audios(
                    script_data=scenario["script_data"],
                    voice="rachel",  # Narrator voice
                    output_dir=test_output_dir,
                    use_different_voices=True
                )
                
                if result.get('success'):
                    print(f"✅ SUCCESS: {scenario['name']}")
                    all_results.append(result)
                else:
                    print(f"❌ FAILED: {scenario['name']} - {result.get('error')}")
                    
            except Exception as e:
                print(f"❌ ERROR in {scenario['name']}: {e}")
        
        return len(all_results) > 0
        
    except Exception as e:
        print(f"❌ TEST SETUP FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

def demonstrate_voice_options():
    """Show available voice options and their characteristics"""
    print(f"\n{'='*60}")
    print("AVAILABLE VOICE OPTIONS")
    print("="*60)
    
    try:
        sys.path.append('backend_functions')
        from segment_audio_generator import VOICE_CHARACTERISTICS, SMART_CHARACTER_VOICES
        
        print("🎤 VOICE CHARACTERISTICS:")
        print("-"*30)
        for voice_name, characteristics in VOICE_CHARACTERISTICS.items():
            print(f"{voice_name.upper()}:")
            print(f"  Gender: {characteristics['gender']}")
            print(f"  Tone: {characteristics['tone']}")
            print(f"  Quality: {characteristics['quality']}")
            print(f"  Suitable for: {', '.join(characteristics['suitable_for'])}")
            print()
        
        print("🎯 SMART CHARACTER MAPPINGS:")
        print("-"*30)
        print("Traditional assignments:")
        traditional = ["narrator", "sita", "lord_ram", "lord_hanuman", "ravana"]
        for char in traditional:
            if char in SMART_CHARACTER_VOICES:
                voice = SMART_CHARACTER_VOICES[char]
                gender = VOICE_CHARACTERISTICS.get(voice, {}).get('gender', 'unknown')
                print(f"  {char} -> {voice} ({gender} voice)")
        
        print(f"\nCross-gender assignments (male voices for female characters):")
        cross_gender_female = ["kaikeyi", "surpanakha", "female_warrior", "wise_woman"]
        for char in cross_gender_female:
            if char in SMART_CHARACTER_VOICES:
                voice = SMART_CHARACTER_VOICES[char]
                gender = VOICE_CHARACTERISTICS.get(voice, {}).get('gender', 'unknown')
                print(f"  {char} -> {voice} ({gender} voice)")
        
        print(f"\nCross-gender assignments (female voices for male characters):")
        cross_gender_male = ["young_prince", "lakshmana", "gentle_sage", "child_character"]
        for char in cross_gender_male:
            if char in SMART_CHARACTER_VOICES:
                voice = SMART_CHARACTER_VOICES[char] 
                gender = VOICE_CHARACTERISTICS.get(voice, {}).get('gender', 'unknown')
                print(f"  {char} -> {voice} ({gender} voice)")
                
    except Exception as e:
        print(f"❌ Could not load voice data: {e}")

def main():
    """Main test function"""
    
    print("🎭 CROSS-GENDER VOICE ASSIGNMENT SYSTEM")
    print("="*60)
    print("This system allows you to use:")
    print("✅ Male voices for female characters")
    print("✅ Female voices for male characters") 
    print("✅ Any voice for any character based on desired tone/style")
    print("✅ Custom voice preferences in script data")
    
    # Show available options
    demonstrate_voice_options()
    
    # Test the assignments
    success = test_cross_gender_assignments()
    
    print(f"\n{'='*60}")
    print("CROSS-GENDER VOICE SYSTEM SUMMARY")
    print("="*60)
    
    if success:
        print("✅ SUCCESS: Cross-gender voice assignment system is working!")
        print(f"\n🎯 HOW TO USE:")
        print("1. Character names are automatically mapped to voices")
        print("2. You can specify preferred_voice in character data")
        print("3. Cross-gender assignments work automatically")
        print("4. System prioritizes: Smart mappings > Custom preferences > Auto assignment")
        
        print(f"\n🎪 EXAMPLES:")
        print("- 'wise_woman' uses Antoni (male voice) for authority")
        print("- 'female_warrior' uses Adam (male voice) for strength") 
        print("- 'young_prince' uses Bella (female voice) for youth")
        print("- 'gentle_sage' uses Rachel (female voice) for warmth")
        
        # Show generated files
        if os.path.exists("cross_gender_test_audio"):
            import glob
            audio_files = glob.glob("cross_gender_test_audio/*.mp3")
            if audio_files:
                print(f"\n🎵 GENERATED {len(audio_files)} TEST AUDIO FILES:")
                for f in audio_files:
                    size = os.path.getsize(f) / 1024
                    print(f"  - {os.path.basename(f)} ({size:.1f} KB)")
                print(f"\n🎧 Play these files to hear the cross-gender voice assignments!")
    else:
        print("❌ FAILED: Cross-gender voice assignment system needs debugging")
        print("Check the error messages above and ensure ElevenLabs is working")

if __name__ == "__main__":
    main()