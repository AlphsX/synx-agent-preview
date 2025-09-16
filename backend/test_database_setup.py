#!/usr/bin/env python3
"""
Test script to verify database setup and vector capabilities.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent))

from app.database.connection import db_manager, check_database_health
from app.database.migrations import get_migration_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_database_setup():
    """Test database setup and vector capabilities."""
    try:
        logger.info("Testing database setup...")
        
        # Initialize database connection
        await db_manager.initialize()
        
        # Check health
        health = await check_database_health()
        logger.info(f"Database health: {health}")
        
        if health["status"] != "healthy":
            logger.error("Database health check failed")
            return False
        
        # Check migration status
        migration_status = await get_migration_status()
        logger.info(f"Migration status: {migration_status}")
        
        # Test vector operations
        await test_vector_operations()
        
        logger.info("Database setup test completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Database setup test failed: {e}")
        return False
    finally:
        await db_manager.close()


async def test_vector_operations():
    """Test vector database operations."""
    logger.info("Testing vector operations...")
    
    async with db_manager.get_connection() as conn:
        # Test vector extension
        result = await conn.fetchval("SELECT vector_dims(ARRAY[1,2,3]::vector)")
        assert result == 3, "Vector extension not working"
        logger.info("✓ Vector extension is working")
        
        # Test vector similarity
        result = await conn.fetchval("""
            SELECT ARRAY[1,2,3]::vector <=> ARRAY[1,2,4]::vector
        """)
        assert result is not None, "Vector similarity not working"
        logger.info(f"✓ Vector similarity calculation: {result}")
        
        # Test document table with vector column
        await conn.execute("""
            INSERT INTO documents (title, content, embedding, metadata)
            VALUES ($1, $2, $3, $4)
            ON CONFLICT DO NOTHING
        """, 
        "Test Document", 
        "This is a test document for vector search",
        [0.1] * 1024,  # 1024-dimensional test vector
        {"test": True}
        )
        
        # Test vector search
        results = await conn.fetch("""
            SELECT id, title, content, 1 - (embedding <=> $1::vector) as similarity
            FROM documents
            WHERE 1 - (embedding <=> $1::vector) > 0.5
            ORDER BY embedding <=> $1::vector
            LIMIT 5
        """, [0.1] * 1024)
        
        logger.info(f"✓ Vector search returned {len(results)} results")
        
        if results:
            for row in results:
                logger.info(f"  - {row['title']}: similarity={row['similarity']:.3f}")


if __name__ == "__main__":
    success = asyncio.run(test_database_setup())
    sys.exit(0 if success else 1)