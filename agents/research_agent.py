"""
Research Agent - Main orchestrator for web research
Coordinates multiple content sources and synthesizes information
"""

import asyncio
import concurrent.futures
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json
import os
from dataclasses import asdict

# Import from agents directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from base_scraper import ScrapedContent
from smart_scrapers import (
    GoogleSearchScraper,
    BingSearchScraper,
    DirectNewsScraper,
    WikipediaAPIScraper,
    DuckDuckGoScraper
)
from content_sources import (
    RedditScraper, 
    HackerNewsScraper
)
from fallback_scrapers import (
    NewsAPIFallback,
    OpenNewsAPI,
    SimpleWebScraper,
    LocalNewsAPI
)

class ResearchAgent:
    """
    Main research agent that coordinates multiple scrapers and synthesizes information
    """
    
    def __init__(self, 
                 newsapi_key: Optional[str] = None,
                 max_workers: int = 4,
                 cache_duration_hours: int = 2):
        """
        Initialize the research agent
        
        Args:
            newsapi_key: Optional NewsAPI.org API key
            max_workers: Number of concurrent scraping threads
            cache_duration_hours: How long to cache results
        """
        self.max_workers = max_workers
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache = {}
        
        # Initialize smart scrapers with fallbacks
        self.scrapers = {
            'wikipedia': WikipediaAPIScraper(),
            'local_news': LocalNewsAPI(),
            'simple_web': SimpleWebScraper(),
            'newsapi_free': NewsAPIFallback(),
            'open_news': OpenNewsAPI(),
            'google_search': GoogleSearchScraper(),
            'bing_search': BingSearchScraper(),
            'direct_news': DirectNewsScraper(),
            'duckduckgo': DuckDuckGoScraper(),
            'reddit': RedditScraper(),
            'hackernews': HackerNewsScraper()
        }
        
        print(f"[RESEARCH AGENT] Initialized with {len(self.scrapers)} scrapers")
    
    def _get_cache_key(self, query: str, max_results: int) -> str:
        """Generate cache key for query"""
        return f"{query.lower().strip()}_{max_results}"
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if 'timestamp' not in cache_entry:
            return False
        
        cached_time = datetime.fromisoformat(cache_entry['timestamp'])
        return datetime.now() - cached_time < self.cache_duration
    
    def _save_cache(self, results: List[ScrapedContent], cache_key: str):
        """Save results to cache"""
        cache_entry = {
            'timestamp': datetime.now().isoformat(),
            'results': [asdict(content) for content in results],
            'query': cache_key
        }
        self.cache[cache_key] = cache_entry
    
    def _load_from_cache(self, cache_key: str) -> Optional[List[ScrapedContent]]:
        """Load results from cache if valid"""
        if cache_key not in self.cache:
            return None
        
        cache_entry = self.cache[cache_key]
        if not self._is_cache_valid(cache_entry):
            del self.cache[cache_key]
            return None
        
        # Convert back to ScrapedContent objects
        results = []
        for item in cache_entry['results']:
            # Handle datetime conversion
            if item['published_date']:
                item['published_date'] = datetime.fromisoformat(item['published_date'])
            
            content = ScrapedContent(**item)
            results.append(content)
        
        return results
    
    def scrape_parallel(self, query: str, max_results: int = 20) -> List[ScrapedContent]:
        """
        Scrape content from multiple sources in parallel
        """
        # Check cache first
        cache_key = self._get_cache_key(query, max_results)
        cached_results = self._load_from_cache(cache_key)
        if cached_results:
            print(f"[RESEARCH AGENT] Using cached results for: {query}")
            return cached_results
        
        print(f"[RESEARCH AGENT] Starting parallel scraping for: {query}")
        start_time = datetime.now()
        
        all_contents = []
        results_per_scraper = max(2, max_results // len(self.scrapers))
        
        # Use ThreadPoolExecutor for parallel scraping
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Submit scraping tasks
            future_to_scraper = {
                executor.submit(scraper.scrape, query, results_per_scraper): name 
                for name, scraper in self.scrapers.items()
            }
            
            # Collect results as they complete
            for future in concurrent.futures.as_completed(future_to_scraper, timeout=60):
                scraper_name = future_to_scraper[future]
                
                try:
                    contents = future.result(timeout=30)
                    if contents:
                        all_contents.extend(contents)
                        print(f"[{scraper_name.upper()}] Retrieved {len(contents)} items")
                    else:
                        print(f"[{scraper_name.upper()}] No results found")
                        
                except concurrent.futures.TimeoutError:
                    print(f"[{scraper_name.upper()}] Timed out")
                except Exception as e:
                    print(f"[{scraper_name.upper()}] Error: {e}")
        
        # Combine and deduplicate results
        final_results = self._combine_and_rank_results(all_contents, query, max_results)
        
        # Cache results
        self._save_cache(final_results, cache_key)
        
        duration = datetime.now() - start_time
        print(f"[RESEARCH AGENT] Completed in {duration.total_seconds():.1f}s - {len(final_results)} final results")
        
        return final_results
    
    def _combine_and_rank_results(self, 
                                contents: List[ScrapedContent], 
                                query: str, 
                                max_results: int) -> List[ScrapedContent]:
        """
        Combine results from all scrapers, remove duplicates, and rank by relevance
        """
        if not contents:
            return []
        
        print(f"[RESEARCH AGENT] Processing {len(contents)} total items")
        
        # Remove duplicates based on title similarity
        unique_contents = self._advanced_deduplication(contents)
        print(f"[RESEARCH AGENT] After deduplication: {len(unique_contents)} items")
        
        # Enhanced relevance scoring
        query_terms = self._extract_key_terms(query)
        for content in unique_contents:
            content.relevance_score = self._calculate_enhanced_relevance(content, query_terms, query)
        
        # Sort by relevance score and recency
        unique_contents.sort(key=lambda x: (
            x.relevance_score,
            (x.published_date or datetime.min).timestamp() / 1000000  # Normalize timestamp
        ), reverse=True)
        
        # Return top results
        return unique_contents[:max_results]
    
    def _advanced_deduplication(self, contents: List[ScrapedContent]) -> List[ScrapedContent]:
        """
        Advanced deduplication using multiple similarity metrics
        """
        if len(contents) <= 1:
            return contents
        
        unique_contents = []
        seen_urls = set()
        
        for content in contents:
            # Skip if we've seen this exact URL
            if content.url in seen_urls:
                continue
            
            # Check title similarity with existing content
            is_duplicate = False
            for existing in unique_contents:
                similarity = self._calculate_title_similarity(content.title, existing.title)
                if similarity > 0.85:  # High similarity threshold
                    # Keep the one with higher relevance score
                    if content.relevance_score > existing.relevance_score:
                        unique_contents.remove(existing)
                        unique_contents.append(content)
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_contents.append(content)
                seen_urls.add(content.url)
        
        return unique_contents
    
    def _calculate_title_similarity(self, title1: str, title2: str) -> float:
        """
        Calculate similarity between two titles using word overlap
        """
        def normalize_title(title):
            # Remove common words and normalize
            stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'}
            words = set(word.lower().strip('.,!?";:') for word in title.split() if len(word) > 2 and word.lower() not in stop_words)
            return words
        
        words1 = normalize_title(title1)
        words2 = normalize_title(title2)
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def _extract_key_terms(self, query: str) -> List[str]:
        """
        Extract key terms from query for relevance scoring
        """
        # Simple key term extraction (could be enhanced with NLP)
        stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        words = [word.lower().strip('.,!?";:') for word in query.split() if len(word) > 2 and word.lower() not in stop_words]
        return list(set(words))
    
    def _calculate_enhanced_relevance(self, 
                                    content: ScrapedContent, 
                                    query_terms: List[str], 
                                    original_query: str) -> float:
        """
        Calculate enhanced relevance score considering multiple factors
        """
        score = 0.0
        
        # Text to analyze
        title_lower = content.title.lower()
        summary_lower = (content.summary or '').lower()
        
        # Term matching score (weighted)
        for term in query_terms:
            term_lower = term.lower()
            
            # Title matches (highest weight)
            if term_lower in title_lower:
                score += 3.0
            
            # Summary matches (medium weight)
            if term_lower in summary_lower:
                score += 1.5
        
        # Exact phrase matching bonus
        if original_query.lower() in title_lower:
            score += 5.0
        elif original_query.lower() in summary_lower:
            score += 2.0
        
        # Source credibility bonus (dynamic assessment)
        if self._is_credible_source(content.source):
            score += 1.0
        
        # Recency bonus (last 24 hours get bonus)
        if content.published_date:
            hours_old = (datetime.now() - content.published_date).total_seconds() / 3600
            if hours_old < 24:
                score += 2.0
            elif hours_old < 72:  # Last 3 days
                score += 1.0
        
        # Content type bonus
        if content.content_type == 'news_article':
            score += 0.5
        
        # Normalize score
        max_possible_score = len(query_terms) * 3.0 + 8.0  # Approximate max
        return min(score / max_possible_score, 1.0) if max_possible_score > 0 else 0.0
    
    def _is_credible_source(self, source: str) -> bool:
        """
        Assess source credibility using multiple indicators
        """
        if not source:
            return False
        
        source_lower = source.lower().strip()
        
        # Basic credibility indicators
        credibility_signals = 0
        
        # Well-known news organizations (basic set)
        if any(org in source_lower for org in ['bbc', 'reuters', 'associated press', 'npr']):
            credibility_signals += 2
        
        # Tech/business publications  
        if any(pub in source_lower for pub in ['techcrunch', 'wired', 'bloomberg', 'wall street']):
            credibility_signals += 1
        
        # Academic or research sources
        if any(indicator in source_lower for indicator in ['.edu', 'university', 'journal', 'research']):
            credibility_signals += 1
        
        # Government sources
        if any(gov in source_lower for gov in ['.gov', 'government', 'official']):
            credibility_signals += 1
        
        # Red flags for low credibility
        if any(flag in source_lower for flag in ['blog', 'random', 'anonymous', 'unknown']):
            credibility_signals -= 1
        
        return credibility_signals >= 1
    
    def generate_research_summary(self, contents: List[ScrapedContent], query: str) -> Dict[str, Any]:
        """
        Generate a structured summary of research findings
        """
        if not contents:
            return {
                'query': query,
                'total_items': 0,
                'summary': 'No relevant content found for this query.',
                'key_headlines': [],
                'sources': [],
                'research_timestamp': datetime.now().isoformat()
            }
        
        # Extract key information
        key_headlines = [content.title for content in contents[:5]]
        sources = list(set(content.source for content in contents))
        
        # Generate summary
        summary_points = []
        for i, content in enumerate(contents[:3], 1):
            date_str = content.published_date.strftime('%Y-%m-%d') if content.published_date else 'Recent'
            summary_points.append(f"{i}. {content.title} ({content.source}, {date_str})")
        
        summary = f"Found {len(contents)} relevant items about '{query}'. " + \
                 f"Top findings:\\n" + "\\n".join(summary_points)
        
        return {
            'query': query,
            'total_items': len(contents),
            'summary': summary,
            'key_headlines': key_headlines,
            'sources': sources,
            'items': [asdict(content) for content in contents],
            'research_timestamp': datetime.now().isoformat(),
            'coverage_score': min(len(contents) / 10.0, 1.0),  # How well we covered the topic
            'source_diversity': len(sources) / len(self.scrapers)  # How many different sources
        }
    
    def research_topic(self, query: str, max_results: int = 15) -> Dict[str, Any]:
        """
        Main method to research a topic and return comprehensive results
        
        Args:
            query: Topic to research
            max_results: Maximum number of results to return
            
        Returns:
            Dictionary with research results and metadata
        """
        print(f"[RESEARCH AGENT] Starting research for: '{query}'")
        
        try:
            # Scrape content from multiple sources
            contents = self.scrape_parallel(query, max_results)
            
            # Generate comprehensive summary
            research_summary = self.generate_research_summary(contents, query)
            
            print(f"[RESEARCH AGENT] Research completed - {research_summary['total_items']} items from {len(research_summary['sources'])} sources")
            
            return research_summary
            
        except Exception as e:
            print(f"[RESEARCH AGENT] Error during research: {e}")
            return {
                'query': query,
                'total_items': 0,
                'summary': f'Research failed due to error: {str(e)}',
                'key_headlines': [],
                'sources': [],
                'items': [],
                'error': str(e),
                'research_timestamp': datetime.now().isoformat()
            }
    
    def save_research_results(self, research_results: Dict[str, Any], output_dir: str = "research_cache"):
        """
        Save research results to file for later use
        """
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Create filename based on query and timestamp
            query_clean = "".join(c for c in research_results['query'] if c.isalnum() or c in (' ', '-', '_')).rstrip()
            query_clean = query_clean.replace(' ', '_')[:50]
            
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{query_clean}_{timestamp}.json"
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(research_results, f, indent=2, ensure_ascii=False, default=str)
            
            print(f"[RESEARCH AGENT] Results saved to: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"[RESEARCH AGENT] Error saving results: {e}")
            return None