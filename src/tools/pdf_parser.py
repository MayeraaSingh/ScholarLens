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
        # Try PDF metadata first (but validate it's not a file path)
        if 'pdf_title' in metadata and metadata['pdf_title']:
            pdf_title = metadata['pdf_title'].strip()
            # Skip if it's a file path or too generic
            if not any(x in pdf_title.lower() for x in ['.dvi', '.tex', 'untitled', 'document', '\\']):
                if len(pdf_title) > 10:
                    return pdf_title
        
        # Split text into lines
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        
        # Skip common header/footer patterns
        skip_patterns = [
            r'^full terms',
            r'^http[s]?://',
            r'^issn:',
            r'^\d+$',
            r'^page \d+',
            r'^doi:',
            r'copyright',
            r'^published',
            r'^to cite',
            r'^to link',
            r'^article views',
            r'^download',
            r'^journal homepage',
            r'^submit your',
            r'^citing articles',
            r'science and engineering$',  # Journal subtitle
            r'catalysis reviews',  # Journal name
            r'braz j med biol res',  # Brazilian journal
            r'^\d+\s+braz j',  # Page number + journal abbreviation
            r'^\(\d{4}\)',  # Year in parentheses like "(2013)"
            r'\d{4}\).*,\s*\d+:\d+,\s*\d+-\d+',  # Citation format like "2013), 55:4, 369-453"
            r'www\.',  # Website URLs
            r'^\w+\s*&\s*\w+$',  # Simple names like "Terms & Conditions"
        ]
        
        # Find the title - usually the first substantial line that's not metadata
        potential_titles = []
        for i, line in enumerate(lines[:50]):  # Check first 50 lines
            # Skip if matches any skip pattern
            if any(re.match(pattern, line.lower()) for pattern in skip_patterns):
                continue
            
            # Skip very short or very long lines
            if len(line) < 15 or len(line) > 200:
                continue
            
            # Skip lines that are mostly numbers or special characters
            if sum(c.isdigit() or not c.isalnum() for c in line) / len(line) > 0.5:
                continue
            
            # This might be the title
            potential_titles.append((i, line))
        
        # Collect all possible title candidates with multi-line continuation
        # Only consider titles from first 15 lines to avoid picking up abstract text
        title_candidates = []
        
        for idx, title in potential_titles:
            if idx > 15:  # Don't look for titles beyond line 15
                break
                
            # Check if it looks like a title (starts with capital, has multiple words)
            words = title.split()
            if len(words) >= 3:  # At least 3 words
                # Check capitalization pattern (title case or sentence case)
                caps = sum(1 for w in words if w and w[0].isupper())
                if caps >= 2:  # At least 2 capitalized words
                    candidate_title = title
                    lines_added = 0
                    
                    # Check if the next line continues it (multi-line title)
                    # Limit to 3 continuation lines to avoid abstract text
                    for next_idx in range(idx + 1, min(idx + 4, len(lines))):
                        if lines_added >= 3:  # Max 3 additional lines
                            break
                            
                        next_line = lines[next_idx].strip()
                        # Skip if too short or looks like metadata
                        if len(next_line) < 5:
                            continue
                        if any(re.match(pattern, next_line.lower()) for pattern in skip_patterns):
                            break
                        
                        # Stop if this looks like authors (has commas and "&" or "and", or has author initials pattern)
                        if ',' in next_line:
                            # Check for author patterns: "L.M. Name, F.O. Name"
                            if re.search(r'[A-Z]\.[A-Z]\.?\s+[A-Z]', next_line):
                                break  # Has initial pattern like "L.M. Araújo"
                            # Check for multiple comma-separated names
                            if ('&' in next_line or ' and ' in next_line.lower()):
                                break
                            # More than 2 commas usually means author list or affiliations
                            if next_line.count(',') >= 3:
                                break
                        
                        # Stop if ends with period (likely abstract)
                        if next_line.endswith('.'):
                            break
                        
                        # Check if this could be a title continuation (can start with lowercase in multi-line titles)
                        if next_line:
                            # Check if it's a reasonable continuation (not authors, not section heading)
                            stop_words = ['abstract', 'introduction', 'keywords', 'doi:', 'issn', 'university', 'department', 'laboratory', 'correspondence']
                            if not any(x in next_line.lower() for x in stop_words):
                                # Check it's mostly title-like (not too many uppercase initials suggesting names)
                                # Title words are usually full words, not initials
                                words = next_line.split()
                                single_letter_words = sum(1 for w in words if len(w) <= 2 and w.isupper())
                                if single_letter_words < len(words) * 0.4:  # Less than 40% single letters
                                    # Likely a title continuation
                                    candidate_title += " " + next_line
                                    lines_added += 1
                                else:
                                    break
                            else:
                                break  # Hit something else
                        else:
                            break
                    
                    # Only keep title candidates with reasonable length (10-200 chars)
                    if 10 <= len(candidate_title) <= 200:
                        title_candidates.append(candidate_title)
        
        # Return the longest title candidate (full titles are usually longer than running headers)
        # But also prefer titles that appear earlier if lengths are similar
        if title_candidates:
            # Sort by length descending, but cap at reasonable differences
            title_candidates_with_scores = []
            for i, title in enumerate(title_candidates):
                # Score: length bonus, but penalize if very far down in list
                score = len(title) - (i * 5)  # Subtract 5 points per position
                title_candidates_with_scores.append((score, title))
            
            title_candidates_with_scores.sort(reverse=True, key=lambda x: x[0])
            return title_candidates_with_scores[0][1]
        
        # Fallback: return first potential title if any
        if potential_titles:
            return potential_titles[0][1]
        
        return "Untitled Paper"
    
    def _extract_authors(self, text: str) -> List[str]:
        """Extract author names from text."""
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        authors = []
        
        # Skip patterns that are not authors
        skip_patterns = [
            r'^full terms',
            r'^http[s]?://',
            r'^\d+$',
            r'^issn:',
            r'^doi:',
            r'copyright',
            r'^journal',
            r'^published',
            r'^to cite',
            r'^article views',
        ]
        
        # Look for author patterns in first 60 lines
        found_title = False
        for i, line in enumerate(lines[:60]):
            # Skip unwanted patterns
            if any(re.match(pattern, line.lower()) for pattern in skip_patterns):
                continue
            
            # Skip very short or very long lines
            if len(line) < 5 or len(line) > 250:
                continue
            
            # Look for author patterns after we've likely passed the title
            # Authors often have: multiple names, commas, "and", "&"
            if i > 5:  # Skip first few lines (likely title/journal)
                # Check for author-like patterns
                has_comma = ',' in line
                has_and = ' and ' in line.lower() or ' & ' in line
                has_multiple_caps = sum(1 for c in line if c.isupper()) >= 3
                
                # Strong author indicators
                if (has_comma and has_and) or (has_comma and has_multiple_caps):
                    # Clean and split
                    author_text = line.replace(' and ', ',').replace(' & ', ',')
                    potential_authors = [a.strip() for a in author_text.split(',')]
                    
                    # Filter and validate author names
                    for author in potential_authors:
                        # Must be reasonable length
                        if not (5 <= len(author) <= 80):
                            continue
                        # Should have at least one space (first + last name)
                        if ' ' not in author:
                            continue
                        # Should not contain URLs or numbers
                        if 'http' in author.lower() or re.search(r'\d{4}', author):
                            continue
                        # Should mostly be letters
                        if sum(c.isalpha() or c.isspace() for c in author) / len(author) > 0.7:
                            authors.append(author)
                    
                    if authors:  # Found authors, stop searching
                        break
        
        # If no authors found, try to find a line with just capitalized names
        if not authors:
            for i, line in enumerate(lines[5:40]):  # Skip title area
                # Look for lines with multiple capitalized words (potential author line)
                words = line.split()
                caps_words = [w for w in words if w and w[0].isupper() and len(w) > 1]
                if 2 <= len(caps_words) <= 8:  # Reasonable number of name parts
                    # Check if it looks like names (not too many non-letter chars)
                    if sum(c.isalpha() or c.isspace() for c in line) / len(line) > 0.7:
                        authors.append(line)
                        break
        
        return authors if authors else ["Unknown Authors"]
    
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
