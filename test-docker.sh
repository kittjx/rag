#!/bin/bash

# Quick Docker Test Script

echo "======================================================================"
echo "  Docker 配置测试"
echo "======================================================================"
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

# Check Docker
echo "1. 检查 Docker..."
if command -v docker &> /dev/null; then
    print_success "Docker 已安装: $(docker --version)"
else
    print_error "Docker 未安装"
    exit 1
fi

# Check Docker Compose
echo ""
echo "2. 检查 Docker Compose..."
if docker compose version &> /dev/null; then
    print_success "Docker Compose 已安装: $(docker compose version)"
elif command -v docker-compose &> /dev/null; then
    print_success "Docker Compose 已安装: $(docker-compose --version)"
else
    print_error "Docker Compose 未安装"
    exit 1
fi

# Check Docker daemon
echo ""
echo "3. 检查 Docker 守护进程..."
if docker info &> /dev/null; then
    print_success "Docker 守护进程正在运行"
else
    print_error "Docker 守护进程未运行"
    exit 1
fi

# Validate Dockerfile
echo ""
echo "4. 验证 Dockerfile..."
if [ -f Dockerfile ]; then
    print_success "Dockerfile 存在"
else
    print_error "Dockerfile 不存在"
    exit 1
fi

# Validate docker-compose.yml
echo ""
echo "5. 验证 docker-compose.yml..."
if [ -f docker-compose.yml ]; then
    print_success "docker-compose.yml 存在"
    
    # Validate syntax
    if docker compose config > /dev/null 2>&1 || docker-compose config > /dev/null 2>&1; then
        print_success "docker-compose.yml 语法正确"
    else
        print_error "docker-compose.yml 语法错误"
        exit 1
    fi
else
    print_error "docker-compose.yml 不存在"
    exit 1
fi

# Check .dockerignore
echo ""
echo "6. 检查 .dockerignore..."
if [ -f .dockerignore ]; then
    print_success ".dockerignore 存在"
else
    print_info ".dockerignore 不存在 (可选)"
fi

# Check required directories
echo ""
echo "7. 检查必要目录..."
for dir in data/raw_documents data/processed_chunks data/vector_store data/cache logs models; do
    if [ -d "$dir" ]; then
        print_success "$dir 存在"
    else
        print_info "$dir 不存在，将在构建时创建"
    fi
done

# Check .env file
echo ""
echo "8. 检查环境配置..."
if [ -f .env ]; then
    print_success ".env 文件存在"
else
    print_info ".env 文件不存在"
    if [ -f .env.example ]; then
        print_info "可以从 .env.example 复制: cp .env.example .env"
    fi
fi

echo ""
echo "======================================================================"
print_success "所有检查通过！可以开始构建 Docker 镜像"
echo "======================================================================"
echo ""
echo "下一步:"
echo "  1. 如果需要，创建 .env 文件: cp .env.example .env"
echo "  2. 构建镜像: bash docker-build.sh"
echo "  3. 启动服务: bash docker-deploy.sh"
echo ""

