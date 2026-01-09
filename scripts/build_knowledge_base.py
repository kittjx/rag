# scripts/build_knowledge_base.py
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import config
import hashlib
import json
from typing import List, Dict, Any
from datetime import datetime

# 文本处理模块
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader, TextLoader

# 向量化模块
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    print("错误: 缺少 sentence-transformers 包")
    print("请运行: pip install sentence-transformers")
    sys.exit(1)

try:
    import chromadb
    from chromadb.config import Settings
except ImportError:
    print("错误: 缺少 chromadb 包")
    print("请运行: pip install chromadb")
    sys.exit(1)

class KnowledgeBaseBuilder:
    """知识库构建器"""
    
    def __init__(self):
        self.config = config
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=config.CHUNK_SIZE,
            chunk_overlap=config.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "？", "！", "；", "，", " ", ""],
            length_function=len,
            add_start_index=True
        )
        
        # 初始化嵌入模型
        print("正在加载BGE嵌入模型...")
        self.embedding_model = SentenceTransformer(
            config.EMBEDDING_MODEL,
            cache_folder=config.EMBEDDING_MODEL_PATH
        )
        
        # 初始化向量数据库
        self.init_vector_store()
        
    def init_vector_store(self):
        """初始化向量数据库"""
        print("初始化向量数据库...")
        
        if self.config.VECTOR_DB_TYPE == "chroma":
            self.chroma_client = chromadb.PersistentClient(
                path=self.config.VECTOR_STORE_DIR,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True
                )
            )
            
            # 创建或获取集合
            try:
                self.collection = self.chroma_client.get_collection(
                    self.config.COLLECTION_NAME
                )
                print(f"使用现有集合: {self.config.COLLECTION_NAME}")
            except:
                self.collection = self.chroma_client.create_collection(
                    name=self.config.COLLECTION_NAME,
                    metadata={"description": "公司知识库", "created_at": datetime.now().isoformat()}
                )
                print(f"创建新集合: {self.config.COLLECTION_NAME}")
    
    def load_documents(self, directory: str) -> List[Dict[str, Any]]:
        """加载所有文档"""
        print(f"正在从 {directory} 加载文档...")
        
        supported_extensions = {
            '.pdf': PyPDFLoader,
            '.docx': Docx2txtLoader,
            '.doc': Docx2txtLoader,
            '.txt': TextLoader,
            '.md': TextLoader,
        }
        
        documents = []
        
        for root, _, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in supported_extensions:
                    try:
                        print(f"处理文件: {file_path}")
                        
                        if file_ext == '.pdf':
                            loader = PyPDFLoader(file_path)
                            file_docs = loader.load()
                        elif file_ext in ['.docx', '.doc']:
                            loader = Docx2txtLoader(file_path)
                            file_docs = loader.load()
                        else:
                            loader = TextLoader(file_path, encoding='utf-8')
                            file_docs = loader.load()
                        
                        # 添加元数据
                        for doc in file_docs:
                            doc.metadata.update({
                                "source": file_path,
                                "filename": file,
                                "file_type": file_ext[1:],  # 去掉点
                                "directory": root,
                                "processed_at": datetime.now().isoformat()
                            })
                        
                        documents.extend(file_docs)
                        
                    except Exception as e:
                        print(f"处理文件 {file_path} 时出错: {str(e)}")
                        continue
        
        print(f"共加载 {len(documents)} 个文档")
        return documents
    
    def chunk_documents(self, documents: List[Dict]) -> List[Dict]:
        """分割文档为文本块"""
        print("正在分割文档...")
        
        all_chunks = []
        
        for doc in documents:
            text = doc.page_content
            metadata = doc.metadata
            
            # 分割文本
            chunks = self.text_splitter.split_text(text)
            
            for i, chunk in enumerate(chunks):
                chunk_id = hashlib.md5(f"{metadata['source']}_{i}".encode()).hexdigest()[:16]
                
                chunk_metadata = metadata.copy()
                chunk_metadata.update({
                    "chunk_id": chunk_id,
                    "chunk_index": i,
                    "total_chunks": len(chunks),
                    "chunk_size": len(chunk)
                })
                
                all_chunks.append({
                    "id": chunk_id,
                    "text": chunk,
                    "metadata": chunk_metadata
                })
        
        print(f"分割为 {len(all_chunks)} 个文本块")
        return all_chunks
    
    def generate_embeddings(self, chunks: List[Dict]) -> List[List[float]]:
        """生成文本嵌入向量"""
        print("正在生成嵌入向量...")
        
        texts = [chunk["text"] for chunk in chunks]
        
        # 批量生成嵌入
        embeddings = self.embedding_model.encode(
            texts,
            batch_size=32,
            show_progress_bar=True,
            normalize_embeddings=True,
            convert_to_numpy=True
        )
        
        return embeddings.tolist()
    
    def store_to_vector_db(self, chunks: List[Dict], embeddings: List[List[float]]):
        """存储到向量数据库"""
        print("正在存储到向量数据库...")
        
        if self.config.VECTOR_DB_TYPE == "chroma":
            # 准备数据
            ids = [chunk["id"] for chunk in chunks]
            documents = [chunk["text"] for chunk in chunks]
            metadatas = [chunk["metadata"] for chunk in chunks]
            
            # 分批存储，避免内存问题
            batch_size = 100
            for i in range(0, len(ids), batch_size):
                end_idx = min(i + batch_size, len(ids))
                
                self.collection.add(
                    ids=ids[i:end_idx],
                    embeddings=embeddings[i:end_idx],
                    documents=documents[i:end_idx],
                    metadatas=metadatas[i:end_idx]
                )
                
                print(f"已存储 {end_idx}/{len(ids)} 个文本块")
        
        print("向量数据库存储完成！")
    
    def save_chunks_info(self, chunks: List[Dict]):
        """保存文本块信息到文件"""
        print("正在保存文本块信息...")
        
        chunks_info = []
        for chunk in chunks:
            chunks_info.append({
                "id": chunk["id"],
                "text_preview": chunk["text"][:100] + "...",
                "metadata": chunk["metadata"]
            })
        
        info_file = os.path.join(self.config.PROCESSED_DIR, "chunks_info.json")
        with open(info_file, 'w', encoding='utf-8') as f:
            json.dump(chunks_info, f, ensure_ascii=False, indent=2)
        
        stats_file = os.path.join(self.config.PROCESSED_DIR, "stats.json")
        stats = {
            "total_chunks": len(chunks),
            "total_documents": len(set(chunk["metadata"]["source"] for chunk in chunks)),
            "avg_chunk_size": sum(len(chunk["text"]) for chunk in chunks) / len(chunks),
            "built_at": datetime.now().isoformat(),
            "embedding_model": self.config.EMBEDDING_MODEL,
            "chunk_size": self.config.CHUNK_SIZE,
            "chunk_overlap": self.config.CHUNK_OVERLAP
        }
        
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)
        
        print(f"统计信息已保存到 {stats_file}")
    
    def build(self, rebuild: bool = False):
        """构建知识库"""
        print("开始构建知识库...")
        start_time = datetime.now()
        
        if rebuild and self.config.VECTOR_DB_TYPE == "chroma":
            print("重置向量数据库...")
            try:
                self.chroma_client.delete_collection(self.config.COLLECTION_NAME)
            except:
                pass
            self.init_vector_store()
        
        # 确保目录存在
        os.makedirs(self.config.RAW_DOCS_DIR, exist_ok=True)
        os.makedirs(self.config.PROCESSED_DIR, exist_ok=True)
        os.makedirs(self.config.VECTOR_STORE_DIR, exist_ok=True)
        
        # 构建流程
        documents = self.load_documents(self.config.RAW_DOCS_DIR)
        
        if not documents:
            print("未找到任何文档！请将文档放置在 data/raw_documents/ 目录下")
            return
        
        chunks = self.chunk_documents(documents)
        embeddings = self.generate_embeddings(chunks)
        self.store_to_vector_db(chunks, embeddings)
        self.save_chunks_info(chunks)
        
        elapsed = (datetime.now() - start_time).total_seconds()
        print(f"知识库构建完成！耗时: {elapsed:.2f}秒")

if __name__ == "__main__":
    builder = KnowledgeBaseBuilder()
    builder.build(rebuild=True)  # 设置为False可增量添加文档