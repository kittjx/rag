# config.py
import os
import sys
from dataclasses import dataclass
from pathlib import Path

@dataclass
class Config:
    """应用配置"""

    # 项目路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    DATA_DIR = os.path.join(BASE_DIR, "data")

    # 文档路径
    RAW_DOCS_DIR = os.path.join(DATA_DIR, "raw_documents")
    PROCESSED_DIR = os.path.join(DATA_DIR, "processed_chunks")
    VECTOR_STORE_DIR = os.path.join(DATA_DIR, "vector_store")

    # 模型配置
    # EMBEDDING_MODEL = "BAAI/bge-large-zh"
    # EMBEDDING_MODEL_PATH = os.path.join(BASE_DIR, "models", "bge-large-zh")
    EMBEDDING_MODEL = "BAAI/bge-m3"
    EMBEDDING_MODEL_PATH = os.path.join(BASE_DIR, "models", "bge-m3")
    SAVE_MODEL_AFTER_DOWNLOAD = True

    # 向量数据库配置
    VECTOR_DB_TYPE = "chroma"  # chroma/qdrant
    COLLECTION_NAME = "conscription"

    # 文本分割配置
    CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
    CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

    # LLM后端配置
    LLM_BACKEND = os.getenv("LLM_BACKEND", "auto")  # auto, deepseek, qwen, ollama, openai
    USE_LOCAL_LLM = os.getenv("USE_LOCAL_LLM", "false").lower() == "true"

    # DeepSeek API配置
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_BASE = os.getenv("DEEPSEEK_API_BASE", "https://api.deepseek.com/v1")
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")

    # Qwen API配置
    QWEN_API_KEY = os.getenv("QWEN_API_KEY", "")
    QWEN_API_BASE = os.getenv("QWEN_API_BASE", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    QWEN_MODEL = os.getenv("QWEN_MODEL", "qwen-turbo")

    # Ollama配置
    OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:4b")

    # API服务配置
    API_HOST = os.getenv("API_HOST", "0.0.0.0")
    API_PORT = int(os.getenv("API_PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "False").lower() in ("true", "1", "yes")

    # 缓存配置
    REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
    CACHE_TTL = int(os.getenv("CACHE_TTL", "259200"))  # 72小时

    @classmethod
    def validate(cls):
        """验证配置"""
        errors = []
        warnings = []

        # 检查必需的目录
        required_dirs = [cls.DATA_DIR, cls.RAW_DOCS_DIR, cls.PROCESSED_DIR, cls.VECTOR_STORE_DIR]
        for dir_path in required_dirs:
            if not os.path.exists(dir_path):
                warnings.append(f"目录不存在，将自动创建: {dir_path}")
                Path(dir_path).mkdir(parents=True, exist_ok=True)

        # 检查API密钥
        if not cls.DEEPSEEK_API_KEY and not cls.QWEN_API_KEY and not cls.OLLAMA_BASE_URL:
            warnings.append("DEEPSEEK_API_KEY/QWEN_API_KEY/OLLAMA_BASE_URL 未设置")

        # 检查向量数据库
        if not os.path.exists(cls.VECTOR_STORE_DIR) or not os.listdir(cls.VECTOR_STORE_DIR):
            warnings.append("向量数据库未初始化，请运行 build_knowledge_base.py")

        # 输出警告和错误
        if warnings:
            print("⚠️  配置警告:", file=sys.stderr)
            for warning in warnings:
                print(f"  - {warning}", file=sys.stderr)

        if errors:
            print("❌ 配置错误:", file=sys.stderr)
            for error in errors:
                print(f"  - {error}", file=sys.stderr)
            raise ValueError("配置验证失败")

        return True

config = Config()

# 自动验证配置（仅在非导入时）
if __name__ != "__main__":
    try:
        config.validate()
    except Exception as e:
        print(f"配置验证失败: {e}", file=sys.stderr)

