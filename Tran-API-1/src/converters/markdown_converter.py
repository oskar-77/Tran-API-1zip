"""Markdown converter for unified documents."""

from typing import Optional
from src.converters.base_converter import BaseConverter
from src.schemas.document import (
    Document, Page, TextDirection,
    HeadingBlock, ParagraphBlock, ImageBlock, TableBlock, ListBlock, LinkBlock
)


class MarkdownConverter(BaseConverter):
    """Converter for Markdown output."""
    
    OUTPUT_FORMAT = "markdown"
    OUTPUT_EXTENSION = ".md"
    
    def __init__(self, document: Document, include_frontmatter: bool = True,
                 embed_images: bool = False):
        """Initialize Markdown converter.
        
        Args:
            document: Unified document model
            include_frontmatter: Include YAML frontmatter with metadata
            embed_images: Embed images as base64 or use file paths
        """
        super().__init__(document)
        self.include_frontmatter = include_frontmatter
        self.embed_images = embed_images
    
    def convert(self) -> str:
        """Convert document to Markdown string."""
        parts = []
        
        if self.include_frontmatter:
            frontmatter = self._generate_frontmatter()
            if frontmatter:
                parts.append(frontmatter)
        
        if self.document.title:
            parts.append(f"# {self.document.title}")
            parts.append("")
        
        for page in self.document.pages:
            page_content = self._convert_page(page)
            if page_content:
                parts.append(page_content)
        
        return '\n'.join(parts)
    
    def _generate_frontmatter(self) -> str:
        """Generate YAML frontmatter from metadata."""
        meta = self.document.metadata
        lines = ['---']
        
        if meta.title:
            lines.append(f'title: "{self._escape_yaml(meta.title)}"')
        if meta.author:
            lines.append(f'author: "{self._escape_yaml(meta.author)}"')
        if meta.subject:
            lines.append(f'description: "{self._escape_yaml(meta.subject)}"')
        if meta.keywords:
            keywords = ', '.join(meta.keywords)
            lines.append(f'keywords: "{self._escape_yaml(keywords)}"')
        if meta.created_date:
            lines.append(f'date: "{meta.created_date.isoformat()}"')
        if meta.source_format:
            lines.append(f'source_format: "{meta.source_format}"')
        
        if self.document.direction == TextDirection.RTL:
            lines.append('dir: rtl')
        
        lines.append('---')
        lines.append('')
        
        if len(lines) <= 3:
            return ''
        
        return '\n'.join(lines)
    
    def _convert_page(self, page: Page) -> str:
        """Convert a page to Markdown."""
        parts = []
        
        if len(self.document.pages) > 1:
            if page.title:
                parts.append(f"## {page.title}")
            else:
                parts.append(f"## Page {page.page_number}")
            parts.append("")
        
        for block in page.blocks:
            block_content = self._convert_block(block)
            if block_content:
                parts.append(block_content)
                parts.append("")
        
        if len(self.document.pages) > 1:
            parts.append("---")
            parts.append("")
        
        return '\n'.join(parts)
    
    def _convert_block(self, block) -> str:
        """Convert a block to Markdown."""
        if isinstance(block, HeadingBlock):
            return self._convert_heading(block)
        elif isinstance(block, ParagraphBlock):
            return self._convert_paragraph(block)
        elif isinstance(block, ImageBlock):
            return self._convert_image(block)
        elif isinstance(block, TableBlock):
            return self._convert_table(block)
        elif isinstance(block, ListBlock):
            return self._convert_list(block)
        elif isinstance(block, LinkBlock):
            return self._convert_link(block)
        return ''
    
    def _convert_heading(self, block: HeadingBlock) -> str:
        """Convert heading block to Markdown."""
        prefix = '#' * block.level
        text = block.text
        
        if block.links:
            text = self._apply_links(text, block.links)
        
        return f"{prefix} {text}"
    
    def _convert_paragraph(self, block: ParagraphBlock) -> str:
        """Convert paragraph block to Markdown."""
        text = block.text
        
        if block.links:
            text = self._apply_links(text, block.links)
        
        if block.is_bold and block.is_italic:
            text = f"***{text}***"
        elif block.is_bold:
            text = f"**{text}**"
        elif block.is_italic:
            text = f"*{text}*"
        
        if block.direction == TextDirection.RTL:
            text = f'<div dir="rtl">\n\n{text}\n\n</div>'
        
        return text
    
    def _convert_image(self, block: ImageBlock) -> str:
        """Convert image block to Markdown."""
        alt_text = block.alt_text or block.caption or 'Image'
        
        if self.embed_images and block.image_data:
            src = block.image_data
        elif block.image_path:
            src = block.image_path
        else:
            src = f"image_{block.image_id}"
        
        result = f"![{alt_text}]({src})"
        
        if block.caption:
            result += f"\n\n*{block.caption}*"
        
        return result
    
    def _convert_table(self, block: TableBlock) -> str:
        """Convert table block to Markdown."""
        if not block.rows:
            return ''
        
        parts = []
        
        if block.caption:
            parts.append(f"**{block.caption}**")
            parts.append("")
        
        max_cols = max(len(row.cells) for row in block.rows)
        col_widths = [3] * max_cols
        
        for row in block.rows:
            for i, cell in enumerate(row.cells):
                if i < max_cols:
                    col_widths[i] = max(col_widths[i], len(cell.content) + 2)
        
        for row_idx, row in enumerate(block.rows):
            cells = []
            for i in range(max_cols):
                if i < len(row.cells):
                    content = row.cells[i].content or ''
                else:
                    content = ''
                cells.append(content)
            
            line = '| ' + ' | '.join(cells) + ' |'
            parts.append(line)
            
            if row_idx == 0:
                separator = '| ' + ' | '.join(['-' * max(3, len(c)) for c in cells]) + ' |'
                parts.append(separator)
        
        return '\n'.join(parts)
    
    def _convert_list(self, block: ListBlock) -> str:
        """Convert list block to Markdown."""
        parts = []
        
        for i, item in enumerate(block.items):
            if block.is_ordered:
                parts.append(f"{i + 1}. {item}")
            else:
                parts.append(f"- {item}")
        
        return '\n'.join(parts)
    
    def _convert_link(self, block: LinkBlock) -> str:
        """Convert link block to Markdown."""
        return f"[{block.text}]({block.url})"
    
    def _apply_links(self, text: str, links: list) -> str:
        """Apply links to text content."""
        for link in reversed(links):
            if link.start_index is not None and link.end_index is not None:
                before = text[:link.start_index]
                after = text[link.end_index:]
                link_md = f"[{link.text}]({link.url})"
                text = before + link_md + after
            else:
                text = text.replace(link.text, f"[{link.text}]({link.url})", 1)
        return text
    
    def _escape_yaml(self, text: str) -> str:
        """Escape text for YAML."""
        if not text:
            return ''
        return text.replace('"', '\\"').replace('\n', ' ')
