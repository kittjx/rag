# 🚀 快速部署指南

## 一分钟部署

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd rag

# 2. 配置环境（可选）
cp .env.example .env
# 编辑 .env 添加 API keys

# 3. 一键部署
bash docker-build.sh && bash docker-deploy.sh

# 4. 访问
# Web界面: http://localhost:8080
# API文档: http://localhost:8000/docs
```

## 📋 前置要求

- ✅ Docker 20.10+
- ✅ Docker Compose 2.0+
- ✅ 4GB+ 内存
- ✅ 10GB+ 磁盘空间

## 🎯 部署方式

### 方式1: 使用脚本（最简单）

```bash
bash docker-build.sh    # 构建镜像
bash docker-deploy.sh   # 启动服务
bash docker-stop.sh     # 停止服务
```

### 方式2: 使用 Makefile

```bash
make docker-build    # 构建镜像
make docker-up       # 启动服务
make docker-down     # 停止服务
make docker-logs     # 查看日志
```

### 方式3: 使用 docker-compose

```bash
docker-compose up -d --build    # 构建并启动
docker-compose logs -f          # 查看日志
docker-compose down             # 停止服务
```

## 📚 添加文档并构建知识库

```bash
# 1. 添加文档
cp your_documents/* data/raw_documents/

# 2. 构建知识库
docker-compose exec api python scripts/build_knowledge_base.py

# 3. 查看统计
docker-compose exec api python scripts/manage_kb.py stats
```

## 🔧 常用命令

```bash
# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f api
docker-compose logs -f web

# 重启服务
docker-compose restart

# 进入容器
docker-compose exec api bash

# 测试 API
curl http://localhost:8000/health
```

## 🌐 访问地址

- **Web界面**: http://localhost:8080
- **API文档**: http://localhost:8000/docs
- **API ReDoc**: http://localhost:8000/redoc
- **健康检查**: http://localhost:8000/health

## ⚙️ 环境变量配置

编辑 `.env` 文件：

```env
# LLM API Keys (至少配置一个)
DEEPSEEK_API_KEY=sk-xxx
QWEN_API_KEY=sk-xxx
OPENAI_API_KEY=sk-xxx

# Ollama (本地模型)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Redis (默认配置)
REDIS_HOST=redis
REDIS_PORT=6379
```

## 🔍 故障排查

### 问题1: 端口被占用

```bash
# 修改 docker-compose.yml
services:
  api:
    ports:
      - "9000:8000"  # 改为 9000
```

### 问题2: 无法连接 Redis

```bash
# 检查 Redis 状态
docker-compose ps redis
docker-compose logs redis

# 重启 Redis
docker-compose restart redis
```

### 问题3: 内存不足

```bash
# 查看资源使用
docker stats

# 增加 Docker Desktop 内存限制
# Settings -> Resources -> Memory
```

## 📖 完整文档

- **[DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md)** - 部署总结
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - 详细部署指南
- **[README.md](README.md)** - 项目文档
- **[WEB_INTERFACE_GUIDE.md](WEB_INTERFACE_GUIDE.md)** - Web界面指南

## 🎉 开始使用

```bash
# 一键启动
bash docker-deploy.sh

# 打开浏览器
open http://localhost:8080

# 开始提问！
```

---

**需要帮助？** 查看 [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) 获取详细说明。

