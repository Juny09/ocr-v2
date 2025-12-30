# Image to Text - OCR Web Application

🎯 **商用级 OCR 图片转文字服务**

一个基于 AI 的现代化 OCR 网页应用，支持中英文识别，提供高质量的图片文字提取服务。

## ✨ 功能特性

- 🖼️ **多格式支持**: PNG, JPG, JPEG
- 🤖 **双引擎**: PaddleOCR (默认) / Tesseract OCR (可切换)
- 🎨 **图片预处理**: 灰度化、二值化、去噪、倾斜校正
- 📱 **现代化界面**: 响应式设计、暗黑主题、拖拽上传
- 💾 **便捷操作**: 一键复制、下载结果
- 🔒 **文件限制**: 最大 5MB，保证处理速度
- 🌐 **RESTful API**: 完整的 API 文档
- ⚡ **高性能**: FastAPI 后端，异步处理

## 📁 项目结构

```
ocr/
├── main.py                 # FastAPI 主应用
├── config.py               # 配置管理
├── requirements.txt        # Python 依赖
├── .env.example           # 环境变量模板
├── api/                   # API 路由层
│   ├── __init__.py
│   ├── routes.py          # API 端点定义
│   └── models.py          # Pydantic 数据模型
├── services/              # 业务逻辑层
│   ├── __init__.py
│   └── ocr_service.py     # OCR 引擎服务
├── utils/                 # 工具函数
│   ├── __init__.py
│   └── image_processor.py # 图片预处理
├── static/                # 前端静态文件
│   ├── index.html         # 主页面
│   ├── styles.css         # 样式表
│   └── script.js          # 前端逻辑
└── uploads/               # 临时上传目录 (自动创建)
```

## 🚀 快速开始

### 1. 环境要求

- Python 3.8+
- pip

### 2. 安装依赖

```bash
# 克隆或下载项目到本地
cd ocr

# 创建虚拟环境 (推荐)
python -m venv venv
source venv/bin/activate  # macOS/Linux
# 或
venv\Scripts\activate     # Windows

# 安装 Python 依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑 .env 文件 (可选)
# 默认配置已经可以直接使用
```

### 4. 运行服务

```bash
# 方式 1: 使用 uvicorn 直接运行
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# 方式 2: 使用 Python 运行
python main.py
```

### 5. 访问应用

打开浏览器访问:

- **主页面**: http://localhost:8000
- **API 文档**: http://localhost:8000/api/docs
- **健康检查**: http://localhost:8000/api/health

## 📖 API 文档

### 1. 健康检查

```
GET /api/health
```

**响应示例:**

```json
{
  "status": "healthy",
  "ocr_engine": "paddleocr",
  "version": "1.0.0"
}
```

### 2. OCR 识别

```
POST /api/ocr
```

**请求参数:**

- `file`: 图片文件 (multipart/form-data)
- `preprocess`: 是否预处理 (boolean, 默认: true)

**响应示例:**

```json
{
  "success": true,
  "text": "识别出的完整文本",
  "lines": [
    {
      "text": "第一行文本",
      "confidence": 0.98,
      "bbox": [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
    }
  ],
  "engine": "paddleocr"
}
```

**cURL 示例:**

```bash
curl -X POST "http://localhost:8000/api/ocr" \
  -F "file=@image.png" \
  -F "preprocess=true"
```

## ⚙️ 配置说明

### 环境变量 (.env)

```bash
# 服务器配置
HOST=0.0.0.0
PORT=8000

# OCR 引擎选择
OCR_ENGINE=paddleocr  # paddleocr 或 tesseract

# 文件限制
MAX_FILE_SIZE_MB=5

# CORS 配置
ALLOWED_ORIGINS=http://localhost:8000,http://127.0.0.1:8000

# PaddleOCR 配置
PADDLE_USE_GPU=False
PADDLE_LANG=ch        # ch: 中文, en: 英文

# Tesseract 配置
TESSERACT_LANG=chi_sim+eng
```

### 切换 OCR 引擎

#### 使用 PaddleOCR (默认)

```bash
# .env 文件
OCR_ENGINE=paddleocr
PADDLE_LANG=ch  # 中文
```

#### 使用 Tesseract

```bash
# 1. 安装 Tesseract (macOS)
brew install tesseract
brew install tesseract-lang  # 中文语言包

# 2. .env 文件
OCR_ENGINE=tesseract
TESSERACT_LANG=chi_sim+eng
```

## 🎨 前端功能

- ✅ **拖拽上传**: 支持拖拽文件到上传区域
- ✅ **图片预览**: 上传后立即预览
- ✅ **实时反馈**: 处理状态实时显示
- ✅ **一键复制**: 点击复制识别结果
- ✅ **下载文本**: 导出为 .txt 文件
- ✅ **响应式设计**: 支持移动端和桌面端

## 🔧 技术栈

### 后端

- **FastAPI**: 现代化 Python Web 框架
- **PaddleOCR**: 百度开源 OCR 引擎 (中文识别优秀)
- **Tesseract**: Google 开源 OCR 引擎
- **OpenCV**: 图片预处理
- **Pillow**: 图片处理
- **Pydantic**: 数据验证

### 前端

- **原生 HTML/CSS/JavaScript**: 无框架依赖
- **现代化 UI**: 渐变色、暗黑主题、动画效果
- **响应式设计**: 移动端适配

## 📝 使用示例

### Python 调用 API

```python
import requests

url = "http://localhost:8000/api/ocr"
files = {"file": open("image.png", "rb")}
data = {"preprocess": True}

response = requests.post(url, files=files, data=data)
result = response.json()

if result["success"]:
    print("识别结果:", result["text"])
    print("字符数:", len(result["text"]))
else:
    print("错误:", result["error"])
```

### JavaScript 调用 API

```javascript
const formData = new FormData();
formData.append("file", fileInput.files[0]);
formData.append("preprocess", "true");

fetch("http://localhost:8000/api/ocr", {
  method: "POST",
  body: formData,
})
  .then((response) => response.json())
  .then((data) => {
    if (data.success) {
      console.log("识别结果:", data.text);
    }
  });
```

## 🔒 安全性

- ✅ 文件类型验证 (仅允许图片格式)
- ✅ 文件大小限制 (5MB)
- ✅ CORS 配置
- ✅ 临时文件自动清理
- ✅ 异常处理和错误提示

## 🚀 扩展功能 (roadmap)

- [ ] 用户认证系统
- [ ] API 调用次数限制
- [ ] 批量图片处理
- [ ] 历史记录保存
- [ ] 多语言界面
- [ ] PDF 文件支持
- [ ] 云存储集成
- [ ] 付费套餐

## ⚠️ 常见问题

### 1. PaddleOCR 初始化慢

首次运行时 PaddleOCR 会下载模型文件 (~100MB)，需要等待几分钟。

### 2. Tesseract 找不到

确保已安装 Tesseract OCR:

```bash
# macOS
brew install tesseract

# Ubuntu
sudo apt-get install tesseract-ocr

# Windows
# 从 https://github.com/UB-Mannheim/tesseract/wiki 下载安装
```

### 3. 中文识别不准确

- 使用 PaddleOCR 引擎 (中文识别更优)
- 确保图片清晰、文字不要太小
- 启用预处理选项

### 4. CORS 错误

在 `.env` 文件中添加前端域名到 `ALLOWED_ORIGINS`。

## 📄 许可证

MIT License

## 👨‍💻 开发者

专业 Python 全栈工程师 | AI & Web API 开发

---

**🎉 享受使用本 OCR 服务！如有问题欢迎反馈。**
