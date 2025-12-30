# Use official Python runtime as a parent image
FROM python:3.10-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    OCR_ENGINE=easyocr \
    PADDLE_USE_GPU=False \
    EASYOCR_USE_GPU=False

# Set working directory
WORKDIR /app

# Install system dependencies
# libgl1: for opencv (replaces libgl1-mesa-glx)
# libglib2.0-0: for opencv
# libsm6, libxext6, libxrender1: additional opencv dependencies
# libgomp1: for torch/paddle
# tesseract-ocr: for tesseract engine
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    tesseract-ocr \
    tesseract-ocr-chi-sim \
    tesseract-ocr-eng \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements file
COPY requirements.txt .

# Install python dependencies
# Note: We install torch cpu version explicitly to save space if needed, 
# but easyocr might override. For now, we trust requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create uploads directory
RUN mkdir -p uploads

# Expose port
EXPOSE 8000

# Start command
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]
