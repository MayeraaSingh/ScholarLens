"""
DocumentExtractorAgent for ScholarLens.

Extracts structured content from research paper PDFs including
title, authors, abstract, sections, equations, and metadata.
"""

import time
from typing import Dict, Any, List
from pathlib import Path

from src.agents.base_agent import BaseAgent
from src.tools import parse_pdf, clean_text
from src.utils import get_logger


class DocumentExtractorAgent(BaseAgent):
    """Extracts and structures content from research papers."""
    
    def __init__(self, logger=None, config=None):
        """
        Initialize DocumentExtractorAgent.
        
        Args:
            logger: Logger instance
            config: Configuration object
        """
        super().__init__(name="DocumentExtractor", logger=logger, config=config)
        
        if logger is None:
            self.logger = get_logger("DocumentExtractorAgent")
    
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract content from PDF.
        
        Args:
            data: Must contain 'file_path' key
            
        Returns:
            Dictionary with extracted document structure
        """
        start_time = time.time()
        self._log_start(data)
        
        try:
            # Validate input
            self._validate_input(data, ['file_path'])
            
            file_path = data['file_path']
            extract_images = data.get('extract_images', False)
            extract_tables = data.get('extract_tables', True)
            
            # Parse PDF
            self.logger.info(f"Parsing PDF: {file_path}")
            document = parse_pdf(
                file_path,
                extract_images=extract_images,
                extract_tables=extract_tables
            )
            
            # Clean and structure content
            cleaned_doc = self._clean_document(document)
            
            # Enhance with LLM analysis (placeholder)
            enhanced_doc = self._enhance_metadata(cleaned_doc)
            
            # Create output
            result = enhanced_doc
            output = self._create_output(
                status="success",
                result=result,
                metadata={
                    "file_path": file_path,
                    "num_pages": document.metadata.get('num_pages', 0),
                    "num_sections": len(document.sections),
                    "num_equations": len(document.equations)
                }
            )
            
            duration = time.time() - start_time
            self._log_complete(output, duration)
            
            return output
            
        except Exception as e:
            self._log_error(e)
            return self._create_output(
                status="error",
                result={},
                errors=[str(e)]
            )
    
    def _clean_document(self, document) -> Dict[str, Any]:
        """
        Clean and structure document content.
        
        Args:
            document: Document object from parser
            
        Returns:
            Cleaned document dictionary
        """
        # Clean full text
        cleaned_full_text = clean_text(
            document.full_text,
            remove_latex=False,  # Keep LaTeX for equations
            normalize_unicode=True,
            normalize_whitespace=True,
            fix_line_breaks=True
        )
        
        # Clean abstract
        cleaned_abstract = clean_text(
            document.abstract,
            remove_latex=True,
            normalize_unicode=True,
            normalize_whitespace=True
        )
        
        # Clean sections
        cleaned_sections = []
        for section in document.sections:
            cleaned_content = clean_text(
                section.content,
                remove_latex=False,
                normalize_unicode=True,
                normalize_whitespace=True
            )
            cleaned_sections.append({
                'title': section.title,
                'content': cleaned_content,
                'start_page': section.start_page,
                'end_page': section.end_page,
                'level': section.level
            })
        
        return {
            'title': document.title,
            'authors': document.authors,
            'abstract': cleaned_abstract,
            'sections': cleaned_sections,
            'equations': document.equations,
            'figures': document.figures,
            'tables': document.tables,
            'references': document.references,
            'full_text': cleaned_full_text,
            'metadata': document.metadata
        }
    
    def _enhance_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Enhance document metadata using LLM.
        
        Args:
            document: Document dictionary
            
        Returns:
            Enhanced document
        """
        # TODO: Use Gemini to extract additional metadata
        # - Research domain/field
        # - Key contributions
        # - Paper type (theoretical, empirical, survey)
        # - Year, venue from text if not in metadata
        
        prompt = f"""
Analyze this research paper and extract metadata:

Title: {document['title']}
Abstract: {document['abstract'][:500]}

Extract:
1. Research field/domain
2. Paper type (theoretical/empirical/survey/mixed)
3. Key contributions (1-2 sentences)
4. Main research question

Format as JSON.
"""
        
        # Placeholder: In production, call Gemini here
        llm_response = self._call_llm(prompt, temperature=0.1, max_tokens=500)
        
        # For now, add basic enhancements
        document['metadata']['research_field'] = "Computer Science"  # Placeholder
        document['metadata']['paper_type'] = "empirical"  # Placeholder
        document['metadata']['extracted_at'] = time.time()
        
        return document
