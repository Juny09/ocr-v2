"""
Pydantic models for API request/response validation
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any


class OCRLine(BaseModel):
    """Single line of OCR result"""
    text: str = Field(..., description="Recognized text")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    bbox: Optional[List] = Field(None, description="Bounding box coordinates")


class OCRResponse(BaseModel):
    """OCR API response"""
    success: bool = Field(..., description="Whether OCR was successful")
    text: str = Field(default="", description="Full recognized text")
    lines: List[OCRLine] = Field(default=[], description="Individual text lines")
    engine: str = Field(..., description="OCR engine used")
    error: Optional[str] = Field(None, description="Error message if failed")


class ErrorResponse(BaseModel):
    """Error response"""
    detail: str = Field(..., description="Error detail message")


class HealthResponse(BaseModel):
    """Health check response"""
    status: str = Field(..., description="Service status")
    ocr_engine: str = Field(..., description="Current OCR engine")
    version: str = Field(default="1.0.0", description="API version")
