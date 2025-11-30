"""
MethodologyAgent for ScholarLens.

Extracts and explains research methodology, experimental pipeline,
data collection, and validation approaches.
"""

import time
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..utils import get_logger


class MethodologyAgent(BaseAgent):
    """Analyzes and explains research methodology."""
    
    def __init__(self, logger=None, config=None):
        """
        Initialize MethodologyAgent.
        
        Args:
            logger: Logger instance
            config: Configuration object
        """
        super().__init__(name="Methodology", logger=logger, config=config)
        
        if logger is None:
            self.logger = get_logger("MethodologyAgent")
    
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and explain methodology.
        
        Args:
            data: Must contain 'document' and 'full_text'
            
        Returns:
            Dictionary with approach, pipeline_stages, data_collection, validation
        """
        start_time = time.time()
        self._log_start(data)
        
        try:
            # Validate input
            self._validate_input(data, ['document'])
            
            document = data['document']
            full_text = data.get('full_text', document.get('full_text', ''))
            
            # Extract methodology components
            methodology = {
                'approach': self._identify_research_approach(document, full_text),
                'pipeline_stages': self._extract_pipeline_stages(document, full_text),
                'data_collection': self._extract_data_collection(document, full_text),
                'validation': self._extract_validation_approach(document, full_text)
            }
            
            # Create output
            output = self._create_output(
                status="success",
                result=methodology,
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
    
    def _identify_research_approach(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> str:
        """
        Identify research approach (theoretical/empirical/mixed).
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            Research approach description
        """
        # Get methodology section
        method_section = self._get_methodology_section(document)
        
        prompt = f"""
Identify the research approach used in this paper:

Title: {document.get('title', '')}
Abstract: {document.get('abstract', '')[:500]}
Methodology Section: {method_section[:2000]}

Classify as: theoretical, empirical, mixed-methods, or survey.
Explain the approach in 2-3 sentences.
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=300)
        
        # Placeholder response
        return "The paper employs an empirical research approach, combining theoretical analysis with experimental validation. The methodology includes both algorithmic development and comprehensive evaluation on benchmark datasets."
    
    def _extract_pipeline_stages(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> List[str]:
        """
        Extract experimental pipeline stages.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            List of pipeline stages
        """
        method_section = self._get_methodology_section(document)
        
        prompt = f"""
Extract the experimental/methodological pipeline stages from this paper:

Methodology: {method_section[:3000]}

List the main stages in order (e.g., "1. Data preprocessing", "2. Model training", etc.)
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=500)
        
        # Placeholder response
        return [
            "Data collection and preprocessing",
            "Feature engineering and selection",
            "Model architecture design",
            "Training and optimization",
            "Evaluation on benchmark datasets",
            "Statistical analysis and comparison"
        ]
    
    def _extract_data_collection(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> str:
        """
        Extract data collection methodology.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            Data collection description
        """
        method_section = self._get_methodology_section(document)
        
        prompt = f"""
Describe the data collection methodology from this paper:

Methodology: {method_section[:2000]}

Explain:
- Data sources
- Collection procedures
- Sample size and characteristics
- Data quality measures
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=400)
        
        # Placeholder response
        return "Data was collected from established benchmark datasets in the field. The dataset includes diverse samples ensuring comprehensive coverage. Quality control measures were applied to ensure data integrity and reliability."
    
    def _extract_validation_approach(
        self,
        document: Dict[str, Any],
        full_text: str
    ) -> str:
        """
        Extract validation and evaluation approach.
        
        Args:
            document: Document dictionary
            full_text: Full paper text
            
        Returns:
            Validation approach description
        """
        method_section = self._get_methodology_section(document)
        results_section = self._get_section_by_name(document, ['result', 'evaluation', 'experiment'])
        
        prompt = f"""
Describe the validation and evaluation approach:

Methodology: {method_section[:1500]}
Results/Evaluation: {results_section[:1500]}

Explain:
- Evaluation metrics used
- Baseline comparisons
- Statistical tests
- Cross-validation or hold-out strategy
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.3, max_tokens=400)
        
        # Placeholder response
        return "The approach is validated using standard evaluation metrics including accuracy, precision, and recall. Results are compared against established baseline methods. Statistical significance testing ensures robustness of findings."
    
    def _get_methodology_section(self, document: Dict[str, Any]) -> str:
        """
        Get methodology section content.
        
        Args:
            document: Document dictionary
            
        Returns:
            Methodology section text
        """
        sections = document.get('sections', [])
        method_keywords = ['method', 'approach', 'procedure', 'experiment', 'design']
        
        for section in sections:
            title_lower = section.get('title', '').lower()
            if any(keyword in title_lower for keyword in method_keywords):
                return section.get('content', '')
        
        # Fallback: return abstract or empty
        return document.get('abstract', '')
    
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
