"""
Configuration module for ScholarLens.

Manages environment variables, API keys, model settings, and application constants.
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class ModelConfig:
    """Configuration for LLM model settings."""
    model_name: str
    temperature: float
    max_tokens: int
    top_p: float = 0.95
    top_k: int = 40


@dataclass
class ChunkingConfig:
    """Configuration for text chunking."""
    chunk_size: int
    overlap: int
    min_chunk_size: int


class Config:
    """Central configuration class for ScholarLens application."""
    
    # Project paths
    PROJECT_ROOT = Path(__file__).parent.parent.parent
    SRC_ROOT = PROJECT_ROOT / "src"
    DATA_ROOT = PROJECT_ROOT / "data"
    OUTPUTS_DIR = DATA_ROOT / "outputs"
    SAMPLES_DIR = DATA_ROOT / "samples"
    LOGS_DIR = PROJECT_ROOT / "logs"
    
    # Ensure directories exist
    OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Google Gemini configuration
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL_NAME = os.getenv("GEMINI_MODEL_NAME", "gemini-1.5-pro")
    
    # Model configurations per agent type
    MODEL_CONFIGS: Dict[str, ModelConfig] = {
        "document_extractor": ModelConfig(
            model_name=GEMINI_MODEL_NAME,
            temperature=0.1,
            max_tokens=4096
        ),
        "summary": ModelConfig(
            model_name=GEMINI_MODEL_NAME,
            temperature=0.3,
            max_tokens=2048
        ),
        "methodology": ModelConfig(
            model_name=GEMINI_MODEL_NAME,
            temperature=0.3,
            max_tokens=3072
        ),
        "math": ModelConfig(
            model_name=GEMINI_MODEL_NAME,
            temperature=0.2,
            max_tokens=4096
        ),
        "critique": ModelConfig(
            model_name=GEMINI_MODEL_NAME,
            temperature=0.7,
            max_tokens=3072
        ),
        "implementation": ModelConfig(
            model_name=GEMINI_MODEL_NAME,
            temperature=0.5,
            max_tokens=4096
        ),
        "aggregator": ModelConfig(
            model_name=GEMINI_MODEL_NAME,
            temperature=0.3,
            max_tokens=8192
        )
    }
    
    # Chunking configuration
    CHUNKING_CONFIG = ChunkingConfig(
        chunk_size=8000,  # tokens
        overlap=500,      # tokens
        min_chunk_size=100
    )
    
    # Application settings
    MAX_RETRIES = 3
    RETRY_DELAY = 2  # seconds
    RATE_LIMIT_DELAY = 1  # seconds between API calls
    
    # PDF parsing settings
    PDF_DPI = 300
    PDF_EXTRACT_IMAGES = False
    PDF_EXTRACT_TABLES = True
    
    # Logging settings
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE_MAX_BYTES = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 5
    
    # Session settings
    MAX_SESSIONS = 100
    SESSION_TIMEOUT_HOURS = 24
    
    # Output settings
    OUTPUT_JSON_INDENT = 2
    OUTPUT_MARKDOWN_WIDTH = 80
    
    @classmethod
    def get_model_config(cls, agent_name: str) -> ModelConfig:
        """
        Get model configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            ModelConfig for the agent
        """
        return cls.MODEL_CONFIGS.get(
            agent_name, 
            cls.MODEL_CONFIGS["summary"]  # default fallback
        )
    
    @classmethod
    def validate_environment(cls) -> bool:
        """
        Validate that required environment variables are set.
        
        Returns:
            True if environment is valid, False otherwise
        """
        if not cls.GEMINI_API_KEY:
            print("WARNING: GEMINI_API_KEY not set. LLM calls will fail.")
            return False
        return True
    
    @classmethod
    def get_output_path(cls, filename: str) -> Path:
        """
        Get full path for an output file.
        
        Args:
            filename: Name of the output file
            
        Returns:
            Full path to output file
        """
        return cls.OUTPUTS_DIR / filename
    
    @classmethod
    def to_dict(cls) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of config
        """
        return {
            "project_root": str(cls.PROJECT_ROOT),
            "gemini_model": cls.GEMINI_MODEL_NAME,
            "chunk_size": cls.CHUNKING_CONFIG.chunk_size,
            "overlap": cls.CHUNKING_CONFIG.overlap,
            "max_retries": cls.MAX_RETRIES,
            "log_level": cls.LOG_LEVEL
        }


# Global config instance
config = Config()
