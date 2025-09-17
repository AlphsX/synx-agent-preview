#!/bin/bash

# AI Agent Backend - Production Deployment Script
# This script automates the deployment process for the AI Agent system

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
COMPOSE_FILE="docker-compose.prod.yml"
ENV_FILE=".env"
BACKUP_DIR="./backups"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check environment file
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Environment file $ENV_FILE not found. Please copy .env.example to .env and configure it."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

validate_environment() {
    log_info "Validating environment configuration..."
    
    # Check required environment variables
    required_vars=(
        "GROQ_API_KEY"
        "OPENAI_API_KEY" 
        "ANTHROPIC_API_KEY"
        "SERP_API_KEY"
        "BINANCE_API_KEY"
        "SECRET_KEY"
        "POSTGRES_PASSWORD"
    )
    
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if ! grep -q "^${var}=" "$ENV_FILE" || grep -q "^${var}=$" "$ENV_FILE" || grep -q "^${var}=your_" "$ENV_FILE"; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_error "Missing or incomplete environment variables:"
        for var in "${missing_vars[@]}"; do
            echo "  - $var"
        done
        log_error "Please configure these variables in $ENV_FILE"
        exit 1
    fi
    
    log_success "Environment validation passed"
}

backup_data() {
    log_info "Creating backup of existing data..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup database if container exists
    if docker-compose -f "$COMPOSE_FILE" ps postgres | grep -q "Up"; then
        log_info "Backing up PostgreSQL database..."
        docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_dump -U postgres ai_agent_db > "$BACKUP_DIR/db_backup_$(date +%Y%m%d_%H%M%S).sql"
        log_success "Database backup created"
    fi
    
    # Backup Redis if container exists
    if docker-compose -f "$COMPOSE_FILE" ps redis | grep -q "Up"; then
        log_info "Backing up Redis data..."
        docker-compose -f "$COMPOSE_FILE" exec redis redis-cli BGSAVE
        docker cp ai-agent-redis:/data/dump.rdb "$BACKUP_DIR/redis_backup_$(date +%Y%m%d_%H%M%S).rdb" 2>/dev/null || true
        log_success "Redis backup created"
    fi
}

deploy_services() {
    log_info "Deploying services with Docker Compose..."
    
    # Pull latest images
    log_info "Pulling latest Docker images..."
    docker-compose -f "$COMPOSE_FILE" pull
    
    # Build and start services
    log_info "Building and starting services..."
    docker-compose -f "$COMPOSE_FILE" up -d --build
    
    log_success "Services deployed successfully"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for database
    log_info "Waiting for PostgreSQL..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T postgres pg_isready -U postgres -d ai_agent_db &>/dev/null; then
            log_success "PostgreSQL is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "PostgreSQL failed to start within timeout"
        exit 1
    fi
    
    # Wait for Redis
    log_info "Waiting for Redis..."
    timeout=30
    while [ $timeout -gt 0 ]; do
        if docker-compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping &>/dev/null; then
            log_success "Redis is ready"
            break
        fi
        sleep 2
        timeout=$((timeout - 2))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Redis failed to start within timeout"
        exit 1
    fi
    
    # Wait for backend API
    log_info "Waiting for backend API..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:8000/api/health &>/dev/null; then
            log_success "Backend API is ready"
            break
        fi
        sleep 3
        timeout=$((timeout - 3))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Backend API failed to start within timeout"
        exit 1
    fi
    
    # Wait for frontend
    log_info "Waiting for frontend..."
    timeout=60
    while [ $timeout -gt 0 ]; do
        if curl -f http://localhost:3000 &>/dev/null; then
            log_success "Frontend is ready"
            break
        fi
        sleep 3
        timeout=$((timeout - 3))
    done
    
    if [ $timeout -le 0 ]; then
        log_error "Frontend failed to start within timeout"
        exit 1
    fi
}

verify_deployment() {
    log_info "Verifying deployment..."
    
    # Check service status
    log_info "Checking service status..."
    docker-compose -f "$COMPOSE_FILE" ps
    
    # Test API endpoints
    log_info "Testing API endpoints..."
    
    # Health check
    if curl -f http://localhost:8000/api/health &>/dev/null; then
        log_success "Health check passed"
    else
        log_error "Health check failed"
        exit 1
    fi
    
    # Status check
    if curl -f http://localhost:8000/api/status &>/dev/null; then
        log_success "Status check passed"
    else
        log_error "Status check failed"
        exit 1
    fi
    
    # Frontend check
    if curl -f http://localhost:3000 &>/dev/null; then
        log_success "Frontend check passed"
    else
        log_error "Frontend check failed"
        exit 1
    fi
    
    log_success "Deployment verification completed successfully"
}

show_deployment_info() {
    log_success "🚀 AI Agent Backend deployed successfully!"
    echo
    echo "📊 Service URLs:"
    echo "  Frontend:        http://localhost:3000"
    echo "  Backend API:     http://localhost:8000"
    echo "  API Docs:        http://localhost:8000/docs"
    echo "  Health Check:    http://localhost:8000/api/health"
    echo
    echo "🔧 Management Commands:"
    echo "  View logs:       docker-compose -f $COMPOSE_FILE logs -f"
    echo "  Stop services:   docker-compose -f $COMPOSE_FILE down"
    echo "  Restart:         docker-compose -f $COMPOSE_FILE restart"
    echo "  Scale backend:   docker-compose -f $COMPOSE_FILE up -d --scale backend=3"
    echo
    echo "📁 Backups stored in: $BACKUP_DIR"
    echo
    log_info "For more information, see docs/deployment-guide.md"
}

cleanup_old_images() {
    log_info "Cleaning up old Docker images..."
    docker image prune -f
    log_success "Cleanup completed"
}

# Main deployment process
main() {
    echo "🤖 AI Agent Backend - Production Deployment"
    echo "=========================================="
    echo
    
    check_prerequisites
    validate_environment
    backup_data
    deploy_services
    wait_for_services
    verify_deployment
    cleanup_old_images
    show_deployment_info
}

# Handle script arguments
case "${1:-deploy}" in
    "deploy")
        main
        ;;
    "stop")
        log_info "Stopping all services..."
        docker-compose -f "$COMPOSE_FILE" down
        log_success "All services stopped"
        ;;
    "restart")
        log_info "Restarting all services..."
        docker-compose -f "$COMPOSE_FILE" restart
        log_success "All services restarted"
        ;;
    "logs")
        docker-compose -f "$COMPOSE_FILE" logs -f
        ;;
    "status")
        docker-compose -f "$COMPOSE_FILE" ps
        ;;
    "backup")
        backup_data
        ;;
    "help")
        echo "Usage: $0 [command]"
        echo
        echo "Commands:"
        echo "  deploy   - Deploy the AI Agent system (default)"
        echo "  stop     - Stop all services"
        echo "  restart  - Restart all services"
        echo "  logs     - Show service logs"
        echo "  status   - Show service status"
        echo "  backup   - Create backup of data"
        echo "  help     - Show this help message"
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac