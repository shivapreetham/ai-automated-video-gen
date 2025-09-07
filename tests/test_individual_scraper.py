#!/usr/bin/env python3
"""
Quick test script to test individual scrapers
"""

import sys
import os

# Add agents to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'agents'))

from smart_scrapers import GoogleSearchScraper, BingSearchScraper, WikipediaAPIScraper, DuckDuckGoScraper
from content_sources import RedditScraper

def test_scraper(scraper_name, scraper, query="Mango in india"):
    """Test a single scraper"""
    print(f"\n{'='*50}")
    print(f"TESTING {scraper_name.upper()}")
    print(f"{'='*50}")
    print(f"Query: {query}")
    
    try:
        results = scraper.scrape(query, max_results=3)
        
        if results:
            print(f"\n✓ Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                print(f"\n{i}. {result.title}")
                print(f"   URL: {result.url}")
                print(f"   Source: {result.source}")
                print(f"   Relevance: {result.relevance_score:.2f}")
                if result.summary:
                    print(f"   Summary: {result.summary[:100]}...")
        else:
            print("✗ No results found")
            
    except Exception as e:
        print(f"✗ Error: {e}")

def main():
    """Test various scrapers"""
    query = input("Enter search query (default: 'Mango in india'): ").strip()
    if not query:
        query = "Mango in india"
    
    scrapers = [
        ("Wikipedia", WikipediaAPIScraper()),
        ("Google Search", GoogleSearchScraper()),
        ("DuckDuckGo", DuckDuckGoScraper()),
        ("Bing Search", BingSearchScraper()),
        ("Reddit", RedditScraper()),
    ]
    
    print(f"Testing scrapers with query: '{query}'")
    
    for name, scraper in scrapers:
        test_scraper(name, scraper, query)
        print("\nPress Enter to continue to next scraper...")
        input()

if __name__ == "__main__":
    main()