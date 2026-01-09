# Docker 部署指南

## 🐳 概述

本项目提供完整的 Docker 部署方案，包含：
- **API 服务** - FastAPI 后端
- **Web 界面** - ChatGPT 风格的前端
- **Redis** - 缓存服务

## 📋 前置要求

### 必需
- Docker 20.10+
- Docker Compose 2.0+
- 4GB+ 可用内存
- 10GB+ 可用磁盘空间

### 可选
- NVIDIA GPU (用于本地模型推理)
- Docker Compose V2 (推荐)

## 🚀 快速开始

### 方法1: 使用部署脚本 (推荐)

```bash
# 1. 构建 Docker 镜像
bash docker-build.sh

# 2. 部署服务
bash docker-deploy.sh

# 3. 访问服务
# API: http://localhost:8000
# Web: http://localhost:8080
```

### 方法2: 使用 docker-compose

```bash
# 构建并启动
docker-compose up -d --build

# 查看日志
docker-compose logs -f

# 停止服务
docker-compose down
```

### 方法3: 使用 Makefile

```bash
# 添加到 Makefile 后使用
make docker-build
make docker-up
make docker-down
```

## 📁 目录结构

```
.
├── Dockerfile              # 应用镜像定义
├── docker-compose.yml      # 服务编排配置
├── .dockerignore          # Docker 构建忽略文件
├── docker-build.sh        # 构建脚本
├── docker-deploy.sh       # 部署脚本
├── docker-stop.sh         # 停止脚本
└── data/                  # 数据目录 (挂载到容器)
    ├── raw_documents/     # 原始文档
    ├── processed_chunks/  # 处理后的文本块
    ├── vector_store/      # 向量数据库
    └── cache/             # 缓存数据
```

## ⚙️ 配置

### 环境变量

创建 `.env` 文件：

```bash
# 复制示例文件
cp .env.example .env

# 编辑配置
vim .env
```

必需的环境变量：

```env
# LLM API Keys (至少配置一个)
DEEPSEEK_API_KEY=your_deepseek_api_key
QWEN_API_KEY=your_qwen_api_key
OPENAI_API_KEY=your_openai_api_key

# Ollama (如果使用本地模型)
OLLAMA_BASE_URL=http://host.docker.internal:11434

# Redis (默认配置通常不需要修改)
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=0

# 应用设置
APP_ENV=production
LOG_LEVEL=INFO
```

### 端口配置

默认端口映射：
- `8000` - API 服务
- `8080` - Web 界面
- `6379` - Redis

修改端口（编辑 `docker-compose.yml`）：

```yaml
services:
  api:
    ports:
      - "8000:8000"  # 改为 "9000:8000" 使用 9000 端口
```

## 🔧 使用指南

### 构建知识库

```bash
# 1. 将文档放入 data/raw_documents/
cp your_documents/* data/raw_documents/

# 2. 构建知识库
docker-compose exec api python scripts/build_knowledge_base.py

# 或使用交互式管理工具
docker-compose exec api python scripts/manage_kb.py
```

### 查看日志

```bash
# 所有服务
docker-compose logs -f

# 特定服务
docker-compose logs -f api
docker-compose logs -f web
docker-compose logs -f redis

# 最近 100 行
docker-compose logs --tail=100 api
```

### 服务管理

```bash
# 启动服务
docker-compose up -d

# 停止服务
docker-compose down

# 重启服务
docker-compose restart

# 重启特定服务
docker-compose restart api

# 查看状态
docker-compose ps

# 查看资源使用
docker stats
```

### 进入容器

```bash
# 进入 API 容器
docker-compose exec api bash

# 进入 Redis 容器
docker-compose exec redis sh

# 以 root 用户进入
docker-compose exec -u root api bash
```

### 数据备份

```bash
# 备份数据目录
tar -czf rag-data-backup-$(date +%Y%m%d).tar.gz data/

# 备份 Redis 数据
docker-compose exec redis redis-cli SAVE
cp data/cache/dump.rdb backup/

# 恢复数据
tar -xzf rag-data-backup-20240101.tar.gz
docker-compose restart
```

## 🎯 部署脚本详解

### docker-build.sh

构建 Docker 镜像：

```bash
# 基本用法
bash docker-build.sh

# 功能:
# - 检查 Docker 环境
# - 创建必要目录
# - 构建镜像 (无缓存)
# - 显示构建结果
```

### docker-deploy.sh

部署服务：

