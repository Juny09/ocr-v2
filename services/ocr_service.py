"""
OCR Service with PaddleOCR and Tesseract support
"""
import logging
from pathlib import Path
from typing import Union, Dict, List, Optional
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


import math

def reconstruct_layout(lines: List[Dict]) -> str:
    """
    Reconstruct text layout based on bounding boxes.
    Sorts by Y (rows) and then X (columns).
    Adds spaces to simulate original layout.
    
    Args:
        lines: List of dicts with 'text' and 'bbox' keys
               bbox can be 4 points (EasyOCR/Paddle) or [x,y,w,h] (Tesseract)
    
    Returns:
        Formatted string
    """
    if not lines:
        return ""
        
    # Helper to get center Y of a box
    def get_cy(bbox):
        if isinstance(bbox[0], list): # [[x1,y1], [x2,y2]...]
            ys = [p[1] for p in bbox]
            return sum(ys) / len(ys)
        else: # [x, y, w, h]
            return bbox[1] + bbox[3] / 2
            
    # Helper to get center X
    def get_cx(bbox):
        if isinstance(bbox[0], list):
            xs = [p[0] for p in bbox]
            return sum(xs) / len(xs)
        else:
            return bbox[0] + bbox[2] / 2

    # Helper to get left X
    def get_x(bbox):
        if isinstance(bbox[0], list):
            return min(p[0] for p in bbox)
        else:
            return bbox[0]

    # Helper to get height
    def get_h(bbox):
        if isinstance(bbox[0], list):
            ys = [p[1] for p in bbox]
            return max(ys) - min(ys)
        else:
            return bbox[3]

    # Sort by Y first to process roughly top-to-bottom
    lines.sort(key=lambda l: get_cy(l['bbox']))
    
    rows = []
    current_row = []
    
    if lines:
        current_row.append(lines[0])
        
        # Group into rows based on vertical overlap
        for i in range(1, len(lines)):
            box = lines[i]
            prev_box = current_row[-1]
            
            # Check if vertically aligned (centers are close relative to height)
            h = get_h(prev_box['bbox'])
            y_diff = abs(get_cy(box['bbox']) - get_cy(prev_box['bbox']))
            
            # If y_diff is small enough (e.g. less than half height), consider same row
            if y_diff < h * 0.5:
                current_row.append(box)
            else:
                rows.append(current_row)
                current_row = [box]
        
        if current_row:
            rows.append(current_row)
            
    # Process each row
    output_lines = []
    for row in rows:
        # Sort by X
        row.sort(key=lambda l: get_x(l['bbox']))
        
        line_text = ""
        last_x_end = 0
        
        for item in row:
            box = item['bbox']
            text = item['text']
            
            x_start = get_x(box)
            
            # Calculate spaces needed
            # This is a heuristic: space count = gap / average_char_width
            # But we don't know char width. Assume roughly 10-15px per char or just use spaces.
            # Simpler: gap / 10
            
            if last_x_end > 0:
                gap = max(0, x_start - last_x_end)
                spaces = int(gap / 10)  # rough estimate
                line_text += " " * spaces
            
            line_text += text
            
            # Update last_x_end
            if isinstance(box[0], list):
                last_x_end = max(p[0] for p in box)
            else:
                last_x_end = box[0] + box[2]
                
        output_lines.append(line_text)
        
    return "\n".join(output_lines)


class OCREngine:
    """Base OCR Engine interface"""
    
    def recognize(self, image_path: Union[str, Path]) -> Dict:
        """
        Recognize text from image
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with recognized text and metadata
        """
        raise NotImplementedError


class PaddleOCREngine(OCREngine):
    """PaddleOCR implementation"""
    
    def __init__(self, use_gpu: bool = False, lang: str = "ch"):
        """
        Initialize PaddleOCR engine
        
        Args:
            use_gpu: Whether to use GPU acceleration
            lang: Language model to use ('ch', 'en', etc.)
        """
        try:
            from paddleocr import PaddleOCR
            self.ocr = PaddleOCR(
                use_angle_cls=True,
                lang=lang,
                use_gpu=use_gpu,
                show_log=False
            )
            logger.info(f"PaddleOCR initialized with lang={lang}, gpu={use_gpu}")
        except ImportError:
            raise ImportError(
                "PaddleOCR not installed. Install with: pip install paddleocr"
            )
    
    def recognize(self, image_path: Union[str, Path]) -> Dict:
        """
        Recognize text using PaddleOCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with text, confidence, and bounding boxes
        """
        try:
            result = self.ocr.ocr(str(image_path), cls=True)
            
            if not result or not result[0]:
                return {
                    "success": True,
                    "text": "",
                    "lines": [],
                    "engine": "paddleocr"
                }
            
            lines = []
            full_text = []
            
            for line in result[0]:
                bbox = line[0]  # Bounding box coordinates
                text_info = line[1]  # (text, confidence)
                text = text_info[0]
                confidence = text_info[1]
                
                lines.append({
                    "text": text,
                    "confidence": float(confidence),
                    "bbox": bbox
                })
                full_text.append(text)
            
            return {
                "success": True,
                "text": reconstruct_layout(lines),
                "lines": lines,
                "engine": "paddleocr"
            }
            
        except Exception as e:
            logger.error(f"PaddleOCR recognition failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "engine": "paddleocr"
            }


