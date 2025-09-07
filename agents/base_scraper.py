"""
Base Web Scraper Class
Provides foundation for all scraping agents with rate limiting, error handling, and content validation
"""

import time
import requests
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import logging
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import hashlib

@dataclass
class ScrapedContent:
    """Structure for scraped content"""
    title: str
    url: str
    source: str
    published_date: Optional[datetime]
    summary: Optional[str] = None
    relevance_score: float = 0.0
    content_type: str = "article"
    tags: List[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'title': self.title,
            'url': self.url,
            'source': self.source,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'summary': self.summary,
            'relevance_score': self.relevance_score,
            'content_type': self.content_type,
            'tags': self.tags
        }

class RateLimiter:
    """Simple rate limiter to be respectful to websites"""
    
    def __init__(self, requests_per_minute: int = 30):
        self.requests_per_minute = requests_per_minute
        self.min_delay = 60.0 / requests_per_minute
        self.last_request_time = 0
        self.request_history = []
    
    def wait_if_needed(self):
        """Wait if we need to respect rate limits"""
        current_time = time.time()
        
        # Clean old requests from history
        cutoff_time = current_time - 60
        self.request_history = [t for t in self.request_history if t > cutoff_time]
        
        # Check if we need to wait
        if len(self.request_history) >= self.requests_per_minute:
            sleep_time = 60 - (current_time - self.request_history[0]) + random.uniform(1, 3)
            if sleep_time > 0:
                print(f"[RATE LIMIT] Waiting {sleep_time:.1f}s to respect rate limits")
                time.sleep(sleep_time)
        
        # Add current request to history
        self.request_history.append(current_time)
        
        # Add random delay to appear more human-like
        random_delay = random.uniform(0.5, 2.0)
        time.sleep(random_delay)

