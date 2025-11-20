"""
Error Debugger - LLM-Powered Error Analysis

Uses LLM to debug errors intelligently:
- Analyze root causes
- Suggest fixes
- Find similar past errors
- Learn from resolutions
"""

import json
import traceback
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()


class ErrorDebugger:
    """LLM-powered error debugging."""
    
    def __init__(self, llm=None):
        """
        Initialize error debugger.
        
        Args:
            llm: LLM instance for intelligent debugging
        """
        self.llm = llm
        self.enabled = llm is not None
    
    def analyze(self, error: Exception = None, context: Dict[str, Any] = None, **kwargs) -> Dict[str, Any]:
        """
        Analyze an error or execution result using LLM.
        
        Args:
            error: The exception (optional)
            context: Execution context (optional)
            **kwargs: Flexible arguments (tool_name, tool_input, result, etc.)
            
        Returns:
            Debug analysis with fixes
        """
        if not self.enabled:
            return {"analysis": "LLM not available", "suggestions": []}
        
        # Handle flexible call patterns
        if error is None and context is None:
            # Called with kwargs (e.g., tool_name, tool_input, result)
            tool_name = kwargs.get('tool_name', 'unknown')
            tool_input = kwargs.get('tool_input', {})
            result = kwargs.get('result', {})
            
            # Only analyze if there's an error in the result
            if isinstance(result, dict) and result.get('status') == 'error':
                error_msg = result.get('error', 'Unknown error')
                error = Exception(error_msg)
                context = {
                    "tool_name": tool_name,
                    "tool_input": tool_input,
                    "result": result
                }
            else:
                # No error to analyze
                return {"analysis": "No error detected", "suggestions": []}
        
        if error is None:
            return {"analysis": "No error provided", "suggestions": []}
        
        if context is None:
            context = kwargs or {}
        
        error_trace = ''.join(traceback.format_exception(type(error), error, error.__traceback__)) if error.__traceback__ else str(error)
        
        prompt = f"""Debug this error:

Error: {type(error).__name__}
Message: {str(error)}

Stack Trace:
{error_trace}

Context:
{json.dumps(context, indent=2, default=str)[:1000]}

Provide JSON:
{{
    "root_cause": "What caused this",
    "suggested_fixes": [
        {{"fix": "...", "code": "...", "confidence": 0.0-1.0}}
    ],
    "prevention": "How to avoid in future"
}}"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            json_text = self._extract_json(content)
            if json_text:
                return json.loads(json_text)
            
            return {"analysis": content}
            
        except Exception as e:
            console.print(f"[red]❌ Debug failed: {e}[/red]")
            return {"error": str(e)}
    
    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """Extract JSON from text."""
        if not text:
            return None
        
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        elif "```" in text:
            parts = text.split("```")
            if len(parts) >= 3:
                text = parts[1].strip()
        
        if not text.strip().startswith('{'):
            start = text.find('{')
            end = text.rfind('}')
            if start >= 0 and end > start:
                text = text[start:end+1]
        
        return text.strip() if text.strip() else None
