"""
Base Tool - Abstract base class for all tools.

Provides common patterns:
- Standardized error handling
- Result formatting
- Logging
- Validation
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from rich.console import Console
import traceback

console = Console()


class BaseTool(ABC):
    """Abstract base class for all tools."""
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize base tool.
        
        Args:
            name: Tool name
            description: Tool description
        """
        self.name = name
        self.description = description
        self.logger = console
    
    @abstractmethod
    def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the tool.
        
        Args:
            params: Tool parameters
            
        Returns:
            Dict with 'status' ('success' | 'error') and 'result' or 'error'
        """
        pass
    
    def validate_params(self, params: Dict[str, Any], required: List[str]) -> Optional[str]:
        """
        Validate required parameters.
        
        Args:
            params: Parameters to validate
            required: List of required parameter names
            
        Returns:
            Error message if validation fails, None otherwise
        """
        missing = [p for p in required if p not in params or params[p] is None]
        if missing:
            return f"Missing required parameters: {', '.join(missing)}"
        return None
    
    def format_success(self, result: Any, message: str = None) -> Dict[str, Any]:
        """
        Format successful result.
        
        Args:
            result: Result data
            message: Optional success message
            
        Returns:
            Formatted result dict
        """
        response = {
            "status": "success",
            "result": result
        }
        if message:
            response["message"] = message
        return response
    
    def format_error(self, error: Exception, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Format error result.
        
        Args:
            error: Exception that occurred
            context: Additional context
            
        Returns:
            Formatted error dict
        """
        response = {
            "status": "error",
            "error": str(error),
            "error_type": type(error).__name__
        }
        if context:
            response["context"] = context
        
        # Include traceback in debug mode
        if console.is_terminal:
            response["traceback"] = traceback.format_exc()
        
        return response
    
    def execute_with_error_handling(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute tool with standardized error handling.
        
        Args:
            params: Tool parameters
            
        Returns:
            Formatted result dict
        """
        try:
            return self.execute(params)
        except Exception as e:
            self.logger.print(f"[red]❌ {self.name} failed: {e}[/red]")
            return self.format_error(e, {"params": params})
    
    def log_execution(self, params: Dict[str, Any], result: Dict[str, Any]):
        """
        Log tool execution.
        
        Args:
            params: Tool parameters
            result: Execution result
        """
        status = result.get("status", "unknown")
        if status == "success":
            self.logger.print(f"[green]✅ {self.name} completed successfully[/green]")
        else:
            error = result.get("error", "Unknown error")
            self.logger.print(f"[red]❌ {self.name} failed: {error}[/red]")

