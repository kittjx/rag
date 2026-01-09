# api/routers/documents.py
from fastapi import APIRouter, Depends, HTTPException

from api.models import DocumentSearchRequest, DocumentSearchResponse
from api.services.vector_service import VectorService

router = APIRouter(prefix="/api/v1/documents", tags=["documents"])

# 依赖项
def get_vector_service():
    return VectorService()

@router.post("/search", response_model=DocumentSearchResponse)
async def search_documents(
    request: DocumentSearchRequest,
    vector_service: VectorService = Depends(get_vector_service)
):
    """搜索文档"""
    
    import time
    start_time = time.time()
    
    try:
        # 构建过滤条件
        filter_conditions = None
        if request.filter_by_source or request.filter_by_type:
            filter_conditions = {}
            
            if request.filter_by_source:
                filter_conditions["source"] = {"$contains": request.filter_by_source}
            
            if request.filter_by_type:
                filter_conditions["file_type"] = {"$eq": request.filter_by_type}
        
        # 执行搜索
        results = vector_service.search(
            query=request.query,
            top_k=request.top_k,
            filter_conditions=filter_conditions
        )
        
        processing_time = time.time() - start_time
        
        return DocumentSearchResponse(
            results=results,
            total=len(results),
            query=request.query,
            processing_time=processing_time
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"搜索失败: {str(e)}"
        )

@router.get("/stats")
async def get_document_stats(
    vector_service: VectorService = Depends(get_vector_service)
):
    """获取文档统计信息"""
    
    try:
        stats = vector_service.get_stats()
        
        if "error" in stats:
            raise HTTPException(status_code=500, detail=stats["error"])
        
        return stats
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )