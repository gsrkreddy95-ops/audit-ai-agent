"""
AI Orchestrator Tools for Claude
=================================
These tool definitions enable Claude to use the AI Orchestrator which
directs all evidence collection based on brain's analysis of previous years.

This is the NEW architecture:
- Brain analyzes previous evidence → Creates plan → Directs tools → Monitors execution
"""

# Tool definition for analyze_and_plan
ORCHESTRATOR_ANALYZE_TOOL = {
    "name": "orchestrator_analyze_and_plan",
    "description": """🧠 AI BRAIN ANALYZES EVIDENCE AND CREATES COLLECTION PLAN

This is the NEW BRAIN-FIRST approach. The LLM brain:
1. Analyzes previous year's evidence from SharePoint
2. Understands what evidence is needed (patterns, types, sources)
3. Creates a detailed execution plan with specific tool actions
4. Specifies validation criteria and error handling

Use this FIRST when collecting evidence for any RFI. The brain will analyze
previous year's evidence and tell you exactly what to collect and how.

Example:
User: "Collect evidence for BCR-06.01"
You: Call this tool to analyze previous FY2024 evidence and get a plan

The brain will create a plan like:
- Step 1: Screenshot RDS encryption settings
- Step 2: Export audit logs 
- Step 3: Validate encryption is enabled
- etc.

WHEN TO USE:
- Starting evidence collection for any RFI
- Previous year's evidence is available
- Need brain to decide what evidence is needed
- Want automated, intelligent collection plan""",
    "input_schema": {
        "type": "object",
        "properties": {
            "rfi_code": {
                "type": "string",
                "description": "RFI requirement code (e.g., 'BCR-06.01', 'BCR-12.03')"
            },
            "previous_evidence_files": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "type": {"type": "string"},
                        "size": {"type": "number"},
                        "local_path": {"type": "string"}
                    }
                },
                "description": "List of previous year's evidence files with metadata. Get this from sharepoint_review_evidence tool."
            }
        },
        "required": ["rfi_code", "previous_evidence_files"]
    }
}

# Tool definition for execute_plan
ORCHESTRATOR_EXECUTE_TOOL = {
    "name": "orchestrator_execute_plan",
    "description": """🚀 EXECUTE THE BRAIN'S EVIDENCE COLLECTION PLAN

After the brain analyzes evidence and creates a plan, use this to execute it.
The brain will:
1. Monitor each tool execution
2. Validate outputs against criteria
3. Handle errors automatically
4. Correct tools if they deviate
5. Provide final assessment

Use this AFTER orchestrator_analyze_and_plan has created a plan.

Example:
1. Call orchestrator_analyze_and_plan → Brain creates plan
2. Call orchestrator_execute_plan → Brain executes and monitors

The brain monitors in real-time:
- "Tool A is executing... output looks good ✓"
- "Tool B failed, trying alternative approach..."
- "All evidence collected, quality score: 95%"

WHEN TO USE:
- After brain has analyzed and created a plan
- Ready to collect evidence automatically
- Want brain to monitor and correct execution""",
    "input_schema": {
        "type": "object",
        "properties": {
            "plan": {
                "type": "object",
                "description": "Optional execution plan. If not provided, uses the plan from previous analyze_and_plan call."
            }
        },
        "required": []
    }
}

# Combined tools list
ORCHESTRATOR_TOOLS = [
    ORCHESTRATOR_ANALYZE_TOOL,
    ORCHESTRATOR_EXECUTE_TOOL
]


def get_orchestrator_tools():
    """Get orchestrator tool definitions for Claude"""
    return ORCHESTRATOR_TOOLS


def explain_orchestrator_workflow():
    """
    Explain the brain-first workflow
    
    Returns:
        Explanation text
    """
    return """
🧠 BRAIN-FIRST ARCHITECTURE WORKFLOW:

OLD WAY (Tools decide):
1. Tool runs → Encounters uncertainty → Asks brain → Gets answer → Continues
2. Problem: Tools make decisions, brain is reactive

NEW WAY (Brain directs):
1. Brain analyzes previous evidence → Creates detailed plan → Directs tools → Monitors execution
2. Benefit: Brain proactive, tools execute commands

WORKFLOW:
┌─────────────────────────────────────────┐
│ 1. User: "Collect evidence for BCR-06.01" │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 2. Call orchestrator_analyze_and_plan   │
│    - Brain analyzes FY2024 evidence     │
│    - Understands patterns               │
│    - Creates execution plan             │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 3. Brain's Plan:                        │
│    Step 1: aws_screenshot (RDS config)  │
│    Step 2: aws_export (audit logs)      │
│    Step 3: validate encryption          │
│    Validation: Must show encryption=on  │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 4. Call orchestrator_execute_plan       │
│    - Brain executes Step 1              │
│    - Brain validates output             │
│    - Brain executes Step 2              │
│    - Brain handles errors               │
│    - Brain provides final assessment    │
└────────────────┬────────────────────────┘
                 ↓
┌─────────────────────────────────────────┐
│ 5. Result: Evidence collected           │
│    - 3/3 steps completed                │
│    - Quality score: 95%                 │
│    - Ready for upload                   │
└─────────────────────────────────────────┘

KEY BENEFITS:
✅ Brain analyzes before execution (not during)
✅ Detailed plan with validation criteria
✅ Real-time monitoring and correction
✅ Automatic error recovery
✅ Quality assessment
"""
