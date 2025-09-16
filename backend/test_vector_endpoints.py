"""
Test script for Vector Database API endpoints.

This script tests the vector database API endpoints using FastAPI's test client.
"""

import sys
import os
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.vector.service import VectorDBService
from app.database.models import DocumentResponse, VectorSearchResult


def test_vector_endpoints():
    """Test the vector database API endpoints."""
    print("🧪 Testing Vector Database API Endpoints")
    print("=" * 50)
    
    # Create test client
    client = TestClient(app)
    
    # Mock the vector service to avoid database dependency
    mock_vector_service = AsyncMock(spec=VectorDBService)
    
    # Mock responses
    mock_document = DocumentResponse(
        id=1,
        title="Test Document",
        content="This is a test document for vector search.",
        metadata={"category": "test"},
        source="test_source",
        document_type="text",
        created_at="2024-01-01T00:00:00",
        updated_at="2024-01-01T00:00:00"
    )
    
    mock_search_results = [
        VectorSearchResult(
            id=1,
            title="Test Document",
            content="This is a test document for vector search.",
            metadata={"category": "test"},
            similarity_score=0.95
        )
    ]
    
    mock_vector_service.add_document.return_value = 1
    mock_vector_service.get_document.return_value = mock_document
    mock_vector_service.search.return_value = mock_search_results
    mock_vector_service.list_documents.return_value = [mock_document]
    mock_vector_service.get_document_count.return_value = 1
    mock_vector_service.update_document.return_value = True
    mock_vector_service.delete_document.return_value = True
    mock_vector_service.health_check.return_value = {
        "status": "healthy",
        "model_status": "loaded",
        "embedding_dimension": 1024,
        "document_count": 1,
        "database_connection": "ok",
        "vector_extension": "ok"
    }
    
    with patch('app.vector.router.get_vector_service', return_value=mock_vector_service), \
         patch('app.database.connection.initialize_database'), \
         patch('app.vector.service.vector_service.initialize'):
        try:
            # Test health check endpoint
            print("1. Testing health check endpoint...")
            response = client.get("/api/vector/health")
            assert response.status_code == 200
            health_data = response.json()
            assert health_data["status"] == "healthy"
            print("✅ Health check endpoint working")
            
            # Test document creation endpoint
            print("\n2. Testing document creation endpoint...")
            document_data = {
                "title": "Test Document",
                "content": "This is a test document for vector search.",
                "metadata": {"category": "test"},
                "source": "test_source",
                "document_type": "text"
            }
            response = client.post("/api/vector/documents", json=document_data)
            assert response.status_code == 201
            created_doc = response.json()
            assert created_doc["title"] == "Test Document"
            print("✅ Document creation endpoint working")
            
            # Test document retrieval endpoint
            print("\n3. Testing document retrieval endpoint...")
            response = client.get("/api/vector/documents/1")
            assert response.status_code == 200
            doc_data = response.json()
            assert doc_data["id"] == 1
            print("✅ Document retrieval endpoint working")
            
            # Test vector search endpoint (POST)
            print("\n4. Testing vector search endpoint (POST)...")
            search_data = {
                "query": "test document",
                "top_k": 5,
                "similarity_threshold": 0.7
            }
            response = client.post("/api/vector/search", json=search_data)
            assert response.status_code == 200
            search_results = response.json()
            assert len(search_results) == 1
            assert search_results[0]["similarity_score"] == 0.95
            print("✅ Vector search endpoint (POST) working")
            
            # Test vector search endpoint (GET)
            print("\n5. Testing vector search endpoint (GET)...")
            response = client.get("/api/vector/search?query=test%20document&top_k=5")
            assert response.status_code == 200
            search_results = response.json()
            assert len(search_results) == 1
            print("✅ Vector search endpoint (GET) working")
            
            # Test document listing endpoint
            print("\n6. Testing document listing endpoint...")
            response = client.get("/api/vector/documents?limit=10&offset=0")
            assert response.status_code == 200
            list_data = response.json()
            assert "documents" in list_data
            assert "total_count" in list_data
            assert list_data["total_count"] == 1
            print("✅ Document listing endpoint working")
            
            # Test document update endpoint
            print("\n7. Testing document update endpoint...")
            update_data = {
                "title": "Updated Test Document",
                "metadata": {"category": "test", "updated": True}
            }
            response = client.put("/api/vector/documents/1", json=update_data)
            assert response.status_code == 200
            updated_doc = response.json()
            assert updated_doc["title"] == "Test Document"  # Mock returns original
            print("✅ Document update endpoint working")
            
            # Test document deletion endpoint
            print("\n8. Testing document deletion endpoint...")
            response = client.delete("/api/vector/documents/1")
            assert response.status_code == 204
            print("✅ Document deletion endpoint working")
            
            # Test stats endpoint
            print("\n9. Testing stats endpoint...")
            with patch('app.database.connection.db_manager') as mock_db_manager:
                mock_conn = AsyncMock()
                mock_conn.fetch.return_value = [
                    {"document_type": "text", "count": 5},
                    {"document_type": "article", "count": 3}
                ]
                mock_db_manager.get_connection.return_value.__aenter__.return_value = mock_conn
                
                response = client.get("/api/vector/stats")
                assert response.status_code == 200
                stats_data = response.json()
                assert "total_documents" in stats_data
                assert "document_types" in stats_data
                print("✅ Stats endpoint working")
            
            print("\n" + "=" * 50)
            print("🎉 All vector API endpoint tests passed!")
            
        except AssertionError as e:
            print(f"\n❌ Test assertion failed: {e}")
            return False
        except Exception as e:
            print(f"\n❌ Test failed with error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    return True


if __name__ == "__main__":
    success = test_vector_endpoints()
    if success:
        print("\n✅ All tests passed successfully!")
        exit(0)
    else:
        print("\n❌ Some tests failed!")
        exit(1)