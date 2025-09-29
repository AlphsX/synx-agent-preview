"""
Comprehensive tests for enhanced vector database service.

Tests all enhanced features including hybrid search, document clustering,
automatic summarization, and semantic caching.
"""

import pytest
import asyncio
import json
from typing import List, Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from app.vector.enhanced_service import (
    EnhancedVectorDBService,
    DocumentSummarizer,
    DocumentClusterer,
    SemanticCache
)
from app.database.models import VectorSearchResult, DocumentResponse


class TestDocumentSummarizer:
    """Test document summarization functionality."""
    
    def setup_method(self):
        self.summarizer = DocumentSummarizer()
    
    def test_should_summarize_long_content(self):
        """Test that long content is identified for summarization."""
        long_content = "This is a sentence. " * 15  # 15 sentences
        assert self.summarizer.should_summarize(long_content)
    
    def test_should_not_summarize_short_content(self):
        """Test that short content is not summarized."""
        short_content = "This is a short document with only a few sentences."
        assert not self.summarizer.should_summarize(short_content)
    
    def test_extractive_summarize(self):
        """Test extractive summarization."""
        content = """
        Artificial intelligence is transforming the world. Machine learning algorithms 
        are becoming more sophisticated. Deep learning models can process vast amounts 
        of data. Natural language processing enables computers to understand human language.
        Computer vision allows machines to interpret visual information. Robotics combines 
        AI with physical systems. The future of AI looks very promising. Many industries 
        are adopting AI technologies. Healthcare, finance, and transportation are leading 
        sectors. AI will continue to evolve and improve human lives.
        """
        
        summary = self.summarizer.extractive_summarize(content, max_sentences=3)
        
        assert len(summary) > 0
        assert len(summary) < len(content)
        assert "artificial intelligence" in summary.lower() or "ai" in summary.lower()
    
    def test_summarize_fallback_on_error(self):
        """Test that summarization falls back to truncation on error."""
        # Test with problematic content that might cause NLTK issues
        problematic_content = "A" * 1000  # Very repetitive content
        
        summary = self.summarizer.extractive_summarize(problematic_content)
        
        assert len(summary) <= self.summarizer.max_summary_length + 3  # +3 for "..."
        assert summary.endswith("...")


class TestDocumentClusterer:
    """Test document clustering functionality."""
    
    def setup_method(self):
        self.clusterer = DocumentClusterer()
    
    @pytest.mark.asyncio
    async def test_cluster_documents_success(self):
        """Test successful document clustering."""
        documents = [
            {"id": 1, "content": "Machine learning and artificial intelligence research"},
            {"id": 2, "content": "Deep learning neural networks and AI algorithms"},
            {"id": 3, "content": "Natural language processing and text analysis"},
            {"id": 4, "content": "Computer vision and image recognition technology"},
            {"id": 5, "content": "Robotics and autonomous systems development"},
            {"id": 6, "content": "Data science and statistical analysis methods"},
        ]
        
        result = await self.clusterer.cluster_documents(documents)
        
        assert "clusters" in result
        assert "topics" in result
        assert "n_clusters" in result
        assert "total_documents" in result
        assert result["total_documents"] == len(documents)
        assert isinstance(result["clusters"], dict)
        assert isinstance(result["topics"], dict)
    
    @pytest.mark.asyncio
    async def test_cluster_documents_insufficient_data(self):
        """Test clustering with insufficient documents."""
        documents = [
            {"id": 1, "content": "Short document"},
            {"id": 2, "content": "Another short document"}
        ]
        
        result = await self.clusterer.cluster_documents(documents)
        
        assert "message" in result
        assert "Not enough documents" in result["message"]
    
    def test_get_similar_documents_by_cluster(self):
        """Test getting similar documents from the same cluster."""
        # Mock cluster data
        self.clusterer.cluster_labels = {
            0: [1, 2, 3],
            1: [4, 5, 6]
        }
        
        similar_docs = self.clusterer.get_similar_documents_by_cluster(1)
        assert similar_docs == [2, 3]
        
        similar_docs = self.clusterer.get_similar_documents_by_cluster(4)
        assert similar_docs == [5, 6]
        
        # Test non-existent document
        similar_docs = self.clusterer.get_similar_documents_by_cluster(999)
        assert similar_docs == []


