"""
Universal Intelligence Layer
Provides LLM-powered decision making for ALL tools in the audit agent
Every tool can ask the brain "what should I do?" when facing uncertainty
"""

import json
import re
import base64
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from rich.console import Console
import traceback

console = Console()


class UniversalIntelligence:
    """
    Central intelligence hub that all tools can query for decisions
    
    Tools can ask:
    - "What format is this file?" → Detect CSV, PDF, JSON, etc.
    - "How should I parse this?" → Get parsing strategy
    - "This failed, what should I try?" → Error recovery
    - "What columns/data should I extract?" → Smart extraction
    - "Is this evidence relevant?" → Validation
    """
    
    def __init__(self, llm):
        """
        Initialize universal intelligence
        
        Args:
            llm: LangChain LLM instance (ChatBedrock, etc.)
        """
        self.llm = llm
        self.decision_history = []  # Track decisions for learning
        self.tool_contexts = {}  # Remember context per tool
        
    def ask(self, 
            question: str, 
            context: Optional[Dict[str, Any]] = None,
            tool_name: Optional[str] = None,
            visual_input: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Universal "ask the brain" method
        Any tool can call this when it needs intelligence
        
        Args:
            question: What the tool wants to know
            context: Additional context (file paths, error messages, etc.)
            tool_name: Name of the calling tool
            visual_input: Screenshot or image bytes for visual analysis
        
        Returns:
            {
                "answer": "Direct answer to the question",
                "actions": ["step1", "step2"],
                "reasoning": "Why this is the right approach",
                "confidence": 85,
                "fallback": "What to do if this doesn't work"
            }
        """
        try:
            console.print(f"[cyan]🧠 {tool_name or 'Tool'} asking brain: {question[:100]}...[/cyan]")
            
            # Build comprehensive prompt
            prompt = f"""You are the intelligent brain of an audit automation agent. A tool needs your help making a decision.

**TOOL:** {tool_name or 'Unknown'}

**QUESTION:**
{question}

**CONTEXT:**
{json.dumps(context or {}, indent=2)}

**YOUR TASK:**
Provide intelligent guidance to help the tool succeed. Be specific and actionable.

Respond in JSON:
{{
  "answer": "Direct answer to the question",
  "actions": ["specific step 1", "specific step 2"],
  "reasoning": "Why this approach is correct",
  "confidence": 85,
  "fallback": "Alternative if primary approach fails",
  "additional_context": {{"key": "any extra info that might help"}}
}}"""

            # If visual input provided, use vision model
            if visual_input:
                from langchain_core.messages import HumanMessage
                screenshot_b64 = base64.b64encode(visual_input).decode('utf-8')
                message = HumanMessage(
                    content=[
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{screenshot_b64}"}
                        }
                    ]
                )
                response = self.llm.invoke([message])
            else:
                response = self.llm.invoke(prompt)
            
            # Parse response
            response_text = response.content if hasattr(response, 'content') else str(response)
            decision = self._parse_json_response(response_text)
            
            # Remember this decision
            self._remember_decision(tool_name, question, decision, context)
            
            console.print(f"[green]✓ Brain decision: {decision.get('answer', 'See actions')[:100]}...[/green]")
            console.print(f"[dim]  Confidence: {decision.get('confidence', 0)}%[/dim]")
            
            return decision
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Brain query failed: {e}[/yellow]")
            return {
                "answer": "Unable to get intelligent response",
                "actions": ["proceed_with_caution"],
                "reasoning": f"Error: {e}",
                "confidence": 0,
                "fallback": "Use hardcoded fallback logic"
            }
    
    def detect_file_format(self, file_path: str, sample_bytes: Optional[bytes] = None) -> Dict[str, Any]:
        """
        Intelligently detect file format and structure
        
        Args:
            file_path: Path to file
            sample_bytes: Optional first N bytes for analysis
        
        Returns:
            {
                "format": "csv|json|pdf|xlsx|txt|unknown",
                "structure": {
                    "has_header": true,
                    "delimiter": ",",
                    "columns": ["col1", "col2"],
                    "encoding": "utf-8"
                },
                "parsing_strategy": "Use pandas with header=0, sep=','",
                "confidence": 90
            }
        """
        context = {
            "file_path": file_path,
            "file_extension": Path(file_path).suffix,
            "file_size": Path(file_path).stat().st_size if Path(file_path).exists() else None
        }
        
        if sample_bytes:
            context["sample_content"] = sample_bytes.decode('utf-8', errors='ignore')[:500]
        elif Path(file_path).exists():
            with open(file_path, 'rb') as f:
                sample = f.read(1000)
                context["sample_content"] = sample.decode('utf-8', errors='ignore')
        
        return self.ask(
            question=f"What is the format and structure of this file? How should I parse it?",
            context=context,
            tool_name="file_detector"
        )
    
    def suggest_extraction_strategy(self, 
                                   file_info: Dict[str, Any],
                                   purpose: str) -> Dict[str, Any]:
        """
        Suggest how to extract data from a file
        
        Args:
            file_info: Information about the file (from detect_file_format)
            purpose: What data is needed (e.g., "Extract audit trail timestamps")
        
        Returns:
            {
                "method": "pandas.read_csv|PyPDF2|openpyxl|json.load",
                "parameters": {"sep": ",", "header": 0},
                "columns_to_extract": ["timestamp", "user", "action"],
                "filtering_logic": "rows where action != 'VIEW'",
                "confidence": 85
            }
        """
        return self.ask(
            question=f"How should I extract data for: {purpose}",
            context={
                "file_info": file_info,
                "purpose": purpose
            },
            tool_name="extraction_planner"
        )
    
    def handle_tool_error(self, 
                         tool_name: str,
                         error: Exception,
                         attempted_action: str,
                         context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Intelligent error recovery for any tool
        
        Args:
            tool_name: Name of the tool that failed
            error: Exception that was raised
            attempted_action: What the tool was trying to do
            context: Additional context
        
        Returns:
            {
                "recovery_action": "retry|skip|fallback|abort",
                "retry_with_changes": {"param": "new_value"},
                "alternative_approach": "Try this instead...",
                "reasoning": "Why this recovery should work",
                "confidence": 75
            }
        """
        error_context = {
            "tool": tool_name,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "attempted_action": attempted_action,
            "traceback": traceback.format_exc()[-500:],  # Last 500 chars
            **(context or {})
        }
        
        # Get recent decisions for this tool
        recent = self._get_recent_decisions(tool_name, limit=3)
        if recent:
            error_context["recent_decisions"] = recent
        
        return self.ask(
            question=f"This tool encountered an error. How should it recover?",
            context=error_context,
            tool_name=f"{tool_name}_error_handler"
        )
    
    def validate_output(self,
                       tool_name: str,
                       output_data: Any,
                       expected_schema: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Validate tool output quality
        
        Args:
            tool_name: Name of tool that produced output
            output_data: The output to validate
            expected_schema: Optional schema to validate against
        
        Returns:
            {
                "is_valid": true/false,
                "issues": ["Missing column X", "Row 5 has invalid date"],
                "quality_score": 85,
                "recommendations": ["Add column Y", "Filter empty rows"]
            }
        """
        context = {
            "tool": tool_name,
            "output_type": type(output_data).__name__,
            "output_sample": str(output_data)[:500]
        }
        
        if expected_schema:
            context["expected_schema"] = expected_schema
        
        return self.ask(
            question="Is this output valid and complete?",
            context=context,
            tool_name=f"{tool_name}_validator"
        )
    
    def decide_next_action(self,
                          tool_name: str,
                          current_state: Dict[str, Any],
                          goal: str) -> Dict[str, Any]:
        """
        Decide what action to take next
        
        Args:
            tool_name: Name of tool making decision
            current_state: Current state/progress
            goal: What the tool is trying to achieve
        
        Returns:
            {
                "next_action": "specific_action_name",
                "parameters": {"param1": "value1"},
                "reasoning": "Why this is the right next step",
                "alternatives": ["action2", "action3"]
            }
        """
        return self.ask(
            question=f"What should I do next to achieve: {goal}",
            context={
                "tool": tool_name,
                "current_state": current_state,
                "goal": goal
            },
            tool_name=f"{tool_name}_planner"
        )
    
    def understand_evidence_context(self,
                                   evidence_files: List[str],
                                   rfi_code: str) -> Dict[str, Any]:
        """
        Understand what evidence is needed based on previous patterns
        
        Args:
            evidence_files: List of evidence file names from previous year
            rfi_code: RFI/requirement code
        
        Returns:
            {
                "evidence_type": "aws_config|logs|screenshots|documents",
                "required_content": ["backup_settings", "encryption_status"],
                "collection_method": "aws_cli|screenshot|api_export",
                "specific_instructions": "Navigate to...",
                "similar_past_evidence": ["file1.png", "file2.csv"]
            }
        """
        return self.ask(
            question=f"What evidence is needed for RFI {rfi_code}?",
            context={
                "previous_evidence_files": evidence_files,
                "rfi_code": rfi_code
            },
            tool_name="evidence_requirements_analyzer"
        )
    
    def optimize_tool_parameters(self,
                                tool_name: str,
                                default_params: Dict[str, Any],
                                observed_performance: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Suggest optimized parameters for a tool
        
        Args:
            tool_name: Name of tool to optimize
            default_params: Current/default parameters
            observed_performance: Past performance metrics
        
        Returns:
            {
                "optimized_params": {"timeout": 30, "retry_count": 3},
                "reasoning": "Based on observed failures...",
                "expected_improvement": "50% faster, 90% success rate"
            }
        """
        return self.ask(
            question=f"How can I optimize {tool_name} parameters?",
            context={
                "tool": tool_name,
                "current_params": default_params,
                "performance": observed_performance or {}
            },
            tool_name=f"{tool_name}_optimizer"
        )
    
    def _parse_json_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response with robust error handling"""
        try:
            # Sanitize
            cleaned = response_text.strip()
            cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
            cleaned = re.sub(r"```(?:json)?", "", cleaned)
            cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)
            
            # Extract JSON
            json_match = re.search(r"(\{.*?\})", cleaned, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                json_str = re.sub(r",\s*([}\]])", r"\1", json_str)
                return json.loads(json_str)
            else:
                # Return raw text as answer
                return {
                    "answer": cleaned[:500],
                    "actions": ["manual_review"],
                    "reasoning": "Could not parse structured response",
                    "confidence": 50
                }
        except Exception as e:
            console.print(f"[yellow]⚠️  JSON parse failed: {e}[/yellow]")
            return {
                "answer": response_text[:500],
                "actions": ["manual_review"],
                "reasoning": f"Parse error: {e}",
                "confidence": 0
            }
    
    def _remember_decision(self, 
                          tool_name: Optional[str],
                          question: str,
                          decision: Dict[str, Any],
                          context: Optional[Dict]) -> None:
        """Store decision history for learning"""
        self.decision_history.append({
            "tool": tool_name,
            "question": question,
            "decision": decision,
            "context": context,
            "timestamp": __import__('time').time()
        })
        
        # Keep only last 100 decisions
        if len(self.decision_history) > 100:
            self.decision_history = self.decision_history[-100:]
        
        # Store tool-specific context
        if tool_name:
            if tool_name not in self.tool_contexts:
                self.tool_contexts[tool_name] = []
            self.tool_contexts[tool_name].append({
                "question": question,
                "decision": decision
            })
            # Keep last 10 per tool
            if len(self.tool_contexts[tool_name]) > 10:
                self.tool_contexts[tool_name] = self.tool_contexts[tool_name][-10:]
    
    def _get_recent_decisions(self, tool_name: str, limit: int = 3) -> List[Dict]:
        """Get recent decisions for a specific tool"""
        if tool_name not in self.tool_contexts:
            return []
        return self.tool_contexts[tool_name][-limit:]
    
    def get_tool_learning(self, tool_name: str) -> Dict[str, Any]:
        """
        Get accumulated learning for a specific tool
        
        Returns:
            {
                "total_queries": 42,
                "common_questions": ["How to parse CSV", "Error recovery"],
                "success_patterns": ["Always use UTF-8", "Retry with delay"],
                "failure_patterns": ["Timeout on large files"]
            }
        """
        tool_decisions = [d for d in self.decision_history if d.get('tool') == tool_name]
        
        if not tool_decisions:
            return {"total_queries": 0, "learning": "No data yet"}
        
        return self.ask(
            question=f"What patterns have you learned about {tool_name}?",
            context={
                "tool": tool_name,
                "decision_count": len(tool_decisions),
                "recent_decisions": tool_decisions[-5:]
            },
            tool_name="meta_learner"
        )
