"""Agents package for ScholarLens."""

from .base_agent import (
    BaseAgent,
    AgentInput,
    AgentOutput,
    DocumentInput,
    DocumentOutput,
    SummaryInput,
    SummaryOutput,
    MethodologyInput,
    MethodologyOutput,
    MathInput,
    MathOutput,
    CritiqueInput,
    CritiqueOutput,
    ImplementationInput,
    ImplementationOutput,
    AggregatorInput,
    AggregatorOutput,
    create_agent_input,
    validate_agent_output
)

from .document_agent import DocumentExtractorAgent
from .summary_agent import SummaryAgent
from .method_agent import MethodologyAgent
from .math_agent import MathAgent
from .critique_agent import CritiqueAgent
from .implementation_agent import ImplementationAgent
from .aggregator_agent import AggregatorAgent

__all__ = [
    # Base classes and schemas
    'BaseAgent',
    'AgentInput',
    'AgentOutput',
    'DocumentInput',
    'DocumentOutput',
    'SummaryInput',
    'SummaryOutput',
    'MethodologyInput',
    'MethodologyOutput',
    'MathInput',
    'MathOutput',
    'CritiqueInput',
    'CritiqueOutput',
    'ImplementationInput',
    'ImplementationOutput',
    'AggregatorInput',
    'AggregatorOutput',
    'create_agent_input',
    'validate_agent_output',
    
    # Specialized agents
    'DocumentExtractorAgent',
    'SummaryAgent',
    'MethodologyAgent',
    'MathAgent',
    'CritiqueAgent',
    'ImplementationAgent',
    'AggregatorAgent'
]
