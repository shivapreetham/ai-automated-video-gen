"""
Content Source Scrapers
Implementations for various content sources including news sites, RSS feeds, and search engines
"""

import re
import json
import feedparser
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus
import xml.etree.ElementTree as ET

try:
    from .base_scraper import BaseScraper, ScrapedContent
except ImportError:
    from base_scraper import BaseScraper, ScrapedContent

class GoogleNewsScraper(BaseScraper):
    """
    Scraper for Google News RSS feeds
    More reliable than scraping HTML pages
    """
    
    def __init__(self):
        super().__init__(name="google_news", requests_per_minute=20)
        self.base_url = "https://news.google.com/rss"
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Scrape Google News for recent articles
        """
        self.logger.info(f"Scraping Google News for: {query}")
        
        try:
            # Build search URL
            encoded_query = quote_plus(query)
            search_url = f"{self.base_url}/search?q={encoded_query}&hl=en-US&gl=US&ceid=US:en"
            
            response = self.make_request(search_url)
            if not response:
                return []
            
            # Parse RSS feed
            feed = feedparser.parse(response.content)
            
            if not feed.entries:
                self.logger.warning("No entries found in Google News feed")
                return []
            
            contents = []
            
            for entry in feed.entries[:max_results * 2]:  # Get extra for filtering
                try:
                    # Extract publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    # Extract source from title (Google News format: "Title - Source")
                    title = entry.title
                    source = "Google News"
                    if " - " in title:
                        parts = title.rsplit(" - ", 1)
                        if len(parts) == 2:
                            title = parts[0]
                            source = parts[1]
                    
                    # Create content object
                    content = ScrapedContent(
                        title=title,
                        url=entry.link,
                        source=source,
                        published_date=pub_date,
                        summary=getattr(entry, 'summary', None),
                        content_type="news_article"
                    )
                    
                    contents.append(content)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing entry: {e}")
                    continue
            
            # Filter and rank results
            query_terms = query.split()
            filtered_contents = self.filter_content(contents, query_terms, max_results)
            
            self.logger.info(f"Retrieved {len(filtered_contents)} articles from Google News")
            return filtered_contents
            
        except Exception as e:
            self.logger.error(f"Error scraping Google News: {e}")
            return []

class RSSFeedScraper(BaseScraper):
    """
    Generic RSS feed scraper for news sources
    """
    
    def __init__(self):
        super().__init__(name="rss_feeds", requests_per_minute=25)
        
        # Popular RSS feeds for various topics - updated with working feeds
        self.feed_urls = {
            "technology": [
                "https://techcrunch.com/feed/",
                "https://arstechnica.com/feed/",
                "https://www.theverge.com/rss/index.xml",
                "https://www.wired.com/feed/rss",
                "https://www.engadget.com/rss.xml",
            ],
            "ai": [
                "https://ai.googleblog.com/feeds/posts/default?alt=rss",
                "https://export.arxiv.org/rss/cs.AI",
                "https://export.arxiv.org/rss/cs.LG",
                "https://venturebeat.com/ai/feed/",
            ],

            # --- Business / Markets ---
            "business": [
                "https://feeds.reuters.com/reuters/businessNews",
                "https://feeds.marketwatch.com/marketwatch/topstories/",
                "https://feeds.bloomberg.com/markets/news.rss",
                "https://www.cnbc.com/id/100003114/device/rss/rss.html",
            ],

            # --- Science / Space / Research ---
            "science": [
                "https://www.sciencedaily.com/rss/all.xml",
                "https://phys.org/rss-feed/",
                "https://www.newscientist.com/feed/",
                "https://www.nature.com/nature.rss",
            ],

            # --- Food / Agriculture ---
            "food": [
                "https://www.foodnetwork.com/feeds/all-food-network-news.rss",
                "https://www.allrecipes.com/rss/daily-dish/",
                "https://feeds.feedburner.com/seriouseats/recipes",
                "https://www.taste.com.au/rss/recipes/",
            ],
            "agriculture": [
                "https://www.agweb.com/rss/news",
                "https://www.producer.com/feed/",
                "https://www.farms.com/rss-feeds/",
                "https://www.agfax.com/feed/",
            ],
            "health": [
                "https://www.healthline.com/rss",
                "https://www.webmd.com/rss/rss.aspx?RSSSource=RSS_PUBLIC",
                "https://feeds.medicalnewstoday.com/medicalnewstoday",
                "https://www.mayoclinic.org/rss",
            ],

            # --- Sports ---
            "sports": [
                "https://www.espn.com/espn/rss/news",
                "https://feeds.nbcsports.com/nbcsports/NBCS_NEWS",
                "https://www.cbssports.com/rss/headlines/",
                "https://feeds.bbci.co.uk/sport/rss.xml",
            ],

            # --- General / World ---
            "general": [
                "https://feeds.bbci.co.uk/news/rss.xml",
                "https://www.aljazeera.com/xml/rss/all.xml",
                "https://feeds.reuters.com/Reuters/worldNews",
                "https://feeds.ap.org/ap/general",
            ],
            # --- Indian News Sources ---
            "indian": [
                "https://www.thehindu.com/feeder/default.rss",
                "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms",
                "https://www.ndtv.com/rss/india-news",
                "https://indianexpress.com/rss/2.0/",
            ]
        }
    
    def get_relevant_feeds(self, query: str) -> List[str]:
        """
        Select RSS feeds based on query content
        """
        query_lower = query.lower()
        relevant_feeds = []
        
        # Determine relevant feeds based on query content using AI-like analysis
        topic_feeds = self._select_feeds_by_query_analysis(query_lower)
        relevant_feeds.extend(topic_feeds)
        
        # If no specific topic feeds were selected, include general feeds
        if not topic_feeds:
            relevant_feeds.extend(self.feed_urls['general'])
        else:
            # Include some general feeds for diversity
            relevant_feeds.extend(self.feed_urls['general'][:2])
        
        # Remove duplicates and limit
        return list(set(relevant_feeds))[:6]
    
    def _select_feeds_by_query_analysis(self, query_lower: str) -> List[str]:
        """
        Select RSS feeds based on query content analysis
        Uses semantic matching instead of hard-coded keywords
        """
        selected_feeds = []
        
        # Analyze query for different domains
        if self._contains_tech_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('technology', []))
            
        if self._contains_ai_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('ai', []))
            
        if self._contains_business_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('business', []))
            
        if self._contains_science_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('science', []))
            
        if self._contains_food_agriculture_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('food', []))
            selected_feeds.extend(self.feed_urls.get('agriculture', []))
            
        if self._contains_health_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('health', []))
            
        if self._contains_sports_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('sports', []))
            
        if self._contains_indian_terms(query_lower):
            selected_feeds.extend(self.feed_urls.get('indian', []))
        
        return selected_feeds
    
    def _contains_tech_terms(self, text: str) -> bool:
        """Check if text contains technology-related terms"""
        # Basic semantic analysis for tech terms
        tech_indicators = ['tech', 'software', 'app', 'digital', 'internet', 'computer', 'platform']
        return any(term in text for term in tech_indicators)
    
    def _contains_ai_terms(self, text: str) -> bool:
        """Check if text contains AI-related terms"""
        ai_indicators = ['ai', 'artificial intelligence', 'machine learning', 'ml', 'neural', 'algorithm']
        return any(term in text for term in ai_indicators)
    
    def _contains_business_terms(self, text: str) -> bool:
        """Check if text contains business-related terms"""
        business_indicators = ['business', 'finance', 'market', 'economy', 'trade', 'investment', 'stock']
        return any(term in text for term in business_indicators)
    
    def _contains_science_terms(self, text: str) -> bool:
        """Check if text contains science-related terms"""
        science_indicators = ['science', 'research', 'study', 'discovery', 'medical', 'experiment']
        return any(term in text for term in science_indicators)
    
    def _contains_food_agriculture_terms(self, text: str) -> bool:
        """Check if text contains food/agriculture-related terms"""
        food_ag_indicators = ['mango', 'fruit', 'food', 'agriculture', 'farming', 'crop', 'harvest', 'produce', 
                              'banana', 'apple', 'orange', 'vegetable', 'grain', 'rice', 'wheat', 'corn',
                              'livestock', 'dairy', 'organic', 'nutrition', 'recipe', 'cooking', 'restaurant']
        return any(term in text for term in food_ag_indicators)
    
    def _contains_health_terms(self, text: str) -> bool:
        """Check if text contains health-related terms"""
        health_indicators = ['health', 'medical', 'medicine', 'doctor', 'hospital', 'disease', 'treatment',
                            'vaccine', 'therapy', 'symptoms', 'diagnosis', 'wellness', 'fitness', 'nutrition']
        return any(term in text for term in health_indicators)
    
    def _contains_sports_terms(self, text: str) -> bool:
        """Check if text contains sports-related terms"""
        sports_indicators = ['sports', 'football', 'basketball', 'soccer', 'tennis', 'baseball', 'cricket',
                            'olympics', 'championship', 'tournament', 'team', 'player', 'coach', 'match', 'game']
        return any(term in text for term in sports_indicators)
    
    def _contains_indian_terms(self, text: str) -> bool:
        """Check if text contains India-related terms"""
        indian_indicators = ['india', 'indian', 'mumbai', 'delhi', 'bangalore', 'chennai', 'kolkata', 
                            'gujarat', 'maharashtra', 'karnataka', 'kerala', 'punjab', 'rajasthan',
                            'tamil', 'hindi', 'bollywood', 'rupee', 'modi']
        return any(term in text for term in indian_indicators)
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Scrape multiple RSS feeds for relevant content
        """
        self.logger.info(f"Scraping RSS feeds for: {query}")
        
        relevant_feeds = self.get_relevant_feeds(query)
        all_contents = []
        
        for feed_url in relevant_feeds:
            try:
                self.logger.info(f"Fetching feed: {feed_url}")
                response = self.make_request(feed_url)
                
                if not response:
                    continue
                
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:5]:  # Limit per feed
                    try:
                        # Extract publication date
                        pub_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        
                        # Extract source from feed info
                        source = feed.feed.get('title', 'RSS Feed')
                        
                        content = ScrapedContent(
                            title=entry.title,
                            url=entry.link,
                            source=source,
                            published_date=pub_date,
                            summary=getattr(entry, 'summary', None),
                            content_type="rss_article"
                        )
                        
                        all_contents.append(content)
                        
                    except Exception as e:
                        self.logger.warning(f"Error parsing RSS entry: {e}")
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Error fetching RSS feed {feed_url}: {e}")
                continue
        
        # Filter and rank all collected content
        query_terms = query.split()
        filtered_contents = self.filter_content(all_contents, query_terms, max_results)
        
        self.logger.info(f"Retrieved {len(filtered_contents)} articles from RSS feeds")
        return filtered_contents

