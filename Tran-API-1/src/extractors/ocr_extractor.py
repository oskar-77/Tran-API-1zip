"""OCR extractor for images and scanned PDFs with enhanced Arabic support."""

import os
import cv2
import numpy as np
import pytesseract
from pathlib import Path
from typing import Optional, List, Tuple
from PIL import Image
from pdf2image import convert_from_path
from bidi.algorithm import get_display
from arabic_reshaper import reshape

from src.extractors.base_extractor import BaseExtractor
from src.schemas.document import (
    Document, Page, Metadata, TextDirection, BoundingBox, TextStyle,
    PositionedTextBlock, TableBlock, TableRow, TableCell, OCRResult
)
from src.utils.text_utils import (
    detect_text_direction, clean_text, is_arabic_text, 
    clean_arabic_text, get_text_metrics, fix_arabic_text
)
from src.utils.image_utils import generate_image_id


class OCRExtractor(BaseExtractor):
    """Extractor for images and scanned PDFs using Tesseract OCR."""
    
    SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.tiff', '.tif', '.bmp', '.gif', '.webp']
    
    def __init__(self, file_path: str, languages: List[str] = None):
        super().__init__(file_path)
        self.languages = languages or ['ara', 'eng']
        self.lang_string = '+'.join(self.languages)
        
    def extract(self) -> Document:
        """Extract content from image using OCR."""
        image = Image.open(str(self.file_path))
        
        preprocessed = self._preprocess_image(image)
        
        ocr_result = self._perform_ocr(preprocessed)
        
        metadata = self._extract_metadata(image, ocr_result)
        
        blocks = []
        for text_block in ocr_result.blocks:
            blocks.append(text_block)
        for table in ocr_result.tables:
            blocks.append(table)
        
        direction = TextDirection.RTL if ocr_result.is_rtl else TextDirection.LTR
        
        page = Page(
            page_number=1,
            blocks=blocks,
            direction=direction
        )
        
        return Document(
            title=metadata.title or self.file_path.stem,
            metadata=metadata,
            pages=[page],
            direction=direction
        )
    
    def _preprocess_image(self, image: Image.Image) -> np.ndarray:
        """Preprocess image for better OCR accuracy."""
        img_array = np.array(image)
        
        if len(img_array.shape) == 3:
            gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
        else:
            gray = img_array
        
        denoised = cv2.fastNlMeansDenoising(gray, None, 10, 7, 21)
        
        thresh = cv2.adaptiveThreshold(
            denoised, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, 
            cv2.THRESH_BINARY, 11, 2
        )
        
        kernel = np.ones((1, 1), np.uint8)
        processed = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel)
        
        return processed
    
    def _perform_ocr(self, image: np.ndarray) -> OCRResult:
        """Perform OCR on preprocessed image."""
        custom_config = r'--oem 3 --psm 6'
        
        data = pytesseract.image_to_data(
            image, lang=self.lang_string, 
            config=custom_config,
            output_type=pytesseract.Output.DICT
        )
        
        positioned_blocks = []
        confidences = []
        all_text_parts = []
        
        n_boxes = len(data['level'])
        current_block_text = []
        current_block_info = None
        
        for i in range(n_boxes):
            level = data['level'][i]
            text = data['text'][i].strip()
            conf = float(data['conf'][i])
            
            if not text or conf < 0:
                continue
            
            x, y, w, h = data['left'][i], data['top'][i], data['width'][i], data['height'][i]
            
            if level == 5:
                all_text_parts.append(text)
                confidences.append(conf)
                
                if text:
                    text_is_arabic = is_arabic_text(text)
                    display_text = fix_arabic_text(text) if text_is_arabic else text
                    direction = TextDirection.RTL if text_is_arabic else TextDirection(detect_text_direction(text))
                    font_size = max(8, h * 0.75)
                    
                    block = PositionedTextBlock(
                        text=display_text,
                        bbox=BoundingBox(x=x, y=y, width=w, height=h),
                        style=TextStyle(font_size=font_size),
                        direction=direction,
                        confidence=conf / 100.0,
                        language='ar' if text_is_arabic else 'en'
                    )
                    positioned_blocks.append(block)
        
        full_text = pytesseract.image_to_string(
            image, lang=self.lang_string, config=custom_config
        )
        full_text = clean_text(full_text)
        
        if is_arabic_text(full_text):
            try:
                reshaped = reshape(full_text)
                full_text = get_display(reshaped)
            except Exception:
                pass
        
        tables = self._extract_tables_from_image(image)
        
        metrics = get_text_metrics(full_text)
        avg_confidence = sum(confidences) / len(confidences) if confidences else 0
        
        return OCRResult(
            text=full_text,
            confidence=avg_confidence / 100.0,
            language='ar' if metrics['is_rtl'] else 'en',
            word_count=metrics['word_count'],
            blocks=positioned_blocks,
            tables=tables,
            is_rtl=metrics['is_rtl']
        )
    
    def _extract_tables_from_image(self, image: np.ndarray) -> List[TableBlock]:
        """Extract tables from image using contour detection."""
        tables = []
        
        try:
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image.copy()
            
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (40, 1))
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel, iterations=2)
            
            vertical_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 40))
            vertical_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vertical_kernel, iterations=2)
            
            table_mask = cv2.add(horizontal_lines, vertical_lines)
            
            contours, _ = cv2.findContours(table_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                
                if w > 100 and h > 50:
                    table_region = image[y:y+h, x:x+w]
                    table_block = self._ocr_table_region(table_region)
                    if table_block:
                        tables.append(table_block)
        except Exception:
            pass
        
        return tables
    
    def _ocr_table_region(self, table_image: np.ndarray) -> Optional[TableBlock]:
        """OCR a table region and structure the results."""
        try:
            if len(table_image.shape) == 3:
                gray = cv2.cvtColor(table_image, cv2.COLOR_BGR2GRAY)
            else:
                gray = table_image
            
            thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[1]
            
            horizontal_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (30, 1))
            horizontal_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horizontal_kernel)
            
            horizontal_sum = np.sum(horizontal_lines, axis=1)
            row_boundaries = []
            in_line = False
            line_start = 0
            
            for i, val in enumerate(horizontal_sum):
                if val > table_image.shape[1] * 128:
                    if not in_line:
                        in_line = True
                        line_start = i
                else:
                    if in_line:
                        row_boundaries.append((line_start + i) // 2)
                        in_line = False
            
            if not row_boundaries:
                row_boundaries = [0, table_image.shape[0] // 2, table_image.shape[0]]
            
            rows = []
            for i in range(len(row_boundaries) - 1):
                y1 = row_boundaries[i]
                y2 = row_boundaries[i + 1]
                
                row_image = table_image[y1:y2, :]
                text = pytesseract.image_to_string(
                    row_image, lang=self.lang_string, 
                    config='--psm 6'
                ).strip()
                
                if text:
                    cell_texts = text.split('\t') if '\t' in text else [text]
                    cells = []
                    for cell_text in cell_texts:
                        cells.append(TableCell(
                            content=clean_text(cell_text),
                            is_header=(i == 0)
                        ))
                    
                    rows.append(TableRow(
                        cells=cells,
                        is_header_row=(i == 0)
                    ))
            
            if rows:
                return TableBlock(
                    rows=rows,
                    has_header=True,
                    row_count=len(rows),
                    column_count=max(len(row.cells) for row in rows)
                )
        except Exception:
            pass
        
        return None
    
    def _extract_metadata(self, image: Image.Image, ocr_result: OCRResult) -> Metadata:
        """Extract metadata from image and OCR results."""
        base_metadata = self._create_base_metadata()
        
        language = 'ar' if ocr_result.is_rtl else 'en'
        
        return Metadata(
            title=base_metadata.source_filename,
            language=language,
            word_count=ocr_result.word_count,
            page_count=1,
            source_format='image',
            source_filename=base_metadata.source_filename
        )


class ScannedPDFExtractor(BaseExtractor):
    """Extractor for scanned PDFs using OCR."""
    
    SUPPORTED_EXTENSIONS = ['.pdf']
    
    def __init__(self, file_path: str, languages: List[str] = None, dpi: int = 300):
        super().__init__(file_path)
        self.languages = languages or ['ara', 'eng']
        self.lang_string = '+'.join(self.languages)
        self.dpi = dpi
    
    def extract(self) -> Document:
        """Extract content from scanned PDF using OCR."""
        images = convert_from_path(str(self.file_path), dpi=self.dpi)
        
        pages = []
        all_text = []
        total_confidence = 0
        
        for page_num, image in enumerate(images, 1):
            ocr_extractor = OCRExtractor.__new__(OCRExtractor)
            ocr_extractor.languages = self.languages
            ocr_extractor.lang_string = self.lang_string
            ocr_extractor.file_path = self.file_path
            
            preprocessed = ocr_extractor._preprocess_image(image)
            ocr_result = ocr_extractor._perform_ocr(preprocessed)
            
            blocks = list(ocr_result.blocks) + list(ocr_result.tables)
            
            direction = TextDirection.RTL if ocr_result.is_rtl else TextDirection.LTR
            
            page = Page(
                page_number=page_num,
                blocks=blocks,
                direction=direction
            )
            pages.append(page)
            all_text.append(ocr_result.text)
            total_confidence += ocr_result.confidence
        
        combined_text = '\n\n'.join(all_text)
        metrics = get_text_metrics(combined_text)
        
        metadata = self._create_base_metadata()
        metadata.page_count = len(pages)
        metadata.word_count = metrics['word_count']
        metadata.language = 'ar' if metrics['is_rtl'] else 'en'
        metadata.source_format = 'scanned_pdf'
        
        direction = TextDirection.RTL if metrics['is_rtl'] else TextDirection.LTR
        
        return Document(
            title=metadata.title or self.file_path.stem,
            metadata=metadata,
            pages=pages,
            direction=direction
        )
    
    def is_scanned_pdf(self) -> bool:
        """Check if PDF is scanned (image-based) rather than text-based."""
        try:
            import fitz
            doc = fitz.open(str(self.file_path))
            
            text_pages = 0
            for page in doc:
                text = page.get_text().strip()
                if len(text) > 50:
                    text_pages += 1
            
            doc.close()
            return text_pages < len(doc) * 0.3
        except Exception:
            return True


def extract_from_image(
    file_path: str, 
    languages: List[str] = None
) -> OCRResult:
    """
    Convenience function to extract text from an image file.
    
    Args:
        file_path: Path to the image file
        languages: List of language codes (default: ['ara', 'eng'])
    
    Returns:
        OCRResult with extracted text and metadata
    """
    extractor = OCRExtractor(file_path, languages)
    
    image = Image.open(file_path)
    preprocessed = extractor._preprocess_image(image)
    
    return extractor._perform_ocr(preprocessed)


def extract_from_scanned_pdf(
    file_path: str, 
    languages: List[str] = None,
    dpi: int = 300
) -> Document:
    """
    Convenience function to extract text from a scanned PDF.
    
    Args:
        file_path: Path to the PDF file
        languages: List of language codes (default: ['ara', 'eng'])
        dpi: Resolution for PDF to image conversion
    
    Returns:
        Document with extracted content
    """
    extractor = ScannedPDFExtractor(file_path, languages, dpi)
    return extractor.extract()
