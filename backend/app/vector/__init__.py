"""
Vector database module for semantic search and document storage.
"""

from .service import VectorDBService, vector_service, get_vector_service

__all__ = ["VectorDBService", "vector_service", "get_vector_service"]