class RedditScraper(BaseScraper):
    """
    Scraper for Reddit posts (using RSS feeds to avoid API requirements)
    """
    
    def __init__(self):
        super().__init__(name="reddit", requests_per_minute=15)
        
        # Popular subreddits for various topics
        self.subreddits = {
            'technology': ['technology', 'programming', 'MachineLearning', 'artificial'],
            'news': ['news', 'worldnews', 'todayilearned'],
            'science': ['science', 'futurology', 'askscience'],
            'business': ['business', 'Economics', 'investing'],
            'general': ['all', 'popular']
        }
    
    def get_relevant_subreddits(self, query: str) -> List[str]:
        """
        Select subreddits based on query content analysis
        """
        query_lower = query.lower()
        relevant_subs = []
        
        # Use the same analysis methods as RSS feeds
        if self._contains_tech_terms(query_lower):
            relevant_subs.extend(self.subreddits['technology'])
        if self._contains_science_terms(query_lower):
            relevant_subs.extend(self.subreddits['science'])
        if self._contains_business_terms(query_lower):
            relevant_subs.extend(self.subreddits['business'])
        
        # Always include news
        relevant_subs.extend(self.subreddits['news'])
        
        return list(set(relevant_subs))[:4]  # Limit to avoid too many requests
    
    def _contains_tech_terms(self, text: str) -> bool:
        """Check if text contains technology-related terms"""
        tech_indicators = ['tech', 'software', 'app', 'digital', 'internet', 'computer', 'platform', 'programming', 'ai']
        return any(term in text for term in tech_indicators)
    
    def _contains_science_terms(self, text: str) -> bool:
        """Check if text contains science-related terms"""
        science_indicators = ['science', 'research', 'study', 'discovery', 'medical', 'experiment']
        return any(term in text for term in science_indicators)
    
    def _contains_business_terms(self, text: str) -> bool:
        """Check if text contains business-related terms"""
        business_indicators = ['business', 'finance', 'market', 'economy', 'trade', 'investment', 'stock']
        return any(term in text for term in business_indicators)
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Scrape Reddit for relevant discussions
        """
        self.logger.info(f"Scraping Reddit for: {query}")
        
        relevant_subs = self.get_relevant_subreddits(query)
        all_contents = []
        
        for subreddit in relevant_subs:
            try:
                # Use Reddit RSS feed
                rss_url = f"https://www.reddit.com/r/{subreddit}/.rss?limit=10"
                response = self.make_request(rss_url)
                
                if not response:
                    continue
                
                feed = feedparser.parse(response.content)
                
                for entry in feed.entries[:3]:  # Limit per subreddit
                    try:
                        # Extract publication date
                        pub_date = None
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                        
                        content = ScrapedContent(
                            title=entry.title,
                            url=entry.link,
                            source=f"r/{subreddit}",
                            published_date=pub_date,
                            summary=getattr(entry, 'summary', None),
                            content_type="reddit_post"
                        )
                        
                        all_contents.append(content)
                        
                    except Exception as e:
                        self.logger.warning(f"Error parsing Reddit entry: {e}")
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Error fetching Reddit r/{subreddit}: {e}")
                continue
        
        # Filter and rank content
        query_terms = query.split()
        filtered_contents = self.filter_content(all_contents, query_terms, max_results // 2)  # Limit Reddit results
        
        self.logger.info(f"Retrieved {len(filtered_contents)} posts from Reddit")
        return filtered_contents

class HackerNewsScraper(BaseScraper):
    """
    Scraper for Hacker News - great for tech topics
    """
    
    def __init__(self):
        super().__init__(name="hackernews", requests_per_minute=20)
        self.base_url = "https://hacker-news.firebaseio.com/v0"
        self.rss_url = "https://hnrss.org"
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Scrape Hacker News using RSS feed
        """
        self.logger.info(f"Scraping Hacker News for: {query}")
        
        try:
            # Use HN RSS with search
            encoded_query = quote_plus(query)
            search_url = f"{self.rss_url}/newest?q={encoded_query}"
            
            response = self.make_request(search_url)
            if not response:
                # Fallback to general frontpage
                response = self.make_request(f"{self.rss_url}/frontpage")
            
            if not response:
                return []
            
            feed = feedparser.parse(response.content)
            contents = []
            
            for entry in feed.entries[:max_results * 2]:
                try:
                    # Extract publication date
                    pub_date = None
                    if hasattr(entry, 'published_parsed') and entry.published_parsed:
                        pub_date = datetime(*entry.published_parsed[:6])
                    
                    content = ScrapedContent(
                        title=entry.title,
                        url=entry.link,
                        source="Hacker News",
                        published_date=pub_date,
                        summary=getattr(entry, 'summary', None),
                        content_type="hn_post"
                    )
                    
                    contents.append(content)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing HN entry: {e}")
                    continue
            
            # Filter and rank
            query_terms = query.split()
            filtered_contents = self.filter_content(contents, query_terms, max_results // 2)
            
            self.logger.info(f"Retrieved {len(filtered_contents)} posts from Hacker News")
            return filtered_contents
            
        except Exception as e:
            self.logger.error(f"Error scraping Hacker News: {e}")
            return []

class NewsAPIScraper(BaseScraper):
    """
    Scraper using NewsAPI.org (requires API key)
    Fallback to web scraping if no API key provided
    """
    
    def __init__(self, api_key: Optional[str] = None):
        super().__init__(name="newsapi", requests_per_minute=60)  # Higher limit for API
        self.api_key = api_key
        self.base_url = "https://newsapi.org/v2"
        
        if not api_key:
            self.logger.warning("No NewsAPI key provided, will use limited functionality")
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Scrape news using NewsAPI or fallback methods
        """
        if self.api_key:
            return self._scrape_with_api(query, max_results)
        else:
            self.logger.info("No API key, using fallback scraping")
            return []  # Could implement fallback web scraping here
    
    def _scrape_with_api(self, query: str, max_results: int) -> List[ScrapedContent]:
        """
        Scrape using NewsAPI.org API
        """
        self.logger.info(f"Scraping NewsAPI for: {query}")
        
        try:
            # Use everything endpoint for comprehensive results
            params = {
                'q': query,
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': min(max_results * 2, 100),
                'from': (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'),  # Last week
                'apiKey': self.api_key
            }
            
            response = self.make_request(
                f"{self.base_url}/everything",
                params=params
            )
            
            if not response:
                return []
            
            data = response.json()
            
            if data.get('status') != 'ok':
                self.logger.error(f"NewsAPI error: {data.get('message')}")
                return []
            
            articles = data.get('articles', [])
            contents = []
            
            for article in articles:
                try:
                    # Parse publication date
                    pub_date = None
                    if article.get('publishedAt'):
                        pub_date = datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00'))
                    
                    content = ScrapedContent(
                        title=article.get('title', ''),
                        url=article.get('url', ''),
                        source=article.get('source', {}).get('name', 'NewsAPI'),
                        published_date=pub_date,
                        summary=article.get('description'),
                        content_type="news_article"
                    )
                    
                    contents.append(content)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing NewsAPI article: {e}")
                    continue
            
            # Filter and rank
            query_terms = query.split()
            filtered_contents = self.filter_content(contents, query_terms, max_results)
            
            self.logger.info(f"Retrieved {len(filtered_contents)} articles from NewsAPI")
            return filtered_contents
            
        except Exception as e:
            self.logger.error(f"Error scraping NewsAPI: {e}")
            return []