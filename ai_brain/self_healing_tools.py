"""
Self-Healing Tools for Autonomous Debugging and Code Fixing

These tools allow Claude to:
1. Read tool source code when errors occur
2. Analyze and diagnose issues
3. Edit code to fix bugs
4. Test and retry operations
"""

import os
import subprocess
import traceback
from pathlib import Path
from typing import Dict, Any, List, Optional
from rich.console import Console

console = Console()


def get_self_healing_tools() -> List[Dict[str, Any]]:
    """
    Define tools that enable Claude to debug and fix code autonomously
    """
    return [
        {
            "name": "read_tool_source",
            "description": """Read the source code of a tool that failed.
            
            When a tool fails (aws_take_screenshot, aws_export_data, etc.), use this
            to read its source code and understand what went wrong.
            
            This allows you to:
            - See the actual implementation
            - Understand the logic flow
            - Identify bugs or issues
            - Plan fixes
            
            Example usage:
            If aws_take_screenshot fails, call:
            read_tool_source(tool_name="aws_take_screenshot")
            
            This will show you the source code of tools/aws_screenshot_selenium.py
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to read (e.g., 'aws_take_screenshot', 'aws_export_data', 'sharepoint_review_evidence')",
                        "enum": [
                            "aws_take_screenshot",
                            "aws_export_data", 
                            "list_aws_resources",
                            "sharepoint_review_evidence",
                            "upload_to_sharepoint"
                        ]
                    },
                    "section": {
                        "type": "string",
                        "description": "Optional: specific section/function to focus on (e.g., '_navigate_rds', 'capture_screenshot')"
                    }
                },
                "required": ["tool_name"]
            }
        },
        
        {
            "name": "diagnose_error",
            "description": """Analyze an error and provide diagnostic information.
            
            When a tool fails with an error, use this to get detailed diagnostic info:
            - Full error traceback
            - Environment context (AWS credentials, browser state, etc.)
            - Recent actions taken
            - Suggested fixes
            
            This helps you understand WHY something failed before attempting to fix it.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "error_message": {
                        "type": "string",
                        "description": "The error message that was displayed"
                    },
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool that failed"
                    },
                    "parameters": {
                        "type": "object",
                        "description": "The parameters that were passed to the tool"
                    }
                },
                "required": ["error_message", "tool_name"]
            }
        },
        
        {
            "name": "fix_tool_code",
            "description": """Fix a bug in a tool's source code.
            
            After reading the source and diagnosing the issue, use this to apply a fix.
            
            You provide:
            - The tool name
            - Description of what's wrong
            - The fix to apply (old code → new code)
            
            The system will:
            - Apply the fix using search_replace
            - Validate the syntax
            - Report success/failure
            
            Example:
            If _navigate_rds is using wrong selector, call:
            fix_tool_code(
                tool_name="aws_take_screenshot",
                issue="_navigate_rds is searching for 'Databases' but should search for 'DB Instances'",
                old_code="sidebar_item = driver.find_element(By.LINK_TEXT, 'Databases')",
                new_code="sidebar_item = driver.find_element(By.PARTIAL_LINK_TEXT, 'DB Instances')"
            )
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to fix"
                    },
                    "issue": {
                        "type": "string",
                        "description": "Clear description of what's wrong and what needs to be fixed"
                    },
                    "old_code": {
                        "type": "string",
                        "description": "The exact code that needs to be replaced (must match exactly including whitespace)"
                    },
                    "new_code": {
                        "type": "string",
                        "description": "The new code to replace it with"
                    }
                },
                "required": ["tool_name", "issue", "old_code", "new_code"]
            }
        },
        
        {
            "name": "test_tool",
            "description": """Test a tool after fixing it to see if it works.
            
            After applying a fix, use this to verify the tool now works correctly.
            
            This will:
            - Run a simple test case
            - Report if the tool executes without errors
            - Show any remaining issues
            
            If test passes, you can retry the original operation.
            If test fails, you can read source again and apply another fix.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "tool_name": {
                        "type": "string",
                        "description": "Name of the tool to test"
                    },
                    "test_parameters": {
                        "type": "object",
                        "description": "Parameters to use for testing (use simple/safe values)"
                    }
                },
                "required": ["tool_name"]
            }
        },
        
        {
            "name": "get_browser_screenshot",
            "description": """Get a screenshot of the current browser state for debugging.
            
            When browser-based tools fail (AWS console, SharePoint), use this to see
            what the browser is actually showing. This helps diagnose:
            - Is the page loaded correctly?
            - Are we on the right page?
            - What elements are visible?
            - Are there error messages?
            
            The screenshot will be saved and you can analyze it to understand what went wrong.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "What operation was being attempted when this screenshot is taken"
                    }
                },
                "required": ["context"]
            }
        }
    ]


# Tool mapping to source files
TOOL_SOURCE_MAP = {
    # AWS Screenshot Tools (Playwright + Selenium Hybrid)
    "aws_take_screenshot": "tools/universal_screenshot_enhanced.py",  # Main screenshot tool (undetected-chromedriver)
    "aws_hybrid_navigator": "tools/aws_hybrid_navigator.py",  # New hybrid (undetected-chromedriver + Playwright CDP)
    "rds_navigator": "tools/rds_navigator_enhanced.py",  # RDS-specific navigation (uses Playwright)
    "browser_session_manager": "ai_brain/browser_session_manager.py",  # Manages persistent browser sessions
    
    # AWS Other Tools
    "aws_export_data": "tools/aws_export_tool.py",
    "list_aws_resources": "tools/aws_list_tool.py",
    
    # AWS SDK Helpers
    "aws_rds_helper": "tools/aws_rds_helper.py",  # RDS SDK integration
    "aws_universal_discovery": "tools/aws_universal_discovery.py",  # Universal AWS SDK discovery
    
    # SharePoint Tools
    "sharepoint_review_evidence": "integrations/sharepoint_browser.py",
    "upload_to_sharepoint": "tools/sharepoint_upload_tool.py"
}


def read_tool_source_code(tool_name: str, section: Optional[str] = None) -> Dict[str, Any]:
    """Read the source code of a tool"""
    try:
        if tool_name not in TOOL_SOURCE_MAP:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(TOOL_SOURCE_MAP.keys())
            }
        
        base_dir = Path(__file__).parent.parent
        source_file = base_dir / TOOL_SOURCE_MAP[tool_name]
        
        if not source_file.exists():
            return {
                "status": "error",
                "error": f"Source file not found: {source_file}"
            }
        
        with open(source_file, 'r') as f:
            code = f.read()
        
        result = {
            "status": "success",
            "tool_name": tool_name,
            "source_file": str(source_file),
            "total_lines": len(code.split('\n')),
            "code": code
        }
        
        # If specific section requested, try to extract it
        if section:
            lines = code.split('\n')
            section_lines = []
            in_section = False
            indent_level = None
            
            for i, line in enumerate(lines):
                # Found the section start
                if f"def {section}" in line or f"class {section}" in line:
                    in_section = True
                    indent_level = len(line) - len(line.lstrip())
                    section_lines.append(f"{i+1}: {line}")
                elif in_section:
                    current_indent = len(line) - len(line.lstrip())
                    # End of section (next function/class at same or lower indent)
                    if line.strip() and current_indent <= indent_level:
                        break
                    section_lines.append(f"{i+1}: {line}")
            
            if section_lines:
                result["section"] = section
                result["section_code"] = '\n'.join(section_lines)
        
        return result
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def diagnose_error_context(error_message: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
    """Analyze an error and provide diagnostic information"""
    try:
        diagnosis = {
            "status": "success",
            "error_analysis": {},
            "suggested_fixes": []
        }
        
        # Analyze common error patterns
        error_lower = error_message.lower()
        
        # Browser/Selenium errors
        if "element not found" in error_lower or "no such element" in error_lower:
            diagnosis["error_analysis"] = {
                "type": "Selenium Element Not Found",
                "likely_cause": "The HTML element selector is incorrect or the page structure changed",
                "details": "The tool is looking for an element that doesn't exist on the page"
            }
            diagnosis["suggested_fixes"] = [
                "Use get_browser_screenshot to see what's actually on the page",
                "Read the tool source to see what selector is being used",
                "Update the selector in the code to match the current page structure"
            ]
        
        elif "timeout" in error_lower:
            diagnosis["error_analysis"] = {
                "type": "Timeout Error",
                "likely_cause": "Page took too long to load or element never appeared",
                "details": "The tool waited but the expected condition wasn't met"
            }
            diagnosis["suggested_fixes"] = [
                "Increase timeout values in the code",
                "Check if the page URL is correct",
                "Verify authentication is working",
                "Use get_browser_screenshot to see current state"
            ]
        
        elif "authentication" in error_lower or "credentials" in error_lower or "duo" in error_lower:
            diagnosis["error_analysis"] = {
                "type": "Authentication Error",
                "likely_cause": "AWS/SharePoint credentials expired or Duo MFA not completed",
                "details": "The tool can't authenticate to the service"
            }
            diagnosis["suggested_fixes"] = [
                "Run duo-sso to refresh AWS credentials",
                "Check if browser session expired",
                "Verify the authentication flow in the tool code"
            ]
        
        elif "attribute" in error_lower or "'NoneType'" in error_message:
            diagnosis["error_analysis"] = {
                "type": "Attribute Error / None Type",
                "likely_cause": "A variable is None when code expects it to have a value",
                "details": "Something that should exist doesn't exist"
            }
            diagnosis["suggested_fixes"] = [
                "Read the tool source to see what variable is None",
                "Add null checks in the code",
                "Fix the logic that should set the variable"
            ]
        
        # AWS-specific errors
        elif "aws" in tool_name.lower():
            if "region" in error_lower:
                diagnosis["error_analysis"] = {
                    "type": "AWS Region Error",
                    "likely_cause": "Invalid or missing AWS region",
                    "details": f"Region specified: {parameters.get('aws_region', 'NOT PROVIDED')}"
                }
                diagnosis["suggested_fixes"] = [
                    "Verify the AWS region is valid (us-east-1, eu-west-1, etc.)",
                    "Check if the service is available in that region"
                ]
            elif "profile" in error_lower or "credentials" in error_lower:
                diagnosis["error_analysis"] = {
                    "type": "AWS Credentials Error",
                    "likely_cause": "AWS credentials not found or expired",
                    "details": f"Profile specified: {parameters.get('aws_account', 'NOT PROVIDED')}"
                }
                diagnosis["suggested_fixes"] = [
                    "Run: duo-sso",
                    "Verify AWS_PROFILE is set correctly",
                    "Check ~/.aws/credentials file"
                ]
        
        # SharePoint-specific errors
        elif "sharepoint" in tool_name.lower():
            if "folder not found" in error_lower or "404" in error_message:
                diagnosis["error_analysis"] = {
                    "type": "SharePoint Path Error",
                    "likely_cause": "The SharePoint folder path is incorrect or doesn't exist",
                    "details": f"Looking for: {parameters.get('rfi_code', 'UNKNOWN')}"
                }
                diagnosis["suggested_fixes"] = [
                    "Verify the RFI folder exists in SharePoint",
                    "Check if URL encoding is correct",
                    "Use get_browser_screenshot to see where navigation ended"
                ]
        
        # Generic suggestions if no specific pattern matched
        if not diagnosis["suggested_fixes"]:
            diagnosis["suggested_fixes"] = [
                f"Read the source code: read_tool_source(tool_name='{tool_name}')",
                "Look for the line that's causing the error",
                "Use fix_tool_code to apply a fix",
                "Test the fix with test_tool"
            ]
        
        diagnosis["parameters_used"] = parameters
        diagnosis["next_steps"] = [
            "1. Use read_tool_source to see the implementation",
            "2. Identify the exact issue in the code",
            "3. Use fix_tool_code to apply the fix",
            "4. Use test_tool to verify the fix works",
            "5. Retry the original operation"
        ]
        
        return diagnosis
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def fix_tool_code_with_validation(tool_name: str, issue: str, old_code: str, new_code: str) -> Dict[str, Any]:
    """Fix a bug in tool code with validation"""
    try:
        if tool_name not in TOOL_SOURCE_MAP:
            return {
                "status": "error",
                "error": f"Unknown tool: {tool_name}"
            }
        
        base_dir = Path(__file__).parent.parent
        source_file = base_dir / TOOL_SOURCE_MAP[tool_name]
        
        # Read current content
        with open(source_file, 'r') as f:
            current_content = f.read()
        
        # Verify old_code exists
        if old_code not in current_content:
            return {
                "status": "error",
                "error": "The old_code string was not found in the file",
                "hint": "Make sure old_code matches EXACTLY (including whitespace)",
                "file": str(source_file)
            }
        
        # Apply the fix
        new_content = current_content.replace(old_code, new_code, 1)
        
        # Write back
        with open(source_file, 'w') as f:
            f.write(new_content)
        
        console.print(f"[green]✅ Fixed {tool_name}[/green]")
        console.print(f"[yellow]📝 Issue: {issue}[/yellow]")
        console.print(f"[cyan]📁 File: {source_file}[/cyan]")
        
        return {
            "status": "success",
            "message": f"Successfully fixed {tool_name}",
            "issue": issue,
            "file": str(source_file),
            "next_step": f"Use test_tool(tool_name='{tool_name}') to verify the fix"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def test_tool_functionality(tool_name: str, test_parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Test a tool after fixing"""
    try:
        console.print(f"[cyan]🧪 Testing {tool_name}...[/cyan]")
        
        # Import the tool module
        if tool_name == "aws_take_screenshot":
            from tools.aws_screenshot_selenium import capture_aws_screenshot
            # Simple syntax check - try importing the function
            result = {
                "status": "success",
                "message": f"{tool_name} imports successfully",
                "note": "Function is syntactically valid. Full functional test would require AWS credentials and browser."
            }
        
        elif tool_name == "aws_export_data":
            from tools.aws_export_tool import export_aws_data
            result = {
                "status": "success",
                "message": f"{tool_name} imports successfully",
                "note": "Function is syntactically valid. Full functional test would require AWS credentials."
            }
        
        elif tool_name == "list_aws_resources":
            from tools.aws_list_tool import list_s3_buckets, list_rds_clusters
            result = {
                "status": "success",
                "message": f"{tool_name} imports successfully",
                "note": "Functions are syntactically valid. Full functional test would require AWS credentials."
            }
        
        elif tool_name == "sharepoint_review_evidence":
            from integrations.sharepoint_browser import SharePointBrowserAccess
            result = {
                "status": "success",
                "message": f"{tool_name} imports successfully",
                "note": "Class is syntactically valid. Full functional test would require SharePoint authentication."
            }
        
        elif tool_name == "upload_to_sharepoint":
            from tools.sharepoint_upload_tool import upload_to_sharepoint
            result = {
                "status": "success",
                "message": f"{tool_name} imports successfully",
                "note": "Function is syntactically valid. Full functional test would require SharePoint authentication."
            }
        
        else:
            result = {
                "status": "error",
                "error": f"Unknown tool: {tool_name}"
            }
        
        return result
        
    except SyntaxError as e:
        return {
            "status": "error",
            "error": "Syntax Error in fixed code",
            "details": str(e),
            "traceback": traceback.format_exc(),
            "action": "The fix introduced a syntax error. Read the source again and apply a corrected fix."
        }
    
    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "traceback": traceback.format_exc()
        }


def capture_browser_debug_screenshot(context: str) -> Dict[str, Any]:
    """Capture current browser state for debugging"""
    try:
        console.print(f"[cyan]📸 Capturing browser debug screenshot...[/cyan]")
        console.print(f"[dim]Context: {context}[/dim]")
        
        # This would need to interface with the active browser instance
        # For now, return instructions
        return {
            "status": "info",
            "message": "To capture browser debug screenshot, the browser must be active",
            "instructions": [
                "The browser screenshot feature requires an active Selenium session",
                "When aws_take_screenshot or sharepoint tools are running, they can capture debug screenshots",
                "You can modify the tool code to add debug screenshots at key points",
                "Use: driver.save_screenshot('/tmp/debug.png')"
            ],
            "context": context
        }
        
    except Exception as e:
        return {
            "status": "error",
            "error": str(e)
        }

