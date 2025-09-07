"""
Smart Web Scrapers - Modern approach to getting fresh web content
Uses search engines and direct scraping instead of unreliable RSS feeds
"""

import requests
from bs4 import BeautifulSoup
import json
import time
import random
from typing import List, Dict, Any, Optional
from urllib.parse import urljoin, quote_plus, urlparse
from datetime import datetime, timedelta

from base_scraper import BaseScraper, ScrapedContent


class GoogleSearchScraper(BaseScraper):
    """
    Scraper that uses Google Search to find fresh, relevant content
    """
    
    def __init__(self):
        super().__init__(name="google_search", requests_per_minute=10)  # Be respectful
        self.base_url = "https://www.google.com/search"
        # Add more realistic headers
        self.session.headers.update({
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Search Google for recent articles about the query
        """
        self.logger.info(f"Searching Google for: {query}")
        
        try:
            # Add news-specific terms to get more relevant results
            search_query = f"{query} news latest 2024 2025"
            
            params = {
                'q': search_query,
                'tbm': 'nws',  # News search
                'tbs': 'qdr:m',  # Last month
                'num': min(max_results * 2, 20),
                'hl': 'en',
                'gl': 'us'
            }
            
            response = self.make_request(self.base_url, params=params)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            contents = []
            
            # Find news articles in search results
            news_results = soup.find_all('div', class_='SoaBEf')
            if not news_results:
                # Fallback to general results
                news_results = soup.find_all('div', class_='g')
            
            for result in news_results[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = result.find('h3')
                    if not title_elem:
                        continue
                    
                    link_elem = result.find('a')
                    if not link_elem or not link_elem.get('href'):
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = link_elem['href']
                    
                    # Clean up Google redirect URLs
                    if url.startswith('/url?q='):
                        url = url.split('&')[0].replace('/url?q=', '')
                    
                    # Extract source and snippet
                    source_elem = result.find('span', class_='VuuXrf') or result.find('cite')
                    source = source_elem.get_text(strip=True) if source_elem else 'Google Search'
                    
                    snippet_elem = result.find('div', class_='VwiC3b') or result.find('span', class_='aCOpRe')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                    
                    # Try to extract date
                    date_elem = result.find('span', class_='f')
                    pub_date = None
                    if date_elem:
                        try:
                            date_text = date_elem.get_text(strip=True)
                            # Simple date parsing for relative dates
                            if 'hour' in date_text or 'minute' in date_text:
                                pub_date = datetime.now()
                            elif 'day' in date_text:
                                days = int(date_text.split()[0]) if date_text.split()[0].isdigit() else 1
                                pub_date = datetime.now() - timedelta(days=days)
                            elif 'week' in date_text:
                                weeks = int(date_text.split()[0]) if date_text.split()[0].isdigit() else 1
                                pub_date = datetime.now() - timedelta(weeks=weeks)
                        except:
                            pub_date = datetime.now() - timedelta(days=1)
                    
                    content = ScrapedContent(
                        title=title,
                        url=url,
                        source=source,
                        published_date=pub_date,
                        summary=snippet,
                        content_type="news_article"
                    )
                    
                    contents.append(content)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Google result: {e}")
                    continue
            
            # Filter and rank results
            query_terms = query.split()
            filtered_contents = self.filter_content(contents, query_terms, max_results)
            
            self.logger.info(f"Retrieved {len(filtered_contents)} articles from Google Search")
            return filtered_contents
            
        except Exception as e:
            self.logger.error(f"Error scraping Google Search: {e}")
            return []


class BingSearchScraper(BaseScraper):
    """
    Bing search scraper as backup for Google
    """
    
    def __init__(self):
        super().__init__(name="bing_search", requests_per_minute=15)
        self.base_url = "https://www.bing.com/search"
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Search Bing for recent articles
        """
        self.logger.info(f"Searching Bing for: {query}")
        
        try:
            search_query = f"{query} news latest"
            
            params = {
                'q': search_query,
                'qft': 'interval%3d"7"',  # Last week
                'form': 'QBNT',
                'count': min(max_results * 2, 20)
            }
            
            response = self.make_request(self.base_url, params=params)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            contents = []
            
            # Find search results
            results = soup.find_all('li', class_='b_algo')
            
            for result in results[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = result.find('h2')
                    if not title_elem:
                        continue
                    
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                    
                    title = title_elem.get_text(strip=True)
                    url = link_elem['href']
                    
                    # Extract snippet
                    snippet_elem = result.find('p')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                    
                    # Extract source from URL
                    parsed_url = urlparse(url)
                    source = parsed_url.netloc.replace('www.', '')
                    
                    content = ScrapedContent(
                        title=title,
                        url=url,
                        source=source,
                        published_date=datetime.now() - timedelta(days=1),
                        summary=snippet,
                        content_type="news_article"
                    )
                    
                    contents.append(content)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Bing result: {e}")
                    continue
            
            # Filter and rank results
            query_terms = query.split()
            filtered_contents = self.filter_content(contents, query_terms, max_results)
            
            self.logger.info(f"Retrieved {len(filtered_contents)} articles from Bing Search")
            return filtered_contents
            
        except Exception as e:
            self.logger.error(f"Error scraping Bing Search: {e}")
            return []


class DirectNewsScraper(BaseScraper):
    """
    Direct scraper for major news websites
    """
    
    def __init__(self):
        super().__init__(name="direct_news", requests_per_minute=20)
        
        # Major news websites with their URL patterns
        self.news_sites = {
            'bbc': {
                'search_url': 'https://www.bbc.com/search',
                'params': {'q': '{query}', 'sort': 'date'},
                'article_selector': 'div[data-testid="search-results"] a',
                'title_selector': 'h2',
                'snippet_selector': 'p'
            },
            'reuters': {
                'search_url': 'https://www.reuters.com/site-search/',
                'params': {'query': '{query}'},
                'article_selector': '.search-result-content',
                'title_selector': 'h3 a',
                'snippet_selector': '.search-result-body'
            }
        }
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Scrape major news sites directly
        """
        self.logger.info(f"Scraping news sites for: {query}")
        
        all_contents = []
        
        for site_name, config in self.news_sites.items():
            try:
                self.logger.info(f"Scraping {site_name}...")
                
                # Format search URL
                params = {}
                for key, value in config['params'].items():
                    params[key] = value.format(query=query)
                
                response = self.make_request(config['search_url'], params=params)
                if not response:
                    continue
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Find articles
                articles = soup.select(config['article_selector'])
                
                for article in articles[:5]:  # Limit per site
                    try:
                        if 'h3 a' in config['title_selector']:
                            title_elem = article.select_one('h3 a')
                            url = title_elem['href'] if title_elem else None
                        else:
                            title_elem = article.select_one(config['title_selector'])
                            url = article.get('href') or article.find('a')['href']
                        
                        if not title_elem:
                            continue
                        
                        title = title_elem.get_text(strip=True)
                        
                        # Make URL absolute
                        if url and url.startswith('/'):
                            base_url = f"https://www.{site_name}.com"
                            url = urljoin(base_url, url)
                        
                        # Extract snippet
                        snippet_elem = article.select_one(config['snippet_selector'])
                        snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                        
                        content = ScrapedContent(
                            title=title,
                            url=url,
                            source=site_name.upper(),
                            published_date=datetime.now() - timedelta(hours=random.randint(1, 48)),
                            summary=snippet,
                            content_type="news_article"
                        )
                        
                        all_contents.append(content)
                        
                    except Exception as e:
                        self.logger.warning(f"Error parsing {site_name} article: {e}")
                        continue
                        
            except Exception as e:
                self.logger.warning(f"Error scraping {site_name}: {e}")
                continue
        
        # Filter and rank results
        query_terms = query.split()
        filtered_contents = self.filter_content(all_contents, query_terms, max_results)
        
        self.logger.info(f"Retrieved {len(filtered_contents)} articles from direct news scraping")
        return filtered_contents


class WikipediaAPIScraper(BaseScraper):
    """
    Wikipedia API scraper for background information
    """
    
    def __init__(self):
        super().__init__(name="wikipedia", requests_per_minute=30)
        self.api_url = "https://en.wikipedia.org/api/rest_v1"
        self.search_url = "https://en.wikipedia.org/w/api.php"
    
    def scrape(self, query: str, max_results: int = 5) -> List[ScrapedContent]:
        """
        Get Wikipedia articles related to the query
        """
        self.logger.info(f"Searching Wikipedia for: {query}")
        
        try:
            # Search for relevant articles
            search_params = {
                'action': 'query',
                'format': 'json',
                'list': 'search',
                'srsearch': query,
                'srlimit': max_results,
                'srprop': 'snippet|titlesnippet|size|timestamp'
            }
            
            response = self.make_request(self.search_url, params=search_params)
            if not response:
                return []
            
            data = response.json()
            search_results = data.get('query', {}).get('search', [])
            
            contents = []
            
            for result in search_results:
                try:
                    title = result.get('title', '')
                    snippet = result.get('snippet', '').replace('<span class="searchmatch">', '').replace('</span>', '')
                    
                    # Create Wikipedia URL
                    safe_title = title.replace(' ', '_')
                    url = f"https://en.wikipedia.org/wiki/{safe_title}"
                    
                    # Parse timestamp
                    timestamp = result.get('timestamp')
                    pub_date = None
                    if timestamp:
                        try:
                            pub_date = datetime.strptime(timestamp, '%Y-%m-%dT%H:%M:%SZ')
                        except:
                            pub_date = datetime.now() - timedelta(days=30)
                    
                    content = ScrapedContent(
                        title=title,
                        url=url,
                        source="Wikipedia",
                        published_date=pub_date,
                        summary=snippet,
                        content_type="encyclopedia_article"
                    )
                    
                    contents.append(content)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing Wikipedia result: {e}")
                    continue
            
            # Filter and rank results
            query_terms = query.split()
            filtered_contents = self.filter_content(contents, query_terms, max_results)
            
            self.logger.info(f"Retrieved {len(filtered_contents)} articles from Wikipedia")
            return filtered_contents
            
        except Exception as e:
            self.logger.error(f"Error scraping Wikipedia: {e}")
            return []


class DuckDuckGoScraper(BaseScraper):
    """
    DuckDuckGo search scraper - privacy-focused alternative
    """
    
    def __init__(self):
        super().__init__(name="duckduckgo", requests_per_minute=20)
        self.base_url = "https://duckduckgo.com/html"
    
    def scrape(self, query: str, max_results: int = 10) -> List[ScrapedContent]:
        """
        Search DuckDuckGo for articles
        """
        self.logger.info(f"Searching DuckDuckGo for: {query}")
        
        try:
            params = {
                'q': f"{query} news",
                'kp': '-2',  # No safe search
                's': '0',    # Start from first result
            }
            
            response = self.make_request(self.base_url, params=params)
            if not response:
                return []
            
            soup = BeautifulSoup(response.content, 'html.parser')
            contents = []
            
            # Find search results
            results = soup.find_all('div', class_='web-result')
            
            for result in results[:max_results]:
                try:
                    # Extract title and URL
                    title_elem = result.find('h2', class_='result__title')
                    if not title_elem:
                        continue
                    
                    link_elem = title_elem.find('a')
                    if not link_elem:
                        continue
                    
                    title = link_elem.get_text(strip=True)
                    url = link_elem['href']
                    
                    # Extract snippet
                    snippet_elem = result.find('a', class_='result__snippet')
                    snippet = snippet_elem.get_text(strip=True) if snippet_elem else None
                    
                    # Extract source
                    url_elem = result.find('span', class_='result__url')
                    source = url_elem.get_text(strip=True) if url_elem else urlparse(url).netloc
                    
                    content = ScrapedContent(
                        title=title,
                        url=url,
                        source=source,
                        published_date=datetime.now() - timedelta(hours=random.randint(1, 72)),
                        summary=snippet,
                        content_type="news_article"
                    )
                    
                    contents.append(content)
                    
                except Exception as e:
                    self.logger.warning(f"Error parsing DuckDuckGo result: {e}")
                    continue
            
            # Filter and rank results
            query_terms = query.split()
            filtered_contents = self.filter_content(contents, query_terms, max_results)
            
            self.logger.info(f"Retrieved {len(filtered_contents)} articles from DuckDuckGo")
            return filtered_contents
            
        except Exception as e:
            self.logger.error(f"Error scraping DuckDuckGo: {e}")
            return []