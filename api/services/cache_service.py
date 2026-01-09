# api/services/cache_service.py
import redis
import json
import hashlib
from typing import Optional, Any, Dict
from datetime import timedelta
from config import config

class CacheService:
    """缓存服务"""
    
    def __init__(self):
        try:
            self.client = redis.Redis.from_url(
                config.REDIS_URL,
                decode_responses=True,
                socket_timeout=5,
                socket_connect_timeout=5
            )
            # 测试连接
            self.client.ping()
            self.available = True
        except:
            self.available = False
    
    def _make_key(self, prefix: str, query: str) -> str:
        """生成缓存键"""
        query_hash = hashlib.md5(query.encode()).hexdigest()
        return f"{prefix}:{query_hash}"
    
    def get(self, key: str) -> Optional[Any]:
        """获取缓存"""
        if not self.available:
            return None
        
        try:
            value = self.client.get(key)
            if value:
                return json.loads(value)
        except:
            pass
        return None
    
    def set(self, key: str, value: Any, ttl: int = None):
        """设置缓存"""
        if not self.available:
            return
        
        try:
            if ttl is None:
                ttl = config.CACHE_TTL
            
            self.client.setex(
                key,
                timedelta(seconds=ttl),
                json.dumps(value)
            )
        except:
            pass
    
    def get_cached_answer(self, question: str) -> Optional[Dict]:
        """获取缓存的回答"""
        key = self._make_key("answer", question)
        return self.get(key)
    
    def cache_answer(self, question: str, answer: Dict, ttl: int = None):
        """缓存回答"""
        key = self._make_key("answer", question)
        self.set(key, answer, ttl)
    
    def clear_cache(self, pattern: str = "*") -> int:
        """清除缓存"""
        if not self.available:
            return 0
        
        try:
            keys = self.client.keys(pattern)
            if keys:
                return self.client.delete(*keys)
        except:
            pass
        return 0