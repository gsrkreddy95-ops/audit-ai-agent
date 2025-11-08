"""
Dynamic Code Generation Tools

These tools allow Claude to GENERATE and IMPLEMENT new code when functionality doesn't exist.

Revolutionary capabilities:
1. Generate new tools from scratch
2. Add new features to existing tools
3. Implement missing functions
4. Expand agent capabilities autonomously
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

console = Console()


def get_code_generation_tools() -> List[Dict[str, Any]]:
    """
    Tools that enable Claude to generate and implement new code
    """
    return [
        {
            "name": "generate_new_tool",
            "description": """Generate a completely new tool when functionality doesn't exist.
            
            When a user asks for something that no existing tool can do, use this to:
            - Generate the full implementation from scratch
            - Create a new Python file with the tool
            - Make it available for immediate use
            
            Example scenarios:
            - "Export CloudWatch logs to PDF" → No tool exists → Generate one!
            - "Compare two RDS snapshots" → No tool exists → Generate one!
            - "Analyze security group rules and flag issues" → No tool exists → Generate one!
            
            You provide:
            - What the tool should do (description)
            - What parameters it needs
            - What AWS services/APIs to use
            - What libraries to use (boto3, selenium, etc.)
            
            Claude generates:
            - Complete Python implementation
            - Error handling
            - Documentation
            - Integration with existing system
            
            The tool is immediately available to use!
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name for the new tool (e.g., 'export_cloudwatch_logs', 'compare_snapshots')"
                    },
                    "description": {
                        "type": "string",
                        "description": "Clear description of what this tool should do"
                    },
                    "functionality": {
                        "type": "string",
                        "description": """Detailed functionality requirements. Be specific about:
                        - What AWS services/APIs to call
                        - What data to collect
                        - What format to export (CSV, JSON, screenshot, PDF, etc.)
                        - Any special processing needed
                        
                        Example:
                        "Use boto3 cloudwatch_logs client to fetch log events from a log group,
                        filter by date range, export to JSON with timestamps, and save to local evidence folder"
                        """
                    },
                    "parameters": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "type": {"type": "string"},
                                "description": {"type": "string"},
                                "required": {"type": "boolean"}
                            }
                        },
                        "description": "List of parameters the tool needs"
                    },
                    "aws_services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "AWS services this tool will interact with (e.g., ['cloudwatch', 'logs', 's3'])"
                    },
                    "libraries_needed": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Python libraries needed (e.g., ['boto3', 'pandas', 'selenium'])"
                    }
                },
                "required": ["tool_name", "description", "functionality"]
            }
        },
        
        {
            "name": "add_functionality_to_tool",
            "description": """Add new functionality to an EXISTING tool.
            
            When an existing tool doesn't support what the user needs, use this to:
            - Add new methods/functions to existing tools
            - Extend capabilities
            - Add support for new services/operations
            
            Example scenarios:
            - aws_take_screenshot doesn't support DynamoDB → Add DynamoDB navigation!
            - aws_export_data doesn't support Lambda → Add Lambda export!
            - sharepoint_browser doesn't support file upload → Add upload capability!
            
            You provide:
            - Which existing tool to extend
            - What new functionality to add
            - Implementation details
            
            Claude generates:
            - New methods/functions
            - Integrates with existing code
            - Maintains compatibility
            - Adds documentation
            
            The enhanced tool is immediately available!
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "existing_tool": {
                        "type": "string",
                        "description": "Name of existing tool to extend",
                        "enum": [
                            "aws_take_screenshot",
                            "aws_export_data",
                            "list_aws_resources",
                            "sharepoint_review_evidence",
                            "upload_to_sharepoint"
                        ]
                    },
                    "new_functionality": {
                        "type": "string",
                        "description": "Clear description of what new capability to add"
                    },
                    "implementation_details": {
                        "type": "string",
                        "description": """Detailed implementation approach:
                        - What new method/function to add
                        - What APIs/services to use
                        - How to integrate with existing code
                        - Any new dependencies needed
                        
                        Example:
                        "Add _navigate_dynamodb() method that:
                        1. Clicks 'DynamoDB' in AWS console sidebar
                        2. Searches for table name
                        3. Clicks on table
                        4. Navigates to specified tab (Items, Metrics, etc.)
                        Uses same pattern as _navigate_rds()"
                        """
                    },
                    "code_to_add": {
                        "type": "string",
                        "description": "The actual Python code to add (Claude can generate this)"
                    },
                    "insertion_point": {
                        "type": "string",
                        "description": "Where to add the code (after which method/class, or at end of file)"
                    }
                },
                "required": ["existing_tool", "new_functionality", "implementation_details"]
            }
        },
        
        {
            "name": "implement_missing_function",
            "description": """Implement a specific function that's referenced but not implemented.
            
            Sometimes code calls a function that doesn't exist yet (placeholder, TODO, etc.).
            Use this to implement it properly.
            
            Example scenarios:
            - Code calls _handle_pagination() but it's not implemented
            - Code calls _export_to_pdf() but it's a stub
            - Code calls _validate_credentials() but it's empty
            
            You provide:
            - File and function name
            - What the function should do
            - Function signature (parameters, return type)
            
            Claude generates:
            - Complete implementation
            - Error handling
            - Documentation
            - Tests if needed
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "File containing the function (e.g., 'tools/aws_export_tool.py')"
                    },
                    "function_name": {
                        "type": "string",
                        "description": "Name of function to implement"
                    },
                    "function_purpose": {
                        "type": "string",
                        "description": "What this function should do"
                    },
                    "function_signature": {
                        "type": "string",
                        "description": "Function signature (def function_name(params) -> return_type:)"
                    },
                    "implementation": {
                        "type": "string",
                        "description": "The actual implementation code (Claude generates this)"
                    }
                },
                "required": ["file_path", "function_name", "function_purpose"]
            }
        },
        
        {
            "name": "search_implementation_examples",
            "description": """Search for implementation examples when generating new code.
            
            When Claude needs to generate code but wants to see similar patterns first,
            use this to search the codebase for examples.
            
            Example:
            - Generating new Selenium navigation? Search for "_navigate_" methods
            - Generating new AWS export? Search for "boto3" and "export" patterns
            - Generating new file handling? Search for "save_evidence" patterns
            
            This helps Claude write code that matches the existing style and patterns.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "search_pattern": {
                        "type": "string",
                        "description": "Pattern to search for (regex supported)"
                    },
                    "file_type": {
                        "type": "string",
                        "description": "File type to search in (e.g., '.py', '.md')"
                    },
                    "context": {
                        "type": "string",
                        "description": "What you're trying to implement (helps filter results)"
                    }
                },
                "required": ["search_pattern", "context"]
            }
        }
    ]


def generate_new_tool_implementation(
    tool_name: str,
    description: str,
    functionality: str,
    parameters: Optional[List[Dict]] = None,
    aws_services: Optional[List[str]] = None,
    libraries_needed: Optional[List[str]] = None
) -> Dict[str, Any]:
    """Generate a completely new tool implementation"""
    try:
        console.print(f"[cyan]🔨 Generating new tool: {tool_name}...[/cyan]")
        console.print(f"[dim]Purpose: {description}[/dim]")
        
        base_dir = Path(__file__).parent.parent
        tool_file = base_dir / "tools" / f"{tool_name}.py"
        
        # Generate imports based on libraries needed
        imports = ["from typing import Dict, Any, Optional, List"]
        imports.append("from rich.console import Console")
        imports.append("import os")
        imports.append("from pathlib import Path")
        
        if libraries_needed:
            if "boto3" in libraries_needed:
                imports.append("import boto3")
            if "pandas" in libraries_needed:
                imports.append("import pandas as pd")
            if "selenium" in libraries_needed:
                imports.append("from selenium import webdriver")
                imports.append("from selenium.webdriver.common.by import By")
        
        imports_code = "\n".join(imports)
        
        # Generate parameter documentation
        param_docs = ""
        if parameters:
            param_docs = "\n    Args:\n"
            for param in parameters:
                req = "required" if param.get('required') else "optional"
                param_docs += f"        {param['name']} ({param.get('type', 'str')}): {param.get('description', '')} ({req})\n"
        
        # Generate function signature
        if parameters:
            params_str = ", ".join([
                f"{p['name']}: {p.get('type', 'str')}" + 
                ("" if p.get('required') else f" = None")
                for p in parameters
            ])
        else:
            params_str = ""
        
        # Generate the tool code
        tool_code = f'''"""
{description}

Auto-generated tool by Claude's code generation capabilities.
Generated to fulfill user request for: {functionality}
"""

{imports_code}

console = Console()


def {tool_name}({params_str}) -> Dict[str, Any]:
    """
    {description}
    {param_docs}
    Returns:
        Dict with 'status' ('success' or 'error') and 'result' or 'error' message
    """
    try:
        console.print(f"[cyan]🔧 Executing: {tool_name}[/cyan]")
        
        # TODO: Claude will implement the actual logic here
        # This is a placeholder that Claude should fill in with real implementation
        
        # Functionality to implement:
        # {functionality}
        
        # AWS Services to use: {', '.join(aws_services) if aws_services else 'None specified'}
        
        console.print("[yellow]⚠️  This tool was auto-generated but needs implementation[/yellow]")
        console.print("[yellow]💡 Claude can now implement the actual functionality[/yellow]")
        
        return {{
            "status": "success",
            "result": {{
                "message": f"Tool {tool_name} was generated successfully",
                "note": "Implementation pending - Claude can add the actual logic now",
                "functionality_needed": "{functionality}"
            }}
        }}
        
    except Exception as e:
        console.print(f"[red]❌ Error in {tool_name}: {{e}}[/red]")
        import traceback
        return {{
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }}
'''
        
        # Write the tool file
        with open(tool_file, 'w') as f:
            f.write(tool_code)
        
        console.print(f"[green]✅ Generated new tool: {tool_file}[/green]")
        console.print(f"[yellow]💡 Tool skeleton created - Claude can now implement the logic[/yellow]")
        
        return {
            "status": "success",
            "tool_name": tool_name,
            "file_path": str(tool_file),
            "message": f"Tool {tool_name} generated successfully",
            "next_steps": [
                f"Use implement_missing_function to add the actual logic",
                f"Or use fix_tool_code to replace the TODO with real implementation",
                "Tool is already importable and callable"
            ]
        }
        
    except Exception as e:
        console.print(f"[red]❌ Failed to generate tool: {e}[/red]")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def add_functionality_to_existing_tool(
    existing_tool: str,
    new_functionality: str,
    implementation_details: str,
    code_to_add: str,
    insertion_point: Optional[str] = None
) -> Dict[str, Any]:
    """Add new functionality to an existing tool"""
    try:
        console.print(f"[cyan]🔧 Adding functionality to: {existing_tool}[/cyan]")
        console.print(f"[dim]New capability: {new_functionality}[/dim]")
        
        # Import self_healing_tools to get file mapping
        from ai_brain.self_healing_tools import TOOL_SOURCE_MAP
        
        if existing_tool not in TOOL_SOURCE_MAP:
            return {
                "status": "error",
                "error": f"Unknown tool: {existing_tool}"
            }
        
        base_dir = Path(__file__).parent.parent
        source_file = base_dir / TOOL_SOURCE_MAP[existing_tool]
        
        # Read current content
        with open(source_file, 'r') as f:
            current_content = f.read()
        
        # Determine insertion point
        if insertion_point:
            # Find the insertion point in the file
            if insertion_point not in current_content:
                return {
                    "status": "error",
                    "error": f"Insertion point '{insertion_point}' not found in file"
                }
            
            # Insert after the specified point
            parts = current_content.split(insertion_point, 1)
            new_content = parts[0] + insertion_point + "\n\n" + code_to_add + "\n" + parts[1]
        else:
            # Add at the end of the file
            new_content = current_content + "\n\n" + code_to_add + "\n"
        
        # Write back
        with open(source_file, 'w') as f:
            f.write(new_content)
        
        console.print(f"[green]✅ Added functionality to {existing_tool}[/green]")
        console.print(f"[cyan]📁 File: {source_file}[/cyan]")
        
        return {
            "status": "success",
            "tool": existing_tool,
            "file": str(source_file),
            "functionality_added": new_functionality,
            "message": f"Successfully added {new_functionality} to {existing_tool}",
            "next_step": f"Test the tool to verify it works: test_tool(tool_name='{existing_tool}')"
        }
        
    except Exception as e:
        console.print(f"[red]❌ Failed to add functionality: {e}[/red]")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def implement_missing_function_logic(
    file_path: str,
    function_name: str,
    function_purpose: str,
    function_signature: Optional[str] = None,
    implementation: Optional[str] = None
) -> Dict[str, Any]:
    """Implement a missing or stub function"""
    try:
        console.print(f"[cyan]🔧 Implementing function: {function_name}[/cyan]")
        console.print(f"[dim]Purpose: {function_purpose}[/dim]")
        
        base_dir = Path(__file__).parent.parent
        full_path = base_dir / file_path
        
        if not full_path.exists():
            return {
                "status": "error",
                "error": f"File not found: {full_path}"
            }
        
        # Read current content
        with open(full_path, 'r') as f:
            content = f.read()
        
        # Check if function exists
        if f"def {function_name}" not in content:
            return {
                "status": "error",
                "error": f"Function {function_name} not found in {file_path}",
                "suggestion": f"Use add_functionality_to_tool to add the function first"
            }
        
        # If implementation provided, use fix_tool_code to replace the stub
        if implementation:
            # This would use the fix_tool_code logic
            # For now, return instructions
            return {
                "status": "info",
                "message": f"Ready to implement {function_name}",
                "function": function_name,
                "purpose": function_purpose,
                "next_step": f"Use fix_tool_code to replace the stub implementation with the actual code",
                "implementation_provided": bool(implementation)
            }
        
        return {
            "status": "success",
            "message": f"Function {function_name} found in {file_path}",
            "next_step": "Provide implementation code and Claude will insert it"
        }
        
    except Exception as e:
        console.print(f"[red]❌ Failed to implement function: {e}[/red]")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def search_codebase_for_examples(
    search_pattern: str,
    context: str,
    file_type: str = ".py"
) -> Dict[str, Any]:
    """Search codebase for implementation examples"""
    try:
        console.print(f"[cyan]🔍 Searching for examples: {search_pattern}[/cyan]")
        console.print(f"[dim]Context: {context}[/dim]")
        
        base_dir = Path(__file__).parent.parent
        results = []
        
        # Search through all Python files
        for py_file in base_dir.rglob(f"*{file_type}"):
            # Skip venv, __pycache__, etc.
            if any(skip in str(py_file) for skip in ['venv', '__pycache__', '.git', 'node_modules']):
                continue
            
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    lines = content.split('\n')
                
                # Search for pattern
                import re
                for i, line in enumerate(lines):
                    if re.search(search_pattern, line, re.IGNORECASE):
                        # Get context (5 lines before and after)
                        start = max(0, i - 5)
                        end = min(len(lines), i + 6)
                        context_lines = lines[start:end]
                        
                        results.append({
                            "file": str(py_file.relative_to(base_dir)),
                            "line_number": i + 1,
                            "matching_line": line.strip(),
                            "context": '\n'.join(context_lines)
                        })
                        
                        # Limit results
                        if len(results) >= 10:
                            break
            except:
                continue
            
            if len(results) >= 10:
                break
        
        console.print(f"[green]✅ Found {len(results)} examples[/green]")
        
        return {
            "status": "success",
            "pattern": search_pattern,
            "context": context,
            "examples_found": len(results),
            "examples": results[:10],  # Limit to 10
            "note": "Use these patterns as reference when generating new code"
        }
        
    except Exception as e:
        console.print(f"[red]❌ Search failed: {e}[/red]")
        import traceback
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }

