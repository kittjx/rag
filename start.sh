#!/bin/bash
# start.sh - Knowledge Base API Startup Script

set -e  # Exit on error

# 获取脚本所在目录
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== 知识库API服务启动脚本 ===${NC}"

# 检查Python环境
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}错误: 未找到Python3${NC}"
    exit 1
fi

# 加载环境变量（如果存在.env文件）
if [ -f .env ]; then
    echo -e "${GREEN}加载环境变量...${NC}"
    export $(cat .env | grep -v '^#' | xargs)
else
    echo -e "${YELLOW}警告: 未找到.env文件，使用默认配置${NC}"
fi

# 设置默认环境变量（如果未设置）
export DEEPSEEK_API_KEY="${DEEPSEEK_API_KEY:-}"
export REDIS_URL="${REDIS_URL:-redis://localhost:6379}"
export API_HOST="${API_HOST:-0.0.0.0}"
export API_PORT="${API_PORT:-8000}"
export WORKERS="${WORKERS:-2}"
export MODE="${MODE:-production}"

# 检查必需的环境变量
if [ -z "$DEEPSEEK_API_KEY" ]; then
    echo -e "${YELLOW}警告: DEEPSEEK_API_KEY 未设置${NC}"
fi

# 检查Redis连接（支持Docker和本地）
echo -e "${GREEN}检查Redis连接...${NC}"

# 尝试使用Python检查Redis连接
REDIS_CHECK=$(python3 -c "
import sys
try:
    import redis
    client = redis.Redis.from_url('$REDIS_URL', socket_timeout=2, socket_connect_timeout=2)
    client.ping()
    print('OK')
except Exception as e:
    print(f'FAIL:{e}')
" 2>&1)

if [[ "$REDIS_CHECK" == "OK" ]]; then
    echo -e "${GREEN}✓ Redis连接成功 ($REDIS_URL)${NC}"
elif [[ "$REDIS_CHECK" == FAIL:* ]]; then
    echo -e "${YELLOW}⚠ Redis连接失败${NC}"
    echo -e "${YELLOW}  URL: $REDIS_URL${NC}"
    echo -e "${YELLOW}  错误: ${REDIS_CHECK#FAIL:}${NC}"
    echo -e "${YELLOW}  提示: 如果使用Docker，运行 'make redis-start' 或 'docker-compose up -d redis'${NC}"
    echo -e "${YELLOW}  缓存功能将不可用，但不影响核心功能${NC}"
else
    echo -e "${YELLOW}⚠ 无法检查Redis状态${NC}"
    echo -e "${YELLOW}  缓存功能可能不可用，但不影响核心功能${NC}"
fi

# 检查向量数据库是否存在
if [ ! -d "data/vector_store" ] || [ -z "$(ls -A data/vector_store 2>/dev/null)" ]; then
    echo -e "${YELLOW}警告: 向量数据库未初始化${NC}"
    echo -e "${YELLOW}请先运行: python scripts/build_knowledge_base.py${NC}"
fi

# 启动FastAPI服务
echo -e "${GREEN}启动知识库API服务...${NC}"
echo -e "模式: ${MODE}"
echo -e "地址: ${API_HOST}:${API_PORT}"
echo -e "工作进程: ${WORKERS}"

if [ "$MODE" = "development" ] || [ "$MODE" = "dev" ]; then
    # 开发模式 - 启用热重载
    echo -e "${YELLOW}开发模式 - 启用热重载${NC}"
    uvicorn api.main:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --reload \
        --log-level debug
else
    # 生产模式
    echo -e "${GREEN}生产模式${NC}"
    uvicorn api.main:app \
        --host "$API_HOST" \
        --port "$API_PORT" \
        --workers "$WORKERS" \
        --log-level info \
        --access-log \
        --proxy-headers \
        --forwarded-allow-ips "*"
fi