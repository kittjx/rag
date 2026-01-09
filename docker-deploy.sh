#!/bin/bash

# Docker Deployment Script for RAG Knowledge Base System

set -e  # Exit on error

echo "======================================================================"
echo "  知识库问答系统 - Docker 部署脚本"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# Check if Docker is running
if ! docker info &> /dev/null; then
    print_error "Docker is not running. Please start Docker first."
    exit 1
fi

# Parse command line arguments
REBUILD=false
DETACH=true

while [[ $# -gt 0 ]]; do
    case $1 in
        --rebuild)
            REBUILD=true
            shift
            ;;
        --foreground|-f)
            DETACH=false
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --rebuild       Rebuild Docker images before starting"
            echo "  --foreground,-f Run in foreground (default: background)"
            echo "  --help,-h       Show this help message"
            echo ""
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Rebuild if requested
if [ "$REBUILD" = true ]; then
    print_step "Rebuilding Docker images..."
    bash docker-build.sh
    echo ""
fi

# Check if .env file exists
if [ ! -f .env ]; then
    print_warn ".env file not found. Using default configuration."
    print_warn "Some features may not work without proper API keys."
    echo ""
fi

# Stop existing containers
print_step "Stopping existing containers..."
if docker compose version &> /dev/null; then
    docker compose down 2>/dev/null || true
else
    docker-compose down 2>/dev/null || true
fi
echo ""

# Start services
print_step "Starting services..."
echo ""

if [ "$DETACH" = true ]; then
    if docker compose version &> /dev/null; then
        docker compose up -d
    else
        docker-compose up -d
    fi
else
    if docker compose version &> /dev/null; then
        docker compose up
    else
        docker-compose up
    fi
fi

if [ "$DETACH" = true ]; then
    echo ""
    print_info "Waiting for services to be healthy..."
    sleep 5
    
    # Check service status
    echo ""
    print_step "Service Status:"
    if docker compose version &> /dev/null; then
        docker compose ps
    else
        docker-compose ps
    fi
    
    echo ""
    echo "======================================================================"
    echo "  🎉 部署成功！"
    echo "======================================================================"
    echo ""
    echo "服务地址:"
    echo "  📡 API服务:  http://localhost:8000"
    echo "  🌐 Web界面:  http://localhost:8080"
    echo "  🔴 Redis:    localhost:6379"
    echo ""
    echo "API文档:"
    echo "  📚 Swagger UI: http://localhost:8000/docs"
    echo "  📖 ReDoc:      http://localhost:8000/redoc"
    echo ""
    echo "管理命令:"
    echo "  查看日志:   docker-compose logs -f"
    echo "  查看状态:   docker-compose ps"
    echo "  停止服务:   docker-compose down"
    echo "  重启服务:   docker-compose restart"
    echo ""
    echo "构建知识库:"
    echo "  docker-compose exec api python scripts/build_knowledge_base.py"
    echo ""
    echo "查看知识库统计:"
    echo "  docker-compose exec api python scripts/manage_kb.py stats"
    echo ""
fi