class BaseScraper(ABC):
    """
    Abstract base class for all web scrapers
    Provides common functionality like rate limiting, error handling, and content validation
    """
    
    def __init__(self, 
                 name: str,
                 requests_per_minute: int = 30,
                 timeout: int = 10,
                 max_retries: int = 3):
        self.name = name
        self.rate_limiter = RateLimiter(requests_per_minute)
        self.timeout = timeout
        self.max_retries = max_retries
        self.session = None
        self.logger = self._setup_logger()
        self._setup_session()
    
    def _setup_logger(self) -> logging.Logger:
        """Setup logger for this scraper"""
        logger = logging.getLogger(f"scraper_{self.name}")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(f'[{self.name.upper()}] %(levelname)s: %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _setup_session(self):
        """Setup requests session with proper headers"""
        self.session = requests.Session()
        
        # User agents to rotate through
        user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        ]
        
        self.session.headers.update({
            'User-Agent': random.choice(user_agents),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
    
    def make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """
        Make HTTP request with rate limiting and error handling
        """
        for attempt in range(self.max_retries):
            try:
                self.rate_limiter.wait_if_needed()
                
                response = self.session.request(
                    method=method,
                    url=url,
                    timeout=self.timeout,
                    **kwargs
                )
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:  # Too Many Requests
                    wait_time = min(60 * (attempt + 1), 300)  # Max 5 minutes
                    self.logger.warning(f"Rate limited, waiting {wait_time}s")
                    time.sleep(wait_time)
                    continue
                elif response.status_code in [403, 404]:
                    self.logger.warning(f"Access denied or not found: {url}")
                    return None
                else:
                    self.logger.warning(f"HTTP {response.status_code} for {url}")
                    
            except requests.exceptions.Timeout:
                self.logger.warning(f"Timeout for {url} (attempt {attempt + 1})")
            except requests.exceptions.ConnectionError:
                self.logger.warning(f"Connection error for {url} (attempt {attempt + 1})")
            except Exception as e:
                self.logger.error(f"Unexpected error for {url}: {e}")
            
            if attempt < self.max_retries - 1:
                wait_time = 2 ** attempt + random.uniform(1, 3)
                time.sleep(wait_time)
        
        self.logger.error(f"Failed to fetch {url} after {self.max_retries} attempts")
        return None
    
    def validate_content(self, content: ScrapedContent) -> bool:
        """
        Validate scraped content quality and relevance
        """
        if not content.title or len(content.title.strip()) < 5:
            return False
        
        if not content.url or not self._is_valid_url(content.url):
            return False
        
        # Check for spam patterns using AI-based detection
        if self._is_spam_content(content.title):
            return False
        
        # Check if content is too old (default: 30 days)
        if content.published_date:
            cutoff_date = datetime.now() - timedelta(days=30)
            if content.published_date < cutoff_date:
                return False
        
        return True
    
    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid"""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except:
            return False
    
    def _is_spam_content(self, title: str) -> bool:
        """
        Check if content appears to be spam using pattern analysis
        Uses simple heuristics to avoid external AI dependencies
        """
        if not title:
            return True
        
        title_lower = title.lower()
        
        # Basic spam detection heuristics
        spam_signals = 0
        
        # Excessive punctuation
        if title.count('!') > 2 or title.count('?') > 2:
            spam_signals += 1
        
        # All caps words (more than 2)
        caps_words = [word for word in title.split() if word.isupper() and len(word) > 2]
        if len(caps_words) > 2:
            spam_signals += 1
        
        # Common spam phrases (minimal set)
        basic_spam_phrases = ['click here', 'buy now', 'limited time', 'act now', 'free money']
        if any(phrase in title_lower for phrase in basic_spam_phrases):
            spam_signals += 2
        
        # Too many numbers in title
        number_count = sum(1 for char in title if char.isdigit())
        if number_count > len(title) * 0.3:  # More than 30% numbers
            spam_signals += 1
        
        return spam_signals >= 2  # Threshold for spam detection
    
    def calculate_relevance_score(self, content: ScrapedContent, query_terms: List[str]) -> float:
        """
        Calculate relevance score for content based on query terms with stricter matching
        """
        if not query_terms:
            return 1.0
        
        score = 0.0
        title_lower = content.title.lower()
        summary_lower = (content.summary or '').lower()
        text_to_analyze = f"{title_lower} {summary_lower}"
        
        # Count how many query terms are found
        terms_found = 0
        total_terms = len(query_terms)
        
        for term in query_terms:
            term_lower = term.lower()
            if term_lower in text_to_analyze:
                terms_found += 1
                # Weight title matches higher
                if term_lower in title_lower:
                    score += 2.0
                else:
                    score += 1.0
        
        # More lenient term coverage requirements  
        term_coverage = terms_found / total_terms
        if term_coverage < 0.2:
            score *= 0.1  # Only heavily penalize very low coverage
        elif term_coverage < 0.4:
            score *= 0.5  # Light penalty for low coverage
        elif term_coverage < 0.6:
            score *= 0.8  # Very light penalty for medium coverage
        
        # Additional penalty for very generic/political content that happens to contain keywords
        if self._seems_unrelated_political_content(title_lower, query_terms):
            score *= 0.1
            
        # Normalize by number of terms
        max_score = len(query_terms) * 2.0
        return min(score / max_score if max_score > 0 else 0.0, 1.0)
    
    def _seems_unrelated_political_content(self, title_lower: str, query_terms: List[str]) -> bool:
        """
        Check if content seems to be unrelated political/policy content that happens to match keywords
        """
        political_indicators = [
            'policy', 'minister', 'government', 'parliament', 'congress', 'senate', 
            'election', 'vote', 'political', 'diplomat', 'embassy', 'treaty',
            'act east', 'foreign policy', 'bilateral', 'asean', 'trump', 'biden',
            'protest', 'police', 'arrest', 'settlement', 'occupied', 'tensions'
        ]
        
        # If it contains political terms and query seems to be about something specific (not politics)
        has_political_content = any(indicator in title_lower for indicator in political_indicators)
        
        # Check if query seems to be about non-political topics
        query_text = ' '.join(query_terms).lower()
        non_political_indicators = [
            'mango', 'fruit', 'food', 'recipe', 'cooking', 'health', 'nutrition',
            'sports', 'game', 'technology', 'app', 'software'
        ]
        
        seems_non_political_query = any(indicator in query_text for indicator in non_political_indicators)
        
        return has_political_content and seems_non_political_query
    
    def filter_content(self, contents: List[ScrapedContent], 
                      query_terms: List[str] = None,
                      max_results: int = 20) -> List[ScrapedContent]:
        """
        Filter and rank scraped content
        """
        # Validate content
        valid_contents = [c for c in contents if self.validate_content(c)]
        self.logger.info(f"Filtered {len(contents)} -> {len(valid_contents)} valid items")
        
        # Calculate relevance scores if query terms provided
        if query_terms:
            for content in valid_contents:
                content.relevance_score = self.calculate_relevance_score(content, query_terms)
            
            # Filter out very low relevance content (threshold: 0.1 - very lenient)
            valid_contents = [c for c in valid_contents if c.relevance_score >= 0.1]
            self.logger.info(f"After relevance filtering: {len(valid_contents)} items remain")
        
        # Sort by relevance score (descending) and then by date
        valid_contents.sort(key=lambda x: (
            x.relevance_score,
            x.published_date or datetime.min
        ), reverse=True)
        
        # Remove duplicates based on title similarity
        unique_contents = self._remove_duplicates(valid_contents)
        
        return unique_contents[:max_results]
    
    def _remove_duplicates(self, contents: List[ScrapedContent]) -> List[ScrapedContent]:
        """Remove duplicate content based on title similarity"""
        seen_hashes = set()
        unique_contents = []
        
        for content in contents:
            # Create hash of normalized title
            normalized_title = ''.join(c.lower() for c in content.title if c.isalnum())
            content_hash = hashlib.md5(normalized_title.encode()).hexdigest()
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_contents.append(content)
        
        return unique_contents
    
    @abstractmethod
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Abstract method to be implemented by specific scrapers
        
        Args:
            query: Search query or topic
            max_results: Maximum number of results to return
            
        Returns:
            List of ScrapedContent objects
        """
        pass
    
    def __del__(self):
        """Cleanup session on destruction"""
        if hasattr(self, 'session') and self.session:
            self.session.close()