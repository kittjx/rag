# api/services/vector_service.py
from typing import List, Dict, Any, Optional
import torch
import numpy as np
import chromadb
from transformers import AutoTokenizer, AutoModel
from config import config
import os

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
            # 确定是否使用本地模型
            use_local = os.path.exists(config.EMBEDDING_MODEL_PATH)
            
            # 加载嵌入模型
            print("正在加载嵌入模型...")
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
            print(f"使用设备: {self.device}")
            
            if use_local:
                print(f"从本地加载模型: {config.EMBEDDING_MODEL_PATH}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    config.EMBEDDING_MODEL_PATH,
                    local_files_only=True
                )
                
                self.embedding_model = AutoModel.from_pretrained(
                    config.EMBEDDING_MODEL_PATH,
                    local_files_only=True
                ).to(self.device)
            else:
                print(f"从HuggingFace在线加载模型: {config.EMBEDDING_MODEL}")
                
                self.tokenizer = AutoTokenizer.from_pretrained(
                    config.EMBEDDING_MODEL
                )
                
                self.embedding_model = AutoModel.from_pretrained(
                    config.EMBEDDING_MODEL
                ).to(self.device)
            
            self.embedding_model.eval()
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
    
    def encode_text(self, text: str) -> np.ndarray:
        """将单个文本编码为向量"""
        with torch.no_grad():
            # Tokenize
            encoded = self.tokenizer(
                text,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            ).to(self.device)
            
            # Get embeddings
            outputs = self.embedding_model(**encoded)
            
            # Use CLS token embedding (first token)
            embedding = outputs.last_hidden_state[:, 0]
            
            # Normalize embedding
            embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
            
            return embedding.cpu().numpy()[0]
    
    def encode_texts(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """批量将文本编码为向量"""
        all_embeddings = []
        
        with torch.no_grad():
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                
                # Tokenize
                encoded = self.tokenizer(
                    batch_texts,
                    padding=True,
                    truncation=True,
                    max_length=512,
                    return_tensors='pt'
                ).to(self.device)
                
                # Get embeddings
                outputs = self.embedding_model(**encoded)
                
                # Use CLS token embedding (first token)
                embeddings = outputs.last_hidden_state[:, 0]
                
                # Normalize embeddings
                embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)
                
                all_embeddings.append(embeddings.cpu().numpy())
        
        return np.vstack(all_embeddings)
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_conditions: Optional[Dict] = None
    ) -> List[Dict[str, Any]]:
        """搜索相关文档"""
        
        # 生成查询向量
        query_embedding = self.encode_text(query).tolist()
        
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
                "collection_name": config.COLLECTION_NAME,
                "device": str(self.device)
            }
        except Exception as e:
            return {
                "error": str(e),
                "status": "error"
            }