"""
Demonstration of AI Model Optimization Features

This script demonstrates:
1. Dynamic model selection based on query complexity
2. Performance monitoring and tracking
3. Cost optimization insights
4. Quality assessment
5. Analytics and recommendations
"""

import asyncio
import json
import time
from datetime import datetime
from typing import List, Dict, Any

from app.ai.optimization_service import AIOptimizationService, QueryComplexity, ModelTier
from app.ai.enhanced_service import EnhancedAIService
from app.ai.models import AIModel
from app.ai.service import AIService


class MockAIService:
    """Mock AI service for demonstration"""
    
    def __init__(self):
        self.models = [
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
                description="High-quality model for complex tasks",
                max_tokens=8192,
                available=True
            ),
            AIModel(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                description="Excellent for reasoning and analysis",
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
            ),
            AIModel(
                id="llama-3.1-8b-instant",
                name="Llama 3.1 8B Instant",
                provider="groq",
                description="Ultra-fast responses",
                max_tokens=4096,
                available=True
            )
        ]
    
    def get_available_models(self) -> List[AIModel]:
        return self.models
    
    async def chat(self, messages, model_id, **kwargs):
        # Simulate response generation
        await asyncio.sleep(0.1)
        yield f"Mock response from {model_id}: This is a simulated AI response."


async def demonstrate_query_analysis():
    """Demonstrate query complexity analysis"""
    print("🔍 QUERY ANALYSIS DEMONSTRATION")
    print("=" * 50)
    
    mock_service = MockAIService()
    optimization_service = AIOptimizationService(mock_service)
    
    test_queries = [
        "Hello",
        "What is machine learning?",
        "Explain the differences between supervised and unsupervised learning algorithms, and provide examples of when to use each approach",
        "Design a comprehensive microservices architecture for a high-traffic e-commerce platform with real-time inventory management, payment processing, and recommendation systems",
        "What's the current Bitcoin price?",
        "Write a Python function to sort a list",
        "Create a marketing strategy for our new product launch"
    ]
    
    for query in test_queries:
        analysis = await optimization_service.analyze_query(query)
        print(f"\nQuery: '{query[:60]}{'...' if len(query) > 60 else ''}'")
        print(f"  Complexity: {analysis.complexity.value}")
        print(f"  Domain: {analysis.domain}")
        print(f"  Real-time data needed: {analysis.requires_real_time_data}")
        print(f"  Estimated tokens: {analysis.estimated_tokens}")
        print(f"  Confidence: {analysis.confidence:.2f}")


