"""
Vector Database Service with Snowflake Arctic embeddings.

This service provides document storage and retrieval using vector embeddings
for semantic search capabilities in the AI agent system.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

from sentence_transformers import SentenceTransformer
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.database.connection import db_manager
from app.database.models import VectorSearchResult, DocumentCreate, DocumentResponse
from app.config import settings

logger = logging.getLogger(__name__)


class VectorDBService:
    """
    Vector database service for document storage and semantic search.
    
    Uses Snowflake Arctic embeddings for high-quality vector representations
    and PostgreSQL with pgvector extension for efficient similarity search.
    """
    
    def __init__(self):
        self.model = None
        self.executor = ThreadPoolExecutor(max_workers=4)
        self._model_lock = asyncio.Lock()
        self.embedding_dimension = 1024  # Snowflake Arctic embedding dimension
        
    async def initialize(self):
        """Initialize the embedding model."""
        if self.model is None:
            async with self._model_lock:
                if self.model is None:  # Double-check pattern
                    logger.info("Loading Snowflake Arctic embedding model...")
                    # Load model in thread pool to avoid blocking
                    loop = asyncio.get_event_loop()
                    self.model = await loop.run_in_executor(
                        self.executor,
                        self._load_model
                    )
                    logger.info("Snowflake Arctic embedding model loaded successfully")
    
    def _load_model(self) -> SentenceTransformer:
        """Load the Snowflake Arctic embedding model."""
        return SentenceTransformer('Snowflake/snowflake-arctic-embed-l-v2.0')
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for the given text."""
        if self.model is None:
            await self.initialize()
        
        # Run embedding generation in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            self.executor,
            lambda: self.model.encode(text).tolist()
        )
        
        return embedding
    
    async def add_document(
        self, 
        content: str, 
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        document_type: str = "text"
    ) -> int:
        """
        Add a document to the vector database.
        
        Args:
            content: The document content to store
            title: Optional document title
            metadata: Optional metadata dictionary
            source: Optional source identifier
            document_type: Type of document (default: "text")
            
        Returns:
            The ID of the inserted document
        """
        try:
            # Generate embedding for the content
            embedding = await self._generate_embedding(content)
            
            # Insert document with embedding
            query = """
            INSERT INTO documents (title, content, embedding, metadata, source, document_type)
            VALUES ($1, $2, $3::vector, $4, $5, $6)
            RETURNING id
            """
            
            async with db_manager.get_connection() as conn:
                document_id = await conn.fetchval(
                    query,
                    title,
                    content,
                    embedding,
                    metadata or {},
                    source,
                    document_type
                )
            
            logger.info(f"Document added with ID: {document_id}")
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            raise
    
    async def update_document(
        self,
        document_id: int,
        content: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        document_type: Optional[str] = None
    ) -> bool:
        """
        Update an existing document in the vector database.
        
        Args:
            document_id: ID of the document to update
            content: New content (will regenerate embedding if provided)
            title: New title
            metadata: New metadata
            source: New source
            document_type: New document type
            
        Returns:
            True if document was updated, False if not found
        """
        try:
            # Build update query dynamically based on provided fields
            update_fields = []
            values = []
            param_count = 1
            
            if title is not None:
                update_fields.append(f"title = ${param_count}")
                values.append(title)
                param_count += 1
            
            if content is not None:
                # Generate new embedding for updated content
                embedding = await self._generate_embedding(content)
                update_fields.append(f"content = ${param_count}")
                values.append(content)
                param_count += 1
                update_fields.append(f"embedding = ${param_count}::vector")
                values.append(embedding)
                param_count += 1
            
            if metadata is not None:
                update_fields.append(f"metadata = ${param_count}")
                values.append(metadata)
                param_count += 1
            
            if source is not None:
                update_fields.append(f"source = ${param_count}")
                values.append(source)
                param_count += 1
            
            if document_type is not None:
                update_fields.append(f"document_type = ${param_count}")
                values.append(document_type)
                param_count += 1
            
            if not update_fields:
                return False  # Nothing to update
            
            # Add updated_at field
            update_fields.append("updated_at = CURRENT_TIMESTAMP")
            
            # Add document_id for WHERE clause
            values.append(document_id)
            
            query = f"""
            UPDATE documents 
            SET {', '.join(update_fields)}
            WHERE id = ${param_count}
            """
            
            async with db_manager.get_connection() as conn:
                result = await conn.execute(query, *values)
                updated = result.split()[-1] == "1"  # Check if one row was updated
            
            if updated:
                logger.info(f"Document {document_id} updated successfully")
            else:
                logger.warning(f"Document {document_id} not found for update")
            
            return updated
            
        except Exception as e:
            logger.error(f"Error updating document {document_id}: {e}")
            raise
    
    async def delete_document(self, document_id: int) -> bool:
        """
        Delete a document from the vector database.
        
        Args:
            document_id: ID of the document to delete
            
        Returns:
            True if document was deleted, False if not found
        """
        try:
            query = "DELETE FROM documents WHERE id = $1"
            
            async with db_manager.get_connection() as conn:
                result = await conn.execute(query, document_id)
                deleted = result.split()[-1] == "1"  # Check if one row was deleted
            
            if deleted:
                logger.info(f"Document {document_id} deleted successfully")
            else:
                logger.warning(f"Document {document_id} not found for deletion")
            
            return deleted
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            raise
    
    async def search(
        self, 
        query: str, 
        top_k: int = 5,
        similarity_threshold: float = 0.7,
        document_type: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[VectorSearchResult]:
        """
        Perform vector similarity search.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            similarity_threshold: Minimum similarity score (0-1)
            document_type: Filter by document type
            source: Filter by source
            
        Returns:
            List of search results with similarity scores
        """
        try:
            # Generate embedding for the query
            query_embedding = await self._generate_embedding(query)
            
            # Build search query with optional filters
            where_conditions = ["1 - (embedding <=> $1::vector) > $2"]
            params = [query_embedding, similarity_threshold]
            param_count = 3
            
            if document_type:
                where_conditions.append(f"document_type = ${param_count}")
                params.append(document_type)
                param_count += 1
            
            if source:
                where_conditions.append(f"source = ${param_count}")
                params.append(source)
                param_count += 1
            
            params.append(top_k)  # LIMIT parameter
            
            search_query = f"""
            SELECT id, title, content, metadata, 
                   1 - (embedding <=> $1::vector) as similarity_score
            FROM documents
            WHERE {' AND '.join(where_conditions)}
            ORDER BY embedding <=> $1::vector
            LIMIT ${param_count}
            """
            
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch(search_query, *params)
            
            # Convert results to VectorSearchResult objects
            results = []
            for row in rows:
                result = VectorSearchResult(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    metadata=row['metadata'] or {},
                    similarity_score=float(row['similarity_score'])
                )
                results.append(result)
            
            logger.info(f"Vector search returned {len(results)} results for query: {query[:50]}...")
            return results
            
        except Exception as e:
            logger.error(f"Error performing vector search: {e}")
            raise
    
    async def get_document(self, document_id: int) -> Optional[DocumentResponse]:
        """
        Get a document by ID.
        
        Args:
            document_id: ID of the document to retrieve
            
        Returns:
            Document data or None if not found
        """
        try:
            query = """
            SELECT id, title, content, metadata, source, document_type, created_at, updated_at
            FROM documents
            WHERE id = $1
            """
            
            async with db_manager.get_connection() as conn:
                row = await conn.fetchrow(query, document_id)
            
            if row:
                return DocumentResponse(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    metadata=row['metadata'] or {},
                    source=row['source'],
                    document_type=row['document_type'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {document_id}: {e}")
            raise
    
    async def list_documents(
        self,
        limit: int = 50,
        offset: int = 0,
        document_type: Optional[str] = None,
        source: Optional[str] = None
    ) -> List[DocumentResponse]:
        """
        List documents with optional filtering.
        
        Args:
            limit: Maximum number of documents to return
            offset: Number of documents to skip
            document_type: Filter by document type
            source: Filter by source
            
        Returns:
            List of documents
        """
        try:
            where_conditions = []
            params = []
            param_count = 1
            
            if document_type:
                where_conditions.append(f"document_type = ${param_count}")
                params.append(document_type)
                param_count += 1
            
            if source:
                where_conditions.append(f"source = ${param_count}")
                params.append(source)
                param_count += 1
            
            params.extend([limit, offset])
            
            where_clause = ""
            if where_conditions:
                where_clause = f"WHERE {' AND '.join(where_conditions)}"
            
            query = f"""
            SELECT id, title, content, metadata, source, document_type, created_at, updated_at
            FROM documents
            {where_clause}
            ORDER BY created_at DESC
            LIMIT ${param_count} OFFSET ${param_count + 1}
            """
            
            async with db_manager.get_connection() as conn:
                rows = await conn.fetch(query, *params)
            
            documents = []
            for row in rows:
                doc = DocumentResponse(
                    id=row['id'],
                    title=row['title'],
                    content=row['content'],
                    metadata=row['metadata'] or {},
                    source=row['source'],
                    document_type=row['document_type'],
                    created_at=row['created_at'],
                    updated_at=row['updated_at']
                )
                documents.append(doc)
            
            return documents
            
        except Exception as e:
            logger.error(f"Error listing documents: {e}")
            raise
    
    async def get_document_count(
        self,
        document_type: Optional[str] = None,
        source: Optional[str] = None
    ) -> int:
        """
        Get the total count of documents with optional filtering.
        
        Args:
            document_type: Filter by document type
            source: Filter by source
            
        Returns:
            Total number of documents
        """
        try:
            where_conditions = []
            params = []
            param_count = 1
            
            if document_type:
                where_conditions.append(f"document_type = ${param_count}")
                params.append(document_type)
                param_count += 1
            
            if source:
                where_conditions.append(f"source = ${param_count}")
                params.append(source)
                param_count += 1
            
            where_clause = ""
            if where_conditions:
                where_clause = f"WHERE {' AND '.join(where_conditions)}"
            
            query = f"SELECT COUNT(*) FROM documents {where_clause}"
            
            async with db_manager.get_connection() as conn:
                count = await conn.fetchval(query, *params)
            
            return count
            
        except Exception as e:
            logger.error(f"Error getting document count: {e}")
            raise
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Check the health of the vector database service.
        
        Returns:
            Health status information
        """
        try:
            # Check if model is loaded
            model_status = "loaded" if self.model is not None else "not_loaded"
            
            # Check database connection and vector extension
            async with db_manager.get_connection() as conn:
                # Test basic query
                await conn.fetchval("SELECT 1")
                
                # Test vector extension
                await conn.fetchval("SELECT vector_dims(ARRAY[1,2,3]::vector)")
                
                # Get document count
                doc_count = await conn.fetchval("SELECT COUNT(*) FROM documents")
            
            return {
                "status": "healthy",
                "model_status": model_status,
                "embedding_dimension": self.embedding_dimension,
                "document_count": doc_count,
                "database_connection": "ok",
                "vector_extension": "ok"
            }
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "model_status": "unknown",
                "database_connection": "error"
            }


# Global service instance
vector_service = VectorDBService()


async def get_vector_service() -> VectorDBService:
    """Get the vector database service instance."""
    return vector_service