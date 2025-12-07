"""Unified document schema models using Pydantic."""

from enum import Enum
from typing import Optional, Union, List
from datetime import datetime
from pydantic import BaseModel, Field


class TextDirection(str, Enum):
    """Text direction enumeration."""
    LTR = "ltr"
    RTL = "rtl"
    AUTO = "auto"


class BlockType(str, Enum):
    """Block type enumeration."""
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    IMAGE = "image"
    TABLE = "table"
    LIST = "list"
    LINK = "link"
    CODE = "code"
    QUOTE = "quote"
    POSITIONED_TEXT = "positioned_text"


class BoundingBox(BaseModel):
    """Bounding box for positioned elements (in points)."""
    x: float = Field(default=0, description="X coordinate (left)")
    y: float = Field(default=0, description="Y coordinate (top)")
    width: float = Field(default=0, description="Width")
    height: float = Field(default=0, description="Height")


class TextStyle(BaseModel):
    """Text styling information."""
    font_family: Optional[str] = Field(default=None, description="Font family name")
    font_size: float = Field(default=12, description="Font size in points")
    font_weight: str = Field(default="normal", description="Font weight (normal, bold)")
    font_style: str = Field(default="normal", description="Font style (normal, italic)")
    color: Optional[str] = Field(default=None, description="Text color in hex format")
    background_color: Optional[str] = Field(default=None, description="Background color in hex")
    underline: bool = Field(default=False, description="Is underlined")
    strikethrough: bool = Field(default=False, description="Is strikethrough")


class TextSpan(BaseModel):
    """A span of text with consistent styling."""
    text: str = Field(description="The text content")
    style: TextStyle = Field(default_factory=TextStyle, description="Text styling")
    bbox: Optional[BoundingBox] = Field(default=None, description="Position if available")


class PageDimensions(BaseModel):
    """Page dimensions and margins."""
    width: float = Field(default=612, description="Page width in points (letter=612)")
    height: float = Field(default=792, description="Page height in points (letter=792)")
    rotation: int = Field(default=0, description="Page rotation in degrees")


class Link(BaseModel):
    """Link model for hyperlinks within text."""
    text: str = Field(default="", description="Link display text")
    url: str = Field(description="Link URL")
    start_index: Optional[int] = Field(default=None, description="Start index in parent text")
    end_index: Optional[int] = Field(default=None, description="End index in parent text")


class Metadata(BaseModel):
    """Document metadata."""
    title: Optional[str] = Field(default=None, description="Document title")
    author: Optional[str] = Field(default=None, description="Document author")
    created_date: Optional[datetime] = Field(default=None, description="Creation date")
    modified_date: Optional[datetime] = Field(default=None, description="Last modification date")
    subject: Optional[str] = Field(default=None, description="Document subject")
    keywords: list[str] = Field(default_factory=list, description="Document keywords")
    language: Optional[str] = Field(default=None, description="Document language")
    page_count: Optional[int] = Field(default=None, description="Total page count")
    word_count: Optional[int] = Field(default=None, description="Total word count")
    source_format: Optional[str] = Field(default=None, description="Original file format")
    source_filename: Optional[str] = Field(default=None, description="Original filename")


class BaseBlock(BaseModel):
    """Base block model."""
    type: BlockType = Field(description="Block type")
    direction: TextDirection = Field(default=TextDirection.AUTO, description="Text direction")
    position_hint: Optional[str] = Field(default=None, description="Position hint in document")


class HeadingBlock(BaseBlock):
    """Heading block model."""
    type: BlockType = Field(default=BlockType.HEADING)
    level: int = Field(ge=1, le=6, description="Heading level (1-6)")
    text: str = Field(description="Heading text")
    links: list[Link] = Field(default_factory=list, description="Links within heading")


class ParagraphBlock(BaseBlock):
    """Paragraph block model."""
    type: BlockType = Field(default=BlockType.PARAGRAPH)
    text: str = Field(description="Paragraph text")
    links: list[Link] = Field(default_factory=list, description="Links within paragraph")
    is_bold: bool = Field(default=False, description="Is text bold")
    is_italic: bool = Field(default=False, description="Is text italic")


class ImageBlock(BaseBlock):
    """Image block model."""
    type: BlockType = Field(default=BlockType.IMAGE)
    image_id: str = Field(description="Unique image identifier")
    caption: Optional[str] = Field(default=None, description="Image caption")
    alt_text: Optional[str] = Field(default=None, description="Image alt text")
    image_data: Optional[str] = Field(default=None, description="Base64 encoded image data")
    image_path: Optional[str] = Field(default=None, description="Path to image file")
    image_format: Optional[str] = Field(default=None, description="Image format (png, jpg, etc.)")
    width: Optional[int] = Field(default=None, description="Image width in pixels")
    height: Optional[int] = Field(default=None, description="Image height in pixels")


class TableCell(BaseModel):
    """Table cell model."""
    content: str = Field(default="", description="Cell content")
    is_header: bool = Field(default=False, description="Is header cell")
    colspan: int = Field(default=1, ge=1, description="Column span")
    rowspan: int = Field(default=1, ge=1, description="Row span")
    links: list[Link] = Field(default_factory=list, description="Links within cell")


