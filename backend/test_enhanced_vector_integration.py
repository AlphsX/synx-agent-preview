"""
Integration tests for enhanced vector database API endpoints.

Tests the complete API functionality including hybrid search, clustering,
summarization, and caching through HTTP endpoints.
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock

from app.main import app
from app.vector.enhanced_service import EnhancedVectorDBService
from app.database.models import VectorSearchResult, DocumentResponse


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_enhanced_service():
    """Create mock enhanced vector service."""
    service = Mock(spec=EnhancedVectorDBService)
    return service


class TestEnhancedVectorEndpoints:
    """Test enhanced vector database API endpoints."""
    
    def test_create_document_with_summary(self, client, mock_enhanced_service):
        """Test document creation with summarization endpoint."""
        # Mock service response
        mock_enhanced_service.add_document_with_summary.return_value = 1
        mock_enhanced_service.get_document.return_value = DocumentResponse(
            id=1,
            title="Test Document",
            content="Test content",
            metadata={"summarized": True, "summary": "Test summary"},
            source="test",
            document_type="text",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.post(
                "/api/vector/enhanced/documents",
                json={
                    "title": "Test Document",
                    "content": "This is a test document with some content",
                    "metadata": {},
                    "source": "test",
                    "document_type": "text",
                    "auto_summarize": True
                }
            )
            
            assert response.status_code == 201
            data = response.json()
            assert data["id"] == 1
            assert data["title"] == "Test Document"
            assert data["metadata"]["summarized"] is True
    
    def test_hybrid_search_post(self, client, mock_enhanced_service):
        """Test hybrid search POST endpoint."""
        # Mock service response
        mock_results = [
            VectorSearchResult(
                id=1,
                title="Test Result",
                content="Test content",
                metadata={},
                similarity_score=0.85
            )
        ]
        mock_enhanced_service.hybrid_search.return_value = mock_results
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.post(
                "/api/vector/enhanced/search/hybrid",
                json={
                    "query": "machine learning algorithms",
                    "top_k": 5,
                    "vector_weight": 0.7,
                    "keyword_weight": 0.3,
                    "similarity_threshold": 0.6,
                    "use_cache": True
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert "search_metadata" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["id"] == 1
            assert data["search_metadata"]["search_type"] == "hybrid"
    
    def test_hybrid_search_get(self, client, mock_enhanced_service):
        """Test hybrid search GET endpoint."""
        # Mock service response
        mock_results = [
            VectorSearchResult(
                id=2,
                title="Another Result",
                content="Another content",
                metadata={},
                similarity_score=0.75
            )
        ]
        mock_enhanced_service.hybrid_search.return_value = mock_results
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.get(
                "/api/vector/enhanced/search/hybrid",
                params={
                    "query": "deep learning",
                    "top_k": 3,
                    "vector_weight": 0.8,
                    "keyword_weight": 0.2,
                    "similarity_threshold": 0.5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 1
            assert data["results"][0]["id"] == 2
    
    def test_document_clustering_post(self, client, mock_enhanced_service):
        """Test document clustering POST endpoint."""
        # Mock service response
        mock_cluster_result = {
            "clusters": {
                "0": [1, 2, 3],
                "1": [4, 5, 6]
            },
            "topics": {
                "0": ["machine", "learning", "ai"],
                "1": ["data", "science", "analysis"]
            },
            "detailed_clusters": {
                "0": {
                    "document_ids": [1, 2, 3],
                    "document_count": 3,
                    "documents": [
                        {"id": 1, "title": "ML Basics", "content_preview": "Machine learning..."},
                        {"id": 2, "title": "AI Overview", "content_preview": "Artificial intelligence..."},
                        {"id": 3, "title": "Deep Learning", "content_preview": "Deep learning..."}
                    ]
                }
            },
            "n_clusters": 2,
            "total_documents": 6
        }
        mock_enhanced_service.cluster_documents_by_topic.return_value = mock_cluster_result
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.post(
                "/api/vector/enhanced/clustering",
                json={
                    "document_type": "text",
                    "source": "academic",
                    "min_documents": 5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "clusters" in data
            assert "topics" in data
            assert "detailed_clusters" in data
            assert data["n_clusters"] == 2
            assert data["total_documents"] == 6
    
    def test_document_clustering_get(self, client, mock_enhanced_service):
        """Test document clustering GET endpoint."""
        # Mock service response
        mock_cluster_result = {
            "clusters": {"0": [1, 2]},
            "topics": {"0": ["test", "document"]},
            "n_clusters": 1,
            "total_documents": 2
        }
        mock_enhanced_service.cluster_documents_by_topic.return_value = mock_cluster_result
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.get(
                "/api/vector/enhanced/clustering",
                params={
                    "document_type": "text",
                    "min_documents": 3
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "clusters" in data
            assert data["n_clusters"] == 1
    
    def test_document_recommendations_post(self, client, mock_enhanced_service):
        """Test document recommendations POST endpoint."""
        # Mock service response
        mock_recommendations = [
            VectorSearchResult(
                id=2,
                title="Similar Document",
                content="Similar content",
                metadata={},
                similarity_score=0.8
            ),
            VectorSearchResult(
                id=3,
                title="Related Document",
                content="Related content",
                metadata={},
                similarity_score=0.7
            )
        ]
        mock_enhanced_service.get_document_recommendations.return_value = mock_recommendations
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.post(
                "/api/vector/enhanced/recommendations",
                json={
                    "document_id": 1,
                    "recommendation_type": "similar",
                    "top_k": 5
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2
            assert data[0]["id"] == 2
            assert data[1]["id"] == 3
    
    def test_document_recommendations_get(self, client, mock_enhanced_service):
        """Test document recommendations GET endpoint."""
        # Mock service response
        mock_recommendations = [
            VectorSearchResult(
                id=4,
                title="Cluster Document",
                content="Cluster content",
                metadata={},
                similarity_score=0.9
            )
        ]
        mock_enhanced_service.get_document_recommendations.return_value = mock_recommendations
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.get(
                "/api/vector/enhanced/recommendations/1",
                params={
                    "recommendation_type": "cluster",
                    "top_k": 3
                }
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 1
            assert data[0]["id"] == 4
    
    def test_cache_stats(self, client, mock_enhanced_service):
        """Test cache statistics endpoint."""
        # Mock service response
        mock_stats = {
            "total_entries": 15,
            "avg_access_count": 2.3,
            "max_access_count": 8,
            "cache_size_limit": 1000
        }
        mock_enhanced_service.get_semantic_cache_stats.return_value = mock_stats
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.get("/api/vector/enhanced/cache/stats")
            
            assert response.status_code == 200
            data = response.json()
            assert data["total_entries"] == 15
            assert data["avg_access_count"] == 2.3
            assert data["cache_size_limit"] == 1000
    
    def test_clear_cache(self, client, mock_enhanced_service):
        """Test cache clearing endpoint."""
        # Mock service response
        mock_enhanced_service.clear_semantic_cache.return_value = None
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.delete("/api/vector/enhanced/cache")
            
            assert response.status_code == 200
            data = response.json()
            assert "message" in data
            assert "cleared successfully" in data["message"]
    
    def test_enhanced_health_check(self, client, mock_enhanced_service):
        """Test enhanced health check endpoint."""
        # Mock service response
        mock_health = {
            "status": "healthy",
            "model_status": "loaded",
            "document_count": 100,
            "enhanced_features": {
                "summarizer": "available",
                "clusterer": "available",
                "semantic_cache": "available",
                "hybrid_search": "available"
            },
            "cache_stats": {
                "total_entries": 10,
                "avg_access_count": 1.5
            }
        }
        mock_enhanced_service.health_check_enhanced.return_value = mock_health
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.get("/api/vector/enhanced/health")
            
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "healthy"
            assert "enhanced_features" in data
            assert "cache_stats" in data
    
    def test_get_available_features(self, client):
        """Test available features endpoint."""
        response = client.get("/api/vector/enhanced/features")
        
        assert response.status_code == 200
        data = response.json()
        assert "features" in data
        assert "version" in data
        assert "status" in data
        
        features = data["features"]
        assert "hybrid_search" in features
        assert "document_clustering" in features
        assert "automatic_summarization" in features
        assert "semantic_caching" in features
        assert "document_recommendations" in features
    
    def test_error_handling(self, client, mock_enhanced_service):
        """Test error handling in endpoints."""
        # Mock service to raise an exception
        mock_enhanced_service.hybrid_search.side_effect = Exception("Service error")
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            response = client.post(
                "/api/vector/enhanced/search/hybrid",
                json={
                    "query": "test query",
                    "top_k": 5
                }
            )
            
            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "Service error" in data["detail"]
    
    def test_validation_errors(self, client):
        """Test request validation errors."""
        # Test invalid top_k value
        response = client.post(
            "/api/vector/enhanced/search/hybrid",
            json={
                "query": "test query",
                "top_k": 0  # Invalid: should be >= 1
            }
        )
        
        assert response.status_code == 422
        
        # Test invalid similarity_threshold
        response = client.post(
            "/api/vector/enhanced/search/hybrid",
            json={
                "query": "test query",
                "similarity_threshold": 1.5  # Invalid: should be <= 1.0
            }
        )
        
        assert response.status_code == 422
    
    def test_missing_required_fields(self, client):
        """Test missing required fields in requests."""
        # Test missing query field
        response = client.post(
            "/api/vector/enhanced/search/hybrid",
            json={
                "top_k": 5
                # Missing required "query" field
            }
        )
        
        assert response.status_code == 422
        
        # Test missing content field for document creation
        response = client.post(
            "/api/vector/enhanced/documents",
            json={
                "title": "Test Document"
                # Missing required "content" field
            }
        )
        
        assert response.status_code == 422


class TestEnhancedVectorIntegration:
    """Integration tests for enhanced vector features."""
    
    @pytest.mark.asyncio
    async def test_full_workflow_integration(self, client):
        """Test complete workflow integration."""
        # This would be a full integration test with real database
        # For now, we'll mock the dependencies
        
        mock_service = Mock(spec=EnhancedVectorDBService)
        
        # Mock document creation
        mock_service.add_document_with_summary.return_value = 1
        mock_service.get_document.return_value = DocumentResponse(
            id=1,
            title="Integration Test Doc",
            content="Test content for integration",
            metadata={"summarized": True},
            source="test",
            document_type="text",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
        
        # Mock hybrid search
        mock_service.hybrid_search.return_value = [
            VectorSearchResult(
                id=1,
                title="Integration Test Doc",
                content="Test content for integration",
                metadata={"summarized": True},
                similarity_score=0.95
            )
        ]
        
        # Mock clustering
        mock_service.cluster_documents_by_topic.return_value = {
            "clusters": {"0": [1]},
            "topics": {"0": ["integration", "test"]},
            "n_clusters": 1,
            "total_documents": 1
        }
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_service
            
            # Step 1: Create document with summarization
            create_response = client.post(
                "/api/vector/enhanced/documents",
                json={
                    "title": "Integration Test Doc",
                    "content": "This is a test document for integration testing. " * 20,
                    "auto_summarize": True
                }
            )
            assert create_response.status_code == 201
            
            # Step 2: Perform hybrid search
            search_response = client.post(
                "/api/vector/enhanced/search/hybrid",
                json={
                    "query": "integration test",
                    "top_k": 5,
                    "use_cache": True
                }
            )
            assert search_response.status_code == 200
            search_data = search_response.json()
            assert len(search_data["results"]) == 1
            
            # Step 3: Cluster documents
            cluster_response = client.post(
                "/api/vector/enhanced/clustering",
                json={"min_documents": 1}
            )
            assert cluster_response.status_code == 200
            cluster_data = cluster_response.json()
            assert cluster_data["n_clusters"] == 1
            
            # Step 4: Get recommendations
            rec_response = client.post(
                "/api/vector/enhanced/recommendations",
                json={
                    "document_id": 1,
                    "recommendation_type": "similar",
                    "top_k": 3
                }
            )
            assert rec_response.status_code == 200
    
    def test_performance_with_large_requests(self, client, mock_enhanced_service):
        """Test performance with large requests."""
        # Mock service to handle large requests
        mock_enhanced_service.hybrid_search.return_value = []
        
        with patch('app.vector.enhanced_router.get_enhanced_vector_service') as mock_get_service:
            mock_get_service.return_value = mock_enhanced_service
            
            # Test with large query
            large_query = "machine learning " * 100  # Very long query
            
            response = client.post(
                "/api/vector/enhanced/search/hybrid",
                json={
                    "query": large_query,
                    "top_k": 50  # Maximum allowed
                }
            )
            
            assert response.status_code == 200
            
            # Test with maximum top_k
            response = client.get(
                "/api/vector/enhanced/search/hybrid",
                params={
                    "query": "test",
                    "top_k": 50
                }
            )
            
            assert response.status_code == 200


if __name__ == "__main__":
    # Run integration tests
    pytest.main([__file__, "-v", "--tb=short"])