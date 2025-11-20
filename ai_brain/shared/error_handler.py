"""
Error Handler - Standardized error handling and retry logic.

Provides:
- Consistent error handling patterns
- Configurable retry strategies
- Error classification
- Recovery suggestions
"""

from typing import Dict, Any, Optional, Callable, List
from enum import Enum
from dataclasses import dataclass
from rich.console import Console
import time
import traceback

console = Console()


class ErrorCategory(Enum):
    """Error categories for classification."""
    NETWORK = "network"
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    RESOURCE_NOT_FOUND = "resource_not_found"
    TIMEOUT = "timeout"
    VALIDATION = "validation"
    UNKNOWN = "unknown"


@dataclass
class RetryConfig:
    """Retry configuration."""
    max_attempts: int = 3
    initial_delay: float = 1.0
    backoff_factor: float = 2.0
    max_delay: float = 60.0
    retryable_errors: List[ErrorCategory] = None
    
    def __post_init__(self):
        if self.retryable_errors is None:
            self.retryable_errors = [
                ErrorCategory.NETWORK,
                ErrorCategory.TIMEOUT,
                ErrorCategory.AUTHENTICATION
            ]


class ErrorHandler:
    """Standardized error handling and retry logic."""
    
    def __init__(self, retry_config: Optional[RetryConfig] = None):
        """
        Initialize error handler.
        
        Args:
            retry_config: Retry configuration (uses defaults if None)
        """
        self.retry_config = retry_config or RetryConfig()
    
    @staticmethod
    def classify_error(error: Exception) -> ErrorCategory:
        """
        Classify error into category.
        
        Args:
            error: Exception to classify
            
        Returns:
            Error category
        """
        error_str = str(error).lower()
        error_type = type(error).__name__
        
        # Network errors
        if any(keyword in error_str for keyword in ['connection', 'timeout', 'network', 'unreachable']):
            return ErrorCategory.NETWORK
        
        # Authentication errors
        if any(keyword in error_str for keyword in ['auth', 'unauthorized', 'invalid credentials', 'token']):
            return ErrorCategory.AUTHENTICATION
        
        # Permission errors
        if any(keyword in error_str for keyword in ['permission', 'forbidden', 'access denied', 'unauthorized']):
            return ErrorCategory.PERMISSION
        
        # Resource not found
        if any(keyword in error_str for keyword in ['not found', 'does not exist', '404']):
            return ErrorCategory.RESOURCE_NOT_FOUND
        
        # Timeout errors
        if 'timeout' in error_str or 'Timeout' in error_type:
            return ErrorCategory.TIMEOUT
        
        # Validation errors
        if any(keyword in error_str for keyword in ['invalid', 'validation', 'malformed']):
            return ErrorCategory.VALIDATION
        
        return ErrorCategory.UNKNOWN
    
    def is_retryable(self, error: Exception) -> bool:
        """
        Check if error is retryable.
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is retryable
        """
        category = self.classify_error(error)
        return category in self.retry_config.retryable_errors
    
    def retry_with_backoff(
        self,
        func: Callable,
        *args,
        error_context: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Execute function with retry and exponential backoff.
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            error_context: Context for error messages
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result
            
        Raises:
            Last exception if all retries fail
        """
        last_error = None
        delay = self.retry_config.initial_delay
        
        for attempt in range(1, self.retry_config.max_attempts + 1):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_error = e
                
                if not self.is_retryable(e):
                    console.print(f"[red]❌ Non-retryable error: {e}[/red]")
                    raise
                
                if attempt < self.retry_config.max_attempts:
                    context_msg = f" ({error_context})" if error_context else ""
                    console.print(
                        f"[yellow]⚠️  Attempt {attempt}/{self.retry_config.max_attempts} failed{context_msg}, "
                        f"retrying in {delay:.1f}s...[/yellow]"
                    )
                    time.sleep(delay)
                    delay = min(delay * self.retry_config.backoff_factor, self.retry_config.max_delay)
                else:
                    console.print(f"[red]❌ All {self.retry_config.max_attempts} attempts failed{context_msg}[/red]")
        
        raise last_error
    
    def format_error_response(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Format error into standardized response.
        
        Args:
            error: Exception that occurred
            context: Additional context
            
        Returns:
            Formatted error dict
        """
        category = self.classify_error(error)
        
        response = {
            "status": "error",
            "error": str(error),
            "error_type": type(error).__name__,
            "error_category": category.value,
            "retryable": self.is_retryable(error)
        }
        
        if context:
            response["context"] = context
        
        # Add recovery suggestions
        response["suggestions"] = self._get_recovery_suggestions(category)
        
        return response
    
    @staticmethod
    def _get_recovery_suggestions(category: ErrorCategory) -> List[str]:
        """Get recovery suggestions for error category."""
        suggestions = {
            ErrorCategory.NETWORK: [
                "Check network connectivity",
                "Verify AWS endpoint is reachable",
                "Check firewall/proxy settings"
            ],
            ErrorCategory.AUTHENTICATION: [
                "Refresh AWS credentials",
                "Verify credentials are valid",
                "Check MFA token if required"
            ],
            ErrorCategory.PERMISSION: [
                "Verify IAM permissions",
                "Check resource policies",
                "Confirm role has required access"
            ],
            ErrorCategory.RESOURCE_NOT_FOUND: [
                "Verify resource exists",
                "Check resource name/ID",
                "Confirm correct region/account"
            ],
            ErrorCategory.TIMEOUT: [
                "Increase timeout value",
                "Check network latency",
                "Verify resource is responsive"
            ],
            ErrorCategory.VALIDATION: [
                "Check parameter format",
                "Verify required fields are present",
                "Review input validation rules"
            ]
        }
        
        return suggestions.get(category, ["Review error details and retry"])

