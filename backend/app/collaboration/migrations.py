"""
Database migrations for collaboration features.
"""

import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database.connection import db_manager

logger = logging.getLogger(__name__)

async def create_collaboration_tables():
    """Create all collaboration-related database tables."""
    
    collaboration_tables_sql = """
    -- Create enum types
    DO $$ BEGIN
        CREATE TYPE collaboration_role AS ENUM ('owner', 'editor', 'viewer', 'commenter');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    DO $$ BEGIN
        CREATE TYPE presence_status AS ENUM ('online', 'away', 'busy', 'offline');
    EXCEPTION
        WHEN duplicate_object THEN null;
    END $$;
    
    -- Shared conversations table
    CREATE TABLE IF NOT EXISTS shared_conversations (
        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
        conversation_id VARCHAR NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
        owner_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        share_token VARCHAR UNIQUE NOT NULL,
        is_public BOOLEAN DEFAULT FALSE,
        allow_anonymous BOOLEAN DEFAULT FALSE,
        max_participants INTEGER DEFAULT 10,
        default_role collaboration_role DEFAULT 'viewer',
        allow_branching BOOLEAN DEFAULT TRUE,
        allow_editing BOOLEAN DEFAULT FALSE,
        description TEXT,
        tags JSONB DEFAULT '[]'::jsonb,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        expires_at TIMESTAMP WITH TIME ZONE
    );
    
    -- Conversation participants table
    CREATE TABLE IF NOT EXISTS conversation_participants (
        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
        shared_conversation_id VARCHAR NOT NULL REFERENCES shared_conversations(id) ON DELETE CASCADE,
        user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
        display_name VARCHAR NOT NULL,
        avatar_color VARCHAR DEFAULT '#3B82F6',
        role collaboration_role DEFAULT 'viewer',
        session_id VARCHAR NOT NULL,
        is_anonymous BOOLEAN DEFAULT FALSE,
        presence_status presence_status DEFAULT 'online',
        last_seen TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        is_typing BOOLEAN DEFAULT FALSE,
        typing_updated_at TIMESTAMP WITH TIME ZONE,
        can_edit BOOLEAN DEFAULT FALSE,
        can_branch BOOLEAN DEFAULT TRUE,
        can_invite BOOLEAN DEFAULT FALSE,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Conversation branches table
    CREATE TABLE IF NOT EXISTS conversation_branches (
        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
        shared_conversation_id VARCHAR NOT NULL REFERENCES shared_conversations(id) ON DELETE CASCADE,
        parent_message_id VARCHAR NOT NULL,
        creator_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
        title VARCHAR NOT NULL,
        description TEXT,
        branch_type VARCHAR DEFAULT 'alternative',
        is_active BOOLEAN DEFAULT TRUE,
        is_merged BOOLEAN DEFAULT FALSE,
        merged_at TIMESTAMP WITH TIME ZONE,
        merged_by VARCHAR REFERENCES users(id) ON DELETE SET NULL,
        tags JSONB DEFAULT '[]'::jsonb,
        vote_score INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Branch messages table
    CREATE TABLE IF NOT EXISTS branch_messages (
        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
        branch_id VARCHAR NOT NULL REFERENCES conversation_branches(id) ON DELETE CASCADE,
        author_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
        content TEXT NOT NULL,
        role VARCHAR NOT NULL,
        model_id VARCHAR,
        external_data_used JSONB DEFAULT '{}'::jsonb,
        processing_time INTEGER,
        tokens_used INTEGER,
        is_suggestion BOOLEAN DEFAULT FALSE,
        parent_message_id VARCHAR,
        vote_score INTEGER DEFAULT 0,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Typing indicators table
    CREATE TABLE IF NOT EXISTS typing_indicators (
        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
        conversation_id VARCHAR NOT NULL,
        user_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
        session_id VARCHAR NOT NULL,
        display_name VARCHAR NOT NULL,
        is_typing BOOLEAN DEFAULT TRUE,
        typing_text VARCHAR,
        started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL
    );
    
    -- Collaboration events table
    CREATE TABLE IF NOT EXISTS collaboration_events (
        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
        shared_conversation_id VARCHAR NOT NULL REFERENCES shared_conversations(id) ON DELETE CASCADE,
        user_id VARCHAR REFERENCES users(id) ON DELETE SET NULL,
        event_type VARCHAR NOT NULL,
        event_data JSONB DEFAULT '{}'::jsonb,
        description TEXT,
        ip_address VARCHAR,
        user_agent VARCHAR,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Conversation invites table
    CREATE TABLE IF NOT EXISTS conversation_invites (
        id VARCHAR PRIMARY KEY DEFAULT gen_random_uuid()::text,
        shared_conversation_id VARCHAR NOT NULL REFERENCES shared_conversations(id) ON DELETE CASCADE,
        inviter_id VARCHAR NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        invitee_email VARCHAR,
        invitee_id VARCHAR REFERENCES users(id) ON DELETE CASCADE,
        invite_token VARCHAR UNIQUE NOT NULL,
        role collaboration_role DEFAULT 'viewer',
        message TEXT,
        is_accepted BOOLEAN DEFAULT FALSE,
        is_expired BOOLEAN DEFAULT FALSE,
        accepted_at TIMESTAMP WITH TIME ZONE,
        expires_at TIMESTAMP WITH TIME ZONE NOT NULL,
        created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
        updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
    );
    
    -- Create indexes for better performance
    CREATE INDEX IF NOT EXISTS idx_shared_conversations_conversation_id ON shared_conversations(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_shared_conversations_owner_id ON shared_conversations(owner_id);
    CREATE INDEX IF NOT EXISTS idx_shared_conversations_share_token ON shared_conversations(share_token);
    
    CREATE INDEX IF NOT EXISTS idx_conversation_participants_shared_conversation_id ON conversation_participants(shared_conversation_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_participants_user_id ON conversation_participants(user_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_participants_session_id ON conversation_participants(session_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_participants_presence_status ON conversation_participants(presence_status);
    
    CREATE INDEX IF NOT EXISTS idx_conversation_branches_shared_conversation_id ON conversation_branches(shared_conversation_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_branches_parent_message_id ON conversation_branches(parent_message_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_branches_creator_id ON conversation_branches(creator_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_branches_is_active ON conversation_branches(is_active);
    
    CREATE INDEX IF NOT EXISTS idx_branch_messages_branch_id ON branch_messages(branch_id);
    CREATE INDEX IF NOT EXISTS idx_branch_messages_author_id ON branch_messages(author_id);
    CREATE INDEX IF NOT EXISTS idx_branch_messages_created_at ON branch_messages(created_at);
    
    CREATE INDEX IF NOT EXISTS idx_typing_indicators_conversation_id ON typing_indicators(conversation_id);
    CREATE INDEX IF NOT EXISTS idx_typing_indicators_session_id ON typing_indicators(session_id);
    CREATE INDEX IF NOT EXISTS idx_typing_indicators_expires_at ON typing_indicators(expires_at);
    
    CREATE INDEX IF NOT EXISTS idx_collaboration_events_shared_conversation_id ON collaboration_events(shared_conversation_id);
    CREATE INDEX IF NOT EXISTS idx_collaboration_events_user_id ON collaboration_events(user_id);
    CREATE INDEX IF NOT EXISTS idx_collaboration_events_event_type ON collaboration_events(event_type);
    CREATE INDEX IF NOT EXISTS idx_collaboration_events_created_at ON collaboration_events(created_at);
    
    CREATE INDEX IF NOT EXISTS idx_conversation_invites_shared_conversation_id ON conversation_invites(shared_conversation_id);
    CREATE INDEX IF NOT EXISTS idx_conversation_invites_invite_token ON conversation_invites(invite_token);
    CREATE INDEX IF NOT EXISTS idx_conversation_invites_invitee_email ON conversation_invites(invitee_email);
    CREATE INDEX IF NOT EXISTS idx_conversation_invites_expires_at ON conversation_invites(expires_at);
    
    -- Create triggers for updated_at timestamps
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    DROP TRIGGER IF EXISTS update_shared_conversations_updated_at ON shared_conversations;
    CREATE TRIGGER update_shared_conversations_updated_at
        BEFORE UPDATE ON shared_conversations
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_conversation_participants_updated_at ON conversation_participants;
    CREATE TRIGGER update_conversation_participants_updated_at
        BEFORE UPDATE ON conversation_participants
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_conversation_branches_updated_at ON conversation_branches;
    CREATE TRIGGER update_conversation_branches_updated_at
        BEFORE UPDATE ON conversation_branches
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_branch_messages_updated_at ON branch_messages;
    CREATE TRIGGER update_branch_messages_updated_at
        BEFORE UPDATE ON branch_messages
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    
    DROP TRIGGER IF EXISTS update_conversation_invites_updated_at ON conversation_invites;
    CREATE TRIGGER update_conversation_invites_updated_at
        BEFORE UPDATE ON conversation_invites
        FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
    """
    
    try:
        async with db_manager.get_session() as session:
            # Execute the SQL to create all tables
            await session.execute(text(collaboration_tables_sql))
            await session.commit()
            
            logger.info("Successfully created collaboration tables and indexes")
            return True
            
    except Exception as e:
        logger.error(f"Error creating collaboration tables: {e}")
        raise

