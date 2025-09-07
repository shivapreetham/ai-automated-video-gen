#!/usr/bin/env python3
"""
Test script for Daily News Uploader
"""

import sys
import os
from datetime import datetime

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from daily_news_uploader import DailyNewsUploader, ABPLiveNewsScraper
from content_generator_integration import ContentGenerator

def test_abp_scraper():
    """Test ABP Live news scraper"""
    print("=" * 60)
    print("TESTING ABP LIVE NEWS SCRAPER")
    print("=" * 60)
    
    scraper = ABPLiveNewsScraper()
    
    # Test fetching news
    print("Fetching trending news from ABP Live...")
    news_items = scraper.fetch_trending_news()
    
    if news_items:
        print(f"SUCCESS: Successfully fetched {len(news_items)} news items")
        
        print("\nTop 5 news items:")
        for i, item in enumerate(news_items[:5], 1):
            print(f"\n{i}. {item['title']}")
            print(f"   Category: {item['category']}")
            print(f"   Published: {item['published']}")
            print(f"   Description: {item['description'][:100]}...")
    else:
        print("FAILED: Failed to fetch news items")
        return False
    
    # Test getting titles for generation
    print(f"\n{'-'*40}")
    print("Testing title selection for content generation...")
    
    titles = scraper.get_trending_titles_for_generation(limit=5)
    
    if titles:
        print(f"SUCCESS: Selected {len(titles)} titles for generation:")
        for i, title in enumerate(titles, 1):
            print(f"  {i}. {title}")
    else:
        print("FAILED: No suitable titles found")
        return False
    
    return True

def test_content_generator():
    """Test content generator integration"""
    print("\n" + "=" * 60)
    print("TESTING CONTENT GENERATOR INTEGRATION")
    print("=" * 60)
    
    generator = ContentGenerator()
    
    # Test with a sample title
    test_title = "Breaking News: Massive Devotee Rush at Temple During Sawan Festival"
    
    print(f"Generating content for: {test_title}")
    
    result = generator.generate_content(test_title, "ABP Live")
    
    if result['status'] == 'success':
        print("SUCCESS: Content generation successful!")
        print(f"  Output file: {result['output_file']}")
        print(f"  Generated at: {result['generated_at']}")
        print(f"  Preview: {result['content_preview'][:100]}...")
        return True
    else:
        print(f"FAILED: Content generation failed: {result.get('error', 'Unknown error')}")
        return False

def test_full_pipeline():
    """Test the complete daily upload pipeline"""
    print("\n" + "=" * 60)
    print("TESTING FULL DAILY UPLOAD PIPELINE")
    print("=" * 60)
    
    uploader = DailyNewsUploader()
    
    try:
        print("Running daily upload process...")
        uploader.run_daily_upload()
        print("SUCCESS: Daily upload process completed successfully!")
        return True
    except Exception as e:
        print(f"FAILED: Daily upload process failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Daily News Uploader Test Suite")
    print(f"Started at: {datetime.now()}")
    
    results = {
        'ABP Scraper': test_abp_scraper(),
        'Content Generator': test_content_generator(),
        'Full Pipeline': test_full_pipeline()
    }
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    for test_name, result in results.items():
        status = "PASS" if result else "FAIL"
        print(f"{test_name:<20} | {status}")
    
    all_passed = all(results.values())
    print(f"\nOverall Result: {'SUCCESS' if all_passed else 'SOME TESTS FAILED'}")
    
    if all_passed:
        print("\nAll tests passed! The daily news uploader is ready to use.")
        print("\nNext steps:")
        print("1. Customize the content generation integration in content_generator_integration.py")
        print("2. Update the generation script path in daily_news_uploader.py")
        print("3. Run 'python daily_news_uploader.py' to start the scheduler")
        print("4. Or run 'python daily_news_uploader.py --run-once' for a single run")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())