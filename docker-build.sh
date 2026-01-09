#!/bin/bash

# Docker Build Script for RAG Knowledge Base System

set -e  # Exit on error

echo "======================================================================"
echo "  知识库问答系统 - Docker 构建脚本"
echo "======================================================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
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

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_info "Docker version: $(docker --version)"
print_info "Docker Compose version: $(docker-compose --version 2>/dev/null || docker compose version)"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    print_warn ".env file not found"
    if [ -f .env.example ]; then
        print_info "Creating .env from .env.example..."
        cp .env.example .env
        print_warn "Please edit .env file and add your API keys"
        echo ""
    else
        print_warn "No .env.example found. You may need to set environment variables manually."
        echo ""
    fi
fi

# Create necessary directories
print_info "Creating necessary directories..."
mkdir -p data/raw_documents
mkdir -p data/processed_chunks
mkdir -p data/vector_store
mkdir -p data/cache
mkdir -p logs
mkdir -p models
echo ""

# Build Docker images
print_info "Building Docker images..."
echo ""

if docker compose version &> /dev/null; then
    docker compose build --no-cache
else
    docker-compose build --no-cache
fi

echo ""
print_info "✅ Docker images built successfully!"
echo ""

# Show built images
print_info "Built images:"
docker images | grep -E "rag|REPOSITORY"
echo ""

echo "======================================================================"
echo "  构建完成！"
echo "======================================================================"
echo ""
echo "下一步:"
echo "  1. 编辑 .env 文件，添加你的 API keys"
echo "  2. 将文档放入 data/raw_documents/ 目录"
echo "  3. 运行: bash docker-deploy.sh"
echo ""
echo "或者使用 docker-compose:"
echo "  docker-compose up -d"
echo ""

