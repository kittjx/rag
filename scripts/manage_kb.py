#!/usr/bin/env python3
"""
知识库管理工具
提供知识库的查看、清理、重建等功能
"""

import os
import sys
import json
import argparse
import warnings
from pathlib import Path

# 添加项目根目录到路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

os.environ['HF_HUB_OFFLINE'] = '1'
os.environ['TRANSFORMERS_OFFLINE'] = '1'
os.environ['HF_DATASETS_OFFLINE'] = '1'
os.environ['DISABLE_TELEMETRY'] = 'True'

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from config import config
import chromadb

def show_stats():
    """显示知识库统计信息"""
    print("📊 知识库统计信息")
    print("=" * 50)
    
    # 检查向量数据库
    try:
        client = chromadb.PersistentClient(path=config.VECTOR_STORE_DIR)
        collection = client.get_collection(config.COLLECTION_NAME)
        count = collection.count()
        
        print(f"✅ 向量数据库: 已连接")
        print(f"   集合名称: {config.COLLECTION_NAME}")
        print(f"   文档块数量: {count}")
        
    except Exception as e:
        print(f"❌ 向量数据库: 未初始化或错误")
        print(f"   错误: {e}")
    
    # 检查处理后的文件
    stats_file = Path(config.PROCESSED_DIR) / "stats.json"
    if stats_file.exists():
        with open(stats_file, 'r', encoding='utf-8') as f:
            stats = json.load(f)
        
        print(f"\n📄 处理统计:")
        print(f"   总文档数: {stats.get('total_documents', 0)}")
        print(f"   总文本块: {stats.get('total_chunks', 0)}")
        print(f"   平均块大小: {stats.get('avg_chunk_size', 0):.0f} 字符")
        print(f"   构建时间: {stats.get('built_at', 'N/A')}")
        print(f"   嵌入模型: {stats.get('embedding_model', 'N/A')}")
    
    # 检查原始文档
    raw_docs_dir = Path(config.RAW_DOCS_DIR)
    if raw_docs_dir.exists():
        doc_files = list(raw_docs_dir.rglob("*"))
        doc_files = [f for f in doc_files if f.is_file()]
        
        print(f"\n📁 原始文档:")
        print(f"   文件数量: {len(doc_files)}")
        
        # 按类型统计
        extensions = {}
        for f in doc_files:
            ext = f.suffix.lower()
            extensions[ext] = extensions.get(ext, 0) + 1
        
        for ext, count in sorted(extensions.items()):
            print(f"   {ext or '(无扩展名)'}: {count} 个")

def list_documents():
    """列出所有文档"""
    print("📚 文档列表")
    print("=" * 50)
    
    chunks_info_file = Path(config.PROCESSED_DIR) / "chunks_info.json"
    if not chunks_info_file.exists():
        print("❌ 未找到文档信息文件")
        return
    
    with open(chunks_info_file, 'r', encoding='utf-8') as f:
        chunks = json.load(f)
    
    # 按来源分组
    sources = {}
    for chunk in chunks:
        source = chunk['metadata'].get('source', 'unknown')
        if source not in sources:
            sources[source] = []
        sources[source].append(chunk)
    
    print(f"共 {len(sources)} 个文档:\n")
    
    for i, (source, doc_chunks) in enumerate(sorted(sources.items()), 1):
        filename = Path(source).name
        print(f"{i}. {filename}")
        print(f"   路径: {source}")
        print(f"   文本块数: {len(doc_chunks)}")
        print(f"   类型: {doc_chunks[0]['metadata'].get('file_type', 'unknown')}")
        print()

