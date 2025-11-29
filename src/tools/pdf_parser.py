"""
PDF parsing tool for ScholarLens.

Extracts text, sections, equations, and metadata from research papers in PDF format.
Uses PyMuPDF (fitz) as primary parser with fallback to pdfplumber.
"""

import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict

try:
    import fitz  # PyMuPDF
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

try:
    import pdfplumber
    PDFPLUMBER_AVAILABLE = True
except ImportError:
    PDFPLUMBER_AVAILABLE = False


@dataclass
class Section:
    """Represents a section in the paper."""
    title: str
    content: str
    start_page: int
    end_page: int
    level: int = 1


@dataclass
class Document:
    """Represents a parsed research paper document."""
    title: str
    authors: List[str]
    abstract: str
    sections: List[Section]
    equations: List[str]
    figures: List[str]
    tables: List[str]
    references: List[str]
    full_text: str
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert document to dictionary."""
        return {
            'title': self.title,
            'authors': self.authors,
            'abstract': self.abstract,
            'sections': [asdict(s) for s in self.sections],
            'equations': self.equations,
            'figures': self.figures,
            'tables': self.tables,
            'references': self.references,
            'full_text': self.full_text,
            'metadata': self.metadata
        }


class PDFParser:
    """Handles PDF parsing and text extraction."""
    
    def __init__(self, extract_images: bool = False, extract_tables: bool = True):
        """
        Initialize PDF parser.
        
        Args:
            extract_images: Whether to extract image metadata
            extract_tables: Whether to extract table information
        """
        self.extract_images = extract_images
        self.extract_tables = extract_tables
        
        if not PYMUPDF_AVAILABLE and not PDFPLUMBER_AVAILABLE:
            raise ImportError(
                "Neither PyMuPDF nor pdfplumber is available. "
                "Install with: pip install pymupdf pdfplumber"
            )
    
    def parse_pdf(self, pdf_path: str) -> Document:
        """
        Parse PDF file and extract structured content.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Document object with extracted content
        """
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
        
        # Try PyMuPDF first, fallback to pdfplumber
        if PYMUPDF_AVAILABLE:
            return self._parse_with_pymupdf(pdf_path)
        elif PDFPLUMBER_AVAILABLE:
            return self._parse_with_pdfplumber(pdf_path)
        else:
            raise RuntimeError("No PDF parser available")
    
    def _parse_with_pymupdf(self, pdf_path: Path) -> Document:
        """
        Parse PDF using PyMuPDF.
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Document object
        """
        doc = fitz.open(pdf_path)
        
        # Extract full text
        full_text = ""
        page_texts = []
        for page_num in range(len(doc)):
            page = doc[page_num]
            text = page.get_text()
            page_texts.append(text)
            full_text += text + "\n\n"
        
        # Extract metadata
        metadata = {
            'num_pages': len(doc),
            'file_size': pdf_path.stat().st_size,
            'filename': pdf_path.name
        }
        
        # Try to get PDF metadata
        pdf_metadata = doc.metadata
        if pdf_metadata:
            metadata.update({
                'pdf_title': pdf_metadata.get('title', ''),
                'pdf_author': pdf_metadata.get('author', ''),
                'pdf_subject': pdf_metadata.get('subject', ''),
                'pdf_keywords': pdf_metadata.get('keywords', '')
            })
        
        # Extract structured elements
        title = self._extract_title(full_text, metadata)
        authors = self._extract_authors(full_text)
        abstract = self._extract_abstract(full_text)
        sections = self._extract_sections(page_texts)
        equations = self._extract_equations(full_text)
        figures = self._extract_figures(doc) if self.extract_images else []
        tables = self._extract_tables(full_text) if self.extract_tables else []
        references = self._extract_references(full_text)
        
        doc.close()
        
        return Document(
            title=title,
            authors=authors,
            abstract=abstract,
            sections=sections,
            equations=equations,
            figures=figures,
            tables=tables,
            references=references,
            full_text=full_text,
            metadata=metadata
        )
    
    def _parse_with_pdfplumber(self, pdf_path: Path) -> Document:
        """
        Parse PDF using pdfplumber (fallback).
        
        Args:
            pdf_path: Path to PDF file
            
        Returns:
            Document object
        """
        with pdfplumber.open(pdf_path) as pdf:
            # Extract text from all pages
            full_text = ""
            page_texts = []
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    page_texts.append(text)
                    full_text += text + "\n\n"
            
            # Metadata
            metadata = {
                'num_pages': len(pdf.pages),
                'file_size': pdf_path.stat().st_size,
                'filename': pdf_path.name
            }
            
            # Extract structured elements
            title = self._extract_title(full_text, metadata)
            authors = self._extract_authors(full_text)
            abstract = self._extract_abstract(full_text)
            sections = self._extract_sections(page_texts)
            equations = self._extract_equations(full_text)
            figures = []  # pdfplumber doesn't easily extract figure info
            tables = []
            references = self._extract_references(full_text)
        
        return Document(
            title=title,
            authors=authors,
            abstract=abstract,
            sections=sections,
            equations=equations,
            figures=figures,
            tables=tables,
            references=references,
            full_text=full_text,
            metadata=metadata
        )
    
    def _extract_title(self, text: str, metadata: Dict[str, Any]) -> str:
        """Extract paper title from text or metadata."""
        # Try PDF metadata first
        if 'pdf_title' in metadata and metadata['pdf_title']:
            return metadata['pdf_title']
        
        # Heuristic: title is usually the first non-empty line or largest text
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        if lines:
            # Take first substantial line (not URL, not single word)
            for line in lines[:10]:
                if len(line) > 10 and not line.startswith('http'):
                    return line
        
        return "Untitled Paper"
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract author names from text."""
        # Simple heuristic: look for lines after title, before abstract
        # This is approximate and may need improvement
        lines = text.split('\n')
        authors = []
        
        # Look for common author patterns (names with commas, "and", etc.)
        for i, line in enumerate(lines[:30]):  # Check first 30 lines
            line = line.strip()
            # Skip empty lines and lines that are too long (likely not authors)
            if not line or len(line) > 200:
                continue
            
            # Check if line looks like authors (has "and" or multiple commas)
            if ' and ' in line.lower() or line.count(',') >= 1:
                # Clean and split
                author_text = line.replace(' and ', ',').replace('&', ',')
                potential_authors = [a.strip() for a in author_text.split(',')]
                # Filter out non-name patterns
                for author in potential_authors:
                    if 3 < len(author) < 50 and not author.startswith('http'):
                        authors.append(author)
                break
        
        return authors if authors else ["Unknown Author"]
    
    def _extract_abstract(self, text: str) -> str:
        """Extract abstract section from text."""
        # Look for "Abstract" heading
        abstract_pattern = r'(?i)abstract\s*\n(.*?)(?=\n\s*\n\s*(?:1\.|introduction|keywords)|\Z)'
        match = re.search(abstract_pattern, text, re.DOTALL)
        
        if match:
            abstract = match.group(1).strip()
            # Clean up
            abstract = re.sub(r'\s+', ' ', abstract)
            return abstract
        
        # Fallback: take first substantial paragraph after title
        paragraphs = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 100]
        if paragraphs:
            return paragraphs[0][:1000]  # Limit length
        
        return "No abstract found"
    
    def _extract_sections(self, page_texts: List[str]) -> List[Section]:
        """Extract paper sections from page texts."""
        sections = []
        
        # Common section headers
        section_patterns = [
            r'^\s*(\d+\.?\s+[A-Z][a-zA-Z\s]+)',  # "1. Introduction"
            r'^\s*([A-Z][A-Z\s]{5,})',  # "INTRODUCTION"
        ]
        
        current_section = None
        current_content = []
        
        for page_num, page_text in enumerate(page_texts):
            lines = page_text.split('\n')
            
            for line in lines:
                # Check if line is a section header
                is_header = False
                for pattern in section_patterns:
                    if re.match(pattern, line.strip()):
                        # Save previous section
                        if current_section:
                            sections.append(Section(
                                title=current_section,
                                content='\n'.join(current_content),
                                start_page=page_num,
                                end_page=page_num,
                                level=1
                            ))
                        
                        current_section = line.strip()
                        current_content = []
                        is_header = True
                        break
                
                if not is_header and current_section:
                    current_content.append(line)
        
        # Add last section
        if current_section:
            sections.append(Section(
                title=current_section,
                content='\n'.join(current_content),
                start_page=len(page_texts) - 1,
                end_page=len(page_texts) - 1,
                level=1
            ))
        
        return sections
    
    def _extract_equations(self, text: str) -> List[str]:
        """Extract equations from text."""
        equations = []
        
        # Look for LaTeX-style equations
        latex_patterns = [
            r'\$\$(.*?)\$\$',  # Display math
            r'\$(.*?)\$',      # Inline math
            r'\\begin\{equation\}(.*?)\\end\{equation\}',
            r'\\begin\{align\}(.*?)\\end\{align\}',
        ]
        
        for pattern in latex_patterns:
            matches = re.findall(pattern, text, re.DOTALL)
            equations.extend([m.strip() for m in matches if m.strip()])
        
        # Look for numbered equations (heuristic)
        numbered_eq = re.findall(r'\(\d+\)\s*$', text, re.MULTILINE)
        
        return list(set(equations))[:50]  # Limit to 50 unique equations
    
    def _extract_figures(self, doc) -> List[str]:
        """Extract figure references from PyMuPDF document."""
        figures = []
        
        for page_num in range(len(doc)):
            page = doc[page_num]
            images = page.get_images()
            
            for img_index, img in enumerate(images):
                figures.append(f"Figure on page {page_num + 1}, index {img_index}")
        
        return figures
    
    def _extract_tables(self, text: str) -> List[str]:
        """Extract table references from text."""
        # Simple heuristic: look for "Table X" references
        table_refs = re.findall(r'Table\s+\d+', text, re.IGNORECASE)
        return list(set(table_refs))
    
    def _extract_references(self, text: str) -> List[str]:
        """Extract references/bibliography from text."""
        references = []
        
        # Look for references section
        ref_pattern = r'(?i)(?:references|bibliography)\s*\n(.*?)(?=\Z)'
        match = re.search(ref_pattern, text, re.DOTALL)
        
        if match:
            ref_text = match.group(1)
            # Split by common reference patterns
            ref_lines = re.split(r'\n\[\d+\]|\n\d+\.', ref_text)
            references = [ref.strip() for ref in ref_lines if len(ref.strip()) > 20][:100]
        
        return references


def parse_pdf(pdf_path: str, extract_images: bool = False, extract_tables: bool = True) -> Document:
    """
    Convenience function to parse a PDF file.
    
    Args:
        pdf_path: Path to PDF file
        extract_images: Whether to extract image metadata
        extract_tables: Whether to extract table information
        
    Returns:
        Document object with extracted content
    """
    parser = PDFParser(extract_images=extract_images, extract_tables=extract_tables)
    return parser.parse_pdf(pdf_path)
