"""
MathAgent for ScholarLens.

Interprets mathematical equations, explains their purpose and intuition,
and connects formal math to conceptual understanding.
"""

import time
from typing import Dict, Any, List

from .base_agent import BaseAgent
from ..utils import get_logger
from ..tools import clean_text


class MathAgent(BaseAgent):
    """Interprets and explains mathematical content."""
    
    def __init__(self, logger=None, config=None):
        """
        Initialize MathAgent.
        
        Args:
            logger: Logger instance
            config: Configuration object
        """
        super().__init__(name="Math", logger=logger, config=config)
        
        if logger is None:
            self.logger = get_logger("MathAgent")
    
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Interpret equations and provide explanations.
        
        Args:
            data: Must contain 'equations' and 'context'
            
        Returns:
            Dictionary with equation interpretations
        """
        start_time = time.time()
        self._log_start(data)
        
        try:
            # Validate input
            equations = data.get('equations', [])
            context = data.get('context', '')
            
            if not equations:
                # No equations found
                result = {
                    'interpretations': [],
                    'note': 'No mathematical equations found in the paper'
                }
            else:
                # Interpret each equation
                interpretations = []
                for i, equation in enumerate(equations[:20]):  # Limit to 20 equations
                    interpretation = self._interpret_equation(
                        equation,
                        context,
                        equation_number=i + 1
                    )
                    interpretations.append(interpretation)
                
                result = {
                    'interpretations': interpretations,
                    'total_equations': len(equations)
                }
            
            # Create output
            output = self._create_output(
                status="success",
                result=result,
                metadata={
                    "num_equations_analyzed": len(result.get('interpretations', []))
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
    
    def _interpret_equation(
        self,
        equation: str,
        context: str,
        equation_number: int
    ) -> Dict[str, Any]:
        """
        Interpret a single equation.
        
        Args:
            equation: LaTeX equation string
            context: Surrounding text context
            equation_number: Equation number
            
        Returns:
            Dictionary with equation, explanation, variables, intuition
        """
        # Clean equation
        from ..tools.text_cleaner import TextCleaner
        cleaner = TextCleaner()
        cleaned_eq = cleaner.clean_equation(equation)
        
        prompt = f"""
Interpret this mathematical equation from a research paper:

Equation {equation_number}: {cleaned_eq}

Context: {context[:1000]}

Provide:
1. What the equation represents/calculates
2. Meaning of each variable/symbol
3. Intuitive explanation (in plain language)
4. How it relates to the paper's main contribution

Format as structured text.
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.2, max_tokens=600)
        
        # Placeholder response
        return {
            'equation_number': equation_number,
            'equation': cleaned_eq,
            'explanation': f"This equation defines the core computational relationship in the proposed method. It combines multiple factors to produce the final output.",
            'variables': self._extract_variables(cleaned_eq),
            'intuition': "Intuitively, this equation balances different considerations to optimize the desired objective. Each term contributes a specific aspect to the overall computation.",
            'purpose': "Formalize the mathematical foundation of the proposed approach"
        }
    
    def _extract_variables(self, equation: str) -> List[Dict[str, str]]:
        """
        Extract variables from equation.
        
        Args:
            equation: Equation string
            
        Returns:
            List of variable dictionaries
        """
        # Simple heuristic: look for common LaTeX variable patterns
        import re
        
        # Find single letters and Greek letters
        variables = set()
        
        # Single letters (a-z, A-Z)
        single_vars = re.findall(r'\b[a-zA-Z]\b', equation)
        variables.update(single_vars)
        
        # Greek letters
        greek_vars = re.findall(r'\\(alpha|beta|gamma|delta|epsilon|theta|lambda|mu|sigma|pi|tau|phi|omega)', equation)
        variables.update([f'\\{g}' for g in greek_vars])
        
        # Convert to list of dicts with placeholder meanings
        var_list = []
        for var in sorted(variables):
            var_list.append({
                'symbol': var,
                'meaning': f"Variable {var} (meaning to be inferred from context)"
            })
        
        return var_list[:15]  # Limit to 15 variables
    
    def _get_equation_context(
        self,
        full_text: str,
        equation: str,
        context_window: int = 500
    ) -> str:
        """
        Get surrounding context for an equation.
        
        Args:
            full_text: Full paper text
            equation: Equation string
            context_window: Characters to include before/after
            
        Returns:
            Context string
        """
        # Try to find equation in text
        equation_clean = equation.strip()
        
        # Find position (approximate)
        pos = full_text.find(equation_clean[:50])  # Match first 50 chars
        
        if pos == -1:
            # Not found, return beginning of text
            return full_text[:context_window * 2]
        
        # Extract context
        start = max(0, pos - context_window)
        end = min(len(full_text), pos + len(equation_clean) + context_window)
        
        return full_text[start:end]
