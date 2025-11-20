"""
Step-by-Step Execution Engine

The brain's execution layer that runs tools one step at a time,
monitors outputs, adapts to failures, and learns from results.

Unlike delegating to Claude, this gives the brain direct control
over the execution flow.
"""

import json
from typing import Dict, List, Optional, Any, Callable
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.panel import Panel

console = Console()


class StepExecutor:
    """
    Executes a multi-step plan with monitoring and adaptation.
    
    Features:
    - Runs tools one at a time
    - Monitors each output
    - Searches for solutions on failures
    - Adapts the plan dynamically
    - Reports progress to user
    """
    
    def __init__(self, tool_executor, knowledge_manager, web_search):
        """
        Initialize step executor.
        
        Args:
            tool_executor: ToolExecutor instance
            knowledge_manager: KnowledgeManager instance
            web_search: WebSearchTool instance
        """
        self.tool_executor = tool_executor
        self.knowledge = knowledge_manager
        self.web_search = web_search
    
    def execute_plan(
        self,
        plan: Dict[str, Any],
        max_retries_per_step: int = 2
    ) -> Dict[str, Any]:
        """
        Execute a multi-step plan.
        
        Args:
            plan: Execution plan from Brain Analysis
            max_retries_per_step: How many times to retry a failed step
            
        Returns:
            {
                "success": bool,
                "steps_completed": int,
                "steps_failed": int,
                "results": [step_results],
                "final_output": Any
            }
        """
        steps = plan.get("steps", [])
        if not steps:
            console.print("[yellow]⚠️  No steps in plan, cannot execute[/yellow]")
            return {
                "success": False,
                "error": "No execution steps provided"
            }
        
        console.print(f"\n[bold cyan]⚡ EXECUTING {len(steps)} STEPS[/bold cyan]\n")
        
        results = []
        completed = 0
        failed = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            
            for i, step in enumerate(steps, 1):
                task = progress.add_task(f"Step {i}/{len(steps)}: {step.get('description', 'Running...')}", total=None)
                
                result = self._execute_step(step, max_retries_per_step)
                results.append(result)
                
                if result.get("success"):
                    completed += 1
                    progress.update(task, description=f"[green]✓ Step {i}: {step.get('description', 'Done')}[/green]")
                else:
                    failed += 1
                    progress.update(task, description=f"[red]✗ Step {i}: {step.get('description', 'Failed')}[/red]")
                    
                    # If step is critical, stop execution
                    if step.get("critical", False):
                        console.print(f"[red]❌ Critical step failed, aborting plan[/red]")
                        break
        
        # Determine overall success
        overall_success = failed == 0
        
        console.print(f"\n[bold]📊 Execution Summary:[/bold]")
        console.print(f"  ✅ Completed: {completed}")
        console.print(f"  ❌ Failed: {failed}")
        console.print(f"  📈 Success Rate: {(completed/(completed+failed)*100) if (completed+failed) > 0 else 0:.0f}%\n")
        
        return {
            "success": overall_success,
            "steps_completed": completed,
            "steps_failed": failed,
            "results": results,
            "final_output": results[-1] if results else None
        }
    
    def _execute_step(
        self,
        step: Dict[str, Any],
        max_retries: int
    ) -> Dict[str, Any]:
        """
        Execute a single step with retry logic.
        
        Args:
            step: Step specification {tool, params, description, critical}
            max_retries: Maximum retry attempts
            
        Returns:
            Step result with success/error info
        """
        tool_name = step.get("tool")
        params = step.get("params", {})
        description = step.get("description", tool_name)
        
        last_error = None
        
        for attempt in range(1, max_retries + 1):
            try:
                console.print(f"[dim]   Executing: {tool_name}[/dim]")
                
                # Execute via tool executor
                result = self.tool_executor.execute_tool(tool_name, params)
                
                if result.get("status") == "success":
                    return {
                        "success": True,
                        "step": description,
                        "tool": tool_name,
                        "result": result.get("result"),
                        "attempts": attempt
                    }
                else:
                    last_error = result.get("error", "Unknown error")
                    console.print(f"[yellow]   Attempt {attempt} failed: {last_error}[/yellow]")
                    
                    # Try to find solution
                    if attempt < max_retries:
                        solution = self._search_for_solution(last_error, tool_name, params)
                        if solution:
                            # Adapt params based on solution
                            params = self._adapt_params(params, solution)
                            console.print(f"[cyan]   Adapting params based on solution...[/cyan]")
                        
            except Exception as e:
                last_error = str(e)
                console.print(f"[red]   Exception on attempt {attempt}: {e}[/red]")
        
        # All retries exhausted
        return {
            "success": False,
            "step": description,
            "tool": tool_name,
            "error": last_error,
            "attempts": max_retries
        }
    
    def _search_for_solution(
        self,
        error: str,
        tool_name: str,
        params: Dict[str, Any]
    ) -> Optional[str]:
        """Search for a solution to an error."""
        
        # Check knowledge base first
        solution = self.knowledge.find_error_solution(error)
        if solution:
            console.print(f"[green]   💡 Found solution in knowledge base[/green]")
            return solution.get("solution")
        
        # Search the web for error
        console.print(f"[yellow]   🌐 Searching web for solution...[/yellow]")
        search_query = f"{tool_name} error: {error[:100]}"
        
        search_result = self.web_search.search(search_query, max_results=2)
        
        if search_result.get("success"):
            answer = search_result.get("answer")
            if answer:
                # Store for future
                self.knowledge.add_error_solution(error, answer, {
                    "tool": tool_name,
                    "params": params
                })
                return answer
        
        return None
    
    def _adapt_params(
        self,
        original_params: Dict[str, Any],
        solution: str
    ) -> Dict[str, Any]:
        """
        Adapt parameters based on a solution suggestion.
        
        This is a simple heuristic-based adaptation.
        Can be enhanced with LLM-based param adjustment.
        """
        # For now, return original params
        # Future: Use LLM to intelligently modify params based on solution
        return original_params.copy()

