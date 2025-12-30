"""
Image preprocessing utilities for OCR
"""
import cv2
import numpy as np
from PIL import Image
from typing import Union
from pathlib import Path


class ImageProcessor:
    """Image preprocessing for better OCR results"""
    
    @staticmethod
    def crop(image: np.ndarray, x: int, y: int, w: int, h: int) -> np.ndarray:
        """
        Crop image to specified region
        
        Args:
            image: Input image
            x: X coordinate of top-left corner
            y: Y coordinate of top-left corner
            w: Width of crop area
            h: Height of crop area
            
        Returns:
            Cropped image
        """
        height, width = image.shape[:2]
        
        # Ensure coordinates are within bounds
        x = max(0, min(x, width))
        y = max(0, min(y, height))
        w = max(0, min(w, width - x))
        h = max(0, min(h, height - y))
        
        if w == 0 or h == 0:
            return image
            
        return image[y:y+h, x:x+w]

    @staticmethod
    def load_image(image_path: Union[str, Path]) -> np.ndarray:
        """
        Load image from file path
        
        Args:
            image_path: Path to the image file
            
        Returns:
            numpy array of the image
        """
        image = cv2.imread(str(image_path))
        if image is None:
            raise ValueError(f"Failed to load image from {image_path}")
        return image
    
    @staticmethod
    def save_image(image: np.ndarray, output_path: Union[str, Path]) -> None:
        """
        Save image to file
        
        Args:
            image: Image array
            output_path: Output file path
        """
        cv2.imwrite(str(output_path), image)

    @staticmethod
    def convert_to_grayscale(image: np.ndarray) -> np.ndarray:
        """
        Convert image to grayscale
        
        Args:
            image: Input image as numpy array
            
        Returns:
            Grayscale image
        """
        if len(image.shape) == 3:
            return cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        return image
    
    @staticmethod
    def apply_threshold(image: np.ndarray, method: str = "otsu") -> np.ndarray:
        """
        Apply thresholding to image
        
        Args:
            image: Grayscale image
            method: Thresholding method ('otsu' or 'adaptive')
            
        Returns:
            Binary image
        """
        if method == "otsu":
            _, binary = cv2.threshold(
                image, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU
            )
        elif method == "adaptive":
            binary = cv2.adaptiveThreshold(
                image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY, 11, 2
            )
        else:
            raise ValueError(f"Unknown threshold method: {method}")
        
        return binary
    
    @staticmethod
    def denoise(image: np.ndarray) -> np.ndarray:
        """
        Remove noise from image
        
        Args:
            image: Input image
            
        Returns:
            Denoised image
        """
        return cv2.fastNlMeansDenoising(image, None, 10, 7, 21)
    
    @staticmethod
    def deskew(image: np.ndarray) -> np.ndarray:
        """
        Deskew the image
        
        Args:
            image: Input image
            
        Returns:
            Deskewed image
        """
        coords = np.column_stack(np.where(image > 0))
        if len(coords) == 0:
            return image
            
        angle = cv2.minAreaRect(coords)[-1]
        
        if angle < -45:
            angle = -(90 + angle)
        else:
            angle = -angle
            
        (h, w) = image.shape[:2]
        center = (w // 2, h // 2)
        M = cv2.getRotationMatrix2D(center, angle, 1.0)
        rotated = cv2.warpAffine(
            image, M, (w, h),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE
        )
        
        return rotated
    
    @classmethod
    def preprocess(
        cls,
        image_path: Union[str, Path],
        grayscale: bool = True,
        threshold: bool = True,
        denoise_image: bool = True,
        deskew_image: bool = False
    ) -> np.ndarray:
        """
        Complete preprocessing pipeline
        
        Args:
            image_path: Path to image file
            grayscale: Whether to convert to grayscale
            threshold: Whether to apply thresholding
            denoise_image: Whether to denoise
            deskew_image: Whether to deskew
            
        Returns:
            Preprocessed image
        """
        # Load image
        image = cls.load_image(image_path)
        
        # Convert to grayscale
        if grayscale:
            image = cls.convert_to_grayscale(image)
        
        # Denoise
        if denoise_image and len(image.shape) == 2:
            image = cls.denoise(image)
        
        # Deskew
        if deskew_image and len(image.shape) == 2:
            image = cls.deskew(image)
        
        # Apply thresholding
        if threshold and len(image.shape) == 2:
            image = cls.apply_threshold(image, method="otsu")
        
        return image
    
    @staticmethod
    def save_image(image: np.ndarray, output_path: Union[str, Path]) -> None:
        """
        Save processed image
        
        Args:
            image: Image to save
            output_path: Output file path
        """
        cv2.imwrite(str(output_path), image)
