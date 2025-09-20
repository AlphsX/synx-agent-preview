# Vector Database Service

This module provides vector database functionality for the AI Agent backend, enabling semantic search and document storage using PostgreSQL with pgvector extension and Snowflake Arctic embeddings.

## Overview

The Vector Database Service consists of three main components:

1. **VectorDBService** - Core service class for vector operations
2. **Router** - FastAPI endpoints for vector database operations
3. **Models** - Pydantic models for request/response serialization

## Features

- **Document Storage**: Store documents with automatic vector embedding generation
- **Semantic Search**: Find similar documents using vector similarity search
- **Document Management**: Full CRUD operations for documents
- **Bulk Operations**: Efficient bulk document creation
- **Filtering**: Search and list documents by type, source, and other metadata
- **Health Monitoring**: Service health checks and statistics

## Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   FastAPI       │    │  VectorDBService │    │   PostgreSQL    │
│   Router        │───▶│                 │───▶│   + pgvector    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌─────────────────┐
                       │  Snowflake      │
                       │  Arctic Model   │
                       │  (Embeddings)   │
                       └─────────────────┘
```

## API Endpoints

### Document Management

- `POST /api/vector/documents` - Create a new document
- `GET /api/vector/documents/{id}` - Get document by ID
- `PUT /api/vector/documents/{id}` - Update document
- `DELETE /api/vector/documents/{id}` - Delete document
- `GET /api/vector/documents` - List documents with pagination
- `POST /api/vector/documents/bulk` - Create multiple documents

### Search Operations

- `POST /api/vector/search` - Vector similarity search (JSON body)
- `GET /api/vector/search` - Vector similarity search (query parameters)

### Service Management

- `GET /api/vector/health` - Service health check
- `GET /api/vector/stats` - Database statistics

## Usage Examples

### Creating a Document

```python
import httpx

# Create a document
document_data = {
    "title": "AI and Machine Learning Guide",
    "content": "Artificial intelligence and machine learning are transforming industries...",
    "metadata": {"category": "technology", "tags": ["AI", "ML"]},
    "source": "knowledge_base",
    "document_type": "article"
}

response = httpx.post("http://localhost:8000/api/vector/documents", json=document_data)
document = response.json()
print(f"Created document with ID: {document['id']}")
```

### Searching Documents

```python
# Search for similar documents
search_data = {
    "query": "machine learning algorithms",
    "top_k": 5,
    "similarity_threshold": 0.7,
    "document_type": "article"
}

response = httpx.post("http://localhost:8000/api/vector/search", json=search_data)
results = response.json()

for result in results:
    print(f"Title: {result['title']}")
    print(f"Similarity: {result['similarity_score']:.3f}")
    print(f"Content: {result['content'][:100]}...")
    print("---")
```

### Using the Service Directly

```python
from app.vector.service import vector_service

# Initialize the service
await vector_service.initialize()

# Add a document
doc_id = await vector_service.add_document(
    content="Python is a versatile programming language",
    title="Python Programming",
    metadata={"language": "python", "difficulty": "beginner"}
)

# Search for similar documents
results = await vector_service.search(
    query="programming languages",
    top_k=3,
    similarity_threshold=0.6
)

for result in results:
    print(f"{result.title}: {result.similarity_score:.3f}")
```

## Configuration

The vector service uses the following configuration from `app.config`:

- `ARCTIC_MODEL_NAME`: Snowflake Arctic model name (default: "Snowflake/snowflake-arctic-embed-m")
- `VECTOR_DIMENSION`: Embedding dimension (default: 1024)
- `MAX_VECTOR_RESULTS`: Maximum search results (default: 10)
- `DATABASE_URL`: PostgreSQL connection string

## Database Schema

The service uses the `documents` table with the following structure:

```sql
CREATE TABLE documents (
    id SERIAL PRIMARY KEY,
    title VARCHAR(500),
    content TEXT NOT NULL,
    embedding VECTOR(1024),
    metadata JSONB DEFAULT '{}',
    source VARCHAR(255),
    document_type VARCHAR(100) DEFAULT 'text',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Vector similarity search index
CREATE INDEX idx_documents_embedding ON documents 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);
```

## Performance Considerations

### Embedding Generation

- Embeddings are generated using the Snowflake Arctic model
- Generation runs in a thread pool to avoid blocking async operations
- Model is loaded once and reused for all operations

### Vector Search

- Uses cosine similarity with IVFFlat index for efficient search
- Configurable similarity threshold to filter low-quality matches
- Supports filtering by document type and source

### Bulk Operations

- Bulk document creation processes documents sequentially
- Consider using background tasks for large bulk operations
- Monitor memory usage when processing many documents

## Error Handling

The service implements comprehensive error handling:

- **Database Connection Errors**: Graceful degradation with informative error messages
- **Model Loading Errors**: Fallback to error responses if embedding model fails
- **Validation Errors**: Proper HTTP status codes and error details
- **Resource Not Found**: 404 responses for missing documents

## Testing

Run the test suite to verify functionality:

```bash
# Test service structure and imports
python backend/test_vector_simple.py

# Test API endpoints (requires mocking)
python backend/test_vector_endpoints.py

# Full integration test (requires database)
python backend/test_vector_service.py
```

## Integration with Chat Service

The vector service integrates with the enhanced chat service for context-aware responses:

```python
from app.vector.service import vector_service

# In chat service
async def get_relevant_context(self, message: str):
    # Search for relevant documents
    results = await vector_service.search(
        query=message,
        top_k=3,
        similarity_threshold=0.7
    )
    
    # Extract content for context
    context = [result.content for result in results]
    return context
```

## Monitoring and Maintenance

### Health Checks

The service provides health check endpoints that verify:
- Database connectivity
- Vector extension availability
- Embedding model status
- Document count statistics

### Logging

All operations are logged with appropriate levels:
- INFO: Successful operations and initialization
- WARNING: Non-critical issues (e.g., document not found)
- ERROR: Critical failures requiring attention

### Metrics

The stats endpoint provides:
- Total document count
- Document type distribution
- Top sources by document count
- Embedding dimension information

## Future Enhancements

Planned improvements include:

1. **Batch Processing**: Async batch operations for better performance
2. **Caching**: Redis caching for frequently accessed documents
3. **Indexing**: Additional indexes for metadata filtering
4. **Compression**: Vector compression for storage efficiency
5. **Replication**: Read replicas for scaling search operations

## Dependencies

- `sentence-transformers`: For Snowflake Arctic embeddings
- `asyncpg`: Async PostgreSQL driver
- `pgvector`: PostgreSQL vector extension
- `fastapi`: Web framework for API endpoints
- `pydantic`: Data validation and serialization