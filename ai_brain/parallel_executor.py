"""
Parallel Execution Manager - Executes multiple AWS console actions simultaneously

When user requests screenshots/exports across multiple accounts and regions,
this module orchestrates parallel browser sessions to complete all tasks faster.

Example:
    User: "Get screenshot of IAM identity provider cloudSSO in ctr-int us-east-1 
           and ctr-prod us-east-1 eu-west-1 ap-northeast-1"
    
    ParallelExecutor detects:
    - ctr-int: us-east-1
    - ctr-prod: us-east-1, eu-west-1, ap-northeast-1
    
    Creates 4 parallel browser sessions and executes simultaneously.
"""

import threading
from typing import Dict, List, Any, Callable, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed
from rich.console import Console

console = Console()


class ParallelExecutor:
    """Manages parallel execution of AWS console actions across accounts/regions."""
    
    def __init__(self, max_workers: int = 3):
        """
        Initialize parallel executor.
        
        Args:
            max_workers: Maximum number of parallel browser sessions (default: 3)
        """
        self.max_workers = max_workers
    
    def parse_multi_account_request(self, params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Parse a single request into multiple account-region combinations.
        
        Args:
            params: Original tool parameters
            
        Returns:
            List of parameter dicts, one per account-region combination
        """
        account_param = params.get("aws_account")
        region_param = params.get("aws_region")
        
        # Normalize accounts to list
        if isinstance(account_param, str):
            # Check if comma-separated or space-separated
            accounts = [a.strip() for a in account_param.replace(',', ' ').split() if a.strip()]
        elif isinstance(account_param, (list, tuple)):
            accounts = [str(a).strip() for a in account_param if a]
        else:
            accounts = [account_param] if account_param else []
        
        # Normalize regions to list
        if isinstance(region_param, str):
            # Check if comma-separated or space-separated
            regions = [r.strip() for r in region_param.replace(',', ' ').split() if r.strip()]
        elif isinstance(region_param, (list, tuple)):
            regions = [str(r).strip() for r in region_param if r]
        else:
            regions = [region_param] if region_param else []
        
        # If no accounts/regions specified, return original params
        if not accounts or not regions:
            return [params]
        
        # Generate all combinations
        combinations = []
        for account in accounts:
            for region in regions:
                sub_params = dict(params)
                sub_params["aws_account"] = account
                sub_params["aws_region"] = region
                combinations.append(sub_params)
        
        return combinations
    
    def execute_parallel(
        self,
        execute_func: Callable[[Dict[str, Any]], Dict[str, Any]],
        params_list: List[Dict[str, Any]],
        task_name: str = "task"
    ) -> Dict[str, Any]:
        """
        Execute multiple tasks in parallel.
        
        Args:
            execute_func: Function to execute (e.g., _aws_console_action_single)
            params_list: List of parameter dicts, one per task
            task_name: Name of task for logging
            
        Returns:
            Dict with 'results' (list of successful results) and 'failures' (list of failures)
        """
        if len(params_list) == 1:
            # Single task - execute directly
            result = execute_func(params_list[0])
            return {
                "status": result.get("status", "success"),
                "results": [result] if result.get("status") == "success" else [],
                "failures": [] if result.get("status") == "success" else [result]
            }
        
        console.print(f"\n[bold cyan]🚀 Executing {len(params_list)} {task_name}(s) in parallel...[/bold cyan]")
        
        results = []
        failures = []
        results_lock = threading.Lock()
        
        def execute_with_logging(params: Dict[str, Any]) -> Dict[str, Any]:
            """Execute single task and log result."""
            account = params.get("aws_account", "unknown")
            region = params.get("aws_region", "unknown")
            
            try:
                console.print(f"[cyan]   → Starting: {account} @ {region}[/cyan]")
                result = execute_func(params)
                
                with results_lock:
                    if result.get("status") == "success":
                        results.append({
                            "account": account,
                            "region": region,
                            "result": result
                        })
                        console.print(f"[green]   ✅ Completed: {account} @ {region}[/green]")
                    else:
                        failures.append({
                            "account": account,
                            "region": region,
                            "result": result
                        })
                        console.print(f"[red]   ❌ Failed: {account} @ {region} - {result.get('error', 'Unknown error')}[/red]")
                
                return result
                
            except Exception as e:
                error_result = {
                    "status": "error",
                    "error": str(e),
                    "account": account,
                    "region": region
                }
                with results_lock:
                    failures.append({
                        "account": account,
                        "region": region,
                        "result": error_result
                    })
                console.print(f"[red]   ❌ Exception: {account} @ {region} - {str(e)}[/red]")
                return error_result
        
        # Execute in parallel
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = {executor.submit(execute_with_logging, params): params for params in params_list}
            
            # Wait for all to complete
            for future in as_completed(futures):
                try:
                    future.result()  # This will raise if there was an exception
                except Exception as e:
                    params = futures[future]
                    console.print(f"[red]   ❌ Thread exception: {params.get('aws_account')} @ {params.get('aws_region')} - {str(e)}[/red]")
        
        # Determine overall status
        if results and not failures:
            status = "success"
        elif results and failures:
            status = "partial_success"
        else:
            status = "error"
        
        console.print(f"\n[bold green]📊 Parallel execution complete: {len(results)} success, {len(failures)} failures[/bold green]")
        
        return {
            "status": status,
            "results": results,
            "failures": failures,
            "total": len(params_list),
            "successful": len(results),
            "failed": len(failures)
        }

