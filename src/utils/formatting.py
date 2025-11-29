"""
Formatting utilities for ScholarLens.

Handles conversion of analysis results to various output formats
including Markdown and JSON.
"""

import json
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path


class MarkdownFormatter:
    """Formats research analysis results into Markdown."""
    
    def __init__(self, width: int = 80):
        """
        Initialize formatter.
        
        Args:
            width: Maximum line width for formatting
        """
        self.width = width
    
    def format_header(self, title: str, level: int = 1) -> str:
        """
        Format a markdown header.
        
        Args:
            title: Header title
            level: Header level (1-6)
            
        Returns:
            Formatted header
        """
        return f"{'#' * level} {title}\n\n"
    
    def format_section(self, title: str, content: str, level: int = 2) -> str:
        """
        Format a section with title and content.
        
        Args:
            title: Section title
            content: Section content
            level: Header level
            
        Returns:
            Formatted section
        """
        section = self.format_header(title, level)
        section += f"{content}\n\n"
        return section
    
    def format_list(self, items: List[str], ordered: bool = False) -> str:
        """
        Format a list of items.
        
        Args:
            items: List items
            ordered: Whether list is ordered
            
        Returns:
            Formatted list
        """
        if ordered:
            return '\n'.join(f"{i+1}. {item}" for i, item in enumerate(items)) + '\n\n'
        else:
            return '\n'.join(f"- {item}" for item in items) + '\n\n'
    
    def format_code_block(self, code: str, language: str = "") -> str:
        """
        Format a code block.
        
        Args:
            code: Code content
            language: Programming language for syntax highlighting
            
        Returns:
            Formatted code block
        """
        return f"```{language}\n{code}\n```\n\n"
    
    def format_table(self, headers: List[str], rows: List[List[str]]) -> str:
        """
        Format a markdown table.
        
        Args:
            headers: Table headers
            rows: Table rows
            
        Returns:
            Formatted table
        """
        table = "| " + " | ".join(headers) + " |\n"
        table += "| " + " | ".join(["---"] * len(headers)) + " |\n"
        for row in rows:
            table += "| " + " | ".join(row) + " |\n"
        return table + "\n"
    
    def format_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format metadata section.
        
        Args:
            metadata: Metadata dictionary
            
        Returns:
            Formatted metadata
        """
        lines = []
        lines.append("**Paper Information**\n")
        
        if "title" in metadata:
            lines.append(f"- **Title:** {metadata['title']}")
        if "authors" in metadata:
            authors = metadata['authors']
            if isinstance(authors, list):
                authors = ", ".join(authors)
            lines.append(f"- **Authors:** {authors}")
        if "year" in metadata:
            lines.append(f"- **Year:** {metadata['year']}")
        if "venue" in metadata:
            lines.append(f"- **Venue:** {metadata['venue']}")
        
        lines.append(f"- **Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return '\n'.join(lines) + '\n\n'
    
    def format_summaries(self, summaries: Dict[str, Any]) -> str:
        """
        Format summaries section.
        
        Args:
            summaries: Summaries dictionary
            
        Returns:
            Formatted summaries
        """
        output = self.format_header("Summaries", 2)
        
        if "tldr" in summaries:
            output += self.format_section("TL;DR", summaries["tldr"], 3)
        
        if "paragraph_summary" in summaries:
            output += self.format_section("Paragraph Summary", summaries["paragraph_summary"], 3)
        
        if "detailed_summary" in summaries:
            output += self.format_section("Detailed Summary", summaries["detailed_summary"], 3)
        
        if "key_findings" in summaries:
            output += self.format_header("Key Findings", 3)
            output += self.format_list(summaries["key_findings"])
        
        return output
    
    def format_methodology(self, methodology: Dict[str, Any]) -> str:
        """
        Format methodology section.
        
        Args:
            methodology: Methodology dictionary
            
        Returns:
            Formatted methodology
        """
        output = self.format_header("Methodology", 2)
        
        if "approach" in methodology:
            output += self.format_section("Research Approach", methodology["approach"], 3)
        
        if "pipeline_stages" in methodology:
            output += self.format_header("Pipeline Stages", 3)
            output += self.format_list(methodology["pipeline_stages"], ordered=True)
        
        if "data_collection" in methodology:
            output += self.format_section("Data Collection", methodology["data_collection"], 3)
        
        if "validation" in methodology:
            output += self.format_section("Validation", methodology["validation"], 3)
        
        return output
    
    def format_math(self, math_explanations: Dict[str, Any]) -> str:
        """
        Format math explanations section.
        
        Args:
            math_explanations: Math explanations dictionary
            
        Returns:
            Formatted math section
        """
        output = self.format_header("Mathematical Analysis", 2)
        
        if "interpretations" in math_explanations:
            for i, interpretation in enumerate(math_explanations["interpretations"], 1):
                if isinstance(interpretation, dict):
                    output += self.format_header(f"Equation {i}", 3)
                    
                    if "equation" in interpretation:
                        output += "**Equation:**\n\n"
                        output += self.format_code_block(interpretation["equation"], "latex")
                    
                    if "explanation" in interpretation:
                        output += f"**Explanation:** {interpretation['explanation']}\n\n"
                    
                    if "intuition" in interpretation:
                        output += f"**Intuition:** {interpretation['intuition']}\n\n"
                else:
                    output += f"{interpretation}\n\n"
        
        return output
    
    def format_critique(self, critique: Dict[str, Any]) -> str:
        """
        Format critique section.
        
        Args:
            critique: Critique dictionary
            
        Returns:
            Formatted critique
        """
        output = self.format_header("Critical Analysis", 2)
        
        if "assumptions" in critique:
            output += self.format_header("Assumptions", 3)
            output += self.format_list(critique["assumptions"])
        
        if "limitations" in critique:
            output += self.format_header("Limitations", 3)
            output += self.format_list(critique["limitations"])
        
        if "biases" in critique:
            output += self.format_header("Potential Biases", 3)
            output += self.format_list(critique["biases"])
        
        if "reproducibility_score" in critique:
            score = critique["reproducibility_score"]
            output += self.format_section(
                "Reproducibility Score",
                f"{score}/10",
                3
            )
        
        return output
    
    def format_implementation(self, implementation: Dict[str, Any]) -> str:
        """
        Format implementation section.
        
        Args:
            implementation: Implementation dictionary
            
        Returns:
            Formatted implementation
        """
        output = self.format_header("Implementation Guidance", 2)
        
        if "pseudocode" in implementation:
            output += self.format_header("Pseudo-code", 3)
            for code_block in implementation["pseudocode"]:
                if isinstance(code_block, dict):
                    if "title" in code_block:
                        output += f"**{code_block['title']}**\n\n"
                    if "code" in code_block:
                        output += self.format_code_block(code_block["code"], "python")
                else:
                    output += self.format_code_block(str(code_block), "python")
        
        if "complexity" in implementation:
            output += self.format_header("Complexity Analysis", 3)
            for key, value in implementation["complexity"].items():
                output += f"- **{key}:** {value}\n"
            output += "\n"
        
        if "recommendations" in implementation:
            output += self.format_header("Implementation Recommendations", 3)
            output += self.format_list(implementation["recommendations"])
        
        return output
    
    def format_full_report(self, report: Dict[str, Any]) -> str:
        """
        Format complete research report.
        
        Args:
            report: Complete report dictionary
            
        Returns:
            Formatted markdown report
        """
        output = ""
        
        # Title
        title = report.get("metadata", {}).get("title", "Research Paper Analysis")
        output += self.format_header(title, 1)
        output += "---\n\n"
        
        # Metadata
        if "metadata" in report:
            output += self.format_metadata(report["metadata"])
        
        output += "---\n\n"
        
        # Summaries
        if "summaries" in report:
            output += self.format_summaries(report["summaries"])
        
        # Methodology
        if "methodology" in report:
            output += self.format_methodology(report["methodology"])
        
        # Math
        if "math_explanations" in report:
            output += self.format_math(report["math_explanations"])
        
        # Critique
        if "critique" in report:
            output += self.format_critique(report["critique"])
        
        # Implementation
        if "implementation" in report:
            output += self.format_implementation(report["implementation"])
        
        # Footer
        output += "---\n\n"
        output += f"*Generated by ScholarLens on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n"
        
        return output


def dict_to_markdown(report: Dict[str, Any], width: int = 80) -> str:
    """
    Convert report dictionary to markdown.
    
    Args:
        report: Report dictionary
        width: Maximum line width
        
    Returns:
        Markdown formatted report
    """
    formatter = MarkdownFormatter(width=width)
    return formatter.format_full_report(report)


def export_json(data: Dict[str, Any], filepath: Path, indent: int = 2) -> None:
    """
    Export data to JSON file.
    
    Args:
        data: Data to export
        filepath: Output file path
        indent: JSON indentation
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=indent, ensure_ascii=False)


def export_markdown(markdown: str, filepath: Path) -> None:
    """
    Export markdown to file.
    
    Args:
        markdown: Markdown content
        filepath: Output file path
    """
    filepath.parent.mkdir(parents=True, exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(markdown)
