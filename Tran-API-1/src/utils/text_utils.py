"""Text utility functions for document processing."""

import re
import unicodedata
from typing import Optional


def is_arabic_text(text: str) -> bool:
    """Check if text contains Arabic characters."""
    if not text:
        return False
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')
    return bool(arabic_pattern.search(text))


def is_hebrew_text(text: str) -> bool:
    """Check if text contains Hebrew characters."""
    if not text:
        return False
    hebrew_pattern = re.compile(r'[\u0590-\u05FF\uFB1D-\uFB4F]')
    return bool(hebrew_pattern.search(text))


def detect_text_direction(text: str) -> str:
    """Detect text direction (RTL or LTR) based on content."""
    if not text:
        return "ltr"
    
    rtl_chars = 0
    ltr_chars = 0
    
    for char in text:
        category = unicodedata.bidirectional(char)
        if category in ('R', 'AL', 'AN'):
            rtl_chars += 1
        elif category == 'L':
            ltr_chars += 1
    
    if rtl_chars > ltr_chars:
        return "rtl"
    return "ltr"


def clean_text(text: str, preserve_newlines: bool = True) -> str:
    """Clean and normalize text content."""
    if not text:
        return ""
    
    text = unicodedata.normalize('NFKC', text)
    
    if preserve_newlines:
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            cleaned_line = ' '.join(line.split())
            cleaned_lines.append(cleaned_line)
        text = '\n'.join(cleaned_lines)
    else:
        text = ' '.join(text.split())
    
    text = text.strip()
    
    return text


def extract_urls(text: str) -> list[tuple[str, int, int]]:
    """Extract URLs from text with their positions."""
    if not text:
        return []
    
    url_pattern = re.compile(
        r'https?://(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*|'
        r'www\.(?:[-\w.]|(?:%[\da-fA-F]{2}))+[^\s]*'
    )
    
    urls = []
    for match in url_pattern.finditer(text):
        url = match.group()
        if not url.startswith('http'):
            url = 'https://' + url
        urls.append((url, match.start(), match.end()))
    
    return urls


def split_into_paragraphs(text: str) -> list[str]:
    """Split text into paragraphs."""
    if not text:
        return []
    
    paragraphs = re.split(r'\n\s*\n', text)
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    return paragraphs


def count_words(text: str) -> int:
    """Count words in text."""
    if not text:
        return 0
    
    words = text.split()
    return len(words)


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to maximum length."""
    if not text or len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """Normalize whitespace in text."""
    if not text:
        return ""
    
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


def is_heading(text: str, min_length: int = 3, max_length: int = 200) -> bool:
    """Heuristic check if text looks like a heading."""
    if not text:
        return False
    
    text = text.strip()
    
    if len(text) < min_length or len(text) > max_length:
        return False
    
    if text.endswith('.') and not text.endswith('...'):
        return False
    
    if '\n' in text:
        return False
    
    return True
