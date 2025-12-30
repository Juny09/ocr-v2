"""
API routes for OCR service
"""
import os
import shutil
import logging
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from fastapi.responses import JSONResponse

from .models import OCRResponse, ErrorResponse, HealthResponse
from services import OCRService
from utils import ImageProcessor
import config

logger = logging.getLogger(__name__)

# Create router
router = APIRouter()

# OCR service will be initialized lazily on first use
ocr_service = None
ocr_init_error = None


def get_ocr_service():
    """Lazy initialization of OCR service"""
    global ocr_service, ocr_init_error
    
    if ocr_service is not None:
        return ocr_service
    
    if ocr_init_error is not None:
        raise ocr_init_error
    
    try:
        logger.info(f"Initializing OCR service with engine: {config.OCR_ENGINE}")
        if config.OCR_ENGINE == "paddleocr":
            ocr_service = OCRService(
                engine_type="paddleocr",
                use_gpu=config.PADDLE_USE_GPU,
                lang=config.PADDLE_LANG
            )
        elif config.OCR_ENGINE == "easyocr":
            ocr_service = OCRService(
                engine_type="easyocr",
                lang=config.EASYOCR_LANG,
                use_gpu=config.EASYOCR_USE_GPU
            )
        else:
            ocr_service = OCRService(
                engine_type="tesseract",
                lang=config.TESSERACT_LANG
            )
        logger.info("OCR service initialized successfully")
        return ocr_service
    except Exception as e:
        logger.error(f"Failed to initialize OCR service: {str(e)}")
        ocr_init_error = e
        raise e


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    # Always return healthy - OCR will be initialized on first use
    ocr_status = "ready" if ocr_service else "not_initialized"
    return HealthResponse(
        status="healthy",
        ocr_engine=f"{config.OCR_ENGINE} ({ocr_status})",
        version="1.0.0"
    )


