#!/bin/bash

# AI-SERVIS Universal Deployment Script
# This script deploys the complete AI-SERVIS Universal system

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="ai-servis-universal"
DOCKER_COMPOSE_FILE="docker-compose.universal.yml"
CONFIG_FILE="config.json"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

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

check_dependencies() {
    log_info "Checking dependencies..."
    
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
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        log_error "Docker is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "All dependencies are available"
}

create_directories() {
    log_info "Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data/audio
    mkdir -p data/communications
    mkdir -p data/core
    mkdir -p volumes/mqtt-data
    mkdir -p volumes/mqtt-logs
    mkdir -p volumes/redis-data-dev
    mkdir -p volumes/postgres-data-dev
    mkdir -p volumes/prometheus-data
    mkdir -p volumes/grafana-data
    mkdir -p volumes/signal-data
    mkdir -p backups
    
    log_success "Directories created"
}

check_config() {
    log_info "Checking configuration..."
    
    if [ ! -f "$CONFIG_FILE" ]; then
        log_warning "Configuration file not found. Creating from example..."
        if [ -f "config.json.example" ]; then
            cp config.json.example config.json
            log_warning "Please edit config.json with your service credentials before continuing."
            read -p "Press Enter to continue after editing the configuration..."
        else
            log_error "No configuration file or example found. Please create config.json"
            exit 1
        fi
    fi
    
    log_success "Configuration file found"
}

backup_existing() {
    if [ -d "volumes" ] && [ "$(ls -A volumes 2>/dev/null)" ]; then
        log_info "Backing up existing data..."
        mkdir -p "$BACKUP_DIR"
        cp -r volumes "$BACKUP_DIR/"
        log_success "Backup created at $BACKUP_DIR"
    fi
}

build_images() {
    log_info "Building Docker images..."
    
    # Build core orchestrator
    log_info "Building core orchestrator..."
    docker build -t ai-servis-core modules/core-orchestrator/
    
    # Build audio assistant
    log_info "Building audio assistant..."
    docker build -t ai-servis-audio modules/ai-audio-assistant/
    
    # Build communications
    log_info "Building communications..."
    docker build -t ai-servis-communications modules/ai-communications/
    
    # Build platform controllers
    log_info "Building platform controllers..."
    docker build -t ai-servis-platform-linux modules/ai-platform-controllers/linux/
    
    # Build service discovery
    log_info "Building service discovery..."
    docker build -t ai-servis-discovery modules/service-discovery/
    
    log_success "All images built successfully"
}

deploy_services() {
    log_info "Deploying services..."
    
    # Stop existing services
    log_info "Stopping existing services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" down --remove-orphans || true
    
    # Start infrastructure services first
    log_info "Starting infrastructure services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d mqtt-broker redis postgres
    
    # Wait for infrastructure to be ready
    log_info "Waiting for infrastructure services to be ready..."
    sleep 10
    
    # Start application services
    log_info "Starting application services..."
    docker-compose -f "$DOCKER_COMPOSE_FILE" up -d
    
    log_success "All services deployed"
}

wait_for_services() {
    log_info "Waiting for services to be ready..."
    
    # Wait for core orchestrator
    log_info "Waiting for core orchestrator..."
    timeout 60 bash -c 'until curl -f http://localhost:8000/health 2>/dev/null; do sleep 2; done' || {
        log_error "Core orchestrator failed to start"
        return 1
    }
    
    # Wait for audio assistant
    log_info "Waiting for audio assistant..."
    timeout 60 bash -c 'until curl -f http://localhost:8001/health 2>/dev/null; do sleep 2; done' || {
        log_warning "Audio assistant may not be ready (audio device access required)"
    }
    
    # Wait for communications
    log_info "Waiting for communications..."
    timeout 60 bash -c 'until curl -f http://localhost:8002/health 2>/dev/null; do sleep 2; done' || {
        log_warning "Communications service may not be ready (API credentials required)"
    }
    
    log_success "Services are ready"
}

show_status() {
    log_info "Service Status:"
    echo ""
    docker-compose -f "$DOCKER_COMPOSE_FILE" ps
    echo ""
    
    log_info "Service URLs:"
    echo "  Core Orchestrator: http://localhost:8000"
    echo "  Audio Assistant:   http://localhost:8001"
    echo "  Communications:    http://localhost:8002"
    echo "  Platform Control:  http://localhost:8003"
    echo "  Service Discovery: http://localhost:8004"
    echo "  Grafana:           http://localhost:3000 (admin/admin)"
    echo "  Prometheus:        http://localhost:9090"
    echo ""
}

show_logs() {
    log_info "Recent logs:"
    echo ""
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs --tail=20
    echo ""
}

cleanup() {
    log_info "Cleaning up..."
    docker system prune -f
    log_success "Cleanup completed"
}

# Main deployment function
deploy() {
    log_info "Starting AI-SERVIS Universal deployment..."
    echo ""
    
    check_dependencies
    create_directories
    check_config
    backup_existing
    build_images
    deploy_services
    wait_for_services
    show_status
    
    log_success "AI-SERVIS Universal deployment completed successfully!"
    echo ""
    log_info "Next steps:"
    echo "  1. Configure your service credentials in config.json"
    echo "  2. Restart services: docker-compose -f $DOCKER_COMPOSE_FILE restart"
    echo "  3. Check logs: docker-compose -f $DOCKER_COMPOSE_FILE logs -f"
    echo "  4. Access Grafana at http://localhost:3000 for monitoring"
    echo ""
}

# Command line options
case "${1:-deploy}" in
    "deploy")
        deploy
        ;;
    "status")
        show_status
        ;;
    "logs")
        show_logs
        ;;
    "stop")
        log_info "Stopping all services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" down
        log_success "All services stopped"
        ;;
    "restart")
        log_info "Restarting all services..."
        docker-compose -f "$DOCKER_COMPOSE_FILE" restart
        log_success "All services restarted"
        ;;
    "cleanup")
        cleanup
        ;;
    "backup")
        backup_existing
        ;;
    "help"|"-h"|"--help")
        echo "AI-SERVIS Universal Deployment Script"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  deploy    Deploy the complete system (default)"
        echo "  status    Show service status"
        echo "  logs      Show recent logs"
        echo "  stop      Stop all services"
        echo "  restart   Restart all services"
        echo "  cleanup   Clean up Docker resources"
        echo "  backup    Create backup of existing data"
        echo "  help      Show this help message"
        echo ""
        ;;
    *)
        log_error "Unknown command: $1"
        echo "Use '$0 help' for usage information"
        exit 1
        ;;
esac
