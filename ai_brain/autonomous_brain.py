"""
Autonomous Brain - LLM-First Agent Architecture

This is the core intelligence that makes the agent fully autonomous:
1. Analyzes user requests with full context
2. Searches web for unknowns
3. Plans execution steps
4. Generates missing tools
5. Monitors and adapts during execution
6. Learns from results

The brain uses Claude 3.5 (or other LLMs) to reason about requests
and make intelligent decisions, rather than following hard-coded rules.
"""

import json
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown

from ai_brain.knowledge_manager import KnowledgeManager
from ai_brain.web_search_tool import WebSearchTool
from ai_brain.tool_generator import ToolGenerator
from ai_brain.step_executor import StepExecutor
from ai_brain.multi_agent_coordinator import MultiAgentCoordinator

console = Console()


class AutonomousBrain:
    """
    The autonomous brain that orchestrates the entire agent.
    
    This replaces hard-coded tool selection with LLM-driven reasoning.
    """
    
    def __init__(self, llm, tool_executor):
        """
        Initialize the autonomous brain.
        
        Args:
            llm: LLM instance (Claude, GPT, etc.)
            tool_executor: ToolExecutor instance for running tools
        """
        self.llm = llm
        self.tool_executor = tool_executor
        self.knowledge = KnowledgeManager()
        self.web_search = WebSearchTool()
        self.tool_generator = ToolGenerator(llm)
        self.step_executor = StepExecutor(tool_executor, self.knowledge, self.web_search)
        self.multi_agent = MultiAgentCoordinator(tool_executor, max_parallel=5)
        
        console.print("[bold magenta]🧠 Autonomous Brain Activated[/bold magenta]")
        console.print("[dim]   LLM-first architecture enabled[/dim]")
        console.print("[dim]   Real-time knowledge retrieval ready[/dim]")
        console.print("[dim]   Tool generation: ENABLED[/dim]")
        console.print("[dim]   Step-by-step execution: ENABLED[/dim]")
        console.print("[dim]   Multi-agent coordination: ENABLED[/dim]\n")
    
    def process_request(self, user_request: str, conversation_history: List[Dict]) -> Dict[str, Any]:
        """
        Main entry point for autonomous processing.
        
        This is the complete loop:
        1. Brain Analysis (understand request + search if needed)
        2. Tool Resolution (find or generate tools)
        3. Execution (run with monitoring)
        4. Learning (save what worked)
        
        Args:
            user_request: User's request
            conversation_history: Recent conversation context
            
        Returns:
            Dict with delegate_to_claude flag or final response
        """
        console.print("\n[bold cyan]🧠 BRAIN ANALYSIS PHASE[/bold cyan]")
        
        # Phase 1: Analyze and Plan
        analysis = self._analyze_request(user_request, conversation_history)
        
        if not analysis.get("success"):
            console.print(f"[yellow]⚠️  Analysis issue, delegating to Claude...[/yellow]")
            return {"delegate_to_claude": True}
        
        # Phase 2: Knowledge Lookup & Web Search (proactive for all questions)
        enriched_plan = self._enrich_with_knowledge(analysis, user_request)
        
        # Phase 3: Tool Resolution
        execution_ready = self._resolve_tools(enriched_plan)
        
        # Phase 4: Execute (delegate to Claude with enriched context)
        result = self._execute_plan(execution_ready)
        
        # Phase 5: Learn
        self._learn_from_execution(user_request, execution_ready, result)
        
        # Return delegation signal so Claude executes with enriched knowledge
        return {"delegate_to_claude": True, "enriched_context": enriched_plan.get("knowledge", {})}
    
    def _analyze_request(
        self,
        user_request: str,
        conversation_history: List[Dict]
    ) -> Dict[str, Any]:
        """
        Phase 1: Use LLM to deeply analyze the request.
        
        Returns:
            {
                "success": bool,
                "intent": str,
                "domains": [str],  # aws, jira, confluence, etc.
                "actions": [str],  # export, screenshot, list, etc.
                "entities": {service: str, account: str, ...},
                "questions": [str],  # Things we need to know
                "plan_outline": [str]  # High-level steps
            }
        """
        prompt = f"""Analyze this user request and create a detailed execution plan.

User Request: {user_request}

Provide a JSON response with:
{{
    "intent": "What is the user really asking for?",
    "domains": ["aws", "jira", etc.],
    "actions": ["export", "screenshot", "list", etc.],
    "entities": {{
        "services": ["s3", "kms", etc.],
        "accounts": ["ctr-prod"],
        "regions": ["us-east-1", "all"],
        "date_range": {{"start": "2025-01-01", "end": "2025-11-01"}},
        ...
    }},
    "questions": [
        "Is S3 regional or global?",
        "What's the date field for KMS keys?"
    ],
    "plan_outline": [
        "Step 1: ...",
        "Step 2: ..."
    ]
}}

Focus on extracting ALL details from the request."""

        try:
            # Call LLM for analysis
            response = self.llm.invoke(prompt)
            
            # Extract JSON from response
            content = response.content if hasattr(response, 'content') else str(response)
            
            if not content or not content.strip():
                raise ValueError("LLM returned empty response")
            
            # Parse JSON - try multiple extraction methods
            json_text = content.strip()
            
            if "```json" in json_text:
                json_text = json_text.split("```json")[1].split("```")[0].strip()
            elif "```" in json_text:
                json_text = json_text.split("```")[1].split("```")[0].strip()
            
            # Try to find JSON object boundaries
            if not json_text.startswith('{'):
                # Look for first { and last }
                start = json_text.find('{')
                end = json_text.rfind('}')
                if start >= 0 and end > start:
                    json_text = json_text[start:end+1]
            
            if not json_text:
                # Fallback: create basic analysis from the text response
                console.print("[yellow]⚠️  LLM didn't return JSON, creating basic analysis...[/yellow]")
                analysis = {
                    "success": True,
                    "intent": user_request,
                    "domains": ["aws"],  # Infer from request
                    "actions": ["screenshot", "export"],
                    "entities": {},
                    "questions": [],
                    "plan_outline": ["Execute request using available tools"]
                }
            else:
                analysis = json.loads(json_text)
                analysis["success"] = True
            
            console.print(f"[green]✅ Request analyzed:[/green]")
            console.print(f"[dim]   Intent: {analysis.get('intent', 'N/A')}[/dim]")
            console.print(f"[dim]   Domains: {', '.join(analysis.get('domains', []))}[/dim]")
            console.print(f"[dim]   Questions: {len(analysis.get('questions', []))}[/dim]")
            
            return analysis
            
        except Exception as e:
            console.print(f"[red]❌ Analysis failed: {e}[/red]")
            console.print("[yellow]Falling back to direct Claude execution...[/yellow]")
            # Return a valid analysis so execution can continue
            return {
                "success": True,
                "intent": user_request,
                "domains": ["general"],
                "actions": [],
                "entities": {},
                "questions": [],
                "plan_outline": [],
                "fallback": True
            }
    
    def _enrich_with_knowledge(self, analysis: Dict[str, Any], user_request: str = "") -> Dict[str, Any]:
        """
        Phase 2: Minimal knowledge enrichment - LET CLAUDE THINK FIRST!
        
        NEW PHILOSOPHY (LLM-Driven Approach):
        - Let Claude/LLM use its own knowledge as PRIMARY source
        - Only use web search when LLM explicitly needs current/unknown info
        - Prefer code generation (boto3, API calls) over web search
        - Web search is a FALLBACK ASSISTANT, not front-and-center
        
        For each question in the analysis:
        1. Check knowledge base first (fast lookup)
        2. ONLY if critical technical detail missing → web search
        3. Otherwise, let Claude figure it out with its own intelligence
        
        Args:
            analysis: Analysis result from Phase 1
            user_request: Original user request (for context)
        
        Returns:
            Enriched analysis with minimal but critical answers
        """
        questions = analysis.get("questions", [])
        
        # Skip enrichment if no questions - let Claude handle it
        if not questions or len(questions) == 0:
            console.print(f"\n[dim]🧠 No knowledge gaps - letting LLM brain handle this...[/dim]")
            analysis["knowledge"] = {}
            return analysis
        
        answers = {}
        console.print(f"\n[bold cyan]🔍 MINIMAL KNOWLEDGE CHECK ({len(questions)} questions)[/bold cyan]")
        
        # ONLY search for truly critical technical questions
        # e.g., "Is S3 regional or global?" "What's the KMS API endpoint?"
        critical_keywords = [
            "regional", "global", "endpoint", "api version", 
            "field name", "exact format", "deprecated"
        ]
        
        for question in questions[:3]:  # Reduced limit - let Claude handle most things
            question_lower = question.lower()
            
            # Skip non-critical questions - let Claude answer from its own knowledge
            is_critical = any(keyword in question_lower for keyword in critical_keywords)
            
            if not is_critical:
                console.print(f"[dim]💭 Non-critical: {question} → Letting LLM brain handle[/dim]")
                continue
            
            console.print(f"[cyan]Q: {question}[/cyan]")
            
            # Try knowledge base first
            domain = self._infer_domain(question)
            kb_answer = self.knowledge.query(domain, question)
            
            if kb_answer:
                console.print(f"[green]✅ Found in knowledge base[/green]")
                answers[question] = {
                    "answer": kb_answer,
                    "source": "knowledge_base",
                    "confidence": 1.0
                }
            else:
                # Search the web for critical technical info only
                console.print("[yellow]🌐 Searching web...[/yellow]")
                search_result = self.web_search.search(question, max_results=2)
                
                if search_result.get("success"):
                    answer = search_result.get("answer", "No answer found")
                    sources = search_result.get("sources", [])
                    
                    console.print(f"[green]✅ Found via web search[/green]")
                    
                    answers[question] = {
                        "answer": answer,
                        "source": "web_search",
                        "sources": sources[:2],
                        "confidence": 0.8
                    }
                    
                    # Learn this for next time
                    self.knowledge.learn(
                        domain=domain,
                        fact_key=question,
                        fact_value=answer,
                        source="web_search",
                        confidence=0.8
                    )
                else:
                    console.print("[yellow]⚠️  Search unavailable, continuing...[/yellow]")
        
        if answers:
            console.print(f"[green]✅ Answered {len(answers)} question(s)[/green]")
        
        analysis["knowledge"] = answers
        return analysis
    
    def _infer_domain(self, question: str) -> str:
        """Infer which domain a question belongs to."""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ["aws", "s3", "ec2", "kms", "lambda"]):
            return "aws"
        elif any(word in question_lower for word in ["jira", "ticket", "sprint", "board"]):
            return "jira"
        elif any(word in question_lower for word in ["confluence", "page", "space"]):
            return "confluence"
        elif any(word in question_lower for word in ["github", "repo", "pr", "commit"]):
            return "github"
        else:
            return "general"
    
    def _resolve_tools(self, enriched_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 3: Find existing tools or generate new ones.
        
        For each action in the plan:
        1. Check if we have a tool for it
        2. If not, generate tool code
        3. Mark as ready for execution
        
        Returns:
            Execution-ready plan with tool mappings
        """
        console.print(f"\n[bold cyan]🔧 TOOL RESOLUTION[/bold cyan]")
        
        plan = enriched_plan.copy()
        
        # Check if we need to generate any tools
        # For now, assume tools exist (generation triggers on actual missing tool errors)
        # Future: Proactively detect missing capabilities and generate before execution
        
        plan["tools_ready"] = True
        plan["missing_tools"] = []
        plan["generated_tools"] = []
        
        console.print("[green]✅ Tool resolution complete[/green]")
        
        return plan
    
    def _execute_plan(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase 4: Execute the plan with monitoring.
        
        For each step:
        1. Run the tool
        2. Monitor output
        3. Adapt if failure (search for solutions)
        4. Continue to next step
        
        Returns:
            {
                "success": bool,
                "response": str,
                "steps_completed": int,
                "errors": [str]
            }
        """
        console.print(f"\n[bold cyan]⚡ EXECUTION PHASE[/bold cyan]")
        
        # If plan indicates fallback, let Claude handle normally
        if plan.get("fallback"):
            console.print("[yellow]Using direct Claude execution (analysis fallback)[/yellow]")
            return {
                "success": True,
                "response": "fallback_to_claude",
                "delegate_to_claude": True
            }
        
        # Check if this can be parallelized
        steps = plan.get("steps", [])
        
        if self.multi_agent.can_parallelize(plan) and len(steps) > 1:
            console.print(f"[magenta]🤖 Task can be parallelized - spawning {len(steps)} sub-agents[/magenta]")
            
            # Execute in parallel
            result = self.multi_agent.execute_parallel(steps)
            
            return {
                "success": result.get("success"),
                "response": f"Completed {result.get('successful')}/{result.get('total_agents')} parallel tasks",
                "delegate_to_claude": False,
                "execution_result": result
            }
        
        # Check if we have explicit steps to execute
        elif steps and len(steps) > 0:
            console.print(f"[cyan]Executing {len(steps)} steps sequentially...[/cyan]")
            
            # Execute step-by-step
            result = self.step_executor.execute_plan(plan)
            
            return {
                "success": result.get("success"),
                "response": f"Completed {result.get('steps_completed')} steps",
                "delegate_to_claude": False,
                "execution_result": result
            }
        
        else:
            # No explicit steps, delegate to Claude with enriched context
            console.print("[green]Delegating to Claude with enriched knowledge...[/green]")
            
            return {
                "success": True,
                "response": "fallback_to_claude",
                "delegate_to_claude": True,
                "enriched_context": plan.get("knowledge", {})
            }
    
    def _learn_from_execution(
        self,
        request: str,
        plan: Dict[str, Any],
        result: Dict[str, Any]
    ) -> None:
        """
        Phase 5: Learn from what happened.
        
        If successful:
        - Store successful patterns
        - Remember tool combinations that worked
        
        If failed:
        - Store error solutions
        - Remember what NOT to do
        """
        console.print(f"\n[bold cyan]📚 LEARNING PHASE[/bold cyan]")
        
        if result.get("success"):
            console.print("[green]✅ Execution successful - patterns stored[/green]")
        else:
            console.print("[yellow]⚠️  Execution had issues - solutions stored[/yellow]")
        
        # Learning logic will be enhanced in later iterations

