"""
Base agent classes and schemas for ScholarLens.

Defines abstract base agent, Pydantic models for input/output,
and common agent functionality.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel, Field
from pathlib import Path


# ============================================================================
# Pydantic Schemas for Agent Input/Output
# ============================================================================

class AgentInput(BaseModel):
    """Base input schema for all agents."""
    session_id: str = Field(..., description="Session identifier")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class AgentOutput(BaseModel):
    """Base output schema for all agents."""
    agent_name: str = Field(..., description="Name of the agent")
    status: str = Field(..., description="Status: success, error, partial")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())
    result: Dict[str, Any] = Field(default_factory=dict, description="Agent results")
    errors: List[str] = Field(default_factory=list, description="Error messages if any")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Execution metadata")


class DocumentInput(AgentInput):
    """Input for DocumentExtractorAgent."""
    file_path: str = Field(..., description="Path to PDF file")
    extract_images: bool = Field(default=False, description="Extract image metadata")
    extract_tables: bool = Field(default=True, description="Extract table information")


class DocumentOutput(AgentOutput):
    """Output from DocumentExtractorAgent."""
    result: Dict[str, Any] = Field(
        default_factory=dict,
        description="Document with title, authors, sections, etc."
    )


class SummaryInput(AgentInput):
    """Input for SummaryAgent."""
    document: Dict[str, Any] = Field(..., description="Parsed document")
    include_tldr: bool = Field(default=True, description="Include TL;DR")
    include_detailed: bool = Field(default=True, description="Include detailed summary")


class SummaryOutput(AgentOutput):
    """Output from SummaryAgent."""
    result: Dict[str, Any] = Field(
        default_factory=lambda: {
            "tldr": "",
            "paragraph_summary": "",
            "detailed_summary": "",
            "key_findings": []
        }
    )


class MethodologyInput(AgentInput):
    """Input for MethodologyAgent."""
    document: Dict[str, Any] = Field(..., description="Parsed document")
    full_text: str = Field(..., description="Full document text")


class MethodologyOutput(AgentOutput):
    """Output from MethodologyAgent."""
    result: Dict[str, Any] = Field(
        default_factory=lambda: {
            "approach": "",
            "pipeline_stages": [],
            "data_collection": "",
            "validation": ""
        }
    )


class MathInput(AgentInput):
    """Input for MathAgent."""
    equations: List[str] = Field(default_factory=list, description="List of equations")
    context: str = Field(..., description="Surrounding context")


class MathOutput(AgentOutput):
    """Output from MathAgent."""
    result: Dict[str, Any] = Field(
        default_factory=lambda: {
            "interpretations": []
        }
    )


class CritiqueInput(AgentInput):
    """Input for CritiqueAgent."""
    document: Dict[str, Any] = Field(..., description="Parsed document")
    full_text: str = Field(..., description="Full document text")


class CritiqueOutput(AgentOutput):
    """Output from CritiqueAgent."""
    result: Dict[str, Any] = Field(
        default_factory=lambda: {
            "assumptions": [],
            "limitations": [],
            "biases": [],
            "reproducibility_score": 0.0
        }
    )


class ImplementationInput(AgentInput):
    """Input for ImplementationAgent."""
    methodology: Dict[str, Any] = Field(..., description="Methodology description")
    algorithms_text: str = Field(..., description="Algorithm descriptions")


class ImplementationOutput(AgentOutput):
    """Output from ImplementationAgent."""
    result: Dict[str, Any] = Field(
        default_factory=lambda: {
            "pseudocode": [],
            "complexity": {},
            "recommendations": []
        }
    )


class AggregatorInput(AgentInput):
    """Input for AggregatorAgent."""
    agent_outputs: Dict[str, Dict[str, Any]] = Field(
        ...,
        description="All agent outputs"
    )


class AggregatorOutput(AgentOutput):
    """Output from AggregatorAgent."""
    result: Dict[str, Any] = Field(
        default_factory=lambda: {
            "metadata": {},
            "summaries": {},
            "methodology": {},
            "math_explanations": {},
            "critique": {},
            "implementation": {},
            "final_markdown": ""
        }
    )


# ============================================================================
# Base Agent Class
# ============================================================================

class BaseAgent(ABC):
    """Abstract base class for all agents."""
    
    def __init__(
        self,
        name: str,
        logger=None,
        config=None
    ):
        """
        Initialize base agent.
        
        Args:
            name: Agent name
            logger: Logger instance
            config: Configuration object
        """
        self.name = name
        self.logger = logger
        self.config = config
    
    @abstractmethod
    def run(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the agent.
        
        Args:
            data: Input data dictionary
            
        Returns:
            Output data dictionary
        """
        pass
    
    def _validate_input(self, data: Dict[str, Any], required_fields: List[str]) -> bool:
        """
        Validate input data has required fields.
        
        Args:
            data: Input data
            required_fields: List of required field names
            
        Returns:
            True if valid, raises ValueError otherwise
        """
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            raise ValueError(f"Missing required fields: {missing_fields}")
        return True
    
    def _create_output(
        self,
        status: str,
        result: Dict[str, Any],
        errors: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create standardized output dictionary.
        
        Args:
            status: Status string
            result: Result dictionary
            errors: List of errors
            metadata: Additional metadata
            
        Returns:
            Output dictionary
        """
        return {
            "agent_name": self.name,
            "status": status,
            "timestamp": datetime.now().isoformat(),
            "result": result,
            "errors": errors or [],
            "metadata": metadata or {}
        }
    
    def _log_start(self, input_data: Dict[str, Any]) -> None:
        """Log agent start."""
        if self.logger:
            self.logger.log_agent_start(self.name, input_data)
    
    def _log_complete(self, output_data: Dict[str, Any], duration: float) -> None:
        """Log agent completion."""
        if self.logger:
            self.logger.log_agent_complete(self.name, output_data, duration)
    
    def _log_error(self, error: Exception) -> None:
        """Log agent error."""
        if self.logger:
            self.logger.log_agent_error(self.name, error)
    
    def _call_llm(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2048
    ) -> str:
        """
        Call LLM with prompt (placeholder for Gemini integration).
        
        Args:
            prompt: Prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated text
        """
        # TODO: Integrate Google Gemini LLM call here (ADK)
        # Example structure:
        #
        # from google.generativeai import GenerativeModel
        # model = GenerativeModel(self.config.GEMINI_MODEL_NAME)
        # response = model.generate_content(
        #     prompt,
        #     generation_config={
        #         'temperature': temperature,
        #         'max_output_tokens': max_tokens
        #     }
        # )
        # return response.text
        
        if self.logger:
            self.logger.info(
                f"LLM call placeholder",
                agent=self.name,
                prompt_length=len(prompt),
                temperature=temperature,
                max_tokens=max_tokens
            )
        
        return f"[LLM Response Placeholder for {self.name}]"
    
    def _format_prompt(self, template: str, **kwargs) -> str:
        """
        Format prompt template with variables.
        
        Args:
            template: Prompt template string
            **kwargs: Variables to fill in template
            
        Returns:
            Formatted prompt
        """
        return template.format(**kwargs)


# ============================================================================
# Utility Functions
# ============================================================================

def create_agent_input(
    agent_type: str,
    session_id: str,
    **kwargs
) -> AgentInput:
    """
    Create appropriate input schema for agent type.
    
    Args:
        agent_type: Type of agent
        session_id: Session ID
        **kwargs: Additional fields
        
    Returns:
        AgentInput subclass instance
    """
    input_classes = {
        'document': DocumentInput,
        'summary': SummaryInput,
        'methodology': MethodologyInput,
        'math': MathInput,
        'critique': CritiqueInput,
        'implementation': ImplementationInput,
        'aggregator': AggregatorInput
    }
    
    input_class = input_classes.get(agent_type, AgentInput)
    return input_class(session_id=session_id, **kwargs)


def validate_agent_output(output: Dict[str, Any]) -> bool:
    """
    Validate agent output has required fields.
    
    Args:
        output: Agent output dictionary
        
    Returns:
        True if valid
    """
    required_fields = ['agent_name', 'status', 'result']
    return all(field in output for field in required_fields)
