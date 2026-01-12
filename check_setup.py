#!/usr/bin/env python3
"""
环境检查脚本
检查系统环境和依赖是否正确配置
"""

import sys
import os
from pathlib import Path

# 加载环境变量
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

def check_python_version():
    """检查Python版本"""
    print("🐍 检查Python版本...")
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"   ✅ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"   ❌ Python版本过低: {version.major}.{version.minor}.{version.micro}")
        print(f"   需要 Python 3.8+")
        return False

def check_dependencies():
    """检查依赖包"""
    print("\n📦 检查依赖包...")
    
    required_packages = {
        'fastapi': 'FastAPI',
        'uvicorn': 'Uvicorn',
        'pydantic': 'Pydantic',
        'chromadb': 'ChromaDB',
        'sentence_transformers': 'Sentence Transformers',
        'langchain_text_splitters': 'LangChain Text Splitters',
        'langchain_community': 'LangChain Community',
        'redis': 'Redis',
        'aiohttp': 'aiohttp',
    }
    
    optional_packages = {
        'tiktoken': 'TikToken (可选)',
        'psutil': 'psutil (可选)',
    }
    
    all_ok = True
    
    for package, name in required_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ❌ {name} - 未安装")
            all_ok = False
    
    print("\n   可选依赖:")
    for package, name in optional_packages.items():
        try:
            __import__(package)
            print(f"   ✅ {name}")
        except ImportError:
            print(f"   ⚠️  {name} - 未安装（不影响核心功能）")
    
    return all_ok

def check_directories():
    """检查目录结构"""
    print("\n📁 检查目录结构...")
    
    required_dirs = [
        'data',
        'data/raw_documents',
        'data/processed_chunks',
        'data/vector_store',
        'models',
        'logs',
    ]
    
    all_ok = True
    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"   ✅ {dir_path}")
        else:
            print(f"   ⚠️  {dir_path} - 不存在，将自动创建")
            path.mkdir(parents=True, exist_ok=True)
    
    return all_ok

def check_env_vars():
    """检查环境变量"""
    print("\n🔧 检查环境变量...")
    
    # 尝试加载.env文件
    env_file = Path('.env')
    if env_file.exists():
        print(f"   ✅ .env 文件存在")
    else:
        print(f"   ⚠️  .env 文件不存在")
        print(f"   建议: cp .env.example .env")
    
    # 检查关键环境变量
    deepseek_key = os.getenv('DEEPSEEK_API_KEY')
    if deepseek_key:
        print(f"   ✅ DEEPSEEK_API_KEY 已设置")
    elif os.getenv('QWEN_API_KEY'):
        print(f"   ✅ QWEN_API_KEY 已设置")
    else:
        print(f"   ⚠️  API KEY 未设置")
    
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    print(f"   ℹ️  REDIS_URL: {redis_url}")
    
    return True

def check_redis():
    """检查Redis连接"""
    print("\n🔴 检查Redis...")

    try:
        import redis
        redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
        print(f"   ℹ️  连接地址: {redis_url}")

        client = redis.Redis.from_url(redis_url, socket_timeout=3, socket_connect_timeout=3)
        client.ping()
        print(f"   ✅ Redis连接成功")

        # 显示Redis信息
        info = client.info('server')
        redis_version = info.get('redis_version', 'unknown')
        print(f"   ℹ️  Redis版本: {redis_version}")

        return True
    except ImportError:
        print(f"   ❌ Redis包未安装")
        return False
    except redis.ConnectionError as e:
        print(f"   ⚠️  Redis连接失败: {e}")
        print(f"   提示: 如果使用Docker，请确保容器正在运行")
        print(f"   示例: docker run -d -p 6379:6379 redis:alpine")
        print(f"   缓存功能将不可用，但不影响核心功能")
        return True
    except Exception as e:
        print(f"   ⚠️  Redis检查失败: {e}")
        print(f"   缓存功能将不可用，但不影响核心功能")
        return True

def check_knowledge_base():
    """检查知识库状态"""
    print("\n📚 检查知识库...")
    
    vector_store_dir = Path('data/vector_store')
    if not vector_store_dir.exists() or not list(vector_store_dir.iterdir()):
        print(f"   ⚠️  向量数据库未初始化")
        print(f"   请运行: python scripts/build_knowledge_base.py")
        return False
    
    raw_docs_dir = Path('data/raw_documents')
    if raw_docs_dir.exists():
        doc_files = [f for f in raw_docs_dir.rglob("*") if f.is_file()]
        print(f"   ℹ️  原始文档: {len(doc_files)} 个文件")
    
    processed_dir = Path('data/processed_chunks')
    stats_file = processed_dir / 'stats.json'
    if stats_file.exists():
        import json
        with open(stats_file, 'r') as f:
            stats = json.load(f)
        print(f"   ✅ 知识库已构建")
        print(f"   ℹ️  文档块数: {stats.get('total_chunks', 0)}")
        print(f"   ℹ️  文档数: {stats.get('total_documents', 0)}")
        return True
    else:
        print(f"   ⚠️  知识库统计信息不存在")
        return False

def main():
    """运行所有检查"""
    print("=" * 60)
    print("知识库问答系统 - 环境检查")
    print("=" * 60)
    
    checks = [
        ("Python版本", check_python_version),
        ("依赖包", check_dependencies),
        ("目录结构", check_directories),
        ("环境变量", check_env_vars),
        ("Redis", check_redis),
        ("知识库", check_knowledge_base),
    ]
    
    results = []
    for name, check_func in checks:
        try:
            result = check_func()
            results.append((name, result))
        except Exception as e:
            print(f"   ❌ 检查失败: {e}")
            results.append((name, False))
    
    # 总结
    print("\n" + "=" * 60)
    print("检查总结")
    print("=" * 60)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有检查通过！可以启动服务了")
        print("运行: bash start.sh 或 make start")
        return 0
    else:
        print("\n⚠️  部分检查未通过，请根据上述提示进行修复")
        return 1

if __name__ == "__main__":
    sys.exit(main())

