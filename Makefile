.PHONY: help install build start dev test test-llm test-stream clean stats redis-start redis-stop redis-logs

help:
	@echo "知识库问答系统 - 可用命令:"
	@echo ""
	@echo "  make install      - 安装依赖"
	@echo "  make build        - 构建知识库"
	@echo "  make start        - 启动服务（生产模式）"
	@echo "  make dev          - 启动服务（开发模式）"
	@echo "  make test         - 运行API测试"
	@echo "  make test-llm     - 测试LLM后端"
	@echo "  make test-stream  - 测试流式问答"
	@echo "  make stats        - 显示知识库统计"
	@echo "  make clean        - 清理缓存和日志"
	@echo ""
	@echo "Redis管理:"
	@echo "  make redis-start  - 启动Redis (Docker)"
	@echo "  make redis-stop   - 停止Redis"
	@echo "  make redis-logs   - 查看Redis日志"
	@echo ""

install:
	@echo "📦 安装依赖..."
	pip install -r requirements.txt
	@echo "✅ 依赖安装完成"

build:
	@echo "🔨 构建知识库..."
	python scripts/build_knowledge_base.py
	@echo "✅ 知识库构建完成"

start:
	@echo "🚀 启动服务（生产模式）..."
	bash start.sh

dev:
	@echo "🚀 启动服务（开发模式）..."
	MODE=development bash start.sh

test:
	@echo "🧪 运行API测试..."
	python test_api.py

test-full:
	@echo "🧪 运行完整API测试..."
	python test_api.py --full

test-llm:
	@echo "🧪 测试LLM后端..."
	python test_llm_backends.py

test-stream:
	@echo "🧪 测试流式问答..."
	python test_stream_chat.py

stats:
	@echo "📊 知识库统计..."
	python scripts/manage_kb.py stats

list:
	@echo "📚 文档列表..."
	python scripts/manage_kb.py list

clean:
	@echo "🧹 清理缓存和日志..."
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	rm -rf logs/*.log 2>/dev/null || true
	@echo "✅ 清理完成"

format:
	@echo "🎨 格式化代码..."
	black api/ scripts/ config.py
	isort api/ scripts/ config.py
	@echo "✅ 格式化完成"

check:
	@echo "🔍 检查代码..."
	flake8 api/ scripts/ --max-line-length=100 --ignore=E203,W503
	@echo "✅ 检查完成"

# Redis管理
redis-start:
	@echo "🔴 启动Redis (Docker)..."
	docker-compose up -d redis
	@echo "✅ Redis已启动"
	@echo "连接地址: redis://localhost:6379"

redis-stop:
	@echo "🔴 停止Redis..."
	docker-compose stop redis
	@echo "✅ Redis已停止"

redis-logs:
	@echo "🔴 Redis日志..."
	docker-compose logs -f redis

redis-cli:
	@echo "🔴 连接Redis CLI..."
	docker-compose exec redis redis-cli

# 完整环境管理
setup: install redis-start
	@echo "✅ 环境设置完成"

check-env:
	@echo "🔍 检查环境..."
	python check_setup.py

