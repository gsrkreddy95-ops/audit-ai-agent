"""
Dynamic Code Execution - Lets Claude write and execute Python code on the fly

This is the KEY to making the agent truly autonomous and intelligent.
Instead of pre-built tools for everything, Claude can write code to solve new problems.
"""

import os
import sys
import subprocess
import tempfile
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from rich.console import Console
import json

console = Console()


def execute_python_code(code: str, description: str = "", timeout: int = 300, 
                       allow_network: bool = True, allow_file_write: bool = True) -> Dict[str, Any]:
    """
    Execute Python code written by Claude dynamically.
    
    This allows Claude to:
    - Write custom scripts for AWS operations (e.g., billing reports)
    - Analyze data in novel ways
    - Integrate with any API or service
    - Process evidence files
    - Generate reports
    - Anything Python can do!
    
    Args:
        code: Python code to execute
        description: What this code does (for logging)
        timeout: Max execution time in seconds
        allow_network: Whether to allow network access
        allow_file_write: Whether to allow writing files
    
    Returns:
        {
            "success": bool,
            "output": str,  # stdout
            "error": str,   # stderr if failed
            "return_value": Any,  # if code uses 'return'
            "execution_time": float
        }
    """
    try:
        console.print(f"[cyan]🧠 Executing Claude-generated code...[/cyan]")
        if description:
            console.print(f"[dim]Purpose: {description}[/dim]")
        
        # Show code preview
        code_preview = code[:500] + "..." if len(code) > 500 else code
        console.print(f"[dim]Code preview:\n{code_preview}[/dim]")
        
        # Create a temporary file for the code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            # Add imports that are commonly needed
            imports = """
import os
import sys
import json
import boto3
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path

# Add project root to path
sys.path.insert(0, '/Users/krishna/Documents/audit-ai-agent')

"""
            
            # Check if code has 'return' statement (which would be a syntax error at top level)
            if 'return ' in code or 'return{' in code:
                # Wrap code in a main function to handle return statements
                full_code = imports + """
def __main__():
""" + "\n".join("    " + line for line in code.split("\n")) + """

# Execute main function and print result
__result__ = __main__()
if __result__ is not None:
    print(__result__)
"""
            else:
                # Code doesn't have return, execute directly
                full_code = imports + code
            
            f.write(full_code)
            temp_file = f.name
        
        # Execute the code
        import time
        start_time = time.time()
        
        try:
            # Run in subprocess for safety
            result = subprocess.run(
                [sys.executable, temp_file],
                capture_output=True,
                text=True,
                timeout=timeout,
                env=os.environ.copy()
            )
            
            execution_time = time.time() - start_time
            
            # Clean up
            os.unlink(temp_file)
            
            if result.returncode == 0:
                console.print(f"[green]✅ Code executed successfully in {execution_time:.2f}s[/green]")
                output = result.stdout.strip()
                if output:
                    console.print(f"[cyan]Output:[/cyan]\n{output}")
                
                return {
                    "success": True,
                    "output": output,
                    "error": "",
                    "execution_time": execution_time
                }
            else:
                console.print(f"[red]❌ Code execution failed[/red]")
                error = result.stderr.strip()
                console.print(f"[red]Error:[/red]\n{error}")
                
                return {
                    "success": False,
                    "output": result.stdout.strip(),
                    "error": error,
                    "execution_time": execution_time
                }
        
        except subprocess.TimeoutExpired:
            os.unlink(temp_file)
            console.print(f"[red]❌ Code execution timed out after {timeout}s[/red]")
            return {
                "success": False,
                "output": "",
                "error": f"Execution timed out after {timeout} seconds",
                "execution_time": timeout
            }
        
        except Exception as e:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
            console.print(f"[red]❌ Code execution error: {e}[/red]")
            return {
                "success": False,
                "output": "",
                "error": str(e),
                "execution_time": time.time() - start_time
            }
    
    except Exception as e:
        console.print(f"[red]❌ Failed to execute code: {e}[/red]")
        traceback.print_exc()
        return {
            "success": False,
            "output": "",
            "error": f"Failed to execute code: {str(e)}",
            "execution_time": 0
        }


