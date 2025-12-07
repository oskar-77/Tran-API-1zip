# Document Processing Agent

## Overview

A comprehensive Python-based document extraction and conversion system that transforms various document formats (PDF, DOCX, PPTX, XLSX, TXT, MD, images) into a unified data model and exports them to multiple output formats (HTML, DOCX, Markdown, JSON). The system features robust support for bidirectional text (RTL/LTR), **enhanced OCR capabilities for scanned documents and images with accurate Arabic text extraction**, and both web API and CLI interfaces. The agent intelligently preserves document structure including text blocks, images, tables, links, and metadata while enabling seamless format conversion.

## Recent Changes (December 2025)

- Added dedicated OCR section in UI with mode toggle between document processing and OCR
- Enhanced Arabic text handling with proper RTL direction using python-bidi and arabic-reshaper
- Added PositionedTextBlock schema for precise text positioning with bounding boxes
- Implemented OCRExtractor for images and scanned PDFs with table extraction
- Added language selector for OCR (Arabic, English, French, Urdu, Persian)
- New API endpoints: /api/ocr/upload, /api/ocr/extract
- Applied fix_arabic_text to all PositionedTextBlocks for proper glyph rendering

## User Preferences

Preferred communication style: Simple, everyday language.

## System Architecture

### Core Design Pattern

**Plugin-Based Extractor/Converter Architecture**: The system uses an abstract factory pattern with separate extractor and converter plugins for each format. All extractors inherit from `BaseExtractor` and convert native formats to a unified `Document` schema (Pydantic models). All converters inherit from `BaseConverter` and transform the unified model to target formats. This design enables easy extensibility - adding a new format requires implementing a single extractor or converter class without modifying core logic.

**Rationale**: Separating extraction and conversion concerns allows independent development of input/output handlers. The unified schema acts as a contract between components, ensuring consistency and enabling any-to-any format conversion.

**Alternatives Considered**: Direct format-to-format conversion would be simpler initially but creates O(n²) complexity as formats grow. The chosen approach requires O(n) extractors + O(m) converters for n input and m output formats.

### Document Schema (src/schemas/document.py)

**Unified Pydantic Data Model**: All extracted content maps to a hierarchical structure: `Document → Pages → Blocks`. Blocks are polymorphic (HeadingBlock, ParagraphBlock, ImageBlock, TableBlock, etc.) with shared base attributes (type, direction, position_hint) and type-specific properties. This schema supports rich metadata, bidirectional text, embedded images (base64), structured tables, and positioned elements with bounding boxes.

**Rationale**: A single canonical representation simplifies conversion logic and enables consistent handling of cross-cutting concerns (text direction, positioning, styling). Pydantic provides validation, serialization, and type safety.

**Trade-offs**: Some format-specific features may not map perfectly to the generic model, requiring lossy conversion or extension points. The schema balances comprehensiveness with maintainability.

### Extractor Pipeline (src/extractors/)

**Format-Specific Extraction**: Each extractor uses native libraries:
- **PDF**: PyMuPDF (fitz) for text blocks, images, tables, and links
- **DOCX**: python-docx for paragraphs, tables, styles, and embedded images
- **PPTX**: python-pptx for slide content and shapes
- **XLSX**: openpyxl for cell data and sheet structure
- **Text/Markdown**: Regex and markdown parsing
- **Images/Scanned PDFs**: Tesseract OCR with Arabic reshaping (pytesseract, arabic_reshaper, python-bidi)

**Rationale**: Using established libraries leverages mature parsing capabilities. Each extractor handles format nuances while mapping to the unified schema.

### Converter Pipeline (src/converters/)

**Output Generation**: Converters transform the unified Document model to:
- **HTML**: Template-based with embedded CSS, base64 images, RTL support
- **DOCX**: python-docx document construction with style preservation
- **Markdown**: Text generation with YAML frontmatter
- **JSON**: Direct Pydantic serialization

**Rationale**: Template-based approach for HTML enables customizable styling. DOCX conversion recreates document structure programmatically. Markdown provides human-readable output.

### Text Direction Handling (src/utils/text_utils.py)

**Automatic RTL/LTR Detection**: Uses Unicode bidirectional character analysis to detect Arabic, Hebrew, and other RTL scripts. Applies `arabic_reshaper` and `python-bidi` for proper Arabic text rendering. Each block stores its direction, with document-level direction as default.

**Rationale**: Critical for Arabic document support. Character-level analysis is more reliable than heuristics. Per-block direction handles mixed-language documents.

### OCR Integration (src/extractors/ocr_extractor.py)

**Tesseract with Preprocessing**: Images undergo OpenCV preprocessing (grayscale, noise reduction, thresholding) before OCR. Supports multi-language recognition (Arabic + English default). Extracts positioned text blocks with bounding boxes and confidence scores.

**Rationale**: Preprocessing improves OCR accuracy. Positioned blocks preserve spatial layout. Multi-language support handles bilingual documents.

### Web API (Tran-API-1/app.py)

**Flask REST Interface**: Provides endpoints for file upload, format conversion, and document processing. Stateless request handling with file-based session storage (uploads/, output/ folders).

**Rationale**: Flask offers lightweight HTTP server for simple API requirements. File-based approach avoids database complexity for prototype/demo use case.

**Trade-offs**: Not production-ready - lacks authentication, request validation, rate limiting, and horizontal scalability. File storage doesn't scale and has no cleanup mechanism.

### CLI Interface (Tran-API-1/main.py)

**Argparse Command System**: Command-line tool for batch processing and automation. Supports extract, convert, and batch operations.

**Rationale**: Enables scripting and integration with other tools. Complements web interface for different use cases.

## External Dependencies

### Document Processing Libraries

- **PyMuPDF (fitz)**: PDF parsing and rendering
- **python-docx**: Word document manipulation
- **python-pptx**: PowerPoint presentation handling
- **openpyxl**: Excel spreadsheet processing
- **markdown**: Markdown parsing and HTML generation

### OCR and Image Processing

- **pytesseract**: Python wrapper for Tesseract OCR engine (requires system Tesseract installation)
- **Pillow (PIL)**: Image manipulation and format conversion
- **opencv-python (cv2)**: Image preprocessing for OCR
- **pdf2image**: PDF to image conversion for scanned document processing

### Text and Internationalization

- **arabic_reshaper**: Arabic text shaping for proper rendering
- **python-bidi**: Bidirectional text algorithm implementation
- **unicodedata**: (stdlib) Unicode character properties for direction detection

### Web Framework

- **Flask**: Web application framework for REST API
- **werkzeug**: WSGI utilities (Flask dependency)

### Data Validation

- **pydantic**: Data validation and settings management using Python type annotations

### Environment Configuration

- **SESSION_SECRET**: Environment variable for Flask session encryption
- **UPLOAD_FOLDER**: File upload directory (defaults to 'uploads/')
- **OUTPUT_FOLDER**: Converted file output directory (defaults to 'output/')

### System Requirements

- **Tesseract OCR**: Must be installed on system PATH (not a Python package)
- **Tesseract Language Data**: Arabic (ara) and English (eng) training data required for OCR
- File system write permissions for upload/output directories