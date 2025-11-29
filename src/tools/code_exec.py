"""
Code execution tool for ScholarLens.

Provides safe execution environment for pseudo-code and small code samples
with timeout and resource limits.
"""

import sys
import io
import contextlib
import time
import signal
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ExecutionResult:
    """Result of code execution."""
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float = 0.0
    return_value: Any = None


class TimeoutError(Exception):
    """Raised when code execution times out."""
    pass


class CodeExecutor:
    """Handles safe execution of code snippets."""
    
    def __init__(
        self,
        timeout: int = 5,
        max_output_length: int = 10000
    ):
        """
        Initialize code executor.
        
        Args:
            timeout: Maximum execution time in seconds
            max_output_length: Maximum length of captured output
        """
        self.timeout = timeout
        self.max_output_length = max_output_length
    
    def execute_python(
        self,
        code: str,
        globals_dict: Optional[Dict[str, Any]] = None,
        locals_dict: Optional[Dict[str, Any]] = None
    ) -> ExecutionResult:
        """
        Execute Python code safely.
        
        Args:
            code: Python code to execute
            globals_dict: Global variables to provide
            locals_dict: Local variables to provide
            
        Returns:
            ExecutionResult with output and status
        """
        # Prepare execution environment
        if globals_dict is None:
            globals_dict = {}
        if locals_dict is None:
            locals_dict = {}
        
        # Add safe built-ins (restricted environment)
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'float': float,
            'int': int,
            'len': len,
            'list': list,
            'max': max,
            'min': min,
            'print': print,
            'range': range,
            'round': round,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'zip': zip,
        }
        
        globals_dict['__builtins__'] = safe_builtins
        
        # Capture output
        output_buffer = io.StringIO()
        error_message = None
        return_value = None
        success = False
        
        start_time = time.time()
        
        try:
            # Redirect stdout/stderr
            with contextlib.redirect_stdout(output_buffer), \
                 contextlib.redirect_stderr(output_buffer):
                
                # Execute code with timeout
                result = self._execute_with_timeout(
                    code,
                    globals_dict,
                    locals_dict,
                    self.timeout
                )
                return_value = result
            
            success = True
            
        except TimeoutError as e:
            error_message = f"Execution timed out after {self.timeout} seconds"
        except SyntaxError as e:
            error_message = f"Syntax error: {str(e)}"
        except Exception as e:
            error_message = f"{type(e).__name__}: {str(e)}"
        
        execution_time = time.time() - start_time
        
        # Get output
        output = output_buffer.getvalue()
        if len(output) > self.max_output_length:
            output = output[:self.max_output_length] + "\n... (output truncated)"
        
        return ExecutionResult(
            success=success,
            output=output,
            error=error_message,
            execution_time=execution_time,
            return_value=return_value
        )
    
    def _execute_with_timeout(
        self,
        code: str,
        globals_dict: Dict[str, Any],
        locals_dict: Dict[str, Any],
        timeout: int
    ) -> Any:
        """
        Execute code with timeout (platform-specific).
        
        Args:
            code: Code to execute
            globals_dict: Global variables
            locals_dict: Local variables
            timeout: Timeout in seconds
            
        Returns:
            Result of execution
        """
        # Note: On Windows, signal.alarm is not available
        # This is a simplified version that doesn't enforce hard timeout on Windows
        
        try:
            # Try to use signal on Unix-like systems
            if hasattr(signal, 'SIGALRM'):
                def timeout_handler(signum, frame):
                    raise TimeoutError("Code execution timed out")
                
                old_handler = signal.signal(signal.SIGALRM, timeout_handler)
                signal.alarm(timeout)
                
                try:
                    result = exec(code, globals_dict, locals_dict)
                finally:
                    signal.alarm(0)
                    signal.signal(signal.SIGALRM, old_handler)
            else:
                # Windows fallback: no hard timeout enforcement
                # In production, consider using multiprocessing with timeout
                result = exec(code, globals_dict, locals_dict)
            
            return result
            
        except Exception as e:
            raise
    
    def validate_syntax(self, code: str) -> Tuple[bool, Optional[str]]:
        """
        Validate Python syntax without executing.
        
        Args:
            code: Python code to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            compile(code, '<string>', 'exec')
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error at line {e.lineno}: {e.msg}"
        except Exception as e:
            return False, str(e)
    
    def analyze_complexity(self, code: str) -> Dict[str, Any]:
        """
        Analyze code complexity (simple metrics).
        
        Args:
            code: Python code to analyze
            
        Returns:
            Dictionary with complexity metrics
        """
        lines = [line for line in code.split('\n') if line.strip() and not line.strip().startswith('#')]
        
        # Count basic structures
        num_loops = sum(1 for line in lines if any(keyword in line for keyword in ['for ', 'while ']))
        num_conditionals = sum(1 for line in lines if 'if ' in line)
        num_functions = sum(1 for line in lines if 'def ' in line)
        num_classes = sum(1 for line in lines if 'class ' in line)
        
        return {
            'lines_of_code': len(lines),
            'num_loops': num_loops,
            'num_conditionals': num_conditionals,
            'num_functions': num_functions,
            'num_classes': num_classes,
            'cyclomatic_complexity': 1 + num_conditionals + num_loops  # Simplified
        }
    
    def sanitize_code(self, code: str) -> str:
        """
        Sanitize code by removing potentially dangerous operations.
        
        Args:
            code: Python code
            
        Returns:
            Sanitized code (or raises exception if dangerous)
        """
        dangerous_patterns = [
            'import os',
            'import sys',
            'import subprocess',
            'import socket',
            '__import__',
            'eval(',
            'exec(',
            'compile(',
            'open(',
            'file(',
            'input(',
            'raw_input(',
        ]
        
        code_lower = code.lower()
        for pattern in dangerous_patterns:
            if pattern.lower() in code_lower:
                raise ValueError(f"Dangerous operation detected: {pattern}")
        
        return code


def execute_code(
    code: str,
    timeout: int = 5,
    validate_only: bool = False
) -> ExecutionResult:
    """
    Convenience function to execute code.
    
    Args:
        code: Python code to execute
        timeout: Maximum execution time in seconds
        validate_only: Only validate syntax without executing
        
    Returns:
        ExecutionResult
    """
    executor = CodeExecutor(timeout=timeout)
    
    if validate_only:
        is_valid, error = executor.validate_syntax(code)
        return ExecutionResult(
            success=is_valid,
            output="",
            error=error
        )
    
    return executor.execute_python(code)


# Example usage for testing
if __name__ == "__main__":
    # Test basic execution
    test_code = """
result = []
for i in range(10):
    result.append(i ** 2)
print("Squares:", result)
"""
    
    executor = CodeExecutor(timeout=2)
    result = executor.execute_code(test_code)
    
    print(f"Success: {result.success}")
    print(f"Output: {result.output}")
    print(f"Time: {result.execution_time:.3f}s")
