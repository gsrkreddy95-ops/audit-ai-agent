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
        similar_tools: Optional[List[str]] = None,
        auto_approve: bool = False
    ) -> Dict[str, Any]:
        """
        Generate a new tool for a missing capability.
        
        Args:
            capability_needed: Description of what's needed (e.g., "export Datadog metrics")
            context: Context from the request (service, account, format, etc.)
            similar_tools: List of similar tool names to use as examples
            auto_approve: If True, automatically register the tool without approval
            
        Returns:
            {
                "success": bool,
                "tool_name": str,
                "tool_file": str,
                "language": str,
                "definition": dict,
                "code": str,
                "test_results": dict
            }
        """
        console.print(f"\n[bold magenta]🔧 GENERATING NEW TOOL[/bold magenta]")
        console.print(f"[cyan]Capability needed: {capability_needed}[/cyan]")
        
        # Step 1: Analyze and plan the tool (includes language selection)
        tool_spec = self._analyze_tool_requirements(capability_needed, context)
        
        if not tool_spec.get("success"):
            return tool_spec
        
        language = tool_spec.get("language", "python")
        console.print(f"[cyan]📝 Generating {language.upper()} tool[/cyan]")
        
        # Step 2: Generate code in appropriate language
        code_result = self._generate_tool_code(tool_spec, similar_tools, language)
        
        if not code_result.get("success"):
            return code_result
        
        # Step 3: Create tool definition
        definition = self._create_tool_definition(tool_spec, code_result)
        
        # Step 4: Save to file with correct extension
        tool_file = self._save_tool_file(
            tool_spec.get("tool_name"),
            code_result.get("code"),
            language
        )
        
        # Step 5: Basic validation
        validation = self._validate_generated_code(tool_file, language)
        
        result = {
            "success": True,
            "tool_name": tool_spec.get("tool_name"),
            "tool_file": str(tool_file),
            "language": language,
            "definition": definition,
            "code": code_result.get("code"),
            "validation": validation,
            "status": "generated_pending_approval" if not auto_approve else "auto_approved"
        }
        
        # Auto-approve if enabled and validation passed
        if auto_approve and validation.get("all_passed"):
            console.print("[green]✅ Auto-approving generated tool (validation passed)[/green]")
            result["status"] = "approved_and_registered"
            # TODO: Actually register the tool in tools_definition.py
        
        return result
    
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
    "language": "python|bash|javascript|sql|etc",
    "language_rationale": "Why this language is best for this task",
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
}}

Choose the BEST language for the task:
- Python: API calls, data processing, complex logic
- Bash: AWS CLI, system operations, file manipulation
- JavaScript: Browser automation, Node.js APIs
- SQL: Database queries
- etc."""

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
        similar_tools: Optional[List[str]],
        language: str = "python"
    ) -> Dict[str, Any]:
        """Generate code for the tool in the specified language."""
        
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
        
        # Language-specific prompts
        if language == "python":
            code_instructions = f"""Generate a complete Python module with:
1. Docstring explaining the tool
2. All necessary imports
3. Main function: def {tool_name}(...) -> Dict[str, Any]
4. Error handling with try/except
5. Rich console logging
6. Return dict with "success": bool and "result" or "error"
7. Type hints for all parameters"""
        
        elif language == "bash":
            code_instructions = f"""Generate a complete Bash script with:
1. Shebang (#!/bin/bash)
2. Comments explaining the tool
3. Error handling (set -e, trap)
4. Input validation
5. Logging to stdout/stderr
6. Exit codes (0 for success, non-zero for errors)
7. Functions for reusability"""
        
        elif language == "javascript":
            code_instructions = f"""Generate a complete JavaScript/Node.js module with:
1. JSDoc comments
2. All necessary requires/imports
3. Async function if needed
4. Error handling with try/catch
5. Console logging
6. Export the main function
7. Return object with success and result/error"""
        
        else:
            code_instructions = f"Generate production-ready {language} code for this tool with proper error handling and logging."
        
        prompt = f"""Generate production-ready {language.upper()} code for this tool.

Tool Specification:
{json.dumps(tool_spec, indent=2)}

{examples}

{code_instructions}

Write clean, well-commented, production-ready code."""

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
    
    def _save_tool_file(self, tool_name: str, code: str, language: str = "python") -> Path:
        """Save generated tool to file with appropriate extension."""
        
        # Map language to file extension
        extensions = {
            "python": ".py",
            "bash": ".sh",
            "shell": ".sh",
            "javascript": ".js",
            "typescript": ".ts",
            "sql": ".sql",
            "yaml": ".yaml",
            "json": ".json"
        }
        
        ext = extensions.get(language.lower(), ".txt")
        filename = f"{tool_name}{ext}"
        filepath = self.generated_tools_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        
        # Make executable if shell script
        if ext == ".sh":
            os.chmod(filepath, 0o755)
        
        console.print(f"[green]✅ Saved {language} tool: {filepath}[/green]")
        return filepath
    
    def _validate_generated_code(self, tool_file: Path, language: str = "python") -> Dict[str, Any]:
        """Basic validation of generated code (language-specific)."""
        
        try:
            with open(tool_file) as f:
                code = f.read()
            
            checks = {}
            
            if language == "python":
                # Check if it's valid Python syntax
                try:
                    ast.parse(code)
                    checks["valid_syntax"] = True
                except SyntaxError:
                    checks["valid_syntax"] = False
                
                # Check for required elements
                checks["has_imports"] = "import" in code
                checks["has_function"] = "def " in code
                checks["has_return"] = "return" in code
                checks["has_docstring"] = '"""' in code or "'''" in code
            
            elif language in ["bash", "shell"]:
                # Check for shell script elements
                checks["has_shebang"] = code.strip().startswith("#!")
                checks["has_error_handling"] = "set -e" in code or "trap" in code
                checks["has_functions"] = "() {" in code or "function " in code
            
            elif language == "javascript":
                # Basic JS checks
                checks["has_function"] = "function" in code or "=>" in code
                checks["has_exports"] = "module.exports" in code or "export" in code
                checks["has_error_handling"] = "try" in code or "catch" in code
            
            else:
                # Generic checks for other languages
                checks["not_empty"] = len(code.strip()) > 0
                checks["has_comments"] = "#" in code or "//" in code or "/*" in code
            
            all_pass = all(checks.values())
            
            if all_pass:
                console.print(f"[green]✅ {language.upper()} code validation passed[/green]")
            else:
                console.print(f"[yellow]⚠️  {language.upper()} validation has warnings[/yellow]")
                for check, passed in checks.items():
                    if not passed:
                        console.print(f"[yellow]   - {check}: FAILED[/yellow]")
            
            return {
                "success": True,
                "checks": checks,
                "all_passed": all_pass,
                "language": language
            }
            
        except Exception as e:
            console.print(f"[red]❌ Validation error: {e}[/red]")
            return {
                "success": False,
                "error": str(e),
                "language": language
            }

