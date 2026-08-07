#!/bin/bash

# CryptoArbitrage V2.3 - Deployment Script
# Production ready deployment with Docker

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="crypto-arbitrage"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Functions
print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

check_requirements() {
    echo "Checking requirements..."
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    print_success "Docker and Docker Compose are installed"
}

setup_environment() {
    echo "Setting up environment..."
    if [ ! -f "$ENV_FILE" ]; then
        print_warning "$ENV_FILE not found. Creating from example..."
        if [ -f ".env.example" ]; then
            cp .env.example "$ENV_FILE"
        else
            cat > "$ENV_FILE" << EOL
# CryptoArbitrage Environment Variables
# V2.3 - Production Configuration

# System Configuration
SYSTEM_MODE=simulation
LOG_LEVEL=INFO

# Exchange API Keys (Replace with your actual keys)
BINANCE_API_KEY=your_binance_api_key
BINANCE_SECRET=your_binance_secret
OKX_API_KEY=your_okx_api_key
OKX_SECRET=your_okx_secret
OKX_PASSPHRASE=your_okx_passphrase

# Memo0 Configuration
MEM0_API_KEY=your_mem0_api_key

# Monitoring
GRAFANA_ADMIN_PASSWORD=admin123
REDIS_PASSWORD=redis123

# Notification Channels
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
EMAIL_SMTP_HOST=
EMAIL_SMTP_PORT=587
EMAIL_USERNAME=
EMAIL_PASSWORD=
EOL
        fi
        print_warning "Please update $ENV_FILE with your API keys and configurations"
        print_warning "Run: nano .env"
    else
        print_success "$ENV_FILE found"
    fi
}

build_images() {
    echo "Building Docker images..."
    docker-compose build --no-cache
    print_success "Docker images built successfully"
}

start_services() {
    echo "Starting services..."
    docker-compose up -d
    print_success "Services started successfully"
}

stop_services() {
    echo "Stopping services..."
    docker-compose down
    print_success "Services stopped successfully"
}

restart_services() {
    echo "Restarting services..."
    docker-compose restart
    print_success "Services restarted successfully"
}

show_logs() {
    echo "Showing logs (Ctrl+C to exit)..."
    docker-compose logs -f
}

show_status() {
    echo "Container status:"
    docker-compose ps
}

show_health() {
    echo "Health check:"
    docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"
}

run_tests() {
    echo "Running tests..."
    docker-compose exec crypto-arbitrage python -m pytest tests/test_v2_2.py -v
}

cleanup() {
    echo "Cleaning up..."
    docker-compose down -v
    docker system prune -f
    print_success "Cleanup completed"
}

update_code() {
    echo "Updating code..."
    git pull origin main
    print_success "Code updated"
    build_images
    restart_services
}

backup_data() {
    echo "Backing up data..."
    BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
    mkdir -p "$BACKUP_DIR"
    cp -r logs data knowledge_base storage "$BACKUP_DIR/"
    print_success "Data backed up to $BACKUP_DIR"
}

show_help() {
    cat << EOL
CryptoArbitrage V2.3 - Deployment Script

Usage: ./deploy.sh [COMMAND]

Commands:
    setup       Check requirements and set up environment
    build       Build Docker images
    start       Start services
    stop        Stop services
    restart     Restart services
    logs        Show logs
    status      Show container status
    health      Show health check
    test        Run tests
    cleanup     Clean up containers and volumes
    update      Update code and restart services
    backup      Backup data
    help        Show this help message

Examples:
    ./deploy.sh setup
    ./deploy.sh start
    ./deploy.sh logs
    ./deploy.sh status

For production deployment with monitoring:
    docker-compose --profile monitoring up -d

For production deployment with cache:
    docker-compose --profile cache up -d

For full production deployment:
    docker-compose --profile monitoring --profile cache up -d

EOL
}

# Main script logic
case "${1:-help}" in
    setup)
        check_requirements
        setup_environment
        ;;
    build)
        build_images
        ;;
    start)
        start_services
        show_status
        ;;
    stop)
        stop_services
        ;;
    restart)
        restart_services
        show_status
        ;;
    logs)
        show_logs
        ;;
    status)
        show_status
        ;;
    health)
        show_health
        ;;
    test)
        run_tests
        ;;
    cleanup)
        cleanup
        ;;
    update)
        update_code
        ;;
    backup)
        backup_data
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        show_help
        exit 1
        ;;
esac
