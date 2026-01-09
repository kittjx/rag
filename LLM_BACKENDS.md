# LLM后端切换指南

## 🎯 概述

本系统支持多种LLM后端，可以轻松切换：
- **DeepSeek** - 高性价比的中文大模型
- **Qwen (通义千问)** - 阿里云的大模型服务
- **OpenAI** - GPT系列模型
- **Ollama** - 本地运行的开源模型

## 🔧 配置方法

### 1. 环境变量配置

编辑 `.env` 文件：

```bash
# 后端选择策略
LLM_BACKEND=auto          # auto, deepseek, qwen, openai, ollama
USE_LOCAL_LLM=false       # true优先使用本地Ollama

# DeepSeek配置
DEEPSEEK_API_KEY=sk-xxxxx
DEEPSEEK_MODEL=deepseek-chat

# Qwen配置
QWEN_API_KEY=sk-xxxxx
QWEN_MODEL=qwen-turbo

# OpenAI配置
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-3.5-turbo

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:7b
```

### 2. 自动检测模式 (推荐)

设置 `LLM_BACKEND=auto`，系统会按以下优先级自动选择：

1. 如果 `USE_LOCAL_LLM=true` → 使用 Ollama
2. 如果配置了 `DEEPSEEK_API_KEY` → 使用 DeepSeek
3. 如果配置了 `QWEN_API_KEY` → 使用 Qwen
4. 如果配置了 `OPENAI_API_KEY` → 使用 OpenAI
5. 默认 → 使用 Ollama (需要本地安装)

### 3. 手动指定后端

```bash
# 使用DeepSeek
LLM_BACKEND=deepseek

# 使用Qwen
LLM_BACKEND=qwen

# 使用OpenAI
LLM_BACKEND=openai

# 使用Ollama
LLM_BACKEND=ollama
```

## 📡 API接口

### 查看当前后端信息

```bash
curl http://localhost:8000/api/v1/system/version
```

响应：
```json
{
  "name": "Knowledge Base API",
  "version": "1.0.0",
  "components": {
    "llm_backend": "deepseek",
    "llm_model": "deepseek-chat"
  }
}
```

### 查看所有后端状态

```bash
curl http://localhost:8000/api/v1/system/llm/backends
```

响应：
```json
{
  "current_backend": "deepseek",
  "current_model": "deepseek-chat",
  "available_backends": [
    {
      "name": "deepseek",
      "model": "deepseek-chat",
      "healthy": true,
      "api_key_configured": true
    },
    {
      "name": "qwen",
      "model": "qwen-turbo",
      "healthy": false,
      "api_key_configured": false
    },
    {
      "name": "openai",
      "model": "gpt-3.5-turbo",
      "healthy": false,
      "api_key_configured": false
    },
    {
      "name": "ollama",
      "model": "qwen2.5:7b",
      "healthy": false,
      "api_key_configured": false
    }
  ]
}
```

### 动态切换后端

```bash
# 切换到Qwen
curl -X POST http://localhost:8000/api/v1/system/llm/switch/qwen

# 切换到Ollama
curl -X POST http://localhost:8000/api/v1/system/llm/switch/ollama
```

响应：
```json
{
  "success": true,
  "message": "已切换到 qwen 后端",
  "current_backend": "qwen",
  "current_model": "qwen-turbo"
}
```

## 🚀 各后端配置指南

### DeepSeek

1. 注册账号: https://platform.deepseek.com/
2. 获取API Key
3. 配置环境变量:
```bash
DEEPSEEK_API_KEY=sk-xxxxx
LLM_BACKEND=deepseek
```

**优点**: 性价比高，中文能力强
**价格**: 约 ¥1/百万tokens

### Qwen (通义千问)

1. 注册阿里云账号: https://dashscope.aliyun.com/
2. 开通DashScope服务
3. 获取API Key
4. 配置环境变量:
```bash
QWEN_API_KEY=sk-xxxxx
LLM_BACKEND=qwen
```

**优点**: 阿里云生态，稳定可靠
**价格**: 按调用量计费

### OpenAI

1. 注册OpenAI账号: https://platform.openai.com/
2. 获取API Key
3. 配置环境变量:
```bash
OPENAI_API_KEY=sk-xxxxx
OPENAI_MODEL=gpt-3.5-turbo  # 或 gpt-4
LLM_BACKEND=openai
```

**优点**: 能力最强，生态完善
**价格**: 较高，按token计费

### Ollama (本地模型)

1. 安装Ollama: https://ollama.ai/
```bash
# macOS
brew install ollama

# Linux
curl -fsSL https://ollama.ai/install.sh | sh
```

2. 下载模型:
```bash
ollama pull qwen2.5:7b
# 或其他模型
ollama pull llama3.1:8b
ollama pull mistral:7b
```

3. 启动Ollama服务:
```bash
ollama serve
```

4. 配置环境变量:
```bash
OLLAMA_MODEL=qwen2.5:7b
LLM_BACKEND=ollama
# 或
USE_LOCAL_LLM=true
```

**优点**: 完全本地，无需API费用，数据隐私
**缺点**: 需要本地GPU，推理速度较慢

## 🔄 自动故障切换

系统支持自动故障切换：

1. 当前后端调用失败时
2. 自动检测其他可用后端
3. 切换到备用后端继续服务

示例：DeepSeek API失败 → 自动切换到Ollama本地模型

## 💡 最佳实践

### 开发环境
```bash
USE_LOCAL_LLM=true
OLLAMA_MODEL=qwen2.5:7b
```
使用本地Ollama，节省API费用

### 生产环境
```bash
LLM_BACKEND=auto
DEEPSEEK_API_KEY=sk-xxxxx
QWEN_API_KEY=sk-xxxxx
```
配置多个后端，自动故障切换

### 高性能需求
```bash
LLM_BACKEND=openai
OPENAI_MODEL=gpt-4
```
使用最强模型

### 成本优化
```bash
LLM_BACKEND=deepseek
DEEPSEEK_MODEL=deepseek-chat
```
使用高性价比模型

## 🧪 测试后端

```bash
# 测试问答
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{
    "question": "你好，请介绍一下自己",
    "top_k": 3
  }'
```

响应会包含使用的后端信息：
```json
{
  "answer": "...",
  "backend": "deepseek",
  "model": "deepseek-chat"
}
```

## 📊 性能对比

| 后端 | 速度 | 成本 | 中文能力 | 部署难度 |
|------|------|------|----------|----------|
| DeepSeek | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Qwen | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| OpenAI | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| Ollama | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## 🔍 故障排查

### 后端不可用

```bash
# 检查后端状态
curl http://localhost:8000/api/v1/system/llm/backends

# 查看日志
tail -f logs/api.log
```

### API Key错误

检查 `.env` 文件中的API Key是否正确

### Ollama连接失败

```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 启动Ollama
ollama serve
```

## 📚 相关文档

- [DeepSeek文档](https://platform.deepseek.com/docs)
- [Qwen文档](https://help.aliyun.com/zh/dashscope/)
- [OpenAI文档](https://platform.openai.com/docs)
- [Ollama文档](https://github.com/ollama/ollama)

