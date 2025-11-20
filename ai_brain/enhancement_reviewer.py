"""
Enhancement Reviewer - LLM Code Review

Before applying code changes, LLM reviews for:
- Code quality
- Security implications
- Performance impact
- Potential bugs
"""

import json
from typing import Dict, Any, Optional
from rich.console import Console

console = Console()


class EnhancementReviewer:
    """LLM-powered code review for enhancements."""
    
    def __init__(self, enhancement_manager=None, llm=None):
        """
        Initialize enhancement reviewer.
        
        Args:
            enhancement_manager: Enhancement manager instance
            llm: LLM instance for reviews
        """
        self.enhancement_manager = enhancement_manager
        self.llm = llm
        self.enabled = llm is not None
    
    def review_proposal(self, proposal_id: str) -> Optional[Dict[str, Any]]:
        """
        Review an enhancement proposal using LLM.
        
        Returns:
            Review results with approval recommendation
        """
        if not self.enabled or not self.enhancement_manager:
            return None
        
        proposal = self.enhancement_manager.get_proposal(proposal_id)
        if not proposal:
            return None
        
        prompt = f"""Review this code enhancement.

Summary: {proposal.get('summary', '')}
Reason: {proposal.get('reason', '')}

Changes:
{json.dumps(proposal.get('files', []), indent=2)[:2000]}

Analyze:
1. Code quality
2. Security risks
3. Side effects
4. Performance

Return JSON:
{{
    "recommendation": "approve" | "reject" | "modify",
    "risk_level": "low" | "medium" | "high",
    "concerns": ["..."],
    "suggestions": ["..."]
}}"""

        try:
            response = self.llm.invoke(prompt)
            content = response.content if hasattr(response, 'content') else str(response)
            
            json_text = self._extract_json(content)
            if json_text:
                return json.loads(json_text)
            
            return {"recommendation": "review_manually", "response": content}
            
        except Exception as e:
            console.print(f"[red]❌ Review failed: {e}[/red]")
            return None
    
    @staticmethod
    def _extract_json(text: str) -> Optional[str]:
        """Extract JSON."""
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
