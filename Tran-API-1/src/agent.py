"""Document Processing Agent - Main orchestration class."""

from pathlib import Path
from typing import Optional, Union, Type
from src.schemas.document import Document, TextDirection
from src.extractors.base_extractor import BaseExtractor
from src.extractors.pdf_extractor import PDFExtractor
from src.extractors.docx_extractor import DocxExtractor
from src.extractors.pptx_extractor import PptxExtractor
from src.extractors.xlsx_extractor import XlsxExtractor
from src.extractors.text_extractor import TextExtractor
from src.extractors.markdown_extractor import MarkdownExtractor
from src.converters.base_converter import BaseConverter
from src.converters.html_converter import HTMLConverter
from src.converters.docx_converter import DocxConverter
from src.converters.markdown_converter import MarkdownConverter


class DocumentAgent:
    """Document Processing Agent for extraction and conversion."""
    
    EXTRACTOR_MAP: dict[str, Type[BaseExtractor]] = {
        '.pdf': PDFExtractor,
        '.docx': DocxExtractor,
        '.pptx': PptxExtractor,
        '.xlsx': XlsxExtractor,
        '.xlsm': XlsxExtractor,
        '.txt': TextExtractor,
        '.md': MarkdownExtractor,
        '.markdown': MarkdownExtractor,
    }
    
    CONVERTER_MAP: dict[str, Type[BaseConverter]] = {
        'html': HTMLConverter,
        'docx': DocxConverter,
        'markdown': MarkdownConverter,
        'md': MarkdownConverter,
    }
    
    def __init__(self):
        """Initialize Document Agent."""
        self._document: Optional[Document] = None
        self._source_path: Optional[Path] = None
    
    @property
    def document(self) -> Optional[Document]:
        """Get current document."""
        return self._document
    
    @document.setter
    def document(self, doc: Document):
        """Set current document."""
        self._document = doc
    
    def load(self, file_path: Union[str, Path]) -> Document:
        """Load and extract content from a file.
        
        Args:
            file_path: Path to the document file
            
        Returns:
            Unified Document model
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file type is not supported
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        ext = file_path.suffix.lower()
        
        if ext not in self.EXTRACTOR_MAP:
            supported = ', '.join(self.EXTRACTOR_MAP.keys())
            raise ValueError(
                f"Unsupported file type: {ext}. "
                f"Supported types: {supported}"
            )
        
        extractor_class = self.EXTRACTOR_MAP[ext]
        extractor = extractor_class(file_path)
        
        self._document = extractor.extract()
        self._source_path = file_path
        
        return self._document
    
    def load_from_json(self, json_str: str) -> Document:
        """Load document from JSON string.
        
        Args:
            json_str: JSON string representation of document
            
        Returns:
            Unified Document model
        """
        self._document = Document.from_json(json_str)
        return self._document
    
    def load_from_dict(self, data: dict) -> Document:
        """Load document from dictionary.
        
        Args:
            data: Dictionary representation of document
            
        Returns:
            Unified Document model
        """
        self._document = Document.from_dict(data)
        return self._document
    
    def export(self, format: str, output_path: Optional[Union[str, Path]] = None,
               **kwargs) -> Union[str, bytes]:
        """Export current document to specified format.
        
        Args:
            format: Output format (html, docx, markdown, md)
            output_path: Optional path to save the output
            **kwargs: Additional converter options
            
        Returns:
            Converted content (string or bytes)
            
        Raises:
            ValueError: If no document loaded or format not supported
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        
        format = format.lower()
        
        if format not in self.CONVERTER_MAP:
            supported = ', '.join(set(self.CONVERTER_MAP.keys()))
            raise ValueError(
                f"Unsupported export format: {format}. "
                f"Supported formats: {supported}"
            )
        
        converter_class = self.CONVERTER_MAP[format]
        converter = converter_class(self._document, **kwargs)
        
        if output_path:
            return converter.save(output_path)
        
        return converter.convert()
    
    def export_to_html(self, output_path: Optional[Union[str, Path]] = None,
                       include_styles: bool = True,
                       embed_images: bool = True) -> str:
        """Export document to HTML.
        
        Args:
            output_path: Optional path to save the HTML file
            include_styles: Include CSS styles
            embed_images: Embed images as base64
            
        Returns:
            HTML content string
        """
        return self.export('html', output_path, 
                          include_styles=include_styles,
                          embed_images=embed_images)
    
    def export_to_docx(self, output_path: Optional[Union[str, Path]] = None,
                       embed_images: bool = True) -> Union[str, bytes]:
        """Export document to DOCX.
        
        Args:
            output_path: Optional path to save the DOCX file
            embed_images: Embed images in document
            
        Returns:
            DOCX bytes or file path if saved
        """
        return self.export('docx', output_path, embed_images=embed_images)
    
    def export_to_markdown(self, output_path: Optional[Union[str, Path]] = None,
                           include_frontmatter: bool = True,
                           embed_images: bool = False) -> str:
        """Export document to Markdown.
        
        Args:
            output_path: Optional path to save the Markdown file
            include_frontmatter: Include YAML frontmatter
            embed_images: Embed images as base64
            
        Returns:
            Markdown content string
        """
        return self.export('markdown', output_path,
                          include_frontmatter=include_frontmatter,
                          embed_images=embed_images)
    
    def export_to_json(self, output_path: Optional[Union[str, Path]] = None,
                       indent: int = 2) -> str:
        """Export document to JSON.
        
        Args:
            output_path: Optional path to save the JSON file
            indent: JSON indentation level
            
        Returns:
            JSON string
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        
        json_str = self._document.to_json(indent=indent)
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            return str(output_path)
        
        return json_str
    
    def get_text(self) -> str:
        """Get all text content from document.
        
        Returns:
            All text content concatenated
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        return self._document.get_all_text()
    
    def get_links(self) -> list:
        """Get all links from document.
        
        Returns:
            List of Link objects
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        return self._document.get_all_links()
    
    def get_images(self) -> list:
        """Get all images from document.
        
        Returns:
            List of ImageBlock objects
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        return self._document.get_all_images()
    
    def get_tables(self) -> list:
        """Get all tables from document.
        
        Returns:
            List of TableBlock objects
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        return self._document.get_all_tables()
    
    def get_metadata(self) -> dict:
        """Get document metadata.
        
        Returns:
            Metadata dictionary
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        return self._document.metadata.model_dump()
    
    def set_title(self, title: str) -> None:
        """Set document title.
        
        Args:
            title: New document title
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        self._document.title = title
        self._document.metadata.title = title
    
    def set_direction(self, direction: str) -> None:
        """Set document text direction.
        
        Args:
            direction: 'rtl', 'ltr', or 'auto'
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        self._document.direction = TextDirection(direction)
    
    def get_summary(self) -> dict:
        """Get document summary.
        
        Returns:
            Summary dictionary with stats
        """
        if not self._document:
            raise ValueError("No document loaded. Call load() first.")
        
        return {
            'title': self._document.title,
            'page_count': len(self._document.pages),
            'total_blocks': sum(len(p.blocks) for p in self._document.pages),
            'image_count': len(self.get_images()),
            'table_count': len(self.get_tables()),
            'link_count': len(self.get_links()),
            'direction': self._document.direction.value,
            'source_format': self._document.metadata.source_format,
            'source_filename': self._document.metadata.source_filename,
        }
    
    @classmethod
    def get_supported_input_formats(cls) -> list[str]:
        """Get list of supported input formats."""
        return list(cls.EXTRACTOR_MAP.keys())
    
    @classmethod
    def get_supported_output_formats(cls) -> list[str]:
        """Get list of supported output formats."""
        return list(set(cls.CONVERTER_MAP.keys()))
    
    def __repr__(self) -> str:
        """String representation."""
        if self._document:
            return f"DocumentAgent(document='{self._document.title}')"
        return "DocumentAgent(no document loaded)"
