#!/usr/bin/env python3
"""
Demo: Universal Intelligence in Action
Shows how ALL tools now query the brain dynamically
"""

import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from rich.console import Console
from rich.panel import Panel
from rich.markdown import Markdown
from langchain_aws import ChatBedrock
from ai_brain.universal_intelligence import UniversalIntelligence
from ai_brain.intelligent_tools import (
    IntelligentFileExporter,
    IntelligentAWSCLI,
    IntelligentEvidenceCollector
)

console = Console()


def demo_universal_intelligence():
    """Demonstrate universal intelligence across all tools"""
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]🧠 Universal Intelligence Demo[/bold cyan]\n"
        "[dim]Showing how ALL tools now use LLM brain for decisions[/dim]",
        border_style="cyan"
    ))
    console.print("="*80 + "\n")
    
    # Initialize LLM
    console.print("[yellow]📡 Initializing Claude 3.5 Sonnet...[/yellow]")
    try:
        llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        console.print("[green]✅ LLM initialized[/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize LLM: {e}[/red]")
        console.print("[yellow]💡 Make sure AWS credentials are configured[/yellow]")
        return
    
    # Initialize Universal Intelligence
    console.print("[yellow]🧠 Creating Universal Intelligence Hub...[/yellow]")
    intelligence = UniversalIntelligence(llm)
    console.print("[green]✅ Universal Intelligence ready[/green]\n")
    
    # Demo 1: General "Ask" - Any tool can query
    console.print(Panel.fit(
        "[bold cyan]Demo 1: Universal Ask[/bold cyan]\n"
        "[dim]Any tool can ask the brain anything[/dim]",
        border_style="cyan"
    ))
    
    response = intelligence.ask(
        question="If I have a file called 'database_export_20250115.xlsx', what's the best way to extract data from it?",
        context={"file_type": "xlsx", "source": "database"},
        tool_name="demo_tool"
    )
    
    console.print(f"[green]Brain's Answer:[/green]")
    console.print(f"[dim]{response.get('answer')}[/dim]")
    console.print(f"[yellow]Confidence: {response.get('confidence')}%[/yellow]\n")
    
    # Demo 2: File Format Detection
    console.print(Panel.fit(
        "[bold cyan]Demo 2: File Format Detection[/bold cyan]\n"
        "[dim]Brain intelligently detects file formats[/dim]",
        border_style="cyan"
    ))
    
    # Simulate different file paths
    test_files = [
        "data.csv",
        "report.xlsx",
        "config.json",
        "documentation.pdf",
        "data_export_20250115.unknown"
    ]
    
    for file_path in test_files:
        result = intelligence.detect_file_format(file_path)
        console.print(f"[cyan]File:[/cyan] {file_path}")
        console.print(f"[green]  Format:[/green] {result.get('answer')}")
        console.print(f"[yellow]  Confidence:[/yellow] {result.get('confidence')}%")
        
        additional = result.get('additional_context', {})
        if additional:
            console.print(f"[dim]  Notes:[/dim]")
            for key, value in additional.items():
                console.print(f"[dim]    - {key}: {value}[/dim]")
        console.print()
    
    # Demo 3: Error Recovery
    console.print(Panel.fit(
        "[bold cyan]Demo 3: Error Recovery[/bold cyan]\n"
        "[dim]Brain suggests fixes when tools fail[/dim]",
        border_style="cyan"
    ))
    
    # Simulate an error
    error = Exception("Connection timeout: AWS RDS endpoint unreachable")
    recovery = intelligence.handle_tool_error(
        tool_name="aws_cli",
        error=error,
        attempted_action="List RDS clusters in us-east-1",
        context={"service": "rds", "region": "us-east-1"}
    )
    
    console.print(f"[red]Error:[/red] {error}")
    console.print(f"[green]Brain's Recovery Action:[/green] {recovery.get('recovery_action')}")
    console.print(f"[yellow]Reasoning:[/yellow] {recovery.get('reasoning')}")
    console.print(f"[cyan]Suggested Changes:[/cyan]")
    for change in recovery.get('retry_with_changes', []):
        console.print(f"  - {change}")
    console.print()
    
    # Demo 4: Evidence Requirement Understanding
    console.print(Panel.fit(
        "[bold cyan]Demo 4: Evidence Requirement Analysis[/bold cyan]\n"
        "[dim]Brain analyzes what evidence is needed[/dim]",
        border_style="cyan"
    ))
    
    # Simulate previous year's evidence
    previous_evidence = [
        "FY2024_RDS_encryption_config.png",
        "FY2024_RDS_backup_settings.png",
        "FY2024_audit_logs_export.csv"
    ]
    
    requirements = intelligence.understand_evidence_context(
        evidence_files=previous_evidence,
        rfi_code="BCR-06.01"
    )
    
    console.print(f"[cyan]Previous Evidence:[/cyan]")
    for file in previous_evidence:
        console.print(f"  - {file}")
    console.print()
    console.print(f"[green]Brain's Analysis:[/green]")
    console.print(f"[dim]{requirements.get('answer')}[/dim]")
    
    additional = requirements.get('additional_context', {})
    if additional:
        console.print(f"\n[yellow]Details:[/yellow]")
        for key, value in additional.items():
            console.print(f"  [cyan]{key}:[/cyan] {value}")
    console.print()
    
    # Demo 5: Extraction Strategy
    console.print(Panel.fit(
        "[bold cyan]Demo 5: Extraction Strategy Suggestion[/bold cyan]\n"
        "[dim]Brain suggests how to extract data from files[/dim]",
        border_style="cyan"
    ))
    
    file_info = {
        "answer": "Excel spreadsheet with multiple sheets",
        "confidence": 95,
        "additional_context": {
            "sheets": ["Summary", "Details", "Raw Data"],
            "has_macros": False
        }
    }
    
    strategy = intelligence.suggest_extraction_strategy(
        file_info=file_info,
        purpose="Extract audit trail data"
    )
    
    console.print(f"[cyan]File Info:[/cyan] {file_info['answer']}")
    console.print(f"[green]Brain's Strategy:[/green] {strategy.get('answer')}")
    console.print(f"\n[yellow]Actions:[/yellow]")
    for action in strategy.get('actions', []):
        console.print(f"  {action}")
    
    params = strategy.get('parameters', {})
    if params:
        console.print(f"\n[cyan]Parameters:[/cyan]")
        for key, value in params.items():
            console.print(f"  {key}: {value}")
    console.print()
    
    # Demo 6: Decision History
    console.print(Panel.fit(
        "[bold cyan]Demo 6: Decision History[/bold cyan]\n"
        "[dim]Brain tracks all decisions for learning[/dim]",
        border_style="cyan"
    ))
    
    console.print(f"[cyan]Total Decisions Made:[/cyan] {len(intelligence.decision_history)}")
    console.print(f"\n[yellow]Recent Decisions:[/yellow]")
    
    for i, decision in enumerate(intelligence.decision_history[-5:], 1):
        console.print(f"\n[green]{i}. {decision['tool']}[/green]")
        console.print(f"[dim]   Q: {decision['question'][:80]}...[/dim]")
        console.print(f"[dim]   A: {decision['answer'][:80]}...[/dim]")
        console.print(f"[yellow]   Confidence: {decision['confidence']}%[/yellow]")
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold green]✅ Universal Intelligence Demo Complete![/bold green]\n"
        "[dim]All tools can now query the brain for intelligent decisions[/dim]",
        border_style="green"
    ))
    console.print("="*80 + "\n")