class TesseractOCREngine(OCREngine):
    """Tesseract OCR implementation"""
    
    def __init__(self, lang: str = "chi_sim+eng"):
        """
        Initialize Tesseract engine
        
        Args:
            lang: Language(s) to use (e.g., 'eng', 'chi_sim+eng')
        """
        try:
            import pytesseract
            from PIL import Image
            
            self.pytesseract = pytesseract
            self.Image = Image
            self.lang = lang
            
            # Test if tesseract is installed
            try:
                pytesseract.get_tesseract_version()
                logger.info(f"Tesseract initialized with lang={lang}")
            except Exception as e:
                raise RuntimeError(
                    "Tesseract not found. Please install Tesseract OCR: "
                    "https://github.com/tesseract-ocr/tesseract"
                )
                
        except ImportError:
            raise ImportError(
                "pytesseract not installed. Install with: pip install pytesseract"
            )
    
    def recognize(self, image_path: Union[str, Path]) -> Dict:
        """
        Recognize text using Tesseract
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with text and metadata
        """
        try:
            image = self.Image.open(image_path)
            
            # Get detailed data
            data = self.pytesseract.image_to_data(
                image,
                lang=self.lang,
                output_type=self.pytesseract.Output.DICT
            )
            
            # Extract text
            text = self.pytesseract.image_to_string(
                image,
                lang=self.lang
            ).strip()
            
            # Build lines with confidence
            lines = []
            n_boxes = len(data['text'])
            
            for i in range(n_boxes):
                if int(data['conf'][i]) > 0:  # Filter out low confidence
                    lines.append({
                        "text": data['text'][i],
                        "confidence": float(data['conf'][i]) / 100.0,
                        "bbox": [
                            data['left'][i],
                            data['top'][i],
                            data['width'][i],
                            data['height'][i]
                        ]
                    })
            
            return {
                "success": True,
                "text": text,
                "lines": lines,
                "engine": "tesseract"
            }
            
        except Exception as e:
            logger.error(f"Tesseract recognition failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "engine": "tesseract"
            }


class EasyOCREngine(OCREngine):
    """EasyOCR implementation"""
    
    def __init__(self, lang: List[str] = None, use_gpu: bool = False):
        """
        Initialize EasyOCR engine
        
        Args:
            lang: List of language codes (e.g., ['ch_sim', 'en'])
            use_gpu: Whether to use GPU acceleration
        """
        try:
            import easyocr
            # Default to Chinese Simplified and English if not provided
            if lang is None:
                lang = ['ch_sim', 'en']
            
            logger.info(f"Initializing EasyOCR with lang={lang}, gpu={use_gpu}. This may take a while if downloading models...")
            self.reader = easyocr.Reader(lang, gpu=use_gpu)
            logger.info(f"EasyOCR initialized successfully")
            
        except ImportError:
            raise ImportError(
                "EasyOCR not installed. Install with: pip install easyocr"
            )
            
    def recognize(self, image_path: Union[str, Path]) -> Dict:
        """
        Recognize text using EasyOCR
        
        Args:
            image_path: Path to image file
            
        Returns:
            Dictionary with text, confidence, and bounding boxes
        """
        try:
            logger.info(f"Starting EasyOCR recognition on {image_path}")
            # easyocr returns list of (bbox, text, prob)
            # bbox is list of 4 points [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            results = self.reader.readtext(str(image_path))
            logger.info(f"EasyOCR recognition completed. Found {len(results)} text segments.")
            
            lines = []
            full_text = []
            
            for (bbox, text, prob) in results:
                lines.append({
                    "text": text,
                    "confidence": float(prob),
                    "bbox": [
                        [int(p[0]), int(p[1])] for p in bbox
                    ]
                })
                full_text.append(text)
                
            return {
                "success": True,
                "text": reconstruct_layout(lines),
                "lines": lines,
                "engine": "easyocr"
            }
            
        except Exception as e:
            logger.error(f"EasyOCR recognition failed: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "engine": "easyocr"
            }


class OCRService:
    """Main OCR service with engine selection"""
    
    def __init__(self, engine_type: str = "paddleocr", **kwargs):
        """
        Initialize OCR service
        
        Args:
            engine_type: Type of OCR engine ('paddleocr', 'tesseract', 'easyocr')
            **kwargs: Additional arguments for the engine
        """
        self.engine_type = engine_type.lower()
        
        if self.engine_type == "paddleocr":
            self.engine = PaddleOCREngine(**kwargs)
        elif self.engine_type == "tesseract":
            self.engine = TesseractOCREngine(**kwargs)
        elif self.engine_type == "easyocr":
            self.engine = EasyOCREngine(**kwargs)
        else:
            raise ValueError(
                f"Unknown OCR engine: {engine_type}. "
                "Supported engines: 'paddleocr', 'tesseract', 'easyocr'"
            )
        
        logger.info(f"OCR Service initialized with {self.engine_type} engine")
    
    def process_image(self, image_path: Union[str, Path]) -> Dict:
        """
        Process image and extract text
        
        Args:
            image_path: Path to image file
            
        Returns:
            OCR result dictionary
        """
        if not Path(image_path).exists():
            return {
                "success": False,
                "error": f"Image file not found: {image_path}"
            }
        
        return self.engine.recognize(image_path)
