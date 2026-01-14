#!/usr/bin/env python3
"""
API 测试脚本
用于快速测试知识库 API 的各个功能
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("🔍 测试健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/system/health")
        if response.status_code == 200:
            print("✅ 健康检查通过")
            return True
        else:
            print(f"❌ 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return False

def test_system_health():
    """测试系统详细健康检查"""
    print("\n🔍 测试系统详细健康检查...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/system/health")
        if response.status_code == 200:
            data = response.json()
            print("✅ 系统健康检查通过")
            print(f"   状态: {data.get('status')}")
            print(f"   运行时间: {data.get('uptime', 0):.2f}秒")
            
            components = data.get('components', {})
            for name, info in components.items():
                status = info.get('status', 'unknown')
                print(f"   {name}: {status}")
            return True
        else:
            print(f"❌ 系统健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_version():
    """测试版本信息"""
    print("\n🔍 测试版本信息...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/system/version")
        if response.status_code == 200:
            data = response.json()
            print("✅ 版本信息获取成功")
            print(f"   名称: {data.get('name')}")
            print(f"   版本: {data.get('version')}")
            return True
        else:
            print(f"❌ 版本信息获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_chat(question="什么是人工智能？"):
    """测试问答接口"""
    print(f"\n🔍 测试问答接口...")
    print(f"   问题: {question}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json={
                "question": question,
                "top_k": 3,
                "temperature": 0.1,
                "use_cache": False
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 问答成功")
            print(f"   回答: {data.get('answer', '')[:100]}...")
            print(f"   来源数量: {len(data.get('sources', []))}")
            print(f"   处理时间: {data.get('processing_time', 0):.2f}秒")
            if data.get('usage'):
                print(f"   Token使用: {data['usage'].get('total_tokens', 0)}")
            return True
        else:
            print(f"❌ 问答失败: {response.status_code}")
            print(f"   错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_document_search(query="测试"):
    """测试文档搜索"""
    print(f"\n🔍 测试文档搜索...")
    print(f"   查询: {query}")
    try:
        response = requests.post(
            f"{BASE_URL}/api/v1/documents/search",
            json={
                "query": query,
                "top_k": 5
            },
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            print("✅ 搜索成功")
            print(f"   结果数量: {data.get('total', 0)}")
            print(f"   处理时间: {data.get('processing_time', 0):.3f}秒")
            return True
        else:
            print(f"❌ 搜索失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def test_document_stats():
    """测试文档统计"""
    print("\n🔍 测试文档统计...")
    try:
        response = requests.get(f"{BASE_URL}/api/v1/documents/stats")
        if response.status_code == 200:
            data = response.json()
            print("✅ 统计信息获取成功")
            print(f"   文档块数量: {data.get('total_chunks', 0)}")
            return True
        else:
            print(f"❌ 统计信息获取失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 请求失败: {e}")
        return False

def main():
    """运行所有测试"""
    print("=" * 50)
    print("知识库 API 测试")
    print("=" * 50)
    
    results = []
    
    # 基础测试
    results.append(("健康检查", test_health()))
    results.append(("系统健康", test_system_health()))
    results.append(("版本信息", test_version()))
    results.append(("文档统计", test_document_stats()))
    
    # 功能测试（可选）
    if "--full" in sys.argv:
        results.append(("文档搜索", test_document_search()))
        results.append(("问答功能", test_chat()))
    
    # 总结
    print("\n" + "=" * 50)
    print("测试总结")
    print("=" * 50)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{name}: {status}")
    
    print(f"\n总计: {passed}/{total} 通过")
    
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())

