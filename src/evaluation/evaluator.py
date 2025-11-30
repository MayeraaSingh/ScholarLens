"""
Evaluation framework for ScholarLens.

Provides quality metrics and validation for agent outputs
including completeness, consistency, and structure checks.
"""

import time
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime


class ReportEvaluator:
    """Evaluates quality and completeness of research reports."""
    
    def __init__(self):
        """Initialize evaluator."""
        self.required_sections = [
            'metadata',
            'summaries',
            'methodology',
            'critique',
            'implementation'
        ]
        
        self.summary_fields = ['tldr', 'paragraph_summary', 'detailed_summary', 'key_findings']
        self.methodology_fields = ['approach', 'pipeline_stages', 'data_collection', 'validation']
        self.critique_fields = ['assumptions', 'limitations', 'biases', 'reproducibility_score']
        self.implementation_fields = ['pseudocode', 'complexity', 'recommendations']
    
    def evaluate_report(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate complete report quality.
        
        Args:
            report: Final report dictionary
            
        Returns:
            Evaluation results dictionary
        """
        evaluation = {
            'timestamp': datetime.now().isoformat(),
            'overall_score': 0.0,
            'completeness': self._check_completeness(report),
            'consistency': self._check_consistency(report),
            'structure': self._check_structure(report),
            'quality_metrics': self._calculate_quality_metrics(report),
            'issues': [],
            'recommendations': []
        }
        
        # Calculate overall score (0-100)
        evaluation['overall_score'] = self._calculate_overall_score(evaluation)
        
        # Generate recommendations
        evaluation['recommendations'] = self._generate_recommendations(evaluation)
        
        return evaluation
    
    def _check_completeness(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check if all required sections are present.
        
        Args:
            report: Report dictionary
            
        Returns:
            Completeness results
        """
        results = {
            'score': 0.0,
            'missing_sections': [],
            'incomplete_sections': [],
            'section_scores': {}
        }
        
        total_sections = len(self.required_sections)
        present_sections = 0
        
        for section in self.required_sections:
            if section in report and report[section]:
                present_sections += 1
                # Check section completeness
                section_score = self._evaluate_section_completeness(section, report[section])
                results['section_scores'][section] = section_score
                
                if section_score < 0.5:
                    results['incomplete_sections'].append(section)
            else:
                results['missing_sections'].append(section)
        
        results['score'] = present_sections / total_sections
        
        return results
    
    def _evaluate_section_completeness(
        self,
        section_name: str,
        section_data: Dict[str, Any]
    ) -> float:
        """
        Evaluate completeness of a specific section.
        
        Args:
            section_name: Name of section
            section_data: Section data
            
        Returns:
            Completeness score (0-1)
        """
        required_fields = {
            'summaries': self.summary_fields,
            'methodology': self.methodology_fields,
            'critique': self.critique_fields,
            'implementation': self.implementation_fields
        }.get(section_name, [])
        
        if not required_fields:
            return 1.0  # No specific requirements
        
        present_fields = sum(1 for field in required_fields if field in section_data and section_data[field])
        return present_fields / len(required_fields)
    
    def _check_consistency(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check consistency across different sections.
        
        Args:
            report: Report dictionary
            
        Returns:
            Consistency results
        """
        results = {
            'score': 1.0,
            'inconsistencies': []
        }
        
        # Check title consistency
        doc_title = report.get('metadata', {}).get('title', '')
        if doc_title == 'Unknown' or doc_title == 'Untitled Paper':
            results['inconsistencies'].append('Document title not properly extracted')
            results['score'] -= 0.1
        
        # Check if key findings match critique limitations
        summaries = report.get('summaries', {})
        critique = report.get('critique', {})
        
        key_findings = summaries.get('key_findings', [])
        limitations = critique.get('limitations', [])
        
        if key_findings and not limitations:
            results['inconsistencies'].append('Key findings present but no limitations identified')
            results['score'] -= 0.1
        
        # Check reproducibility score range
        repro_score = critique.get('reproducibility_score', 0)
        if repro_score < 0 or repro_score > 10:
            results['inconsistencies'].append(f'Invalid reproducibility score: {repro_score}')
            results['score'] -= 0.2
        
        # Check if methodology has pipeline stages
        methodology = report.get('methodology', {})
        pipeline_stages = methodology.get('pipeline_stages', [])
        
        if methodology.get('approach') and not pipeline_stages:
            results['inconsistencies'].append('Methodology described but no pipeline stages identified')
            results['score'] -= 0.1
        
        results['score'] = max(0.0, results['score'])
        
        return results
    
    def _check_structure(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Check structural validity of report.
        
        Args:
            report: Report dictionary
            
        Returns:
            Structure validation results
        """
        results = {
            'score': 1.0,
            'structural_issues': []
        }
        
        # Check if markdown is present
        if 'final_markdown' not in report or not report['final_markdown']:
            results['structural_issues'].append('No markdown representation generated')
            results['score'] -= 0.2
        
        # Check metadata structure
        metadata = report.get('metadata', {})
        if not isinstance(metadata, dict):
            results['structural_issues'].append('Invalid metadata structure')
            results['score'] -= 0.2
        
        # Check if lists are actually lists
        summaries = report.get('summaries', {})
        if 'key_findings' in summaries and not isinstance(summaries['key_findings'], list):
            results['structural_issues'].append('key_findings is not a list')
            results['score'] -= 0.1
        
        critique = report.get('critique', {})
        for field in ['assumptions', 'limitations', 'biases']:
            if field in critique and not isinstance(critique[field], list):
                results['structural_issues'].append(f'{field} is not a list')
                results['score'] -= 0.1
        
        results['score'] = max(0.0, results['score'])
        
        return results
    
    def _calculate_quality_metrics(self, report: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate various quality metrics.
        
        Args:
            report: Report dictionary
            
        Returns:
            Quality metrics
        """
        metrics = {}
        
        # Summary quality
        summaries = report.get('summaries', {})
        metrics['summary_quality'] = self._evaluate_summary_quality(summaries)
        
        # Critique depth
        critique = report.get('critique', {})
        metrics['critique_depth'] = self._evaluate_critique_depth(critique)
        
        # Implementation usefulness
        implementation = report.get('implementation', {})
        metrics['implementation_usefulness'] = self._evaluate_implementation_usefulness(implementation)
        
        # Math coverage
        math_explanations = report.get('math_explanations', {})
        metrics['math_coverage'] = self._evaluate_math_coverage(math_explanations)
        
        return metrics
    
    def _evaluate_summary_quality(self, summaries: Dict[str, Any]) -> float:
        """Evaluate summary quality (0-1)."""
        score = 0.0
        
        tldr = summaries.get('tldr', '')
        if tldr and len(tldr) > 20:
            score += 0.3
        
        para_summary = summaries.get('paragraph_summary', '')
        if para_summary and len(para_summary) > 100:
            score += 0.3
        
        detailed = summaries.get('detailed_summary', '')
        if detailed and len(detailed) > 300:
            score += 0.2
        
        key_findings = summaries.get('key_findings', [])
        if key_findings and len(key_findings) >= 3:
            score += 0.2
        
        return score
    
    def _evaluate_critique_depth(self, critique: Dict[str, Any]) -> float:
        """Evaluate critique depth (0-1)."""
        score = 0.0
        
        assumptions = critique.get('assumptions', [])
        if len(assumptions) >= 3:
            score += 0.25
        
        limitations = critique.get('limitations', [])
        if len(limitations) >= 3:
            score += 0.25
        
        biases = critique.get('biases', [])
        if len(biases) >= 2:
            score += 0.25
        
        repro_score = critique.get('reproducibility_score', 0)
        if 0 <= repro_score <= 10:
            score += 0.25
        
        return score
    
    def _evaluate_implementation_usefulness(self, implementation: Dict[str, Any]) -> float:
        """Evaluate implementation usefulness (0-1)."""
        score = 0.0
        
        pseudocode = implementation.get('pseudocode', [])
        if pseudocode and len(pseudocode) >= 1:
            score += 0.3
        
        complexity = implementation.get('complexity', {})
        if 'time_complexity' in complexity and 'space_complexity' in complexity:
            score += 0.3
        
        recommendations = implementation.get('recommendations', [])
        if len(recommendations) >= 3:
            score += 0.4
        
        return score
    
    def _evaluate_math_coverage(self, math_explanations: Dict[str, Any]) -> float:
        """Evaluate math coverage (0-1)."""
        interpretations = math_explanations.get('interpretations', [])
        
        if not interpretations:
            # Check if paper has no equations
            note = math_explanations.get('note', '')
            if 'no mathematical equations' in note.lower():
                return 1.0  # Perfect score if paper has no equations
            return 0.0
        
        # Score based on number of interpreted equations
        if len(interpretations) >= 5:
            return 1.0
        elif len(interpretations) >= 3:
            return 0.8
        elif len(interpretations) >= 1:
            return 0.5
        else:
            return 0.0
    
    def _calculate_overall_score(self, evaluation: Dict[str, Any]) -> float:
        """
        Calculate overall quality score (0-100).
        
        Args:
            evaluation: Evaluation dictionary
            
        Returns:
            Overall score
        """
        weights = {
            'completeness': 0.3,
            'consistency': 0.2,
            'structure': 0.2,
            'quality_metrics': 0.3
        }
        
        score = 0.0
        
        # Completeness
        score += evaluation['completeness']['score'] * weights['completeness']
        
        # Consistency
        score += evaluation['consistency']['score'] * weights['consistency']
        
        # Structure
        score += evaluation['structure']['score'] * weights['structure']
        
        # Quality metrics (average)
        quality_metrics = evaluation['quality_metrics']
        avg_quality = sum(quality_metrics.values()) / len(quality_metrics) if quality_metrics else 0
        score += avg_quality * weights['quality_metrics']
        
        return round(score * 100, 2)
    
    def _generate_recommendations(self, evaluation: Dict[str, Any]) -> List[str]:
        """
        Generate recommendations for improvement.
        
        Args:
            evaluation: Evaluation dictionary
            
        Returns:
            List of recommendations
        """
        recommendations = []
        
        # Completeness recommendations
        completeness = evaluation['completeness']
        if completeness['missing_sections']:
            recommendations.append(
                f"Add missing sections: {', '.join(completeness['missing_sections'])}"
            )
        
        if completeness['incomplete_sections']:
            recommendations.append(
                f"Complete sections: {', '.join(completeness['incomplete_sections'])}"
            )
        
        # Quality recommendations
        quality = evaluation['quality_metrics']
        
        if quality.get('summary_quality', 1.0) < 0.7:
            recommendations.append("Improve summary quality with more detailed content")
        
        if quality.get('critique_depth', 1.0) < 0.7:
            recommendations.append("Deepen critical analysis with more assumptions and limitations")
        
        if quality.get('implementation_usefulness', 1.0) < 0.7:
            recommendations.append("Add more implementation guidance and pseudo-code")
        
        # Consistency recommendations
        consistency = evaluation['consistency']
        if consistency['inconsistencies']:
            recommendations.append(f"Resolve inconsistencies: {len(consistency['inconsistencies'])} found")
        
        if not recommendations:
            recommendations.append("Report quality is excellent!")
        
        return recommendations


def evaluate_report(report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to evaluate a report.
    
    Args:
        report: Report dictionary
        
    Returns:
        Evaluation results
    """
    evaluator = ReportEvaluator()
    return evaluator.evaluate_report(report)
