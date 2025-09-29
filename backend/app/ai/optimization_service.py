"""
Advanced AI Model Management and Optimization Service

This service provides:
1. Dynamic model selection based on query complexity
2. Model performance monitoring and automatic fallback triggers
3. Cost optimization features for API usage tracking
4. Model response quality assessment and feedback loops
"""

import asyncio
import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import hashlib
from collections import defaultdict, deque

from ..config import settings
from .models import AIModel, ChatMessage, StreamChunk
from .service import AIService

logger = logging.getLogger(__name__)


class QueryComplexity(Enum):
    """Query complexity levels for model selection"""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class ModelTier(Enum):
    """Model performance tiers"""
    FAST = "fast"          # Quick responses, lower quality
    BALANCED = "balanced"  # Good balance of speed and quality
    PREMIUM = "premium"    # High quality, slower responses
    EXPERT = "expert"      # Specialized models for complex tasks


@dataclass
class ModelPerformanceMetrics:
    """Performance metrics for a model"""
    model_id: str
    total_requests: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    avg_response_time: float = 0.0
    avg_tokens_per_request: int = 0
    total_cost: float = 0.0
    quality_score: float = 0.0
    last_used: Optional[datetime] = None
    error_rate: float = 0.0
    availability_score: float = 1.0


@dataclass
class QueryAnalysis:
    """Analysis of a user query"""
    complexity: QueryComplexity
    domain: str
    requires_real_time_data: bool
    estimated_tokens: int
    confidence: float
    reasoning: str


@dataclass
class ModelRecommendation:
    """Model recommendation with reasoning"""
    model_id: str
    confidence: float
    reasoning: str
    estimated_cost: float
    estimated_response_time: float
    tier: ModelTier


