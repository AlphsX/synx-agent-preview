"""
Database connection management with async support for PostgreSQL with pgvector.
"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

import asyncpg
from asyncpg import Connection, Pool
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy setup
Base = declarative_base()
engine = None
async_session_maker = None

# AsyncPG connection pool for vector operations
_connection_pool: Optional[Pool] = None


class DatabaseManager:
    """Manages database connections and provides both SQLAlchemy and AsyncPG interfaces."""
    
    def __init__(self):
        self.engine = None
        self.async_session_maker = None
        self.connection_pool: Optional[Pool] = None
        self._initialized = False
    
    async def initialize(self):
        """Initialize database connections and create tables if needed."""
        if self._initialized:
            return
        
        try:
            # Initialize SQLAlchemy engine for ORM operations
            if settings.DATABASE_URL.startswith("sqlite"):
                # SQLite configuration
                self.engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DEBUG,
                )
            else:
                # PostgreSQL configuration
                self.engine = create_async_engine(
                    settings.DATABASE_URL,
                    echo=settings.DEBUG,
                    pool_size=10,
                    max_overflow=20,
                    pool_pre_ping=True,
                    pool_recycle=3600,
                )
            
            self.async_session_maker = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Initialize AsyncPG pool for vector operations (PostgreSQL only)
            if not settings.DATABASE_URL.startswith("sqlite"):
                self.connection_pool = await asyncpg.create_pool(
                    settings.DATABASE_URL.replace('+asyncpg', ''),
                    min_size=5,
                    max_size=20,
                    command_timeout=60,
                    server_settings={
                        'jit': 'off'  # Disable JIT for better vector performance
                    }
                )
            else:
                # SQLite doesn't support connection pooling like PostgreSQL
                self.connection_pool = None
            
            # Test connections
            await self._test_connections()
            
            self._initialized = True
            logger.info("Database connections initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database connections: {e}")
            raise
    
    async def _test_connections(self):
        """Test both SQLAlchemy and AsyncPG connections."""
        # Test SQLAlchemy connection
        from sqlalchemy import text
        async with self.engine.begin() as conn:
            result = await conn.execute(text("SELECT 1"))
            assert result.scalar() == 1
        
        # Test AsyncPG connection and vector extension (PostgreSQL only)
        if self.connection_pool:
            async with self.connection_pool.acquire() as conn:
                result = await conn.fetchval("SELECT 1")
                assert result == 1
                
                # Test vector extension
                await conn.fetchval("SELECT vector_dims(ARRAY[1,2,3]::vector)")
                logger.info("Vector extension is working correctly")
        else:
            logger.info("Using SQLite - vector operations will be limited")
    
    async def close(self):
        """Close all database connections."""
        if self.connection_pool:
            await self.connection_pool.close()
        
        if self.engine:
            await self.engine.dispose()
        
        self._initialized = False
        logger.info("Database connections closed")
    
    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get an async SQLAlchemy session."""
        if not self._initialized:
            await self.initialize()
        
        async with self.async_session_maker() as session:
            try:
                yield session
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    @asynccontextmanager
    async def get_connection(self) -> AsyncGenerator[Connection, None]:
        """Get an async PostgreSQL connection for vector operations."""
        if not self._initialized:
            await self.initialize()
        
        if self.connection_pool:
            async with self.connection_pool.acquire() as connection:
                yield connection
        else:
            raise NotImplementedError("Raw connections not available for SQLite")
    
    async def execute_raw_query(self, query: str, *args):
        """Execute a raw SQL query using AsyncPG."""
        async with self.get_connection() as conn:
            return await conn.fetch(query, *args)
    
    async def execute_vector_search(
        self, 
        embedding: list, 
        table: str = "documents", 
        limit: int = 10,
        similarity_threshold: float = 0.7
    ):
        """Execute vector similarity search."""
        query = f"""
        SELECT id, title, content, metadata, 
               1 - (embedding <=> $1::vector) as similarity_score
        FROM {table}
        WHERE 1 - (embedding <=> $1::vector) > $2
        ORDER BY embedding <=> $1::vector
        LIMIT $3
        """
        
        async with self.get_connection() as conn:
            return await conn.fetch(query, embedding, similarity_threshold, limit)


# Global database manager instance
db_manager = DatabaseManager()


# Convenience functions for backward compatibility
async def get_database_session() -> AsyncGenerator[AsyncSession, None]:
    """Get a database session."""
    async with db_manager.get_session() as session:
        yield session


async def get_database_connection() -> AsyncGenerator[Connection, None]:
    """Get a raw database connection."""
    async with db_manager.get_connection() as connection:
        yield connection


async def initialize_database():
    """Initialize the database connections."""
    await db_manager.initialize()


async def close_database():
    """Close database connections."""
    await db_manager.close()


# Health check function
async def check_database_health() -> dict:
    """Check database health status."""
    try:
        if not db_manager._initialized:
            return {"status": "unhealthy", "error": "Database not initialized"}
        
        # Test SQLAlchemy connection
        from sqlalchemy import text
        async with db_manager.get_session() as session:
            result = await session.execute(text("SELECT 1"))
            sqlalchemy_ok = result.scalar() == 1
        
        # Test AsyncPG connection
        async with db_manager.get_connection() as conn:
            result = await conn.fetchval("SELECT 1")
            asyncpg_ok = result == 1
            
            # Test vector extension
            vector_result = await conn.fetchval("SELECT vector_dims(ARRAY[1,2,3]::vector)")
            vector_ok = vector_result == 3
        
        if sqlalchemy_ok and asyncpg_ok and vector_ok:
            return {
                "status": "healthy",
                "sqlalchemy": "ok",
                "asyncpg": "ok", 
                "vector_extension": "ok"
            }
        else:
            return {
                "status": "unhealthy",
                "sqlalchemy": "ok" if sqlalchemy_ok else "error",
                "asyncpg": "ok" if asyncpg_ok else "error",
                "vector_extension": "ok" if vector_ok else "error"
            }
    
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}