async def demonstrate_model_recommendation():
    """Demonstrate intelligent model recommendation"""
    print("\n\n🎯 MODEL RECOMMENDATION DEMONSTRATION")
    print("=" * 50)
    
    mock_service = MockAIService()
    optimization_service = AIOptimizationService(mock_service)
    available_models = mock_service.get_available_models()
    
    test_scenarios = [
        {
            "query": "Hello, how are you?",
            "priority": "speed",
            "description": "Simple greeting - prioritize speed"
        },
        {
            "query": "Analyze the economic implications of artificial intelligence on the job market",
            "priority": "quality",
            "description": "Complex analysis - prioritize quality"
        },
        {
            "query": "Write a short poem about nature",
            "priority": "cost",
            "description": "Creative task - prioritize cost"
        },
        {
            "query": "Implement a binary search algorithm in Python with error handling",
            "priority": "balanced",
            "description": "Technical task - balanced approach"
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\nScenario: {scenario['description']}")
        print(f"Query: '{scenario['query'][:60]}{'...' if len(scenario['query']) > 60 else ''}'")
        print(f"Priority: {scenario['priority']}")
        
        # Analyze query
        analysis = await optimization_service.analyze_query(scenario['query'])
        
        # Get recommendation
        recommendation = await optimization_service.recommend_model(
            analysis, 
            available_models, 
            {"priority": scenario['priority']}
        )
        
        print(f"  Recommended Model: {recommendation.model_id}")
        print(f"  Confidence: {recommendation.confidence:.2f}")
        print(f"  Estimated Cost: ${recommendation.estimated_cost:.4f}")
        print(f"  Estimated Response Time: {recommendation.estimated_response_time:.1f}s")
        print(f"  Reasoning: {recommendation.reasoning}")


async def demonstrate_performance_monitoring():
    """Demonstrate performance monitoring and tracking"""
    print("\n\n📊 PERFORMANCE MONITORING DEMONSTRATION")
    print("=" * 50)
    
    mock_service = MockAIService()
    optimization_service = AIOptimizationService(mock_service)
    
    # Simulate usage patterns for different models
    models_usage = {
        "gpt-4o-mini": {"requests": 50, "avg_time": 2.0, "success_rate": 0.95, "avg_cost": 0.001},
        "gpt-4": {"requests": 30, "avg_time": 5.0, "success_rate": 0.98, "avg_cost": 0.05},
        "claude-3-5-sonnet-20241022": {"requests": 25, "avg_time": 4.0, "success_rate": 0.97, "avg_cost": 0.03},
        "llama-3.1-70b-versatile": {"requests": 40, "avg_time": 3.0, "success_rate": 0.92, "avg_cost": 0.0005},
        "llama-3.1-8b-instant": {"requests": 60, "avg_time": 1.5, "success_rate": 0.90, "avg_cost": 0.0002}
    }
    
    print("Simulating usage patterns...")
    
    for model_id, usage in models_usage.items():
        for i in range(usage["requests"]):
            # Simulate some variation in metrics
            response_time = usage["avg_time"] + (i % 5 - 2) * 0.5
            success = (i / usage["requests"]) < usage["success_rate"]
            cost = usage["avg_cost"] * (1 + (i % 3 - 1) * 0.1)
            tokens = 100 + (i % 10) * 20
            quality_score = 0.7 + (i % 4) * 0.075  # Vary quality
            
            await optimization_service.track_model_performance(
                model_id=model_id,
                response_time=max(0.5, response_time),
                success=success,
                tokens_used=tokens,
                cost=max(0.0001, cost),
                quality_score=quality_score
            )
    
    print("\nPerformance Metrics Summary:")
    print("-" * 30)
    
    for model_id, metrics in optimization_service.model_metrics.items():
        print(f"\n{model_id}:")
        print(f"  Total Requests: {metrics.total_requests}")
        print(f"  Success Rate: {(1 - metrics.error_rate) * 100:.1f}%")
        print(f"  Avg Response Time: {metrics.avg_response_time:.2f}s")
        print(f"  Quality Score: {metrics.quality_score:.2f}")
        print(f"  Total Cost: ${metrics.total_cost:.4f}")
        print(f"  Availability Score: {metrics.availability_score:.2f}")


async def demonstrate_cost_optimization():
    """Demonstrate cost optimization features"""
    print("\n\n💰 COST OPTIMIZATION DEMONSTRATION")
    print("=" * 50)
    
    mock_service = MockAIService()
    optimization_service = AIOptimizationService(mock_service)
    
    # First, populate with some performance data (reuse from previous demo)
    models_usage = {
        "gpt-4": {"requests": 100, "avg_cost": 0.05},  # Expensive model, high usage
        "gpt-4o-mini": {"requests": 50, "avg_cost": 0.001},  # Cheap model
        "claude-3-5-sonnet-20241022": {"requests": 30, "avg_cost": 0.03},
    }
    
    for model_id, usage in models_usage.items():
        for i in range(usage["requests"]):
            await optimization_service.track_model_performance(
                model_id=model_id,
                response_time=2.0,
                success=True,
                tokens_used=100,
                cost=usage["avg_cost"],
                quality_score=0.8
            )
    
    # Get analytics
    analytics = await optimization_service.get_model_analytics()
    
    print("Cost Analysis:")
    print("-" * 20)
    print(f"Total Cost: ${analytics['summary']['total_cost']:.4f}")
    print(f"Total Requests: {analytics['summary']['total_requests']}")
    print(f"Cost per Request: ${analytics['cost_analysis']['cost_per_request']:.6f}")
    print(f"Projected Monthly Cost: ${analytics['cost_analysis']['projected_monthly_cost']:.2f}")
    
    print("\nMost Expensive Models:")
    for model_id, cost in analytics['cost_analysis']['most_expensive_models'][:3]:
        print(f"  {model_id}: ${cost:.4f}")
    
    # Get recommendations
    recommendations = await optimization_service.get_optimization_recommendations()
    
    print("\nCost Optimization Recommendations:")
    for rec in recommendations['cost_optimization']:
        print(f"  • {rec}")


async def demonstrate_quality_assessment():
    """Demonstrate response quality assessment"""
    print("\n\n⭐ QUALITY ASSESSMENT DEMONSTRATION")
    print("=" * 50)
    
    mock_service = MockAIService()
    optimization_service = AIOptimizationService(mock_service)
    
    test_responses = [
        {
            "query": "What is artificial intelligence?",
            "response": "Artificial Intelligence (AI) is a field of computer science that focuses on creating systems capable of performing tasks that typically require human intelligence. These tasks include learning, reasoning, problem-solving, perception, and language understanding. For example, AI powers virtual assistants, recommendation systems, and autonomous vehicles.",
            "description": "Comprehensive, well-structured response"
        },
        {
            "query": "Explain machine learning",
            "response": "ML is when computers learn.",
            "description": "Too brief, lacks detail"
        },
        {
            "query": "How does neural network work?",
            "response": "A neural network is a computational model inspired by biological neural networks. It consists of interconnected nodes (neurons) organized in layers. Each connection has a weight that adjusts during training. The network processes input data through these layers, with each neuron applying an activation function to its inputs. Through backpropagation and gradient descent, the network learns to minimize errors and improve predictions. This allows neural networks to recognize patterns, classify data, and make predictions across various domains like image recognition, natural language processing, and game playing.",
            "description": "Detailed, technical explanation with examples"
        },
        {
            "query": "What is Python?",
            "response": "Error: Unable to process request. Sorry, I don't understand. Can you clarify? What do you mean? I'm confused.",
            "description": "Error response with confusion indicators"
        }
    ]
    
    print("Quality Assessment Results:")
    print("-" * 30)
    
    for test in test_responses:
        quality_score = await optimization_service.assess_response_quality(
            test['query'], 
            test['response']
        )
        
        print(f"\nQuery: '{test['query']}'")
        print(f"Response: '{test['response'][:100]}{'...' if len(test['response']) > 100 else ''}'")
        print(f"Description: {test['description']}")
        print(f"Quality Score: {quality_score:.2f}")
        
        # Interpret score
        if quality_score >= 0.8:
            quality_level = "Excellent"
        elif quality_score >= 0.6:
            quality_level = "Good"
        elif quality_score >= 0.4:
            quality_level = "Fair"
        else:
            quality_level = "Poor"
        
        print(f"Quality Level: {quality_level}")


async def demonstrate_enhanced_chat():
    """Demonstrate enhanced chat with optimization"""
    print("\n\n💬 ENHANCED CHAT DEMONSTRATION")
    print("=" * 50)
    
    # Create enhanced service with mock
    enhanced_service = EnhancedAIService()
    enhanced_service.base_service = MockAIService()
    
    test_messages = [
        {
            "message": "Hello there!",
            "preferences": {"priority": "speed"},
            "description": "Simple greeting - should use fast model"
        },
        {
            "message": "Analyze the impact of quantum computing on cryptography and suggest mitigation strategies",
            "preferences": {"priority": "quality"},
            "description": "Complex analysis - should use high-quality model"
        }
    ]
    
    for test in test_messages:
        print(f"\nTest: {test['description']}")
        print(f"Message: '{test['message']}'")
        print(f"Preferences: {test['preferences']}")
        
        # Get recommendation
        recommendation = await enhanced_service.get_model_recommendation(
            message=test['message'],
            user_preferences=test['preferences']
        )
        
        if 'error' not in recommendation:
            print(f"Recommended Model: {recommendation['recommended_model']}")
            print(f"Confidence: {recommendation['confidence']:.2f}")
            print(f"Query Complexity: {recommendation['query_analysis']['complexity']}")
            print(f"Estimated Cost: ${recommendation['estimated_cost']:.4f}")
        else:
            print(f"Error: {recommendation['error']}")


async def main():
    """Run all demonstrations"""
    print("🚀 AI MODEL OPTIMIZATION DEMONSTRATION")
    print("=" * 60)
    print("This demo showcases advanced AI model management features:")
    print("• Dynamic model selection based on query complexity")
    print("• Performance monitoring and automatic fallback")
    print("• Cost optimization and usage tracking")
    print("• Response quality assessment and feedback loops")
    print("=" * 60)
    
    try:
        await demonstrate_query_analysis()
        await demonstrate_model_recommendation()
        await demonstrate_performance_monitoring()
        await demonstrate_cost_optimization()
        await demonstrate_quality_assessment()
        await demonstrate_enhanced_chat()
        
        print("\n\n✅ DEMONSTRATION COMPLETE")
        print("=" * 50)
        print("All optimization features demonstrated successfully!")
        print("\nKey Benefits:")
        print("• Intelligent model selection saves costs and improves performance")
        print("• Automatic fallback ensures high availability")
        print("• Performance monitoring enables data-driven optimization")
        print("• Quality assessment helps maintain response standards")
        print("• Cost tracking prevents budget overruns")
        
    except Exception as e:
        print(f"\n❌ Error during demonstration: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())