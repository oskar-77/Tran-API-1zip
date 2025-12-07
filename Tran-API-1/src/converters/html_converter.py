"""HTML converter for unified documents."""

from typing import Optional
from src.converters.base_converter import BaseConverter
from src.schemas.document import (
    Document, Page, TextDirection,
    HeadingBlock, ParagraphBlock, ImageBlock, TableBlock, ListBlock, LinkBlock
)


class HTMLConverter(BaseConverter):
    """Converter for HTML output."""
    
    OUTPUT_FORMAT = "html"
    OUTPUT_EXTENSION = ".html"
    
    def __init__(self, document: Document, include_styles: bool = True, 
                 embed_images: bool = True):
        """Initialize HTML converter.
        
        Args:
            document: Unified document model
            include_styles: Include CSS styles in output
            embed_images: Embed images as base64 or use links
        """
        super().__init__(document)
        self.include_styles = include_styles
        self.embed_images = embed_images
    
    def convert(self) -> str:
        """Convert document to HTML string."""
        html_parts = []
        
        html_parts.append('<!DOCTYPE html>')
        html_parts.append('<html lang="ar" dir="auto">')
        html_parts.append('<head>')
        html_parts.append('<meta charset="UTF-8">')
        html_parts.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
        
        title = self.document.title or "Document"
        html_parts.append(f'<title>{self._escape_html(title)}</title>')
        
        if self.document.metadata.author:
            html_parts.append(f'<meta name="author" content="{self._escape_html(self.document.metadata.author)}">')
        if self.document.metadata.subject:
            html_parts.append(f'<meta name="description" content="{self._escape_html(self.document.metadata.subject)}">')
        if self.document.metadata.keywords:
            keywords = ', '.join(self.document.metadata.keywords)
            html_parts.append(f'<meta name="keywords" content="{self._escape_html(keywords)}">')
        
        if self.include_styles:
            html_parts.append(self._get_styles())
        
        html_parts.append('</head>')
        
        dir_attr = self._get_direction_attr(self.document.direction)
        html_parts.append(f'<body{dir_attr}>')
        
        html_parts.append('<div class="document-container">')
        
        if self.document.title:
            html_parts.append(f'<h1 class="document-title">{self._escape_html(self.document.title)}</h1>')
        
        for page in self.document.pages:
            html_parts.append(self._convert_page(page))
        
        html_parts.append('</div>')
        html_parts.append('</body>')
        html_parts.append('</html>')
        
        return '\n'.join(html_parts)
    
    def _get_styles(self) -> str:
        """Get CSS styles for the document."""
        return '''<style>
:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --text-color: #333;
    --bg-color: #fff;
    --border-color: #ddd;
}

* {
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: #f5f5f5;
    margin: 0;
    padding: 20px;
}

.document-container {
    max-width: 900px;
    margin: 0 auto;
    background: var(--bg-color);
    padding: 40px;
    border-radius: 8px;
    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
}

.document-title {
    color: var(--primary-color);
    border-bottom: 3px solid var(--secondary-color);
    padding-bottom: 10px;
    margin-bottom: 30px;
}

.page {
    margin-bottom: 40px;
    padding-bottom: 20px;
    border-bottom: 1px solid var(--border-color);
}

.page:last-child {
    border-bottom: none;
}

.page-header {
    color: #666;
    font-size: 0.9em;
    margin-bottom: 20px;
}

h1, h2, h3, h4, h5, h6 {
    color: var(--primary-color);
    margin-top: 1.5em;
    margin-bottom: 0.5em;
}

h1 { font-size: 2em; }
h2 { font-size: 1.75em; }
h3 { font-size: 1.5em; }
h4 { font-size: 1.25em; }
h5 { font-size: 1.1em; }
h6 { font-size: 1em; }

p {
    margin: 1em 0;
    text-align: justify;
}

.rtl {
    direction: rtl;
    text-align: right;
}

.ltr {
    direction: ltr;
    text-align: left;
}

a {
    color: var(--secondary-color);
    text-decoration: none;
}

a:hover {
    text-decoration: underline;
}

img {
    max-width: 100%;
    height: auto;
    display: block;
    margin: 20px auto;
    border-radius: 4px;
}

.image-caption {
    text-align: center;
    color: #666;
    font-style: italic;
    margin-top: 10px;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 20px 0;
}

th, td {
    border: 1px solid var(--border-color);
    padding: 12px;
    text-align: left;
}

th {
    background-color: var(--primary-color);
    color: white;
}

tr:nth-child(even) {
    background-color: #f9f9f9;
}

ul, ol {
    margin: 1em 0;
    padding-left: 2em;
}

li {
    margin: 0.5em 0;
}

.bold {
    font-weight: bold;
}

.italic {
    font-style: italic;
}

@media print {
    body {
        background: white;
        padding: 0;
    }
    
    .document-container {
        box-shadow: none;
        padding: 20px;
    }
    
    .page {
        page-break-after: always;
    }
}

@media (max-width: 600px) {
    .document-container {
        padding: 20px;
    }
    
    table {
        font-size: 0.9em;
    }
    
    th, td {
        padding: 8px;
    }
}
</style>'''
    
    def _get_direction_attr(self, direction: TextDirection) -> str:
        """Get HTML direction attribute."""
        if direction == TextDirection.RTL:
            return ' dir="rtl" class="rtl"'
        elif direction == TextDirection.LTR:
            return ' dir="ltr" class="ltr"'
        return ''
    
    def _convert_page(self, page: Page) -> str:
        """Convert a page to HTML."""
        parts = []
        
        dir_attr = self._get_direction_attr(page.direction)
        parts.append(f'<div class="page" id="page-{page.page_number}"{dir_attr}>')
        
        if len(self.document.pages) > 1:
            title = page.title or f"Page {page.page_number}"
            parts.append(f'<div class="page-header">{self._escape_html(title)}</div>')
        
        for block in page.blocks:
            parts.append(self._convert_block(block))
        
        parts.append('</div>')
        
        return '\n'.join(parts)
    
    def _convert_block(self, block) -> str:
        """Convert a block to HTML."""
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
        """Convert heading block to HTML."""
        dir_attr = self._get_direction_attr(block.direction)
        text = self._escape_html(block.text)
        
        if block.links:
            text = self._apply_links(text, block.links)
        
        return f'<h{block.level}{dir_attr}>{text}</h{block.level}>'
    
    def _convert_paragraph(self, block: ParagraphBlock) -> str:
        """Convert paragraph block to HTML."""
        dir_attr = self._get_direction_attr(block.direction)
        text = self._escape_html(block.text)
        
        if block.links:
            text = self._apply_links(text, block.links)
        
        classes = []
        if block.is_bold:
            classes.append('bold')
        if block.is_italic:
            classes.append('italic')
        
        class_attr = f' class="{" ".join(classes)}"' if classes else ''
        
        return f'<p{dir_attr}{class_attr}>{text}</p>'
    
    def _convert_image(self, block: ImageBlock) -> str:
        """Convert image block to HTML."""
        parts = ['<figure>']
        
        if self.embed_images and block.image_data:
            src = block.image_data
        elif block.image_path:
            src = block.image_path
        else:
            return ''
        
        alt = self._escape_html(block.alt_text or block.caption or 'Image')
        parts.append(f'<img src="{src}" alt="{alt}">')
        
        if block.caption:
            parts.append(f'<figcaption class="image-caption">{self._escape_html(block.caption)}</figcaption>')
        
        parts.append('</figure>')
        
        return '\n'.join(parts)
    
    def _convert_table(self, block: TableBlock) -> str:
        """Convert table block to HTML."""
        parts = ['<table>']
        
        if block.caption:
            parts.append(f'<caption>{self._escape_html(block.caption)}</caption>')
        
        for row in block.rows:
            parts.append('<tr>')
            for cell in row.cells:
                tag = 'th' if cell.is_header else 'td'
                attrs = []
                if cell.colspan > 1:
                    attrs.append(f'colspan="{cell.colspan}"')
                if cell.rowspan > 1:
                    attrs.append(f'rowspan="{cell.rowspan}"')
                attr_str = ' ' + ' '.join(attrs) if attrs else ''
                parts.append(f'<{tag}{attr_str}>{self._escape_html(cell.content)}</{tag}>')
            parts.append('</tr>')
        
        parts.append('</table>')
        
        return '\n'.join(parts)
    
    def _convert_list(self, block: ListBlock) -> str:
        """Convert list block to HTML."""
        tag = 'ol' if block.is_ordered else 'ul'
        dir_attr = self._get_direction_attr(block.direction)
        
        parts = [f'<{tag}{dir_attr}>']
        for item in block.items:
            parts.append(f'<li>{self._escape_html(item)}</li>')
        parts.append(f'</{tag}>')
        
        return '\n'.join(parts)
    
    def _convert_link(self, block: LinkBlock) -> str:
        """Convert link block to HTML."""
        return f'<p><a href="{self._escape_html(block.url)}">{self._escape_html(block.text)}</a></p>'
    
    def _apply_links(self, text: str, links: list) -> str:
        """Apply links to text content."""
        for link in reversed(links):
            if link.start_index is not None and link.end_index is not None:
                before = text[:link.start_index]
                after = text[link.end_index:]
                link_html = f'<a href="{self._escape_html(link.url)}">{self._escape_html(link.text)}</a>'
                text = before + link_html + after
        return text
    
    def _escape_html(self, text: str) -> str:
        """Escape HTML special characters."""
        if not text:
            return ''
        return (text
            .replace('&', '&amp;')
            .replace('<', '&lt;')
            .replace('>', '&gt;')
            .replace('"', '&quot;')
            .replace("'", '&#39;'))
