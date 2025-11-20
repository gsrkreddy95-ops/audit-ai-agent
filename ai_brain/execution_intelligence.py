"""
Execution Intelligence - Smart Execution Optimization

Uses LLM to:
- Optimize execution strategies
- Decide retry logic
- Handle edge cases
- Learn from performance patterns
"""

from typing import Dict, Any
from rich.console import Console

console = Console()


class ExecutionIntelligence:
    """LLM-driven execution optimization."""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.enabled = llm is not None
        self.performance_history = {}
    
    def optimize_execution(
        self,
        tool_name: str,
        params: Dict[str, Any],
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Optimize execution parameters based on past performance.
        
        Args:
            tool_name: Tool to execute
            params: Proposed parameters
            context: Additional context
            
        Returns:
            Optimized parameters and strategy
        """
        if not self.enabled:
            return {"params": params, "strategy": "default"}
        
        # Check performance history
        history = self.performance_history.get(tool_name, [])
        
        if history:
            # Use LLM to optimize based on history
            # For now, return defaults
            pass
        
        return {
            "params": params,
            "strategy": "default",
            "reasoning": "No optimization needed"
        }
    
    def should_retry(
        self,
        tool_name: str,
        error: Exception,
        attempt: int
    ) -> bool:
        """
        Decide if retry makes sense.
        
        Args:
            tool_name: Tool that failed
            error: The error
            attempt: Current attempt number
            
        Returns:
            True if should retry
        """
        if not self.enabled:
            # Default retry logic
            return attempt < 3
        
        # Could ask LLM for smarter retry decisions
        # For now, use simple logic
        return attempt < 3
    
    def record_performance(
        self,
        tool_name: str,
        duration: float,
        success: bool,
        params: Dict[str, Any]
    ) -> None:
        """
        Record performance metrics for learning.
        """
        if tool_name not in self.performance_history:
            self.performance_history[tool_name] = []
        
        self.performance_history[tool_name].append({
            "duration": duration,
            "success": success,
            "params": params
        })
        
        # Keep only last 100 executions
        if len(self.performance_history[tool_name]) > 100:
            self.performance_history[tool_name] = self.performance_history[tool_name][-100:]


def get_execution_intelligence(llm=None):
    """Get execution intelligence instance."""
    return ExecutionIntelligence(llm)
