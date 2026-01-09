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
        context_parts = []
        for i, result in enumerate(search_results[:3]):  # 取前3个最相关的
            context_parts.append(f"[来源{i+1}] {result['text']}")
        
        context = "\n\n".join(context_parts)
        
        if not context.strip():
            return ChatResponse(
                answer="抱歉，在知识库中没有找到相关信息。",
                sources=[],
                cached=False,
                processing_time=time.time() - start_time,
                request_id=request_id
            )
        
        # 4. 调用DeepSeek API
        llm_response = await llm_service.generate_with_context(
            question=request.question,
            context=context
        )
        
        if llm_response.get("error"):
            raise HTTPException(
                status_code=500,
                detail=f"AI服务错误: {llm_response['message']}"
            )
        
        # 5. 缓存结果
        if request.use_cache:
            answer_to_cache = {
                "answer": llm_response["content"],
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
            answer=llm_response["content"],
            sources=search_results,
            cached=False,
            usage=llm_response.get("usage"),
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
        context_parts = []
        for i, result in enumerate(search_results[:3]):
            context_parts.append(f"[来源{i+1}] {result['text']}")
        
        context = "\n\n".join(context_parts)
        
        if not context.strip():
            async def no_context_stream():
                yield f"data: {json.dumps({'content': '抱歉，在知识库中没有找到相关信息。', 'done': True})}\n\n"
            return StreamingResponse(no_context_stream(), media_type="text/event-stream")
        
        # 3. 流式调用DeepSeek API
        async def stream_generator():
            messages = [
                {
                    "role": "system",
                    "content": f"""基于以下参考信息回答问题：

参考信息：
{context}

要求：
1. 只基于参考信息回答
2. 如果参考信息中没有，请说"根据提供的信息，无法回答这个问题"
3. 回答要简洁明了"""
                },
                {
                    "role": "user",
                    "content": request.question
                }
            ]

            # 发送初始信息（包含来源和后端信息）
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