"""
Logging module for ScholarLens.

Provides structured logging with file and console output, agent tracing,
and LLM call tracking.
"""

import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime
from functools import wraps
import time
import json


class ScholarLensLogger:
    """Custom logger for ScholarLens application."""
    
    def __init__(self, name: str, log_dir: Optional[Path] = None):
        """
        Initialize logger.
        
        Args:
            name: Logger name
            log_dir: Directory for log files
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Prevent duplicate handlers
        if self.logger.handlers:
            return
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)
        
        # File handler
        if log_dir:
            log_dir.mkdir(parents=True, exist_ok=True)
            log_file = log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
            file_handler = logging.FileHandler(log_file, encoding='utf-8')
            file_handler.setLevel(logging.DEBUG)
            file_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
            )
            file_handler.setFormatter(file_formatter)
            self.logger.addHandler(file_handler)
    
    def info(self, message: str, **kwargs):
        """Log info message with optional structured data."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.info(message)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional structured data."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.debug(message)
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional structured data."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.warning(message)
    
    def error(self, message: str, **kwargs):
        """Log error message with optional structured data."""
        if kwargs:
            message = f"{message} | {json.dumps(kwargs)}"
        self.logger.error(message, exc_info=True)
    
    def log_agent_start(self, agent_name: str, input_data: Dict[str, Any]):
        """
        Log agent execution start.
        
        Args:
            agent_name: Name of the agent
            input_data: Input data to the agent
        """
        self.info(
            f"🚀 Agent started: {agent_name}",
            agent=agent_name,
            event="start",
            timestamp=datetime.now().isoformat()
        )
    
    def log_agent_complete(self, agent_name: str, output_data: Dict[str, Any], duration: float):
        """
        Log agent execution completion.
        
        Args:
            agent_name: Name of the agent
            output_data: Output data from the agent
            duration: Execution duration in seconds
        """
        self.info(
            f"✅ Agent completed: {agent_name} (duration: {duration:.2f}s)",
            agent=agent_name,
            event="complete",
            duration=duration,
            timestamp=datetime.now().isoformat()
        )
    
    def log_agent_error(self, agent_name: str, error: Exception):
        """
        Log agent execution error.
        
        Args:
            agent_name: Name of the agent
            error: Exception that occurred
        """
        self.error(
            f"❌ Agent failed: {agent_name} - {str(error)}",
            agent=agent_name,
            event="error",
            error_type=type(error).__name__,
            timestamp=datetime.now().isoformat()
        )
    
    def log_llm_call(
        self,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        latency: float,
        agent_name: str
    ):
        """
        Log LLM API call details.
        
        Args:
            model: Model name
            prompt_tokens: Number of prompt tokens
            completion_tokens: Number of completion tokens
            latency: Call latency in seconds
            agent_name: Name of the calling agent
        """
        self.info(
            f"🤖 LLM call: {model}",
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=prompt_tokens + completion_tokens,
            latency=latency,
            agent=agent_name,
            event="llm_call",
            timestamp=datetime.now().isoformat()
        )


def get_logger(name: str, log_dir: Optional[Path] = None) -> ScholarLensLogger:
    """
    Get or create a logger instance.
    
    Args:
        name: Logger name
        log_dir: Directory for log files
        
    Returns:
        ScholarLensLogger instance
    """
    return ScholarLensLogger(name, log_dir)


def time_it(func):
    """
    Decorator to measure function execution time.
    
    Args:
        func: Function to measure
        
    Returns:
        Wrapped function with timing
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        duration = time.time() - start_time
        
        # Try to get logger from self if it's a method
        if args and hasattr(args[0], 'logger'):
            logger = args[0].logger
            logger.debug(f"⏱️ {func.__name__} took {duration:.2f}s")
        
        return result
    return wrapper


def log_agent_execution(agent_name: str):
    """
    Decorator to log agent execution start/complete/error.
    
    Args:
        agent_name: Name of the agent
        
    Returns:
        Decorated function with agent logging
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            logger = getattr(self, 'logger', get_logger(agent_name))
            
            # Log start
            input_data = kwargs if kwargs else (args[0] if args else {})
            logger.log_agent_start(agent_name, input_data)
            
            start_time = time.time()
            try:
                # Execute function
                result = func(self, *args, **kwargs)
                
                # Log completion
                duration = time.time() - start_time
                logger.log_agent_complete(agent_name, result, duration)
                
                return result
            except Exception as e:
                # Log error
                logger.log_agent_error(agent_name, e)
                raise
        
        return wrapper
    return decorator


# Global logger instance
main_logger = get_logger("scholarlens")
