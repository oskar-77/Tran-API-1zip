"""Word document extractor using python-docx."""

from pathlib import Path
from typing import Optional
from docx import Document as DocxDocument
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

from src.extractors.base_extractor import BaseExtractor
from src.schemas.document import (
    Document, Page, Metadata, TextDirection,
    HeadingBlock, ParagraphBlock, ImageBlock, TableBlock, ListBlock,
    TableRow, TableCell, Link
)
from src.utils.text_utils import detect_text_direction, clean_text
from src.utils.image_utils import image_to_base64, generate_image_id


class DocxExtractor(BaseExtractor):
    """Extractor for Word documents using python-docx."""
    
    SUPPORTED_EXTENSIONS = ['.docx']
    
    def extract(self) -> Document:
        """Extract content from Word document."""
        doc = DocxDocument(str(self.file_path))
        
        metadata = self._extract_metadata(doc)
        blocks = []
        
        for element in doc.element.body:
            if element.tag.endswith('p'):
                para = Paragraph(element, doc)
                block = self._extract_paragraph(para)
                if block:
                    blocks.append(block)
            elif element.tag.endswith('tbl'):
                table = Table(element, doc)
                block = self._extract_table(table)
                if block:
                    blocks.append(block)
        
        images = self._extract_images(doc)
        blocks.extend(images)
        
        all_text = " ".join([
            b.text for b in blocks if hasattr(b, 'text')
        ])
        direction = TextDirection(detect_text_direction(all_text))
        
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
    
    def _extract_metadata(self, doc: DocxDocument) -> Metadata:
        """Extract metadata from Word document."""
        base_metadata = self._create_base_metadata()
        core_props = doc.core_properties
        
        return Metadata(
            title=core_props.title or base_metadata.source_filename,
            author=core_props.author,
            created_date=core_props.created,
            modified_date=core_props.modified or base_metadata.modified_date,
            subject=core_props.subject,
            keywords=self._parse_keywords(core_props.keywords),
            source_format='docx',
            source_filename=base_metadata.source_filename
        )
    
    def _parse_keywords(self, keywords_str: Optional[str]) -> list[str]:
        """Parse keywords string into list."""
        if not keywords_str:
            return []
        
        keywords = [k.strip() for k in keywords_str.split(',')]
        return [k for k in keywords if k]
    
    def _extract_paragraph(self, para: Paragraph):
        """Extract paragraph or heading from document."""
        text = clean_text(para.text)
        if not text:
            return None
        
        direction = TextDirection(detect_text_direction(text))
        links = self._extract_links_from_paragraph(para)
        
        style_name = para.style.name.lower() if para.style else ""
        
        if 'heading' in style_name:
            level = self._get_heading_level(style_name)
            return HeadingBlock(
                level=level,
                text=text,
                direction=direction,
                links=links
            )
        
        if 'list' in style_name or self._is_list_paragraph(para):
            return ListBlock(
                items=[text],
                is_ordered='number' in style_name or 'decimal' in style_name,
                direction=direction
            )
        
        is_bold = any(run.bold for run in para.runs if run.bold)
        is_italic = any(run.italic for run in para.runs if run.italic)
        
        return ParagraphBlock(
            text=text,
            direction=direction,
            links=links,
            is_bold=is_bold,
            is_italic=is_italic
        )
    
    def _get_heading_level(self, style_name: str) -> int:
        """Get heading level from style name."""
        for i in range(1, 7):
            if str(i) in style_name:
                return i
        return 1
    
    def _is_list_paragraph(self, para: Paragraph) -> bool:
        """Check if paragraph is a list item."""
        try:
            numPr = para._element.find(qn('w:numPr'))
            return numPr is not None
        except Exception:
            return False
    
    def _extract_links_from_paragraph(self, para: Paragraph) -> list[Link]:
        """Extract hyperlinks from paragraph."""
        links = []
        
        try:
            for hyperlink in para._element.findall(qn('w:hyperlink')):
                rId = hyperlink.get(qn('r:id'))
                if rId:
                    rel = para.part.rels.get(rId)
                    if rel:
                        url = rel.target_ref
                        text_elem = hyperlink.find(qn('w:t'))
                        text = text_elem.text if text_elem is not None else url
                        
                        links.append(Link(
                            text=text or url,
                            url=url
                        ))
        except Exception:
            pass
        
        return links
    
    def _extract_table(self, table: Table) -> Optional[TableBlock]:
        """Extract table from document."""
        rows = []
        
        for row_index, row in enumerate(table.rows):
            cells = []
            for cell in row.cells:
                cell_text = clean_text(cell.text)
                cells.append(TableCell(
                    content=cell_text,
                    is_header=(row_index == 0)
                ))
            
            rows.append(TableRow(
                cells=cells,
                is_header_row=(row_index == 0)
            ))
        
        if not rows:
            return None
        
        return TableBlock(
            rows=rows,
            has_header=True,
            row_count=len(rows),
            column_count=len(rows[0].cells) if rows else 0
        )
    
    def _extract_images(self, doc: DocxDocument) -> list[ImageBlock]:
        """Extract images from document."""
        images = []
        
        try:
            for rel_id, rel in doc.part.rels.items():
                if "image" in rel.reltype:
                    try:
                        image_data = rel.target_part.blob
                        image_format = rel.target_ref.split('.')[-1].lower()
                        
                        image_id = generate_image_id()
                        base64_data = image_to_base64(image_data, image_format)
                        
                        images.append(ImageBlock(
                            image_id=image_id,
                            image_data=base64_data,
                            image_format=image_format
                        ))
                    except Exception:
                        continue
        except Exception:
            pass
        
        return images