```bash
# 后台运行 (默认)
bash docker-deploy.sh

# 前台运行 (查看日志)
bash docker-deploy.sh --foreground

# 重新构建并部署
bash docker-deploy.sh --rebuild

# 查看帮助
bash docker-deploy.sh --help
```

### docker-stop.sh

停止服务：

```bash
# 停止服务 (保留数据)
bash docker-stop.sh

# 停止并删除数据
bash docker-stop.sh --remove-volumes

# 查看帮助
bash docker-stop.sh --help
```

## 📊 监控和调试

### 健康检查

```bash
# API 健康检查
curl http://localhost:8000/health

# Redis 健康检查
docker-compose exec redis redis-cli ping

# 查看容器健康状态
docker-compose ps
```

### 性能监控

```bash
# 实时资源使用
docker stats

# 容器详细信息
docker inspect rag-api
docker inspect rag-redis

# 网络信息
docker network inspect rag_rag-network
```

### 调试技巧

```bash
# 查看容器日志
docker logs rag-api --tail 100 -f

# 检查环境变量
docker-compose exec api env

# 测试网络连接
docker-compose exec api curl http://redis:6379
docker-compose exec api ping redis

# 查看进程
docker-compose exec api ps aux
```

## 🔒 安全建议

### 生产环境

1. **不要暴露 Redis 端口**
   ```yaml
   redis:
     # ports:
     #   - "6379:6379"  # 注释掉
   ```

2. **使用 secrets 管理敏感信息**
   ```yaml
   services:
     api:
       secrets:
         - deepseek_api_key
   secrets:
     deepseek_api_key:
       file: ./secrets/deepseek_key.txt
   ```

3. **限制资源使用**
   ```yaml
   api:
     deploy:
       resources:
         limits:
           cpus: '2'
           memory: 4G
   ```

4. **使用非 root 用户** (已实现)
   - Dockerfile 中已配置 `appuser`

5. **启用 HTTPS**
   - 使用 Nginx 反向代理
   - 配置 SSL 证书

## 🚀 生产部署

### 使用 Nginx 反向代理

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /api {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 使用 Docker Swarm

```bash
# 初始化 Swarm
docker swarm init

# 部署 stack
docker stack deploy -c docker-compose.yml rag

# 查看服务
docker service ls

# 扩展服务
docker service scale rag_api=3
```

### 使用 Kubernetes

参考 `k8s/` 目录中的配置文件（需要单独创建）

## 🔍 故障排查

### 问题1: 容器无法启动

```bash
# 查看详细日志
docker-compose logs api

# 检查配置
docker-compose config

# 重新构建
docker-compose build --no-cache
```

### 问题2: 无法连接 Redis

```bash
# 检查 Redis 是否运行
docker-compose ps redis

# 测试连接
docker-compose exec api ping redis

# 检查网络
docker network ls
docker network inspect rag_rag-network
```

### 问题3: 内存不足

```bash
# 查看资源使用
docker stats

# 增加 Docker 内存限制 (Docker Desktop)
# Settings -> Resources -> Memory

# 或限制容器内存
docker-compose.yml:
  api:
    mem_limit: 2g
```

### 问题4: 模型下载失败

```bash
# 手动下载模型
docker-compose exec api python -c "
from sentence_transformers import SentenceTransformer
model = SentenceTransformer('BAAI/bge-large-zh')
"

# 或挂载预下载的模型
volumes:
  - /path/to/models:/app/models
```

## 📝 最佳实践

1. **定期备份数据**
   ```bash
   # 添加到 crontab
   0 2 * * * cd /path/to/rag && tar -czf backup/data-$(date +\%Y\%m\%d).tar.gz data/
   ```

2. **监控日志大小**
   ```yaml
   logging:
     driver: "json-file"
     options:
       max-size: "10m"
       max-file: "3"
   ```

3. **使用健康检查**
   - 已在 docker-compose.yml 中配置

4. **版本控制**
   ```bash
   # 标记镜像版本
   docker tag rag-api:latest rag-api:v1.0.0
   ```

5. **自动重启**
   ```yaml
   restart: unless-stopped
   ```

## 🎉 总结

Docker 部署提供：
- ✅ **一键部署** - 简化部署流程
- ✅ **环境隔离** - 避免依赖冲突
- ✅ **易于扩展** - 支持水平扩展
- ✅ **便于维护** - 统一管理服务
- ✅ **快速恢复** - 容器化备份恢复

开始使用：
```bash
bash docker-build.sh && bash docker-deploy.sh
```

访问：http://localhost:8080

