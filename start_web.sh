#!/bin/bash

# 知识库问答系统 - Web界面启动脚本

echo "======================================================================"
echo "  知识库问答系统 - 启动Web界面"
echo "======================================================================"
echo ""

# 检查API服务是否运行
echo "🔍 检查API服务..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "✅ API服务正在运行"
else
    echo "⚠️  警告: API服务未运行"
    echo ""
    echo "请先启动API服务:"
    echo "  bash start.sh"
    echo "  或"
    echo "  make start"
    echo ""
    read -p "是否继续启动Web界面? (y/N) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "❌ 已取消"
        exit 1
    fi
fi

echo ""
echo "🚀 启动Web服务器..."
echo ""

# 启动Web服务器
python3 serve_web.py

