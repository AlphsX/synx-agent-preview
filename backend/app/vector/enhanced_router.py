"""
Enhanced API endpoints for advanced vector database operations.

Provides REST endpoints for hybrid search, document clustering, 
summarization, and semantic caching functionality.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.vector.enhanced_service import get_enhanced_vector_service, EnhancedVectorDBService
from app.database.models import (
    DocumentCreate, 
    DocumentResponse, 
    VectorSearchResult
)

router = APIRouter(prefix="/vector/enhanced", tags=["vector-enhanced"])


class HybridSearchRequest(BaseModel):
    """Request model for hybrid search."""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    vector_weight: float = Field(default=0.7, ge=0.0, le=1.0, description="Weight for vector similarity")
    keyword_weight: float = Field(default=0.3, ge=0.0, le=1.0, description="Weight for keyword matching")
    similarity_threshold: float = Field(default=0.6, ge=0.0, le=1.0, description="Minimum combined similarity score")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    source: Optional[str] = Field(None, description="Filter by source")
    use_cache: bool = Field(default=True, description="Whether to use semantic caching")


class DocumentCreateWithSummary(DocumentCreate):
    """Request model for creating documents with automatic summarization."""
    auto_summarize: bool = Field(default=True, description="Whether to automatically summarize large content")


class ClusteringRequest(BaseModel):
    """Request model for document clustering."""
    document_type: Optional[str] = Field(None, description="Filter by document type")
    source: Optional[str] = Field(None, description="Filter by source")
    min_documents: int = Field(default=5, ge=3, le=50, description="Minimum documents required for clustering")


class RecommendationRequest(BaseModel):
    """Request model for document recommendations."""
    document_id: int = Field(..., description="Reference document ID")
    recommendation_type: str = Field(default="similar", description="Type of recommendation: 'similar' or 'cluster'")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of recommendations to return")


class HybridSearchResponse(BaseModel):
    """Response model for hybrid search results."""
    results: List[VectorSearchResult]
    search_metadata: Dict[str, Any] = Field(default_factory=dict)


class ClusteringResponse(BaseModel):
    """Response model for clustering results."""
    clusters: Dict[str, Any] = Field(default_factory=dict)
    topics: Dict[str, List[str]] = Field(default_factory=dict)
    detailed_clusters: Optional[Dict[str, Any]] = None
    n_clusters: Optional[int] = None
    total_documents: Optional[int] = None
    error: Optional[str] = None


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document_with_summary(
    document: DocumentCreateWithSummary,
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Create a new document with automatic summarization for large content.
    
    This endpoint adds a document to the vector database with automatic
    summarization if the content is large enough to benefit from it.
    """
    try:
        document_id = await enhanced_service.add_document_with_summary(
            content=document.content,
            title=document.title,
            metadata=document.metadata,
            source=document.source,
            document_type=document.document_type,
            auto_summarize=document.auto_summarize
        )
        
        # Retrieve the created document to return full response
        created_document = await enhanced_service.get_document(document_id)
        if not created_document:
            raise HTTPException(status_code=500, detail="Failed to retrieve created document")
        
        return created_document
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.post("/search/hybrid", response_model=HybridSearchResponse)
async def hybrid_search(
    search_request: HybridSearchRequest,
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Perform hybrid search combining vector similarity and keyword matching.
    
    This endpoint provides advanced search capabilities that combine the semantic
    understanding of vector embeddings with traditional keyword matching for
    more comprehensive and accurate search results.
    """
    try:
        results = await enhanced_service.hybrid_search(
            query=search_request.query,
            top_k=search_request.top_k,
            vector_weight=search_request.vector_weight,
            keyword_weight=search_request.keyword_weight,
            similarity_threshold=search_request.similarity_threshold,
            document_type=search_request.document_type,
            source=search_request.source,
            use_cache=search_request.use_cache
        )
        
        search_metadata = {
            "query": search_request.query,
            "vector_weight": search_request.vector_weight,
            "keyword_weight": search_request.keyword_weight,
            "results_count": len(results),
            "search_type": "hybrid"
        }
        
        return HybridSearchResponse(
            results=results,
            search_metadata=search_metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform hybrid search: {str(e)}")


@router.get("/search/hybrid")
async def hybrid_search_get(
    query: str = Query(..., description="Search query text"),
    top_k: int = Query(default=5, ge=1, le=50, description="Number of results to return"),
    vector_weight: float = Query(default=0.7, ge=0.0, le=1.0, description="Weight for vector similarity"),
    keyword_weight: float = Query(default=0.3, ge=0.0, le=1.0, description="Weight for keyword matching"),
    similarity_threshold: float = Query(default=0.6, ge=0.0, le=1.0, description="Minimum combined similarity score"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    use_cache: bool = Query(default=True, description="Whether to use semantic caching"),
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Perform hybrid search via GET request.
    
    Alternative endpoint for hybrid search using query parameters.
    """
    try:
        results = await enhanced_service.hybrid_search(
            query=query,
            top_k=top_k,
            vector_weight=vector_weight,
            keyword_weight=keyword_weight,
            similarity_threshold=similarity_threshold,
            document_type=document_type,
            source=source,
            use_cache=use_cache
        )
        
        search_metadata = {
            "query": query,
            "vector_weight": vector_weight,
            "keyword_weight": keyword_weight,
            "results_count": len(results),
            "search_type": "hybrid"
        }
        
        return HybridSearchResponse(
            results=results,
            search_metadata=search_metadata
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to perform hybrid search: {str(e)}")


@router.post("/clustering", response_model=ClusteringResponse)
async def cluster_documents(
    clustering_request: ClusteringRequest,
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Cluster documents by topic and return cluster information.
    
    This endpoint analyzes documents to identify topical clusters and provides
    insights into document organization and content themes.
    """
    try:
        cluster_result = await enhanced_service.cluster_documents_by_topic(
            document_type=clustering_request.document_type,
            source=clustering_request.source,
            min_documents=clustering_request.min_documents
        )
        
        return ClusteringResponse(**cluster_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cluster documents: {str(e)}")


@router.get("/clustering")
async def cluster_documents_get(
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    min_documents: int = Query(default=5, ge=3, le=50, description="Minimum documents required for clustering"),
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Cluster documents via GET request.
    
    Alternative endpoint for document clustering using query parameters.
    """
    try:
        cluster_result = await enhanced_service.cluster_documents_by_topic(
            document_type=document_type,
            source=source,
            min_documents=min_documents
        )
        
        return ClusteringResponse(**cluster_result)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to cluster documents: {str(e)}")


@router.post("/recommendations", response_model=List[VectorSearchResult])
async def get_document_recommendations(
    recommendation_request: RecommendationRequest,
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Get document recommendations based on clustering or similarity.
    
    This endpoint provides intelligent document recommendations using either
    cluster-based or similarity-based approaches.
    """
    try:
        recommendations = await enhanced_service.get_document_recommendations(
            document_id=recommendation_request.document_id,
            recommendation_type=recommendation_request.recommendation_type,
            top_k=recommendation_request.top_k
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/recommendations/{document_id}")
async def get_document_recommendations_get(
    document_id: int,
    recommendation_type: str = Query(default="similar", description="Type of recommendation: 'similar' or 'cluster'"),
    top_k: int = Query(default=5, ge=1, le=20, description="Number of recommendations to return"),
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Get document recommendations via GET request.
    
    Alternative endpoint for document recommendations using path and query parameters.
    """
    try:
        recommendations = await enhanced_service.get_document_recommendations(
            document_id=document_id,
            recommendation_type=recommendation_type,
            top_k=top_k
        )
        
        return recommendations
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get recommendations: {str(e)}")


@router.get("/cache/stats")
async def get_cache_stats(
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Get semantic cache statistics.
    
    Returns information about cache usage, hit rates, and performance metrics.
    """
    try:
        stats = await enhanced_service.get_semantic_cache_stats()
        return stats
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get cache stats: {str(e)}")


@router.delete("/cache")
async def clear_cache(
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Clear the semantic cache.
    
    Removes all cached query responses. Use with caution as this will
    impact performance until the cache is rebuilt.
    """
    try:
        await enhanced_service.clear_semantic_cache()
        return {"message": "Semantic cache cleared successfully"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear cache: {str(e)}")


@router.get("/health")
async def enhanced_health_check(
    enhanced_service: EnhancedVectorDBService = Depends(get_enhanced_vector_service)
):
    """
    Check the health of the enhanced vector database service.
    
    Returns comprehensive status information about the service and all
    enhanced features including caching, clustering, and summarization.
    """
    try:
        health_status = await enhanced_service.health_check_enhanced()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Enhanced health check failed: {str(e)}")


@router.get("/features")
async def get_available_features():
    """
    Get information about available enhanced features.
    
    Returns a description of all enhanced vector database capabilities.
    """
    return {
        "features": {
            "hybrid_search": {
                "description": "Combines vector similarity and keyword matching for comprehensive search",
                "endpoints": ["/search/hybrid"],
                "parameters": ["vector_weight", "keyword_weight", "similarity_threshold"]
            },
            "document_clustering": {
                "description": "Groups documents by topic using machine learning clustering",
                "endpoints": ["/clustering"],
                "parameters": ["document_type", "source", "min_documents"]
            },
            "automatic_summarization": {
                "description": "Automatically generates summaries for large documents",
                "endpoints": ["/documents"],
                "parameters": ["auto_summarize"]
            },
            "semantic_caching": {
                "description": "Caches frequently asked questions using semantic similarity",
                "endpoints": ["/cache/stats", "/cache"],
                "parameters": ["use_cache"]
            },
            "document_recommendations": {
                "description": "Provides intelligent document recommendations",
                "endpoints": ["/recommendations"],
                "parameters": ["recommendation_type", "top_k"]
            }
        },
        "version": "1.0.0",
        "status": "active"
    }