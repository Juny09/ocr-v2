"""
Configuration module for OCR application
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Fix PATH for macOS/Linux if sysctl/other binaries are in /usr/sbin but not in PATH
# This fixes "sysctl: command not found" errors in PaddleOCR/libraries
if os.name == 'posix':
    path = os.environ.get('PATH', '')
    for sbin in ['/usr/sbin', '/sbin']:
        if sbin not in path and os.path.exists(sbin):
            os.environ['PATH'] = f"{path}:{sbin}"

# Base directory
BASE_DIR = Path(__file__).resolve().parent

# Server Configuration
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# OCR Configuration
OCR_ENGINE = os.getenv("OCR_ENGINE", "paddleocr")  # paddleocr or tesseract
MAX_FILE_SIZE_MB = int(os.getenv("MAX_FILE_SIZE_MB", "5"))
MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024

# CORS Configuration
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:8000,http://127.0.0.1:8000"
).split(",")

# File Upload Configuration
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads")
ALLOWED_EXTENSIONS = set(
    os.getenv("ALLOWED_EXTENSIONS", "png,jpg,jpeg").split(",")
)

# PaddleOCR Configuration
PADDLE_USE_GPU = os.getenv("PADDLE_USE_GPU", "False").lower() == "true"
PADDLE_LANG = os.getenv("PADDLE_LANG", "ch")

# Tesseract Configuration
TESSERACT_LANG = os.getenv("TESSERACT_LANG", "chi_sim+eng")

# EasyOCR Configuration
# Format: comma separated languages, e.g. "ch_sim,en"
EASYOCR_LANG = os.getenv("EASYOCR_LANG", "ch_sim,en").split(",")
EASYOCR_USE_GPU = os.getenv("EASYOCR_USE_GPU", "False").lower() == "true"

# Create upload directory if it doesn't exist
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
