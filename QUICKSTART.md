# 快速启动指南

## 一键运行脚本

### macOS/Linux

创建 `start.sh`:

```bash
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
    echo "📥 安装依赖..."
    pip install -r requirements.txt
    touch venv/installed.txt
fi

# 创建 .env 文件
if [ ! -f ".env" ]; then
    echo "⚙️ 创建配置文件..."
    cp .env.example .env
fi

# 启动服务
echo "✨ 启动服务器..."
echo "访问: http://localhost:8000"
python main.py
```

运行:

```bash
chmod +x start.sh
./start.sh
```

### Windows

创建 `start.bat`:

```batch
@echo off
echo 🚀 启动 OCR 服务...

if not exist "venv" (
    echo 📦 创建虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate

if not exist "venv\installed.txt" (
    echo 📥 安装依赖...
    pip install -r requirements.txt
    echo. > venv\installed.txt
)

if not exist ".env" (
    echo ⚙️ 创建配置文件...
    copy .env.example .env
)

echo ✨ 启动服务器...
echo 访问: http://localhost:8000
python main.py
```

运行:

```batch
start.bat
```

## Docker 运行 (可选)

创建 `Dockerfile`:

```dockerfile
FROM python:3.9-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 暴露端口
EXPOSE 8000

# 启动命令
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

运行:

```bash
docker build -t ocr-app .
docker run -p 8000:8000 ocr-app
```

## 常用命令

```bash
# 安装依赖
pip install -r requirements.txt

# 运行开发服务器
uvicorn main:app --reload

# 运行生产服务器
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# 运行测试
pytest test_ocr.py -v

# 查看 API 文档
# 浏览器打开: http://localhost:8000/api/docs
```