@router.post("/ocr", response_model=OCRResponse)
def perform_ocr(
    file: UploadFile = File(..., description="Image file (PNG, JPG, JPEG)"),
    preprocess: bool = Form(True, description="Apply image preprocessing"),
    language: Optional[str] = Form(None, description="Language code(s)"),
    crop_x: Optional[float] = Form(None, description="Crop X coordinate"),
    crop_y: Optional[float] = Form(None, description="Crop Y coordinate"),
    crop_width: Optional[float] = Form(None, description="Crop width"),
    crop_height: Optional[float] = Form(None, description="Crop height"),
):
    """
    Perform OCR on uploaded image
    
    Args:
        file: Uploaded image file
        preprocess: Whether to apply preprocessing
        language: Optional language code(s) (e.g. 'en' or 'ch_sim,en')
        crop_x: X coordinate of top-left corner
        crop_y: Y coordinate of top-left corner
        crop_width: Width of crop area
        crop_height: Height of crop area
        
    Returns:
        OCR result with recognized text
    """
    logger.info(f"Received OCR request for file: {file.filename}, preprocess={preprocess}, language={language}")
    if crop_width and crop_height:
        logger.info(f"Crop parameters: x={crop_x}, y={crop_y}, w={crop_width}, h={crop_height}")
    
    # Initialize OCR service if needed (lazy initialization)
    try:
        service = get_ocr_service()
        
        # Check if language change is needed for EasyOCR
        if config.OCR_ENGINE == "easyocr" and language:
            current_langs = getattr(service.engine, 'reader', None)
            # This is a bit hacky, but EasyOCR reader has lang_list
            # Or we can just re-initialize if the requested lang is different
            # For simplicity, if language is provided and different from config default, re-init
            
            # Parse requested languages
            requested_langs = language.split(',')
            
            # Check if we need to reload
            # Note: We are creating a new engine instance for this request if languages differ
            # Ideally we should cache these, but for now this works
            if set(requested_langs) != set(config.EASYOCR_LANG):
                 logger.info(f"Switching EasyOCR language to {requested_langs}")
                 # Create a temporary service instance or update the existing one
                 # Updating existing one is risky for concurrency, but we are running in thread pool
                 # Let's create a temporary engine just for this request if possible, 
                 # or just re-init the main one (simpler for single user)
                 service = OCRService(
                    engine_type="easyocr",
                    lang=requested_langs,
                    use_gpu=config.EASYOCR_USE_GPU
                 )

    except Exception as e:
        logger.error(f"OCR service initialization failed: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"OCR service initialization failed: {str(e)}"
        )
    
    # Validate file extension
    file_ext = Path(file.filename).suffix.lower().lstrip('.')
    if file_ext not in config.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(config.ALLOWED_EXTENSIONS)}"
        )
    
    # Check file size
    file.file.seek(0, 2)  # Seek to end
    file_size = file.file.tell()
    file.file.seek(0)  # Seek back to start
    
    if file_size > config.MAX_FILE_SIZE_BYTES:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum size: {config.MAX_FILE_SIZE_MB}MB"
        )
    
    # Save uploaded file
    temp_path = config.UPLOAD_DIR / f"temp_{file.filename}"
    processed_path = config.UPLOAD_DIR / f"processed_{file.filename}"
    
    try:
        # Save original file
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        logger.info(
            f"Upload: name={file.filename}, ext={file_ext}, size={file_size} bytes"
        )
        
        # Apply crop if parameters are provided
        if crop_width and crop_height and crop_width > 0 and crop_height > 0:
            try:
                logger.info("Applying crop to image")
                image = ImageProcessor.load_image(temp_path)
                x = int(crop_x) if crop_x is not None else 0
                y = int(crop_y) if crop_y is not None else 0
                w = int(crop_width)
                h = int(crop_height)
                
                cropped_image = ImageProcessor.crop(image, x, y, w, h)
                ImageProcessor.save_image(cropped_image, temp_path)
                logger.info(f"Image cropped to {w}x{h}")
            except Exception as e:
                logger.error(f"Failed to crop image: {str(e)}")
                # Continue with original image if crop fails
        
        if preprocess:
            # PaddleOCR 和 EasyOCR 更适合使用原图（自带图像增强），避免二值化破坏信息
            if config.OCR_ENGINE in ["paddleocr", "easyocr"]:
                ocr_input = temp_path
                logger.info(
                    f"Preprocess: engine={config.OCR_ENGINE}, applied=none, input={ocr_input}"
                )
            else:
                try:
                    processed_image = ImageProcessor.preprocess(
                        temp_path,
                        grayscale=True,
                        threshold=True,
                        denoise_image=True,
                        deskew_image=False
                    )
                    ImageProcessor.save_image(processed_image, processed_path)
                    ocr_input = processed_path
                    logger.info(
                        f"Preprocess: engine=tesseract, applied=grayscale+denoise+threshold, input={ocr_input}"
                    )
                except Exception as e:
                    logger.warning(f"Preprocessing failed: {str(e)}, using original image")
                    ocr_input = temp_path
                    logger.info(
                        f"Preprocess: fallback=original, input={ocr_input}"
                    )
        else:
            ocr_input = temp_path
            logger.info(f"Preprocess: disabled, input={ocr_input}")
        
        # Perform OCR
        result = service.process_image(ocr_input)
        
        # Clean up temporary files
        if temp_path.exists():
            temp_path.unlink()
        if processed_path.exists():
            processed_path.unlink()
        
        if result.get("success"):
            lines = result.get("lines", [])
            text_val = result.get("text", "")
            avg_conf = None
            if lines:
                try:
                    avg_conf = sum([float(x.get("confidence", 0.0)) for x in lines]) / len(lines)
                except Exception:
                    avg_conf = None
            logger.info(
                f"OCR result: engine={result.get('engine')}, text_len={len(text_val)}, lines={len(lines)}, avg_conf={avg_conf}"
            )
            return OCRResponse(
                success=True,
                text=result.get("text", ""),
                lines=[
                    {
                        "text": line.get("text", ""),
                        "confidence": line.get("confidence", 0.0),
                        "bbox": line.get("bbox")
                    }
                    for line in result.get("lines", [])
                ],
                engine=result.get("engine", config.OCR_ENGINE)
            )
        else:
            return OCRResponse(
                success=False,
                text="",
                lines=[],
                engine=result.get("engine", config.OCR_ENGINE),
                error=result.get("error", "Unknown error")
            )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"OCR processing failed: {str(e)}")
        # Clean up on error
        if temp_path.exists():
            temp_path.unlink()
        if processed_path.exists():
            processed_path.unlink()
        
        raise HTTPException(
            status_code=500,
            detail=f"OCR processing failed: {str(e)}"
        )
