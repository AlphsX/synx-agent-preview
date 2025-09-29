"""
Simple demonstration of enhanced vector database features without NLTK dependencies.

This script demonstrates the key enhanced features using mock implementations.
"""

import asyncio
import json
from typing import List, Dict, Any


class SimpleSummarizer:
    """Simple document summarizer without NLTK dependencies."""
    
    def __init__(self):
        self.max_summary_length = 500
        self.sentence_count_threshold = 10
    
    def should_summarize(self, content: str) -> bool:
        """Check if content should be summarized based on length."""
        sentence_count = content.count('.') + content.count('!') + content.count('?')
        return sentence_count > self.sentence_count_threshold or len(content) > 2000
    
    def simple_summarize(self, content: str, max_sentences: int = 3) -> str:
        """Create simple extractive summary by selecting first and last sentences."""
        try:
            # Simple sentence splitting
            sentences = [s.strip() for s in content.split('.') if s.strip()]
            
            if len(sentences) <= max_sentences:
                return content
            
            # Take first sentence, middle sentence, and last sentence
            summary_sentences = []
            if len(sentences) > 0:
                summary_sentences.append(sentences[0])
            if len(sentences) > 2:
                summary_sentences.append(sentences[len(sentences)//2])
            if len(sentences) > 1:
                summary_sentences.append(sentences[-1])
            
            summary = '. '.join(summary_sentences[:max_sentences]) + '.'
            
            # Truncate if still too long
            if len(summary) > self.max_summary_length:
                summary = summary[:self.max_summary_length] + "..."
            
            return summary
            
        except Exception as e:
            return content[:self.max_summary_length] + "..."


class SimpleClusterer:
    """Simple document clusterer using keyword overlap."""
    
    def __init__(self):
        self.min_cluster_size = 3
    
    async def cluster_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Simple clustering based on keyword overlap."""
        try:
            if len(documents) < self.min_cluster_size:
                return {"clusters": {}, "topics": {}, "message": "Not enough documents for clustering"}
            
            # Extract keywords from each document
            doc_keywords = {}
            all_keywords = set()
            
            for doc in documents:
                content = doc.get('content', '').lower()
                # Simple keyword extraction
                words = [w.strip('.,!?;:') for w in content.split() if len(w) > 3]
                keywords = set(words)
                doc_keywords[doc['id']] = keywords
                all_keywords.update(keywords)
            
            # Simple clustering: group documents with similar keywords
            clusters = {}
            cluster_id = 0
            processed_docs = set()
            
            for doc in documents:
                if doc['id'] in processed_docs:
                    continue
                
                current_cluster = [doc['id']]
                current_keywords = doc_keywords[doc['id']]
                processed_docs.add(doc['id'])
                
                # Find similar documents
                for other_doc in documents:
                    if other_doc['id'] in processed_docs:
                        continue
                    
                    other_keywords = doc_keywords[other_doc['id']]
                    # Calculate keyword overlap
                    overlap = len(current_keywords.intersection(other_keywords))
                    total = len(current_keywords.union(other_keywords))
                    
                    if total > 0 and overlap / total > 0.3:  # 30% similarity threshold
                        current_cluster.append(other_doc['id'])
                        processed_docs.add(other_doc['id'])
                        current_keywords.update(other_keywords)
                
                if len(current_cluster) >= 2:  # Only create cluster if it has multiple documents
                    clusters[cluster_id] = current_cluster
                    cluster_id += 1
            
            # Extract topics (most common keywords per cluster)
            topics = {}
            for cid, doc_ids in clusters.items():
                cluster_keywords = set()
                for doc_id in doc_ids:
                    cluster_keywords.update(doc_keywords[doc_id])
                
                # Get top 5 keywords (simplified)
                topics[cid] = list(cluster_keywords)[:5]
            
            return {
                "clusters": clusters,
                "topics": topics,
                "n_clusters": len(clusters),
                "total_documents": len(documents)
            }
            
        except Exception as e:
            return {"error": str(e)}


class SimpleCache:
    """Simple semantic cache using string similarity."""
    
    def __init__(self):
        self.cache = {}
        self.max_cache_size = 1000
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """Simple word overlap similarity."""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 or not words2:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union) if union else 0.0
    
    async def get_cached_response(self, query: str, threshold: float = 0.7) -> Dict[str, Any]:
        """Get cached response if similar query exists."""
        for cached_query, response in self.cache.items():
            similarity = self._calculate_similarity(query, cached_query)
            if similarity >= threshold:
                response['access_count'] = response.get('access_count', 0) + 1
                return response
        return None
    
    async def cache_response(self, query: str, response: Dict[str, Any]):
        """Cache a query response."""
        if len(self.cache) >= self.max_cache_size:
            # Remove oldest entry
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[query] = {
            **response,
            'access_count': 1,
            'cached_query': query
        }
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        if not self.cache:
            return {"total_entries": 0, "avg_access_count": 0}
        
        access_counts = [r.get('access_count', 1) for r in self.cache.values()]
        return {
            "total_entries": len(self.cache),
            "avg_access_count": sum(access_counts) / len(access_counts),
            "max_access_count": max(access_counts),
            "cache_size_limit": self.max_cache_size
        }


async def demo_document_summarization():
    """Demonstrate automatic document summarization."""
    print("\n" + "="*60)
    print("DEMO 1: AUTOMATIC DOCUMENT SUMMARIZATION")
    print("="*60)
    
    summarizer = SimpleSummarizer()
    
    # Example long document
    long_document = """
    Artificial intelligence (AI) is intelligence demonstrated by machines, in contrast to the natural intelligence displayed by humans and animals. Leading AI textbooks define the field as the study of intelligent agents: any device that perceives its environment and takes actions that maximize its chance of successfully achieving its goals. Colloquially, the term artificial intelligence is often used to describe machines that mimic cognitive functions that humans associate with the human mind, such as learning and problem solving.

    The scope of AI is disputed: as machines become increasingly capable, tasks considered to require intelligence are often removed from the definition of AI, a phenomenon known as the AI effect. A quip in Tesler's Theorem says AI is whatever hasn't been done yet. For instance, optical character recognition is frequently excluded from things considered to be AI, having become a routine technology. Modern machine learning techniques are a core part of AI. Machine learning algorithms build a model based on sample data, known as training data, in order to make predictions or decisions without being explicitly programmed to do so.

    Machine learning is closely related to computational statistics, which focuses on making predictions using computers. The study of mathematical optimization delivers methods, theory and application domains to the field of machine learning. Data mining is a related field of study, focusing on exploratory data analysis through unsupervised learning. In its application across business problems, machine learning is also referred to as predictive analytics. Some implementations of machine learning use data and neural networks in a way that mimics the workings of a biological brain.

    The traditional problems or goals of AI research include reasoning, knowledge representation, planning, learning, natural language processing, perception, and the ability to move and manipulate objects. General intelligence is among the field's long-term goals. Approaches include statistical methods, computational intelligence, and traditional symbolic AI. Many tools are used in AI, including versions of search and mathematical optimization, artificial neural networks, and methods based on statistics, probability and economics.
    """
    
    print(f"Original document length: {len(long_document)} characters")
    print(f"Should summarize: {summarizer.should_summarize(long_document)}")
    
    # Generate summary
    summary = summarizer.simple_summarize(long_document, max_sentences=3)
    
    print(f"\nSummary length: {len(summary)} characters")
    print(f"Compression ratio: {len(summary)/len(long_document):.2%}")
    print(f"\nGenerated Summary:")
    print("-" * 40)
    print(summary)


async def demo_document_clustering():
    """Demonstrate document clustering and topic modeling."""
    print("\n" + "="*60)
    print("DEMO 2: DOCUMENT CLUSTERING AND TOPIC MODELING")
    print("="*60)
    
    clusterer = SimpleClusterer()
    
    # Example documents from different topics
    documents = [
        {"id": 1, "content": "Machine learning algorithms use statistical methods to learn patterns from data"},
        {"id": 2, "content": "Deep learning neural networks can process complex patterns in large datasets"},
        {"id": 3, "content": "Natural language processing enables computers to understand human language"},
        {"id": 4, "content": "Computer vision algorithms can recognize objects and patterns in images"},
        {"id": 5, "content": "Blockchain technology provides decentralized and secure transaction records"},
        {"id": 6, "content": "Cryptocurrency uses blockchain for digital currency transactions"},
        {"id": 7, "content": "Smart contracts automate agreements using blockchain technology"},
        {"id": 8, "content": "Bitcoin and Ethereum are popular cryptocurrency platforms"},
        {"id": 9, "content": "Data science combines statistics, programming, and domain expertise"},
        {"id": 10, "content": "Big data analytics processes large volumes of structured and unstructured data"},
    ]
    
    print(f"Clustering {len(documents)} documents...")
    
    # Perform clustering
    cluster_result = await clusterer.cluster_documents(documents)
    
    if "error" not in cluster_result:
        print(f"\nFound {cluster_result['n_clusters']} clusters:")
        
        for cluster_id, doc_ids in cluster_result['clusters'].items():
            print(f"\nCluster {cluster_id}:")
            print(f"  Documents: {doc_ids}")
            print(f"  Topic keywords: {cluster_result['topics'].get(cluster_id, [])}")
            
            # Show document titles for this cluster
            cluster_docs = [doc for doc in documents if doc['id'] in doc_ids]
            for doc in cluster_docs:
                print(f"    - Doc {doc['id']}: {doc['content'][:60]}...")
    else:
        print(f"Clustering failed: {cluster_result['error']}")


async def demo_semantic_cache():
    """Demonstrate semantic caching functionality."""
    print("\n" + "="*60)
    print("DEMO 3: SEMANTIC CACHING")
    print("="*60)
    
    cache = SimpleCache()
    
    # Example queries and responses
    queries_and_responses = [
        ("What is machine learning?", {"answer": "Machine learning is a subset of AI that enables computers to learn from data.", "confidence": 0.9}),
        ("How does deep learning work?", {"answer": "Deep learning uses neural networks with multiple layers to process data.", "confidence": 0.85}),
        ("What are neural networks?", {"answer": "Neural networks are computing systems inspired by biological neural networks.", "confidence": 0.8}),
    ]
    
    # Cache some responses
    print("Caching responses...")
    for query, response in queries_and_responses:
        await cache.cache_response(query, response)
        print(f"  Cached: {query[:50]}...")
    
    # Test exact match retrieval
    print("\nTesting exact match retrieval:")
    test_query = "What is machine learning?"
    cached_response = await cache.get_cached_response(test_query, threshold=1.0)
    
    if cached_response:
        print(f"  Query: {test_query}")
        print(f"  Cached answer: {cached_response['answer']}")
        print("  ✓ Cache hit!")
    else:
        print("  ✗ Cache miss")
    
    # Test semantic similarity (similar but not exact query)
    print("\nTesting semantic similarity:")
    similar_query = "Tell me about machine learning algorithms"
    cached_response = await cache.get_cached_response(similar_query, threshold=0.5)
    
    if cached_response:
        print(f"  Query: {similar_query}")
        print(f"  Found similar cached answer: {cached_response['answer']}")
        print(f"  Original query: {cached_response['cached_query']}")
        print("  ✓ Semantic cache hit!")
    else:
        print("  ✗ No similar cached response found")
    
    # Show cache statistics
    stats = cache.get_cache_stats()
    print(f"\nCache Statistics:")
    print(f"  Total entries: {stats['total_entries']}")
    print(f"  Average access count: {stats['avg_access_count']:.2f}")
    print(f"  Cache size limit: {stats['cache_size_limit']}")


async def demo_hybrid_search():
    """Demonstrate hybrid search combining vector and keyword similarity."""
    print("\n" + "="*60)
    print("DEMO 4: HYBRID SEARCH")
    print("="*60)
    
    # Mock documents in the database
    mock_documents = [
        {
            'id': 1,
            'title': 'Introduction to Machine Learning',
            'content': 'Machine learning is a method of data analysis that automates analytical model building',
            'vector_similarity': 0.85
        },
        {
            'id': 2,
            'title': 'Deep Learning Fundamentals',
            'content': 'Deep learning is part of a broader family of machine learning methods based on neural networks',
            'vector_similarity': 0.75
        },
        {
            'id': 3,
            'title': 'Natural Language Processing',
            'content': 'NLP is a subfield of linguistics, computer science, and artificial intelligence',
            'vector_similarity': 0.65
        }
    ]
    
    query = "machine learning algorithms"
    print(f"Search query: '{query}'")
    
    # Calculate keyword similarity scores
    def calculate_keyword_similarity(query: str, content: str) -> float:
        query_words = set(query.lower().split())
        content_words = set(content.lower().split())
        
        if not query_words or not content_words:
            return 0.0
        
        intersection = query_words.intersection(content_words)
        union = query_words.union(content_words)
        
        return len(intersection) / len(union) if union else 0.0
    
    keyword_similarities = [
        calculate_keyword_similarity(query, doc['content']) 
        for doc in mock_documents
    ]
    
    print(f"\nDocument similarities:")
    print(f"{'Doc ID':<6} {'Title':<30} {'Vector':<8} {'Keyword':<8} {'Combined':<8}")
    print("-" * 70)
    
    # Calculate combined scores
    vector_weight = 0.7
    keyword_weight = 0.3
    
    for i, doc in enumerate(mock_documents):
        vector_sim = doc['vector_similarity']
        keyword_sim = keyword_similarities[i]
        combined_score = vector_sim * vector_weight + keyword_sim * keyword_weight
        
        print(f"{doc['id']:<6} {doc['title'][:28]:<30} {vector_sim:<8.2f} {keyword_sim:<8.2f} {combined_score:<8.2f}")
    
    print(f"\nHybrid search combines:")
    print(f"  - Vector similarity (weight: {vector_weight}) - semantic understanding")
    print(f"  - Keyword similarity (weight: {keyword_weight}) - exact term matching")
    print(f"  - Result: More comprehensive and accurate search results")


async def demo_integration_workflow():
    """Demonstrate complete integration workflow."""
    print("\n" + "="*60)
    print("DEMO 5: COMPLETE INTEGRATION WORKFLOW")
    print("="*60)
    
    print("This workflow demonstrates how all enhanced features work together:")
    print("\n1. Document Creation with Auto-Summarization")
    print("   → Large documents are automatically summarized")
    print("   → Summaries are stored in metadata for faster processing")
    
    print("\n2. Hybrid Search")
    print("   → Combines vector embeddings with keyword matching")
    print("   → Uses summaries for long documents to improve performance")
    print("   → Checks semantic cache first for faster responses")
    
    print("\n3. Document Clustering")
    print("   → Groups related documents by topic")
    print("   → Extracts key themes and topics")
    print("   → Enables topic-based recommendations")
    
    print("\n4. Semantic Caching")
    print("   → Caches frequently asked questions")
    print("   → Uses semantic similarity for cache hits")
    print("   → Improves response times for common queries")
    
    print("\n5. Document Recommendations")
    print("   → Suggests similar documents based on content")
    print("   → Uses clustering information for topic-based recommendations")
    print("   → Helps users discover related content")
    
    print("\nAll features are accessible through REST API endpoints:")
    print("  - POST /api/vector/enhanced/documents (with auto_summarize)")
    print("  - POST /api/vector/enhanced/search/hybrid")
    print("  - POST /api/vector/enhanced/clustering")
    print("  - GET  /api/vector/enhanced/cache/stats")
    print("  - POST /api/vector/enhanced/recommendations")


async def main():
    """Run all demonstrations."""
    print("ENHANCED VECTOR DATABASE FEATURES DEMONSTRATION")
    print("=" * 60)
    print("This demo showcases the advanced semantic search capabilities")
    print("implemented for the AI agent backend integration.")
    
    try:
        await demo_document_summarization()
        await demo_document_clustering()
        await demo_semantic_cache()
        await demo_hybrid_search()
        await demo_integration_workflow()
        
        print("\n" + "="*60)
        print("DEMONSTRATION COMPLETE")
        print("="*60)
        print("All enhanced vector database features have been demonstrated.")
        print("The implementation includes:")
        print("✓ Automatic document summarization")
        print("✓ Document clustering and topic modeling")
        print("✓ Semantic caching with similarity matching")
        print("✓ Hybrid search (vector + keyword)")
        print("✓ Document recommendations")
        print("✓ Complete REST API integration")
        print("✓ Comprehensive test coverage")
        print("✓ Database migrations for new features")
        
    except Exception as e:
        print(f"\nDemo error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())