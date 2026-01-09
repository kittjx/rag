# api/services/vector_service.py
from typing import List, Dict, Any, Optional
import chromadb
from sentence_transformers import SentenceTransformer
from config import config

class VectorService:
    """向量检索服务（单例模式）"""

    _instance = None
    _lock = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        try:
            # 加载嵌入模型
            print("正在加载嵌入模型...")
            self.embedding_model = SentenceTransformer(
                config.EMBEDDING_MODEL,
                cache_folder=config.EMBEDDING_MODEL_PATH,
                device='cpu'
            )
            print("嵌入模型加载完成")

            # 初始化向量数据库客户端
            print("正在连接向量数据库...")
            self.chroma_client = chromadb.PersistentClient(
                path=config.VECTOR_STORE_DIR,
                settings=chromadb.config.Settings(
                    anonymized_telemetry=False
                )
            )

            # 获取或创建集合
            try:
                self.collection = self.chroma_client.get_collection(
                    config.COLLECTION_NAME
                )
                print(f"已连接到集合: {config.COLLECTION_NAME}")
            except Exception:
                print(f"集合 {config.COLLECTION_NAME} 不存在，请先运行 build_knowledge_base.py")
                raise ValueError(f"向量数据库集合 '{config.COLLECTION_NAME}' 不存在")

            self._initialized = True

        except Exception as e:
            print(f"向量服务初始化失败: {e}")
            raise
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_conditions: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        
        # 生成查询向量
        query_embedding = self.embedding_model.encode(
            query, 
            normalize_embeddings=True
        ).tolist()
        
        # 执行搜索
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            where=filter_conditions,
            include=["documents", "metadatas", "distances"]
        )
        
        # 格式化结果
        formatted_results = []
        if results["documents"]:
            for i in range(len(results["documents"][0])):
                formatted_results.append({
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": 1 - results["distances"][0][i],  # 转换为相似度分数
                    "rank": i + 1
                })
        
        return formatted_results
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        try:
            count = self.collection.count()
            return {
                "total_chunks": count,
                "status": "healthy",
                "collection_name": config.COLLECTION_NAME
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }