"""
AggregatorAgent for ScholarLens.

Synthesizes outputs from all specialized agents into a cohesive
research report with both structured data and markdown format.
"""

import time
from typing import Dict, Any, List
from datetime import datetime

from src.agents.base_agent import BaseAgent
from src.utils import get_logger, dict_to_markdown


class AggregatorAgent(BaseAgent):
    """Aggregates all agent outputs into final research report."""
    
    def __init__(self, logger=None, config=None):
        """
        Initialize AggregatorAgent.
        
        Args:
            logger: Logger instance
            config: Configuration object
        """
        super().__init__(name="Aggregator", logger=logger, config=config)
        
        if logger is None:
            self.logger = get_logger("AggregatorAgent")
    
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Aggregate all agent outputs into final report.
        
        Args:
            data: Must contain 'agent_outputs' with all agent results
            
        Returns:
            Dictionary with complete research report
        """
        start_time = time.time()
        self._log_start(data)
        
        try:
            # Validate input
            self._validate_input(data, ['agent_outputs'])
            
            agent_outputs = data['agent_outputs']
            
            # Build final report structure
            report = self._build_report_structure(agent_outputs)
            
            # Generate markdown representation
            markdown = self._generate_markdown(report)
            report['final_markdown'] = markdown
            
            # Add report metadata
            report['report_metadata'] = {
                'generated_at': datetime.now().isoformat(),
                'agents_used': list(agent_outputs.keys()),
                'report_version': '1.0'
            }
            
            # Create output
            output = self._create_output(
                status="success",
                result=report,
                metadata={
                    "num_agents": len(agent_outputs),
                    "report_size": len(markdown)
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
    
    def _build_report_structure(
        self,
        agent_outputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Build structured report from agent outputs.
        
        Args:
            agent_outputs: Dictionary of agent outputs
            
        Returns:
            Structured report dictionary
        """
        report = {}
        
        # Extract document metadata
        document_output = agent_outputs.get('DocumentExtractor', {})
        document_result = document_output.get('result', {})
        
        report['metadata'] = self._extract_metadata(document_result)
        
        # Extract summaries
        summary_output = agent_outputs.get('Summary', {})
        summary_result = summary_output.get('result', {})
        report['summaries'] = summary_result
        
        # Extract methodology
        methodology_output = agent_outputs.get('Methodology', {})
        methodology_result = methodology_output.get('result', {})
        report['methodology'] = methodology_result
        
        # Extract math explanations
        math_output = agent_outputs.get('Math', {})
        math_result = math_output.get('result', {})
        report['math_explanations'] = math_result
        
        # Extract critique
        critique_output = agent_outputs.get('Critique', {})
        critique_result = critique_output.get('result', {})
        report['critique'] = critique_result
        
        # Extract implementation
        implementation_output = agent_outputs.get('Implementation', {})
        implementation_result = implementation_output.get('result', {})
        report['implementation'] = implementation_result
        
        # Add synthesis section
        report['synthesis'] = self._synthesize_insights(agent_outputs)
        
        return report
    
    def _extract_metadata(self, document: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract and structure paper metadata.
        
        Args:
            document: Document result from DocumentExtractor
            
        Returns:
            Metadata dictionary
        """
        return {
            'title': document.get('title', 'Unknown'),
            'authors': document.get('authors', []),
            'abstract': document.get('abstract', ''),
            'num_pages': document.get('metadata', {}).get('num_pages', 0),
            'num_sections': len(document.get('sections', [])),
            'num_equations': len(document.get('equations', [])),
            'num_figures': len(document.get('figures', [])),
            'num_references': len(document.get('references', []))
        }
    
    def _synthesize_insights(
        self,
        agent_outputs: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Synthesize high-level insights from all agents.
        
        Args:
            agent_outputs: Dictionary of agent outputs
            
        Returns:
            Synthesis dictionary
        """
        # Collect key information from each agent
        summary = agent_outputs.get('Summary', {}).get('result', {})
        methodology = agent_outputs.get('Methodology', {}).get('result', {})
        critique = agent_outputs.get('Critique', {}).get('result', {})
        
        # Create synthesis prompt
        prompt = f"""
Synthesize the key insights from this research paper analysis:

Summary: {summary.get('tldr', '')}
Key Findings: {', '.join(summary.get('key_findings', [])[:3])}
Approach: {methodology.get('approach', '')}
Reproducibility Score: {critique.get('reproducibility_score', 0)}/10
Main Limitations: {', '.join(critique.get('limitations', [])[:2])}

Provide:
1. Overall assessment (2-3 sentences)
2. Practical applicability (1-2 sentences)
3. Research impact potential (1-2 sentences)
"""
        
        # TODO: integrate Gemini LLM call here (ADK)
        llm_response = self._call_llm(prompt, temperature=0.5, max_tokens=500)
        
        # Placeholder synthesis
        return {
            'overall_assessment': 'This research makes a solid contribution to the field with well-designed methodology and thorough evaluation. The approach demonstrates practical applicability while acknowledging important limitations.',
            'practical_applicability': 'The methods presented can be readily applied to real-world problems with appropriate adaptation and validation.',
            'research_impact': 'The work has potential for moderate to high impact, particularly in advancing understanding of key challenges in the domain.',
            'future_directions': [
                'Extension to broader problem domains',
                'Integration with complementary approaches',
                'Long-term validation and stability analysis'
            ]
        }
    
    def _generate_markdown(self, report: Dict[str, Any]) -> str:
        """
        Generate markdown representation of report.
        
        Args:
            report: Complete report dictionary
            
        Returns:
            Markdown string
        """
        # Use the formatting utility to generate markdown
        try:
            markdown = dict_to_markdown(report)
            return markdown
        except Exception as e:
            self.logger.error(f"Error generating markdown: {e}")
            # Fallback: simple markdown generation
            return self._generate_simple_markdown(report)
    
    def _generate_simple_markdown(self, report: Dict[str, Any]) -> str:
        """
        Generate simple markdown (fallback).
        
        Args:
            report: Report dictionary
            
        Returns:
            Simple markdown string
        """
        lines = []
        
        # Title
        title = report.get('metadata', {}).get('title', 'Research Paper Analysis')
        lines.append(f"# {title}\n")
        lines.append("---\n")
        
        # Metadata
        metadata = report.get('metadata', {})
        if metadata.get('authors'):
            authors = ', '.join(metadata['authors'])
            lines.append(f"**Authors:** {authors}\n")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        lines.append("\n---\n")
        
        # Summaries
        summaries = report.get('summaries', {})
        if summaries:
            lines.append("\n## Summaries\n")
            if summaries.get('tldr'):
                lines.append(f"\n### TL;DR\n{summaries['tldr']}\n")
            if summaries.get('paragraph_summary'):
                lines.append(f"\n### Paragraph Summary\n{summaries['paragraph_summary']}\n")
        
        # Methodology
        methodology = report.get('methodology', {})
        if methodology:
            lines.append("\n## Methodology\n")
            if methodology.get('approach'):
                lines.append(f"\n{methodology['approach']}\n")
        
        # Critique
        critique = report.get('critique', {})
        if critique:
            lines.append("\n## Critical Analysis\n")
            if critique.get('assumptions'):
                lines.append("\n### Assumptions\n")
                for assumption in critique['assumptions'][:5]:
                    lines.append(f"- {assumption}\n")
        
        # Implementation
        implementation = report.get('implementation', {})
        if implementation and implementation.get('recommendations'):
            lines.append("\n## Implementation Recommendations\n")
            for rec in implementation['recommendations'][:5]:
                lines.append(f"- {rec}\n")
        
        lines.append(f"\n---\n*Generated by ScholarLens*\n")
        
        return ''.join(lines)
