#!/usr/bin/env python3
"""
Test script for the Research Agent web scraping functionality
"""

import os
import sys
import json
from datetime import datetime

# Add agents to Python path and fix imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

def test_individual_scrapers():
    """Test each scraper individually"""
    print("=" * 60)
    print("TESTING INDIVIDUAL SCRAPERS")
    print("=" * 60)
    
    from smart_scrapers import GoogleSearchScraper, BingSearchScraper, WikipediaAPIScraper, DuckDuckGoScraper
    from content_sources import RedditScraper, HackerNewsScraper
    
    test_query = "artificial intelligence"
    scrapers_to_test = [
        ("Google Search", GoogleSearchScraper()),
        ("Bing Search", BingSearchScraper()),
        ("Wikipedia", WikipediaAPIScraper()),
        ("DuckDuckGo", DuckDuckGoScraper()),
        ("Reddit", RedditScraper()),
        ("Hacker News", HackerNewsScraper())
    ]
    
    results = {}
    
    for scraper_name, scraper in scrapers_to_test:
        print(f"\\n[TESTING] {scraper_name}")
        print("-" * 40)
        
        try:
            contents = scraper.scrape(test_query, max_results=5)
            
            if contents:
                print(f"[SUCCESS] Retrieved {len(contents)} items")
                
                # Show first result
                first_result = contents[0]
                print(f"   Sample: {first_result.title[:60]}...")
                print(f"   Source: {first_result.source}")
                print(f"   URL: {first_result.url[:60]}...")
                if first_result.published_date:
                    print(f"   Date: {first_result.published_date.strftime('%Y-%m-%d %H:%M')}")
                print(f"   Relevance: {first_result.relevance_score:.2f}")
                
                results[scraper_name] = {
                    'success': True,
                    'count': len(contents),
                    'sample_title': first_result.title
                }
            else:
                print(f"[WARNING] No results found")
                results[scraper_name] = {
                    'success': False,
                    'count': 0,
                    'error': 'No results'
                }
                
        except Exception as e:
            print(f"[ERROR] {scraper_name} failed: {e}")
            results[scraper_name] = {
                'success': False,
                'count': 0,
                'error': str(e)
            }
    
    return results

def test_research_agent():
    """Test the main Research Agent"""
    print("\\n" + "=" * 60)
    print("TESTING RESEARCH AGENT")
    print("=" * 60)
    
    from research_agent import ResearchAgent
    
    try:
        # Initialize research agent
        print("[INIT] Creating Research Agent...")
        agent = ResearchAgent(max_workers=2)  # Reduce workers for testing
        
        # Test research
        test_queries = [
            "latest AI developments",
        ]
        
        for query in test_queries:
            print(f"\\n[RESEARCH] Testing query: '{query}'")
            print("-" * 50)
            
            try:
                results = agent.research_topic(query, max_results=8)
                
                print(f"[RESULTS] Query: {results['query']}")
                print(f"   Total items: {results['total_items']}")
                print(f"   Sources: {len(results['sources'])}")
                print(f"   Coverage score: {results.get('coverage_score', 0):.2f}")
                
                if results['key_headlines']:
                    print("   Top headlines:")
                    for i, headline in enumerate(results['key_headlines'][:3], 1):
                        print(f"      {i}. {headline[:70]}...")
                
                # Save results for inspection
                timestamp = datetime.now().strftime('%H%M%S')
                filename = f"test_research_{query.replace(' ', '_')}_{timestamp}.json"
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(results, f, indent=2, ensure_ascii=False, default=str)
                
                print(f"   Detailed results saved to: {filename}")
                
                return True
                
            except Exception as e:
                print(f"[ERROR] Research failed for '{query}': {e}")
                return False
                
    except Exception as e:
        print(f"[ERROR] Research Agent initialization failed: {e}")
        return False

def test_performance():
    """Test performance metrics"""
    print("\\n" + "=" * 60)
    print("TESTING PERFORMANCE")
    print("=" * 60)
    
    from research_agent import ResearchAgent
    import time
    
    try:
        agent = ResearchAgent(max_workers=3)
        
        start_time = time.time()
        results = agent.research_topic("latest AI developments", max_results=10)
        end_time = time.time()
        
        duration = end_time - start_time
        
        print(f"[PERFORMANCE] Research completed in {duration:.2f} seconds")
        print(f"   Items found: {results['total_items']}")
        print(f"   Items per second: {results['total_items'] / duration:.2f}")
        print(f"   Sources queried: {len(results['sources'])}")
        
        if duration < 30:  # Should complete within 30 seconds
            print("[SUCCESS] Performance test passed")
            return True
        else:
            print("[WARNING] Performance slower than expected")
            return False
            
    except Exception as e:
        print(f"[ERROR] Performance test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("Research Agent Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test individual scraper
    # scraper_results = test_individual_scrapers()
    
    # Test research agent
    research_success = test_research_agent()
    
    # # Test performance
    # performance_success = test_performance()
    
    # Summary
    print("\\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    # print("Individual Scrapers:")
    # for scraper_name, result in scraper_results.items():
    #     status = "PASS" if result['success'] else "FAIL"
    #     count = result['count']
    #     print(f"   {scraper_name:<15} | {status:<4} | {count} items")
    
    print(f"\\nResearch Agent:       {'PASS' if research_success else 'FAIL'}")
    # print(f"Performance Test:     {'PASS' if performance_success else 'FAIL'}")
    
    # Calculate overall success
    # scraper_successes = sum(1 for r in scraper_results.values() if r['success'])
    # total_scrapers = len(scraper_results)
    
    # overall_success = (
    #     scraper_successes >= total_scrapers // 2 and  # At least half scrapers working
    #     research_success and 
    #     performance_success
    # )
    
    # print(f"\\nOVERALL RESULT: {'SUCCESS' if overall_success else 'NEEDS ATTENTION'}")
    
    # if not overall_success:
    #     print("\\nSome tests failed. This might be due to:")
    #     print("- Network connectivity issues")
    #     print("- Website changes or blocking")
    #     print("- Missing dependencies")
    #     print("- Rate limiting")
    #     print("\\nCheck individual test outputs above for details.")
    
    # return 0 if overall_success else 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)