def analyze_past_evidence(evidence_path: str, rfi_code: Optional[str] = None, 
                         year: Optional[str] = None) -> Dict[str, Any]:
    """
    Analyze past audit evidence (SOC2, ISO, etc.) to learn patterns and requirements.
    
    This helps Claude understand:
    - What format evidence should be in
    - What level of detail is needed
    - What specific data points auditors look for
    - How to structure new evidence collection
    
    Args:
        evidence_path: Path to past evidence (can be SharePoint path or local)
        rfi_code: Optional RFI code to focus on
        year: Optional year to analyze (e.g., "FY2024")
    
    Returns:
        {
            "success": bool,
            "patterns": {
                "file_types": list,  # e.g., ["png", "csv", "pdf"]
                "naming_conventions": list,
                "required_fields": list,
                "detail_level": str
            },
            "examples": list,  # Sample evidence items
            "recommendations": str  # How to collect similar evidence
        }
    """
    try:
        console.print(f"[cyan]📚 Analyzing past evidence for learning...[/cyan]")
        if rfi_code:
            console.print(f"[dim]RFI: {rfi_code}[/dim]")
        if year:
            console.print(f"[dim]Year: {year}[/dim]")
        
        # Import required modules
        from evidence_manager.llm_evidence_analyzer import LLMEvidenceAnalyzer
        from integrations.sharepoint_browser import SharePointBrowserAccess
        
        patterns = {
            "file_types": [],
            "naming_conventions": [],
            "required_fields": [],
            "detail_level": "standard"
        }
        examples = []
        recommendations = ""
        
        # If it's a SharePoint path, use SharePoint access
        if 'sharepoint.com' in evidence_path or evidence_path.startswith('TD&R'):
            console.print("[cyan]📂 Accessing SharePoint evidence...[/cyan]")
            sp = SharePointBrowserAccess()
            if sp.connect():
                # Navigate to the evidence folder
                if sp.navigate_to_path(evidence_path):
                    # List contents
                    items = sp.list_folder_contents()
                    
                    # Analyze file types and patterns
                    for item in items:
                        if item.get('type') == 'file':
                            name = item.get('name', '')
                            ext = Path(name).suffix.lower().replace('.', '')
                            if ext and ext not in patterns['file_types']:
                                patterns['file_types'].append(ext)
                            
                            examples.append({
                                "name": name,
                                "type": ext,
                                "url": item.get('url', '')
                            })
                    
                    # Generate recommendations
                    if 'png' in patterns['file_types'] or 'jpg' in patterns['file_types']:
                        recommendations += "📸 Evidence includes screenshots. For similar evidence, use aws_take_screenshot tool.\n"
                    
                    if 'csv' in patterns['file_types'] or 'xlsx' in patterns['file_types']:
                        recommendations += "📊 Evidence includes data exports. For similar evidence, use aws_export_data or boto3 to export data.\n"
                    
                    if 'pdf' in patterns['file_types'] or 'docx' in patterns['file_types']:
                        recommendations += "📄 Evidence includes documents. For similar evidence, generate reports with compliance details.\n"
                    
                    console.print(f"[green]✅ Analyzed {len(examples)} past evidence items[/green]")
                    sp.close()
                else:
                    sp.close()
                    return {
                        "success": False,
                        "error": f"Could not navigate to {evidence_path}",
                        "patterns": patterns,
                        "examples": examples,
                        "recommendations": recommendations
                    }
            else:
                return {
                    "success": False,
                    "error": "Could not connect to SharePoint",
                    "patterns": patterns,
                    "examples": examples,
                    "recommendations": recommendations
                }
        
        # If it's a local path
        elif os.path.exists(evidence_path):
            console.print("[cyan]📂 Analyzing local evidence...[/cyan]")
            path = Path(evidence_path)
            
            if path.is_file():
                files = [path]
            else:
                files = list(path.glob('**/*'))
            
            for file in files:
                if file.is_file():
                    ext = file.suffix.lower().replace('.', '')
                    if ext and ext not in patterns['file_types']:
                        patterns['file_types'].append(ext)
                    
                    examples.append({
                        "name": file.name,
                        "type": ext,
                        "path": str(file)
                    })
            
            console.print(f"[green]✅ Analyzed {len(examples)} local evidence items[/green]")
        
        else:
            return {
                "success": False,
                "error": f"Path not found: {evidence_path}",
                "patterns": patterns,
                "examples": examples,
                "recommendations": recommendations
            }
        
        # Analyze naming conventions
        if examples:
            # Look for common patterns
            names = [ex['name'] for ex in examples]
            
            # Check for timestamps
            if any(any(c.isdigit() for c in name) for name in names):
                patterns['naming_conventions'].append("Includes timestamps or dates")
            
            # Check for service names
            services = ['rds', 'ec2', 's3', 'iam', 'cloudwatch', 'vpc', 'aurora']
            if any(any(svc in name.lower() for svc in services) for name in names):
                patterns['naming_conventions'].append("Includes AWS service names")
            
            # Check for regions
            regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
            if any(any(region in name.lower() for region in regions) for name in names):
                patterns['naming_conventions'].append("Includes AWS regions")
        
        return {
            "success": True,
            "patterns": patterns,
            "examples": examples[:10],  # Return first 10 as samples
            "recommendations": recommendations,
            "total_items": len(examples)
        }
    
    except Exception as e:
        console.print(f"[red]❌ Failed to analyze evidence: {e}[/red]")
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "patterns": {},
            "examples": [],
            "recommendations": ""
        }

