# api/routers/chat.py
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from fastapi.responses import StreamingResponse
import time
import uuid
import json

from api.models import ChatRequest, ChatResponse
from api.services.vector_service import VectorService
from api.services.unified_llm_service import UnifiedLLMService
from api.services.cache_service import CacheService

router = APIRouter(prefix="/api/v1/chat", tags=["chat"])

# 依赖项
def get_vector_service():
    return VectorService()

def get_llm_service():
    return UnifiedLLMService()

def get_cache_service():
    return CacheService()

def build_context_from_results(search_results, max_sources: int = 3) -> str:
    """从检索结果构建上下文的辅助函数"""
    context_parts = []
    for i, result in enumerate(search_results[:max_sources]):
        context_parts.append(f"[来源{i+1}] {result['text']}")
    return "\n\n".join(context_parts)

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    vector_service: VectorService = Depends(get_vector_service),
    llm_service: UnifiedLLMService = Depends(get_llm_service),
    cache_service: CacheService = Depends(get_cache_service)
):
    """问答接口"""
    
    start_time = time.time()
    request_id = str(uuid.uuid4())
    
    try:
        # 1. 检查缓存
        if request.use_cache:
            cached_answer = cache_service.get_cached_answer(request.question)
            if cached_answer:
                return ChatResponse(
                    answer=cached_answer["answer"],
                    sources=cached_answer.get("sources", []),
                    cached=True,
                    processing_time=time.time() - start_time,
                    request_id=request_id
                )
        
        # 2. 向量检索
        search_results = vector_service.search(
            query=request.question,
            top_k=request.top_k
        )
        
        # 3. 构建上下文
        context = build_context_from_results(search_results, max_sources=3)
        
        if not context.strip():
            return ChatResponse(
                answer="抱歉,在知识库中没有找到相关信息。",
                sources=[],
                cached=False,
                processing_time=time.time() - start_time,
                request_id=request_id
            )
        
        # 4. 构建消息并调用LLM (统一使用generate方法)
        messages = llm_service.build_rag_messages(
            question=request.question,
            context=context
        )
        
        # 收集完整响应 (非流式)
        response_content = ""
        async for chunk in llm_service.generate(
            messages=messages,
            temperature=request.temperature,
            stream=False
        ):
            response_content += chunk
        
        # 5. 缓存结果
        if request.use_cache:
            answer_to_cache = {
                "answer": response_content,
                "sources": search_results,
                "question": request.question
            }
            
            # 后台任务缓存
            background_tasks.add_task(
                cache_service.cache_answer,
                request.question,
                answer_to_cache
            )
        
        # 6. 返回响应
        processing_time = time.time() - start_time
        
        return ChatResponse(
            answer=response_content,
            sources=search_results,
            cached=False,
            processing_time=processing_time,
            request_id=request_id
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"内部服务器错误: {str(e)}"
        )

@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    vector_service: VectorService = Depends(get_vector_service),
    llm_service: UnifiedLLMService = Depends(get_llm_service)
):
    """流式问答接口"""
    
    try:
        # 1. 向量检索
        search_results = vector_service.search(
            query=request.question,
            top_k=request.top_k
        )
        
        # 2. 构建上下文
        context = build_context_from_results(search_results, max_sources=3)
        
        if not context.strip():
            async def no_context_stream():
                yield f"data: {json.dumps({'content': '抱歉,在知识库中没有找到相关信息。', 'done': True})}\n\n"
            return StreamingResponse(no_context_stream(), media_type="text/event-stream")
        
        # 3. 流式调用LLM (统一使用generate方法)
        async def stream_generator():
            # 构建消息
            messages = llm_service.build_rag_messages(
                question=request.question,
                context=context
            )

            # 发送初始信息(包括来源和后端信息)
            initial_data = {
                "sources": [
                    {
                        "text": r["text"][:100] + "..." if len(r["text"]) > 100 else r["text"],
                        "score": r["score"],
                        "metadata": r["metadata"]
                    }
                    for r in search_results[:3]
                ],
                "backend": llm_service.current_backend.value,
                "model": llm_service.configs[llm_service.current_backend]["model"]
            }
            yield f"data: {json.dumps(initial_data)}\n\n"

            # 流式生成回答
            async for chunk in llm_service.generate(
                messages=messages,
                temperature=request.temperature,
                stream=True
            ):
                yield f"data: {json.dumps({'content': chunk})}\n\n"

            # 结束标记
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            stream_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
        
    except Exception as e:
        async def error_stream():
            error_data = {
                "error": True,
                "message": str(e)
            }
            yield f"data: {json.dumps(error_data)}\n\n"
        
        return StreamingResponse(error_stream(), media_type="text/event-stream")