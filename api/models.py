# api/models.py
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

class ChatRequest(BaseModel):
    """聊天请求"""
    question: str = Field(..., description="用户问题", min_length=1, max_length=2000)
    top_k: Optional[int] = Field(5, ge=1, le=20, description="检索文档数量")
    temperature: Optional[float] = Field(0.1, ge=0.0, le=2.0, description="温度参数")
    stream: Optional[bool] = Field(False, description="是否流式输出")
    session_id: Optional[str] = Field(None, description="会话ID")
    use_cache: Optional[bool] = Field(True, description="是否使用缓存")

class ChatResponse(BaseModel):
    """聊天响应"""
    answer: str = Field(..., description="AI回答")
    sources: List[Dict[str, Any]] = Field([], description="参考来源")
    cached: bool = Field(False, description="是否来自缓存")
    usage: Optional[Dict[str, Any]] = Field(None, description="API使用情况")
    processing_time: Optional[float] = Field(None, description="处理时间（秒）")
    request_id: Optional[str] = Field(None, description="请求ID")

class DocumentSearchRequest(BaseModel):
    """文档搜索请求"""
    query: str = Field(..., description="搜索查询")
    top_k: Optional[int] = Field(5, ge=1, le=50, description="返回结果数量")
    filter_by_source: Optional[str] = Field(None, description="按来源过滤")
    filter_by_type: Optional[str] = Field(None, description="按文件类型过滤")

class DocumentSearchResponse(BaseModel):
    """文档搜索响应"""
    results: List[Dict[str, Any]] = Field(..., description="搜索结果")
    total: int = Field(..., description="总结果数")
    query: str = Field(..., description="原始查询")
    processing_time: float = Field(..., description="处理时间")

class SystemHealthResponse(BaseModel):
    """系统健康状态响应"""
    status: str = Field(..., description="状态: healthy/unhealthy")
    timestamp: datetime = Field(..., description="检查时间")
    components: Dict[str, Dict[str, Any]] = Field(..., description="组件状态")
    uptime: float = Field(..., description="运行时间（秒）")

class ErrorResponse(BaseModel):
    """错误响应"""
    error: bool = Field(True, description="是否错误")
    message: str = Field(..., description="错误信息")
    code: Optional[str] = Field(None, description="错误代码")
    details: Optional[Dict[str, Any]] = Field(None, description="详细信息")