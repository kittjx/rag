# LLM后端切换功能实现总结

## 📋 实现概述

本次更新为系统添加了完整的多LLM后端支持，允许用户在DeepSeek、Qwen、OpenAI和Ollama之间灵活切换。

## 🎯 核心功能

### 1. 统一LLM服务 (`UnifiedLLMService`)

**文件**: `api/services/unified_llm_service.py`

#### 主要特性:
- ✅ 支持4种LLM后端: DeepSeek, Qwen, OpenAI, Ollama
- ✅ 自动检测可用后端
- ✅ 智能故障转移
- ✅ 统一的API接口
- ✅ 健康状态监控

#### 核心方法:

```python
class UnifiedLLMService:
    def __init__(self):
        # 自动检测最佳后端
        
    async def generate(messages, temperature, max_tokens, stream):
        # 统一生成接口
        
    async def generate_with_context(question, context, system_prompt):
        # RAG专用接口
        
    def switch_backend(backend):
        # 手动切换后端
        
    def auto_switch_on_failure():
        # 自动故障转移
        
    def get_backend_info():
        # 获取后端信息
```

### 2. 配置管理

**文件**: `config.py`

新增配置项:
```python
# LLM后端选择
LLM_BACKEND = "auto"  # auto, deepseek, qwen, openai, ollama
USE_LOCAL_LLM = False

# DeepSeek配置
DEEPSEEK_API_KEY = "..."
DEEPSEEK_API_BASE = "..."
DEEPSEEK_MODEL = "deepseek-chat"

# Qwen配置
QWEN_API_KEY = "..."
QWEN_API_BASE = "..."
QWEN_MODEL = "qwen-turbo"

# OpenAI配置
OPENAI_API_KEY = "..."
OPENAI_API_BASE = "..."
OPENAI_MODEL = "gpt-3.5-turbo"

# Ollama配置
OLLAMA_BASE_URL = "http://localhost:11434"
OLLAMA_MODEL = "qwen2.5:7b"
```

### 3. API端点

**文件**: `api/routers/system.py`

新增端点:

#### GET `/api/v1/system/version`
获取系统版本和当前LLM后端信息

响应:
```json
{
  "llm_backend": "deepseek",
  "llm_model": "deepseek-chat"
}
```

#### GET `/api/v1/system/llm/backends`
获取所有后端状态

响应:
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
    }
  ]
}
```

#### POST `/api/v1/system/llm/switch/{backend}`
动态切换LLM后端

请求:
```bash
curl -X POST http://localhost:8000/api/v1/system/llm/switch/qwen
```

响应:
```json
{
  "success": true,
  "message": "已切换到 qwen 后端",
  "current_backend": "qwen",
  "current_model": "qwen-turbo"
}
```

### 4. 路由更新

**文件**: `api/routers/chat.py`

- ✅ 使用 `UnifiedLLMService` 替代 `DeepSeekService`
- ✅ 保持向后兼容
- ✅ 响应中包含后端信息

## 📁 文件变更清单

### 新增文件
1. `api/services/unified_llm_service.py` - 统一LLM服务
2. `.env.example` - 环境变量示例
3. `LLM_BACKENDS.md` - LLM后端使用指南
4. `test_llm_backends.py` - LLM后端测试脚本
5. `LLM_BACKEND_IMPLEMENTATION.md` - 本文档

### 修改文件
1. `config.py` - 添加LLM后端配置
2. `api/routers/chat.py` - 使用UnifiedLLMService
3. `api/routers/system.py` - 添加LLM后端管理端点
4. `README.md` - 更新文档
5. `Makefile` - 添加test-llm命令

## 🔄 后端切换逻辑

### 自动检测优先级

```
1. 如果 USE_LOCAL_LLM=true
   → 使用 Ollama

2. 如果 LLM_BACKEND != "auto"
   → 使用指定后端

3. 自动检测:
   a. 检测到 DEEPSEEK_API_KEY → DeepSeek
   b. 检测到 QWEN_API_KEY → Qwen
   c. 检测到 OPENAI_API_KEY → OpenAI
   d. 默认 → Ollama
```

### 故障转移

```
当前后端调用失败
  ↓
