"""
Comprehensive tests for AI Model Optimization Service

Tests cover:
1. Query complexity analysis
2. Dynamic model selection
3. Performance monitoring
4. Cost optimization
5. Quality assessment
6. API endpoints
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta
import json

from app.ai.optimization_service import (
    AIOptimizationService, QueryComplexity, ModelTier, 
    QueryAnalysis, ModelRecommendation, ModelPerformanceMetrics
)
from app.ai.enhanced_service import EnhancedAIService
from app.ai.models import AIModel, ChatMessage
from app.ai.service import AIService


class TestQueryAnalysis:
    """Test query complexity analysis"""
    
    @pytest.fixture
    def optimization_service(self):
        mock_ai_service = Mock(spec=AIService)
        return AIOptimizationService(mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_simple_query_analysis(self, optimization_service):
        """Test analysis of simple queries"""
        simple_queries = [
            "hello",
            "hi there",
            "what is AI?",
            "thanks"
        ]
        
        for query in simple_queries:
            analysis = await optimization_service.analyze_query(query)
            assert analysis.complexity == QueryComplexity.SIMPLE
            assert analysis.confidence > 0
            assert analysis.estimated_tokens > 0
    
    @pytest.mark.asyncio
    async def test_complex_query_analysis(self, optimization_service):
        """Test analysis of complex queries"""
        complex_queries = [
            "Analyze the pros and cons of different machine learning algorithms for natural language processing tasks",
            "Implement a comprehensive strategy for optimizing database performance in a distributed system",
            "Evaluate the effectiveness of various neural network architectures for computer vision applications"
        ]
        
        for query in complex_queries:
            analysis = await optimization_service.analyze_query(query)
            assert analysis.complexity in [QueryComplexity.COMPLEX, QueryComplexity.EXPERT]
            assert analysis.estimated_tokens > 20
    
    @pytest.mark.asyncio
    async def test_domain_detection(self, optimization_service):
        """Test domain detection in queries"""
        domain_queries = [
            ("Write a Python function to sort a list", "coding"),
            ("Create a marketing strategy for our product", "business"),
            ("Write a creative story about space exploration", "creative"),
            ("Design a scalable microservices architecture", "technical"),
            ("Conduct a research study on user behavior", "research")
        ]
        
        for query, expected_domain in domain_queries:
            analysis = await optimization_service.analyze_query(query)
            assert analysis.domain == expected_domain
    
    @pytest.mark.asyncio
    async def test_real_time_data_detection(self, optimization_service):
        """Test detection of queries requiring real-time data"""
        real_time_queries = [
            "What's the current Bitcoin price?",
            "Latest news about AI developments",
            "What's trending on social media today?",
            "Current weather in New York"
        ]
        
        static_queries = [
            "Explain machine learning concepts",
            "How to write clean code?",
            "History of computer science"
        ]
        
        for query in real_time_queries:
            analysis = await optimization_service.analyze_query(query)
            assert analysis.requires_real_time_data == True
        
        for query in static_queries:
            analysis = await optimization_service.analyze_query(query)
            assert analysis.requires_real_time_data == False


class TestModelRecommendation:
    """Test model recommendation system"""
    
    @pytest.fixture
    def optimization_service(self):
        mock_ai_service = Mock(spec=AIService)
        return AIOptimizationService(mock_ai_service)
    
    @pytest.fixture
    def sample_models(self):
        return [
            AIModel(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="openai",
                description="Fast and cost-effective model",
                max_tokens=4096,
                available=True
            ),
            AIModel(
                id="gpt-4",
                name="GPT-4",
                provider="openai",
                description="High-quality model",
                max_tokens=8192,
                available=True
            ),
            AIModel(
                id="llama-3.1-70b-versatile",
                name="Llama 3.1 70B",
                provider="groq",
                description="Versatile open-source model",
                max_tokens=8192,
                available=True
            )
        ]
    
    @pytest.mark.asyncio
    async def test_speed_priority_recommendation(self, optimization_service, sample_models):
        """Test model recommendation with speed priority"""
        query_analysis = QueryAnalysis(
            complexity=QueryComplexity.SIMPLE,
            domain="general",
            requires_real_time_data=False,
            estimated_tokens=10,
            confidence=0.8,
            reasoning="Simple query"
        )
        
        user_preferences = {"priority": "speed"}
        
        recommendation = await optimization_service.recommend_model(
            query_analysis, sample_models, user_preferences
        )
        
        assert recommendation.model_id in ["gpt-4o-mini", "llama-3.1-70b-versatile"]  # Fast models
        assert recommendation.confidence > 0
        assert recommendation.estimated_cost >= 0
    
    @pytest.mark.asyncio
    async def test_quality_priority_recommendation(self, optimization_service, sample_models):
        """Test model recommendation with quality priority"""
        query_analysis = QueryAnalysis(
            complexity=QueryComplexity.EXPERT,
            domain="technical",
            requires_real_time_data=False,
            estimated_tokens=100,
            confidence=0.9,
            reasoning="Expert technical query"
        )
        
        user_preferences = {"priority": "quality"}
        
        recommendation = await optimization_service.recommend_model(
            query_analysis, sample_models, user_preferences
        )
        
        assert recommendation.model_id == "gpt-4"  # Highest quality model
        assert recommendation.confidence > 0
    
    @pytest.mark.asyncio
    async def test_cost_priority_recommendation(self, optimization_service, sample_models):
        """Test model recommendation with cost priority"""
        query_analysis = QueryAnalysis(
            complexity=QueryComplexity.MODERATE,
            domain="general",
            requires_real_time_data=False,
            estimated_tokens=50,
            confidence=0.7,
            reasoning="Moderate query"
        )
        
        user_preferences = {"priority": "cost"}
        
        recommendation = await optimization_service.recommend_model(
            query_analysis, sample_models, user_preferences
        )
        
        # Should recommend the most cost-effective model
        assert recommendation.model_id in ["gpt-4o-mini", "llama-3.1-70b-versatile"]
        assert recommendation.estimated_cost < 0.1  # Should be relatively cheap


class TestPerformanceMonitoring:
    """Test performance monitoring and tracking"""
    
    @pytest.fixture
    def optimization_service(self):
        mock_ai_service = Mock(spec=AIService)
        return AIOptimizationService(mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_performance_tracking(self, optimization_service):
        """Test model performance tracking"""
        model_id = "gpt-4o"
        
        # Track several successful requests
        for i in range(5):
            await optimization_service.track_model_performance(
                model_id=model_id,
                response_time=2.0 + i * 0.5,
                success=True,
                tokens_used=100 + i * 10,
                cost=0.01 + i * 0.001
            )
        
        # Track one failed request
        await optimization_service.track_model_performance(
            model_id=model_id,
            response_time=10.0,
            success=False,
            tokens_used=0,
            cost=0.0
        )
        
        metrics = optimization_service.model_metrics[model_id]
        
        assert metrics.total_requests == 6
        assert metrics.successful_requests == 5
        assert metrics.failed_requests == 1
        assert metrics.error_rate == 1/6
        assert metrics.avg_response_time > 0
        assert metrics.total_cost > 0
    
    @pytest.mark.asyncio
    async def test_quality_assessment(self, optimization_service):
        """Test response quality assessment"""
        test_cases = [
            ("What is AI?", "Artificial Intelligence is a field of computer science that focuses on creating systems capable of performing tasks that typically require human intelligence.", 0.7),
            ("Hello", "Hi there!", 0.3),  # Too short
            ("Explain quantum computing", "Quantum computing is a revolutionary technology that uses quantum mechanical phenomena to process information. For example, quantum computers use qubits instead of classical bits.", 0.8)
        ]
        
        for query, response, expected_min_quality in test_cases:
            quality_score = await optimization_service.assess_response_quality(query, response)
            assert 0.0 <= quality_score <= 1.0
            if expected_min_quality:
                assert quality_score >= expected_min_quality - 0.2  # Allow some tolerance


class TestEnhancedAIService:
    """Test the enhanced AI service integration"""
    
    @pytest.fixture
    def enhanced_service(self):
        with patch('app.ai.enhanced_service.AIService') as mock_ai_service:
            mock_ai_service.return_value.get_available_models.return_value = [
                AIModel(
                    id="gpt-4o-mini",
                    name="GPT-4o Mini",
                    provider="openai",
                    description="Fast model",
                    max_tokens=4096,
                    available=True
                )
            ]
            return EnhancedAIService()
    
    @pytest.mark.asyncio
    async def test_model_recommendation_endpoint(self, enhanced_service):
        """Test model recommendation functionality"""
        recommendation = await enhanced_service.get_model_recommendation(
            message="What is machine learning?",
            user_preferences={"priority": "balanced"}
        )
        
        assert "recommended_model" in recommendation
        assert "confidence" in recommendation
        assert "reasoning" in recommendation
        assert "query_analysis" in recommendation
    
    @pytest.mark.asyncio
    async def test_optimization_analytics(self, enhanced_service):
        """Test optimization analytics"""
        # First, generate some data by tracking performance
        await enhanced_service.optimization_service.track_model_performance(
            model_id="gpt-4o-mini",
            response_time=2.0,
            success=True,
            tokens_used=100,
            cost=0.01,
            quality_score=0.8
        )
        
        analytics = await enhanced_service.get_optimization_analytics()
        
        assert "analytics" in analytics
        assert "recommendations" in analytics
        assert "settings" in analytics
    
    @pytest.mark.asyncio
    async def test_settings_update(self, enhanced_service):
        """Test optimization settings update"""
        new_settings = {
            "auto_model_selection": False,
            "cost_tracking_enabled": True,
            "fallback_threshold": 0.8
        }
        
        result = await enhanced_service.update_optimization_settings(new_settings)
        
        assert result["success"] == True
        assert "updated" in result
        assert enhanced_service.auto_model_selection == False
        assert enhanced_service.optimization_service.fallback_threshold == 0.8


class TestOptimizationAPI:
    """Test optimization API endpoints"""
    
    @pytest.fixture
    def client(self):
        from fastapi.testclient import TestClient
        from app.main import app
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test optimization health endpoint"""
        response = client.get("/api/ai/optimization/health")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] == True
        assert "status" in data
    
    def test_model_recommendation_endpoint(self, client):
        """Test model recommendation endpoint"""
        response = client.get("/api/ai/optimization/models/recommendation?message=Hello&priority=speed")
        assert response.status_code == 200
        data = response.json()
        assert "recommendation" in data
    
    def test_analytics_endpoint(self, client):
        """Test analytics endpoint"""
        response = client.get("/api/ai/optimization/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "analytics" in data
    
    def test_settings_endpoint(self, client):
        """Test settings endpoint"""
        response = client.get("/api/ai/optimization/settings")
        assert response.status_code == 200
        data = response.json()
        assert "settings" in data


class TestCostOptimization:
    """Test cost optimization features"""
    
    @pytest.fixture
    def optimization_service(self):
        mock_ai_service = Mock(spec=AIService)
        return AIOptimizationService(mock_ai_service)
    
    @pytest.mark.asyncio
    async def test_cost_calculation(self, optimization_service):
        """Test cost calculation for different models"""
        # Test with known cost model
        model_id = "gpt-4o"
        tokens = 1000
        
        cost_info = optimization_service.cost_per_token.get(model_id)
        assert cost_info is not None
        
        estimated_cost = (cost_info["input"] + cost_info["output"]) * tokens / 2000
        assert estimated_cost > 0
    
    @pytest.mark.asyncio
    async def test_cost_tracking(self, optimization_service):
        """Test cost tracking over multiple requests"""
        model_id = "gpt-4"
        
        total_expected_cost = 0
        for i in range(3):
            cost = 0.05 + i * 0.01
            total_expected_cost += cost
            
            await optimization_service.track_model_performance(
                model_id=model_id,
                response_time=3.0,
                success=True,
                tokens_used=200,
                cost=cost
            )
        
        metrics = optimization_service.model_metrics[model_id]
        assert abs(metrics.total_cost - total_expected_cost) < 0.001
    
    @pytest.mark.asyncio
    async def test_cost_optimization_recommendations(self, optimization_service):
        """Test cost optimization recommendations"""
        # Create expensive usage pattern
        expensive_model = "gpt-4"
        for i in range(20):
            await optimization_service.track_model_performance(
                model_id=expensive_model,
                response_time=5.0,
                success=True,
                tokens_used=500,
                cost=0.1  # High cost
            )
        
        recommendations = await optimization_service.get_optimization_recommendations()
        
        assert "cost_optimization" in recommendations
        cost_recommendations = recommendations["cost_optimization"]
        
        # Should have recommendations about expensive models
        assert len(cost_recommendations) > 0
        assert any(expensive_model in rec for rec in cost_recommendations)


if __name__ == "__main__":
    # Run specific test categories
    import sys
    
    if len(sys.argv) > 1:
        test_category = sys.argv[1]
        if test_category == "query":
            pytest.main(["-v", "TestQueryAnalysis"])
        elif test_category == "recommendation":
            pytest.main(["-v", "TestModelRecommendation"])
        elif test_category == "performance":
            pytest.main(["-v", "TestPerformanceMonitoring"])
        elif test_category == "api":
            pytest.main(["-v", "TestOptimizationAPI"])
        elif test_category == "cost":
            pytest.main(["-v", "TestCostOptimization"])
        else:
            pytest.main(["-v"])
    else:
        pytest.main(["-v"])