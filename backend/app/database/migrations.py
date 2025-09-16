"""
Database migration system for schema changes.
"""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

from app.database.connection import db_manager

logger = logging.getLogger(__name__)


class Migration:
    """Base class for database migrations."""
    
    def __init__(self, version: str, description: str):
        self.version = version
        self.description = description
        self.timestamp = datetime.now()
    
    async def up(self, connection):
        """Apply the migration."""
        raise NotImplementedError("Subclasses must implement the up method")
    
    async def down(self, connection):
        """Rollback the migration."""
        raise NotImplementedError("Subclasses must implement the down method")


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self):
        self.migrations: List[Migration] = []
        self._migration_table = "schema_migrations"
    
    def add_migration(self, migration: Migration):
        """Add a migration to the manager."""
        self.migrations.append(migration)
        # Sort migrations by version
        self.migrations.sort(key=lambda m: m.version)
    
    async def _ensure_migration_table(self, connection):
        """Ensure the migration tracking table exists."""
        await connection.execute(f"""
            CREATE TABLE IF NOT EXISTS {self._migration_table} (
                version VARCHAR(255) PRIMARY KEY,
                description TEXT,
                applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
    
    async def get_applied_migrations(self, connection) -> List[str]:
        """Get list of applied migration versions."""
        await self._ensure_migration_table(connection)
        
        result = await connection.fetch(
            f"SELECT version FROM {self._migration_table} ORDER BY version"
        )
        return [row['version'] for row in result]
    
    async def apply_migration(self, migration: Migration, connection):
        """Apply a single migration."""
        try:
            logger.info(f"Applying migration {migration.version}: {migration.description}")
            
            # Start transaction
            async with connection.transaction():
                await migration.up(connection)
                
                # Record migration as applied
                await connection.execute(
                    f"""
                    INSERT INTO {self._migration_table} (version, description)
                    VALUES ($1, $2)
                    ON CONFLICT (version) DO NOTHING
                    """,
                    migration.version,
                    migration.description
                )
            
            logger.info(f"Successfully applied migration {migration.version}")
            
        except Exception as e:
            logger.error(f"Failed to apply migration {migration.version}: {e}")
            raise
    
    async def rollback_migration(self, migration: Migration, connection):
        """Rollback a single migration."""
        try:
            logger.info(f"Rolling back migration {migration.version}: {migration.description}")
            
            # Start transaction
            async with connection.transaction():
                await migration.down(connection)
                
                # Remove migration record
                await connection.execute(
                    f"DELETE FROM {self._migration_table} WHERE version = $1",
                    migration.version
                )
            
            logger.info(f"Successfully rolled back migration {migration.version}")
            
        except Exception as e:
            logger.error(f"Failed to rollback migration {migration.version}: {e}")
            raise
    
    async def migrate_up(self, target_version: Optional[str] = None):
        """Apply all pending migrations up to target version."""
        async with db_manager.get_connection() as connection:
            applied_migrations = await self.get_applied_migrations(connection)
            
            for migration in self.migrations:
                if migration.version in applied_migrations:
                    continue
                
                if target_version and migration.version > target_version:
                    break
                
                await self.apply_migration(migration, connection)
    
    async def migrate_down(self, target_version: str):
        """Rollback migrations down to target version."""
        async with db_manager.get_connection() as connection:
            applied_migrations = await self.get_applied_migrations(connection)
            
            # Find migrations to rollback (in reverse order)
            migrations_to_rollback = []
            for migration in reversed(self.migrations):
                if migration.version in applied_migrations and migration.version > target_version:
                    migrations_to_rollback.append(migration)
            
            for migration in migrations_to_rollback:
                await self.rollback_migration(migration, connection)
    
    async def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status."""
        async with db_manager.get_connection() as connection:
            applied_migrations = await self.get_applied_migrations(connection)
            
            pending_migrations = [
                m for m in self.migrations 
                if m.version not in applied_migrations
            ]
            
            return {
                "total_migrations": len(self.migrations),
                "applied_migrations": len(applied_migrations),
                "pending_migrations": len(pending_migrations),
                "applied_versions": applied_migrations,
                "pending_versions": [m.version for m in pending_migrations],
                "latest_applied": applied_migrations[-1] if applied_migrations else None,
                "next_pending": pending_migrations[0].version if pending_migrations else None
            }


# Example migrations
class InitialMigration(Migration):
    """Initial database schema migration."""
    
    def __init__(self):
        super().__init__("001", "Initial database schema with vector extension")
    
    async def up(self, connection):
        """Create initial schema."""
        # This is handled by init.sql, but we track it as a migration
        await connection.execute("SELECT 1")  # No-op since init.sql handles this
    
    async def down(self, connection):
        """Drop all tables."""
        await connection.execute("""
            DROP TABLE IF EXISTS messages CASCADE;
            DROP TABLE IF EXISTS conversations CASCADE;
            DROP TABLE IF EXISTS documents CASCADE;
            DROP TABLE IF EXISTS users CASCADE;
        """)


class AddDocumentIndexesMigration(Migration):
    """Add additional indexes for document search performance."""
    
    def __init__(self):
        super().__init__("002", "Add additional indexes for document search")
    
    async def up(self, connection):
        """Add indexes."""
        await connection.execute("""
            CREATE INDEX IF NOT EXISTS idx_documents_content_gin 
            ON documents USING gin(to_tsvector('english', content));
            
            CREATE INDEX IF NOT EXISTS idx_documents_title_gin 
            ON documents USING gin(to_tsvector('english', title));
        """)
    
    async def down(self, connection):
        """Remove indexes."""
        await connection.execute("""
            DROP INDEX IF EXISTS idx_documents_content_gin;
            DROP INDEX IF EXISTS idx_documents_title_gin;
        """)


class ConversationPersistenceMigration(Migration):
    """Ensure conversation persistence tables and indexes are optimized."""
    
    def __init__(self):
        super().__init__("003", "Optimize conversation persistence tables and indexes")
    
    async def up(self, connection):
        """Add conversation-specific optimizations."""
        await connection.execute("""
            -- Add additional indexes for conversation queries
            CREATE INDEX IF NOT EXISTS idx_messages_role ON messages(role);
            CREATE INDEX IF NOT EXISTS idx_messages_model_id ON messages(model_id) WHERE model_id IS NOT NULL;
            CREATE INDEX IF NOT EXISTS idx_conversations_title_gin ON conversations USING gin(to_tsvector('english', title));
            
            -- Add index for conversation search by content
            CREATE INDEX IF NOT EXISTS idx_messages_content_gin ON messages USING gin(to_tsvector('english', content));
            
            -- Add composite index for conversation message retrieval
            CREATE INDEX IF NOT EXISTS idx_messages_conversation_created ON messages(conversation_id, created_at DESC);
            
            -- Add index for user conversation retrieval
            CREATE INDEX IF NOT EXISTS idx_conversations_user_updated ON conversations(user_id, updated_at DESC) WHERE user_id IS NOT NULL;
        """)
    
    async def down(self, connection):
        """Remove conversation-specific optimizations."""
        await connection.execute("""
            DROP INDEX IF EXISTS idx_messages_role;
            DROP INDEX IF EXISTS idx_messages_model_id;
            DROP INDEX IF EXISTS idx_conversations_title_gin;
            DROP INDEX IF EXISTS idx_messages_content_gin;
            DROP INDEX IF EXISTS idx_messages_conversation_created;
            DROP INDEX IF EXISTS idx_conversations_user_updated;
        """)


# Global migration manager
migration_manager = MigrationManager()

# Register migrations
migration_manager.add_migration(InitialMigration())
migration_manager.add_migration(AddDocumentIndexesMigration())
migration_manager.add_migration(ConversationPersistenceMigration())


# Convenience functions
async def run_migrations():
    """Run all pending migrations."""
    await migration_manager.migrate_up()


async def get_migration_status():
    """Get migration status."""
    return await migration_manager.get_migration_status()


async def rollback_to_version(version: str):
    """Rollback to specific version."""
    await migration_manager.migrate_down(version)