class TableRow(BaseModel):
    """Table row model."""
    cells: list[TableCell] = Field(default_factory=list, description="Row cells")
    is_header_row: bool = Field(default=False, description="Is header row")


class TableBlock(BaseBlock):
    """Table block model."""
    type: BlockType = Field(default=BlockType.TABLE)
    rows: list[TableRow] = Field(default_factory=list, description="Table rows")
    caption: Optional[str] = Field(default=None, description="Table caption")
    has_header: bool = Field(default=False, description="Has header row")
    column_count: int = Field(default=0, ge=0, description="Number of columns")
    row_count: int = Field(default=0, ge=0, description="Number of rows")


class ListBlock(BaseBlock):
    """List block model."""
    type: BlockType = Field(default=BlockType.LIST)
    items: list[str] = Field(default_factory=list, description="List items")
    is_ordered: bool = Field(default=False, description="Is ordered list")
    links: list[Link] = Field(default_factory=list, description="Links within list items")


class LinkBlock(BaseBlock):
    """Standalone link block model."""
    type: BlockType = Field(default=BlockType.LINK)
    text: str = Field(description="Link display text")
    url: str = Field(description="Link URL")


class PositionedTextBlock(BaseBlock):
    """Text block with precise positioning and size information."""
    type: BlockType = Field(default=BlockType.POSITIONED_TEXT)
    text: str = Field(description="The text content")
    bbox: BoundingBox = Field(default_factory=BoundingBox, description="Position and size")
    style: TextStyle = Field(default_factory=TextStyle, description="Text styling")
    confidence: float = Field(default=1.0, ge=0, le=1, description="OCR confidence score")
    language: Optional[str] = Field(default=None, description="Detected language")


class OCRResult(BaseModel):
    """OCR extraction result with detailed information."""
    text: str = Field(description="Extracted text")
    confidence: float = Field(default=0, description="Average confidence score")
    language: str = Field(default="unknown", description="Detected language")
    word_count: int = Field(default=0, description="Total word count")
    blocks: List[PositionedTextBlock] = Field(default_factory=list, description="Positioned text blocks")
    tables: List[TableBlock] = Field(default_factory=list, description="Extracted tables")
    is_rtl: bool = Field(default=False, description="Is predominantly RTL text")


Block = Union[HeadingBlock, ParagraphBlock, ImageBlock, TableBlock, ListBlock, LinkBlock, PositionedTextBlock]


class Page(BaseModel):
    """Page model representing a document page or section."""
    page_number: int = Field(ge=1, description="Page number (1-indexed)")
    title: Optional[str] = Field(default=None, description="Page/section title")
    blocks: list[Block] = Field(default_factory=list, description="Content blocks")
    direction: TextDirection = Field(default=TextDirection.AUTO, description="Page text direction")


class Document(BaseModel):
    """Unified document model."""
    title: Optional[str] = Field(default=None, description="Document title")
    metadata: Metadata = Field(default_factory=Metadata, description="Document metadata")
    pages: list[Page] = Field(default_factory=list, description="Document pages")
    direction: TextDirection = Field(default=TextDirection.AUTO, description="Document text direction")
    
    def to_json(self, indent: int = 2) -> str:
        """Export document to JSON string."""
        return self.model_dump_json(indent=indent)
    
    def to_dict(self) -> dict:
        """Export document to dictionary."""
        return self.model_dump()
    
    @classmethod
    def from_json(cls, json_str: str) -> "Document":
        """Create document from JSON string."""
        return cls.model_validate_json(json_str)
    
    @classmethod
    def from_dict(cls, data: dict) -> "Document":
        """Create document from dictionary."""
        return cls.model_validate(data)
    
    def get_all_text(self) -> str:
        """Get all text content from document."""
        texts = []
        for page in self.pages:
            for block in page.blocks:
                if hasattr(block, 'text'):
                    texts.append(block.text)
                elif hasattr(block, 'items'):
                    texts.extend(block.items)
                elif isinstance(block, TableBlock):
                    for row in block.rows:
                        for cell in row.cells:
                            texts.append(cell.content)
        return "\n".join(texts)
    
    def get_all_links(self) -> list[Link]:
        """Get all links from document."""
        links = []
        for page in self.pages:
            for block in page.blocks:
                if hasattr(block, 'links'):
                    links.extend(block.links)
                if isinstance(block, LinkBlock):
                    links.append(Link(text=block.text, url=block.url))
                elif isinstance(block, TableBlock):
                    for row in block.rows:
                        for cell in row.cells:
                            links.extend(cell.links)
        return links
    
    def get_all_images(self) -> list[ImageBlock]:
        """Get all images from document."""
        images = []
        for page in self.pages:
            for block in page.blocks:
                if isinstance(block, ImageBlock):
                    images.append(block)
        return images
    
    def get_all_tables(self) -> list[TableBlock]:
        """Get all tables from document."""
        tables = []
        for page in self.pages:
            for block in page.blocks:
                if isinstance(block, TableBlock):
                    tables.append(block)
        return tables
    
    def add_page(self, page: Page) -> None:
        """Add a page to the document."""
        self.pages.append(page)
    
    def get_page(self, page_number: int) -> Optional[Page]:
        """Get page by number."""
        for page in self.pages:
            if page.page_number == page_number:
                return page
        return None
