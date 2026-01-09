#!/bin/bash

# Docker Stop Script for RAG Knowledge Base System

echo "======================================================================"
echo "  知识库问答系统 - 停止 Docker 服务"
echo "======================================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

# Parse command line arguments
REMOVE_VOLUMES=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --remove-volumes|-v)
            REMOVE_VOLUMES=true
            shift
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --remove-volumes,-v  Remove volumes (WARNING: deletes all data)"
            echo "  --help,-h            Show this help message"
            echo ""
            exit 0
            ;;
        *)
            print_warn "Unknown option: $1"
            shift
            ;;
    esac
done

# Stop containers
print_info "Stopping containers..."

if docker compose version &> /dev/null; then
    if [ "$REMOVE_VOLUMES" = true ]; then
        print_warn "Removing volumes (this will delete all data)..."
        docker compose down -v
    else
        docker compose down
    fi
else
    if [ "$REMOVE_VOLUMES" = true ]; then
        print_warn "Removing volumes (this will delete all data)..."
        docker-compose down -v
    else
        docker-compose down
    fi
fi

echo ""
print_info "✅ Services stopped successfully!"
echo ""

if [ "$REMOVE_VOLUMES" = true ]; then
    print_warn "All data has been removed."
else
    print_info "Data volumes preserved. Use --remove-volumes to delete data."
fi
echo ""

