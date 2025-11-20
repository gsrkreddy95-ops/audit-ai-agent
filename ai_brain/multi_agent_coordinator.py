"""
Multi-Agent Coordinator

Spawns and coordinates multiple sub-agents for complex workflows.

Use cases:
- Parallel evidence collection across regions
- Concurrent exports for multiple services
- Distributed screenshot capture
- Complex multi-step workflows that can be parallelized
"""

import asyncio
import json
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from rich.live import Live
from rich.table import Table

console = Console()


class SubAgent:
    """
    A sub-agent that can execute a specific task independently.
    
    Sub-agents share the same tool executor but work on different
    portions of the overall task (e.g., different AWS regions).
    """
    
    def __init__(self, agent_id: str, tool_executor, task: Dict[str, Any]):
        """
        Initialize sub-agent.
        
        Args:
            agent_id: Unique identifier
            tool_executor: Shared tool executor
            task: Task specification for this sub-agent
        """
        self.id = agent_id
        self.tool_executor = tool_executor
        self.task = task
        self.status = "initialized"
        self.result = None
    
    def execute(self) -> Dict[str, Any]:
        """
        Execute this sub-agent's task.
        
        Returns:
            Task result
        """
        console.print(f"[dim]🤖 SubAgent-{self.id} starting: {self.task.get('description')}[/dim]")
        
        self.status = "running"
        
        try:
            tool_name = self.task.get("tool")
            params = self.task.get("params", {})
            
            result = self.tool_executor.execute_tool(tool_name, params)
            
            if result.get("status") == "success":
                self.status = "completed"
                self.result = result
                console.print(f"[green]✅ SubAgent-{self.id} completed[/green]")
            else:
                self.status = "failed"
                self.result = result
                console.print(f"[red]❌ SubAgent-{self.id} failed: {result.get('error')}[/red]")
            
            return {
                "agent_id": self.id,
                "status": self.status,
                "result": self.result
            }
            
        except Exception as e:
            self.status = "error"
            self.result = {"status": "error", "error": str(e)}
            console.print(f"[red]❌ SubAgent-{self.id} error: {e}[/red]")
            
            return {
                "agent_id": self.id,
                "status": "error",
                "error": str(e)
            }


class MultiAgentCoordinator:
    """
    Coordinates multiple sub-agents working in parallel.
    
    The coordinator:
    1. Analyzes if a task can be parallelized
    2. Splits into sub-tasks
    3. Spawns sub-agents
    4. Monitors progress
    5. Aggregates results
    """
    
    def __init__(self, tool_executor, max_parallel: int = 5):
        """
        Initialize coordinator.
        
        Args:
            tool_executor: Shared tool executor
            max_parallel: Maximum parallel sub-agents
        """
        self.tool_executor = tool_executor
        self.max_parallel = max_parallel
        self.sub_agents: List[SubAgent] = []
    
    def can_parallelize(self, plan: Dict[str, Any]) -> bool:
        """
        Determine if a plan can be parallelized.
        
        Args:
            plan: Execution plan
            
        Returns:
            True if plan can be split into parallel sub-tasks
        """
        # Check for parallelizable patterns
        steps = plan.get("steps", [])
        
        # Pattern 1: Multiple regions for same service
        regions = set()
        for step in steps:
            params = step.get("params", {})
            region = params.get("aws_region")
            if region:
                regions.add(region)
        
        if len(regions) > 1:
            return True
        
        # Pattern 2: Multiple independent services
        services = set()
        for step in steps:
            params = step.get("params", {})
            service = params.get("service")
            if service:
                services.add(service)
        
        if len(services) > 1:
            return True
        
        # Pattern 3: Explicit parallel flag
        if plan.get("parallel", False):
            return True
        
        return False
    
    def execute_parallel(
        self,
        tasks: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel using sub-agents.
        
        Args:
            tasks: List of task specifications
            
        Returns:
            Aggregated results from all sub-agents
        """
        console.print(f"\n[bold magenta]🤖 MULTI-AGENT EXECUTION ({len(tasks)} parallel tasks)[/bold magenta]\n")
        
        # Create sub-agents
        self.sub_agents = []
        for i, task in enumerate(tasks, 1):
            agent = SubAgent(f"A{i}", self.tool_executor, task)
            self.sub_agents.append(agent)
        
        # Execute in parallel with thread pool
        results = []
        
        with ThreadPoolExecutor(max_workers=min(self.max_parallel, len(tasks))) as executor:
            # Submit all tasks
            futures = {
                executor.submit(agent.execute): agent
                for agent in self.sub_agents
            }
            
            # Collect results as they complete
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                console=console
            ) as progress:
                
                task = progress.add_task(
                    "Sub-agents executing...",
                    total=len(futures)
                )
                
                for future in as_completed(futures):
                    agent = futures[future]
                    try:
                        result = future.result()
                        results.append(result)
                        progress.update(task, advance=1)
                    except Exception as e:
                        console.print(f"[red]❌ SubAgent-{agent.id} exception: {e}[/red]")
                        results.append({
                            "agent_id": agent.id,
                            "status": "error",
                            "error": str(e)
                        })
                        progress.update(task, advance=1)
        
        # Aggregate results
        successful = [r for r in results if r.get("status") == "completed"]
        failed_results = [r for r in results if r.get("status") in ("failed", "error")]
        
        console.print(f"\n[bold]📊 Multi-Agent Summary:[/bold]")
        console.print(f"  ✅ Successful: {len(successful)}")
        console.print(f"  ❌ Failed: {len(failed_results)}")
        console.print(f"  📈 Success Rate: {(len(successful)/len(results)*100) if results else 0:.0f}%\n")
        
        return {
            "success": len(failed_results) == 0,
            "total_agents": len(self.sub_agents),
            "successful": len(successful),
            "failed": len(failed_results),
            "results": results,
            "aggregated_output": self._aggregate_outputs(successful)
        }
    
    def _aggregate_outputs(self, successful_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate outputs from multiple sub-agents into a unified result.
        
        Args:
            successful_results: Results from successful sub-agents
            
        Returns:
            Aggregated output
        """
        if not successful_results:
            return {}
        
        # Collect all files/artifacts
        all_files = []
        all_data = []
        
        for result in successful_results:
            agent_result = result.get("result", {})
            
            # Collect files
            if isinstance(agent_result, dict):
                files = agent_result.get("result", {}).get("files", [])
                if files:
                    all_files.extend(files)
                
                # Collect data
                data = agent_result.get("result", {}).get("data")
                if data:
                    all_data.append(data)
        
        return {
            "files": all_files,
            "data": all_data,
            "agent_count": len(successful_results)
        }

