"""
AI Orchestrator - The Brain That Directs ALL Tools
=====================================
The LLM brain analyzes previous evidence, creates action plans, and directs tools.
Tools don't decide what to do - the BRAIN decides and tools execute.

Architecture:
1. Brain analyzes previous year's evidence from SharePoint
2. Brain creates detailed execution plan (what evidence to collect, how, in what order)
3. Brain monitors tool execution in real-time
4. Brain corrects tools if they deviate from plan
5. Brain validates outputs and decides next actions

This is PROACTIVE intelligence, not reactive "ask when uncertain"
"""

import os
import json
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from ai_brain.plan_models import ExecutionPlan, PlanStep
from evidence_manager.document_intelligence import DocumentIntelligence, DocumentInsight
from tools.universal_output_validator import UniversalOutputValidator  # NEW

console = Console()


class AIOrchestrator:
    """
    The Brain - Analyzes evidence, plans collection, directs tools
    
    Key Difference from Universal Intelligence:
    - UniversalIntelligence: Tools ask "what should I do?"
    - AIOrchestrator: Brain says "here's what you'll do, execute it"
    """
    
    def __init__(self, llm, evidence_manager, tool_executor,
                 document_intelligence: Optional[DocumentIntelligence] = None):
        """
        Args:
            llm: LLM instance (Claude)
            evidence_manager: Local evidence manager
            tool_executor: Tool executor with all tools
        """
        self.llm = llm
        self.evidence_manager = evidence_manager
        self.tool_executor = tool_executor
        self.output_validator = UniversalOutputValidator()  # NEW: Universal validation
        self.execution_plan = None
        self.plan_model: Optional[ExecutionPlan] = None
        self.execution_history = []
        self.current_rfi = None
        self.document_intelligence = document_intelligence or DocumentIntelligence(llm)
        self.latest_evidence_intelligence: List[DocumentInsight] = []

        console.print("\n[bold cyan]🧠 AI Orchestrator Initialized[/bold cyan]")
        console.print("[dim]  The Brain will analyze evidence and direct all tools[/dim]\n")

    # ------------------------------------------------------------------
    # LLM helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _strip_json_block(text: str) -> str:
        """Remove Markdown fences and return the raw JSON payload."""

        cleaned = text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned[3:].lstrip()
            if cleaned.lower().startswith("json"):
                cleaned = cleaned[4:].lstrip()
            if "```" in cleaned:
                cleaned = cleaned.rsplit("```", 1)[0]
        return cleaned.strip()

    def _call_llm_json(self, prompt: str, *, description: str) -> Tuple[Any, str]:
        """Invoke the LLM expecting JSON output and return parsed data."""

        if not self.llm:
            raise RuntimeError("LLM is not configured for orchestrator operations")

        response = self.llm.invoke(prompt)
        content = getattr(response, "content", str(response))
        cleaned = self._strip_json_block(content)

        try:
            return json.loads(cleaned), cleaned
        except json.JSONDecodeError as exc:
            raise ValueError(f"Failed to parse {description} JSON: {exc}") from exc
    
    def analyze_and_plan(self, rfi_code: str, previous_evidence_files: List[Dict]) -> Dict[str, Any]:
        """
        STEP 1: Brain analyzes previous evidence and creates execution plan
        
        This is the KEY method - the brain decides EVERYTHING before tools execute
        
        Args:
            rfi_code: RFI requirement code (e.g., "BCR-06.01")
            previous_evidence_files: List of previous year's evidence files with metadata
        
        Returns:
            Execution plan with specific tool actions
        """
        console.print(f"\n[bold cyan]🧠 BRAIN ANALYZING EVIDENCE FOR {rfi_code}[/bold cyan]")
        console.print("[dim]  Studying previous year's evidence to plan collection...[/dim]\n")
        
        # Prepare evidence analysis prompt
        evidence_summary, insights = self._summarize_evidence_files(
            previous_evidence_files,
            rfi_code=rfi_code,
        )
        self.latest_evidence_intelligence = insights
        
        prompt = f"""You are the AI Brain orchestrating evidence collection for audit RFI {rfi_code}.

PREVIOUS YEAR'S EVIDENCE:
{evidence_summary}

YOUR TASK:
Analyze the previous evidence and create a DETAILED execution plan for collecting this year's evidence.

PRIORITY RULES (CRITICAL):
1. If previous year's evidence contains screenshots (PNG/JPG), you MUST prioritize producing an equivalent or improved set of SCREENSHOTS FIRST before any data exports.
2. Only include export / data extraction steps (CSV/JSON) AFTER all required screenshots are planned, and ONLY if they add unique audit value not visually captured.
3. Maintain 1:1 or better coverage with prior screenshot set (do NOT reduce screenshot count unless redundant) and explicitly list each required screenshot as its own step.
4. For each screenshot step, include precise UI context (service, resource, tab, filter state) so it can be deterministically reproduced.
5. If subfolders or nested evidence patterns exist, reflect them in hierarchical ordering (e.g., group screenshots by resource or environment).
6. Minimize tool switching: batch all screenshot steps logically before exports to reduce session overhead.

You must specify:
1. What evidence is needed (based on previous year's patterns)
2. Which tools to use (aws_screenshot, aws_export, sharepoint_browser, etc.)
3. Exact parameters for each tool
4. Order of execution (some evidence may depend on others)
5. Validation criteria (how to know if evidence is good)
6. Error handling strategy (what to do if a tool fails)

AVAILABLE TOOLS:
- aws_take_screenshot: Capture AWS console screenshots
  * Parameters: service, resource_name, aws_account, aws_region, config_tab, rfi_code
  
- aws_export_data: Export AWS data to CSV/JSON
  * Parameters: service, export_type, aws_account, aws_region, format, rfi_code
  
- list_aws_resources: List AWS resources (RDS, S3, EC2, etc.)
  * Parameters: service, aws_account, aws_region
  
- intelligent_file_export: Export files with brain-powered parsing
  * Parameters: file_path, output_format, extraction_goal

OUTPUT FORMAT (JSON):
{{
  "rfi_code": "{rfi_code}",
  "evidence_type": "Database configuration and audit logs",
    "collection_strategy": "SCREENSHOTS FIRST (replicate prior visual evidence) then minimal supplemental exports if needed",
  "execution_plan": [
    {{
      "step": 1,
      "tool": "aws_take_screenshot",
      "description": "Capture RDS encryption settings",
      "parameters": {{
        "service": "rds",
        "resource_name": "prod-cluster-1",
        "aws_account": "123456789",
        "aws_region": "us-east-1",
        "config_tab": "Configuration",
        "rfi_code": "{rfi_code}"
      }},
      "validation": "Screenshot must show encryption status",
      "depends_on": [],
      "if_fails": "Try backup cluster or different region"
    }},
    {{
      "step": 2,
      "tool": "aws_export_data",
      "description": "Export audit logs for past 90 days",
      "parameters": {{
        "service": "rds",
        "export_type": "audit_logs",
        "aws_account": "123456789",
        "aws_region": "us-east-1",
        "format": "csv",
        "rfi_code": "{rfi_code}"
      }},
      "validation": "CSV must have timestamps and user actions",
      "depends_on": [1],
      "if_fails": "Export last 30 days only if 90 days times out"
    }}
  ],
  "success_criteria": [
    "All RDS clusters documented",
    "Encryption status visible",
    "Audit logs covering full period"
  ],
  "estimated_time_minutes": 15
}}

Create a comprehensive plan now:"""

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[cyan]Brain analyzing evidence patterns..."),
                console=console
            ) as progress:
                progress.add_task("analyze", total=None)
                plan_payload, raw_plan = self._call_llm_json(
                    prompt,
                    description="execution plan",
                )

            if not isinstance(plan_payload, dict):
                raise ValueError("LLM returned non-object execution plan")

            plan_dict = plan_payload
            plan_obj = ExecutionPlan.from_dict(plan_dict)

            # Store plan
            self.plan_model = plan_obj
            self.execution_plan = plan_obj.to_dict()
            self.current_rfi = rfi_code

            # Display plan
            self._display_execution_plan(plan_obj)

            evidence_payload = [
                {
                    "file_name": insight.file_name,
                    "document_type": insight.document_type,
                    "summary": insight.structured_insights.get("summary"),
                    "recommended_actions": insight.structured_insights.get("recommended_actions", []),
                    "key_entities": insight.structured_insights.get("key_entities", []),
                    "confidence": insight.structured_insights.get("confidence"),
                }
                for insight in insights
            ]

            return {
                "status": "success",
                "plan": plan_obj.to_dict(),
                "message": f"Brain created {len(plan_obj.steps)} step execution plan",
                "plan_progress": plan_obj.summarise_progress(),
                "evidence_intelligence": evidence_payload,
            }
        
        except Exception as e:
            console.print(f"[red]❌ Failed to obtain execution plan: {e}[/red]")
            if 'raw_plan' in locals():
                console.print(f"[yellow]Raw response:[/yellow]\n{raw_plan[:500]}")

            return {
                "status": "error",
                "error": f"Failed to generate execution plan: {e}",
                "raw_response": locals().get('raw_plan')
            }
    
    def execute_plan(self, plan: Optional[Dict] = None) -> Dict[str, Any]:
        """
        STEP 2: Execute the brain's plan, with brain monitoring each step
        
        Args:
            plan: Execution plan (uses stored plan if not provided)
        
        Returns:
            Execution results
        """
        if plan:
            self.plan_model = ExecutionPlan.from_dict(plan)
            self.execution_plan = self.plan_model.to_dict()

        if not self.execution_plan:
            return {
                "status": "error",
                "error": "No execution plan available. Call analyze_and_plan() first."
            }

        if not self.plan_model:
            self.plan_model = ExecutionPlan.from_dict(self.execution_plan)

        plan_obj = self.plan_model
        plan = plan_obj.to_dict()
        rfi_code = plan_obj.rfi_code
        steps = plan_obj.steps
        
        console.print(f"\n[bold green]🚀 EXECUTING BRAIN'S PLAN FOR {rfi_code}[/bold green]")
        console.print(f"[dim]  {len(steps)} steps to execute[/dim]\n")
        
        results = []
        completed_steps = [s.step for s in steps if s.status == 'completed']

        for step_obj in steps:
            step_num = step_obj.step
            tool_name = step_obj.tool
            description = step_obj.description
            parameters = step_obj.parameters or {}
            validation = step_obj.validation
            depends_on = step_obj.depends_on or []
            if_fails = step_obj.if_fails

            step_obj.mark_in_progress()

            console.print(f"[cyan]━━━ Step {step_num}: {description} ━━━[/cyan]")
            console.print(f"[dim]  Tool: {tool_name}[/dim]")
            console.print(f"[dim]  Validation: {validation}[/dim]")

            if depends_on:
                missing_deps = [d for d in depends_on if d not in completed_steps]
                if missing_deps:
                    console.print(f"[yellow]⚠️  Skipping - depends on steps {missing_deps}[/yellow]\n")
                    results.append({
                        "step": step_num,
                        "status": "skipped",
                        "reason": f"Dependencies not met: {missing_deps}"
                    })
                    step_obj.status = "skipped"
                    continue

            try:
                console.print(f"[yellow]🔧 Executing {tool_name}...[/yellow]")

                result = self.tool_executor.execute_tool(tool_name, parameters)
                
                # 🔍 NEW: Validate tool output
                console.print(f"\n[bold yellow]🔍 Validating tool output...[/bold yellow]")
                validation_result = self.output_validator.validate_tool_output(
                    tool_name=tool_name,
                    tool_parameters=parameters,
                    tool_output=result
                )
                
                # Add validation to result
                if isinstance(result, dict):
                    result["validation"] = validation_result
                
                # Check validation
                if not validation_result.get("valid"):
                    console.print(f"\n[bold red]⚠️  OUTPUT VALIDATION FAILED![/bold red]")
                    console.print(f"[red]   Confidence: {validation_result.get('confidence', 0)*100:.0f}%[/red]")
                    console.print(f"[red]   Issues: {validation_result.get('issues', [])}[/red]")
                    
                    if validation_result.get("diagnosis"):
                        console.print(f"\n[yellow]🔍 Diagnosis:[/yellow]")
                        console.print(f"[yellow]   {validation_result['diagnosis']}[/yellow]")
                    
                    if validation_result.get("suggested_fix"):
                        console.print(f"\n[cyan]💡 Suggested Fix:[/cyan]")
                        console.print(f"[cyan]   {validation_result['suggested_fix']}[/cyan]\n")
                    
                    # Mark step as needing attention
                    step.status = 'needs_attention'
                    console.print(f"[yellow]⚠️  Step marked as 'needs_attention'[/yellow]")
                else:
                    console.print(f"\n[green]✅ Output validated (Confidence: {validation_result.get('confidence', 0)*100:.0f}%)[/green]\n")

                if result.get('status') == 'success':
                    console.print(f"[green]✅ Step {step_num} completed[/green]")

                    is_valid = self._validate_step_output(
                        step_num=step_num,
                        tool_name=tool_name,
                        result=result,
                        validation_criteria=validation
                    )

                    if is_valid:
                        completed_steps.append(step_num)
                        step_obj.mark_completed(
                            output_summary=self._summarize_tool_output(result),
                            validation_notes="Validated successfully"
                        )
                        results.append({
                            "step": step_num,
                            "status": "success",
                            "tool": tool_name,
                            "result": result,
                            "validated": True
                        })
                    else:
                        console.print(f"[yellow]⚠️  Output validation failed[/yellow]")
                        step_obj.mark_invalid("Failed validation criteria")
                        results.append({
                            "step": step_num,
                            "status": "invalid_output",
                            "tool": tool_name,
                            "result": result,
                            "validated": False
                        })
                else:
                    console.print(f"[red]❌ Step {step_num} failed: {result.get('error')}[/red]")

                    recovery_action = self._handle_step_failure(
                        step_num=step_num,
                        tool_name=tool_name,
                        error=result.get('error'),
                        if_fails_guidance=if_fails
                    )

                    step_obj.mark_failed(result.get('error', 'Unknown error'))
                    results.append({
                        "step": step_num,
                        "status": "failed",
                        "tool": tool_name,
                        "error": result.get('error'),
                        "recovery_action": recovery_action
                    })

                console.print()

            except Exception as e:
                console.print(f"[red]❌ Step {step_num} exception: {e}[/red]\n")
                step_obj.mark_failed(str(e))
                results.append({
                    "step": step_num,
                    "status": "exception",
                    "tool": tool_name,
                    "error": str(e)
                })
        
        # Brain final assessment
        final_assessment = self._assess_execution_results(plan, results)
        
        # Store execution history
        self.execution_history.append({
            "timestamp": datetime.now().isoformat(),
            "rfi_code": rfi_code,
            "plan": plan_obj.to_dict(),
            "results": results,
            "assessment": final_assessment
        })

        # Persist latest plan snapshot for monitoring hooks
        self.execution_plan = plan_obj.to_dict()

        return {
            "status": "completed",
            "rfi_code": rfi_code,
            "steps_completed": len([s for s in plan_obj.steps if s.status == 'completed']),
            "steps_total": len(plan_obj.steps),
            "results": results,
            "assessment": final_assessment,
            "plan": plan_obj.to_dict()
        }
    
    def monitor_tool_action(self, tool_name: str, action: str, parameters: Dict) -> Dict[str, Any]:
        """
        REAL-TIME MONITORING: Brain watches tool actions and corrects if wrong
        
        This is called BEFORE a tool executes to ensure it's doing the right thing
        
        Args:
            tool_name: Tool about to execute
            action: Action tool is about to take
            parameters: Parameters tool will use
        
        Returns:
            Approval or correction from brain
        """
        console.print(f"\n[cyan]🧠 Brain monitoring: {tool_name} about to {action}[/cyan]")
        
        # Check against execution plan
        if self.execution_plan:
            # Find if this action is in the plan
            planned_steps = self.execution_plan.get('execution_plan', [])
            matching_step = None
            
            for step in planned_steps:
                if step.get('tool') == tool_name:
                    # Check if parameters match
                    planned_params = step.get('parameters', {})
                    if self._parameters_match(planned_params, parameters):
                        matching_step = step
                        break
            
            if matching_step:
                console.print(f"[green]✅ Action matches brain's plan (Step {matching_step.get('step')})[/green]")
                return {
                    "approved": True,
                    "message": "Action aligns with execution plan",
                    "step": matching_step.get('step')
                }
            else:
                console.print(f"[yellow]⚠️  Action NOT in brain's plan - asking brain for guidance...[/yellow]")
                
                # Ask brain if this is okay
                guidance = self._get_brain_guidance_for_unplanned_action(
                    tool_name=tool_name,
                    action=action,
                    parameters=parameters
                )
                
                return guidance
        else:
            console.print(f"[yellow]⚠️  No execution plan - brain will evaluate action...[/yellow]")
            
            # No plan exists, ask brain if action makes sense
            guidance = self._get_brain_guidance_for_unplanned_action(
                tool_name=tool_name,
                action=action,
                parameters=parameters
            )
            
            return guidance
    
    def _summarize_evidence_files(self, files: List[Dict],
                                  rfi_code: Optional[str] = None) -> Tuple[str, List[DocumentInsight]]:
        """Summarize evidence files for brain analysis."""
        if not files:
            return "No previous evidence found", []

        context = rfi_code or self.current_rfi

        if self.document_intelligence:
            return self.document_intelligence.build_brief_summary(files, context=context)

        summary = []
        for file_info in files:
            name = file_info.get('name', 'unknown')
            file_type = file_info.get('type', 'unknown')
            size = file_info.get('size', 0)
            summary.append(f"- {name} ({file_type}, {size} bytes)")

        return "\n".join(summary), []
    
    def _display_execution_plan(self, plan: Any):
        """Display the brain's execution plan."""

        if isinstance(plan, ExecutionPlan):
            plan_dict = plan.to_dict()
            steps_iterable = plan.steps
        else:
            plan_dict = plan or {}
            steps_iterable = plan_dict.get('execution_plan', [])

        console.print(Panel.fit(
            f"[bold green]Brain's Execution Plan[/bold green]\n\n"
            f"[cyan]RFI:[/cyan] {plan_dict.get('rfi_code')}\n"
            f"[cyan]Evidence Type:[/cyan] {plan_dict.get('evidence_type')}\n"
            f"[cyan]Strategy:[/cyan] {plan_dict.get('collection_strategy')}\n"
            f"[cyan]Steps:[/cyan] {len(plan_dict.get('execution_plan', []))}\n"
            f"[cyan]Estimated Time:[/cyan] {plan_dict.get('estimated_time_minutes', 'N/A')} minutes",
            border_style="green"
        ))

        for step in steps_iterable:
            if isinstance(step, PlanStep):
                step_no = step.step
                description = step.description
                tool = step.tool
                validation = step.validation
                status = step.status
            else:
                step_no = step.get('step')
                description = step.get('description')
                tool = step.get('tool')
                validation = step.get('validation')
                status = step.get('status', 'pending')

            console.print(f"\n[yellow]Step {step_no}:[/yellow] {description}")
            console.print(f"[dim]  Tool: {tool}[/dim]")
            console.print(f"[dim]  Validation: {validation}[/dim]")
            console.print(f"[dim]  Status: {status}[/dim]")

    def _summarize_tool_output(self, result: Dict[str, Any]) -> str:
        """Create a compact textual summary of a tool result."""

        if not isinstance(result, dict):
            return str(result)[:400]

        payload = result.get('result', result)
        if isinstance(payload, (dict, list)):
            try:
                return json.dumps(payload, default=str)[:400]
            except Exception:
                return str(payload)[:400]
        if isinstance(payload, str):
            return payload[:400]
        return str(payload)[:400]

    def _validate_step_output(self, step_num: int, tool_name: str, 
                              result: Dict, validation_criteria: str) -> bool:
        """
        Brain validates if tool output meets criteria
        
        Returns:
            True if valid, False otherwise
        """
        console.print(f"[cyan]🧠 Brain validating step {step_num} output...[/cyan]")
        
        prompt = f"""You are validating the output of a tool execution.

TOOL: {tool_name}
STEP: {step_num}
VALIDATION CRITERIA: {validation_criteria}

TOOL OUTPUT:
{json.dumps(result, indent=2)[:1000]}

QUESTION: Does this output meet the validation criteria?

Respond with JSON:
{{
  "valid": true/false,
  "reasoning": "Why output is valid or invalid",
  "issues": ["list", "of", "issues"] or [],
  "recommendation": "What to do if invalid"
}}"""

        try:
            validation, _ = self._call_llm_json(
                prompt,
                description=f"validation for step {step_num}",
            )

            if not isinstance(validation, dict):
                raise ValueError("Validation response was not a JSON object")

            is_valid = validation.get('valid', False)
            reasoning = validation.get('reasoning', '')
            
            if is_valid:
                console.print(f"[green]✅ Validation passed: {reasoning}[/green]")
            else:
                console.print(f"[red]❌ Validation failed: {reasoning}[/red]")
                issues = validation.get('issues', [])
                if issues:
                    console.print(f"[yellow]Issues:[/yellow]")
                    for issue in issues:
                        console.print(f"  - {issue}")
            
            return is_valid
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Validation error: {e}[/yellow]")
            # Default to True if brain can't validate
            return True
    
    def _handle_step_failure(self, step_num: int, tool_name: str, 
                             error: str, if_fails_guidance: str) -> Dict[str, Any]:
        """
        Brain decides what to do when a step fails
        
        Returns:
            Recovery action
        """
        console.print(f"[cyan]🧠 Brain analyzing failure of step {step_num}...[/cyan]")
        
        prompt = f"""A tool execution step has failed. Decide what to do.

STEP: {step_num}
TOOL: {tool_name}
ERROR: {error}
PLAN GUIDANCE: {if_fails_guidance}

OPTIONS:
1. Retry with same parameters
2. Retry with modified parameters
3. Skip this step and continue
4. Try alternative tool
5. Stop execution (critical failure)

Respond with JSON:
{{
  "action": "retry|skip|stop|alternative",
  "reasoning": "Why this is the best approach",
  "modifications": {{"param": "new_value"}} if retry with changes,
  "alternative_tool": "tool_name" if using alternative
}}"""

        try:
            recovery, _ = self._call_llm_json(
                prompt,
                description=f"failure handling for step {step_num}",
            )

            if not isinstance(recovery, dict):
                raise ValueError("Recovery response was not a JSON object")

            action = recovery.get('action', 'skip')
            reasoning = recovery.get('reasoning', '')
            
            console.print(f"[yellow]Brain decision: {action.upper()}[/yellow]")
            console.print(f"[dim]Reasoning: {reasoning}[/dim]")
            
            return recovery
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Recovery decision error: {e}[/yellow]")
            return {
                "action": "skip",
                "reasoning": "Brain error, defaulting to skip"
            }
    
    def _assess_execution_results(self, plan: Dict, results: List[Dict]) -> Dict[str, Any]:
        """
        Brain's final assessment of execution
        
        Returns:
            Assessment with recommendations
        """
        console.print(f"\n[cyan]🧠 Brain assessing execution results...[/cyan]")
        
        success_criteria = plan.get('success_criteria', [])
        
        prompt = f"""Assess the execution results against success criteria.

SUCCESS CRITERIA:
{json.dumps(success_criteria, indent=2)}

EXECUTION RESULTS:
{json.dumps(results, indent=2)[:2000]}

Provide assessment in JSON:
{{
  "overall_success": true/false,
  "criteria_met": ["criterion1", "criterion2"],
  "criteria_failed": ["criterion3"],
  "quality_score": 0-100,
  "recommendations": ["what to improve", "missing evidence"],
  "ready_for_upload": true/false
}}"""

        try:
            assessment, _ = self._call_llm_json(
                prompt,
                description="execution assessment",
            )

            if not isinstance(assessment, dict):
                raise ValueError("Assessment response was not a JSON object")

            success = assessment.get('overall_success', False)
            quality = assessment.get('quality_score', 0)
            
            if success:
                console.print(f"[green]✅ Execution successful (Quality: {quality}%)[/green]")
            else:
                console.print(f"[red]❌ Execution incomplete (Quality: {quality}%)[/red]")
            
            criteria_met = assessment.get('criteria_met', [])
            criteria_failed = assessment.get('criteria_failed', [])
            
            if criteria_met:
                console.print(f"[green]Met:[/green] {', '.join(criteria_met)}")
            if criteria_failed:
                console.print(f"[red]Failed:[/red] {', '.join(criteria_failed)}")
            
            return assessment
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Assessment error: {e}[/yellow]")
            return {
                "overall_success": False,
                "quality_score": 0,
                "error": str(e)
            }
    
    def _parameters_match(self, planned: Dict, actual: Dict) -> bool:
        """Check if actual parameters match planned parameters"""
        # Simple match - could be more sophisticated
        for key, value in planned.items():
            if key not in actual or actual[key] != value:
                return False
        return True
    
    def _get_brain_guidance_for_unplanned_action(self, tool_name: str, 
                                                  action: str, parameters: Dict) -> Dict[str, Any]:
        """
        Ask brain if an unplanned action is okay
        
        Returns:
            Guidance (approve or correct)
        """
        prompt = f"""A tool is about to execute an action that wasn't in your plan.

TOOL: {tool_name}
ACTION: {action}
PARAMETERS: {json.dumps(parameters, indent=2)}

CURRENT RFI: {self.current_rfi}
YOUR PLAN: {json.dumps(self.execution_plan, indent=2)[:1000] if self.execution_plan else "No plan"}

QUESTION: Should this action proceed, or should it be modified/blocked?

Respond with JSON:
{{
  "approved": true/false,
  "reasoning": "Why approve or block",
  "corrections": {{"param": "corrected_value"}} if needs changes,
  "alternative_action": "what to do instead" if blocking
}}"""

        try:
            guidance, _ = self._call_llm_json(
                prompt,
                description="unplanned action guidance",
            )

            if not isinstance(guidance, dict):
                raise ValueError("Guidance response was not a JSON object")

            approved = guidance.get('approved', False)
            reasoning = guidance.get('reasoning', '')
            
            if approved:
                console.print(f"[green]✅ Brain approved: {reasoning}[/green]")
            else:
                console.print(f"[red]❌ Brain blocked: {reasoning}[/red]")
            
            return guidance
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Brain guidance error: {e}[/yellow]")
            # Default to approve with warning
            return {
                "approved": True,
                "reasoning": f"Brain error, defaulting to approve: {e}"
            }
