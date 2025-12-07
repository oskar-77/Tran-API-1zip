"""Text utility functions for document processing with enhanced Arabic support."""

import re
import unicodedata
from typing import Optional, Tuple, List
from bidi.algorithm import get_display
from arabic_reshaper import reshape


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


def is_rtl_text(text: str) -> bool:
    """Check if text is predominantly RTL (Arabic, Hebrew, etc.)."""
    if not text:
        return False
    return is_arabic_text(text) or is_hebrew_text(text)


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


def fix_arabic_text(text: str) -> str:
    """
    Fix Arabic text for proper display.
    Reshapes Arabic characters and applies BiDi algorithm.
    """
    if not text or not is_arabic_text(text):
        return text
    
    try:
        reshaped = reshape(text)
        bidi_text = get_display(reshaped)
        return bidi_text
    except Exception:
        return text


def normalize_arabic_text(text: str) -> str:
    """
    Normalize Arabic text by:
    - Removing diacritics (tashkeel) if needed
    - Normalizing letter forms
    """
    if not text:
        return ""
    
    diacritics = re.compile(r'[\u064B-\u0652\u0670]')
    normalized = diacritics.sub('', text)
    
    normalized = normalized.replace('\u0622', '\u0627')
    normalized = normalized.replace('\u0623', '\u0627')
    normalized = normalized.replace('\u0625', '\u0627')
    
    return normalized


def preserve_arabic_order(text: str) -> str:
    """
    Preserve the logical order of Arabic text.
    Useful when OCR returns reversed text.
    """
    if not text or not is_arabic_text(text):
        return text
    
    words = text.split()
    
    arabic_words = []
    for word in words:
        if is_arabic_text(word):
            arabic_words.append(word)
        else:
            arabic_words.append(word)
    
    return ' '.join(arabic_words)


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


def clean_arabic_text(text: str, preserve_diacritics: bool = True) -> str:
    """
    Clean Arabic text specifically.
    - Normalizes Unicode
    - Optionally preserves diacritics
    - Fixes common OCR errors in Arabic
    """
    if not text:
        return ""
    
    text = unicodedata.normalize('NFKC', text)
    
    text = ' '.join(text.split())
    
    if not preserve_diacritics:
        text = normalize_arabic_text(text)
    
    text = text.replace('\u200C', '')
    text = text.replace('\u200D', '')
    text = text.replace('\u200E', '')
    text = text.replace('\u200F', '')
    text = text.replace('\u00A0', ' ')
    
    return text.strip()


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
    """Count words in text (handles Arabic and English)."""
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


def get_text_metrics(text: str) -> dict:
    """
    Get metrics about text content.
    Returns character counts, word counts, and language detection.
    """
    if not text:
        return {
            'total_chars': 0,
            'arabic_chars': 0,
            'english_chars': 0,
            'word_count': 0,
            'line_count': 0,
            'direction': 'ltr',
            'is_rtl': False
        }
    
    arabic_pattern = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]')
    english_pattern = re.compile(r'[a-zA-Z]')
    
    arabic_chars = len(arabic_pattern.findall(text))
    english_chars = len(english_pattern.findall(text))
    
    direction = detect_text_direction(text)
    
    return {
        'total_chars': len(text),
        'arabic_chars': arabic_chars,
        'english_chars': english_chars,
        'word_count': count_words(text),
        'line_count': len(text.split('\n')),
        'direction': direction,
        'is_rtl': direction == 'rtl'
    }


def merge_text_blocks(blocks: List[dict], same_line_threshold: float = 5.0) -> List[dict]:
    """
    Merge text blocks that are on the same line.
    Used for reconstructing text from OCR results.
    
    Args:
        blocks: List of text blocks with 'text', 'x', 'y', 'width', 'height'
        same_line_threshold: Y-coordinate difference threshold for same line
    
    Returns:
        Merged list of text blocks
    """
    if not blocks:
        return []
    
    sorted_blocks = sorted(blocks, key=lambda b: (b.get('y', 0), -b.get('x', 0)))
    
    merged = []
    current_line = []
    current_y = None
    
    for block in sorted_blocks:
        y = block.get('y', 0)
        
        if current_y is None or abs(y - current_y) <= same_line_threshold:
            current_line.append(block)
            current_y = y
        else:
            if current_line:
                current_line.sort(key=lambda b: -b.get('x', 0))
                merged_text = ' '.join([b.get('text', '') for b in current_line])
                merged.append({
                    'text': merged_text,
                    'x': current_line[-1].get('x', 0),
                    'y': current_y,
                    'width': sum(b.get('width', 0) for b in current_line),
                    'height': max(b.get('height', 0) for b in current_line)
                })
            current_line = [block]
            current_y = y
    
    if current_line:
        current_line.sort(key=lambda b: -b.get('x', 0))
        merged_text = ' '.join([b.get('text', '') for b in current_line])
        merged.append({
            'text': merged_text,
            'x': current_line[-1].get('x', 0),
            'y': current_y,
            'width': sum(b.get('width', 0) for b in current_line),
            'height': max(b.get('height', 0) for b in current_line)
        })
    
    return merged
