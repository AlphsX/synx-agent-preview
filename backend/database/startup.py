#!/usr/bin/env python3
"""
Database startup and management script.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add the backend directory to Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.database.connection import db_manager, check_database_health
from app.database.migrations import run_migrations, get_migration_status

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def wait_for_database(max_retries: int = 30, delay: int = 2):
    """Wait for database to be available."""
    for attempt in range(max_retries):
        try:
            await db_manager.initialize()
            health = await check_database_health()
            if health["status"] == "healthy":
                logger.info("Database is healthy and ready")
                return True
        except Exception as e:
            logger.warning(f"Database not ready (attempt {attempt + 1}/{max_retries}): {e}")
        
        if attempt < max_retries - 1:
            await asyncio.sleep(delay)
    
    logger.error("Database failed to become available")
    return False


async def initialize_database():
    """Initialize database with migrations."""
    try:
        logger.info("Initializing database...")
        
        # Wait for database to be available
        if not await wait_for_database():
            sys.exit(1)
        
        # Run migrations
        logger.info("Running database migrations...")
        await run_migrations()
        
        # Check migration status
        status = await get_migration_status()
        logger.info(f"Migration status: {status}")
        
        # Final health check
        health = await check_database_health()
        logger.info(f"Database health: {health}")
        
        if health["status"] == "healthy":
            logger.info("Database initialization completed successfully")
        else:
            logger.error("Database initialization failed health check")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        sys.exit(1)
    finally:
        await db_manager.close()


if __name__ == "__main__":
    asyncio.run(initialize_database())