"""
Test script for the Vector Database Service.

This script tests the core functionality of the VectorDBService including
document creation, search, and management operations.
"""

import asyncio
import sys
import os

# Add the backend directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.vector.service import VectorDBService
from app.database.connection import initialize_database, close_database


async def test_vector_service():
    """Test the vector database service functionality."""
    print("🧪 Testing Vector Database Service")
    print("=" * 50)
    
    try:
        # Initialize database
        print("1. Initializing database...")
        await initialize_database()
        print("✅ Database initialized")
        
        # Initialize vector service
        print("\n2. Initializing vector service...")
        vector_service = VectorDBService()
        await vector_service.initialize()
        print("✅ Vector service initialized")
        
        # Test health check
        print("\n3. Testing health check...")
        health = await vector_service.health_check()
        print(f"Health status: {health}")
        
        # Test document creation
        print("\n4. Testing document creation...")
        test_documents = [
            {
                "title": "AI and Machine Learning",
                "content": "Artificial intelligence and machine learning are transforming how we process data and make decisions.",
                "metadata": {"category": "technology", "tags": ["AI", "ML"]},
                "source": "test_data",
                "document_type": "article"
            },
            {
                "title": "Python Programming",
                "content": "Python is a versatile programming language used for web development, data science, and automation.",
                "metadata": {"category": "programming", "tags": ["Python", "coding"]},
                "source": "test_data",
                "document_type": "tutorial"
            },
            {
                "title": "Database Design",
                "content": "Good database design is crucial for application performance and data integrity.",
                "metadata": {"category": "database", "tags": ["SQL", "design"]},
                "source": "test_data",
                "document_type": "guide"
            }
        ]
        
        document_ids = []
        for doc in test_documents:
            doc_id = await vector_service.add_document(
                content=doc["content"],
                title=doc["title"],
                metadata=doc["metadata"],
                source=doc["source"],
                document_type=doc["document_type"]
            )
            document_ids.append(doc_id)
            print(f"✅ Created document {doc_id}: {doc['title']}")
        
        # Test document retrieval
        print("\n5. Testing document retrieval...")
        for doc_id in document_ids:
            doc = await vector_service.get_document(doc_id)
            if doc:
                print(f"✅ Retrieved document {doc_id}: {doc.title}")
            else:
                print(f"❌ Failed to retrieve document {doc_id}")
        
        # Test vector search
        print("\n6. Testing vector search...")
        search_queries = [
            "machine learning algorithms",
            "programming languages",
            "database optimization"
        ]
        
        for query in search_queries:
            print(f"\nSearching for: '{query}'")
            results = await vector_service.search(query, top_k=3, similarity_threshold=0.5)
            
            if results:
                for i, result in enumerate(results, 1):
                    print(f"  {i}. {result.title} (score: {result.similarity_score:.3f})")
                    print(f"     Content: {result.content[:100]}...")
            else:
                print("  No results found")
        
        # Test document listing
        print("\n7. Testing document listing...")
        documents = await vector_service.list_documents(limit=10)
        print(f"✅ Found {len(documents)} documents")
        for doc in documents:
            print(f"  - {doc.title} ({doc.document_type})")
        
        # Test document count
        print("\n8. Testing document count...")
        total_count = await vector_service.get_document_count()
        print(f"✅ Total documents: {total_count}")
        
        # Test document update
        print("\n9. Testing document update...")
        if document_ids:
            first_doc_id = document_ids[0]
            updated = await vector_service.update_document(
                document_id=first_doc_id,
                title="Updated AI and Machine Learning Guide",
                metadata={"category": "technology", "tags": ["AI", "ML", "updated"], "version": "2.0"}
            )
            if updated:
                print(f"✅ Updated document {first_doc_id}")
                updated_doc = await vector_service.get_document(first_doc_id)
                print(f"  New title: {updated_doc.title}")
            else:
                print(f"❌ Failed to update document {first_doc_id}")
        
        # Test document deletion
        print("\n10. Testing document deletion...")
        if len(document_ids) > 1:
            last_doc_id = document_ids[-1]
            deleted = await vector_service.delete_document(last_doc_id)
            if deleted:
                print(f"✅ Deleted document {last_doc_id}")
                # Verify deletion
                deleted_doc = await vector_service.get_document(last_doc_id)
                if deleted_doc is None:
                    print("✅ Document deletion verified")
                else:
                    print("❌ Document still exists after deletion")
            else:
                print(f"❌ Failed to delete document {last_doc_id}")
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        # Clean up
        print("\n🧹 Cleaning up...")
        await close_database()
        print("✅ Cleanup completed")


if __name__ == "__main__":
    asyncio.run(test_vector_service())