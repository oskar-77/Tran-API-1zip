"""Base converter class for all document converters."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union
from src.schemas.document import Document


class BaseConverter(ABC):
    """Abstract base class for document converters."""
    
    OUTPUT_FORMAT: str = ""
    OUTPUT_EXTENSION: str = ""
    
    def __init__(self, document: Document):
        """Initialize converter with unified document."""
        self.document = document
    
    @abstractmethod
    def convert(self) -> str:
        """Convert document to target format and return as string."""
        pass
    
    def save(self, output_path: Union[str, Path]) -> str:
        """Convert and save to file."""
        output_path = Path(output_path)
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        content = self.convert()
        
        if isinstance(content, bytes):
            with open(output_path, 'wb') as f:
                f.write(content)
        else:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(content)
        
        return str(output_path)
    
    def get_output_filename(self, base_name: Optional[str] = None) -> str:
        """Generate output filename."""
        if base_name:
            name = base_name
        elif self.document.title:
            name = self.document.title
        elif self.document.metadata.source_filename:
            name = Path(self.document.metadata.source_filename).stem
        else:
            name = "document"
        
        name = "".join(c for c in name if c.isalnum() or c in ' -_').strip()
        name = name.replace(' ', '_')
        
        return f"{name}{self.OUTPUT_EXTENSION}"
