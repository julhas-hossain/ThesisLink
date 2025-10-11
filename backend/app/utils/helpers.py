"""
Helper utility functions for various operations.
"""
import re
from typing import Dict, Any
from datetime import datetime


def replace_placeholders(text: str, placeholders: Dict[str, str]) -> str:
    """
    Replace placeholders in text with actual values.
    
    Placeholders format: [PlaceholderName]
    
    Args:
        text: Text containing placeholders
        placeholders: Dictionary mapping placeholder names to values
        
    Returns:
        str: Text with placeholders replaced
    """
    result = text
    for key, value in placeholders.items():
        pattern = f"\\[{key}\\]"
        result = re.sub(pattern, str(value), result, flags=re.IGNORECASE)
    return result


def extract_placeholders(text: str) -> list[str]:
    """
    Extract all placeholders from text.
    
    Args:
        text: Text containing placeholders in format [PlaceholderName]
        
    Returns:
        list: List of placeholder names found
    """
    pattern = r'\[(\w+)\]'
    matches = re.findall(pattern, text)
    return list(set(matches))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
    """
    # Remove path components
    filename = filename.split('\\')[-1].split('/')[-1]
    
    # Remove invalid characters
    filename = re.sub(r'[^\w\s.-]', '', filename)
    
    # Limit length
    if len(filename) > 255:
        name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
        filename = name[:250] + ('.' + ext if ext else '')
    
    return filename


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.
    
    Args:
        filename: File name
        
    Returns:
        str: File extension with dot (e.g., '.pdf')
    """
    if '.' in filename:
        return '.' + filename.rsplit('.', 1)[1].lower()
    return ''


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        str: Formatted size (e.g., '1.5 MB')
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def generate_unique_filename(original_filename: str) -> str:
    """
    Generate unique filename using timestamp.
    
    Args:
        original_filename: Original filename
        
    Returns:
        str: Unique filename
    """
    timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S_%f')
    name, ext = original_filename.rsplit('.', 1) if '.' in original_filename else (original_filename, '')
    sanitized_name = re.sub(r'[^\w\s-]', '', name)[:50]
    return f"{sanitized_name}_{timestamp}.{ext}" if ext else f"{sanitized_name}_{timestamp}"
