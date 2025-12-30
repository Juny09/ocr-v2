"""
Services package
"""
from .ocr_service import OCRService, PaddleOCREngine, TesseractOCREngine

__all__ = ["OCRService", "PaddleOCREngine", "TesseractOCREngine"]
