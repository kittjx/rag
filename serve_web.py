#!/usr/bin/env python3
"""
简单的HTTP服务器，用于提供Web界面
"""

import http.server
import socketserver
import os
import sys

PORT = 8080
DIRECTORY = "web"

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)
    
    def end_headers(self):
        # 添加CORS头
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()

def main():
    # 检查web目录是否存在
    if not os.path.exists(DIRECTORY):
        print(f"❌ 错误: {DIRECTORY} 目录不存在")
        sys.exit(1)
    
    # 检查必要文件
    required_files = ['index.html', 'style.css', 'app.js']
    for file in required_files:
        if not os.path.exists(os.path.join(DIRECTORY, file)):
            print(f"❌ 错误: {file} 文件不存在")
            sys.exit(1)
    
    print("=" * 60)
    print("  知识库问答系统 - Web界面")
    print("=" * 60)
    print(f"\n🌐 Web服务器启动在: http://localhost:{PORT}")
    print(f"📁 服务目录: {DIRECTORY}")
    print("\n⚠️  请确保API服务正在运行: http://localhost:8000")
    print("\n按 Ctrl+C 停止服务器\n")
    print("=" * 60)
    
    try:
        with socketserver.TCPServer(("", PORT), MyHTTPRequestHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 服务器已停止")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

