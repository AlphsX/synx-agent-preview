"""
API endpoints for vector database operations.

Provides REST endpoints for document management and vector search functionality.
"""

from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field

from app.vector.service import get_vector_service, VectorDBService
from app.database.models import (
    DocumentCreate, 
    DocumentResponse, 
    VectorSearchResult
)

router = APIRouter(prefix="/vector", tags=["vector"])


class DocumentUpdateRequest(BaseModel):
    """Request model for updating documents."""
    title: Optional[str] = None
    content: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    source: Optional[str] = None
    document_type: Optional[str] = None


class VectorSearchRequest(BaseModel):
    """Request model for vector search."""
    query: str = Field(..., description="Search query text")
    top_k: int = Field(default=5, ge=1, le=50, description="Number of results to return")
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score")
    document_type: Optional[str] = Field(None, description="Filter by document type")
    source: Optional[str] = Field(None, description="Filter by source")


class BulkDocumentCreate(BaseModel):
    """Request model for bulk document creation."""
    documents: List[DocumentCreate] = Field(..., description="List of documents to create")


class DocumentListResponse(BaseModel):
    """Response model for document listing."""
    documents: List[DocumentResponse]
    total_count: int
    limit: int
    offset: int


@router.post("/documents", response_model=DocumentResponse, status_code=201)
async def create_document(
    document: DocumentCreate,
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Create a new document with vector embedding.
    
    This endpoint adds a document to the vector database, automatically
    generating embeddings using the Snowflake Arctic model.
    """
    try:
        document_id = await vector_service.add_document(
            content=document.content,
            title=document.title,
            metadata=document.metadata,
            source=document.source,
            document_type=document.document_type
        )
        
        # Retrieve the created document to return full response
        created_document = await vector_service.get_document(document_id)
        if not created_document:
            raise HTTPException(status_code=500, detail="Failed to retrieve created document")
        
        return created_document
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create document: {str(e)}")


@router.post("/documents/bulk", response_model=List[DocumentResponse], status_code=201)
async def create_documents_bulk(
    request: BulkDocumentCreate,
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Create multiple documents in bulk.
    
    This endpoint allows efficient creation of multiple documents at once.
    Each document will have its embedding generated automatically.
    """
    try:
        created_documents = []
        
        for document in request.documents:
            document_id = await vector_service.add_document(
                content=document.content,
                title=document.title,
                metadata=document.metadata,
                source=document.source,
                document_type=document.document_type
            )
            
            created_document = await vector_service.get_document(document_id)
            if created_document:
                created_documents.append(created_document)
        
        return created_documents
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create documents: {str(e)}")


@router.get("/documents/{document_id}", response_model=DocumentResponse)
async def get_document(
    document_id: int,
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Get a document by ID.
    
    Retrieves a specific document from the vector database.
    """
    try:
        document = await vector_service.get_document(document_id)
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
        
        return document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get document: {str(e)}")


@router.put("/documents/{document_id}", response_model=DocumentResponse)
async def update_document(
    document_id: int,
    update_request: DocumentUpdateRequest,
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Update an existing document.
    
    Updates document fields and regenerates embeddings if content is changed.
    """
    try:
        updated = await vector_service.update_document(
            document_id=document_id,
            content=update_request.content,
            title=update_request.title,
            metadata=update_request.metadata,
            source=update_request.source,
            document_type=update_request.document_type
        )
        
        if not updated:
            raise HTTPException(status_code=404, detail="Document not found")
        
        # Return updated document
        updated_document = await vector_service.get_document(document_id)
        if not updated_document:
            raise HTTPException(status_code=500, detail="Failed to retrieve updated document")
        
        return updated_document
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update document: {str(e)}")


@router.delete("/documents/{document_id}", status_code=204)
async def delete_document(
    document_id: int,
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Delete a document by ID.
    
    Removes a document from the vector database.
    """
    try:
        deleted = await vector_service.delete_document(document_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Document not found")
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete document: {str(e)}")


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents(
    limit: int = Query(default=50, ge=1, le=100, description="Maximum number of documents to return"),
    offset: int = Query(default=0, ge=0, description="Number of documents to skip"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    List documents with optional filtering.
    
    Returns a paginated list of documents with optional filters.
    """
    try:
        documents = await vector_service.list_documents(
            limit=limit,
            offset=offset,
            document_type=document_type,
            source=source
        )
        
        total_count = await vector_service.get_document_count(
            document_type=document_type,
            source=source
        )
        
        return DocumentListResponse(
            documents=documents,
            total_count=total_count,
            limit=limit,
            offset=offset
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list documents: {str(e)}")


@router.post("/search", response_model=List[VectorSearchResult])
async def search_documents(
    search_request: VectorSearchRequest,
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Perform vector similarity search.
    
    Searches for documents similar to the query using vector embeddings.
    Returns results ranked by similarity score.
    """
    try:
        results = await vector_service.search(
            query=search_request.query,
            top_k=search_request.top_k,
            similarity_threshold=search_request.similarity_threshold,
            document_type=search_request.document_type,
            source=search_request.source
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")


@router.get("/search")
async def search_documents_get(
    query: str = Query(..., description="Search query text"),
    top_k: int = Query(default=5, ge=1, le=50, description="Number of results to return"),
    similarity_threshold: float = Query(default=0.7, ge=0.0, le=1.0, description="Minimum similarity score"),
    document_type: Optional[str] = Query(None, description="Filter by document type"),
    source: Optional[str] = Query(None, description="Filter by source"),
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Perform vector similarity search via GET request.
    
    Alternative endpoint for vector search using query parameters.
    """
    try:
        results = await vector_service.search(
            query=query,
            top_k=top_k,
            similarity_threshold=similarity_threshold,
            document_type=document_type,
            source=source
        )
        
        return results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to search documents: {str(e)}")


@router.get("/health")
async def health_check(
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Check the health of the vector database service.
    
    Returns status information about the service and its dependencies.
    """
    try:
        health_status = await vector_service.health_check()
        
        if health_status["status"] == "healthy":
            return health_status
        else:
            raise HTTPException(status_code=503, detail=health_status)
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Health check failed: {str(e)}")


@router.get("/stats")
async def get_stats(
    vector_service: VectorDBService = Depends(get_vector_service)
):
    """
    Get statistics about the vector database.
    
    Returns information about document counts, types, and sources.
    """
    try:
        total_documents = await vector_service.get_document_count()
        
        # Get document type distribution
        from app.database.connection import db_manager
        async with db_manager.get_connection() as conn:
            type_stats = await conn.fetch("""
                SELECT document_type, COUNT(*) as count
                FROM documents
                GROUP BY document_type
                ORDER BY count DESC
            """)
            
            source_stats = await conn.fetch("""
                SELECT source, COUNT(*) as count
                FROM documents
                WHERE source IS NOT NULL
                GROUP BY source
                ORDER BY count DESC
                LIMIT 10
            """)
        
        return {
            "total_documents": total_documents,
            "document_types": [{"type": row["document_type"], "count": row["count"]} for row in type_stats],
            "top_sources": [{"source": row["source"], "count": row["count"]} for row in source_stats],
            "embedding_dimension": vector_service.embedding_dimension
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")