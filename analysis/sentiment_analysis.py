"""
Sentiment analysis module for the Telegram Trading Bot.
Analyzes market sentiment from news and social media.
"""

import asyncio
import aiohttp
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    VADER_AVAILABLE = True
except ImportError:
    VADER_AVAILABLE = False

try:
    from textblob import TextBlob
    TEXTBLOB_AVAILABLE = True
except ImportError:
    TEXTBLOB_AVAILABLE = False

try:
    from newsapi import NewsApiClient
    NEWSAPI_AVAILABLE = True
except ImportError:
    NEWSAPI_AVAILABLE = False

from loguru import logger
from ..core.config import get_settings
from ..core.exceptions import SentimentAnalysisError
from ..core.utils import safe_json_loads


@dataclass
class SentimentResult:
    """Sentiment analysis result."""
    score: float  # -1 (very negative) to 1 (very positive)
    label: str    # 'positive', 'negative', 'neutral'
    confidence: float  # 0 to 1
    source_count: int  # Number of sources analyzed


@dataclass
class NewsArticle:
    """News article data."""
    title: str
    description: str
    content: str
    source: str
    published_at: datetime
    url: str


class SentimentAnalyzer:
    """Sentiment analysis engine."""
    
    def __init__(self):
        self.settings = get_settings()
        self.vader_analyzer = None
        self.news_client = None
        
        if VADER_AVAILABLE:
            self.vader_analyzer = SentimentIntensityAnalyzer()
        
        if NEWSAPI_AVAILABLE and self.settings.api.news_api_key:
            self.news_client = NewsApiClient(api_key=self.settings.api.news_api_key)
    
    def analyze_text_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of a single text."""
        if not text or not text.strip():
            return SentimentResult(0.0, 'neutral', 0.0, 0)
        
        scores = []
        methods_used = 0
        
        # VADER sentiment analysis
        if self.vader_analyzer:
            try:
                vader_scores = self.vader_analyzer.polarity_scores(text)
                compound_score = vader_scores['compound']
                scores.append(compound_score)
                methods_used += 1
            except Exception as e:
                logger.warning(f"VADER analysis failed: {e}")
        
        # TextBlob sentiment analysis
        if TEXTBLOB_AVAILABLE:
            try:
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity  # -1 to 1
                scores.append(polarity)
                methods_used += 1
            except Exception as e:
                logger.warning(f"TextBlob analysis failed: {e}")
        
        if not scores:
            logger.warning("No sentiment analysis methods available")
            return SentimentResult(0.0, 'neutral', 0.0, 0)
        
        # Average the scores
        avg_score = sum(scores) / len(scores)
        
        # Determine label
        if avg_score > 0.1:
            label = 'positive'
        elif avg_score < -0.1:
            label = 'negative'
        else:
            label = 'neutral'
        
        # Calculate confidence based on score magnitude and method agreement
        confidence = min(abs(avg_score), 1.0)
        if len(scores) > 1:
            # Boost confidence if methods agree
            score_std = sum((s - avg_score) ** 2 for s in scores) / len(scores)
            agreement_factor = max(0, 1 - score_std)
            confidence = min(confidence * (1 + agreement_factor), 1.0)
        
        return SentimentResult(avg_score, label, confidence, methods_used)
    
    def clean_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis."""
        if not text:
            return ""
        
        # Remove HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        # Remove special characters but keep basic punctuation
        text = re.sub(r'[^\w\s.,!?;:-]', '', text)
        
        return text
    
    async def fetch_news_articles(self, symbol: str, days_back: int = 7, max_articles: int = 50) -> List[NewsArticle]:
        """Fetch news articles related to a trading symbol."""
        if not self.news_client:
            logger.warning("News API client not available")
            return []
        
        articles = []
        
        try:
            # Create search queries for the symbol
            queries = self._generate_search_queries(symbol)
            
            from_date = (datetime.now() - timedelta(days=days_back)).strftime('%Y-%m-%d')
            
            for query in queries:
                try:
                    response = self.news_client.get_everything(
                        q=query,
                        from_param=from_date,
                        language='en',
                        sort_by='relevancy',
                        page_size=min(max_articles // len(queries), 20)
                    )
                    
                    if response.get('status') == 'ok':
                        for article_data in response.get('articles', []):
                            article = self._parse_news_article(article_data)
                            if article:
                                articles.append(article)
                
                except Exception as e:
                    logger.warning(f"Failed to fetch news for query '{query}': {e}")
                    continue
            
            # Remove duplicates based on title similarity
            articles = self._remove_duplicate_articles(articles)
            
            logger.info(f"Fetched {len(articles)} news articles for {symbol}")
            return articles[:max_articles]
            
        except Exception as e:
            logger.error(f"Error fetching news articles: {e}")
            return []
    
    def _generate_search_queries(self, symbol: str) -> List[str]:
        """Generate search queries for a trading symbol."""
        symbol = symbol.upper()
        queries = [symbol]
        
        # Add common variations and related terms
        symbol_mappings = {
            'EURUSD': ['EUR USD', 'Euro Dollar', 'EUR/USD'],
            'GBPUSD': ['GBP USD', 'Pound Dollar', 'GBP/USD'],
            'USDJPY': ['USD JPY', 'Dollar Yen', 'USD/JPY'],
            'BTCUSD': ['Bitcoin', 'BTC', 'Bitcoin USD'],
            'ETHUSD': ['Ethereum', 'ETH', 'Ethereum USD'],
            'XAUUSD': ['Gold', 'Gold USD', 'XAU/USD'],
            'XAGUSD': ['Silver', 'Silver USD', 'XAG/USD'],
            'US30': ['Dow Jones', 'DJIA', 'Dow'],
            'US500': ['S&P 500', 'SPX', 'S&P'],
            'NAS100': ['NASDAQ', 'NASDAQ 100', 'NDX'],
        }
        
        if symbol in symbol_mappings:
            queries.extend(symbol_mappings[symbol])
        
        return queries
    
    def _parse_news_article(self, article_data: Dict) -> Optional[NewsArticle]:
        """Parse news article data from API response."""
        try:
            title = article_data.get('title', '')
            description = article_data.get('description', '')
            content = article_data.get('content', '')
            source = article_data.get('source', {}).get('name', 'Unknown')
            url = article_data.get('url', '')
            
            published_at_str = article_data.get('publishedAt', '')
            if published_at_str:
                published_at = datetime.fromisoformat(published_at_str.replace('Z', '+00:00'))
            else:
                published_at = datetime.now()
            
            if not title and not description:
                return None
            
            return NewsArticle(
                title=self.clean_text(title),
                description=self.clean_text(description),
                content=self.clean_text(content),
                source=source,
                published_at=published_at,
                url=url
            )
            
        except Exception as e:
            logger.warning(f"Failed to parse news article: {e}")
            return None
    
    def _remove_duplicate_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Remove duplicate articles based on title similarity."""
        if not articles:
            return articles
        
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Create a normalized title for comparison
            normalized_title = re.sub(r'[^\w\s]', '', article.title.lower())
            normalized_title = ' '.join(normalized_title.split())
            
            # Check for similarity with existing titles
            is_duplicate = False
            for seen_title in seen_titles:
                # Simple similarity check - if 80% of words match
                title_words = set(normalized_title.split())
                seen_words = set(seen_title.split())
                
                if title_words and seen_words:
                    intersection = len(title_words.intersection(seen_words))
                    union = len(title_words.union(seen_words))
                    similarity = intersection / union if union > 0 else 0
                    
                    if similarity > 0.8:
                        is_duplicate = True
                        break
            
            if not is_duplicate:
                unique_articles.append(article)
                seen_titles.add(normalized_title)
        
        return unique_articles
    
    async def analyze_symbol_sentiment(self, symbol: str, days_back: int = 7) -> SentimentResult:
        """Analyze overall sentiment for a trading symbol."""
        try:
            # Fetch news articles
            articles = await self.fetch_news_articles(symbol, days_back)
            
            if not articles:
                logger.warning(f"No news articles found for {symbol}")
                return SentimentResult(0.0, 'neutral', 0.0, 0)
            
            # Analyze sentiment of each article
            sentiments = []
            total_confidence = 0
            
            for article in articles:
                # Combine title and description for analysis
                text = f"{article.title} {article.description}".strip()
                
                if text:
                    sentiment = self.analyze_text_sentiment(text)
                    sentiments.append(sentiment.score)
                    total_confidence += sentiment.confidence
            
            if not sentiments:
                return SentimentResult(0.0, 'neutral', 0.0, 0)
            
            # Calculate weighted average sentiment
            avg_sentiment = sum(sentiments) / len(sentiments)
            
            # Determine label
            if avg_sentiment > 0.1:
                label = 'positive'
            elif avg_sentiment < -0.1:
                label = 'negative'
            else:
                label = 'neutral'
            
            # Calculate overall confidence
            avg_confidence = total_confidence / len(sentiments) if sentiments else 0.0
            
            # Boost confidence based on number of sources and agreement
            source_factor = min(len(articles) / 10, 1.0)  # More sources = higher confidence
            
            # Calculate agreement among sentiments
            if len(sentiments) > 1:
                sentiment_std = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments)
                agreement_factor = max(0, 1 - sentiment_std)
            else:
                agreement_factor = 0.5
            
            final_confidence = min(avg_confidence * source_factor * (1 + agreement_factor), 1.0)
            
            result = SentimentResult(
                score=avg_sentiment,
                label=label,
                confidence=final_confidence,
                source_count=len(articles)
            )
            
            logger.info(f"Sentiment analysis for {symbol}: {label} ({avg_sentiment:.3f}) "
                       f"from {len(articles)} sources")
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing sentiment for {symbol}: {e}")
            raise SentimentAnalysisError(f"Failed to analyze sentiment: {e}")
    
    async def get_market_sentiment_summary(self, symbols: List[str]) -> Dict[str, SentimentResult]:
        """Get sentiment summary for multiple symbols."""
        results = {}
        
        # Analyze symbols concurrently
        tasks = [self.analyze_symbol_sentiment(symbol) for symbol in symbols]
        
        try:
            sentiment_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for symbol, result in zip(symbols, sentiment_results):
                if isinstance(result, Exception):
                    logger.error(f"Failed to analyze sentiment for {symbol}: {result}")
                    results[symbol] = SentimentResult(0.0, 'neutral', 0.0, 0)
                else:
                    results[symbol] = result
            
            return results
            
        except Exception as e:
            logger.error(f"Error getting market sentiment summary: {e}")
            return {symbol: SentimentResult(0.0, 'neutral', 0.0, 0) for symbol in symbols}


# Alternative sentiment analysis using free sources
class FreeSentimentAnalyzer:
    """Free sentiment analysis using web scraping and public APIs."""
    
    def __init__(self):
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def fetch_reddit_sentiment(self, symbol: str) -> List[str]:
        """Fetch sentiment from Reddit (simplified)."""
        # This is a placeholder for Reddit API integration
        # In a real implementation, you would use the Reddit API
        return []
    
    async def fetch_twitter_sentiment(self, symbol: str) -> List[str]:
        """Fetch sentiment from Twitter (simplified)."""
        # This is a placeholder for Twitter API integration
        # In a real implementation, you would use the Twitter API
        return []
    
    async def analyze_free_sentiment(self, symbol: str) -> SentimentResult:
        """Analyze sentiment using free sources."""
        try:
            # Combine data from multiple free sources
            texts = []
            
            # Add Reddit data
            reddit_texts = await self.fetch_reddit_sentiment(symbol)
            texts.extend(reddit_texts)
            
            # Add Twitter data
            twitter_texts = await self.fetch_twitter_sentiment(symbol)
            texts.extend(twitter_texts)
            
            if not texts:
                return SentimentResult(0.0, 'neutral', 0.0, 0)
            
            # Analyze combined sentiment
            analyzer = SentimentAnalyzer()
            combined_text = ' '.join(texts)
            
            return analyzer.analyze_text_sentiment(combined_text)
            
        except Exception as e:
            logger.error(f"Error in free sentiment analysis: {e}")
            return SentimentResult(0.0, 'neutral', 0.0, 0)


def get_sentiment_signal(sentiment_result: SentimentResult, threshold: float = 0.3) -> str:
    """Convert sentiment result to trading signal."""
    if sentiment_result.confidence < 0.3:  # Low confidence
        return 'NEUTRAL'
    
    if sentiment_result.score > threshold:
        return 'BUY'
    elif sentiment_result.score < -threshold:
        return 'SELL'
    else:
        return 'NEUTRAL'

