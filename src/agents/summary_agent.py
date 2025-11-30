"""
SummaryAgent for ScholarLens.

Generates multi-level summaries (TL;DR, paragraph, detailed)
and extracts key findings from research papers.
"""

import time
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..utils import get_logger, chunk_text


class SummaryAgent(BaseAgent):
    """Generates multi-level summaries of research papers."""
    
    def __init__(self, logger=None, config=None):
        """
        Initialize SummaryAgent.
        
        Args:
            logger: Logger instance
            config: Configuration object
        """
        super().__init__(name="Summary", logger=logger, config=config)
        
        if logger is None:
            self.logger = get_logger("SummaryAgent")
    
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate summaries at multiple levels.
        
        Args:
            data: Must contain 'document' key with parsed paper
            
        Returns:
            Dictionary with tldr, paragraph_summary, detailed_summary, key_findings
        """
        start_time = time.time()
        self._log_start(data)
        
        try:
            # Validate input
            self._validate_input(data, ['document'])
            
            document = data['document']
            include_tldr = data.get('include_tldr', True)
            include_detailed = data.get('include_detailed', True)
            
            # Generate summaries at different levels
            summaries = {}
            
            if include_tldr:
                summaries['tldr'] = self._generate_tldr(document)
            
            summaries['paragraph_summary'] = self._generate_paragraph_summary(document)
            
            if include_detailed:
                summaries['detailed_summary'] = self._generate_detailed_summary(document)
            
            summaries['key_findings'] = self._extract_key_findings(document)
            
            # Create output
            output = self._create_output(
                status="success",
                result=summaries,
                metadata={
                    "title": document.get('title', 'Unknown'),
                    "num_sections": len(document.get('sections', []))
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
    
    def _generate_tldr(self, document: Dict[str, Any]) -> str:
        """
        Generate TL;DR summary (2-3 sentences).
        
        Args:
            document: Document dictionary
            
        Returns:
            TL;DR string
        """
        prompt = f"""
Create a TL;DR (2-3 sentences) for this research paper:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')[:1000]}

TL;DR should capture the main contribution and key result.
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=200)
        
        # Placeholder response
        return f"TL;DR: This paper presents {document.get('title', 'a research contribution')}. The main finding demonstrates novel results in the field. The approach shows promising improvements over existing methods."
    
    def _generate_paragraph_summary(self, document: Dict[str, Any]) -> str:
        """
        Generate paragraph summary (100-150 words).
        
        Args:
            document: Document dictionary
            
        Returns:
            Paragraph summary string
        """
        prompt = f"""
Write a paragraph summary (100-150 words) for this research paper:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')}

Include: research problem, approach, key results, and significance.
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=300)
        
        # Placeholder response
        abstract = document.get('abstract', 'No abstract available')
        if len(abstract) > 500:
            return abstract[:500] + "..."
        return abstract
    
    def _generate_detailed_summary(self, document: Dict[str, Any]) -> str:
        """
        Generate detailed summary (500+ words).
        
        Args:
            document: Document dictionary
            
        Returns:
            Detailed summary string
        """
        # Collect content from key sections
        sections_text = self._get_key_sections_text(document)
        
        prompt = f"""
Write a comprehensive summary (500+ words) for this research paper:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')}

Key Sections:
{sections_text[:3000]}

Cover:
1. Background and motivation
2. Research question and objectives
3. Methodology and approach
4. Key results and findings
5. Implications and future work
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=1500)
        
        # Placeholder response
        return f"""
This paper addresses {document.get('title', 'an important research problem')}.

Background: The research builds on prior work in the field and identifies key gaps in current understanding.

Methodology: The authors employ a systematic approach combining theoretical analysis and empirical evaluation.

Results: The study demonstrates significant findings that advance the state of the art.

Implications: These results have important implications for both research and practice in the field.

Future Work: The authors identify several promising directions for extending this work.
"""
    
    def _extract_key_findings(self, document: Dict[str, Any]) -> List[str]:
        """
        Extract key findings from the paper.
        
        Args:
            document: Document dictionary
            
        Returns:
            List of key findings
        """
        # Look for results, conclusion sections
        results_text = self._get_section_by_name(document, ['result', 'conclusion', 'discussion'])
        
        prompt = f"""
Extract 3-5 key findings from this research paper:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')}
Results/Conclusions: {results_text[:2000]}

List the most important findings as bullet points.
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=500)
        
        # Placeholder response
        return [
            "The proposed method achieves state-of-the-art performance on benchmark datasets",
            "Experimental results demonstrate significant improvements over baseline approaches",
            "The approach is computationally efficient and scalable to large-scale problems",
            "Theoretical analysis provides strong guarantees on convergence and optimality"
        ]
    
    def _get_key_sections_text(self, document: Dict[str, Any]) -> str:
        """
        Get text from key sections (intro, methods, results, conclusion).
        
        Args:
            document: Document dictionary
            
        Returns:
            Combined text from key sections
        """
        sections = document.get('sections', [])
        key_section_names = ['introduction', 'method', 'result', 'conclusion', 'discussion']
        
        key_texts = []
        for section in sections:
            title_lower = section.get('title', '').lower()
            if any(name in title_lower for name in key_section_names):
                key_texts.append(f"{section['title']}: {section.get('content', '')[:1000]}")
        
        return "\n\n".join(key_texts)
    
    def _get_section_by_name(self, document: Dict[str, Any], names: List[str]) -> str:
        """
        Get section content by matching name.
        
        Args:
            document: Document dictionary
            names: List of section names to match
            
        Returns:
            Combined section text
        """
        sections = document.get('sections', [])
        matching_texts = []
        
        for section in sections:
            title_lower = section.get('title', '').lower()
            if any(name in title_lower for name in names):
                matching_texts.append(section.get('content', ''))
        
        return "\n\n".join(matching_texts)
