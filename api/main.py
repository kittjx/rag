# api/main.py
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from contextlib import asynccontextmanager
import time

from api.routers import chat, documents, system
from api.utils.logger import setup_logger

# 配置日志
logger = setup_logger()

# 应用生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时
    logger.info("应用启动中...")
    
    # 初始化服务等...
    
    yield
    
    # 关闭时
    logger.info("应用关闭中...")

# 创建FastAPI应用
app = FastAPI(
    title="知识库问答系统API",
    description="基于RAG的知识库问答系统，使用BGE向量化和DeepSeek API",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

# 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 生产环境应限制
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(GZipMiddleware, minimum_size=1000)

# 异常处理
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_request: Request, exc: RequestValidationError):
    """请求验证异常处理"""
    logger.warning(f"请求验证失败: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": True,
            "message": "请求参数验证失败",
            "details": exc.errors()
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(_request: Request, exc: Exception):
    """通用异常处理"""
    logger.error(f"服务器错误: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": True,
            "message": "服务器内部错误",
            "details": str(exc)
        }
    )

# 请求日志中间件
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """记录请求日志"""
    start_time = time.time()
    
    # 跳过健康检查的详细日志
    if request.url.path == "/api/v1/system/health":
        response = await call_next(request)
        return response
    
    request_id = request.headers.get("X-Request-ID", "unknown")
    client_ip = request.client.host if request.client else "unknown"
    
    logger.info(f"请求开始: {request.method} {request.url.path} - IP: {client_ip} - ID: {request_id}")
    
    try:
        response = await call_next(request)
        process_time = time.time() - start_time
        
        logger.info(f"请求完成: {request.method} {request.url.path} - 状态: {response.status_code} - 耗时: {process_time:.3f}s")
        
        # 添加响应头
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        return response
        
    except Exception as e:
        process_time = time.time() - start_time
        logger.error(f"请求失败: {request.method} {request.url.path} - 错误: {str(e)} - 耗时: {process_time:.3f}s")
        raise

# 注册路由
app.include_router(chat.router)
app.include_router(documents.router)
app.include_router(system.router)

# 根路由
@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "知识库问答系统API",
        "docs": "/api/docs",
        "version": "1.0.0"
    }

@app.get("/health")
async def simple_health():
    """简易健康检查（用于负载均衡）"""
    return {"status": "healthy", "timestamp": time.time()}