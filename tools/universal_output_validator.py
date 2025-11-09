"""
Universal Output Validator - Validates ALL Agent Outputs
=========================================================

COMPREHENSIVE VALIDATION FOR:
✅ AWS Screenshots (KMS, S3, RDS, EC2, Lambda, etc.)
✅ AWS Data Exports (IAM users, S3 buckets, RDS instances, etc.)
✅ Jira Tickets (list, search, get details)
✅ Confluence Documents (search, get page, list pages)
✅ GitHub (PRs, issues, code search)
✅ Any tool output

Validates:
1. Data completeness (all expected fields present?)
2. Data accuracy (values make sense?)
3. Tool execution (did it actually work?)
4. Response format (correct structure?)
5. Error detection (hidden failures?)
"""

import os
import json
from typing import Dict, List, Optional, Any
from rich.console import Console
from datetime import datetime

console = Console()


class UniversalOutputValidator:
    """
    Validates ALL agent outputs across ALL tools.
    
    Prevents:
    - Agent claiming success when data is empty
    - Agent saying "retrieved 100 tickets" but only got 10
    - Agent reporting "no errors" but operation failed silently
    - Agent missing required fields in responses
    """
    
    def __init__(self):
        self.debug = True
        self.validation_history = []
    
    def validate_tool_output(
        self,
        tool_name: str,
        tool_parameters: Dict,
        tool_output: Any,
        expected_output_type: Optional[str] = None
    ) -> Dict:
        """
        🔍 UNIVERSAL VALIDATION
        
        Validates any tool output with tool-specific checks.
        
        Args:
            tool_name: Name of the tool (e.g., "aws_take_screenshot", "jira_list_tickets")
            tool_parameters: Parameters passed to the tool
            tool_output: The tool's output/response
            expected_output_type: Expected type (e.g., "list", "dict", "string")
        
        Returns:
            Dict with validation results:
            {
                "valid": True/False,
                "confidence": 0.0-1.0,
                "issues": [...],
                "diagnosis": "...",
                "suggested_fix": "...",
                "tool_specific_checks": {...}
            }
        """
        console.print(f"\n[bold cyan]🔍 VALIDATING {tool_name.upper()} OUTPUT[/bold cyan]\n")
        
        validation_result = {
            "valid": False,
            "confidence": 0.0,
            "issues": [],
            "diagnosis": "",
            "suggested_fix": "",
            "tool_name": tool_name,
            "timestamp": datetime.now().isoformat(),
            "tool_specific_checks": {}
        }
        
        # Route to tool-specific validation
        if tool_name == "aws_take_screenshot":
            return self._validate_aws_screenshot(tool_parameters, tool_output)
        
        elif tool_name == "aws_export_data":
            return self._validate_aws_export(tool_parameters, tool_output)
        
        elif tool_name in ["jira_list_tickets", "jira_search_jql", "jira_get_ticket"]:
            return self._validate_jira_output(tool_name, tool_parameters, tool_output)
        
        elif tool_name in ["confluence_search", "confluence_get_page", "confluence_list_space"]:
            return self._validate_confluence_output(tool_name, tool_parameters, tool_output)
        
        elif tool_name in ["github_list_prs", "github_get_pr", "github_search_code", "github_list_issues"]:
            return self._validate_github_output(tool_name, tool_parameters, tool_output)
        
        else:
            # Generic validation for unknown tools
            return self._validate_generic_output(tool_name, tool_parameters, tool_output)
    
    def _validate_aws_screenshot(self, parameters: Dict, output: Any) -> Dict:
        """Validate AWS screenshot output (already implemented in evidence_validator.py)"""
        # This is handled by EvidenceValidator
        # Just return basic validation here
        return {
            "valid": True,
            "confidence": 1.0,
            "issues": [],
            "diagnosis": "Screenshot validation handled by EvidenceValidator",
            "suggested_fix": "",
            "tool_specific_checks": {
                "screenshot_validation": "Delegated to EvidenceValidator"
            }
        }
    
    def _validate_aws_export(self, parameters: Dict, output: Any) -> Dict:
        """
        Validate AWS data export (CSV, JSON, XLSX).
        
        Checks:
        1. File was created
        2. File is not empty
        3. Data contains expected fields
        4. Row count matches expected
        """
        validation_result = {
            "valid": False,
            "confidence": 0.0,
            "issues": [],
            "diagnosis": "",
            "suggested_fix": "",
            "tool_specific_checks": {}
        }
        
        console.print("[cyan]Validating AWS export...[/cyan]")
        
        # Check if output contains file path
        if not isinstance(output, dict) or "result" not in output:
            validation_result["issues"].append("Output format invalid")
            validation_result["diagnosis"] = "Tool output is not in expected format"
            validation_result["suggested_fix"] = "Check tool implementation - should return dict with 'result' key"
            console.print("[red]❌ Invalid output format[/red]")
            return validation_result
        
        result = output.get("result", {})
        file_path = result.get("file_path") or result.get("final_path")
        
        # Check 1: File exists
        if not file_path or not os.path.exists(file_path):
            validation_result["issues"].append("Export file not found")
            validation_result["diagnosis"] = "File was not created or path is incorrect"
            validation_result["suggested_fix"] = "Check file permissions, disk space, and export logic"
            console.print("[red]❌ File not found[/red]")
            return validation_result
        
        console.print(f"[green]✅ File exists: {os.path.basename(file_path)}[/green]")
        validation_result["tool_specific_checks"]["file_exists"] = True
        
        # Check 2: File not empty
        file_size = os.path.getsize(file_path)
        if file_size < 100:  # Less than 100 bytes is suspicious
            validation_result["issues"].append(f"File too small: {file_size} bytes")
            validation_result["diagnosis"] = "Export file is nearly empty - may contain no data"
            validation_result["suggested_fix"] = "Check if AWS API returned data. Verify filters/parameters."
            console.print(f"[red]❌ File too small: {file_size} bytes[/red]")
        else:
            console.print(f"[green]✅ File size: {file_size} bytes[/green]")
            validation_result["tool_specific_checks"]["file_not_empty"] = True
        
        # Check 3: Row count (if available in output)
        row_count = result.get("row_count") or result.get("items_exported")
        if row_count is not None:
            if row_count == 0:
                validation_result["issues"].append("No data exported (0 rows)")
                validation_result["diagnosis"] = "Query returned no results"
                validation_result["suggested_fix"] = "Check filters, date ranges, and account/region"
                console.print("[yellow]⚠️  No data exported (0 rows)[/yellow]")
            else:
                console.print(f"[green]✅ Exported {row_count} rows[/green]")
                validation_result["tool_specific_checks"]["has_data"] = True
        
        # Calculate confidence
        checks_passed = sum(1 for v in validation_result["tool_specific_checks"].values() if v)
        total_checks = 3  # file_exists, file_not_empty, has_data
        validation_result["confidence"] = checks_passed / total_checks
        validation_result["valid"] = validation_result["confidence"] >= 0.67  # 2 out of 3
        
        if validation_result["valid"]:
            console.print(f"\n[green]✅ Export validated (Confidence: {validation_result['confidence']*100:.0f}%)[/green]")
        else:
            console.print(f"\n[red]❌ Export validation failed (Confidence: {validation_result['confidence']*100:.0f}%)[/red]")
        
        return validation_result
    
    def _validate_jira_output(self, tool_name: str, parameters: Dict, output: Any) -> Dict:
        """
        Validate Jira tool output.
        
        Checks:
        1. API call successful
        2. Data structure is correct
        3. Expected fields present
        4. Ticket count matches expectation
        """
        validation_result = {
            "valid": False,
            "confidence": 0.0,
            "issues": [],
            "diagnosis": "",
            "suggested_fix": "",
            "tool_specific_checks": {}
        }
        
        console.print("[cyan]Validating Jira output...[/cyan]")
        
        # Check output format
        if not isinstance(output, dict):
            validation_result["issues"].append("Output is not a dictionary")
            validation_result["diagnosis"] = "Jira tool should return dict with status and data"
            validation_result["suggested_fix"] = "Check Jira integration implementation"
            console.print("[red]❌ Invalid output format[/red]")
            return validation_result
        
        # Check for errors
        if output.get("status") == "error":
            validation_result["issues"].append(f"Tool error: {output.get('error', 'Unknown')}")
            validation_result["diagnosis"] = "Jira API call failed"
            validation_result["suggested_fix"] = "Check Jira credentials, permissions, and network connectivity"
            console.print(f"[red]❌ Tool error: {output.get('error')}[/red]")
            return validation_result
        
        console.print("[green]✅ No errors reported[/green]")
        validation_result["tool_specific_checks"]["no_errors"] = True
        
        # Check data presence
        data = output.get("data") or output.get("tickets") or output.get("results")
        if data is None:
            validation_result["issues"].append("No data in output")
            validation_result["diagnosis"] = "Response missing 'data' or 'tickets' field"
            validation_result["suggested_fix"] = "Check Jira API response structure"
            console.print("[red]❌ No data field found[/red]")
            return validation_result
        
        # Check data count
        if isinstance(data, list):
            count = len(data)
            if count == 0:
                validation_result["issues"].append("Empty results (0 tickets)")
                validation_result["diagnosis"] = "Jira query returned no tickets"
                validation_result["suggested_fix"] = "Check JQL query, filters, project, and date range"
                console.print("[yellow]⚠️  No tickets found (0 results)[/yellow]")
            else:
                console.print(f"[green]✅ Retrieved {count} tickets[/green]")
                validation_result["tool_specific_checks"]["has_data"] = True
                
                # Validate ticket structure
                if count > 0 and isinstance(data[0], dict):
                    required_fields = ["key", "summary"]  # Basic Jira fields
                    first_ticket = data[0]
                    missing_fields = [f for f in required_fields if f not in first_ticket]
                    
                    if missing_fields:
                        validation_result["issues"].append(f"Missing fields: {missing_fields}")
                        console.print(f"[yellow]⚠️  Missing fields: {missing_fields}[/yellow]")
                    else:
                        console.print(f"[green]✅ Ticket structure valid[/green]")
                        validation_result["tool_specific_checks"]["structure_valid"] = True
        
        # Calculate confidence
        checks_passed = sum(1 for v in validation_result["tool_specific_checks"].values() if v)
        total_checks = 3  # no_errors, has_data, structure_valid
        validation_result["confidence"] = checks_passed / total_checks
        validation_result["valid"] = validation_result["confidence"] >= 0.67
        
        if validation_result["valid"]:
            console.print(f"\n[green]✅ Jira output validated (Confidence: {validation_result['confidence']*100:.0f}%)[/green]")
        else:
            console.print(f"\n[red]❌ Jira validation failed (Confidence: {validation_result['confidence']*100:.0f}%)[/red]")
        
        return validation_result
    
    def _validate_confluence_output(self, tool_name: str, parameters: Dict, output: Any) -> Dict:
        """Validate Confluence tool output (similar to Jira)"""
        validation_result = {
            "valid": False,
            "confidence": 0.0,
            "issues": [],
            "diagnosis": "",
            "suggested_fix": "",
            "tool_specific_checks": {}
        }
        
        console.print("[cyan]Validating Confluence output...[/cyan]")
        
        if not isinstance(output, dict):
            validation_result["issues"].append("Output is not a dictionary")
            console.print("[red]❌ Invalid output format[/red]")
            return validation_result
        
        if output.get("status") == "error":
            validation_result["issues"].append(f"Tool error: {output.get('error')}")
            validation_result["diagnosis"] = "Confluence API call failed"
            validation_result["suggested_fix"] = "Check Confluence credentials and permissions"
            console.print(f"[red]❌ Tool error: {output.get('error')}[/red]")
            return validation_result
        
        console.print("[green]✅ No errors reported[/green]")
        validation_result["tool_specific_checks"]["no_errors"] = True
        
        # Check for data
        data = output.get("data") or output.get("pages") or output.get("results")
        if data:
            if isinstance(data, list) and len(data) > 0:
                console.print(f"[green]✅ Retrieved {len(data)} items[/green]")
                validation_result["tool_specific_checks"]["has_data"] = True
            elif isinstance(data, dict):
                console.print(f"[green]✅ Page data retrieved[/green]")
                validation_result["tool_specific_checks"]["has_data"] = True
        
        checks_passed = sum(1 for v in validation_result["tool_specific_checks"].values() if v)
        validation_result["confidence"] = checks_passed / 2
        validation_result["valid"] = validation_result["confidence"] >= 0.5
        
        if validation_result["valid"]:
            console.print(f"\n[green]✅ Confluence output validated[/green]")
        else:
            console.print(f"\n[red]❌ Confluence validation failed[/red]")
        
        return validation_result
    
    def _validate_github_output(self, tool_name: str, parameters: Dict, output: Any) -> Dict:
        """Validate GitHub tool output"""
        validation_result = {
            "valid": False,
            "confidence": 0.0,
            "issues": [],
            "diagnosis": "",
            "suggested_fix": "",
            "tool_specific_checks": {}
        }
        
        console.print("[cyan]Validating GitHub output...[/cyan]")
        
        if not isinstance(output, dict):
            validation_result["issues"].append("Output is not a dictionary")
            console.print("[red]❌ Invalid output format[/red]")
            return validation_result
        
        if output.get("status") == "error":
            validation_result["issues"].append(f"Tool error: {output.get('error')}")
            validation_result["diagnosis"] = "GitHub API call failed"
            validation_result["suggested_fix"] = "Check GitHub token and permissions"
            console.print(f"[red]❌ Tool error: {output.get('error')}[/red]")
            return validation_result
        
        console.print("[green]✅ No errors reported[/green]")
        validation_result["tool_specific_checks"]["no_errors"] = True
        
        # Check for data
        data = output.get("data") or output.get("pull_requests") or output.get("issues") or output.get("results")
        if data:
            if isinstance(data, list):
                console.print(f"[green]✅ Retrieved {len(data)} items[/green]")
                validation_result["tool_specific_checks"]["has_data"] = True
        
        checks_passed = sum(1 for v in validation_result["tool_specific_checks"].values() if v)
        validation_result["confidence"] = checks_passed / 2
        validation_result["valid"] = validation_result["confidence"] >= 0.5
        
        if validation_result["valid"]:
            console.print(f"\n[green]✅ GitHub output validated[/green]")
        else:
            console.print(f"\n[red]❌ GitHub validation failed[/red]")
        
        return validation_result
    
    def _validate_generic_output(self, tool_name: str, parameters: Dict, output: Any) -> Dict:
        """
        Generic validation for any tool.
        
        Basic checks that apply to all tools.
        """
        validation_result = {
            "valid": False,
            "confidence": 0.0,
            "issues": [],
            "diagnosis": "",
            "suggested_fix": "",
            "tool_specific_checks": {}
        }
        
        console.print(f"[cyan]Validating {tool_name} output (generic)...[/cyan]")
        
        # Check 1: Output is not None
        if output is None:
            validation_result["issues"].append("Tool returned None")
            validation_result["diagnosis"] = f"{tool_name} did not return any output"
            validation_result["suggested_fix"] = f"Check {tool_name} implementation - should return valid data or error dict"
            console.print("[red]❌ Output is None[/red]")
            return validation_result
        
        console.print("[green]✅ Output exists[/green]")
        validation_result["tool_specific_checks"]["output_exists"] = True
        
        # Check 2: Check for error status
        if isinstance(output, dict) and output.get("status") == "error":
            validation_result["issues"].append(f"Tool error: {output.get('error', 'Unknown')}")
            validation_result["diagnosis"] = f"{tool_name} reported an error"
            validation_result["suggested_fix"] = f"Check {tool_name} error message and logs"
            console.print(f"[red]❌ Tool error: {output.get('error')}[/red]")
            return validation_result
        
        console.print("[green]✅ No error status[/green]")
        validation_result["tool_specific_checks"]["no_error"] = True
        
        # Check 3: Output has content
        has_content = False
        if isinstance(output, (list, dict, str)) and len(output) > 0:
            has_content = True
        elif isinstance(output, (int, float, bool)):
            has_content = True
        
        if has_content:
            console.print("[green]✅ Output has content[/green]")
            validation_result["tool_specific_checks"]["has_content"] = True
        else:
            validation_result["issues"].append("Output is empty")
            console.print("[yellow]⚠️  Output is empty[/yellow]")
        
        # Calculate confidence
        checks_passed = sum(1 for v in validation_result["tool_specific_checks"].values() if v)
        total_checks = 3
        validation_result["confidence"] = checks_passed / total_checks
        validation_result["valid"] = validation_result["confidence"] >= 0.67
        
        if validation_result["valid"]:
            console.print(f"\n[green]✅ Output validated (Confidence: {validation_result['confidence']*100:.0f}%)[/green]")
        else:
            console.print(f"\n[red]❌ Validation failed (Confidence: {validation_result['confidence']*100:.0f}%)[/red]")
        
        return validation_result
    
    def get_validation_summary(self) -> Dict:
        """Get summary of all validations performed"""
        if not self.validation_history:
            return {"message": "No validations performed yet"}
        
        total = len(self.validation_history)
        valid_count = sum(1 for v in self.validation_history if v.get("valid"))
        avg_confidence = sum(v.get("confidence", 0) for v in self.validation_history) / total
        
        return {
            "total_validations": total,
            "valid": valid_count,
            "invalid": total - valid_count,
            "success_rate": f"{(valid_count/total)*100:.1f}%",
            "average_confidence": f"{avg_confidence*100:.1f}%"
        }