def clear_knowledge_base():
    """清空知识库"""
    print("🗑️  清空知识库")
    print("=" * 50)
    
    confirm = input("⚠️  确定要清空知识库吗？此操作不可恢复！(yes/no): ")
    if confirm.lower() != 'yes':
        print("❌ 操作已取消")
        return
    
    try:
        # 删除向量数据库
        client = chromadb.PersistentClient(path=config.VECTOR_STORE_DIR)
        try:
            client.delete_collection(config.COLLECTION_NAME)
            print("✅ 向量数据库已清空")
        except:
            print("⚠️  向量数据库集合不存在")
        
        # 清空处理后的文件
        processed_dir = Path(config.PROCESSED_DIR)
        if processed_dir.exists():
            for file in processed_dir.glob("*"):
                if file.is_file():
                    file.unlink()
            print("✅ 处理文件已清空")
        
        print("\n✅ 知识库已清空，请重新运行 build_knowledge_base.py 构建")
        
    except Exception as e:
        print(f"❌ 清空失败: {e}")

def search_test(query: str, top_k: int = 5):
    """测试搜索功能"""
    print(f"🔍 搜索测试: {query}")
    print("=" * 50)
    
    try:
        import torch
        import numpy as np
        from transformers import AutoTokenizer, AutoModel
        
        # 确定是否使用本地模型
        use_local = os.path.exists(config.EMBEDDING_MODEL_PATH)
        
        # 加载模型
        print("加载嵌入模型...")
        device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"使用设备: {device}")
        
        if use_local:
            print(f"从本地加载: {config.EMBEDDING_MODEL_PATH}")
            
            # Suppress the incorrect Mistral regex warning
            with warnings.catch_warnings():
                warnings.filterwarnings('ignore', message='.*fix_mistral_regex.*')
                
                tokenizer = AutoTokenizer.from_pretrained(
                    config.EMBEDDING_MODEL_PATH,
                    local_files_only=True
                )
            
            model = AutoModel.from_pretrained(
                config.EMBEDDING_MODEL_PATH,
                local_files_only=True
            ).to(device)
        else:
            print(f"从在线加载: {config.EMBEDDING_MODEL}")
            
            tokenizer = AutoTokenizer.from_pretrained(
                config.EMBEDDING_MODEL
            )
            
            model = AutoModel.from_pretrained(
                config.EMBEDDING_MODEL
            ).to(device)
        
        model.eval()
        print("模型加载完成")
        
        # 连接数据库
        print("连接向量数据库...")
        client = chromadb.PersistentClient(path=config.VECTOR_STORE_DIR)
        collection = client.get_collection(config.COLLECTION_NAME)
        
        # 生成查询向量
        print("生成查询向量...")
        with torch.no_grad():
            encoded = tokenizer(
                query,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors='pt'
            ).to(device)
            
            outputs = model(**encoded)
            
            # Use CLS token embedding
            embedding = outputs.last_hidden_state[:, 0]
            
            # Normalize
            embedding = torch.nn.functional.normalize(embedding, p=2, dim=1)
            
            query_embedding = embedding.cpu().numpy()[0].tolist()
        
        # 搜索
        print("执行搜索...")
        results = collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        print(f"\n找到 {len(results['documents'][0])} 个结果:\n")
        
        for i, (doc, metadata, distance) in enumerate(zip(
            results['documents'][0],
            results['metadatas'][0],
            results['distances'][0]
        ), 1):
            score = 1 - distance
            print(f"{i}. 相似度: {score:.4f}")
            print(f"   来源: {Path(metadata.get('source', '')).name}")
            print(f"   内容: {doc[:100]}...")
            print()
        
    except Exception as e:
        print(f"❌ 搜索失败: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description="知识库管理工具")
    parser.add_argument('command', choices=['stats', 'list', 'clear', 'search'],
                       help='命令: stats(统计) | list(列表) | clear(清空) | search(搜索)')
    parser.add_argument('--query', '-q', help='搜索查询（用于search命令）')
    parser.add_argument('--top-k', '-k', type=int, default=5, help='返回结果数量')
    
    args = parser.parse_args()
    
    if args.command == 'stats':
        show_stats()
    elif args.command == 'list':
        list_documents()
    elif args.command == 'clear':
        clear_knowledge_base()
    elif args.command == 'search':
        if not args.query:
            print("❌ 搜索命令需要 --query 参数")
            sys.exit(1)
        search_test(args.query, args.top_k)

if __name__ == "__main__":
    main()