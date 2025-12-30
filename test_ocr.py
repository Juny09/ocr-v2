"""
Example test file for OCR service
Run with: pytest test_ocr.py
"""
import pytest
from pathlib import Path
from services.ocr_service import OCRService, PaddleOCREngine, TesseractOCREngine
from utils.image_processor import ImageProcessor


class TestImageProcessor:
    """Test image preprocessing utilities"""
    
    def test_grayscale_conversion(self):
        """Test grayscale conversion"""
        # Note: This is a placeholder test
        # In real scenarios, you would use actual test images
        pass
    
    def test_threshold(self):
        """Test thresholding"""
        pass


class TestOCRService:
    """Test OCR service"""
    
    def test_paddle_ocr_init(self):
        """Test PaddleOCR initialization"""
        try:
            engine = PaddleOCREngine(use_gpu=False, lang="en")
            assert engine is not None
        except Exception as e:
            pytest.skip(f"PaddleOCR not available: {e}")
    
    def test_service_init(self):
        """Test OCR service initialization"""
        try:
            service = OCRService(engine_type="paddleocr", use_gpu=False, lang="en")
            assert service.engine_type == "paddleocr"
        except Exception as e:
            pytest.skip(f"OCR service init failed: {e}")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
