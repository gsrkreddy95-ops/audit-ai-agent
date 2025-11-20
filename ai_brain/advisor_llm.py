"""
Advisor LLM - Secondary Brain for Code Review & Planning

A second LLM (GPT/Gemini) that reviews Claude's work and provides:
- Alternative perspectives on solutions
- Code review for safety
- Optimization suggestions
- Quality validation
"""

import os
import json
import requests
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()


class AdvisorLLM:
    """
    Secondary LLM for advisory/review functions.
    
    Works alongside Claude (primary LLM) to provide:
    - Independent code review
    - Alternative solution suggestions  
    - Quality checks
    - Optimization recommendations
    """
    
    def __init__(
        self,
        api_key: str,
        provider: str = "openai",
        model: str = "gpt-4",
        api_base: Optional[str] = None
    ):
        """
        Initialize Advisor LLM.
        
        Args:
            api_key: API key for the advisor LLM
            provider: Provider (openai, google, anthropic)
            model: Model name (gpt-4, gpt-5, gemini-pro)
            api_base: Optional custom API base URL
        """
        self.api_key = api_key
        self.provider = provider.lower()
        self.model = model
        self.api_base = api_base or self._get_default_base_url()
        self.enabled = bool(api_key)
        
        if self.enabled:
            console.print(f"[dim]🧠 Advisor LLM enabled ({self.provider} / {self.model})[/dim]")
    
    def _get_default_base_url(self) -> str:
        """Get default API base URL for provider."""
        urls = {
            "openai": "https://api.openai.com/v1",
            "google": "https://generativelanguage.googleapis.com/v1beta",
            "anthropic": "https://api.anthropic.com/v1"
        }
        return urls.get(self.provider, "https://api.openai.com/v1")
    
    def review_plan(self, plan: Dict[str, Any], user_request: str) -> Optional[Dict[str, Any]]:
        """
        Review an execution plan before it runs.
        
        Returns:
            {"approval": "approve"|"reject"|"modify", "concerns": [...], "suggestions": [...]}
        """
        if not self.enabled:
            return None
        
        prompt = f"""Review this execution plan for potential issues.

User Request: {user_request}
Plan: {json.dumps(plan, indent=2, default=str)[:2000]}

Review for:
1. Missing steps
2. Security concerns
3. Efficiency issues
4. Better alternatives

Return JSON:
{{
    "approval": "approve" | "modify" | "reject",
    "concerns": ["..."],
    "suggestions": ["..."],
    "confidence": 0.0-1.0
}}"""

        return self._call_api(prompt)
    
    def review_output(self, tool_name: str, output: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Review tool execution output for quality/completeness.
        """
        if not self.enabled:
            return None
        
        prompt = f"""Review this tool execution.

Tool: {tool_name}
Output: {json.dumps(output, indent=2, default=str)[:1500]}

Check:
1. Correctness
2. Completeness
3. Potential issues
4. Optimization opportunities

Return JSON:
{{
    "quality": "good" | "acceptable" | "poor",
    "issues": ["..."],
    "suggestions": ["..."]
}}"""

        return self._call_api(prompt)
    
    def _call_api(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call the advisor LLM API."""
        if self.provider == "openai":
            return self._call_openai(prompt)
        return None
    
    def _call_openai(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call OpenAI API."""
        url = f"{self.api_base}/chat/completions"
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3,
            "max_tokens": 2000
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            
            if response.status_code == 429:
                console.print(f"[yellow]⚠️  Advisor API 429: {response.text[:200]}[/yellow]")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            content = data['choices'][0]['message']['content']
            
            # Try to parse as JSON
            json_text = self._extract_json(content)
            if json_text:
                return json.loads(json_text)
            
            return {"response": content}
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Advisor error: {e}[/yellow]")
            return None
    
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
