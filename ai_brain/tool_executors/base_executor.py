"""
Base Tool Executor - Common patterns for all executors

Provides:
- Standardized error handling
- Result formatting
- Logging
- Validation
"""

from typing import Dict, Any, Optional
from rich.console import Console
from ai_brain.shared import ErrorHandler, CacheManager

console = Console()


class BaseToolExecutor:
    """Base class for all tool executors."""
    
    def __init__(self, error_handler: Optional[ErrorHandler] = None, cache_manager: Optional[CacheManager] = None):
        """
        Initialize base executor.
        
        Args:
            error_handler: Error handler instance
            cache_manager: Cache manager instance
        """
        self.error_handler = error_handler or ErrorHandler()
        self.cache_manager = cache_manager
        self.logger = console
    
    def execute(self, tool_name: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool with standardized error handling.
        
        Args:
            tool_name: Tool name
            params: Tool parameters
            
        Returns:
            Formatted result dict
        """
        try:
            result = self._execute_impl(tool_name, params)
            return self._format_success(result)
        except Exception as e:
            return self._format_error(e, {"tool_name": tool_name, "params": params})
    
    def _execute_impl(self, tool_name: str, params: Dict[str, Any]) -> Any:
        """
        Implementation-specific execution.
        
        Subclasses must implement this.
        """
        raise NotImplementedError("Subclasses must implement _execute_impl")
    
    def _format_success(self, result: Any) -> Dict[str, Any]:
        """Format successful result."""
        return {
            "status": "success",
            "result": result
        }
    
    def _format_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """Format error result."""
        if self.error_handler:
            return self.error_handler.format_error_response(error, context)
        
        return {
            "status": "error",
            "error": str(error),
            "error_type": type(error).__name__,
            "context": context
        }
    
    def validate_params(self, params: Dict[str, Any], required: list) -> Optional[str]:
        """Validate required parameters."""
        missing = [p for p in required if p not in params or params[p] is None]
        if missing:
            return f"Missing required parameters: {', '.join(missing)}"
        return None