class AIOptimizationService:
    """Advanced AI model management and optimization service"""
    
    def __init__(self, ai_service: AIService):
        self.ai_service = ai_service
        
        # Performance tracking
        self.model_metrics: Dict[str, ModelPerformanceMetrics] = {}
        self.recent_responses: deque = deque(maxlen=1000)  # Last 1000 responses for analysis
        
        # Model configuration
        self.model_tiers = self._initialize_model_tiers()
        self.cost_per_token = self._initialize_cost_mapping()
        
        # Query analysis patterns
        self.complexity_patterns = self._initialize_complexity_patterns()
        self.domain_patterns = self._initialize_domain_patterns()
        
        # Optimization settings
        self.fallback_threshold = 0.7  # Availability threshold for fallback
        self.quality_threshold = 0.6   # Minimum quality score
        self.cost_optimization_enabled = True
        self.performance_monitoring_enabled = True
        
        logger.info("AI Optimization Service initialized")
    
    def _initialize_model_tiers(self) -> Dict[str, ModelTier]:
        """Initialize model tier mappings"""
        return {
            # Fast tier - quick responses
            "gpt-4o-mini": ModelTier.FAST,
            "claude-3-5-haiku-20241022": ModelTier.FAST,
            "llama-3.1-8b-instant": ModelTier.FAST,
            
            # Balanced tier - good performance/cost ratio
            "gpt-4o": ModelTier.BALANCED,
            "llama-3.1-70b-versatile": ModelTier.BALANCED,
            "mixtral-8x7b-32768": ModelTier.BALANCED,
            
            # Premium tier - high quality
            "gpt-4": ModelTier.PREMIUM,
            "claude-3-5-sonnet-20241022": ModelTier.PREMIUM,
            "claude-3-opus-20240229": ModelTier.PREMIUM,
            
            # Expert tier - specialized models
            "gpt-4-turbo": ModelTier.EXPERT,
            "claude-3-5-sonnet-20241022": ModelTier.EXPERT,
        }
    
    def _initialize_cost_mapping(self) -> Dict[str, Dict[str, float]]:
        """Initialize cost per token mappings (input/output)"""
        return {
            # OpenAI models (per 1K tokens)
            "gpt-4o": {"input": 0.005, "output": 0.015},
            "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            
            # Anthropic models (per 1K tokens)
            "claude-3-5-sonnet-20241022": {"input": 0.003, "output": 0.015},
            "claude-3-5-haiku-20241022": {"input": 0.00025, "output": 0.00125},
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015},
            "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
            
            # Groq models (often free or very low cost)
            "llama-3.1-70b-versatile": {"input": 0.0001, "output": 0.0001},
            "llama-3.1-8b-instant": {"input": 0.00005, "output": 0.00005},
            "mixtral-8x7b-32768": {"input": 0.0001, "output": 0.0001},
        }
    
    def _initialize_complexity_patterns(self) -> Dict[QueryComplexity, List[str]]:
        """Initialize patterns for query complexity detection"""
        return {
            QueryComplexity.SIMPLE: [
                r'\b(hello|hi|hey|thanks|thank you)\b',
                r'\b(what is|define|meaning of)\b',
                r'\b(yes|no|maybe|ok|okay)\b',
                r'^.{1,20}$',  # Very short queries
            ],
            QueryComplexity.MODERATE: [
                r'\b(explain|describe|how to|why|when|where)\b',
                r'\b(compare|difference|similar|versus|vs)\b',
                r'\b(list|examples|steps|process)\b',
                r'^.{21,100}$',  # Medium length queries
            ],
            QueryComplexity.COMPLEX: [
                r'\b(analyze|evaluate|assess|critique|review)\b',
                r'\b(strategy|approach|methodology|framework)\b',
                r'\b(pros and cons|advantages|disadvantages)\b',
                r'\b(implement|develop|create|design|build)\b',
                r'^.{101,300}$',  # Longer queries
            ],
            QueryComplexity.EXPERT: [
                r'\b(optimize|algorithm|architecture|performance)\b',
                r'\b(research|academic|scientific|technical)\b',
                r'\b(comprehensive|detailed|thorough|in-depth)\b',
                r'\b(multi-step|complex|advanced|sophisticated)\b',
                r'^.{301,}$',  # Very long queries
            ]
        }
    
    def _initialize_domain_patterns(self) -> Dict[str, List[str]]:
        """Initialize patterns for domain detection"""
        return {
            "coding": [
                r'\b(code|programming|function|class|variable|algorithm)\b',
                r'\b(python|javascript|java|c\+\+|html|css|sql)\b',
                r'\b(debug|error|exception|syntax|compile)\b',
            ],
            "business": [
                r'\b(strategy|marketing|sales|revenue|profit|business)\b',
                r'\b(management|leadership|team|project|planning)\b',
                r'\b(analysis|metrics|kpi|roi|growth)\b',
            ],
            "creative": [
                r'\b(write|story|poem|creative|art|design|music)\b',
                r'\b(brainstorm|idea|concept|inspiration|imagination)\b',
                r'\b(novel|script|lyrics|painting|drawing)\b',
            ],
            "technical": [
                r'\b(system|architecture|infrastructure|database|server)\b',
                r'\b(api|protocol|network|security|encryption)\b',
                r'\b(performance|optimization|scalability|deployment)\b',
            ],
            "research": [
                r'\b(research|study|analysis|data|statistics|findings)\b',
                r'\b(hypothesis|methodology|experiment|survey|report)\b',
                r'\b(academic|scientific|peer-reviewed|publication)\b',
            ],
            "general": []  # Default fallback
        }
    
    async def analyze_query(self, message: str, context: Dict[str, Any] = None) -> QueryAnalysis:
        """Analyze query complexity and characteristics"""
        message_lower = message.lower()
        
        # Determine complexity
        complexity_scores = {}
        for complexity, patterns in self.complexity_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            complexity_scores[complexity] = score
        
        # Get highest scoring complexity
        complexity = max(complexity_scores, key=complexity_scores.get)
        confidence = complexity_scores[complexity] / len(self.complexity_patterns[complexity])
        
        # Determine domain
        domain_scores = {}
        for domain, patterns in self.domain_patterns.items():
            score = 0
            for pattern in patterns:
                if re.search(pattern, message_lower):
                    score += 1
            domain_scores[domain] = score
        
        domain = max(domain_scores, key=domain_scores.get) if max(domain_scores.values()) > 0 else "general"
        
        # Check if requires real-time data
        real_time_patterns = [
            r'\b(current|latest|recent|now|today|trending)\b',
            r'\b(news|price|weather|stock|market)\b',
            r'\b(what\'s happening|update|status)\b'
        ]
        requires_real_time_data = any(re.search(pattern, message_lower) for pattern in real_time_patterns)
        
        # Estimate tokens (rough approximation)
        estimated_tokens = len(message.split()) * 1.3  # Account for tokenization
        
        # Build reasoning
        reasoning_parts = [
            f"Length: {len(message)} chars",
            f"Complexity indicators: {complexity_scores[complexity]}",
            f"Domain: {domain}",
            f"Real-time data needed: {requires_real_time_data}"
        ]
        reasoning = "; ".join(reasoning_parts)
        
        return QueryAnalysis(
            complexity=complexity,
            domain=domain,
            requires_real_time_data=requires_real_time_data,
            estimated_tokens=int(estimated_tokens),
            confidence=confidence,
            reasoning=reasoning
        )
    
    async def recommend_model(self, query_analysis: QueryAnalysis, 
                            available_models: List[AIModel],
                            user_preferences: Dict[str, Any] = None) -> ModelRecommendation:
        """Recommend the best model based on query analysis and current performance"""
        
        if not available_models:
            raise ValueError("No available models provided")
        
        user_preferences = user_preferences or {}
        priority = user_preferences.get("priority", "balanced")  # "speed", "quality", "cost", "balanced"
        
        # Filter models by availability and performance
        viable_models = []
        for model in available_models:
            if not model.available:
                continue
                
            metrics = self.model_metrics.get(model.id)
            if metrics and metrics.availability_score < self.fallback_threshold:
                continue
                
            viable_models.append(model)
        
        if not viable_models:
            # Fallback to any available model
            viable_models = [m for m in available_models if m.available]
            if not viable_models:
                raise ValueError("No viable models available")
        
        # Score models based on query requirements
        model_scores = []
        for model in viable_models:
            score = await self._score_model_for_query(model, query_analysis, priority)
            model_scores.append((model, score))
        
        # Sort by score (highest first)
        model_scores.sort(key=lambda x: x[1]["total_score"], reverse=True)
        
        best_model, best_score = model_scores[0]
        
        return ModelRecommendation(
            model_id=best_model.id,
            confidence=best_score["confidence"],
            reasoning=best_score["reasoning"],
            estimated_cost=best_score["estimated_cost"],
            estimated_response_time=best_score["estimated_response_time"],
            tier=self.model_tiers.get(best_model.id, ModelTier.BALANCED)
        )
    
    async def _score_model_for_query(self, model: AIModel, query_analysis: QueryAnalysis, 
                                   priority: str) -> Dict[str, Any]:
        """Score a model's suitability for a specific query"""
        
        metrics = self.model_metrics.get(model.id, ModelPerformanceMetrics(model.id))
        tier = self.model_tiers.get(model.id, ModelTier.BALANCED)
        
        # Base scores
        scores = {
            "performance": 0.0,
            "cost": 0.0,
            "speed": 0.0,
            "quality": 0.0,
            "availability": 0.0
        }
        
        # Performance score based on historical data
        if metrics.total_requests > 0:
            scores["performance"] = (metrics.successful_requests / metrics.total_requests) * 100
            scores["quality"] = metrics.quality_score * 100
            scores["availability"] = metrics.availability_score * 100
        else:
            # Default scores for new models
            scores["performance"] = 80.0
            scores["quality"] = 70.0
            scores["availability"] = 90.0
        
        # Speed score (inverse of response time)
        if metrics.avg_response_time > 0:
            # Normalize response time (assume 10s is very slow, 1s is very fast)
            normalized_time = min(metrics.avg_response_time / 10.0, 1.0)
            scores["speed"] = (1.0 - normalized_time) * 100
        else:
            # Default based on tier
            speed_defaults = {
                ModelTier.FAST: 90.0,
                ModelTier.BALANCED: 70.0,
                ModelTier.PREMIUM: 50.0,
                ModelTier.EXPERT: 40.0
            }
            scores["speed"] = speed_defaults.get(tier, 70.0)
        
        # Adjust quality score based on tier
        tier_quality_bonus = {
            ModelTier.FAST: 0.0,
            ModelTier.BALANCED: 10.0,
            ModelTier.PREMIUM: 25.0,
            ModelTier.EXPERT: 35.0
        }
        scores["quality"] += tier_quality_bonus.get(tier, 0.0)
        
        # Cost score (lower cost = higher score)
        cost_info = self.cost_per_token.get(model.id, {"input": 0.001, "output": 0.001})
        avg_cost_per_token = (cost_info["input"] + cost_info["output"]) / 2
        estimated_cost = avg_cost_per_token * query_analysis.estimated_tokens / 1000
        
        # Normalize cost (assume $0.1 per request is expensive, $0.001 is cheap)
        normalized_cost = min(estimated_cost / 0.1, 1.0)
        scores["cost"] = (1.0 - normalized_cost) * 100
        
        # Adjust scores based on query complexity and domain
        complexity_adjustments = {
            QueryComplexity.SIMPLE: {"speed": 1.2, "cost": 1.3, "quality": 0.8},
            QueryComplexity.MODERATE: {"speed": 1.0, "cost": 1.0, "quality": 1.0},
            QueryComplexity.COMPLEX: {"speed": 0.8, "cost": 0.9, "quality": 1.2},
            QueryComplexity.EXPERT: {"speed": 0.6, "cost": 0.7, "quality": 1.4}
        }
        
        adjustments = complexity_adjustments.get(query_analysis.complexity, {})
        for score_type, adjustment in adjustments.items():
            scores[score_type] *= adjustment
        
        # Apply priority weighting
        priority_weights = {
            "speed": {"speed": 0.4, "performance": 0.3, "availability": 0.2, "quality": 0.05, "cost": 0.05},
            "quality": {"quality": 0.4, "performance": 0.3, "availability": 0.2, "speed": 0.05, "cost": 0.05},
            "cost": {"cost": 0.4, "performance": 0.3, "availability": 0.2, "speed": 0.05, "quality": 0.05},
            "balanced": {"performance": 0.25, "quality": 0.25, "speed": 0.2, "cost": 0.15, "availability": 0.15}
        }
        
        weights = priority_weights.get(priority, priority_weights["balanced"])
        
        # Calculate weighted total score
        total_score = sum(scores[key] * weights[key] for key in scores)
        
        # Calculate confidence based on data availability
        confidence = min(metrics.total_requests / 100.0, 1.0) if metrics.total_requests > 0 else 0.5
        
        # Build reasoning
        reasoning_parts = [
            f"Tier: {tier.value}",
            f"Performance: {scores['performance']:.1f}",
            f"Quality: {scores['quality']:.1f}",
            f"Speed: {scores['speed']:.1f}",
            f"Cost: {scores['cost']:.1f}",
            f"Priority: {priority}"
        ]
        reasoning = "; ".join(reasoning_parts)
        
        return {
            "total_score": total_score,
            "individual_scores": scores,
            "confidence": confidence,
            "reasoning": reasoning,
            "estimated_cost": estimated_cost,
            "estimated_response_time": metrics.avg_response_time or self._estimate_response_time(tier)
        }
    
    def _estimate_response_time(self, tier: ModelTier) -> float:
        """Estimate response time based on model tier"""
        estimates = {
            ModelTier.FAST: 2.0,
            ModelTier.BALANCED: 4.0,
            ModelTier.PREMIUM: 8.0,
            ModelTier.EXPERT: 12.0
        }
        return estimates.get(tier, 5.0)
    
    async def track_model_performance(self, model_id: str, response_time: float, 
                                    success: bool, tokens_used: int, cost: float,
                                    quality_score: Optional[float] = None):
        """Track model performance metrics"""
        
        if not self.performance_monitoring_enabled:
            return
        
        if model_id not in self.model_metrics:
            self.model_metrics[model_id] = ModelPerformanceMetrics(model_id)
        
        metrics = self.model_metrics[model_id]
        
        # Update counters
        metrics.total_requests += 1
        if success:
            metrics.successful_requests += 1
        else:
            metrics.failed_requests += 1
        
        # Update averages
        metrics.avg_response_time = (
            (metrics.avg_response_time * (metrics.total_requests - 1) + response_time) 
            / metrics.total_requests
        )
        
        metrics.avg_tokens_per_request = (
            (metrics.avg_tokens_per_request * (metrics.total_requests - 1) + tokens_used)
            / metrics.total_requests
        )
        
        # Update cost
        metrics.total_cost += cost
        
        # Update quality score if provided
        if quality_score is not None:
            if metrics.quality_score == 0.0:
                metrics.quality_score = quality_score
            else:
                # Exponential moving average
                metrics.quality_score = 0.8 * metrics.quality_score + 0.2 * quality_score
        
        # Update error rate
        metrics.error_rate = metrics.failed_requests / metrics.total_requests
        
        # Update availability score (exponential moving average)
        availability_update = 1.0 if success else 0.0
        metrics.availability_score = 0.9 * metrics.availability_score + 0.1 * availability_update
        
        # Update last used timestamp
        metrics.last_used = datetime.now()
        
        logger.debug(f"Updated metrics for {model_id}: success_rate={1-metrics.error_rate:.2f}, "
                    f"avg_time={metrics.avg_response_time:.2f}s, quality={metrics.quality_score:.2f}")
    
    async def assess_response_quality(self, query: str, response: str, 
                                    context: Dict[str, Any] = None) -> float:
        """Assess the quality of a model's response"""
        
        # Simple heuristic-based quality assessment
        # In a production system, this could use a dedicated quality model
        
        quality_score = 0.0
        max_score = 100.0
        
        # Length appropriateness (not too short, not too long)
        response_length = len(response)
        query_length = len(query)
        
        if response_length < 10:
            quality_score += 10  # Very short responses are usually poor
        elif response_length < query_length * 0.5:
            quality_score += 30  # Short but reasonable
        elif response_length < query_length * 3:
            quality_score += 50  # Good length ratio
        elif response_length < query_length * 10:
            quality_score += 40  # A bit long but okay
        else:
            quality_score += 20  # Too verbose
        
        # Coherence indicators
        sentences = response.split('.')
        if len(sentences) > 1:
            quality_score += 15  # Multi-sentence responses are usually better
        
        # Specific content indicators
        if any(word in response.lower() for word in ['because', 'therefore', 'however', 'additionally']):
            quality_score += 10  # Logical connectors indicate good structure
        
        if any(word in response.lower() for word in ['example', 'for instance', 'such as']):
            quality_score += 10  # Examples indicate thorough responses
        
        # Error indicators (negative scoring)
        if 'error' in response.lower() or 'sorry' in response.lower():
            quality_score -= 20
        
        if response.count('?') > 3:
            quality_score -= 10  # Too many questions might indicate confusion
        
        # Context utilization (if context was provided)
        if context:
            context_types = len(context.keys())
            if context_types > 0:
                # Check if response seems to use the context
                context_keywords = []
                for ctx_type, ctx_data in context.items():
                    if isinstance(ctx_data, dict) and 'results' in ctx_data:
                        for result in ctx_data['results'][:3]:  # Check first 3 results
                            if isinstance(result, dict) and 'title' in result:
                                context_keywords.extend(result['title'].lower().split()[:5])
                
                # Count how many context keywords appear in response
                response_lower = response.lower()
                context_usage = sum(1 for keyword in context_keywords if keyword in response_lower)
                quality_score += min(context_usage * 5, 15)  # Up to 15 points for context usage
        
        # Normalize to 0-1 scale
        return min(quality_score / max_score, 1.0)
    
    async def get_optimization_recommendations(self) -> Dict[str, Any]:
        """Get recommendations for optimizing AI model usage"""
        
        recommendations = {
            "cost_optimization": [],
            "performance_optimization": [],
            "quality_optimization": [],
            "general_recommendations": []
        }
        
        if not self.model_metrics:
            recommendations["general_recommendations"].append(
                "No usage data available yet. Start using the system to get personalized recommendations."
            )
            return recommendations
        
        # Analyze cost patterns
        total_cost = sum(metrics.total_cost for metrics in self.model_metrics.values())
        if total_cost > 0:
            # Find most expensive models
            expensive_models = sorted(
                [(model_id, metrics.total_cost) for model_id, metrics in self.model_metrics.items()],
                key=lambda x: x[1], reverse=True
            )[:3]
            
            for model_id, cost in expensive_models:
                if cost > total_cost * 0.3:  # If model accounts for >30% of costs
                    recommendations["cost_optimization"].append(
                        f"Consider using cheaper alternatives to {model_id} for simple queries (current cost: ${cost:.2f})"
                    )
        
        # Analyze performance patterns
        for model_id, metrics in self.model_metrics.items():
            if metrics.total_requests > 10:  # Only analyze models with sufficient data
                
                # Poor availability
                if metrics.availability_score < 0.8:
                    recommendations["performance_optimization"].append(
                        f"{model_id} has low availability ({metrics.availability_score:.1%}). Consider using fallback models."
                    )
                
                # Slow response times
                if metrics.avg_response_time > 10.0:
                    recommendations["performance_optimization"].append(
                        f"{model_id} has slow response times ({metrics.avg_response_time:.1f}s). Consider faster alternatives for simple queries."
                    )
                
                # Poor quality
                if metrics.quality_score < 0.6:
                    recommendations["quality_optimization"].append(
                        f"{model_id} has low quality scores ({metrics.quality_score:.1%}). Consider using higher-tier models for important queries."
                    )
        
        # General recommendations
        total_requests = sum(metrics.total_requests for metrics in self.model_metrics.values())
        if total_requests > 100:
            # Usage pattern analysis
            most_used = max(self.model_metrics.items(), key=lambda x: x[1].total_requests)
            recommendations["general_recommendations"].append(
                f"Most used model: {most_used[0]} ({most_used[1].total_requests} requests)"
            )
            
            # Efficiency recommendations
            if self.cost_optimization_enabled:
                recommendations["general_recommendations"].append(
                    "Cost optimization is enabled. The system will automatically choose cost-effective models when possible."
                )
        
        return recommendations
    
    async def get_model_analytics(self) -> Dict[str, Any]:
        """Get comprehensive analytics about model usage"""
        
        if not self.model_metrics:
            return {"message": "No analytics data available yet"}
        
        analytics = {
            "summary": {},
            "model_performance": {},
            "cost_analysis": {},
            "usage_patterns": {}
        }
        
        # Summary statistics
        total_requests = sum(metrics.total_requests for metrics in self.model_metrics.values())
        total_cost = sum(metrics.total_cost for metrics in self.model_metrics.values())
        avg_quality = sum(metrics.quality_score for metrics in self.model_metrics.values()) / len(self.model_metrics)
        
        analytics["summary"] = {
            "total_requests": total_requests,
            "total_models_used": len(self.model_metrics),
            "total_cost": round(total_cost, 4),
            "average_quality_score": round(avg_quality, 3),
            "data_collection_period": "Last 30 days"  # Assuming metrics are from last 30 days
        }
        
        # Model performance details
        for model_id, metrics in self.model_metrics.items():
            analytics["model_performance"][model_id] = {
                "requests": metrics.total_requests,
                "success_rate": round((metrics.successful_requests / metrics.total_requests) * 100, 1) if metrics.total_requests > 0 else 0,
                "avg_response_time": round(metrics.avg_response_time, 2),
                "quality_score": round(metrics.quality_score, 3),
                "availability_score": round(metrics.availability_score, 3),
                "total_cost": round(metrics.total_cost, 4),
                "last_used": metrics.last_used.isoformat() if metrics.last_used else None
            }
        
        # Cost analysis
        if total_cost > 0:
            cost_by_model = {model_id: metrics.total_cost for model_id, metrics in self.model_metrics.items()}
            sorted_costs = sorted(cost_by_model.items(), key=lambda x: x[1], reverse=True)
            
            analytics["cost_analysis"] = {
                "most_expensive_models": sorted_costs[:5],
                "cost_per_request": round(total_cost / total_requests, 6) if total_requests > 0 else 0,
                "projected_monthly_cost": round(total_cost * 30, 2)  # Rough projection
            }
        
        # Usage patterns
        if total_requests > 0:
            usage_by_model = {model_id: metrics.total_requests for model_id, metrics in self.model_metrics.items()}
            sorted_usage = sorted(usage_by_model.items(), key=lambda x: x[1], reverse=True)
            
            analytics["usage_patterns"] = {
                "most_used_models": sorted_usage[:5],
                "usage_distribution": {model_id: round((requests / total_requests) * 100, 1) 
                                     for model_id, requests in sorted_usage}
            }
        
        return analytics
    
    def clear_metrics(self):
        """Clear all performance metrics (useful for testing or reset)"""
        self.model_metrics.clear()
        self.recent_responses.clear()
        logger.info("AI optimization metrics cleared")
    
    def export_metrics(self) -> Dict[str, Any]:
        """Export metrics for backup or analysis"""
        return {
            "model_metrics": {
                model_id: asdict(metrics) 
                for model_id, metrics in self.model_metrics.items()
            },
            "export_timestamp": datetime.now().isoformat(),
            "settings": {
                "fallback_threshold": self.fallback_threshold,
                "quality_threshold": self.quality_threshold,
                "cost_optimization_enabled": self.cost_optimization_enabled,
                "performance_monitoring_enabled": self.performance_monitoring_enabled
            }
        }
    
    def import_metrics(self, data: Dict[str, Any]):
        """Import metrics from backup"""
        if "model_metrics" in data:
            for model_id, metrics_dict in data["model_metrics"].items():
                # Convert datetime strings back to datetime objects
                if "last_used" in metrics_dict and metrics_dict["last_used"]:
                    metrics_dict["last_used"] = datetime.fromisoformat(metrics_dict["last_used"])
                
                self.model_metrics[model_id] = ModelPerformanceMetrics(**metrics_dict)
        
        if "settings" in data:
            settings = data["settings"]
            self.fallback_threshold = settings.get("fallback_threshold", self.fallback_threshold)
            self.quality_threshold = settings.get("quality_threshold", self.quality_threshold)
            self.cost_optimization_enabled = settings.get("cost_optimization_enabled", self.cost_optimization_enabled)
            self.performance_monitoring_enabled = settings.get("performance_monitoring_enabled", self.performance_monitoring_enabled)
        
        logger.info(f"Imported metrics for {len(self.model_metrics)} models")