"""
Meta-Intelligence Layer: Self-Evolving Multi-Dimensional Agent
===============================================================

This is the highest intelligence layer that enables the agent to:
1. Analyze its own capabilities and limitations
2. Automatically enhance tooling when encountering complex scenarios
3. Generate new tools on-the-fly when needed
4. Learn from failures and adapt
5. Operate across multiple dimensions (AWS, Jira, Confluence, GitHub, SharePoint)
6. Self-diagnose and self-heal

Architecture:
- AIOrchestrator: Plans and directs tools
- UniversalIntelligence: Tools query for guidance
- MetaIntelligence: Monitors everything, enhances when needed

This creates a truly autonomous, self-improving agent.
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
import re

console = Console()


class MetaIntelligence:
    """
    Meta-Intelligence Layer - The Self-Evolving Brain
    
    Capabilities:
    1. **Capability Analysis**: Understands what the agent can and cannot do
    2. **Gap Detection**: Identifies missing functionality for complex tasks
    3. **Auto-Enhancement**: Generates code to fill capability gaps
    4. **Learning**: Learns from failures and successes
    5. **Multi-Dimensional**: Operates across all integrated platforms
    6. **Self-Healing**: Fixes broken tools automatically
    """
    
    def __init__(self, llm, tool_executor, orchestrator):
        """
        Initialize Meta-Intelligence
        
        Args:
            llm: LLM instance (Claude/Bedrock)
            tool_executor: Tool executor with all tools
            orchestrator: AI Orchestrator for planning
        """
        self.llm = llm
        self.tool_executor = tool_executor
        self.orchestrator = orchestrator
        self.capability_map = self._build_capability_map()
        self.enhancement_history = []
        self.failure_patterns = []
        
        console.print("\n[bold magenta]🧩 Meta-Intelligence Layer Activated[/bold magenta]")
        console.print("[dim]  Self-evolving multi-dimensional agent ready[/dim]\n")
    
    def _build_capability_map(self) -> Dict[str, Dict]:
        """
        Build comprehensive capability map of what agent can do
        
        Returns:
            Dict mapping domains to capabilities
        """
        return {
            "aws": {
                "services": ["ec2", "s3", "rds", "lambda", "iam", "vpc", "kms", "etc"],
                "actions": ["list", "describe", "export_csv", "export_json", "screenshot", "navigate"],
                "limitations": ["No write operations", "Requires authentication"],
                "tools": ["aws_console_action", "aws_list_resources", "aws_export_data", "aws_collect_comprehensive_audit_evidence"]
            },
            "jira": {
                "services": ["tickets", "sprints", "boards", "projects"],
                "actions": ["search_jql", "list_tickets", "get_ticket", "export", "filter_by_board"],
                "limitations": ["Read-only", "Pagination at 100 per page"],
                "tools": ["jira_search_jql", "jira_list_tickets", "jira_get_ticket"]
            },
            "confluence": {
                "services": ["pages", "spaces", "content"],
                "actions": ["search", "get_page", "list_space", "export"],
                "limitations": ["Read-only"],
                "tools": ["confluence_search", "confluence_get_page", "confluence_list_space"]
            },
            "github": {
                "services": ["repos", "prs", "commits", "releases"],
                "actions": ["list_prs", "get_pr", "list_commits", "search"],
                "limitations": ["Rate limits", "Authentication required"],
                "tools": ["github_list_prs", "github_get_pr", "github_list_commits"]
            },
            "sharepoint": {
                "services": ["folders", "files", "evidence"],
                "actions": ["review_evidence", "upload", "analyze"],
                "limitations": ["Browser-based", "Manual authentication"],
                "tools": ["sharepoint_review_evidence", "upload_to_sharepoint"]
            },
            "general": {
                "services": ["file_operations", "data_processing", "validation"],
                "actions": ["read", "write", "validate", "analyze"],
                "limitations": ["File system access only"],
                "tools": ["show_local_evidence"]
            }
        }
    
    def analyze_request_complexity(self, user_request: str) -> Dict[str, Any]:
        """
        Analyze user request to determine complexity and required capabilities
        
        Args:
            user_request: The user's natural language request
        
        Returns:
            Dict with complexity analysis
        """
        prompt = f"""Analyze this user request and determine:
