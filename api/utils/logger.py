# api/utils/logger.py
import logging
import sys
from pathlib import Path
from config import config

def setup_logger():
    """配置日志"""
    
    # 创建日志目录
    log_dir = Path(config.BASE_DIR) / "logs"
    log_dir.mkdir(exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 根日志配置
    logger = logging.getLogger()
    logger.setLevel(logging.INFO if not config.DEBUG else logging.DEBUG)
    
    # 清除已有处理器
    logger.handlers.clear()
    
    # 控制台处理器
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(console_handler)
    
    # 文件处理器
    file_handler = logging.FileHandler(
        log_dir / "api.log",
        encoding="utf-8"
    )
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(file_handler)
    
    # 错误日志单独文件
    error_handler = logging.FileHandler(
        log_dir / "error.log",
        encoding="utf-8"
    )
    error_handler.setLevel(logging.ERROR)
    error_handler.setFormatter(logging.Formatter(log_format, date_format))
    logger.addHandler(error_handler)
    
    # 设置第三方库的日志级别
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("chromadb").setLevel(logging.WARNING)
    
    return logger
