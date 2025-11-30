"""
CritiqueAgent for ScholarLens.

Provides critical analysis of research papers including
assumptions, limitations, biases, and reproducibility assessment.
"""

import time
from typing import Dict, Any, List

from src.agents.base_agent import BaseAgent
from src.utils import get_logger


class CritiqueAgent(BaseAgent):
    """Performs critical analysis of research papers."""
    
    def __init__(self, logger=None, config=None):
        """
        Initialize CritiqueAgent.
        
        Args:
            logger: Logger instance
            config: Configuration object
        """
        super().__init__(name="Critique", logger=logger, config=config)
        
        if logger is None:
            self.logger = get_logger("CritiqueAgent")
    
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Perform critical analysis of the paper.
        
        Args:
            data: Must contain 'document' and 'full_text'
            
        Returns:
            Dictionary with assumptions, limitations, biases, reproducibility_score
        """
        start_time = time.time()
        self._log_start(data)
        
        try:
            # Validate input
            self._validate_input(data, ['document'])
            
            document = data['document']
            full_text = data.get('full_text', document.get('full_text', ''))
            
            # Perform critical analysis
            critique = {
                'assumptions': self._identify_assumptions(document, full_text),
                'limitations': self._identify_limitations(document, full_text),
                'biases': self._identify_biases(document, full_text),
                'reproducibility_score': self._assess_reproducibility(document, full_text),
                'generalizability': self._assess_generalizability(document, full_text),
                'ethical_considerations': self._identify_ethical_issues(document, full_text)
            }
            
            # Create output
            output = self._create_output(
                status="success",
                result=critique,
                metadata={
                    "title": document.get('title', 'Unknown')
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
    
    def _identify_assumptions(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> List[str]:
        """
        Identify explicit and implicit assumptions.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            List of assumptions
        """
        method_section = self._get_section_content(document, ['method', 'approach'])
        
        prompt = f"""
Identify key assumptions (both explicit and implicit) in this research:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')[:500]}
Methodology: {method_section[:2000]}

List 4-6 major assumptions, including:
- Data assumptions
- Theoretical assumptions
- Methodological assumptions
- Simplifying assumptions
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.7, max_tokens=600)
        
        # Placeholder response
        return [
            "The data is assumed to be independent and identically distributed (i.i.d.)",
            "The model assumes that the underlying relationships are stationary over time",
            "It is assumed that the evaluation metrics adequately capture performance",
            "The approach assumes sufficient computational resources are available",
            "External validity is assumed to hold across different domains"
        ]
    
    def _identify_limitations(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> List[str]:
        """
        Identify research limitations.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            List of limitations
        """
        # Check if paper explicitly discusses limitations
        limitations_section = self._get_section_content(
            document,
            ['limitation', 'discussion', 'conclusion']
        )
        
        prompt = f"""
Identify key limitations of this research:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')[:500]}
Discussion/Limitations: {limitations_section[:2000]}

List 4-6 important limitations, including:
- Methodological limitations
- Data limitations
- Scope limitations
- Practical limitations
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.7, max_tokens=600)
        
        # Placeholder response
        return [
            "Limited to specific types of datasets and may not generalize to all domains",
            "Computational complexity may be prohibitive for very large-scale applications",
            "Does not account for certain edge cases or outlier scenarios",
            "Evaluation is based on offline metrics and may not reflect online performance",
            "Long-term effects and stability have not been thoroughly investigated"
        ]
    
    def _identify_biases(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> List[str]:
        """
        Identify potential biases in the research.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            List of potential biases
        """
        prompt = f"""
Identify potential biases in this research:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')[:500]}

Consider:
- Selection bias
- Confirmation bias
- Publication bias
- Dataset bias
- Algorithmic bias
- Reporting bias

List 3-5 potential biases with brief explanations.
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.7, max_tokens=500)
        
        # Placeholder response
        return [
            "Selection bias: The dataset may not be representative of the full population",
            "Benchmark bias: Evaluation on standard benchmarks may favor certain approaches",
            "Reporting bias: Negative or null results may be underreported"
        ]
    
    def _assess_reproducibility(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> float:
        """
        Assess reproducibility of the research (0-10 scale).
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            Reproducibility score (0-10)
        """
        # Check for reproducibility indicators
        indicators = {
            'code_available': False,
            'data_available': False,
            'detailed_methodology': False,
            'hyperparameters_specified': False,
            'random_seed_mentioned': False
        }
        
        full_text_lower = full_text.lower()
        
        # Check for code availability
        if 'github' in full_text_lower or 'code available' in full_text_lower or 'open source' in full_text_lower:
            indicators['code_available'] = True
        
        # Check for data availability
        if 'dataset available' in full_text_lower or 'data available' in full_text_lower:
            indicators['data_available'] = True
        
        # Check for detailed methodology
        method_section = self._get_section_content(document, ['method', 'experiment'])
        if len(method_section) > 1000:
            indicators['detailed_methodology'] = True
        
        # Check for hyperparameters
        if 'hyperparameter' in full_text_lower or 'learning rate' in full_text_lower:
            indicators['hyperparameters_specified'] = True
        
        # Check for random seed
        if 'random seed' in full_text_lower or 'reproducibility' in full_text_lower:
            indicators['random_seed_mentioned'] = True
        
        # Calculate score (2 points each)
        score = sum(2.0 for v in indicators.values() if v)
        
        return round(score, 1)
    
    def _assess_generalizability(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> str:
        """
        Assess generalizability of findings.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            Generalizability assessment
        """
        prompt = f"""
Assess the generalizability of findings in this research:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')[:500]}

Consider:
- Range of datasets/domains tested
- Diversity of experimental conditions
- Scope of claims vs. evidence

Provide a brief assessment (3-4 sentences).
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.7, max_tokens=300)
        
        # Placeholder response
        return "The findings appear to be reasonably generalizable within the specific domain studied. However, broader generalization to other domains would require additional validation. The scope of experimental evaluation provides moderate confidence in the robustness of results."
    
    def _identify_ethical_issues(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> List[str]:
        """
        Identify potential ethical considerations.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            List of ethical considerations
        """
        # Check for common ethical keywords
        full_text_lower = full_text.lower()
        ethical_concerns = []
        
        if 'privacy' in full_text_lower or 'personal data' in full_text_lower:
            ethical_concerns.append("Privacy considerations regarding data collection and usage")
        
        if 'bias' in full_text_lower or 'fairness' in full_text_lower:
            ethical_concerns.append("Potential fairness and bias implications of the approach")
        
        if 'human subject' in full_text_lower or 'irb' in full_text_lower:
            ethical_concerns.append("Human subjects research with appropriate ethical oversight")
        
        if not ethical_concerns:
            ethical_concerns.append("No major ethical concerns explicitly identified in the paper")
        
        return ethical_concerns
    
    def _get_section_content(self, document: Dict[str, Any], names: List[str]) -> str:
        """Get section content by matching names."""
        sections = document.get('sections', [])
        matching_texts = []
        
        for section in sections:
            title_lower = section.get('title', '').lower()
            if any(name in title_lower for name in names):
                matching_texts.append(section.get('content', ''))
        
        return "\n\n".join(matching_texts)
