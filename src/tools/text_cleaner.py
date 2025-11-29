"""
Text cleaning utilities for ScholarLens.

Handles LaTeX cleanup, unicode normalization, whitespace handling,
and other text preprocessing tasks.
"""

import re
import unicodedata
from typing import List, Optional, Dict


class TextCleaner:
    """Handles various text cleaning operations."""
    
    def __init__(self):
        """Initialize text cleaner."""
        # Common LaTeX commands to remove or replace
        self.latex_replacements = {
            r'\\textbf\{([^}]+)\}': r'\1',
            r'\\textit\{([^}]+)\}': r'\1',
            r'\\emph\{([^}]+)\}': r'\1',
            r'\\section\{([^}]+)\}': r'\1',
            r'\\subsection\{([^}]+)\}': r'\1',
            r'\\cite\{[^}]+\}': '',
            r'\\ref\{[^}]+\}': '',
            r'\\label\{[^}]+\}': '',
            r'\\begin\{[^}]+\}': '',
            r'\\end\{[^}]+\}': '',
            r'\\[a-zA-Z]+': '',  # Other LaTeX commands
        }
    
    def clean_text(
        self,
        text: str,
        remove_latex: bool = True,
        normalize_unicode: bool = True,
        normalize_whitespace: bool = True,
        remove_urls: bool = False,
        fix_line_breaks: bool = True
    ) -> str:
        """
        Clean text with various options.
        
        Args:
            text: Input text
            remove_latex: Remove LaTeX commands
            normalize_unicode: Normalize unicode characters
            normalize_whitespace: Normalize whitespace
            remove_urls: Remove URLs
            fix_line_breaks: Fix hyphenated line breaks
            
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        # Normalize unicode
        if normalize_unicode:
            text = self.normalize_unicode(text)
        
        # Remove LaTeX
        if remove_latex:
            text = self.remove_latex(text)
        
        # Fix line breaks
        if fix_line_breaks:
            text = self.fix_line_breaks(text)
        
        # Remove URLs
        if remove_urls:
            text = self.remove_urls(text)
        
        # Normalize whitespace
        if normalize_whitespace:
            text = self.normalize_whitespace(text)
        
        return text
    
    def normalize_unicode(self, text: str) -> str:
        """
        Normalize unicode characters.
        
        Args:
            text: Input text
            
        Returns:
            Normalized text
        """
        # Use NFKC normalization (compatibility composition)
        text = unicodedata.normalize('NFKC', text)
        
        # Replace common unicode symbols with ASCII equivalents
        replacements = {
            '\u2018': "'",  # Left single quote
            '\u2019': "'",  # Right single quote
            '\u201c': '"',  # Left double quote
            '\u201d': '"',  # Right double quote
            '\u2013': '-',  # En dash
            '\u2014': '--', # Em dash
            '\u2026': '...', # Ellipsis
            '\u00a0': ' ',  # Non-breaking space
            '\u00ad': '',   # Soft hyphen
        }
        
        for unicode_char, ascii_char in replacements.items():
            text = text.replace(unicode_char, ascii_char)
        
        return text
    
    def remove_latex(self, text: str) -> str:
        """
        Remove LaTeX commands from text.
        
        Args:
            text: Input text with LaTeX
            
        Returns:
            Text with LaTeX removed
        """
        # Apply replacements in order
        for pattern, replacement in self.latex_replacements.items():
            text = re.sub(pattern, replacement, text)
        
        # Remove remaining curly braces
        text = text.replace('{', '').replace('}', '')
        
        # Clean up multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        return text
    
    def fix_line_breaks(self, text: str) -> str:
        """
        Fix hyphenated line breaks and join lines properly.
        
        Args:
            text: Input text
            
        Returns:
            Text with fixed line breaks
        """
        # Fix hyphenated line breaks (word- \n word -> word)
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        
        # Join lines that should be continuous (lowercase to lowercase)
        text = re.sub(r'([a-z,])\s*\n\s*([a-z])', r'\1 \2', text)
        
        # Keep paragraph breaks (double newlines)
        text = re.sub(r'\n\s*\n', '\n\n', text)
        
        # Remove single line breaks within paragraphs
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """
        Normalize whitespace in text.
        
        Args:
            text: Input text
            
        Returns:
            Text with normalized whitespace
        """
        # Replace multiple spaces with single space
        text = re.sub(r' +', ' ', text)
        
        # Replace multiple newlines with double newline
        text = re.sub(r'\n\n+', '\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = text.split('\n')
        lines = [line.strip() for line in lines]
        text = '\n'.join(lines)
        
        # Remove leading/trailing whitespace from entire text
        text = text.strip()
        
        return text
    
    def remove_urls(self, text: str) -> str:
        """
        Remove URLs from text.
        
        Args:
            text: Input text
            
        Returns:
            Text with URLs removed
        """
        # Remove http/https URLs
        text = re.sub(r'https?://\S+', '', text)
        
        # Remove www URLs
        text = re.sub(r'www\.\S+', '', text)
        
        return text
    
    def remove_special_characters(self, text: str, keep: str = '') -> str:
        """
        Remove special characters, optionally keeping some.
        
        Args:
            text: Input text
            keep: String of characters to keep
            
        Returns:
            Text with special characters removed
        """
        # Keep alphanumeric, whitespace, and specified characters
        pattern = f'[^a-zA-Z0-9\\s{re.escape(keep)}]'
        text = re.sub(pattern, '', text)
        
        return text
    
    def remove_citations(self, text: str) -> str:
        """
        Remove citation markers from text.
        
        Args:
            text: Input text
            
        Returns:
            Text with citations removed
        """
        # Remove [1], [2,3], [Author et al., 2020] style citations
        text = re.sub(r'\[\d+(?:,\s*\d+)*\]', '', text)
        text = re.sub(r'\[[^\]]*\d{4}[^\]]*\]', '', text)
        
        # Remove (Author, 2020) style citations
        text = re.sub(r'\([^)]*\d{4}[^)]*\)', '', text)
        
        return text
    
    def extract_sentences(self, text: str) -> List[str]:
        """
        Split text into sentences.
        
        Args:
            text: Input text
            
        Returns:
            List of sentences
        """
        # Simple sentence splitting (handles common cases)
        # Split on period, exclamation, question mark followed by space/newline
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    def truncate_text(self, text: str, max_length: int, suffix: str = '...') -> str:
        """
        Truncate text to maximum length.
        
        Args:
            text: Input text
            max_length: Maximum length
            suffix: Suffix to add when truncated
            
        Returns:
            Truncated text
        """
        if len(text) <= max_length:
            return text
        
        # Truncate at word boundary
        truncated = text[:max_length - len(suffix)]
        last_space = truncated.rfind(' ')
        
        if last_space > 0:
            truncated = truncated[:last_space]
        
        return truncated + suffix
    
    def clean_equation(self, equation: str) -> str:
        """
        Clean LaTeX equation.
        
        Args:
            equation: LaTeX equation string
            
        Returns:
            Cleaned equation
        """
        # Remove extra whitespace
        equation = equation.strip()
        
        # Remove display math delimiters if present
        equation = re.sub(r'^\$\$|\$\$$', '', equation)
        equation = re.sub(r'^\$|\$$', '', equation)
        
        # Normalize whitespace
        equation = re.sub(r'\s+', ' ', equation)
        
        return equation


def clean_text(
    text: str,
    remove_latex: bool = True,
    normalize_unicode: bool = True,
    normalize_whitespace: bool = True,
    remove_urls: bool = False,
    fix_line_breaks: bool = True
) -> str:
    """
    Convenience function to clean text.
    
    Args:
        text: Input text
        remove_latex: Remove LaTeX commands
        normalize_unicode: Normalize unicode characters
        normalize_whitespace: Normalize whitespace
        remove_urls: Remove URLs
        fix_line_breaks: Fix hyphenated line breaks
        
    Returns:
        Cleaned text
    """
    cleaner = TextCleaner()
    return cleaner.clean_text(
        text,
        remove_latex=remove_latex,
        normalize_unicode=normalize_unicode,
        normalize_whitespace=normalize_whitespace,
        remove_urls=remove_urls,
        fix_line_breaks=fix_line_breaks
    )
