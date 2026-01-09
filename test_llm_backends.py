#!/usr/bin/env python3
"""
LLM后端测试脚本
测试多后端切换功能
"""

import requests
import json
import sys
from typing import Dict, Any

BASE_URL = "http://localhost:8000"

def print_section(title: str):
    """打印分隔线"""
    print("\n" + "=" * 60)
    print(f"  {title}")
    print("=" * 60)

def test_version():
    """测试版本信息"""
    print_section("1. 测试版本信息")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/system/version")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 系统版本: {data['version']}")
            print(f"✅ LLM后端: {data['components']['llm_backend']}")
            print(f"✅ LLM模型: {data['components']['llm_model']}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_backends_info():
    """测试后端信息"""
    print_section("2. 测试后端信息")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/system/llm/backends")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 当前后端: {data['current_backend']}")
            print(f"✅ 当前模型: {data['current_model']}")
            print("\n可用后端:")
            
            for backend in data['available_backends']:
                status = "✅" if backend['healthy'] else "❌"
                api_key = "✅" if backend['api_key_configured'] else "❌"
                print(f"  {status} {backend['name']:10s} - 模型: {backend['model']:20s} - API密钥: {api_key}")
            
            return data
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return None
    except Exception as e:
        print(f"❌ 错误: {e}")
        return None

def test_switch_backend(backend: str):
    """测试切换后端"""
    print_section(f"3. 测试切换到 {backend}")
    
    try:
        response = requests.post(f"{BASE_URL}/api/v1/system/llm/switch/{backend}")
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ {data['message']}")
                print(f"✅ 当前后端: {data['current_backend']}")
                print(f"✅ 当前模型: {data['current_model']}")
                return True
            else:
                print(f"⚠️  {data['message']}")
                return False
        else:
            print(f"❌ 请求失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def test_chat(question: str = "你好，请简单介绍一下自己"):
    """测试问答"""
    print_section("4. 测试问答功能")
    
    try:
        payload = {
            "question": question,
            "top_k": 3,
            "use_cache": False
        }
        
        print(f"问题: {question}")
        print("正在请求...")
        
        response = requests.post(
            f"{BASE_URL}/api/v1/chat",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ 回答:")
            print(f"{data['answer'][:200]}...")
            print(f"\n使用后端: {data.get('backend', 'unknown')}")
            print(f"使用模型: {data.get('model', 'unknown')}")
            return True
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        return False

def main():
    """主函数"""
    print("=" * 60)
    print("  LLM后端测试")
    print("=" * 60)
    
    # 检查服务是否运行
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code != 200:
            print("❌ 服务未运行，请先启动服务")
            print("运行: bash start.sh 或 make start")
            sys.exit(1)
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        print("请确保服务正在运行: http://localhost:8000")
        sys.exit(1)
    
    # 运行测试
    results = []
    
    # 1. 测试版本信息
    results.append(("版本信息", test_version()))
    
    # 2. 测试后端信息
    backends_data = test_backends_info()
    results.append(("后端信息", backends_data is not None))
    
    # 3. 测试切换后端（如果有多个可用）
    if backends_data:
        available = [b for b in backends_data['available_backends'] if b['healthy']]
        if len(available) > 1:
            # 切换到第二个可用后端
            second_backend = available[1]['name']
            results.append((f"切换到{second_backend}", test_switch_backend(second_backend)))
        else:
            print("\n⚠️  只有一个后端可用，跳过切换测试")
    
    # 4. 测试问答
    results.append(("问答功能", test_chat()))
    
    # 总结
    print_section("测试总结")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅" if result else "❌"
        print(f"{status} {name}")
    
    print(f"\n通过: {passed}/{total}")
    
    if passed == total:
        print("\n🎉 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试未通过")
        return 1

if __name__ == "__main__":
    sys.exit(main())

