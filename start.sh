#!/bin/bash

echo "🚀 启动 OCR 服务..."

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "📦 创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 检查依赖
if [ ! -f "venv/installed.txt" ]; then
    echo "📥 安装依赖 (首次运行需要几分钟)..."
    pip install --upgrade pip
    pip install -r requirements.txt
    touch venv/installed.txt
    echo "✅ 依赖安装完成"
fi

# 创建 .env 文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建配置文件..."
    cp .env.example .env
fi

# 启动服务
echo ""
echo "✨ 启动服务器..."
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  📱 主页: http://localhost:8000"
echo "  📚 API 文档: http://localhost:8000/api/docs"
echo "  ❤️  健康检查: http://localhost:8000/api/health"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
python3 main.py
