"""Base extractor class for all document extractors."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Union
from src.schemas.document import Document, Metadata


class BaseExtractor(ABC):
    """Abstract base class for document extractors."""
    
    SUPPORTED_EXTENSIONS: list[str] = []
    
    def __init__(self, file_path: Union[str, Path]):
        """Initialize extractor with file path."""
        self.file_path = Path(file_path)
        self._validate_file()
    
    def _validate_file(self) -> None:
        """Validate that file exists and has supported extension."""
        if not self.file_path.exists():
            raise FileNotFoundError(f"File not found: {self.file_path}")
        
        if self.SUPPORTED_EXTENSIONS:
            ext = self.file_path.suffix.lower()
            if ext not in self.SUPPORTED_EXTENSIONS:
                raise ValueError(
                    f"Unsupported file extension: {ext}. "
                    f"Supported: {', '.join(self.SUPPORTED_EXTENSIONS)}"
                )
    
    @abstractmethod
    def extract(self) -> Document:
        """Extract content from document and return unified Document model."""
        pass
    
    def _create_base_metadata(self) -> Metadata:
        """Create base metadata from file."""
        import os
        from datetime import datetime
        
        stat = self.file_path.stat()
        
        return Metadata(
            source_filename=self.file_path.name,
            source_format=self.file_path.suffix.lower().lstrip('.'),
            modified_date=datetime.fromtimestamp(stat.st_mtime),
        )
    
    @classmethod
    def can_handle(cls, file_path: Union[str, Path]) -> bool:
        """Check if this extractor can handle the given file."""
        ext = Path(file_path).suffix.lower()
        return ext in cls.SUPPORTED_EXTENSIONS
    
    def get_file_size(self) -> int:
        """Get file size in bytes."""
        return self.file_path.stat().st_size
    
    def get_filename(self) -> str:
        """Get filename without path."""
        return self.file_path.name
    
    def get_extension(self) -> str:
        """Get file extension."""
        return self.file_path.suffix.lower()
