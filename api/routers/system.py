# api/routers/system.py
from fastapi import APIRouter, Depends
import time
from datetime import datetime
from typing import Dict, Any

from api.models import SystemHealthResponse
from api.services.vector_service import VectorService
from api.services.cache_service import CacheService
from api.services.unified_llm_service import UnifiedLLMService

router = APIRouter(prefix="/api/v1/system", tags=["system"])

# 启动时间
START_TIME = time.time()

# 依赖项
def get_vector_service():
    return VectorService()

def get_cache_service():
    return CacheService()

def get_llm_service():
    return UnifiedLLMService()

@router.get("/health", response_model=SystemHealthResponse)
async def health_check(
    vector_service: VectorService = Depends(get_vector_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """系统健康检查"""
    
    components = {}
    
    # 检查向量数据库
    try:
        vector_stats = vector_service.get_stats()
        components["vector_db"] = {
            "status": "healthy" if "error" not in vector_stats else "unhealthy",
            "details": vector_stats
        }
    except Exception as e:
        components["vector_db"] = {
            "status": "unhealthy",
            "error": str(e)
        }
    
    # 检查缓存服务
    components["cache"] = {
        "status": "healthy" if cache_service.available else "unhealthy",
        "available": cache_service.available
    }
    
    # 检查系统资源
    try:
        import psutil
        components["system"] = {
            "cpu_percent": psutil.cpu_percent(),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent
        }
    except ImportError:
        components["system"] = {
            "status": "unavailable",
            "message": "psutil not installed"
        }
    
    # 确定总体状态
    all_healthy = all(
        comp["status"] == "healthy" 
        for comp in components.values() 
        if "status" in comp
    )
    
    return SystemHealthResponse(
        status="healthy" if all_healthy else "unhealthy",
        timestamp=datetime.now(),
        components=components,
        uptime=time.time() - START_TIME
    )

@router.get("/version")
async def get_version(
    llm_service: UnifiedLLMService = Depends(get_llm_service)
):
    """获取版本信息"""
    backend_info = llm_service.get_backend_info()

    return {
        "name": "Knowledge Base API",
        "version": "1.0.0",
        "description": "基于RAG的知识库问答系统",
        "components": {
            "embedding": "BGE-m3",
            "vector_db": "ChromaDB",
            "llm_backend": backend_info["current_backend"],
            "llm_model": backend_info["current_model"],
            "api_framework": "FastAPI"
        }
    }

@router.get("/llm/backends", response_model=Dict[str, Any])
async def get_llm_backends(
    llm_service: UnifiedLLMService = Depends(get_llm_service)
):
    """获取所有LLM后端信息"""
    return llm_service.get_backend_info()

@router.post("/llm/switch/{backend}")
async def switch_llm_backend(
    backend: str,
    llm_service: UnifiedLLMService = Depends(get_llm_service)
):
    """切换LLM后端"""
    from api.services.unified_llm_service import LLMBackend

    try:
        backend_enum = LLMBackend(backend.lower())
        success = llm_service.switch_backend(backend_enum)

        if success:
            return {
                "success": True,
                "message": f"已切换到 {backend} 后端",
                "current_backend": llm_service.current_backend.value,
                "current_model": llm_service.configs[llm_service.current_backend]["model"]
            }
        else:
            return {
                "success": False,
                "message": f"{backend} 后端不可用或未配置",
                "current_backend": llm_service.current_backend.value
            }
    except ValueError:
        return {
            "success": False,
            "message": f"未知的后端: {backend}，可选值: deepseek, qwen, ollama"
        }