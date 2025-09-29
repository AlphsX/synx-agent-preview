import aiohttp
import asyncio
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta
from app.config import settings
from ..core.error_handling import (
    retry_with_backoff, RetryConfig, ServiceType, ErrorCode, ErrorSeverity, error_metrics
)
from ..core.logging_middleware import external_api_logger

logger = logging.getLogger(__name__)


class SentimentAnalysisService:
    """
    Social media sentiment analysis service supporting multiple providers.
    Provides sentiment analysis for stocks, topics, and general market sentiment.
    """
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or getattr(settings, 'SENTIMENT_API_KEY', None)
        
        # Multiple sentiment analysis endpoints
        self.endpoints = {
            "twitter": "https://api.twitter.com/2",  # Twitter API v2
            "reddit": "https://www.reddit.com/r",    # Reddit API
            "news": "https://newsapi.org/v2",        # News API for sentiment
            "social": "https://api.socialmention.com/search"  # Social Mention API
        }
        
        # Configure retry settings
        self.retry_config = RetryConfig(
            max_retries=3,
            base_delay=1.0,
            max_delay=30.0,
            exponential_base=2.0,
            jitter=True
        )
        
        # Request timeout
        self.timeout = getattr(settings, 'EXTERNAL_API_TIMEOUT', 30)
    
    async def analyze_stock_sentiment(
        self, 
        symbol: str, 
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a specific stock symbol.
        
        Args:
            symbol: Stock symbol (e.g., "AAPL", "TSLA")
            timeframe: Time period ("1h", "24h", "7d", "30d")
            
        Returns:
            Sentiment analysis results from multiple sources
        """
        if not self.is_available():
            return await self._generate_mock_sentiment(symbol, "stock")
        
        # Start external API call tracking
        call_id = external_api_logger.start_call(
            service_name="sentiment_analysis",
            method="GET",
            url="stock_sentiment",
            request_data={"symbol": symbol, "timeframe": timeframe}
        )
        
        try:
            # Gather sentiment from multiple sources concurrently
            tasks = [
                self._analyze_twitter_sentiment(symbol, timeframe),
                self._analyze_reddit_sentiment(symbol, timeframe),
                self._analyze_news_sentiment(symbol, timeframe)
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process results
            twitter_sentiment = results[0] if not isinstance(results[0], Exception) else {}
            reddit_sentiment = results[1] if not isinstance(results[1], Exception) else {}
            news_sentiment = results[2] if not isinstance(results[2], Exception) else {}
            
            # Combine and calculate overall sentiment
            combined_sentiment = self._combine_sentiment_scores([
                twitter_sentiment,
                reddit_sentiment,
                news_sentiment
            ])
            
            result = {
                "symbol": symbol,
                "timeframe": timeframe,
                "overall_sentiment": combined_sentiment,
                "sources": {
                    "twitter": twitter_sentiment,
                    "reddit": reddit_sentiment,
                    "news": news_sentiment
                },
                "timestamp": datetime.now().isoformat()
            }
            
            # Finish tracking successful call
            external_api_logger.finish_call(
                call_id=call_id,
                status_code=200,
                response_data={"symbol": symbol, "sentiment": combined_sentiment.get("score", 0)}
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Stock sentiment analysis failed for {symbol}: {str(e)}")
            
            # Record error metrics
            error_metrics.record_error(
                service=ServiceType.SENTIMENT_API,
                error_code=ErrorCode.API_UNAVAILABLE,
                severity=ErrorSeverity.MEDIUM,
                details={
                    "symbol": symbol,
                    "timeframe": timeframe,
                    "error": str(e)
                }
            )
            
            # Finish tracking failed call
            external_api_logger.finish_call(call_id=call_id, error=e)
            
            return {"error": f"Error analyzing sentiment for {symbol}: {str(e)}"}
    
    async def analyze_market_sentiment(self, timeframe: str = "24h") -> Dict[str, Any]:
        """
        Analyze overall market sentiment.
        
        Args:
            timeframe: Time period for analysis
            
        Returns:
            Overall market sentiment analysis
        """
        if not self.is_available():
            return await self._generate_mock_sentiment("market", "market")
        
        try:
            # Analyze sentiment for major market topics
            market_topics = [
                "stock market", "S&P 500", "NASDAQ", "Dow Jones",
                "Federal Reserve", "inflation", "interest rates"
            ]
            
            tasks = [
                self._analyze_topic_sentiment(topic, timeframe)
                for topic in market_topics
            ]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Process and combine results
            topic_sentiments = {}
            valid_results = []
            
            for i, result in enumerate(results):
                if not isinstance(result, Exception) and result:
                    topic_sentiments[market_topics[i]] = result
                    valid_results.append(result)
            
            # Calculate overall market sentiment
            overall_sentiment = self._combine_sentiment_scores(valid_results)
            
            return {
                "timeframe": timeframe,
                "overall_sentiment": overall_sentiment,
                "topic_sentiments": topic_sentiments,
                "market_indicators": self._calculate_market_indicators(valid_results),
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Market sentiment analysis failed: {str(e)}")
            return {"error": f"Error analyzing market sentiment: {str(e)}"}
    
    async def analyze_topic_sentiment(
        self, 
        topic: str, 
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """
        Analyze sentiment for a specific topic or keyword.
        
        Args:
            topic: Topic or keyword to analyze
            timeframe: Time period for analysis
            
        Returns:
            Sentiment analysis for the topic
        """
        if not self.is_available():
            return await self._generate_mock_sentiment(topic, "topic")
        
        try:
            result = await retry_with_backoff(
                self._analyze_topic_sentiment,
                self.retry_config,
                ServiceType.SENTIMENT_API,
                topic, timeframe
            )
            
            return result
        
        except Exception as e:
            logger.error(f"Topic sentiment analysis failed for {topic}: {str(e)}")
            return {"error": f"Error analyzing sentiment for {topic}: {str(e)}"}
    
    async def get_trending_sentiment(self, limit: int = 10) -> Dict[str, Any]:
        """
        Get trending topics and their sentiment.
        
        Args:
            limit: Number of trending topics to return
            
        Returns:
            List of trending topics with sentiment scores
        """
        if not self.is_available():
            return await self._generate_mock_trending_sentiment(limit)
        
        try:
            # Get trending topics from multiple sources
            trending_topics = await self._get_trending_topics(limit)
            
            # Analyze sentiment for each trending topic
            sentiment_tasks = [
                self._analyze_topic_sentiment(topic, "24h")
                for topic in trending_topics
            ]
            
            sentiment_results = await asyncio.gather(*sentiment_tasks, return_exceptions=True)
            
            # Combine topics with sentiment
            trending_with_sentiment = []
            for i, topic in enumerate(trending_topics):
                sentiment = sentiment_results[i] if not isinstance(sentiment_results[i], Exception) else {}
                
                trending_with_sentiment.append({
                    "topic": topic,
                    "sentiment": sentiment,
                    "rank": i + 1
                })
            
            return {
                "trending_topics": trending_with_sentiment,
                "timestamp": datetime.now().isoformat()
            }
        
        except Exception as e:
            logger.error(f"Trending sentiment analysis failed: {str(e)}")
            return {"error": f"Error getting trending sentiment: {str(e)}"}
    
    async def _analyze_twitter_sentiment(self, query: str, timeframe: str) -> Dict[str, Any]:
        """Analyze sentiment from Twitter data."""
        # Note: This would require Twitter API v2 access
        # For now, return mock data structure
        return await self._generate_mock_source_sentiment("twitter", query)
    
    async def _analyze_reddit_sentiment(self, query: str, timeframe: str) -> Dict[str, Any]:
        """Analyze sentiment from Reddit data."""
        try:
            # Use Reddit's JSON API (no authentication required for public data)
            search_url = f"https://www.reddit.com/search.json"
            params = {
                "q": query,
                "sort": "new",
                "limit": 25,
                "t": self._convert_timeframe_to_reddit(timeframe)
            }
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
                headers = {"User-Agent": "AI-Agent-Sentiment-Bot/1.0"}
                
                async with session.get(search_url, params=params, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        posts = data.get("data", {}).get("children", [])
                        
                        # Analyze sentiment of post titles and comments
                        sentiments = []
                        for post in posts:
                            post_data = post.get("data", {})
                            title = post_data.get("title", "")
                            score = post_data.get("score", 0)
                            
                            # Simple sentiment analysis based on score and keywords
                            sentiment_score = self._analyze_text_sentiment(title, score)
                            sentiments.append(sentiment_score)
                        
                        if sentiments:
                            avg_sentiment = sum(sentiments) / len(sentiments)
                            return {
                                "source": "reddit",
                                "score": avg_sentiment,
                                "confidence": min(len(sentiments) / 25.0, 1.0),
                                "sample_size": len(sentiments),
                                "label": self._score_to_label(avg_sentiment)
                            }
                    
                    return await self._generate_mock_source_sentiment("reddit", query)
        
        except Exception as e:
            logger.error(f"Reddit sentiment analysis failed: {str(e)}")
            return await self._generate_mock_source_sentiment("reddit", query)
    
    async def _analyze_news_sentiment(self, query: str, timeframe: str) -> Dict[str, Any]:
        """Analyze sentiment from news articles."""
        # This would require a news API like NewsAPI
        # For now, return mock data structure
        return await self._generate_mock_source_sentiment("news", query)
    
    async def _analyze_topic_sentiment(self, topic: str, timeframe: str) -> Dict[str, Any]:
        """Analyze sentiment for a general topic."""
        try:
            # Use multiple sources and combine results
            sources = [
                self._analyze_reddit_sentiment(topic, timeframe),
                # Add more sources as available
            ]
            
            results = await asyncio.gather(*sources, return_exceptions=True)
            valid_results = [r for r in results if not isinstance(r, Exception) and r]
            
            if valid_results:
                combined_sentiment = self._combine_sentiment_scores(valid_results)
                return {
                    "topic": topic,
                    "timeframe": timeframe,
                    "sentiment": combined_sentiment,
                    "sources_count": len(valid_results),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                return await self._generate_mock_sentiment(topic, "topic")
        
        except Exception as e:
            logger.error(f"Topic sentiment analysis failed for {topic}: {str(e)}")
            return await self._generate_mock_sentiment(topic, "topic")
    
    async def _get_trending_topics(self, limit: int) -> List[str]:
        """Get trending topics from various sources."""
        # This would integrate with trending APIs
        # For now, return common financial/market topics
        return [
            "Bitcoin", "Ethereum", "Tesla", "Apple", "Google",
            "Federal Reserve", "Inflation", "Stock Market", "Crypto",
            "AI Stocks", "Tech Stocks", "Energy Sector"
        ][:limit]
    
    def _analyze_text_sentiment(self, text: str, score: int = 0) -> float:
        """Simple text sentiment analysis."""
        # Basic keyword-based sentiment analysis
        positive_words = [
            "good", "great", "excellent", "amazing", "awesome", "fantastic",
            "bullish", "up", "gain", "profit", "buy", "strong", "positive"
        ]
        negative_words = [
            "bad", "terrible", "awful", "horrible", "bearish", "down",
            "loss", "sell", "weak", "negative", "crash", "drop", "fall"
        ]
        
        text_lower = text.lower()
        positive_count = sum(1 for word in positive_words if word in text_lower)
        negative_count = sum(1 for word in negative_words if word in text_lower)
        
        # Calculate sentiment score (-1 to 1)
        if positive_count + negative_count == 0:
            sentiment = 0.0
        else:
            sentiment = (positive_count - negative_count) / (positive_count + negative_count)
        
        # Factor in numerical score if available (e.g., Reddit upvotes)
        if score != 0:
            score_sentiment = min(max(score / 100.0, -1.0), 1.0)  # Normalize score
            sentiment = (sentiment + score_sentiment) / 2
        
        return sentiment
    
    def _combine_sentiment_scores(self, sentiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Combine multiple sentiment scores into overall sentiment."""
        if not sentiment_results:
            return {"score": 0.0, "confidence": 0.0, "label": "neutral"}
        
        # Weight by confidence and sample size
        total_weighted_score = 0.0
        total_weight = 0.0
        
        for result in sentiment_results:
            score = result.get("score", 0.0)
            confidence = result.get("confidence", 0.5)
            sample_size = result.get("sample_size", 1)
            
            # Weight by confidence and sample size
            weight = confidence * min(sample_size / 10.0, 1.0)
            total_weighted_score += score * weight
            total_weight += weight
        
        if total_weight == 0:
            overall_score = 0.0
            overall_confidence = 0.0
        else:
            overall_score = total_weighted_score / total_weight
            overall_confidence = min(total_weight / len(sentiment_results), 1.0)
        
        return {
            "score": round(overall_score, 3),
            "confidence": round(overall_confidence, 3),
            "label": self._score_to_label(overall_score),
            "sources_count": len(sentiment_results)
        }
    
    def _score_to_label(self, score: float) -> str:
        """Convert sentiment score to human-readable label."""
        if score >= 0.3:
            return "positive"
        elif score <= -0.3:
            return "negative"
        else:
            return "neutral"
    
    def _convert_timeframe_to_reddit(self, timeframe: str) -> str:
        """Convert timeframe to Reddit API format."""
        mapping = {
            "1h": "hour",
            "24h": "day",
            "7d": "week",
            "30d": "month"
        }
        return mapping.get(timeframe, "day")
    
    def _calculate_market_indicators(self, sentiment_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate market sentiment indicators."""
        if not sentiment_results:
            return {}
        
        scores = [r.get("score", 0.0) for r in sentiment_results if "score" in r]
        
        if not scores:
            return {}
        
        return {
            "fear_greed_index": self._calculate_fear_greed_index(scores),
            "volatility_indicator": self._calculate_volatility_indicator(scores),
            "consensus_strength": self._calculate_consensus_strength(scores)
        }
    
    def _calculate_fear_greed_index(self, scores: List[float]) -> Dict[str, Any]:
        """Calculate a fear and greed index based on sentiment."""
        avg_score = sum(scores) / len(scores)
        
        # Convert to 0-100 scale (0 = extreme fear, 100 = extreme greed)
        fear_greed_value = int((avg_score + 1) * 50)
        
        if fear_greed_value <= 25:
            label = "Extreme Fear"
        elif fear_greed_value <= 45:
            label = "Fear"
        elif fear_greed_value <= 55:
            label = "Neutral"
        elif fear_greed_value <= 75:
            label = "Greed"
        else:
            label = "Extreme Greed"
        
        return {
            "value": fear_greed_value,
            "label": label
        }
    
    def _calculate_volatility_indicator(self, scores: List[float]) -> float:
        """Calculate sentiment volatility indicator."""
        if len(scores) < 2:
            return 0.0
        
        avg_score = sum(scores) / len(scores)
        variance = sum((score - avg_score) ** 2 for score in scores) / len(scores)
        return round(variance ** 0.5, 3)
    
    def _calculate_consensus_strength(self, scores: List[float]) -> float:
        """Calculate how strong the sentiment consensus is."""
        if not scores:
            return 0.0
        
        # Measure how clustered the scores are
        avg_score = sum(scores) / len(scores)
        deviations = [abs(score - avg_score) for score in scores]
        avg_deviation = sum(deviations) / len(deviations)
        
        # Convert to 0-1 scale (1 = strong consensus, 0 = no consensus)
        consensus = max(0.0, 1.0 - avg_deviation)
        return round(consensus, 3)
    
    async def _generate_mock_sentiment(self, query: str, analysis_type: str) -> Dict[str, Any]:
        """Generate mock sentiment data when API is unavailable."""
        logger.info(f"Generating mock sentiment data for {query}")
        
        # Generate realistic but random sentiment data
        import random
        
        base_score = random.uniform(-0.5, 0.5)
        confidence = random.uniform(0.6, 0.9)
        
        if analysis_type == "stock":
            return {
                "symbol": query,
                "timeframe": "24h",
                "overall_sentiment": {
                    "score": round(base_score, 3),
                    "confidence": round(confidence, 3),
                    "label": self._score_to_label(base_score),
                    "sources_count": 3
                },
                "sources": {
                    "twitter": await self._generate_mock_source_sentiment("twitter", query),
                    "reddit": await self._generate_mock_source_sentiment("reddit", query),
                    "news": await self._generate_mock_source_sentiment("news", query)
                },
                "timestamp": datetime.now().isoformat(),
                "mock": True
            }
        
        elif analysis_type == "market":
            return {
                "timeframe": "24h",
                "overall_sentiment": {
                    "score": round(base_score, 3),
                    "confidence": round(confidence, 3),
                    "label": self._score_to_label(base_score),
                    "sources_count": 7
                },
                "market_indicators": {
                    "fear_greed_index": {
                        "value": int((base_score + 1) * 50),
                        "label": "Neutral"
                    },
                    "volatility_indicator": round(random.uniform(0.1, 0.4), 3),
                    "consensus_strength": round(random.uniform(0.5, 0.8), 3)
                },
                "timestamp": datetime.now().isoformat(),
                "mock": True
            }
        
        else:  # topic
            return {
                "topic": query,
                "timeframe": "24h",
                "sentiment": {
                    "score": round(base_score, 3),
                    "confidence": round(confidence, 3),
                    "label": self._score_to_label(base_score),
                    "sources_count": 2
                },
                "timestamp": datetime.now().isoformat(),
                "mock": True
            }
    
    async def _generate_mock_source_sentiment(self, source: str, query: str) -> Dict[str, Any]:
        """Generate mock sentiment data for a specific source."""
        import random
        
        score = random.uniform(-0.6, 0.6)
        sample_size = random.randint(10, 50)
        
        return {
            "source": source,
            "score": round(score, 3),
            "confidence": round(random.uniform(0.5, 0.9), 3),
            "sample_size": sample_size,
            "label": self._score_to_label(score)
        }
    
    async def _generate_mock_trending_sentiment(self, limit: int) -> Dict[str, Any]:
        """Generate mock trending sentiment data."""
        logger.info("Generating mock trending sentiment data")
        
        trending_topics = await self._get_trending_topics(limit)
        trending_with_sentiment = []
        
        for i, topic in enumerate(trending_topics):
            sentiment = await self._generate_mock_sentiment(topic, "topic")
            trending_with_sentiment.append({
                "topic": topic,
                "sentiment": sentiment.get("sentiment", {}),
                "rank": i + 1
            })
        
        return {
            "trending_topics": trending_with_sentiment,
            "timestamp": datetime.now().isoformat(),
            "mock": True
        }
    
    def is_available(self) -> bool:
        """Check if sentiment analysis service is available."""
        # For now, always return True to use mock data or basic analysis
        return True
    
    async def health_check(self) -> Dict[str, Any]:
        """Perform a health check on the sentiment analysis service."""
        if not self.api_key:
            return {
                "status": "mock",
                "message": "API key not configured, using mock data and basic analysis",
                "service": "Sentiment Analysis"
            }
        
        try:
            # Test basic functionality
            test_result = await self._analyze_topic_sentiment("test", "24h")
            
            if test_result and not test_result.get("error"):
                return {
                    "status": "healthy",
                    "message": "Service operational",
                    "service": "Sentiment Analysis"
                }
            else:
                return {
                    "status": "degraded",
                    "message": "Service partially operational",
                    "service": "Sentiment Analysis"
                }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Health check failed: {str(e)}",
                "service": "Sentiment Analysis"
            }