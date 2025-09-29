"""
Enhanced Vector Database Service with advanced semantic search features.

This service extends the basic vector database with:
- Hybrid search combining vector similarity and keyword matching
- Document clustering and topic modeling capabilities
- Automatic document summarization for large content
- Semantic caching for frequently asked questions
"""

import logging
import hashlib
import json
from typing import List, Dict, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from sentence_transformers import SentenceTransformer
from sklearn.cluster import KMeans
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.tokenize import word_tokenize, sent_tokenize
    from nltk.stem import PorterStemmer
    NLTK_AVAILABLE = True
except ImportError:
    NLTK_AVAILABLE = False
import re

from app.database.connection import db_manager
from app.database.models import VectorSearchResult, DocumentResponse
from app.vector.service import VectorDBService
from app.config import settings

logger = logging.getLogger(__name__)

# Download required NLTK data if available
if NLTK_AVAILABLE:
    try:
        nltk.data.find('tokenizers/punkt')
        nltk.data.find('corpora/stopwords')
    except LookupError:
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
        except:
            NLTK_AVAILABLE = False
            logger.warning("NLTK data not available, using fallback text processing")


class DocumentSummarizer:
    """Handles automatic document summarization for large content."""
    
    def __init__(self):
        self.max_summary_length = 500  # Maximum summary length in characters
        self.sentence_count_threshold = 10  # Minimum sentences to trigger summarization
    
    def should_summarize(self, content: str) -> bool:
        """Check if content should be summarized based on length."""
        if NLTK_AVAILABLE:
            sentences = sent_tokenize(content)
            return len(sentences) > self.sentence_count_threshold or len(content) > 2000
        else:
            # Fallback: estimate sentences by counting periods
            sentence_count = content.count('.') + content.count('!') + content.count('?')
            return sentence_count > self.sentence_count_threshold or len(content) > 2000
    
    def extractive_summarize(self, content: str, max_sentences: int = 3) -> str:
        """
        Create extractive summary by selecting most important sentences.
        Uses TF-IDF scoring to rank sentences.
        """
        try:
            if NLTK_AVAILABLE:
                sentences = sent_tokenize(content)
                if len(sentences) <= max_sentences:
                    return content
                
                # Preprocess sentences for TF-IDF
                stop_words = set(stopwords.words('english'))
                stemmer = PorterStemmer()
                
                processed_sentences = []
                for sentence in sentences:
                    # Clean and tokenize
                    words = word_tokenize(sentence.lower())
                    words = [stemmer.stem(word) for word in words 
                            if word.isalnum() and word not in stop_words]
                    processed_sentences.append(' '.join(words))
            else:
                # Fallback: simple sentence splitting
                sentences = re.split(r'[.!?]+', content)
                sentences = [s.strip() for s in sentences if s.strip()]
                if len(sentences) <= max_sentences:
                    return content
                
                # Simple preprocessing without NLTK
                stop_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should'}
                
                processed_sentences = []
                for sentence in sentences:
                    words = re.findall(r'\b\w+\b', sentence.lower())
                    words = [word for word in words if word not in stop_words and len(word) > 2]
                    processed_sentences.append(' '.join(words))
            
            # Calculate TF-IDF scores
            if len(processed_sentences) == 0:
                return content[:self.max_summary_length] + "..."
            
            vectorizer = TfidfVectorizer()
            tfidf_matrix = vectorizer.fit_transform(processed_sentences)
            
            # Calculate sentence scores (sum of TF-IDF scores)
            sentence_scores = np.array(tfidf_matrix.sum(axis=1)).flatten()
            
            # Get top sentences
            top_indices = sentence_scores.argsort()[-max_sentences:][::-1]
            top_indices = sorted(top_indices)  # Maintain original order
            
            summary_sentences = [sentences[i] for i in top_indices]
            summary = '. '.join(summary_sentences)
            if not summary.endswith('.'):
                summary += '.'
            
            # Truncate if still too long
            if len(summary) > self.max_summary_length:
                summary = summary[:self.max_summary_length] + "..."
            
            return summary
            
        except Exception as e:
            logger.warning(f"Summarization failed, using truncation: {e}")
            return content[:self.max_summary_length] + "..."


