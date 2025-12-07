"""Plain text file extractor."""

from pathlib import Path
import re

from src.extractors.base_extractor import BaseExtractor
from src.schemas.document import (
    Document, Page, Metadata, TextDirection,
    HeadingBlock, ParagraphBlock, ListBlock, Link
)
from src.utils.text_utils import (
    detect_text_direction, clean_text, split_into_paragraphs,
    count_words, extract_urls
)


class TextExtractor(BaseExtractor):
    """Extractor for plain text files."""
    
    SUPPORTED_EXTENSIONS = ['.txt']
    
    def extract(self) -> Document:
        """Extract content from text file."""
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
        
        return Document(
            title=self.file_path.stem,
            metadata=metadata,
            pages=[page],
            direction=direction
        )
    
    def _extract_metadata(self, content: str) -> Metadata:
        """Extract metadata from text content."""
        base_metadata = self._create_base_metadata()
        
        lines = content.split('\n')
        title = lines[0].strip() if lines else None
        
        if title and len(title) > 100:
            title = None
        
        return Metadata(
            title=title or base_metadata.source_filename,
            word_count=count_words(content),
            source_format='txt',
            source_filename=base_metadata.source_filename,
            modified_date=base_metadata.modified_date
        )
    
    def _parse_content(self, content: str) -> list:
        """Parse text content into blocks."""
        blocks = []
        
        paragraphs = split_into_paragraphs(content)
        
        for i, para_text in enumerate(paragraphs):
            para_text = clean_text(para_text)
            if not para_text:
                continue
            
            direction = TextDirection(detect_text_direction(para_text))
            
            if self._is_heading(para_text, i == 0):
                level = 1 if i == 0 else 2
                blocks.append(HeadingBlock(
                    level=level,
                    text=para_text,
                    direction=direction
                ))
            elif self._is_list(para_text):
                items = self._parse_list(para_text)
                is_ordered = self._is_ordered_list(para_text)
                blocks.append(ListBlock(
                    items=items,
                    is_ordered=is_ordered,
                    direction=direction
                ))
            else:
                links = self._extract_links(para_text)
                blocks.append(ParagraphBlock(
                    text=para_text,
                    direction=direction,
                    links=links
                ))
        
        return blocks
    
    def _is_heading(self, text: str, is_first: bool) -> bool:
        """Check if text looks like a heading."""
        if len(text) > 100:
            return False
        
        if '\n' in text:
            return False
        
        if is_first and len(text) < 80:
            return True
        
        if text.isupper() and len(text) < 60:
            return True
        
        return False
    
    def _is_list(self, text: str) -> bool:
        """Check if text is a list."""
        lines = text.split('\n')
        if len(lines) < 2:
            return False
        
        list_patterns = [
            r'^\s*[-*•]\s+',
            r'^\s*\d+[.)]\s+',
            r'^\s*[a-zA-Z][.)]\s+',
        ]
        
        matches = 0
        for line in lines:
            for pattern in list_patterns:
                if re.match(pattern, line):
                    matches += 1
                    break
        
        return matches >= len(lines) * 0.5
    
    def _is_ordered_list(self, text: str) -> bool:
        """Check if list is ordered."""
        lines = text.split('\n')
        for line in lines:
            if re.match(r'^\s*\d+[.)]\s+', line):
                return True
            if re.match(r'^\s*[a-zA-Z][.)]\s+', line):
                return True
        return False
    
    def _parse_list(self, text: str) -> list[str]:
        """Parse list text into items."""
        lines = text.split('\n')
        items = []
        
        for line in lines:
            item = re.sub(r'^\s*[-*•\d.)\s]+', '', line)
            item = item.strip()
            if item:
                items.append(item)
        
        return items
    
    def _extract_links(self, text: str) -> list[Link]:
        """Extract URLs from text."""
        url_data = extract_urls(text)
        links = []
        
        for url, start, end in url_data:
            links.append(Link(
                text=url,
                url=url,
                start_index=start,
                end_index=end
            ))
        
        return links
