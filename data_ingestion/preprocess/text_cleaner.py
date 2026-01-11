"""
Text Cleaner for Legal Documents
Cleans scraped legal text for better embeddings and retrieval
"""
import re
from typing import Optional

def remove_extra_whitespace(text: str) -> str:
    """
    Remove extra whitespace and newlines
    
    Args:
        text: Raw text
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Replace multiple newlines with single newline
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Replace multiple spaces with single space
    text = re.sub(r' {2,}', ' ', text)
    
    # Remove trailing/leading whitespace from lines
    lines = [line.strip() for line in text.split('\n')]
    text = '\n'.join(line for line in lines if line)
    
    return text.strip()


def remove_repeated_section_numbers(text: str, section_number: str) -> str:
    """
    Remove repeated section numbers within content
    
    Args:
        text: Text content
        section_number: Section number to remove if repeated
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Remove standalone "Section 438" or "Section 438:" at start of lines
    pattern = rf'^\s*Section\s+{re.escape(section_number)}\s*[:\-]?\s*\n?'
    text = re.sub(pattern, '', text, flags=re.MULTILINE | re.IGNORECASE)
    
    # Remove repeated section numbers in middle of text
    # But keep first occurrence
    section_pattern = rf'\bSection\s+{re.escape(section_number)}\b'
    matches = list(re.finditer(section_pattern, text, re.IGNORECASE))
    
    if len(matches) > 1:
        # Keep first occurrence, remove others
        for match in reversed(matches[1:]):  # Start from end to preserve indices
            text = text[:match.start()] + text[match.end():]
    
    return text.strip()


def normalize_quotes(text: str) -> str:
    """
    Normalize different quote styles to standard quotes
    
    Args:
        text: Text with mixed quotes
        
    Returns:
        Text with normalized quotes
    """
    if not text:
        return ""
    
    # Replace fancy quotes with standard quotes
    text = text.replace('"', '"')  # Left double quote
    text = text.replace('"', '"')  # Right double quote
    text = text.replace(''', "'")  # Left single quote
    text = text.replace(''', "'")  # Right single quote
    
    return text


def remove_navigation_text(text: str) -> str:
    """
    Remove common navigation and header/footer text
    
    Args:
        text: Text that may contain navigation elements
        
    Returns:
        Cleaned text
    """
    if not text:
        return ""
    
    # Common navigation phrases to remove
    navigation_patterns = [
        r'Home\s*>\s*Acts',
        r'Acts\s*>\s*Criminal',
        r'Criminal Procedure Code',
        r'Print\s+Page',
        r'Download\s+PDF',
        r'Last\s+Updated.*?\n',
        r'©.*?Government of India.*?\n',
        r'Disclaimer.*?\n',
    ]
    
    for pattern in navigation_patterns:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE | re.MULTILINE)
    
    return text.strip()


def clean_legal_text(text: str, section_number: Optional[str] = None) -> str:
    """
    Main cleaning function for legal text
    
    Applies all cleaning functions in sequence:
    1. Remove navigation text
    2. Normalize quotes
    3. Remove repeated section numbers
    4. Remove extra whitespace
    
    Args:
        text: Raw legal text
        section_number: Optional section number for removing repetitions
        
    Returns:
        Fully cleaned text ready for embedding
    """
    if not text:
        return ""
    
    # Step 1: Remove navigation elements
    text = remove_navigation_text(text)
    
    # Step 2: Normalize quotes
    text = normalize_quotes(text)
    
    # Step 3: Remove repeated section numbers (if provided)
    if section_number:
        text = remove_repeated_section_numbers(text, section_number)
    
    # Step 4: Remove extra whitespace (should be last)
    text = remove_extra_whitespace(text)
    
    return text


def validate_cleaned_text(text: str, min_length: int = 50) -> bool:
    """
    Validate that cleaned text meets minimum requirements
    
    Args:
        text: Cleaned text to validate
        min_length: Minimum required length
        
    Returns:
        True if text is valid, False otherwise
    """
    if not text:
        return False
    
    if len(text) < min_length:
        return False
    
    # Check if text is not just whitespace
    if not text.strip():
        return False
    
    # Check if text has some actual content (not just special chars)
    if not re.search(r'[a-zA-Z]{3,}', text):
        return False
    
    return True