def demo_intelligent_tools():
    """Demonstrate intelligent tool wrappers"""
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold cyan]🔧 Intelligent Tools Demo[/bold cyan]\n"
        "[dim]Showing tool wrappers that use universal intelligence[/dim]",
        border_style="cyan"
    ))
    console.print("="*80 + "\n")
    
    # Initialize LLM
    console.print("[yellow]📡 Initializing LLM...[/yellow]")
    try:
        llm = ChatBedrock(
            model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        console.print("[green]✅ LLM initialized[/green]\n")
    except Exception as e:
        console.print(f"[red]❌ Failed to initialize LLM: {e}[/red]")
        return
    
    # Initialize intelligence
    intelligence = UniversalIntelligence(llm)
    
    # Demo Intelligent File Exporter
    console.print(Panel.fit(
        "[bold cyan]Intelligent File Exporter[/bold cyan]\n"
        "[dim]Brain-powered file format detection and extraction[/dim]",
        border_style="cyan"
    ))
    
    exporter = IntelligentFileExporter(intelligence)
    console.print("[green]✅ File exporter ready (with brain power!)[/green]")
    console.print("[dim]   Can handle: CSV, JSON, Excel, PDF, unknown formats[/dim]")
    console.print("[dim]   Features: Auto-detect format, suggest parsing, validate output, error recovery[/dim]\n")
    
    # Demo Intelligent AWS CLI
    console.print(Panel.fit(
        "[bold cyan]Intelligent AWS CLI[/bold cyan]\n"
        "[dim]Brain-optimized AWS command execution[/dim]",
        border_style="cyan"
    ))
    
    aws_cli = IntelligentAWSCLI(intelligence)
    console.print("[green]✅ AWS CLI ready (with brain power!)[/green]")
    console.print("[dim]   Features: Command optimization, error recovery, parameter tuning[/dim]")
    
    # Simulate command execution
    result = aws_cli.execute_command(
        service="rds",
        action="list-clusters",
        context={"region": "us-east-1"}
    )
    console.print(f"\n[cyan]Command Strategy:[/cyan]")
    console.print(f"[dim]{result.get('answer')}[/dim]\n")
    
    # Demo Intelligent Evidence Collector
    console.print(Panel.fit(
        "[bold cyan]Intelligent Evidence Collector[/bold cyan]\n"
        "[dim]Brain-guided evidence collection planning[/dim]",
        border_style="cyan"
    ))
    
    collector = IntelligentEvidenceCollector(intelligence)
    console.print("[green]✅ Evidence collector ready (with brain power!)[/green]")
    console.print("[dim]   Features: Requirement analysis, collection planning, validation[/dim]")
    
    # Simulate evidence collection
    previous_evidence = [
        "FY2024_RDS_config.png",
        "FY2024_backup_settings.png"
    ]
    
    plan = collector.collect_for_rfi(
        rfi_code="BCR-06.01",
        previous_evidence=previous_evidence
    )
    
    console.print(f"\n[cyan]Collection Plan:[/cyan]")
    console.print(f"[green]Evidence Type:[/green] {plan.get('answer')}")
    
    context = plan.get('additional_context', {})
    if context:
        console.print(f"\n[yellow]Required Content:[/yellow]")
        for item in context.get('required_content', []):
            console.print(f"  - {item}")
        
        console.print(f"\n[yellow]Collection Method:[/yellow] {context.get('collection_method')}")
    
    console.print("\n" + "="*80)
    console.print(Panel.fit(
        "[bold green]✅ Intelligent Tools Demo Complete![/bold green]\n"
        "[dim]All tools now have access to universal intelligence[/dim]",
        border_style="green"
    ))
    console.print("="*80 + "\n")


def show_architecture():
    """Show the universal intelligence architecture"""
    
    architecture = """
# Universal Intelligence Architecture

## Before (Siloed Intelligence) ❌
```
Browser Tools → BrowserIntelligence (LLM)
CSV Export → Hardcoded logic
PDF Tool → Fixed templates
AWS CLI → Manual commands
```

## After (Universal Intelligence) ✅
```
                UniversalIntelligence (LLM Brain)
                          ↓
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
   File Exporter      AWS CLI      Evidence Collector
        ↓                 ↓                 ↓
   Browser Tools    PDF Generator   SharePoint Tools
```

## Key Features
- ✅ **Central Brain**: All tools query same intelligence hub
- ✅ **Dynamic Decisions**: No hardcoded logic, LLM decides
- ✅ **Error Recovery**: Brain suggests fixes automatically
- ✅ **Decision History**: Learning from past decisions
- ✅ **Tool Agnostic**: Any tool can use any intelligence method
- ✅ **Fallback Support**: Works without LLM (degraded mode)

## Intelligence Methods
1. `ask()` - General query for any decision
2. `detect_file_format()` - Smart format detection
3. `suggest_extraction_strategy()` - How to parse data
4. `handle_tool_error()` - Error recovery
5. `validate_output()` - Quality checking
6. `decide_next_action()` - Action planning
7. `understand_evidence_context()` - Requirement analysis
8. `optimize_tool_parameters()` - Performance tuning
9. `analyze_file_structure()` - Structure analysis
10. `suggest_workflow()` - Multi-step planning
"""
    
    console.print("\n")
    md = Markdown(architecture)
    console.print(Panel(md, title="[bold cyan]Architecture Overview[/bold cyan]", border_style="cyan"))
    console.print("\n")


def main():
    """Main demo entry point"""
    
    console.print("\n[bold cyan]🎯 Universal Intelligence Demo Suite[/bold cyan]")
    console.print("[dim]Choose a demo to run:[/dim]\n")
    
    console.print("1. Universal Intelligence Hub")
    console.print("2. Intelligent Tool Wrappers")
    console.print("3. Architecture Overview")
    console.print("4. Run All Demos")
    console.print("5. Exit\n")
    
    try:
        choice = input("Enter choice (1-5): ").strip()
        
        if choice == '1':
            demo_universal_intelligence()
        elif choice == '2':
            demo_intelligent_tools()
        elif choice == '3':
            show_architecture()
        elif choice == '4':
            show_architecture()
            demo_universal_intelligence()
            demo_intelligent_tools()
        elif choice == '5':
            console.print("\n[yellow]👋 Goodbye![/yellow]\n")
            return
        else:
            console.print("\n[red]Invalid choice. Please enter 1-5.[/red]\n")
            return main()
        
        # Ask if want to run another
        console.print("\n[cyan]Run another demo? (y/n): [/cyan]", end='')
        again = input().strip().lower()
        if again == 'y':
            main()
        else:
            console.print("\n[yellow]👋 Goodbye![/yellow]\n")
    
    except KeyboardInterrupt:
        console.print("\n\n[yellow]👋 Goodbye![/yellow]\n")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
