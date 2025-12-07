"""PDF document extractor using PyMuPDF."""

import fitz
from typing import Optional
from pathlib import Path
from datetime import datetime

from src.extractors.base_extractor import BaseExtractor
from src.schemas.document import (
    Document, Page, Metadata, TextDirection,
    HeadingBlock, ParagraphBlock, ImageBlock, TableBlock, LinkBlock,
    TableRow, TableCell, Link
)
from src.utils.text_utils import detect_text_direction, clean_text, is_heading
from src.utils.image_utils import image_to_base64, generate_image_id, get_image_format


class PDFExtractor(BaseExtractor):
    """Extractor for PDF documents using PyMuPDF."""
    
    SUPPORTED_EXTENSIONS = ['.pdf']
    
    def extract(self) -> Document:
        """Extract content from PDF document."""
        doc = fitz.open(str(self.file_path))
        
        try:
            metadata = self._extract_metadata(doc)
            pages = []
            
            for page_num in range(len(doc)):
                page = self._extract_page(doc[page_num], page_num + 1)
                pages.append(page)
            
            all_text = " ".join([
                block.text for page in pages for block in page.blocks 
                if hasattr(block, 'text')
            ])
            direction = TextDirection(detect_text_direction(all_text))
            
            return Document(
                title=metadata.title or self.file_path.stem,
                metadata=metadata,
                pages=pages,
                direction=direction
            )
        finally:
            doc.close()
    
    def _extract_metadata(self, doc: fitz.Document) -> Metadata:
        """Extract metadata from PDF."""
        base_metadata = self._create_base_metadata()
        pdf_metadata = doc.metadata
        
        created_date = None
        modified_date = base_metadata.modified_date
        
        if pdf_metadata.get('creationDate'):
            created_date = self._parse_pdf_date(pdf_metadata['creationDate'])
        if pdf_metadata.get('modDate'):
            modified_date = self._parse_pdf_date(pdf_metadata['modDate']) or modified_date
        
        return Metadata(
            title=pdf_metadata.get('title') or base_metadata.source_filename,
            author=pdf_metadata.get('author'),
            created_date=created_date,
            modified_date=modified_date,
            subject=pdf_metadata.get('subject'),
            keywords=self._parse_keywords(pdf_metadata.get('keywords', '')),
            page_count=len(doc),
            source_format='pdf',
            source_filename=base_metadata.source_filename
        )
    
    def _parse_pdf_date(self, date_str: str) -> Optional[datetime]:
        """Parse PDF date string."""
        if not date_str:
            return None
        
        try:
            if date_str.startswith('D:'):
                date_str = date_str[2:]
            date_str = date_str[:14]
            return datetime.strptime(date_str, '%Y%m%d%H%M%S')
        except (ValueError, IndexError):
            return None
    
    def _parse_keywords(self, keywords_str: str) -> list[str]:
        """Parse keywords string into list."""
        if not keywords_str:
            return []
        
        keywords = [k.strip() for k in keywords_str.split(',')]
        return [k for k in keywords if k]
    
    def _extract_page(self, page: fitz.Page, page_num: int) -> Page:
        """Extract content from a PDF page."""
        blocks = []
        
        text_blocks = self._extract_text_blocks(page)
        blocks.extend(text_blocks)
        
        images = self._extract_images(page)
        blocks.extend(images)
        
        links = self._extract_links(page)
        blocks.extend(links)
        
        tables = self._extract_tables(page)
        blocks.extend(tables)
        
        all_text = " ".join([b.text for b in text_blocks if hasattr(b, 'text')])
        direction = TextDirection(detect_text_direction(all_text))
        
        return Page(
            page_number=page_num,
            blocks=blocks,
            direction=direction
        )
    
    def _extract_text_blocks(self, page: fitz.Page) -> list:
        """Extract text blocks from page."""
        blocks = []
        
        text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
        
        for block in text_dict.get("blocks", []):
            if block.get("type") != 0:
                continue
            
            block_text = ""
            max_font_size = 0
            is_bold = False
            
            for line in block.get("lines", []):
                line_text = ""
                for span in line.get("spans", []):
                    span_text = span.get("text", "")
                    line_text += span_text
                    
                    font_size = span.get("size", 12)
                    if font_size > max_font_size:
                        max_font_size = font_size
                    
                    flags = span.get("flags", 0)
                    if flags & 2 ** 4:
                        is_bold = True
                
                block_text += line_text + "\n"
            
            block_text = clean_text(block_text)
            if not block_text:
                continue
            
            direction = TextDirection(detect_text_direction(block_text))
            
            if is_heading(block_text) and (max_font_size >= 14 or is_bold):
                level = self._determine_heading_level(max_font_size)
                blocks.append(HeadingBlock(
                    level=level,
                    text=block_text,
                    direction=direction,
                    position_hint=f"page_{page.number + 1}"
                ))
            else:
                blocks.append(ParagraphBlock(
                    text=block_text,
                    direction=direction,
                    is_bold=is_bold,
                    position_hint=f"page_{page.number + 1}"
                ))
        
        return blocks
    
    def _determine_heading_level(self, font_size: float) -> int:
        """Determine heading level based on font size."""
        if font_size >= 24:
            return 1
        elif font_size >= 20:
            return 2
        elif font_size >= 16:
            return 3
        elif font_size >= 14:
            return 4
        elif font_size >= 12:
            return 5
        return 6
    
    def _extract_images(self, page: fitz.Page) -> list[ImageBlock]:
        """Extract images from page."""
        images = []
        
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            try:
                xref = img[0]
                base_image = page.parent.extract_image(xref)
                
                if not base_image:
                    continue
                
                image_data = base_image["image"]
                image_format = base_image.get("ext", "png")
                
                image_id = generate_image_id()
                base64_data = image_to_base64(image_data, image_format)
                
                images.append(ImageBlock(
                    image_id=image_id,
                    image_data=base64_data,
                    image_format=image_format,
                    width=base_image.get("width"),
                    height=base_image.get("height"),
                    position_hint=f"page_{page.number + 1}_img_{img_index + 1}"
                ))
            except Exception:
                continue
        
        return images
    
    def _extract_links(self, page: fitz.Page) -> list[LinkBlock]:
        """Extract links from page."""
        links = []
        
        for link in page.get_links():
            if link.get("kind") == fitz.LINK_URI:
                uri = link.get("uri", "")
                if uri:
                    rect = link.get("from", fitz.Rect())
                    text = page.get_text("text", clip=rect).strip() or uri
                    
                    links.append(LinkBlock(
                        text=text,
                        url=uri,
                        position_hint=f"page_{page.number + 1}"
                    ))
        
        return links
    
    def _extract_tables(self, page: fitz.Page) -> list[TableBlock]:
        """Extract tables from page using PyMuPDF's table detection."""
        tables = []
        
        try:
            page_tables = page.find_tables()
            
            for table_index, table in enumerate(page_tables):
                rows = []
                table_data = table.extract()
                
                if not table_data:
                    continue
                
                for row_index, row_data in enumerate(table_data):
                    cells = []
                    for cell_content in row_data:
                        cell_text = str(cell_content) if cell_content else ""
                        cells.append(TableCell(
                            content=clean_text(cell_text),
                            is_header=(row_index == 0)
                        ))
                    
                    rows.append(TableRow(
                        cells=cells,
                        is_header_row=(row_index == 0)
                    ))
                
                if rows:
                    tables.append(TableBlock(
                        rows=rows,
                        has_header=True,
                        row_count=len(rows),
                        column_count=len(rows[0].cells) if rows else 0,
                        position_hint=f"page_{page.number + 1}_table_{table_index + 1}"
                    ))
        except Exception:
            pass
        
        return tables
