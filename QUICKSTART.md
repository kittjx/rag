# 快速开始指南

## 🚀 5分钟快速启动

### 前置要求
- Python 3.8+
- Docker (用于 Redis，可选)
- DeepSeek API Key

### 步骤 1: 克隆并安装

```bash
# 进入项目目录
cd rag

# 安装依赖
pip install -r requirements.txt
```

### 步骤 2: 启动 Redis

**使用 Docker (推荐):**

```bash
# 方式1: 使用 make
make redis-start

# 方式2: 使用 docker-compose
docker-compose up -d redis

# 方式3: 直接使用 docker
docker run -d -p 6379:6379 --name rag-redis redis:alpine
```

**验证 Redis 运行:**

```bash
# 检查容器状态
docker ps | grep redis

# 测试连接
redis-cli ping
# 应该返回: PONG
```

### 步骤 3: 配置环境变量

```bash
# 复制示例配置
cp .env.example .env

# 编辑 .env 文件，设置你的 API Key
# DEEPSEEK_API_KEY=sk-your-api-key-here
```

### 步骤 4: 准备文档

```bash
# 将你的文档放入此目录
cp your-documents/* data/raw_documents/

# 支持的格式: PDF, DOCX, TXT, MD
```

### 步骤 5: 构建知识库

```bash
# 构建知识库
make build

# 或直接运行脚本
python scripts/build_knowledge_base.py
```

这个过程会：
- 📄 加载所有文档
- ✂️ 分割成文本块
- 🧮 生成向量嵌入
- 💾 存储到 ChromaDB

**预计时间:** 取决于文档数量，通常 1-5 分钟

### 步骤 6: 检查环境

```bash
# 运行环境检查
python check_setup.py

# 或使用 make
make check-env
```

确保所有检查都通过 ✅

### 步骤 7: 启动服务

```bash
# 生产模式
make start

# 或开发模式（支持热重载）
make dev
```

服务启动后访问: **http://localhost:8000**

### 步骤 8: 测试 API

**方式1: 使用测试脚本**

```bash
# 基础测试
make test

# 完整测试（包括问答）
python test_api.py --full
```

**方式2: 使用 Swagger UI**

浏览器访问: http://localhost:8000/api/docs

**方式3: 使用 curl**

```bash
# 健康检查
curl http://localhost:8000/health

# 问答测试
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你的问题",
    "top_k": 5
  }'
```

## 🎯 常用命令

```bash
# 查看知识库统计
make stats

# 查看文档列表
make list

# 查看 Redis 日志
make redis-logs

# 停止 Redis
make redis-stop

# 清理缓存
make clean
```

## 🔧 故障排除

### Redis 连接失败

```bash
# 检查 Redis 是否运行
docker ps | grep redis

# 重启 Redis
docker restart rag-redis

# 查看 Redis 日志
docker logs rag-redis
```

### 知识库未初始化

```bash
# 检查文档目录
ls -la data/raw_documents/

# 重新构建
make build
```

### API 调用失败

```bash
# 检查 API Key
cat .env | grep DEEPSEEK_API_KEY

# 查看服务日志
tail -f logs/api.log
```

## 📚 下一步

- 📖 阅读完整文档: [README.md](README.md)
- 🔍 查看改进说明: [IMPROVEMENTS.md](IMPROVEMENTS.md)
- 🛠️ 使用管理工具: `python scripts/manage_kb.py --help`

## 💡 提示

1. **开发模式**: 使用 `make dev` 启动，支持代码热重载
2. **查看日志**: 日志文件在 `logs/` 目录
3. **Redis 可选**: 不使用 Redis 也能运行，只是没有缓存
4. **文档更新**: 添加新文档后重新运行 `make build`

祝使用愉快！🎉

