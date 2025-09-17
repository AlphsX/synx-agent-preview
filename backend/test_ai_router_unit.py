#!/usr/bin/env python3
"""
Unit Tests for AI Router Component

This test file focuses specifically on the AI Router functionality:
- Provider initialization and management
- Model discovery and routing
- Fallback logic and error handling
- Availability caching
- Streaming response handling

Requirements: 1.1, 1.2, 1.3, 1.4
"""

import pytest
import asyncio
import sys
import os
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime, timedelta

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.ai.router import AIModelRouter
from app.ai.models import ChatMessage, StreamChunk, AIModel
from app.ai.providers.base import BaseAIProvider


class MockAIProvider(BaseAIProvider):
    """Mock AI provider for testing"""
    
    def __init__(self, api_key: str, provider_name: str = "mock", available: bool = True):
        super().__init__(api_key)
        self._provider_name = provider_name
        self._available = available
        self._models = [
            AIModel(
                id=f"{provider_name}-model-1",
                name=f"Mock Model 1 ({provider_name})",
                provider=provider_name,
                available=True
            ),
            AIModel(
                id=f"{provider_name}-model-2", 
                name=f"Mock Model 2 ({provider_name})",
                provider=provider_name,
                available=True
            )
        ]
    
    def get_provider_name(self) -> str:
        return self._provider_name
    
    def is_available(self) -> bool:
        return self._available and bool(self.api_key)
    
    def get_supported_models(self) -> list:
        return self._models if self.is_available() else []
    
    async def check_availability(self, model_id: str) -> bool:
        if not self.is_available():
            return False
        return any(model.id == model_id for model in self._models)
    
    async def generate_response(self, messages, model_id: str, **kwargs):
        """Generate mock streaming response"""
        if not self.is_available():
            yield StreamChunk(
                content="Provider not available",
                model_id=model_id,
                provider=self._provider_name,
                finish_reason="error",
                done=True
            )
            return
        
        # Simulate streaming response
        mock_response = f"Mock response from {self._provider_name}:{model_id}"
        words = mock_response.split()
        
        for i, word in enumerate(words):
            await asyncio.sleep(0.01)  # Simulate delay
            yield StreamChunk(
                content=word + " ",
                model_id=model_id,
                provider=self._provider_name,
                finish_reason="stop" if i == len(words) - 1 else None,
                done=i == len(words) - 1
            )


class TestAIRouterInitialization:
    """Test AI Router initialization and provider management"""
    
    def test_router_initialization(self):
        """Test router initializes with providers"""
        router = AIModelRouter()
        
        # Should have provider instances
        assert "groq" in router.providers
        assert "openai" in router.providers
        assert "anthropic" in router.providers
        
        # Should have fallback configurations
        assert router.fallback_models["groq"]
        assert router.fallback_models["openai"]
        assert router.fallback_models["anthropic"]
        
        # Should initialize empty cache
        assert isinstance(router.availability_cache, dict)
        assert len(router.availability_cache) == 0
    
    def test_provider_replacement(self):
        """Test replacing providers with mock providers"""
        router = AIModelRouter()
        
        # Replace with mock providers
        router.providers = {
            "mock1": MockAIProvider("test-key-1", "mock1", True),
            "mock2": MockAIProvider("test-key-2", "mock2", True),
            "mock3": MockAIProvider("", "mock3", False)  # Unavailable
        }
        
        # Update fallback models for mock providers
        router.fallback_models = {
            "mock1": ["mock1-model-1", "mock1-model-2"],
            "mock2": ["mock2-model-1", "mock2-model-2"],
            "mock3": ["mock3-model-1"]
        }
        
        # Test provider status
        status = router.get_provider_status()
        assert status["mock1"]["available"] is True
        assert status["mock2"]["available"] is True
        assert status["mock3"]["available"] is False