async def drop_collaboration_tables():
    """Drop all collaboration tables (for testing/cleanup)."""
    
    drop_tables_sql = """
    -- Drop tables in reverse dependency order
    DROP TABLE IF EXISTS conversation_invites CASCADE;
    DROP TABLE IF EXISTS collaboration_events CASCADE;
    DROP TABLE IF EXISTS typing_indicators CASCADE;
    DROP TABLE IF EXISTS branch_messages CASCADE;
    DROP TABLE IF EXISTS conversation_branches CASCADE;
    DROP TABLE IF EXISTS conversation_participants CASCADE;
    DROP TABLE IF EXISTS shared_conversations CASCADE;
    
    -- Drop custom types
    DROP TYPE IF EXISTS collaboration_role CASCADE;
    DROP TYPE IF EXISTS presence_status CASCADE;
    
    -- Drop function
    DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;
    """
    
    try:
        async with db_manager.get_session() as session:
            await session.execute(text(drop_tables_sql))
            await session.commit()
            
            logger.info("Successfully dropped collaboration tables")
            return True
            
    except Exception as e:
        logger.error(f"Error dropping collaboration tables: {e}")
        raise

async def run_collaboration_migrations():
    """Run all collaboration migrations."""
    try:
        logger.info("Running collaboration migrations...")
        
        # Create collaboration tables
        await create_collaboration_tables()
        
        logger.info("Collaboration migrations completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error running collaboration migrations: {e}")
        raise

# Migration verification
async def verify_collaboration_tables():
    """Verify that all collaboration tables exist."""
    
    verification_sql = """
    SELECT table_name 
    FROM information_schema.tables 
    WHERE table_schema = 'public' 
    AND table_name IN (
        'shared_conversations',
        'conversation_participants', 
        'conversation_branches',
        'branch_messages',
        'typing_indicators',
        'collaboration_events',
        'conversation_invites'
    )
    ORDER BY table_name;
    """
    
    try:
        async with db_manager.get_session() as session:
            result = await session.execute(text(verification_sql))
            tables = [row[0] for row in result.fetchall()]
            
            expected_tables = [
                'branch_messages',
                'collaboration_events',
                'conversation_branches',
                'conversation_participants',
                'shared_conversations',
                'typing_indicators',
                'conversation_invites'
            ]
            
            missing_tables = set(expected_tables) - set(tables)
            
            if missing_tables:
                logger.error(f"Missing collaboration tables: {missing_tables}")
                return False
            
            logger.info(f"All collaboration tables verified: {tables}")
            return True
            
    except Exception as e:
        logger.error(f"Error verifying collaboration tables: {e}")
        return False