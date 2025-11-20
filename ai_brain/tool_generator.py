"""
Dynamic Tool Generator

Generates new Python tools on-the-fly when the agent encounters
a capability gap. Uses LLM to write tool code, tests it, and
integrates it into the agent's toolset.
"""

import os
import json
import ast
from typing import Dict, List, Optional, Any
from pathlib import Path
from datetime import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()


class ToolGenerator:
    """
    Generates new tools dynamically using LLM reasoning.
    
    Workflow:
    1. Analyze what capability is needed
    2. Search for similar examples in codebase
    3. Generate Python code for the new tool
    4. Create tool definition schema
    5. Test the generated code
    6. Register with tool executor
    """
    
    def __init__(self, llm, repo_root: Optional[Path] = None):
        """
        Initialize tool generator.
        
        Args:
            llm: LLM instance for code generation
            repo_root: Repository root path
        """
        self.llm = llm
        self.repo_root = repo_root or Path(__file__).parent.parent
        self.generated_tools_dir = self.repo_root / "tools" / "generated"
        self.generated_tools_dir.mkdir(parents=True, exist_ok=True)
        
        console.print("[dim]🔧 Tool Generator initialized[/dim]")
    
    def generate_tool(
        self,
        capability_needed: str,
        context: Dict[str, Any],
        similar_tools: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Generate a new tool for a missing capability.
        
        Args:
            capability_needed: Description of what's needed (e.g., "export Datadog metrics")
            context: Context from the request (service, account, format, etc.)
            similar_tools: List of similar tool names to use as examples
            
        Returns:
            {
                "success": bool,
                "tool_name": str,
                "tool_file": str,
                "definition": dict,
                "code": str,
                "test_results": dict
            }
        """
        console.print(f"\n[bold magenta]🔧 GENERATING NEW TOOL[/bold magenta]")
        console.print(f"[cyan]Capability needed: {capability_needed}[/cyan]")
        
        # Step 1: Analyze and plan the tool
        tool_spec = self._analyze_tool_requirements(capability_needed, context)
        
        if not tool_spec.get("success"):
            return tool_spec
        
        # Step 2: Generate code
        code_result = self._generate_tool_code(tool_spec, similar_tools)
        
        if not code_result.get("success"):
            return code_result
        
        # Step 3: Create tool definition
        definition = self._create_tool_definition(tool_spec, code_result)
        
        # Step 4: Save to file
        tool_file = self._save_tool_file(
            tool_spec.get("tool_name"),
            code_result.get("code")
        )
        
        # Step 5: Basic validation
        validation = self._validate_generated_code(tool_file)
        
        return {
            "success": True,
            "tool_name": tool_spec.get("tool_name"),
            "tool_file": str(tool_file),
            "definition": definition,
            "code": code_result.get("code"),
            "validation": validation,
            "status": "generated_pending_approval"
        }
    
    def _analyze_tool_requirements(
        self,
        capability: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use LLM to analyze what the tool should do."""
        
        prompt = f"""Analyze this capability requirement and design a tool specification.

Capability Needed: {capability}

Context: {json.dumps(context, indent=2)}

Generate a JSON spec with:
{{
    "tool_name": "descriptive_snake_case_name",
    "description": "What this tool does",
    "service_type": "aws|jira|github|general",
    "inputs": {{
        "param_name": {{"type": "str|int|bool|list", "required": true|false, "description": "..."}},
        ...
    }},
    "outputs": {{
        "field_name": "description",
        ...
    }},
    "dependencies": ["boto3", "requests", etc.],
    "similar_to": "existing_tool_name if any"
}}"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0]
            elif "```" in content:
                content = content.split("```")[1].split("```")[0]
            
            spec = json.loads(content.strip())
            spec["success"] = True
            
            console.print(f"[green]✅ Tool spec created: {spec.get('tool_name')}[/green]")
            return spec
            
        except Exception as e:
            console.print(f"[red]❌ Spec generation failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def _generate_tool_code(
        self,
        tool_spec: Dict[str, Any],
        similar_tools: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Generate Python code for the tool."""
        
        tool_name = tool_spec.get("tool_name")
        description = tool_spec.get("description")
        inputs = tool_spec.get("inputs", {})
        dependencies = tool_spec.get("dependencies", [])
        
        # Load similar tool code as examples if provided
        examples = ""
        if similar_tools:
            for tool in similar_tools[:2]:  # Limit to 2 examples
                try:
                    tool_path = self.repo_root / "tools" / f"{tool}.py"
                    if tool_path.exists():
                        with open(tool_path) as f:
                            examples += f"\n\n# Example: {tool}\n{f.read()[:2000]}"  # First 2000 chars
                except:
                    pass
        
        prompt = f"""Generate production-ready Python code for this tool.

Tool Specification:
{json.dumps(tool_spec, indent=2)}

{examples}

Generate a complete Python module with:
1. Docstring explaining the tool
2. All necessary imports
3. Main function: def {tool_name}(...) -> Dict[str, Any]
4. Error handling with try/except
5. Rich console logging
6. Return dict with "success": bool and "result" or "error"

Write clean, well-commented code following the project's style."""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            # Extract Python code
            if "```python" in content:
                code = content.split("```python")[1].split("```")[0]
            elif "```" in content:
                code = content.split("```")[1].split("```")[0]
            else:
                code = content
            
            console.print(f"[green]✅ Generated {len(code)} chars of Python code[/green]")
            
            return {
                "success": True,
                "code": code.strip()
            }
            
        except Exception as e:
            console.print(f"[red]❌ Code generation failed: {e}[/red]")
            return {"success": False, "error": str(e)}
    
    def _create_tool_definition(
        self,
        tool_spec: Dict[str, Any],
        code_result: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create tool definition schema for tools_definition.py."""
        
        tool_name = tool_spec.get("tool_name")
        description = tool_spec.get("description")
        inputs = tool_spec.get("inputs", {})
        
        # Convert inputs to JSON schema format
        properties = {}
        required = []
        
        for param, spec in inputs.items():
            properties[param] = {
                "type": spec.get("type", "string"),
                "description": spec.get("description", "")
            }
            if spec.get("required"):
                required.append(param)
        
        definition = {
            "name": tool_name,
            "description": description,
            "input_schema": {
                "type": "object",
                "properties": properties,
                "required": required
            }
        }
        
        return definition
    
    def _save_tool_file(self, tool_name: str, code: str) -> Path:
        """Save generated tool to file."""
        
        filename = f"{tool_name}.py"
        filepath = self.generated_tools_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        console.print(f"[green]✅ Saved tool: {filepath}[/green]")
        return filepath
    
    def _validate_generated_code(self, tool_file: Path) -> Dict[str, Any]:
        """Basic validation of generated Python code."""
        
        try:
            with open(tool_file) as f:
                code = f.read()
            
            # Check if it's valid Python syntax
            ast.parse(code)
            
            # Check for required elements
            has_imports = "import" in code
            has_function = "def " in code
            has_return = "return" in code
            has_docstring = '"""' in code or "'''" in code
            
            checks = {
                "valid_syntax": True,
                "has_imports": has_imports,
                "has_function": has_function,
                "has_return": has_return,
                "has_docstring": has_docstring
            }
            
            all_pass = all(checks.values())
            
            if all_pass:
                console.print("[green]✅ Code validation passed[/green]")
            else:
                console.print("[yellow]⚠️  Code validation has warnings[/yellow]")
                for check, passed in checks.items():
                    if not passed:
                        console.print(f"[yellow]   - {check}: FAILED[/yellow]")
            
            return {
                "success": True,
                "checks": checks,
                "all_passed": all_pass
            }
            
        except SyntaxError as e:
            console.print(f"[red]❌ Syntax error in generated code: {e}[/red]")
            return {
                "success": False,
                "error": f"Syntax error: {e}",
                "checks": {"valid_syntax": False}
            }
        except Exception as e:
            console.print(f"[red]❌ Validation error: {e}[/red]")
            return {
                "success": False,
                "error": str(e)
            }

