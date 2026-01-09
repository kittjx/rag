#!/bin/bash

# Connection Diagnostic Script

echo "======================================================================"
echo "  连接诊断工具"
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

# 1. Check if containers are running
echo "1. 检查容器状态..."
if docker ps | grep -q rag-api; then
    print_success "API 容器正在运行"
else
    print_error "API 容器未运行"
    echo "   启动容器: docker-compose up -d"
fi

if docker ps | grep -q rag-web; then
    print_success "Web 容器正在运行"
else
    print_info "Web 容器未运行（可选）"
fi

if docker ps | grep -q rag-redis; then
    print_success "Redis 容器正在运行"
else
    print_info "Redis 容器未运行（可选）"
fi

echo ""

# 2. Check port bindings
echo "2. 检查端口绑定..."
if docker ps | grep rag-api | grep -q "0.0.0.0:8000"; then
    print_success "API 端口 8000 已绑定"
else
    print_error "API 端口 8000 未绑定"
    echo "   检查: docker ps | grep rag-api"
fi

if docker ps | grep rag-web | grep -q "0.0.0.0:8080"; then
    print_success "Web 端口 8080 已绑定"
else
    print_info "Web 端口 8080 未绑定（如果本地运行 Web 则正常）"
fi

echo ""

# 3. Test API from host
echo "3. 测试从主机访问 API..."
if curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    print_success "可以从主机访问 API (http://localhost:8000)"
    echo "   响应: $(curl -s http://localhost:8000/health)"
else
    print_error "无法从主机访问 API (http://localhost:8000)"
    echo "   这是问题所在！"
fi

echo ""

# 4. Test API from inside container
echo "4. 测试从容器内访问 API..."
if docker ps | grep -q rag-api; then
    if docker exec rag-api curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
        print_success "可以从容器内访问 API"
    else
        print_error "无法从容器内访问 API"
    fi
else
    print_info "API 容器未运行，跳过此检查"
fi

echo ""

# 5. Check if port is in use
echo "5. 检查端口占用..."
if lsof -i :8000 > /dev/null 2>&1; then
    print_info "端口 8000 正在使用中:"
    lsof -i :8000 | grep LISTEN
else
    print_error "端口 8000 未被占用"
fi

if lsof -i :8080 > /dev/null 2>&1; then
    print_info "端口 8080 正在使用中:"
    lsof -i :8080 | grep LISTEN
else
    print_info "端口 8080 未被占用"
fi

echo ""

# 6. Check Docker network
echo "6. 检查 Docker 网络..."
if docker network ls | grep -q rag_rag-network; then
    print_success "Docker 网络 rag_rag-network 存在"
    
    # Check if containers are connected
    if docker network inspect rag_rag-network | grep -q rag-api; then
        print_success "API 容器已连接到网络"
    fi
else
    print_error "Docker 网络不存在"
fi

echo ""

# 7. Show container logs (last 10 lines)
echo "7. API 容器日志（最后 10 行）..."
if docker ps | grep -q rag-api; then
    docker logs --tail 10 rag-api 2>&1 | sed 's/^/   /'
else
    print_info "API 容器未运行"
fi

echo ""
echo "======================================================================"
echo "  诊断完成"
echo "======================================================================"
echo ""

# Provide recommendations
echo "建议:"
echo ""

if ! docker ps | grep -q rag-api; then
    echo "1. 启动 API 容器:"
    echo "   docker-compose up -d api"
    echo ""
fi

if ! curl -s -f http://localhost:8000/health > /dev/null 2>&1; then
    echo "2. 如果 API 容器正在运行但无法访问，尝试:"
    echo "   - 重启容器: docker-compose restart api"
    echo "   - 检查防火墙设置"
    echo "   - 检查 Docker Desktop 网络设置"
    echo ""
fi

echo "3. 查看完整日志:"
echo "   docker-compose logs -f api"
echo ""

echo "4. 如果问题仍然存在，尝试重新构建:"
echo "   docker-compose down"
echo "   docker-compose up -d --build"
echo ""