class DocumentClusterer:
    """Handles document clustering and topic modeling."""
    
    def __init__(self):
        self.min_cluster_size = 3
        self.max_clusters = 20
        self.tfidf_vectorizer = None
        self.cluster_model = None
        self.cluster_labels = {}
        self.cluster_topics = {}
    
    async def cluster_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Cluster documents based on content similarity.
        Returns cluster assignments and topic keywords.
        """
        try:
            if len(documents) < self.min_cluster_size:
                return {"clusters": {}, "topics": {}, "message": "Not enough documents for clustering"}
            
            # Extract content for clustering
            contents = [doc.get('content', '') for doc in documents]
            doc_ids = [doc.get('id') for doc in documents]
            
            # Create TF-IDF vectors
            self.tfidf_vectorizer = TfidfVectorizer(
                max_features=1000,
                stop_words='english',
                ngram_range=(1, 2),
                min_df=2,
                max_df=0.8
            )
            
            tfidf_matrix = self.tfidf_vectorizer.fit_transform(contents)
            
            # Determine optimal number of clusters
            n_clusters = min(self.max_clusters, max(2, len(documents) // 3))
            
            # Perform K-means clustering
            self.cluster_model = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = self.cluster_model.fit_predict(tfidf_matrix)
            
            # Organize results
            clusters = defaultdict(list)
            for doc_id, label in zip(doc_ids, cluster_labels):
                clusters[int(label)].append(doc_id)
            
            # Extract topic keywords for each cluster
            feature_names = self.tfidf_vectorizer.get_feature_names_out()
            topics = {}
            
            for cluster_id in range(n_clusters):
                cluster_docs = [i for i, label in enumerate(cluster_labels) if label == cluster_id]
                if cluster_docs:
                    # Get centroid of cluster
                    cluster_center = self.cluster_model.cluster_centers_[cluster_id]
                    
                    # Get top features for this cluster
                    top_indices = cluster_center.argsort()[-10:][::-1]
                    top_keywords = [feature_names[i] for i in top_indices if cluster_center[i] > 0]
                    
                    topics[cluster_id] = top_keywords[:5]  # Top 5 keywords
            
            # Store results
            self.cluster_labels = dict(clusters)
            self.cluster_topics = topics
            
            return {
                "clusters": dict(clusters),
                "topics": topics,
                "n_clusters": n_clusters,
                "total_documents": len(documents)
            }
            
        except Exception as e:
            logger.error(f"Document clustering failed: {e}")
            return {"error": str(e)}
    
    def get_similar_documents_by_cluster(self, document_id: int) -> List[int]:
        """Get documents in the same cluster as the given document."""
        for cluster_id, doc_ids in self.cluster_labels.items():
            if document_id in doc_ids:
                return [doc_id for doc_id in doc_ids if doc_id != document_id]
        return []


class SemanticCache:
    """Handles semantic caching for frequently asked questions."""
    
    def __init__(self):
        self.cache = {}  # query_hash -> (response, timestamp, access_count)
        self.similarity_threshold = 0.85
        self.cache_ttl = timedelta(hours=24)  # Cache TTL
        self.max_cache_size = 1000
        self.access_count_threshold = 3  # Minimum access count to keep in cache
    
    def _get_query_hash(self, query: str) -> str:
        """Generate hash for query normalization."""
        # Normalize query: lowercase, remove extra spaces, basic cleaning
        normalized = re.sub(r'\s+', ' ', query.lower().strip())
        return hashlib.md5(normalized.encode()).hexdigest()
    
    async def get_cached_response(self, query: str, query_embedding: List[float]) -> Optional[Dict[str, Any]]:
        """
        Check if query has a cached response based on semantic similarity.
        """
        try:
            query_hash = self._get_query_hash(query)
            
            # Check exact match first
            if query_hash in self.cache:
                response, timestamp, access_count = self.cache[query_hash]
                if datetime.now() - timestamp < self.cache_ttl:
                    # Update access count and timestamp
                    self.cache[query_hash] = (response, datetime.now(), access_count + 1)
                    logger.info(f"Cache hit (exact): {query[:50]}...")
                    return response
                else:
                    # Remove expired entry
                    del self.cache[query_hash]
            
            # Check semantic similarity with existing cached queries
            query_vector = np.array(query_embedding).reshape(1, -1)
            
            for cached_hash, (cached_response, timestamp, access_count) in self.cache.items():
                if datetime.now() - timestamp >= self.cache_ttl:
                    continue
                
                # Get cached query embedding (stored in response metadata)
                if 'query_embedding' in cached_response.get('metadata', {}):
                    cached_vector = np.array(cached_response['metadata']['query_embedding']).reshape(1, -1)
                    similarity = cosine_similarity(query_vector, cached_vector)[0][0]
                    
                    if similarity >= self.similarity_threshold:
                        # Update access count
                        self.cache[cached_hash] = (cached_response, datetime.now(), access_count + 1)
                        logger.info(f"Cache hit (semantic): {query[:50]}... (similarity: {similarity:.3f})")
                        return cached_response
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking semantic cache: {e}")
            return None
    
    async def cache_response(self, query: str, query_embedding: List[float], response: Dict[str, Any]):
        """Cache a query response with semantic information."""
        try:
            query_hash = self._get_query_hash(query)
            
            # Add query embedding to response metadata for similarity checking
            response_with_metadata = response.copy()
            if 'metadata' not in response_with_metadata:
                response_with_metadata['metadata'] = {}
            response_with_metadata['metadata']['query_embedding'] = query_embedding
            response_with_metadata['metadata']['original_query'] = query
            response_with_metadata['metadata']['cached_at'] = datetime.now().isoformat()
            
            # Store in cache
            self.cache[query_hash] = (response_with_metadata, datetime.now(), 1)
            
            # Clean up cache if it's too large
            await self._cleanup_cache()
            
            logger.info(f"Cached response for query: {query[:50]}...")
            
        except Exception as e:
            logger.error(f"Error caching response: {e}")
    
    async def _cleanup_cache(self):
        """Clean up expired and least accessed cache entries."""
        try:
            current_time = datetime.now()
            
            # Remove expired entries
            expired_keys = [
                key for key, (_, timestamp, _) in self.cache.items()
                if current_time - timestamp >= self.cache_ttl
            ]
            for key in expired_keys:
                del self.cache[key]
            
            # If still too large, remove least accessed entries
            if len(self.cache) > self.max_cache_size:
                # Sort by access count (ascending) and remove least accessed
                sorted_entries = sorted(
                    self.cache.items(),
                    key=lambda x: (x[1][2], x[1][1])  # Sort by access_count, then timestamp
                )
                
                entries_to_remove = len(self.cache) - self.max_cache_size
                for key, _ in sorted_entries[:entries_to_remove]:
                    del self.cache[key]
            
        except Exception as e:
            logger.error(f"Error cleaning up cache: {e}")
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {"total_entries": 0, "avg_access_count": 0}
        
        access_counts = [access_count for _, _, access_count in self.cache.values()]
        return {
            "total_entries": len(self.cache),
            "avg_access_count": sum(access_counts) / len(access_counts),
            "max_access_count": max(access_counts),
            "cache_size_limit": self.max_cache_size
        }


class EnhancedVectorDBService(VectorDBService):
    """
    Enhanced vector database service with advanced semantic search features.
    """
    
    def __init__(self):
        super().__init__()
        self.summarizer = DocumentSummarizer()
        self.clusterer = DocumentClusterer()
        self.semantic_cache = SemanticCache()
        self.keyword_vectorizer = None
        
    async def add_document_with_summary(
        self,
        content: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        source: Optional[str] = None,
        document_type: str = "text",
        auto_summarize: bool = True
    ) -> int:
        """
        Add document with automatic summarization for large content.
        """
        try:
            processed_content = content
            summary = None
            
            # Generate summary if content is large
            if auto_summarize and self.summarizer.should_summarize(content):
                summary = self.summarizer.extractive_summarize(content)
                logger.info(f"Generated summary for document: {len(content)} -> {len(summary)} chars")
            
            # Add summary to metadata
            if metadata is None:
                metadata = {}
            
            if summary:
                metadata['summary'] = summary
                metadata['original_length'] = len(content)
                metadata['summarized'] = True
            else:
                metadata['summarized'] = False
            
            # Use parent method to add document
            document_id = await super().add_document(
                content=processed_content,
                title=title,
                metadata=metadata,
                source=source,
                document_type=document_type
            )
            
            return document_id
            
        except Exception as e:
            logger.error(f"Error adding document with summary: {e}")
            raise 
   
    async def hybrid_search(
        self,
        query: str,
        top_k: int = 5,
        vector_weight: float = 0.7,
        keyword_weight: float = 0.3,
        similarity_threshold: float = 0.6,
        document_type: Optional[str] = None,
        source: Optional[str] = None,
        use_cache: bool = True
    ) -> List[VectorSearchResult]:
        """
        Perform hybrid search combining vector similarity and keyword matching.
        
        Args:
            query: Search query text
            top_k: Number of results to return
            vector_weight: Weight for vector similarity (0-1)
            keyword_weight: Weight for keyword matching (0-1)
            similarity_threshold: Minimum combined similarity score
            document_type: Filter by document type
            source: Filter by source
            use_cache: Whether to use semantic caching
            
        Returns:
            List of search results ranked by combined similarity
        """
        try:
            # Generate query embedding
            query_embedding = await self._generate_embedding(query)
            
            # Check semantic cache first
            if use_cache:
                cached_response = await self.semantic_cache.get_cached_response(query, query_embedding)
                if cached_response:
                    return cached_response.get('results', [])
            
            # Get all documents for keyword search
            async with db_manager.get_connection() as conn:
                # Build base query with filters
                where_conditions = ["1=1"]
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
                
                # Get documents with vector similarity
                vector_query = f"""
                SELECT id, title, content, metadata, 
                       1 - (embedding <=> $1::vector) as vector_similarity
                FROM documents
                WHERE {' AND '.join(where_conditions)}
                ORDER BY embedding <=> $1::vector
                LIMIT {top_k * 3}
                """
                
                vector_params = [query_embedding] + params
                vector_results = await conn.fetch(vector_query, *vector_params)
            
            if not vector_results:
                return []
            
            # Prepare documents for keyword search
            documents = []
            for row in vector_results:
                doc_content = row['content']
                # Use summary if available and original content is long
                if (row['metadata'] and 
                    row['metadata'].get('summarized') and 
                    len(doc_content) > 1000):
                    doc_content = row['metadata'].get('summary', doc_content)
                
                documents.append({
                    'id': row['id'],
                    'title': row['title'],
                    'content': row['content'],
                    'search_content': doc_content,  # Content used for keyword search
                    'metadata': row['metadata'] or {},
                    'vector_similarity': float(row['vector_similarity'])
                })
            
            # Perform keyword search using TF-IDF
            keyword_scores = await self._calculate_keyword_similarity(
                query, [doc['search_content'] for doc in documents]
            )
            
            # Combine scores
            combined_results = []
            for i, doc in enumerate(documents):
                vector_sim = doc['vector_similarity']
                keyword_sim = keyword_scores[i] if i < len(keyword_scores) else 0.0
                
                # Normalize weights
                total_weight = vector_weight + keyword_weight
                if total_weight > 0:
                    vector_weight_norm = vector_weight / total_weight
                    keyword_weight_norm = keyword_weight / total_weight
                else:
                    vector_weight_norm = keyword_weight_norm = 0.5
                
                combined_score = (vector_sim * vector_weight_norm + 
                                keyword_sim * keyword_weight_norm)
                
                if combined_score >= similarity_threshold:
                    result = VectorSearchResult(
                        id=doc['id'],
                        title=doc['title'],
                        content=doc['content'],
                        metadata=doc['metadata'],
                        similarity_score=combined_score
                    )
                    combined_results.append(result)
            
            # Sort by combined score and limit results
            combined_results.sort(key=lambda x: x.similarity_score, reverse=True)
            final_results = combined_results[:top_k]
            
            # Cache the results
            if use_cache and final_results:
                cache_response = {
                    'results': final_results,
                    'search_type': 'hybrid',
                    'vector_weight': vector_weight,
                    'keyword_weight': keyword_weight
                }
                await self.semantic_cache.cache_response(query, query_embedding, cache_response)
            
            logger.info(f"Hybrid search returned {len(final_results)} results for query: {query[:50]}...")
            return final_results
            
        except Exception as e:
            logger.error(f"Error performing hybrid search: {e}")
            raise
    
    async def _calculate_keyword_similarity(self, query: str, documents: List[str]) -> List[float]:
        """Calculate keyword similarity using TF-IDF."""
        try:
            if not documents:
                return []
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=5000,
                min_df=1,
                max_df=0.95
            )
            
            # Fit on documents + query
            all_texts = documents + [query]
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate similarity between query and each document
            query_vector = tfidf_matrix[-1]  # Last item is the query
            doc_vectors = tfidf_matrix[:-1]  # All except the last
            
            similarities = cosine_similarity(query_vector, doc_vectors).flatten()
            
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"Error calculating keyword similarity: {e}")
            return [0.0] * len(documents)
    
    async def cluster_documents_by_topic(
        self,
        document_type: Optional[str] = None,
        source: Optional[str] = None,
        min_documents: int = 5
    ) -> Dict[str, Any]:
        """
        Cluster documents by topic and return cluster information.
        """
        try:
            # Get documents for clustering
            documents = await self.list_documents(
                limit=1000,  # Reasonable limit for clustering
                document_type=document_type,
                source=source
            )
            
            if len(documents) < min_documents:
                return {
                    "error": f"Not enough documents for clustering (minimum: {min_documents})",
                    "document_count": len(documents)
                }
            
            # Convert to format expected by clusterer
            doc_data = []
            for doc in documents:
                content = doc.content
                # Use summary for long documents
                if (doc.metadata and 
                    doc.metadata.get('summarized') and 
                    len(content) > 1000):
                    content = doc.metadata.get('summary', content)
                
                doc_data.append({
                    'id': doc.id,
                    'content': content,
                    'title': doc.title,
                    'metadata': doc.metadata
                })
            
            # Perform clustering
            cluster_result = await self.clusterer.cluster_documents(doc_data)
            
            # Add document details to cluster result
            if 'clusters' in cluster_result:
                detailed_clusters = {}
                for cluster_id, doc_ids in cluster_result['clusters'].items():
                    cluster_docs = [doc for doc in documents if doc.id in doc_ids]
                    detailed_clusters[cluster_id] = {
                        'document_ids': doc_ids,
                        'document_count': len(doc_ids),
                        'documents': [
                            {
                                'id': doc.id,
                                'title': doc.title,
                                'content_preview': doc.content[:200] + "..." if len(doc.content) > 200 else doc.content
                            }
                            for doc in cluster_docs
                        ]
                    }
                cluster_result['detailed_clusters'] = detailed_clusters
            
            return cluster_result
            
        except Exception as e:
            logger.error(f"Error clustering documents: {e}")
            return {"error": str(e)}
    
    async def get_document_recommendations(
        self,
        document_id: int,
        recommendation_type: str = "similar",
        top_k: int = 5
    ) -> List[VectorSearchResult]:
        """
        Get document recommendations based on clustering or similarity.
        
        Args:
            document_id: ID of the reference document
            recommendation_type: "similar" (vector similarity) or "cluster" (same cluster)
            top_k: Number of recommendations to return
        """
        try:
            # Get the reference document
            reference_doc = await self.get_document(document_id)
            if not reference_doc:
                raise ValueError(f"Document {document_id} not found")
            
            if recommendation_type == "cluster":
                # Get documents from the same cluster
                similar_doc_ids = self.clusterer.get_similar_documents_by_cluster(document_id)
                if not similar_doc_ids:
                    # Fallback to vector similarity
                    recommendation_type = "similar"
                else:
                    # Get document details
                    recommendations = []
                    for doc_id in similar_doc_ids[:top_k]:
                        doc = await self.get_document(doc_id)
                        if doc:
                            # Calculate similarity with reference document
                            similarity = await self._calculate_document_similarity(
                                reference_doc.content, doc.content
                            )
                            result = VectorSearchResult(
                                id=doc.id,
                                title=doc.title,
                                content=doc.content,
                                metadata=doc.metadata,
                                similarity_score=similarity
                            )
                            recommendations.append(result)
                    
                    # Sort by similarity
                    recommendations.sort(key=lambda x: x.similarity_score, reverse=True)
                    return recommendations
            
            if recommendation_type == "similar":
                # Use vector similarity search
                content_for_search = reference_doc.content
                # Use summary if available for long documents
                if (reference_doc.metadata and 
                    reference_doc.metadata.get('summarized') and 
                    len(content_for_search) > 1000):
                    content_for_search = reference_doc.metadata.get('summary', content_for_search)
                
                results = await self.search(
                    query=content_for_search,
                    top_k=top_k + 1,  # +1 to exclude the reference document
                    similarity_threshold=0.3
                )
                
                # Remove the reference document from results
                recommendations = [r for r in results if r.id != document_id]
                return recommendations[:top_k]
            
            return []
            
        except Exception as e:
            logger.error(f"Error getting document recommendations: {e}")
            raise
    
    async def _calculate_document_similarity(self, content1: str, content2: str) -> float:
        """Calculate similarity between two documents using embeddings."""
        try:
            embedding1 = await self._generate_embedding(content1)
            embedding2 = await self._generate_embedding(content2)
            
            vec1 = np.array(embedding1).reshape(1, -1)
            vec2 = np.array(embedding2).reshape(1, -1)
            
            similarity = cosine_similarity(vec1, vec2)[0][0]
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculating document similarity: {e}")
            return 0.0
    
    async def get_semantic_cache_stats(self) -> Dict[str, Any]:
        """Get semantic cache statistics."""
        return self.semantic_cache.get_cache_stats()
    
    async def clear_semantic_cache(self):
        """Clear the semantic cache."""
        self.semantic_cache.cache.clear()
        logger.info("Semantic cache cleared")
    
    async def health_check_enhanced(self) -> Dict[str, Any]:
        """Enhanced health check including new features."""
        try:
            # Get base health check
            health_status = await super().health_check()
            
            # Add enhanced features status
            health_status.update({
                "enhanced_features": {
                    "summarizer": "available",
                    "clusterer": "available",
                    "semantic_cache": "available",
                    "hybrid_search": "available"
                },
                "cache_stats": await self.get_semantic_cache_stats()
            })
            
            return health_status
            
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "enhanced_features": "error"
            }


# Global enhanced service instance
enhanced_vector_service = EnhancedVectorDBService()


async def get_enhanced_vector_service() -> EnhancedVectorDBService:
    """Get the enhanced vector database service instance."""
    return enhanced_vector_service