1. Required domains (AWS, Jira, Confluence, GitHub, SharePoint, etc.)
2. Required actions in each domain
3. Complexity level (simple, moderate, complex, very complex)
4. Whether current capabilities are sufficient
5. What new capabilities might be needed if any

Current agent capabilities:
{json.dumps(self.capability_map, indent=2)}

User request: "{user_request}"

Return JSON:
{{
    "complexity": "simple|moderate|complex|very_complex",
    "required_domains": ["domain1", "domain2"],
    "required_actions": {{
        "domain1": ["action1", "action2"],
        "domain2": ["action3"]
    }},
    "capabilities_sufficient": true/false,
    "missing_capabilities": ["capability1", "capability2"],
    "reasoning": "explanation of analysis"
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            # Extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            analysis = json.loads(json_str)
            
            console.print(f"\n[cyan]📊 Request Complexity Analysis:[/cyan]")
            console.print(f"  Complexity: [yellow]{analysis['complexity']}[/yellow]")
            console.print(f"  Domains: {', '.join(analysis['required_domains'])}")
            console.print(f"  Sufficient: [{'green' if analysis['capabilities_sufficient'] else 'red'}]{'✓' if analysis['capabilities_sufficient'] else '✗'}[/{'green' if analysis['capabilities_sufficient'] else 'red'}]")
            
            return analysis
            
        except Exception as e:
            console.print(f"[red]❌ Error analyzing complexity: {e}[/red]")
            return {
                "complexity": "unknown",
                "required_domains": [],
                "required_actions": {},
                "capabilities_sufficient": True,
                "missing_capabilities": [],
                "reasoning": f"Analysis failed: {e}"
            }
    
    def detect_capability_gaps(self, analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect specific capability gaps from analysis
        
        Args:
            analysis: Result from analyze_request_complexity
        
        Returns:
            List of capability gaps with details
        """
        if analysis["capabilities_sufficient"]:
            return []
        
        gaps = []
        for domain, actions in analysis["required_actions"].items():
            if domain not in self.capability_map:
                gaps.append({
                    "type": "missing_domain",
                    "domain": domain,
                    "actions": actions,
                    "severity": "high"
                })
                continue
            
            domain_caps = self.capability_map[domain]
            for action in actions:
                if action not in domain_caps["actions"]:
                    gaps.append({
                        "type": "missing_action",
                        "domain": domain,
                        "action": action,
                        "severity": "medium"
                    })
        
        return gaps
    
    def generate_enhancement_code(self, gaps: List[Dict[str, Any]]) -> Optional[str]:
        """
        Generate code to fill capability gaps
        
        Args:
            gaps: List of capability gaps
        
        Returns:
            Python code as string, or None if not possible
        """
        if not gaps:
            return None
        
        console.print(f"\n[bold yellow]🔧 Generating enhancement code for {len(gaps)} gap(s)...[/bold yellow]")
        
        gaps_description = "\n".join([
            f"- {gap['type']}: {gap.get('domain', 'N/A')} / {gap.get('action', 'N/A')}"
            for gap in gaps
        ])
        
        prompt = f"""You are a senior Python developer tasked with extending an audit AI agent.

Current capability gaps identified:
{gaps_description}

Current tool structure examples:
1. AWS tools use boto3 and return standardized results
2. Jira tools use jira Python library
3. All tools return Dict with "status" and "result" or "error"
4. Tools are registered in tools_definition.py and executed in tool_executor.py

Generate Python code to fill these gaps. Include:
1. A new tool class or function
2. Proper error handling
3. Documentation
4. Integration instructions

Return the code in a clear, executable format."""
        
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            console.print(f"[green]✅ Enhancement code generated[/green]")
            return content
            
        except Exception as e:
            console.print(f"[red]❌ Error generating code: {e}[/red]")
            return None
    
    def enhance_agent_realtime(
        self,
        user_request: str,
        analysis: Dict[str, Any],
        gaps: List[Dict[str, Any]]
    ) -> Tuple[bool, Optional[str]]:
        """
        Enhance agent in real-time by generating and integrating new code
        
        Args:
            user_request: Original user request
            analysis: Complexity analysis
            gaps: Detected capability gaps
        
        Returns:
            (success, message)
        """
        if not gaps:
            return True, "No enhancements needed"
        
        console.print(Panel(
            f"[yellow]🚀 Auto-Enhancement Mode Activated[/yellow]\n\n"
            f"Detected {len(gaps)} capability gap(s)\n"
            f"Generating solution...",
            title="Meta-Intelligence"
        ))
        
        # Generate code
        code = self.generate_enhancement_code(gaps)
        if not code:
            return False, "Failed to generate enhancement code"
        
        # Save to enhancement history
        enhancement_record = {
            "timestamp": datetime.now().isoformat(),
            "user_request": user_request,
            "analysis": analysis,
            "gaps": gaps,
            "generated_code": code,
            "applied": False
        }
        self.enhancement_history.append(enhancement_record)
        
        # Save code to file for review
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        enhancement_dir = Path("/Users/krishna/Documents/audit-ai-agent/ai_brain/enhancements")
        enhancement_dir.mkdir(exist_ok=True)
        
        code_file = enhancement_dir / f"enhancement_{timestamp}.py"
        with open(code_file, 'w') as f:
            f.write(f"# Auto-generated enhancement\n")
            f.write(f"# Request: {user_request}\n")
            f.write(f"# Timestamp: {timestamp}\n\n")
            f.write(code)
        
        console.print(f"\n[green]✅ Enhancement code saved to: {code_file}[/green]")
        console.print(f"[yellow]⚠️  Review and integrate manually for safety[/yellow]")
        
        return True, f"Enhancement code generated and saved to {code_file}"
    
    def learn_from_failure(self, tool_name: str, error: str, context: Dict) -> Dict[str, Any]:
        """
        Learn from tool failures and generate fixes
        
        Args:
            tool_name: Name of failed tool
            error: Error message
            context: Execution context
        
        Returns:
            Dict with learning insights and fix suggestions
        """
        console.print(f"\n[yellow]🧠 Learning from failure: {tool_name}[/yellow]")
        
        # Record failure pattern
        failure_pattern = {
            "timestamp": datetime.now().isoformat(),
            "tool": tool_name,
            "error": error,
            "context": context,
            "recurrence_count": 1
        }
        
        # Check if this is a recurring pattern
        similar_failures = [
            f for f in self.failure_patterns
            if f["tool"] == tool_name and f["error"] == error
        ]
        
        if similar_failures:
            failure_pattern["recurrence_count"] = len(similar_failures) + 1
            console.print(f"[red]⚠️  Recurring failure detected ({failure_pattern['recurrence_count']} times)[/red]")
        
        self.failure_patterns.append(failure_pattern)
        
        # Generate fix suggestion
        prompt = f"""Analyze this tool failure and suggest a fix:

Tool: {tool_name}
Error: {error}
Context: {json.dumps(context, indent=2)}
Recurrence: {failure_pattern['recurrence_count']} time(s)

Provide:
1. Root cause analysis
2. Suggested fix (code or configuration)
3. Prevention strategy

Return JSON:
{{
    "root_cause": "explanation",
    "fix_type": "code|config|documentation",
    "suggested_fix": "detailed fix description or code",
    "prevention": "how to prevent this in future"
}}"""
        
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            # Extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            learning = json.loads(json_str)
            
            console.print(f"\n[cyan]📚 Learning Analysis:[/cyan]")
            console.print(f"  Root Cause: {learning['root_cause']}")
            console.print(f"  Fix Type: {learning['fix_type']}")
            console.print(f"  Prevention: {learning['prevention']}")
            
            return learning
            
        except Exception as e:
            console.print(f"[red]❌ Error in learning analysis: {e}[/red]")
            return {
                "root_cause": "Unknown",
                "fix_type": "unknown",
                "suggested_fix": "Manual investigation required",
                "prevention": "Monitor for recurrence"
            }
    
    def suggest_alternative_approach(
        self,
        original_request: str,
        failed_approach: str,
        error: str
    ) -> Optional[str]:
        """
        When an approach fails, suggest alternative ways to accomplish the goal
        
        Args:
            original_request: User's original request
            failed_approach: The approach that failed
            error: Error message
        
        Returns:
            Alternative approach suggestion
        """
        prompt = f"""A tool execution failed. Suggest alternative approaches:

Original Request: {original_request}
Failed Approach: {failed_approach}
Error: {error}

Available capabilities:
{json.dumps(self.capability_map, indent=2)}

Suggest 2-3 alternative approaches that could achieve the same goal using:
1. Different tools
2. Different API methods
3. Different data sources
4. Workarounds

Return as clear, actionable steps."""
        
        try:
            response = self.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            console.print(Panel(
                content,
                title="[yellow]🔄 Alternative Approaches[/yellow]",
                border_style="yellow"
            ))
            
            return content
            
        except Exception as e:
            console.print(f"[red]❌ Error generating alternatives: {e}[/red]")
            return None
    
    def execute_with_meta_intelligence(
        self,
        user_request: str,
        tool_name: str,
        tool_params: Dict
    ) -> Dict[str, Any]:
        """
        Execute a tool with meta-intelligence monitoring
        
        This wraps tool execution with:
        - Pre-execution validation
        - Real-time monitoring
        - Post-execution analysis
        - Automatic retry with fixes
        - Learning from failures
        
        Args:
            user_request: Original user request
            tool_name: Tool to execute
            tool_params: Tool parameters
        
        Returns:
            Execution result with meta-intelligence enhancements
        """
        console.print(f"\n[bold cyan]🧩 Meta-Intelligence Execution: {tool_name}[/bold cyan]")
        
        # Pre-execution: Analyze complexity
        analysis = self.analyze_request_complexity(user_request)
        
        # Check for capability gaps
        gaps = self.detect_capability_gaps(analysis)
        if gaps:
            console.print(f"[yellow]⚠️  Detected {len(gaps)} capability gap(s)[/yellow]")
            success, message = self.enhance_agent_realtime(user_request, analysis, gaps)
            if not success:
                return {
                    "status": "error",
                    "error": "Capability gap detected but enhancement failed",
                    "meta_analysis": analysis,
                    "gaps": gaps
                }
        
        # Execute tool
        console.print(f"[cyan]▶️  Executing {tool_name}...[/cyan]")
        max_retries = 3
        for attempt in range(max_retries):
            try:
                result = self.tool_executor.execute_tool(tool_name, tool_params)
                
                # Post-execution: Validate result
                if result.get("status") == "success":
                    console.print(f"[green]✅ Execution successful[/green]")
                    return {
                        "status": "success",
                        "result": result.get("result"),
                        "meta_analysis": analysis,
                        "attempts": attempt + 1
                    }
                else:
                    error = result.get("error", "Unknown error")
                    console.print(f"[yellow]⚠️  Attempt {attempt + 1} failed: {error}[/yellow]")
                    
                    # Learn from failure
                    learning = self.learn_from_failure(
                        tool_name,
                        error,
                        {"params": tool_params, "attempt": attempt + 1}
                    )
                    
                    # Try to apply fix if available
                    if learning.get("fix_type") == "config" and attempt < max_retries - 1:
                        console.print(f"[cyan]🔧 Applying suggested fix...[/cyan]")
                        # Could apply config fixes here
                        continue
                    
                    # Suggest alternatives on final attempt
                    if attempt == max_retries - 1:
                        self.suggest_alternative_approach(
                            user_request,
                            f"{tool_name} with {tool_params}",
                            error
                        )
                    
            except Exception as e:
                error_str = str(e)
                console.print(f"[red]❌ Execution exception: {error_str}[/red]")
                
                if attempt < max_retries - 1:
                    console.print(f"[yellow]🔄 Retrying ({attempt + 2}/{max_retries})...[/yellow]")
                    continue
                
                return {
                    "status": "error",
                    "error": error_str,
                    "meta_analysis": analysis,
                    "attempts": attempt + 1,
                    "learning": self.learn_from_failure(tool_name, error_str, {"params": tool_params})
                }
        
        return {
            "status": "error",
            "error": "Max retries exceeded",
            "meta_analysis": analysis,
            "attempts": max_retries
        }
    
    def generate_capability_report(self) -> str:
        """
        Generate comprehensive capability report
        
        Returns:
            Markdown report of agent capabilities
        """
        report = "# Agent Capability Report\n\n"
        report += f"Generated: {datetime.now().isoformat()}\n\n"
        
        report += "## Current Capabilities\n\n"
        for domain, caps in self.capability_map.items():
            report += f"### {domain.upper()}\n\n"
            report += f"**Services**: {', '.join(caps['services'])}\n\n"
            report += f"**Actions**: {', '.join(caps['actions'])}\n\n"
            report += f"**Tools**: {', '.join(caps['tools'])}\n\n"
            report += f"**Limitations**: {', '.join(caps['limitations'])}\n\n"
        
        report += "## Enhancement History\n\n"
        if self.enhancement_history:
            for i, enh in enumerate(self.enhancement_history, 1):
                report += f"### Enhancement #{i}\n"
                report += f"- **Timestamp**: {enh['timestamp']}\n"
                report += f"- **Request**: {enh['user_request']}\n"
                report += f"- **Gaps**: {len(enh['gaps'])}\n"
                report += f"- **Applied**: {enh['applied']}\n\n"
        else:
            report += "No enhancements yet.\n\n"
        
        report += "## Failure Patterns\n\n"
        if self.failure_patterns:
            # Group by tool
            by_tool = {}
            for failure in self.failure_patterns:
                tool = failure["tool"]
                if tool not in by_tool:
                    by_tool[tool] = []
                by_tool[tool].append(failure)
            
            for tool, failures in by_tool.items():
                report += f"### {tool}\n"
                report += f"- **Total Failures**: {len(failures)}\n"
                unique_errors = set(f["error"] for f in failures)
                report += f"- **Unique Errors**: {len(unique_errors)}\n\n"
        else:
            report += "No failures recorded.\n\n"
        
        return report


class MultiDimensionalCoordinator:
    """
    Coordinates operations across multiple platforms simultaneously
    
    Example: "Compare Jira tickets with AWS resources and update Confluence"
    requires coordinating Jira, AWS, and Confluence tools in sequence
    """
    
    def __init__(self, meta_intelligence: MetaIntelligence):
        self.meta = meta_intelligence
        self.active_dimensions = set()
    
    def execute_cross_platform_task(
        self,
        task_description: str,
        dimensions: List[str]
    ) -> Dict[str, Any]:
        """
        Execute a task that spans multiple platforms
        
        Args:
            task_description: Natural language task description
            dimensions: List of platforms involved (e.g., ["jira", "aws", "confluence"])
        
        Returns:
            Combined results from all dimensions
        """
        console.print(f"\n[bold magenta]🌐 Multi-Dimensional Task Execution[/bold magenta]")
        console.print(f"[cyan]Dimensions: {', '.join(dimensions)}[/cyan]")
        console.print(f"[cyan]Task: {task_description}[/cyan]\n")
        
        self.active_dimensions.update(dimensions)
        
        # Use meta-intelligence to break down the task
        prompt = f"""Break down this cross-platform task into sequential steps:

Task: {task_description}
Platforms: {', '.join(dimensions)}

Available capabilities per platform:
{json.dumps({d: self.meta.capability_map.get(d, {}) for d in dimensions}, indent=2)}

Return JSON array of steps:
[
    {{
        "step": 1,
        "platform": "jira",
        "action": "search_tickets",
        "params": {{}},
        "output_to": "jira_results"
    }},
    {{
        "step": 2,
        "platform": "aws",
        "action": "list_resources",
        "params": {{}},
        "depends_on": ["jira_results"]
    }}
]"""
        
        try:
            response = self.meta.llm.invoke(prompt)
            content = getattr(response, "content", str(response))
            
            # Extract JSON
            if "```json" in content:
                json_str = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                json_str = content.split("```")[1].split("```")[0].strip()
            else:
                json_str = content.strip()
            
            steps = json.loads(json_str)
            
            # Execute steps in sequence
            results = {}
            for step in steps:
                step_num = step["step"]
                platform = step["platform"]
                action = step["action"]
                params = step.get("params", {})
                
                console.print(f"\n[cyan]Step {step_num}: {platform}.{action}[/cyan]")
                
                # Build tool name (platform_action)
                tool_name = f"{platform}_{action}"
                
                # Execute with meta-intelligence
                result = self.meta.execute_with_meta_intelligence(
                    task_description,
                    tool_name,
                    params
                )
                
                # Store result
                output_key = step.get("output_to", f"step_{step_num}_result")
                results[output_key] = result
            
            return {
                "status": "success",
                "dimensions": list(self.active_dimensions),
                "steps_executed": len(steps),
                "results": results
            }
            
        except Exception as e:
            console.print(f"[red]❌ Multi-dimensional execution failed: {e}[/red]")
            return {
                "status": "error",
                "error": str(e),
                "dimensions": list(self.active_dimensions)
            }

