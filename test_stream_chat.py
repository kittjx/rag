#!/usr/bin/env python3
"""
流式问答测试脚本
测试流式响应功能
"""

import requests
import json
import sys

BASE_URL = "http://localhost:8000"

def test_stream_chat(question: str = "你好，请介绍一下自己", top_k: int = 3, temperature: float = 0.7):
    """测试流式问答"""
    
    print("=" * 60)
    print("  流式问答测试")
    print("=" * 60)
    print(f"\n问题: {question}")
    print(f"检索数量: {top_k}")
    print(f"温度: {temperature}\n")
    
    try:
        # 发送流式请求
        response = requests.post(
            f"{BASE_URL}/api/v1/chat/stream",
            json={
                "question": question,
                "top_k": top_k,
                "temperature": temperature
            },
            stream=True,
            timeout=30
        )
        
        if response.status_code != 200:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"错误: {response.text}")
            return False
        
        print("✅ 开始接收流式响应...\n")
        
        sources_shown = False
        answer_text = ""
        backend_info = {}
        
        # 逐行读取流式响应
        for line in response.iter_lines():
            if not line:
                continue
            
            line = line.decode('utf-8')
            
            # 解析 SSE 格式
            if line.startswith('data: '):
                data_str = line[6:]  # 去掉 "data: " 前缀
                
                if data_str == '[DONE]':
                    print("\n\n✅ 流式响应完成")
                    break
                
                try:
                    data = json.loads(data_str)
                    
                    # 处理来源信息
                    if 'sources' in data and not sources_shown:
                        sources_shown = True
                        
                        # 显示后端信息
                        if 'backend' in data:
                            backend_info = {
                                'backend': data['backend'],
                                'model': data['model']
                            }
                            print(f"🤖 使用后端: {data['backend']}")
                            print(f"📦 使用模型: {data['model']}\n")
                        
                        # 显示来源
                        print("📚 参考来源:")
                        print("-" * 60)
                        for idx, source in enumerate(data['sources'], 1):
                            score = source['score'] * 100
                            text = source['text'][:80] + "..." if len(source['text']) > 80 else source['text']
                            filename = source['metadata'].get('filename', 'unknown')
                            print(f"\n来源 {idx} (相似度: {score:.1f}%)")
                            print(f"  文件: {filename}")
                            print(f"  内容: {text}")
                        
                        print("\n" + "-" * 60)
                        print("💬 AI回答:")
                        print("-" * 60)
                    
                    # 处理内容（实时打印）
                    if 'content' in data:
                        content = data['content']
                        if content:
                            print(content, end='', flush=True)
                            answer_text += content
                
                except json.JSONDecodeError as e:
                    print(f"\n⚠️  JSON解析错误: {e}")
                    print(f"数据: {data_str}")
        
        print("\n" + "=" * 60)
        print("📊 统计信息:")
        print(f"  回答长度: {len(answer_text)} 字符")
        if backend_info:
            print(f"  后端: {backend_info.get('backend', 'unknown')}")
            print(f"  模型: {backend_info.get('model', 'unknown')}")
        print("=" * 60)
        
        return True
        
    except requests.exceptions.Timeout:
        print("❌ 请求超时")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务")
        print("请确保服务正在运行: http://localhost:8000")
        return False
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主函数"""
    
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
    
    # 测试用例
    test_cases = [
        {
            "question": "你好，请介绍一下自己",
            "top_k": 3,
            "temperature": 0.7
        },
        {
            "question": "什么是健康的生活方式？",
            "top_k": 5,
            "temperature": 0.5
        }
    ]
    
    # 如果有命令行参数，使用自定义问题
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        test_cases = [{
            "question": question,
            "top_k": 3,
            "temperature": 0.7
        }]
    
    # 运行测试
    for idx, test_case in enumerate(test_cases, 1):
        if idx > 1:
            print("\n\n")
            input("按回车继续下一个测试...")
            print("\n")
        
        success = test_stream_chat(**test_case)
        
        if not success:
            print(f"\n❌ 测试 {idx} 失败")
            sys.exit(1)
    
    print("\n\n🎉 所有测试通过！")
    return 0

if __name__ == "__main__":
    sys.exit(main())

