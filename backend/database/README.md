# Database Setup and Management

This directory contains the database configuration, initialization scripts, and migration system for the AI Agent backend.

## Quick Start

1. **Start the database containers:**
   ```bash
   make db-up
   ```

2. **Initialize the database:**
   ```bash
   make db-init
   ```

3. **Complete setup (combines both steps):**
   ```bash
   make db-setup
   ```

## Database Architecture

The system uses PostgreSQL with the pgvector extension for vector similarity search capabilities:

- **PostgreSQL 17** with pgvector 0.8.0 extension
- **Redis** for caching and session management
- **Async connections** using asyncpg and SQLAlchemy
- **Migration system** for schema versioning

## Database Schema

### Core Tables

1. **users** - User authentication and profiles
2. **conversations** - Chat conversation sessions
3. **messages** - Individual chat messages with context
4. **documents** - Vector document storage with embeddings

### Vector Capabilities

- **1024-dimensional embeddings** using Snowflake Arctic model
- **Cosine similarity search** with IVFFlat indexing
- **Configurable similarity thresholds** for search results

## Available Commands

Use the Makefile for easy database management:

```bash
# Database lifecycle
make db-up          # Start containers
make db-down        # Stop containers
make db-restart     # Restart containers
make db-logs        # View logs

# Database operations
make db-init        # Initialize schema and run migrations
make db-migrate     # Run pending migrations
make db-status      # Check migration status
make db-health      # Check database health

# Development
make db-shell       # Connect to PostgreSQL shell
make db-reset       # Reset database (WARNING: deletes all data)
make dev-setup      # Complete development environment setup
```

## Configuration

### Environment Variables

Key database configuration in `.env`:

```bash
# PostgreSQL connection
DATABASE_URL=postgresql+asyncpg://postgres:password@localhost:5432/ai_agent_db

# Redis connection
REDIS_URL=redis://localhost:6379/0

# Vector configuration
VECTOR_DIMENSION=1024
MAX_VECTOR_RESULTS=10
```

### Docker Configuration

The `docker-compose.yml` includes:

- **PostgreSQL** with pgvector extension
- **Redis** for caching
- **Health checks** for both services
- **Persistent volumes** for data storage
- **Network configuration** for service communication

## Migration System

### Creating Migrations

1. Create a new migration class in `migrations.py`:

```python
class MyNewMigration(Migration):
    def __init__(self):
        super().__init__("003", "Description of changes")
    
    async def up(self, connection):
        await connection.execute("ALTER TABLE ...")
    
    async def down(self, connection):
        await connection.execute("DROP ...")
```

2. Register the migration:

```python
migration_manager.add_migration(MyNewMigration())
```

### Running Migrations

```bash
# Run all pending migrations
make db-migrate

# Check migration status
make db-status

# Manual migration management
python -c "from app.database.migrations import *; asyncio.run(run_migrations())"
```

## Connection Management

The system provides two connection interfaces:

### SQLAlchemy (ORM Operations)

```python
from app.database.connection import get_database_session

async with get_database_session() as session:
    result = await session.execute(select(User))
```

### AsyncPG (Vector Operations)

```python
from app.database.connection import get_database_connection

async with get_database_connection() as conn:
    results = await conn.fetch("SELECT * FROM documents WHERE ...")
```

## Vector Search

### Adding Documents

```python
from app.database.connection import db_manager

# Generate embedding (handled by vector service)
embedding = await generate_embedding(content)

# Store document with vector
async with db_manager.get_connection() as conn:
    await conn.execute(
        "INSERT INTO documents (content, embedding) VALUES ($1, $2)",
        content, embedding
    )
```

### Searching Documents

```python
# Vector similarity search
results = await db_manager.execute_vector_search(
    embedding=query_embedding,
    limit=10,
    similarity_threshold=0.7
)
```

## Health Monitoring

### Health Check Endpoint

The database provides health check functionality:

```python
from app.database.connection import check_database_health

health = await check_database_health()
# Returns: {"status": "healthy", "sqlalchemy": "ok", "asyncpg": "ok", "vector_extension": "ok"}
```

### Monitoring Commands

```bash
# Check database health
make db-health

# View container logs
make db-logs

# Connect to database shell
make db-shell
```

## Troubleshooting

### Common Issues

1. **Database not starting:**
   ```bash
   # Check container status
   docker-compose ps
   
   # View logs
   make db-logs
   ```

2. **Connection errors:**
   ```bash
   # Verify database is ready
   make db-health
   
   # Check environment variables
   cat .env | grep DATABASE
   ```

3. **Migration failures:**
   ```bash
   # Check migration status
   make db-status
   
   # Manual migration rollback
   python -c "from app.database.migrations import *; asyncio.run(rollback_to_version('001'))"
   ```

4. **Vector extension issues:**
   ```bash
   # Verify pgvector is installed
   make db-shell
   # In psql: SELECT * FROM pg_extension WHERE extname = 'vector';
   ```

### Performance Tuning

For production deployments:

1. **Adjust connection pool sizes** in `connection.py`
2. **Tune vector index parameters** (lists parameter in IVFFlat)
3. **Monitor query performance** with PostgreSQL logs
4. **Configure appropriate memory settings** for vector operations

## Security Considerations

- **Environment variables** for all sensitive configuration
- **Connection encryption** in production
- **User permissions** properly configured
- **Regular backups** of vector data
- **API key rotation** procedures

## Backup and Recovery

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres ai_agent_db > backup.sql

# Restore database
docker-compose exec -T postgres psql -U postgres ai_agent_db < backup.sql

# Backup with Docker volumes
docker run --rm -v backend_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_backup.tar.gz /data
```