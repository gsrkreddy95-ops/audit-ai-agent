"""
Async Tool Executor - Async/await support for I/O operations

Provides:
- Async tool execution
- Parallel execution support
- Non-blocking I/O operations
- Better resource utilization
"""

import asyncio
from typing import Dict, Any, List, Optional, Callable
from concurrent.futures import ThreadPoolExecutor
from rich.console import Console
from ai_brain.shared import ErrorHandler

console = Console()


class AsyncToolExecutor:
    """
    Async executor for tools that perform I/O operations.
    
    Enables parallel execution and non-blocking operations.
    """
    
    def __init__(self, max_workers: int = 5):
        """
        Initialize async executor.
        
        Args:
            max_workers: Maximum number of parallel workers
        """
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.error_handler = ErrorHandler()
    
    async def execute_async(
        self,
        tool_func: Callable,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute tool function asynchronously.
        
        Args:
            tool_func: Tool function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tool result dict
        """
        try:
            # Run in thread pool (for blocking I/O)
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                self.executor,
                tool_func,
                *args,
                **kwargs
            )
            return {"status": "success", "result": result}
        except Exception as e:
            return self.error_handler.format_error_response(e, {
                "tool_func": tool_func.__name__,
                "args": args,
                "kwargs": kwargs
            })
    
    async def execute_parallel(
        self,
        tasks: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Execute multiple tools in parallel.
        
        Args:
            tasks: List of task dicts with 'tool_func', 'args', 'kwargs'
            
        Returns:
            List of results
        """
        async_tasks = [
            self.execute_async(
                task["tool_func"],
                *task.get("args", []),
                **task.get("kwargs", {})
            )
            for task in tasks
        ]
        
        results = await asyncio.gather(*async_tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append(
                    self.error_handler.format_error_response(
                        result,
                        {"task_index": i, "task": tasks[i]}
                    )
                )
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def execute_with_timeout(
        self,
        tool_func: Callable,
        timeout: float,
        *args,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute tool with timeout.
        
        Args:
            tool_func: Tool function
            timeout: Timeout in seconds
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            Tool result or timeout error
        """
        try:
            result = await asyncio.wait_for(
                self.execute_async(tool_func, *args, **kwargs),
                timeout=timeout
            )
            return result
        except asyncio.TimeoutError:
            return {
                "status": "error",
                "error": f"Tool execution timed out after {timeout}s",
                "error_type": "TimeoutError"
            }
    
    def shutdown(self):
        """Shutdown executor."""
        self.executor.shutdown(wait=True)
        console.print("[dim]🛑 Async executor shut down[/dim]")


# Convenience functions
async def execute_tool_async(tool_func: Callable, *args, **kwargs) -> Dict[str, Any]:
    """Execute a single tool asynchronously."""
    executor = AsyncToolExecutor()
    try:
        return await executor.execute_async(tool_func, *args, **kwargs)
    finally:
        executor.shutdown()


async def execute_tools_parallel(tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Execute multiple tools in parallel."""
    executor = AsyncToolExecutor()
    try:
        return await executor.execute_parallel(tasks)
    finally:
        executor.shutdown()