class TestSemanticCache:
    """Test semantic caching functionality."""
    
    def setup_method(self):
        self.cache = SemanticCache()
    
    def test_get_query_hash(self):
        """Test query hash generation."""
        query1 = "What is machine learning?"
        query2 = "what is machine learning?"
        query3 = "What  is   machine    learning?"
        
        hash1 = self.cache._get_query_hash(query1)
        hash2 = self.cache._get_query_hash(query2)
        hash3 = self.cache._get_query_hash(query3)
        
        # All should produce the same hash due to normalization
        assert hash1 == hash2 == hash3
        assert len(hash1) == 32  # MD5 hash length
    
    @pytest.mark.asyncio
    async def test_cache_and_retrieve_exact_match(self):
        """Test caching and retrieving exact query matches."""
        query = "What is artificial intelligence?"
        query_embedding = [0.1] * 1024  # Mock embedding
        response = {"answer": "AI is...", "metadata": {}}
        
        # Cache the response
        await self.cache.cache_response(query, query_embedding, response)
        
        # Retrieve the cached response
        cached = await self.cache.get_cached_response(query, query_embedding)
        
        assert cached is not None
        assert cached["answer"] == "AI is..."
        assert "query_embedding" in cached["metadata"]
    
    @pytest.mark.asyncio
    async def test_cache_semantic_similarity(self):
        """Test semantic similarity matching in cache."""
        query1 = "What is machine learning?"
        query2 = "Tell me about machine learning"
        
        # Create similar embeddings
        embedding1 = [0.9] * 512 + [0.1] * 512
        embedding2 = [0.85] * 512 + [0.15] * 512  # Very similar
        
        response = {"answer": "ML is...", "metadata": {}}
        
        # Cache first query
        await self.cache.cache_response(query1, embedding1, response)
        
        # Try to retrieve with similar query
        cached = await self.cache.get_cached_response(query2, embedding2)
        
        # Should find the cached response due to high similarity
        assert cached is not None
        assert cached["answer"] == "ML is..."
    
    @pytest.mark.asyncio
    async def test_cache_cleanup(self):
        """Test cache cleanup functionality."""
        # Add many entries to trigger cleanup
        for i in range(self.cache.max_cache_size + 10):
            query = f"Query number {i}"
            embedding = [float(i)] * 1024
            response = {"answer": f"Answer {i}", "metadata": {}}
            await self.cache.cache_response(query, embedding, response)
        
        # Trigger cleanup
        await self.cache._cleanup_cache()
        
        # Cache should be within limits
        assert len(self.cache.cache) <= self.cache.max_cache_size
    
    def test_get_cache_stats(self):
        """Test cache statistics."""
        stats = self.cache.get_cache_stats()
        
        assert "total_entries" in stats
        assert "avg_access_count" in stats
        assert "cache_size_limit" in stats
        assert stats["cache_size_limit"] == self.cache.max_cache_size