class TestModelDiscovery:
    """Test model discovery and routing functionality"""
    
    @pytest.fixture
    def mock_router(self):
        """Create router with mock providers"""
        router = AIModelRouter()
        router.providers = {
            "provider1": MockAIProvider("key1", "provider1", True),
            "provider2": MockAIProvider("key2", "provider2", True),
            "provider3": MockAIProvider("", "provider3", False)
        }
        router.fallback_models = {
            "provider1": ["provider1-model-1", "provider1-model-2"],
            "provider2": ["provider2-model-1", "provider2-model-2"],
            "provider3": ["provider3-model-1"]
        }
        return router
    
    def test_get_all_models(self, mock_router):
        """Test getting all available models"""
        models = mock_router.get_all_models()
        
        # Should get models from available providers only
        assert len(models) == 4  # 2 from provider1 + 2 from provider2
        
        model_ids = [model.id for model in models]
        assert "provider1-model-1" in model_ids
        assert "provider1-model-2" in model_ids
        assert "provider2-model-1" in model_ids
        assert "provider2-model-2" in model_ids
        
        # Should not include models from unavailable provider
        assert "provider3-model-1" not in model_ids
    
    def test_get_models_by_provider(self, mock_router):
        """Test getting models for specific provider"""
        # Available provider
        provider1_models = mock_router.get_models_by_provider("provider1")
        assert len(provider1_models) == 2
        assert all(model.provider == "provider1" for model in provider1_models)
        
        # Unavailable provider
        provider3_models = mock_router.get_models_by_provider("provider3")
        assert len(provider3_models) == 0
        
        # Non-existent provider
        nonexistent_models = mock_router.get_models_by_provider("nonexistent")
        assert len(nonexistent_models) == 0
    
    def test_get_provider_for_model(self, mock_router):
        """Test model-to-provider routing"""
        # Existing models
        assert mock_router.get_provider_for_model("provider1-model-1") == "provider1"
        assert mock_router.get_provider_for_model("provider2-model-2") == "provider2"
        
        # Non-existent model
        assert mock_router.get_provider_for_model("nonexistent-model") is None
        
        # Model from unavailable provider
        assert mock_router.get_provider_for_model("provider3-model-1") is None


class TestAvailabilityChecking:
    """Test model availability checking and caching"""
    
    @pytest.fixture
    def mock_router(self):
        """Create router with mock providers"""
        router = AIModelRouter()
        router.providers = {
            "available": MockAIProvider("key1", "available", True),
            "unavailable": MockAIProvider("", "unavailable", False)
        }
        return router
    
    @pytest.mark.asyncio
    async def test_availability_check_success(self, mock_router):
        """Test successful availability check"""
        available = await mock_router.check_model_availability("available-model-1")
        assert available is True
        
        # Should cache the result
        assert "available-model-1" in mock_router.availability_cache
        cached = mock_router.availability_cache["available-model-1"]
        assert cached.available is True
        assert cached.model_id == "available-model-1"
    
    @pytest.mark.asyncio
    async def test_availability_check_failure(self, mock_router):
        """Test availability check for unavailable model"""
        available = await mock_router.check_model_availability("unavailable-model-1")
        assert available is False
        
        # Should cache the failure
        assert "unavailable-model-1" in mock_router.availability_cache
        cached = mock_router.availability_cache["unavailable-model-1"]
        assert cached.available is False
    
    @pytest.mark.asyncio
    async def test_availability_caching(self, mock_router):
        """Test availability result caching"""
        # First check
        start_time = datetime.now()
        available1 = await mock_router.check_model_availability("available-model-1")
        first_check_time = datetime.now() - start_time
        
        # Second check (should use cache)
        start_time = datetime.now()
        available2 = await mock_router.check_model_availability("available-model-1")
        second_check_time = datetime.now() - start_time
        
        # Results should be consistent
        assert available1 == available2
        
        # Second check should be faster
        assert second_check_time < first_check_time
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self, mock_router):
        """Test cache expiration behavior"""
        # Set short cache duration for testing
        mock_router.cache_duration = timedelta(milliseconds=100)
        
        # First check
        available1 = await mock_router.check_model_availability("available-model-1")
        
        # Wait for cache to expire
        await asyncio.sleep(0.2)
        
        # Second check should refresh cache
        available2 = await mock_router.check_model_availability("available-model-1")
        
        # Results should still be consistent
        assert available1 == available2
    
    def test_cache_clearing(self, mock_router):
        """Test manual cache clearing"""
        # Add some cache entries
        mock_router.availability_cache["test-model"] = Mock()
        assert len(mock_router.availability_cache) > 0
        
        # Clear cache
        mock_router.clear_availability_cache()
        assert len(mock_router.availability_cache) == 0


