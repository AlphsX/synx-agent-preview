# AI Agent Backend Database Management

.PHONY: help db-up db-down db-restart db-logs db-init db-migrate db-status db-health db-shell

help: ## Show this help message
	@echo "AI Agent Backend Database Management"
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

db-up: ## Start PostgreSQL and Redis containers
	docker-compose up -d postgres redis
	@echo "Waiting for database to be ready..."
	@sleep 5
	@docker-compose exec postgres pg_isready -U postgres -d ai_agent_db || (echo "Database not ready, waiting..." && sleep 10)

db-down: ## Stop database containers
	docker-compose down

db-restart: ## Restart database containers
	docker-compose restart postgres redis

db-logs: ## Show database container logs
	docker-compose logs -f postgres

db-init: ## Initialize database with schema and migrations
	python database/startup.py

db-migrate: ## Run database migrations
	python -c "import asyncio; from app.database.migrations import run_migrations; asyncio.run(run_migrations())"

db-status: ## Check migration status
	python -c "import asyncio; from app.database.migrations import get_migration_status; import json; print(json.dumps(asyncio.run(get_migration_status()), indent=2))"

db-health: ## Check database health
	python -c "import asyncio; from app.database.connection import check_database_health; import json; print(json.dumps(asyncio.run(check_database_health()), indent=2))"

db-shell: ## Connect to PostgreSQL shell
	docker-compose exec postgres psql -U postgres -d ai_agent_db

db-setup: db-up db-init ## Complete database setup (start containers and initialize)
	@echo "Database setup completed successfully!"

db-reset: ## Reset database (WARNING: This will delete all data)
	@echo "WARNING: This will delete all data. Press Ctrl+C to cancel, or wait 5 seconds to continue..."
	@sleep 5
	docker-compose down -v
	docker-compose up -d postgres redis
	@sleep 10
	$(MAKE) db-init

# Development helpers
install-deps: ## Install Python dependencies
	pip install -r requirements.txt

dev-setup: install-deps db-setup ## Complete development setup
	@echo "Development environment setup completed!"