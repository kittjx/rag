# 知识库问答系统 (RAG Knowledge Base)

基于 RAG (Retrieval-Augmented Generation) 的中文知识库问答系统，支持多种LLM后端。

## 🌟 特性

- **智能问答**: 基于企业文档的智能问答系统
- **多格式支持**: 支持 PDF、DOCX、TXT、MD 等多种文档格式
- **高效检索**: 使用 BGE-large-zh 向量模型和 ChromaDB 向量数据库
- **🔥 多LLM后端**: 支持 DeepSeek、Qwen、OpenAI、Ollama，可灵活切换
- **🔄 智能切换**: 自动检测可用后端，支持故障自动转移
- **缓存优化**: Redis 缓存提升响应速度
- **流式输出**: 支持流式响应，提升用户体验
- **RESTful API**: 完整的 FastAPI 接口
- **🐳 Docker支持**: 一键启动 Redis

## 📋 系统要求

- Python 3.8+
- Redis (可选，用于缓存)
- 4GB+ RAM (用于加载嵌入模型)

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动 Redis (可选但推荐)

使用 Docker 启动 Redis：

```bash
# 使用 docker-compose
make redis-start

# 或直接使用 docker
docker run -d -p 6379:6379 --name rag-redis redis:alpine
```

如果不使用 Redis，缓存功能将不可用，但不影响核心功能。

### 3. 配置环境变量

复制环境变量示例文件并编辑：

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置必要的配置：

```env
DEEPSEEK_API_KEY=your_api_key_here
REDIS_URL=redis://localhost:6379
```

### 4. 准备文档

将文档放入 `data/raw_documents/` 目录：

```bash
mkdir -p data/raw_documents
# 复制你的文档到这个目录
```

### 5. 构建知识库

```bash
python scripts/build_knowledge_base.py
# 或使用 make
make build
```

这将：
- 加载所有文档
- 分割成文本块
- 生成向量嵌入
- 存储到 ChromaDB

### 6. 启动服务

```bash
# 生产模式
bash start.sh
# 或使用 make
make start

# 开发模式（热重载）
MODE=development bash start.sh
# 或使用 make
make dev
```

服务将在 `http://localhost:8000` 启动

## 🤖 LLM后端配置

系统支持多种LLM后端，可以灵活切换：

### 支持的后端

| 后端 | 说明 | 配置要求 |
|------|------|----------|
| **DeepSeek** | 高性价比中文大模型 | API Key |
| **Qwen** | 阿里云通义千问 | API Key |
| **OpenAI** | GPT系列模型 | API Key |
| **Ollama** | 本地开源模型 | 本地安装 |

### 快速配置

编辑 `.env` 文件：

```bash
# 自动检测模式（推荐）
LLM_BACKEND=auto

# 或指定特定后端
LLM_BACKEND=deepseek  # deepseek, qwen, openai, ollama

# 配置API密钥
DEEPSEEK_API_KEY=sk-xxxxx
QWEN_API_KEY=sk-xxxxx
OPENAI_API_KEY=sk-xxxxx

# 本地模型配置
USE_LOCAL_LLM=false
OLLAMA_MODEL=qwen2.5:7b
```

### 查看和切换后端

```bash
# 查看当前后端
curl http://localhost:8000/api/v1/system/version

# 查看所有后端状态
curl http://localhost:8000/api/v1/system/llm/backends

# 动态切换后端
curl -X POST http://localhost:8000/api/v1/system/llm/switch/qwen
```

**详细文档**: 查看 [LLM_BACKENDS.md](LLM_BACKENDS.md)

## 📚 API 文档

启动服务后访问：

- Swagger UI: `http://localhost:8000/api/docs`
- ReDoc: `http://localhost:8000/api/redoc`

### 主要接口

#### 1. 问答接口

```bash
POST /api/v1/chat
Content-Type: application/json

{
  "question": "你的问题",
  "top_k": 5,
  "temperature": 0.1,
  "use_cache": true
}
```

#### 2. 流式问答

```bash
POST /api/v1/chat/stream
Content-Type: application/json

{
  "question": "你的问题",
  "top_k": 5
}
```

#### 3. 文档搜索

```bash
POST /api/v1/documents/search
Content-Type: application/json

{
  "query": "搜索关键词",
  "top_k": 10
}
```

#### 4. 健康检查

```bash
GET /api/v1/system/health
```

## 🏗️ 项目结构

```
rag/
├── api/                    # API 服务
│   ├── routers/           # 路由模块
│   │   ├── chat.py       # 问答接口
│   │   ├── documents.py  # 文档接口
│   │   └── system.py     # 系统接口
│   ├── services/          # 服务层
│   │   ├── vector_service.py   # 向量检索
│   │   ├── llm_service.py      # LLM 服务
│   │   └── cache_service.py    # 缓存服务
│   ├── utils/             # 工具函数
│   ├── models.py          # 数据模型
│   └── main.py            # 主应用
├── scripts/               # 脚本
│   └── build_knowledge_base.py  # 构建知识库
├── data/                  # 数据目录
│   ├── raw_documents/    # 原始文档
│   ├── processed_chunks/ # 处理后的文本块
│   └── vector_store/     # 向量数据库
├── models/                # 模型文件
├── logs/                  # 日志文件
├── config.py              # 配置文件
├── requirements.txt       # 依赖列表
├── start.sh              # 启动脚本
└── README.md             # 项目文档
```

## ⚙️ 配置说明

主要配置项在 `config.py` 中，可通过环境变量覆盖：

| 环境变量 | 说明 | 默认值 |
|---------|------|--------|
| `DEEPSEEK_API_KEY` | DeepSeek API 密钥 | - |
| `REDIS_URL` | Redis 连接地址 | `redis://localhost:6379` |
| `API_HOST` | API 服务地址 | `0.0.0.0` |
| `API_PORT` | API 服务端口 | `8000` |
| `CHUNK_SIZE` | 文本块大小 | `500` |
| `CHUNK_OVERLAP` | 文本块重叠 | `50` |
| `CACHE_TTL` | 缓存过期时间(秒) | `3600` |

## 🔧 开发

### 运行测试

```bash
pytest tests/
```

### 代码格式化

```bash
black .
isort .
```

## 📝 许可证

MIT License