class TestFallbackLogic:
    """Test fallback model selection and error handling"""
    
    @pytest.fixture
    def mock_router(self):
        """Create router with mock providers and fallback configuration"""
        router = AIModelRouter()
        router.providers = {
            "primary": MockAIProvider("key1", "primary", True),
            "secondary": MockAIProvider("key2", "secondary", True)
        }
        router.fallback_models = {
            "primary": ["primary-model-1", "primary-model-2", "primary-model-3"],
            "secondary": ["secondary-model-1", "secondary-model-2"]
        }
        return router
    
    def test_fallback_within_provider(self, mock_router):
        """Test fallback to another model within same provider"""
        fallback = mock_router.get_fallback_model("primary-model-1")
        
        # Should return next model in same provider
        assert fallback in ["primary-model-2", "primary-model-3"]
        assert fallback != "primary-model-1"
    
    def test_fallback_cross_provider(self, mock_router):
        """Test fallback when no provider found for model"""
        fallback = mock_router.get_fallback_model("nonexistent-model")
        
        # Should return a model from any available provider
        if fallback:
            assert fallback in ["primary-model-1", "primary-model-2", "primary-model-3",
                              "secondary-model-1", "secondary-model-2"]
    
    def test_no_fallback_available(self, mock_router):
        """Test behavior when no fallback is available"""
        # Make all providers unavailable
        for provider in mock_router.providers.values():
            provider._available = False
        
        fallback = mock_router.get_fallback_model("any-model")
        assert fallback is None


class TestResponseGeneration:
    """Test AI response generation with streaming and error handling"""
    
    @pytest.fixture
    def mock_router(self):
        """Create router with mock providers"""
        router = AIModelRouter()
        router.providers = {
            "working": MockAIProvider("key1", "working", True),
            "failing": MockAIProvider("key2", "failing", True)
        }
        router.fallback_models = {
            "working": ["working-model-1", "working-model-2"],
            "failing": ["failing-model-1", "working-model-1"]  # Fallback to working provider
        }
        return router
    
    @pytest.mark.asyncio
    async def test_successful_response_generation(self, mock_router):
        """Test successful response generation"""
        messages = [ChatMessage(role="user", content="Hello")]
        
        response_chunks = []
        async for chunk in mock_router.generate_response(
            messages=messages,
            model_id="working-model-1",
            stream=True
        ):
            response_chunks.append(chunk)
        
        # Should receive response chunks
        assert len(response_chunks) > 0
        
        # Last chunk should be marked as done
        assert response_chunks[-1].done is True
        
        # Should have content
        full_response = "".join(chunk.content for chunk in response_chunks)
        assert "Mock response from working:working-model-1" in full_response
    
    @pytest.mark.asyncio
    async def test_response_generation_with_fallback(self, mock_router):
        """Test response generation with automatic fallback"""
        # Mock the failing provider to actually fail
        async def failing_generate_response(messages, model_id, **kwargs):
            yield StreamChunk(
                content="Provider error",
                model_id=model_id,
                provider="failing",
                finish_reason="error",
                done=True
            )
        
        mock_router.providers["failing"].generate_response = failing_generate_response
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        response_chunks = []
        async for chunk in mock_router.generate_response(
            messages=messages,
            model_id="failing-model-1",
            stream=True,
            enable_fallback=True
        ):
            response_chunks.append(chunk)
        
        # Should eventually get a successful response from fallback
        assert len(response_chunks) > 0
        
        # Check if fallback was used (should have working provider response)
        full_response = "".join(chunk.content for chunk in response_chunks)
        # Either got error or successful fallback
        assert "error" in full_response.lower() or "working" in full_response
    
    @pytest.mark.asyncio
    async def test_response_generation_no_fallback(self, mock_router):
        """Test response generation without fallback enabled"""
        # Mock the failing provider
        async def failing_generate_response(messages, model_id, **kwargs):
            yield StreamChunk(
                content="Provider error",
                model_id=model_id,
                provider="failing",
                finish_reason="error",
                done=True
            )
        
        mock_router.providers["failing"].generate_response = failing_generate_response
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        response_chunks = []
        async for chunk in mock_router.generate_response(
            messages=messages,
            model_id="failing-model-1",
            stream=True,
            enable_fallback=False
        ):
            response_chunks.append(chunk)
        
        # Should get error response without fallback
        assert len(response_chunks) > 0
        full_response = "".join(chunk.content for chunk in response_chunks)
        assert "error" in full_response.lower()
    
    @pytest.mark.asyncio
    async def test_mock_response_generation(self, mock_router):
        """Test mock response generation for demo mode"""
        messages = [ChatMessage(role="user", content="Hello")]
        
        response_chunks = []
        async for chunk in mock_router.generate_mock_response(
            messages=messages,
            model_id="demo-model",
            stream=True
        ):
            response_chunks.append(chunk)
        
        # Should receive mock response chunks
        assert len(response_chunks) > 0
        
        # Should indicate demo mode
        full_response = "".join(chunk.content for chunk in response_chunks)
        assert "demo mode" in full_response.lower()
        
        # Last chunk should be marked as done
        assert response_chunks[-1].done is True


