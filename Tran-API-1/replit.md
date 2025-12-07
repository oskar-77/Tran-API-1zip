# Document Processing Agent

## Overview
A comprehensive Python-based document extraction and conversion system. This agent can read various document formats (PDF, DOCX, PPTX, XLSX, TXT, MD), extract their content into a unified data model, and export to multiple output formats (HTML, DOCX, Markdown, JSON).

## Project Structure
```
project/
├── src/
│   ├── __init__.py
│   ├── agent.py              # Main DocumentAgent class
│   ├── extractors/           # Document extractors
│   │   ├── base_extractor.py
│   │   ├── pdf_extractor.py
│   │   ├── docx_extractor.py
│   │   ├── pptx_extractor.py
│   │   ├── xlsx_extractor.py
│   │   ├── text_extractor.py
│   │   └── markdown_extractor.py
│   ├── converters/           # Output converters
│   │   ├── base_converter.py
│   │   ├── html_converter.py
│   │   ├── docx_converter.py
│   │   └── markdown_converter.py
│   ├── schemas/              # Pydantic data models
│   │   └── document.py
│   ├── utils/                # Utility functions
│   │   ├── text_utils.py
│   │   └── image_utils.py
│   └── parsers/
├── samples/                  # Sample files for testing
├── output/                   # Output directory
├── tests/                    # Unit tests
└── main.py                   # CLI entry point
```

## Features
- **Multi-format extraction**: PDF, DOCX, PPTX, XLSX, TXT, MD
- **Unified data model**: Consistent JSON structure for all document types
- **Content extraction**: Text, images, tables, links, metadata
- **RTL/LTR support**: Automatic text direction detection for Arabic/English
- **Multiple export formats**: HTML, DOCX, Markdown, JSON
- **Modular architecture**: Easy to extend with new extractors/converters

## Dependencies
- PyMuPDF (fitz) - PDF processing
- python-docx - Word document handling
- python-pptx - PowerPoint handling
- openpyxl - Excel handling
- Pillow - Image processing
- Pydantic - Data validation
- markdown - Markdown parsing
- lxml - XML/HTML processing

## Usage

### Command Line Interface
```bash
# Show demo and help
python main.py demo

# Extract document to JSON
python main.py extract document.pdf -o output.json

# Convert to HTML
python main.py convert report.docx -f html -o report.html

# Convert to Markdown
python main.py convert data.xlsx -f markdown

# Show document info
python main.py info presentation.pptx --metadata --links
```

### Python API
```python
from src.agent import DocumentAgent

# Initialize agent
agent = DocumentAgent()

# Load document
agent.load("document.pdf")

# Get summary
print(agent.get_summary())

# Export to different formats
agent.export_to_html("output.html")
agent.export_to_docx("output.docx")
agent.export_to_markdown("output.md")
agent.export_to_json("output.json")

# Access extracted content
text = agent.get_text()
links = agent.get_links()
images = agent.get_images()
tables = agent.get_tables()
```

## Data Model (Unified Schema)
```json
{
  "title": "Document Title",
  "metadata": {
    "author": "Author Name",
    "created_date": "2025-01-01T00:00:00",
    "source_format": "pdf"
  },
  "pages": [
    {
      "page_number": 1,
      "blocks": [
        {"type": "heading", "level": 1, "text": "..."},
        {"type": "paragraph", "text": "..."},
        {"type": "image", "image_id": "...", "caption": "..."},
        {"type": "table", "rows": [...]}
      ]
    }
  ],
  "direction": "auto"
}
```

## Web Interface & API

### Running the Web App
```bash
python app.py
```
Access at: http://localhost:5000

### API Endpoints
- `GET /` - Web interface (Arabic RTL)
- `GET /api/formats` - Get supported formats
- `POST /api/upload` - Upload document (multipart/form-data)
- `POST /api/extract` - Extract text/links from document
- `POST /api/convert` - Convert document to format with options (preserve_styles, embed_images)
- `GET /api/download/<filename>` - Download converted file
- `POST /api/preview` - Get HTML preview of document
- `POST /api/source` - Get source text and metadata from document

### Web Interface Features
- Drag & drop file upload
- Document statistics display (pages, blocks, images, tables, links)
- Convert to HTML, DOCX, Markdown, JSON
- Source view - view original document text
- Preview view - styled HTML preview
- Converted view - preview converted content
- Conversion options (preserve styles, embed images)
- Arabic RTL interface with modern design
- Responsive layout with Bootstrap 5

## Recent Changes
- Initial project setup (Dec 2025)
- Implemented all extractors (PDF, DOCX, PPTX, XLSX, TXT, MD)
- Implemented all converters (HTML, DOCX, Markdown)
- Added RTL/LTR text direction support
- Created CLI interface
- Added Flask web API and Arabic web interface (Dec 2025)
- **Enhanced UI** - Modern Arabic RTL design with gradients and animations (Dec 2025)
- **Source View** - Added `/api/source` endpoint to view original document content
- **Converted View** - Preview converted content before downloading
- **Conversion Options** - Added preserve_styles and embed_images options