检查其他可用后端
  ↓
切换到第一个可用后端
  ↓
继续服务
```

## 🧪 测试

### 运行测试

```bash
# 测试LLM后端
make test-llm

# 或直接运行
python test_llm_backends.py
```

### 测试内容

1. ✅ 版本信息获取
2. ✅ 后端状态查询
3. ✅ 后端切换
4. ✅ 问答功能

## 📊 架构图

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
├─────────────────────────────────────────┤
│                                         │
│  ┌───────────────────────────────────┐ │
│  │   UnifiedLLMService               │ │
│  ├───────────────────────────────────┤ │
│  │                                   │ │
│  │  ┌──────────┐  ┌──────────┐     │ │
│  │  │ DeepSeek │  │   Qwen   │     │ │
│  │  └──────────┘  └──────────┘     │ │
│  │                                   │ │
│  │  ┌──────────┐  ┌──────────┐     │ │
│  │  │  OpenAI  │  │  Ollama  │     │ │
│  │  └──────────┘  └──────────┘     │ │
│  │                                   │ │
│  │  • Auto Detection                │ │
│  │  • Health Check                  │ │
│  │  • Failover                      │ │
│  └───────────────────────────────────┘ │
│                                         │
└─────────────────────────────────────────┘
```

## 💡 使用示例

### 示例1: 使用DeepSeek

```bash
# .env
LLM_BACKEND=deepseek
DEEPSEEK_API_KEY=sk-xxxxx
```

### 示例2: 自动检测

```bash
# .env
LLM_BACKEND=auto
DEEPSEEK_API_KEY=sk-xxxxx
QWEN_API_KEY=sk-yyyyy
```

系统会优先使用DeepSeek

### 示例3: 本地Ollama

```bash
# .env
USE_LOCAL_LLM=true
OLLAMA_MODEL=qwen2.5:7b
```

### 示例4: 运行时切换

```bash
# 启动时使用DeepSeek
LLM_BACKEND=deepseek

# 运行时切换到Qwen
curl -X POST http://localhost:8000/api/v1/system/llm/switch/qwen
```

## 🎯 最佳实践

### 开发环境
```bash
USE_LOCAL_LLM=true
OLLAMA_MODEL=qwen2.5:7b
```
- 节省API费用
- 快速迭代

### 测试环境
```bash
LLM_BACKEND=auto
DEEPSEEK_API_KEY=sk-xxxxx
QWEN_API_KEY=sk-yyyyy
```
- 测试多后端兼容性
- 验证故障转移

### 生产环境
```bash
LLM_BACKEND=deepseek
DEEPSEEK_API_KEY=sk-xxxxx
QWEN_API_KEY=sk-yyyyy  # 备用
```
- 明确指定主后端
- 配置备用后端

## 🔍 故障排查

### 问题1: 后端不可用

```bash
# 检查后端状态
curl http://localhost:8000/api/v1/system/llm/backends

# 查看日志
tail -f logs/api.log
```

### 问题2: API Key错误

检查 `.env` 文件中的API Key是否正确

### 问题3: Ollama连接失败

```bash
# 检查Ollama是否运行
curl http://localhost:11434/api/tags

# 启动Ollama
ollama serve
```

## ✅ 完成清单

- [x] 实现UnifiedLLMService
- [x] 支持4种LLM后端
- [x] 自动检测和切换
- [x] 故障转移机制
- [x] API端点
- [x] 配置管理
- [x] 文档完善
- [x] 测试脚本
- [x] 更新README

## 📚 相关文档

- [LLM_BACKENDS.md](LLM_BACKENDS.md) - 详细使用指南
- [README.md](README.md) - 项目总览
- [IMPROVEMENTS.md](IMPROVEMENTS.md) - 改进历史

## 🎉 总结

本次实现为系统添加了完整的多LLM后端支持，具有以下优势:

1. **灵活性**: 支持4种主流LLM后端
2. **可靠性**: 自动故障转移
3. **易用性**: 自动检测和配置
4. **可扩展性**: 易于添加新后端
5. **向后兼容**: 不影响现有功能

用户现在可以根据需求自由选择和切换LLM后端，大大提升了系统的灵活性和可用性！