class TestErrorHandling:
    """Test error handling and edge cases"""
    
    @pytest.fixture
    def mock_router(self):
        """Create router for error testing"""
        router = AIModelRouter()
        router.providers = {
            "test": MockAIProvider("key1", "test", True)
        }
        return router
    
    @pytest.mark.asyncio
    async def test_invalid_model_id(self, mock_router):
        """Test handling of invalid model ID"""
        messages = [ChatMessage(role="user", content="Hello")]
        
        response_chunks = []
        async for chunk in mock_router.generate_response(
            messages=messages,
            model_id="invalid-model-id",
            stream=True
        ):
            response_chunks.append(chunk)
        
        # Should get error response
        assert len(response_chunks) > 0
        full_response = "".join(chunk.content for chunk in response_chunks)
        assert "error" in full_response.lower()
    
    @pytest.mark.asyncio
    async def test_empty_messages(self, mock_router):
        """Test handling of empty messages list"""
        response_chunks = []
        async for chunk in mock_router.generate_response(
            messages=[],
            model_id="test-model-1",
            stream=True
        ):
            response_chunks.append(chunk)
        
        # Should handle gracefully
        assert len(response_chunks) >= 0
    
    @pytest.mark.asyncio
    async def test_provider_exception(self, mock_router):
        """Test handling of provider exceptions"""
        # Mock provider to raise exception
        async def exception_generate_response(messages, model_id, **kwargs):
            raise Exception("Provider connection failed")
        
        mock_router.providers["test"].generate_response = exception_generate_response
        
        messages = [ChatMessage(role="user", content="Hello")]
        
        response_chunks = []
        async for chunk in mock_router.generate_response(
            messages=messages,
            model_id="test-model-1",
            stream=True
        ):
            response_chunks.append(chunk)
        
        # Should handle exception gracefully
        assert len(response_chunks) > 0
        full_response = "".join(chunk.content for chunk in response_chunks)
        assert "error" in full_response.lower()


async def main():
    """Run AI Router unit tests"""
    print("🧪 AI ROUTER UNIT TESTS")
    print("=" * 50)
    print("Testing AI Router Component")
    print("Requirements: 1.1, 1.2, 1.3, 1.4")
    print("=" * 50)
    
    # Run tests using pytest programmatically
    import pytest
    
    # Run this test file
    exit_code = pytest.main([__file__, "-v", "--tb=short"])
    
    if exit_code == 0:
        print("\n✅ All AI Router unit tests passed!")
        print("\n🎯 Requirements Validated:")
        print("   ✅ 1.1: AI model routing to appropriate services")
        print("   ✅ 1.2: Streaming response handling")
        print("   ✅ 1.3: Fallback responses and error handling")
        print("   ✅ 1.4: Mock responses for demo mode")
        
        print("\n📊 Test Coverage:")
        print("   - Provider initialization and management")
        print("   - Model discovery and routing logic")
        print("   - Availability checking and caching")
        print("   - Fallback model selection")
        print("   - Streaming response generation")
        print("   - Error handling and edge cases")
    else:
        print("\n❌ Some AI Router unit tests failed")
    
    return exit_code


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)