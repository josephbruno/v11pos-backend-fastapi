#!/bin/bash

# FastAPI POS System - Docker Management Script
# Usage: ./docker.sh [command]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Detect if we need sudo for docker
USE_SUDO=""
if ! docker info > /dev/null 2>&1; then
    if sudo docker info > /dev/null 2>&1; then
        print_warning "Using sudo for Docker commands"
        USE_SUDO="sudo"
    else
        print_error "Docker is not running or not accessible. Please start Docker first."
        exit 1
    fi
fi

# Function to check if Docker is running
check_docker() {
    if ! $USE_SUDO docker info > /dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    print_success "Docker is running"
}

# Function to build containers
build() {
    print_header "Building Docker Containers"
    check_docker
    
    print_info "Building images..."
    $USE_SUDO docker compose build
    
    print_success "Build completed successfully!"
}

# Function to start containers
up() {
    print_header "Starting Docker Containers"
    check_docker
    
    print_info "Starting services..."
    $USE_SUDO docker compose up -d
    
    print_info "Waiting for MySQL to be ready..."
    sleep 10
    
    # Check if containers are running
    if $USE_SUDO docker compose ps | grep -q "Up"; then
        print_success "Containers are running!"
        $USE_SUDO docker compose ps
    else
        print_error "Failed to start containers"
        $USE_SUDO docker compose logs
        exit 1
    fi
}

# Function to stop containers
down() {
    print_header "Stopping Docker Containers"
    
    print_info "Stopping services..."
    $USE_SUDO docker compose down
    
    print_success "Containers stopped successfully!"
}

# Function to stop and remove volumes
down_volumes() {
    print_header "Stopping Docker Containers and Removing Volumes"
    
    print_warning "This will remove all data in the database!"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Stopping services and removing volumes..."
        $USE_SUDO docker compose down -v
        print_success "Containers and volumes removed successfully!"
    else
        print_info "Operation cancelled"
    fi
}

# Function to view logs
logs() {
    print_header "Docker Container Logs"
    
    if [ -z "$2" ]; then
        print_info "Showing logs for all services (press Ctrl+C to exit)..."
        $USE_SUDO docker compose logs -f
    else
        print_info "Showing logs for $2 (press Ctrl+C to exit)..."
        $USE_SUDO docker compose logs -f "$2"
    fi
}

# Function to create Alembic migration
migrate_create() {
    print_header "Creating Alembic Migration"
    
    if [ -z "$2" ]; then
        print_error "Please provide a migration message"
        echo "Usage: ./docker.sh migrate:create \"migration message\""
        exit 1
    fi
    
    print_info "Creating migration: $2"
    $USE_SUDO docker compose exec fastapi alembic revision --autogenerate -m "$2"
    
    print_success "Migration created successfully!"
}

# Function to apply Alembic migrations
migrate_up() {
    print_header "Applying Alembic Migrations"
    
    print_info "Applying migrations..."
    $USE_SUDO docker compose exec fastapi alembic upgrade head
    
    print_success "Migrations applied successfully!"
}

# Function to rollback Alembic migration
migrate_down() {
    print_header "Rolling Back Alembic Migration"
    
    print_warning "This will rollback the last migration"
    read -p "Are you sure? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_info "Rolling back migration..."
        $USE_SUDO docker compose exec fastapi alembic downgrade -1
        print_success "Migration rolled back successfully!"
    else
        print_info "Operation cancelled"
    fi
}

# Function to show migration history
migrate_history() {
    print_header "Alembic Migration History"
    
    $USE_SUDO docker compose exec fastapi alembic history
}

# Function to show current migration
migrate_current() {
    print_header "Current Alembic Migration"
    
    $USE_SUDO docker compose exec fastapi alembic current
}

# Function to restart containers
restart() {
    print_header "Restarting Docker Containers"
    
    print_info "Restarting services..."
    $USE_SUDO docker compose restart
    
    print_success "Containers restarted successfully!"
    $USE_SUDO docker compose ps
}

# Function to show container status
status() {
    print_header "Docker Container Status"
    
    $USE_SUDO docker compose ps
}

# Function to execute command in container
exec_cmd() {
    if [ -z "$2" ]; then
        print_info "Opening bash shell in fastapi container..."
        $USE_SUDO docker compose exec fastapi bash
    else
        print_info "Executing command in fastapi container..."
        $USE_SUDO docker compose exec fastapi "${@:2}"
    fi
}

# Function to build and start (full setup)
setup() {
    print_header "Full Docker Setup"
    
    build
    echo ""
    up
    echo ""
    
    print_info "Creating initial migration..."
    sleep 2
    migrate_create "Initial migration"
    echo ""
    
    print_info "Applying migrations..."
    migrate_up
    echo ""
    
    print_success "Setup completed successfully!"
    echo ""
    print_info "API Documentation: http://localhost:8000/docs"
    print_info "Health Check: http://localhost:8000/health"
    echo ""
    print_info "To view logs: ./docker.sh logs"
    print_info "To stop: ./docker.sh down"
}

# Function to show help
show_help() {
    echo "FastAPI POS System - Docker Management Script"
    echo ""
    echo "Usage: ./docker.sh [command]"
    echo ""
    echo "Available commands:"
    echo ""
    echo "  ${GREEN}setup${NC}                    - Full setup (build, up, migrate)"
    echo "  ${GREEN}build${NC}                    - Build Docker images"
    echo "  ${GREEN}up${NC}                       - Start containers"
    echo "  ${GREEN}down${NC}                     - Stop containers"
    echo "  ${GREEN}down:volumes${NC}             - Stop containers and remove volumes"
    echo "  ${GREEN}restart${NC}                  - Restart containers"
    echo "  ${GREEN}status${NC}                   - Show container status"
    echo "  ${GREEN}logs${NC} [service]           - View logs (all or specific service)"
    echo ""
    echo "  ${YELLOW}migrate:create${NC} \"msg\"     - Create new migration"
    echo "  ${YELLOW}migrate:up${NC}               - Apply migrations"
    echo "  ${YELLOW}migrate:down${NC}             - Rollback last migration"
    echo "  ${YELLOW}migrate:history${NC}          - Show migration history"
    echo "  ${YELLOW}migrate:current${NC}          - Show current migration"
    echo ""
    echo "  ${BLUE}exec${NC} [command]           - Execute command in fastapi container"
    echo "  ${BLUE}shell${NC}                    - Open bash shell in fastapi container"
    echo ""
    echo "Examples:"
    echo "  ./docker.sh setup"
    echo "  ./docker.sh logs fastapi"
    echo "  ./docker.sh migrate:create \"Add user table\""
    echo "  ./docker.sh exec python --version"
    echo ""
}

# Main script logic
case "$1" in
    setup)
        setup
        ;;
    build)
        build
        ;;
    up)
        up
        ;;
    down)
        down
        ;;
    down:volumes)
        down_volumes
        ;;
    restart)
        restart
        ;;
    status)
        status
        ;;
    logs)
        logs "$@"
        ;;
    migrate:create)
        migrate_create "$@"
        ;;
    migrate:up)
        migrate_up
        ;;
    migrate:down)
        migrate_down
        ;;
    migrate:history)
        migrate_history
        ;;
    migrate:current)
        migrate_current
        ;;
    exec)
        exec_cmd "$@"
        ;;
    shell)
        exec_cmd
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        if [ -z "$1" ]; then
            show_help
        else
            print_error "Unknown command: $1"
            echo ""
            show_help
            exit 1
        fi
        ;;
esac