class TestEnhancedVectorDBService:
    """Test enhanced vector database service."""
    
    def setup_method(self):
        self.service = EnhancedVectorDBService()
    
    @pytest.mark.asyncio
    async def test_initialization(self):
        """Test service initialization."""
        # Mock the parent initialization
        with patch.object(self.service, '_load_model') as mock_load:
            mock_load.return_value = Mock()
            await self.service.initialize()
            
        assert self.service.summarizer is not None
        assert self.service.clusterer is not None
        assert self.service.semantic_cache is not None
    
    @pytest.mark.asyncio
    async def test_add_document_with_summary(self):
        """Test adding document with automatic summarization."""
        long_content = "This is a very long document. " * 50  # Long enough to trigger summarization
        
        # Mock the parent add_document method
        with patch.object(self.service, 'add_document', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = 123
            
            document_id = await self.service.add_document_with_summary(
                content=long_content,
                title="Test Document",
                auto_summarize=True
            )
            
            assert document_id == 123
            mock_add.assert_called_once()
            
            # Check that metadata includes summary
            call_args = mock_add.call_args
            metadata = call_args.kwargs.get('metadata', {})
            assert 'summarized' in metadata
            assert metadata['summarized'] is True
            assert 'summary' in metadata
            assert 'original_length' in metadata
    
    @pytest.mark.asyncio
    async def test_hybrid_search_without_cache(self):
        """Test hybrid search without using cache."""
        query = "machine learning algorithms"
        
        # Mock database connection and results
        mock_connection = AsyncMock()
        mock_connection.fetch.return_value = [
            {
                'id': 1,
                'title': 'ML Basics',
                'content': 'Machine learning is a subset of AI',
                'metadata': {},
                'vector_similarity': 0.8
            }
        ]
        
        # Mock embedding generation
        with patch.object(self.service, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = [0.1] * 1024
            
            # Mock database manager
            with patch('app.vector.enhanced_service.db_manager') as mock_db:
                mock_db.get_connection.return_value.__aenter__.return_value = mock_connection
                
                # Mock keyword similarity calculation
                with patch.object(self.service, '_calculate_keyword_similarity', new_callable=AsyncMock) as mock_keyword:
                    mock_keyword.return_value = [0.7]
                    
                    results = await self.service.hybrid_search(
                        query=query,
                        top_k=5,
                        use_cache=False
                    )
                    
                    assert len(results) == 1
                    assert results[0].id == 1
                    assert results[0].title == 'ML Basics'
                    # Combined score should be weighted average of vector (0.8) and keyword (0.7)
                    expected_score = 0.8 * 0.7 + 0.7 * 0.3  # default weights
                    assert abs(results[0].similarity_score - expected_score) < 0.01
    
    @pytest.mark.asyncio
    async def test_hybrid_search_with_cache_hit(self):
        """Test hybrid search with cache hit."""
        query = "machine learning algorithms"
        query_embedding = [0.1] * 1024
        
        # Mock cache hit
        cached_response = {
            'results': [
                VectorSearchResult(
                    id=1,
                    title='Cached Result',
                    content='Cached content',
                    metadata={},
                    similarity_score=0.9
                )
            ]
        }
        
        with patch.object(self.service, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
            mock_embed.return_value = query_embedding
            
            with patch.object(self.service.semantic_cache, 'get_cached_response', new_callable=AsyncMock) as mock_cache:
                mock_cache.return_value = cached_response
                
                results = await self.service.hybrid_search(
                    query=query,
                    use_cache=True
                )
                
                assert len(results) == 1
                assert results[0].title == 'Cached Result'
                mock_cache.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cluster_documents_by_topic(self):
        """Test document clustering by topic."""
        # Mock list_documents
        mock_documents = [
            DocumentResponse(
                id=1,
                title="AI Research",
                content="Artificial intelligence research paper",
                metadata={},
                source="academic",
                document_type="paper",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z"
            ),
            DocumentResponse(
                id=2,
                title="ML Algorithms",
                content="Machine learning algorithm implementation",
                metadata={},
                source="academic",
                document_type="paper",
                created_at="2023-01-01T00:00:00Z",
                updated_at="2023-01-01T00:00:00Z"
            )
        ]
        
        with patch.object(self.service, 'list_documents', new_callable=AsyncMock) as mock_list:
            mock_list.return_value = mock_documents
            
            # Mock clusterer
            mock_cluster_result = {
                "clusters": {0: [1, 2]},
                "topics": {0: ["ai", "machine", "learning"]},
                "n_clusters": 1,
                "total_documents": 2
            }
            
            with patch.object(self.service.clusterer, 'cluster_documents', new_callable=AsyncMock) as mock_cluster:
                mock_cluster.return_value = mock_cluster_result
                
                result = await self.service.cluster_documents_by_topic()
                
                assert "detailed_clusters" in result
                assert "clusters" in result
                assert result["n_clusters"] == 1
                mock_list.assert_called_once()
                mock_cluster.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_document_recommendations_similar(self):
        """Test getting similar document recommendations."""
        document_id = 1
        
        # Mock get_document
        mock_doc = DocumentResponse(
            id=1,
            title="Test Doc",
            content="Test content for similarity",
            metadata={},
            source="test",
            document_type="text",
            created_at="2023-01-01T00:00:00Z",
            updated_at="2023-01-01T00:00:00Z"
        )
        
        # Mock search results
        mock_search_results = [
            VectorSearchResult(
                id=1,
                title="Test Doc",
                content="Test content for similarity",
                metadata={},
                similarity_score=1.0
            ),
            VectorSearchResult(
                id=2,
                title="Similar Doc",
                content="Similar test content",
                metadata={},
                similarity_score=0.8
            )
        ]
        
        with patch.object(self.service, 'get_document', new_callable=AsyncMock) as mock_get:
            mock_get.return_value = mock_doc
            
            with patch.object(self.service, 'search', new_callable=AsyncMock) as mock_search:
                mock_search.return_value = mock_search_results
                
                recommendations = await self.service.get_document_recommendations(
                    document_id=document_id,
                    recommendation_type="similar",
                    top_k=5
                )
                
                # Should exclude the reference document
                assert len(recommendations) == 1
                assert recommendations[0].id == 2
                assert recommendations[0].title == "Similar Doc"
    
    @pytest.mark.asyncio
    async def test_calculate_keyword_similarity(self):
        """Test keyword similarity calculation."""
        query = "machine learning algorithms"
        documents = [
            "Machine learning is a subset of artificial intelligence",
            "Deep learning algorithms use neural networks",
            "Natural language processing techniques"
        ]
        
        similarities = await self.service._calculate_keyword_similarity(query, documents)
        
        assert len(similarities) == 3
        assert all(0 <= sim <= 1 for sim in similarities)
        # First document should have highest similarity (contains "machine learning")
        assert similarities[0] >= similarities[2]
    
    @pytest.mark.asyncio
    async def test_calculate_document_similarity(self):
        """Test document similarity calculation."""
        content1 = "Machine learning algorithms"
        content2 = "Deep learning neural networks"
        
        with patch.object(self.service, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
            # Mock similar embeddings
            mock_embed.side_effect = [
                [0.8] * 512 + [0.2] * 512,  # First document embedding
                [0.7] * 512 + [0.3] * 512   # Second document embedding
            ]
            
            similarity = await self.service._calculate_document_similarity(content1, content2)
            
            assert 0 <= similarity <= 1
            assert similarity > 0.5  # Should be reasonably similar
    
    @pytest.mark.asyncio
    async def test_health_check_enhanced(self):
        """Test enhanced health check."""
        # Mock parent health check
        base_health = {
            "status": "healthy",
            "model_status": "loaded",
            "document_count": 10
        }
        
        with patch.object(self.service, 'health_check', new_callable=AsyncMock) as mock_health:
            mock_health.return_value = base_health
            
            health_status = await self.service.health_check_enhanced()
            
            assert health_status["status"] == "healthy"
            assert "enhanced_features" in health_status
            assert "cache_stats" in health_status
            
            enhanced_features = health_status["enhanced_features"]
            assert enhanced_features["summarizer"] == "available"
            assert enhanced_features["clusterer"] == "available"
            assert enhanced_features["semantic_cache"] == "available"
            assert enhanced_features["hybrid_search"] == "available"


@pytest.mark.asyncio
async def test_integration_workflow():
    """Test complete integration workflow of enhanced features."""
    service = EnhancedVectorDBService()
    
    # Mock all external dependencies
    with patch.object(service, '_generate_embedding', new_callable=AsyncMock) as mock_embed:
        mock_embed.return_value = [0.1] * 1024
        
        with patch.object(service, 'add_document', new_callable=AsyncMock) as mock_add:
            mock_add.return_value = 1
            
            # Test document creation with summarization
            doc_id = await service.add_document_with_summary(
                content="This is a long document. " * 20,
                title="Test Document",
                auto_summarize=True
            )
            
            assert doc_id == 1
            
            # Verify summarization was applied
            call_args = mock_add.call_args
            metadata = call_args.kwargs.get('metadata', {})
            assert metadata.get('summarized') is True
            assert 'summary' in metadata


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])