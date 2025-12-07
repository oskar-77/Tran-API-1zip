"""Markdown file extractor."""

from pathlib import Path
import re
import markdown
from lxml import etree

from src.extractors.base_extractor import BaseExtractor
from src.schemas.document import (
    Document, Page, Metadata, TextDirection,
    HeadingBlock, ParagraphBlock, ImageBlock, TableBlock, ListBlock, LinkBlock,
    TableRow, TableCell, Link
)
from src.utils.text_utils import detect_text_direction, clean_text, count_words
from src.utils.image_utils import generate_image_id


class MarkdownExtractor(BaseExtractor):
    """Extractor for Markdown files."""
    
    SUPPORTED_EXTENSIONS = ['.md', '.markdown']
    
    def extract(self) -> Document:
        """Extract content from Markdown file."""
        with open(self.file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        metadata = self._extract_metadata(content)
        blocks = self._parse_content(content)
        
        direction = TextDirection(detect_text_direction(content))
        
        page = Page(
            page_number=1,
            blocks=blocks,
            direction=direction
        )
        
        title = None
        for block in blocks:
            if isinstance(block, HeadingBlock) and block.level == 1:
                title = block.text
                break
        
        return Document(
            title=title or self.file_path.stem,
            metadata=metadata,
            pages=[page],
            direction=direction
        )
    
    def _extract_metadata(self, content: str) -> Metadata:
        """Extract metadata from Markdown content."""
        base_metadata = self._create_base_metadata()
        
        title = None
        title_match = re.match(r'^#\s+(.+)$', content, re.MULTILINE)
        if title_match:
            title = title_match.group(1).strip()
        
        front_matter = {}
        fm_match = re.match(r'^---\s*\n(.+?)\n---\s*\n', content, re.DOTALL)
        if fm_match:
            fm_content = fm_match.group(1)
            for line in fm_content.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    front_matter[key.strip().lower()] = value.strip()
        
        return Metadata(
            title=front_matter.get('title') or title or base_metadata.source_filename,
            author=front_matter.get('author'),
            subject=front_matter.get('description'),
            word_count=count_words(content),
            source_format='md',
            source_filename=base_metadata.source_filename,
            modified_date=base_metadata.modified_date
        )
    
    def _parse_content(self, content: str) -> list:
        """Parse Markdown content into blocks."""
        blocks = []
        
        content = re.sub(r'^---\s*\n(.+?)\n---\s*\n', '', content, flags=re.DOTALL)
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
            if heading_match:
                level = len(heading_match.group(1))
                text = clean_text(heading_match.group(2))
                if text:
                    blocks.append(HeadingBlock(
                        level=level,
                        text=text,
                        direction=TextDirection(detect_text_direction(text))
                    ))
                i += 1
                continue
            
            image_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line)
            if image_match:
                alt_text = image_match.group(1)
                image_url = image_match.group(2)
                blocks.append(ImageBlock(
                    image_id=generate_image_id(),
                    alt_text=alt_text,
                    image_path=image_url,
                    caption=alt_text
                ))
                i += 1
                continue
            
            link_match = re.match(r'^\[([^\]]+)\]\(([^)]+)\)$', line.strip())
            if link_match:
                blocks.append(LinkBlock(
                    text=link_match.group(1),
                    url=link_match.group(2)
                ))
                i += 1
                continue
            
            if re.match(r'^\s*[-*+]\s+', line) or re.match(r'^\s*\d+[.)]\s+', line):
                items = []
                is_ordered = bool(re.match(r'^\s*\d+[.)]\s+', line))
                
                while i < len(lines) and (
                    re.match(r'^\s*[-*+]\s+', lines[i]) or 
                    re.match(r'^\s*\d+[.)]\s+', lines[i])
                ):
                    item = re.sub(r'^\s*[-*+\d.)\s]+', '', lines[i])
                    if item.strip():
                        items.append(clean_text(item))
                    i += 1
                
                if items:
                    all_text = ' '.join(items)
                    blocks.append(ListBlock(
                        items=items,
                        is_ordered=is_ordered,
                        direction=TextDirection(detect_text_direction(all_text))
                    ))
                continue
            
            if line.startswith('|'):
                table_lines = []
                while i < len(lines) and (lines[i].startswith('|') or re.match(r'^[\s|:-]+$', lines[i])):
                    table_lines.append(lines[i])
                    i += 1
                
                if table_lines:
                    table_block = self._parse_table(table_lines)
                    if table_block:
                        blocks.append(table_block)
                continue
            
            if line.strip():
                para_text = line
                i += 1
                while i < len(lines) and lines[i].strip() and not lines[i].startswith('#'):
                    if re.match(r'^\s*[-*+]\s+', lines[i]) or re.match(r'^\s*\d+[.)]\s+', lines[i]):
                        break
                    if lines[i].startswith('|'):
                        break
                    para_text += '\n' + lines[i]
                    i += 1
                
                para_text = clean_text(para_text)
                if para_text:
                    links = self._extract_links(para_text)
                    blocks.append(ParagraphBlock(
                        text=para_text,
                        direction=TextDirection(detect_text_direction(para_text)),
                        links=links
                    ))
                continue
            
            i += 1
        
        return blocks
    
    def _parse_table(self, table_lines: list[str]) -> TableBlock:
        """Parse Markdown table lines into TableBlock."""
        rows = []
        
        for line_index, line in enumerate(table_lines):
            if re.match(r'^[\s|:-]+$', line) and '-' in line:
                continue
            
            cells_text = line.strip('|').split('|')
            cells = []
            
            for cell_text in cells_text:
                cells.append(TableCell(
                    content=clean_text(cell_text),
                    is_header=(line_index == 0)
                ))
            
            if cells:
                rows.append(TableRow(
                    cells=cells,
                    is_header_row=(line_index == 0)
                ))
        
        if not rows:
            return None
        
        return TableBlock(
            rows=rows,
            has_header=True,
            row_count=len(rows),
            column_count=len(rows[0].cells) if rows else 0
        )
    
    def _extract_links(self, text: str) -> list[Link]:
        """Extract Markdown links from text."""
        links = []
        
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        for match in re.finditer(pattern, text):
            links.append(Link(
                text=match.group(1),
                url=match.group(2),
                start_index=match.start(),
                end_index=match.end()
            ))
        
        return links
