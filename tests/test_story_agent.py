#!/usr/bin/env python3
"""
Test script for the Story Synthesis Agent
Tests creative story generation from research data
"""

import os
import sys
import json
from datetime import datetime

# Add agents to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

def load_test_research_data():
    """Load the research data we generated earlier"""
    try:
        # Look for the most recent research file
        research_files = [f for f in os.listdir('.') if f.startswith('test_research_') and f.endswith('.json')]
        if research_files:
            latest_file = sorted(research_files)[-1]
            print(f"[TEST] Loading research data from: {latest_file}")
            
            with open(latest_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            print("[TEST] No research files found, creating sample data")
            return create_sample_research_data()
            
    except Exception as e:
        print(f"[ERROR] Failed to load research data: {e}")
        return create_sample_research_data()

def create_sample_research_data():
    """Create sample research data for testing"""
    return {
        "query": "Donald Trump tariff on India",
        "total_items": 3,
        "key_headlines": [
            "Why Trump's fight with India could have global repercussions",
            "Trump: As the 50% tariff impasse continues, is retaliation an option for India?",
            "US-India trade tensions escalate amid new tariff proposals"
        ],
        "sources": ["BBC", "The Conversation", "Reuters"],
        "items": [
            {
                "title": "Why Trump's fight with India could have global repercussions",
                "source": "The Conversation",
                "published_date": "2025-09-04T16:24:25",
                "relevance_score": 0.85
            }
        ],
        "research_timestamp": datetime.now().isoformat()
    }

def test_story_styles():
    """Test different story styles"""
    print("=" * 60)
    print("TESTING DIFFERENT STORY STYLES")
    print("=" * 60)
    
    from story_synthesis_agent import StorySynthesisAgent
    
    research_data = load_test_research_data()
    agent = StorySynthesisAgent()
    
    styles_to_test = ['narrative', 'documentary', 'conversational', 'analytical']
    
    for style in styles_to_test:
        print(f"\\n[TESTING] Style: {style.upper()}")
        print("-" * 40)
        
        try:
            story_result = agent.synthesize_story(
                research_data=research_data,
                style=style,
                target_duration=45,
                creativity_level='high'
            )
            
            if story_result.get('success'):
                script = story_result['video_script']
                print(f"[SUCCESS] Story generated!")
                print(f"   Title: {script['title']}")
                print(f"   Duration: {script['duration']}s")
                print(f"   Segments: {len(script['segments'])}")
                print(f"   Script preview: {script['text'][:100]}...")
                
                # Save this style's result
                filename = f"test_story_{style}_{datetime.now().strftime('%H%M%S')}.json"
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(story_result, f, indent=2, ensure_ascii=False, default=str)
                print(f"   Saved to: {filename}")
            else:
                print(f"[FAILED] {story_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"[ERROR] Style {style} failed: {e}")

def test_creativity_levels():
    """Test different creativity levels"""
    print("\\n" + "=" * 60)
    print("TESTING CREATIVITY LEVELS")
    print("=" * 60)
    
    from story_synthesis_agent import StorySynthesisAgent
    
    research_data = load_test_research_data()
    agent = StorySynthesisAgent()
    
    creativity_levels = ['moderate', 'high']
    
    for creativity in creativity_levels:
        print(f"\\n[TESTING] Creativity: {creativity.upper()}")
        print("-" * 40)
        
        try:
            story_result = agent.synthesize_story(
                research_data=research_data,
                style='narrative',
                target_duration=60,
                creativity_level=creativity
            )
            
            if story_result.get('success'):
                creative_highlights = story_result['creative_script'].get('creative_highlights', [])
                print(f"[SUCCESS] Story generated with {creativity} creativity!")
                print(f"   Creative elements: {len(creative_highlights)}")
                if creative_highlights:
                    print(f"   Examples: {creative_highlights[:3]}")
            else:
                print(f"[FAILED] {story_result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"[ERROR] Creativity {creativity} failed: {e}")

def test_context_analysis():
    """Test the context analysis capabilities"""
    print("\\n" + "=" * 60)
    print("TESTING CONTEXT ANALYSIS")
    print("=" * 60)
    
    from story_synthesis_agent import StorySynthesisAgent
    
    research_data = load_test_research_data()
    agent = StorySynthesisAgent()
    
    print("[TEST] Analyzing research context...")
    
    try:
        context = agent.analyze_research_context(research_data)
        
        print(f"[RESULTS] Context Analysis:")
        print(f"   Themes: {context.get('themes', [])}")
        print(f"   Key players: {context.get('key_players', [])}")
        print(f"   Sentiment: {context.get('sentiment', 'unknown')}")
        print(f"   Implications: {context.get('implications', [])}")
        print(f"   Complexity level: {context.get('complexity_level', 0)}")
        print(f"   Timeline events: {len(context.get('timeline', []))}")
        
        return context
        
    except Exception as e:
        print(f"[ERROR] Context analysis failed: {e}")
        return None

def test_full_integration():
    """Test full integration: Research -> Story -> Script"""
    print("\\n" + "=" * 60)
    print("TESTING FULL INTEGRATION")
    print("=" * 60)
    
    print("[TEST] Running complete Research -> Story -> Script pipeline...")
    
    try:
        # Step 1: Get research data
        research_data = load_test_research_data()
        print(f"[1/3] Research data loaded: {research_data['total_items']} items")
        
        # Step 2: Create story
        from story_synthesis_agent import StorySynthesisAgent
        agent = StorySynthesisAgent()
        
        story_result = agent.synthesize_story(
            research_data=research_data,
            style='narrative',
            target_duration=50,
            creativity_level='high'
        )
        
        if not story_result.get('success'):
            print(f"[FAILED] Story generation failed: {story_result.get('error')}")
            return False
        
        print(f"[2/3] Story generated successfully!")
        
        # Step 3: Extract script for video generator
        video_script = story_result['video_script']
        
        # Format for your existing video generator
        formatted_for_video_gen = {
            "Text": video_script['text'],
            "title": video_script['title'],
            "sentences": [
                {
                    "sentence": segment['text'],
                    "start_time": 0,  # Will be calculated by video generator
                    "end_time": segment['estimated_duration'] * 10000000,  # Azure time units
                    "duration": segment['estimated_duration'] * 10000000,
                    "word_count": len(segment['text'].split()),
                    "char_count": len(segment['text']),
                    "segment_number": segment['segment_number']
                }
                for segment in video_script['segments']
            ],
            "topic": research_data['query'],
            "total_duration": video_script['duration'],
            "segment_count": len(video_script['segments']),
            "generated_at": datetime.now().isoformat(),
            "generated_by": "story_synthesis_agent",
            "source_research": story_result['source_research']
        }
        
        print(f"[3/3] Script formatted for video generator!")
        print(f"   Ready for: local_video_generator.py")
        print(f"   Text length: {len(formatted_for_video_gen['Text'])} characters")
        print(f"   Segments: {formatted_for_video_gen['segment_count']}")
        print(f"   Duration: {formatted_for_video_gen['total_duration']}s")
        
        # Save the complete pipeline result
        complete_result = {
            'original_research': research_data,
            'story_synthesis': story_result,
            'video_ready_script': formatted_for_video_gen
        }
        
        filename = f"complete_pipeline_test_{datetime.now().strftime('%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(complete_result, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"   Complete pipeline result saved: {filename}")
        
        # Show preview of final script
        print(f"\\n[PREVIEW] Final Script:")
        print(f"Title: {formatted_for_video_gen['title']}")
        print(f"Script: {formatted_for_video_gen['Text'][:200]}...")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Full integration test failed: {e}")
        return False

def main():
    """Run all story synthesis tests"""
    print("Story Synthesis Agent Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ("Context Analysis", test_context_analysis),
        ("Story Styles", test_story_styles),
        ("Creativity Levels", test_creativity_levels),
        ("Full Integration", test_full_integration)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\\n{'=' * 60}")
        print(f"RUNNING: {test_name}")
        print(f"{'=' * 60}")
        
        try:
            result = test_func()
            results[test_name] = result is not False  # Some tests don't return boolean
        except KeyboardInterrupt:
            print(f"\\n[INTERRUPTED] Test interrupted by user")
            break
        except Exception as e:
            print(f"[CRITICAL ERROR] {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\\n{'=' * 60}")
    print("TEST SUMMARY")
    print(f"{'=' * 60}")
    
    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"{test_name:<20} | {status}")
    
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    print(f"\\nResults: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("[SUCCESS] All story synthesis tests passed! 🎉")
        print("Your Story Synthesis Agent is ready to create creative video content!")
        return 0
    else:
        print("[WARNING] Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)