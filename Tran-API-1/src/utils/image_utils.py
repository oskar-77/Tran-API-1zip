"""Image utility functions for document processing."""

import base64
import io
import os
import uuid
from typing import Optional, Tuple
from PIL import Image


def image_to_base64(image_data: bytes, format: str = "PNG") -> str:
    """Convert image bytes to base64 string."""
    if not image_data:
        return ""
    
    encoded = base64.b64encode(image_data).decode('utf-8')
    mime_type = get_mime_type(format)
    return f"data:{mime_type};base64,{encoded}"


def base64_to_image(base64_str: str) -> Optional[bytes]:
    """Convert base64 string to image bytes."""
    if not base64_str:
        return None
    
    if ',' in base64_str:
        base64_str = base64_str.split(',')[1]
    
    try:
        return base64.b64decode(base64_str)
    except Exception:
        return None


def save_image(image_data: bytes, output_path: str, format: Optional[str] = None) -> str:
    """Save image bytes to file."""
    if not image_data:
        raise ValueError("No image data provided")
    
    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    
    try:
        img = Image.open(io.BytesIO(image_data))
        if format:
            img.save(output_path, format=format.upper())
        else:
            img.save(output_path)
        return output_path
    except Exception:
        with open(output_path, 'wb') as f:
            f.write(image_data)
        return output_path


def get_image_format(image_data: bytes) -> Optional[str]:
    """Detect image format from bytes."""
    if not image_data:
        return None
    
    try:
        img = Image.open(io.BytesIO(image_data))
        return img.format.lower() if img.format else None
    except Exception:
        return None


def get_image_dimensions(image_data: bytes) -> Optional[Tuple[int, int]]:
    """Get image dimensions (width, height) from bytes."""
    if not image_data:
        return None
    
    try:
        img = Image.open(io.BytesIO(image_data))
        return img.size
    except Exception:
        return None


def get_mime_type(format: str) -> str:
    """Get MIME type for image format."""
    format = format.lower()
    mime_types = {
        'png': 'image/png',
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'gif': 'image/gif',
        'bmp': 'image/bmp',
        'webp': 'image/webp',
        'tiff': 'image/tiff',
        'tif': 'image/tiff',
        'svg': 'image/svg+xml',
    }
    return mime_types.get(format, 'image/png')


def generate_image_id() -> str:
    """Generate unique image ID."""
    return f"img_{uuid.uuid4().hex[:8]}"


def resize_image(image_data: bytes, max_width: int = 800, max_height: int = 600) -> bytes:
    """Resize image while maintaining aspect ratio."""
    if not image_data:
        return image_data
    
    try:
        img = Image.open(io.BytesIO(image_data))
        original_format = img.format or 'PNG'
        
        if img.width <= max_width and img.height <= max_height:
            return image_data
        
        ratio = min(max_width / img.width, max_height / img.height)
        new_size = (int(img.width * ratio), int(img.height * ratio))
        
        img = img.resize(new_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        img.save(output, format=original_format)
        return output.getvalue()
    except Exception:
        return image_data


def convert_image_format(image_data: bytes, target_format: str = "PNG") -> bytes:
    """Convert image to different format."""
    if not image_data:
        return image_data
    
    try:
        img = Image.open(io.BytesIO(image_data))
        
        if img.mode in ('RGBA', 'LA') and target_format.upper() in ('JPEG', 'JPG'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            background.paste(img, mask=img.split()[-1])
            img = background
        
        output = io.BytesIO()
        img.save(output, format=target_format.upper())
        return output.getvalue()
    except Exception:
        return image_data
