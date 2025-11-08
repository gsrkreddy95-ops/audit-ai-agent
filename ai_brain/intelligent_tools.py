"""
Intelligent File Export Tool
Uses Universal Intelligence to adapt to any file format dynamically
No more hardcoded CSV/PDF logic - the LLM decides how to parse and extract!
"""

import os
import json
from typing import Dict, List, Optional, Any
from pathlib import Path
from rich.console import Console
import pandas as pd

console = Console()


class IntelligentFileExporter:
    """
    Smart file export that asks the brain for help:
    - "What format is this file?" 
    - "How should I parse it?"
    - "What data should I extract?"
    - "This failed, what should I try?"
    """
    
    def __init__(self, intelligence):
        """
        Args:
            intelligence: UniversalIntelligence instance
        """
        self.intelligence = intelligence
        self.supported_formats = ['csv', 'json', 'xlsx', 'xls', 'pdf', 'txt', 'log']
    
    def export_file(self, 
                   file_path: str,
                   output_format: str = 'csv',
                   extraction_goal: Optional[str] = None) -> str:
        """
        Intelligently export file to desired format
        
        Args:
            file_path: Source file
            output_format: Desired output (csv, json, xlsx)
            extraction_goal: What data to extract (e.g., "audit trail timestamps")
        
        Returns:
            Path to exported file
        """
        try:
            console.print(f"\n[cyan]📄 Intelligent File Export[/cyan]")
            console.print(f"[dim]  Source: {file_path}[/dim]")
            console.print(f"[dim]  Target: {output_format}[/dim]")
            
            if not Path(file_path).exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            # Step 1: Ask brain to detect format
            console.print("[cyan]🧠 Asking brain: What format is this file?[/cyan]")
            format_info = self.intelligence.detect_file_format(file_path)
            
            console.print(f"[green]✓ Detected: {format_info.get('answer', 'unknown')}[/green]")
            console.print(f"[dim]  Confidence: {format_info.get('confidence', 0)}%[/dim]")
            
            # Step 2: Ask brain for extraction strategy
            console.print("[cyan]🧠 Asking brain: How should I extract data?[/cyan]")
            strategy = self.intelligence.suggest_extraction_strategy(
                file_info=format_info,
                purpose=extraction_goal or "General export"
            )
            
            console.print(f"[green]✓ Strategy: {strategy.get('answer', 'See actions')}[/green]")
            
            # Step 3: Execute extraction with intelligence guidance
            data = self._extract_with_intelligence(file_path, format_info, strategy)
            
            # Step 4: Validate output
            console.print("[cyan]🧠 Asking brain: Is the extracted data valid?[/cyan]")
            validation = self.intelligence.validate_output(
                tool_name="file_exporter",
                output_data=data
            )
            
            if not validation.get('is_valid', True):
                console.print(f"[yellow]⚠️  Validation issues: {validation.get('issues')}[/yellow]")
                console.print(f"[yellow]💡 Recommendations: {validation.get('recommendations')}[/yellow]")
            
            # Step 5: Export to desired format
            output_path = self._export_data(data, output_format, file_path)
            
            console.print(f"[green]✅ Exported to: {output_path}[/green]")
            return output_path
            
        except Exception as e:
            console.print(f"[red]❌ Export failed: {e}[/red]")
            
            # Ask brain for recovery
            recovery = self.intelligence.handle_tool_error(
                tool_name="file_exporter",
                error=e,
                attempted_action=f"Export {file_path} to {output_format}",
                context={"file": file_path, "format": output_format}
            )
            
            console.print(f"[cyan]🧠 Brain recovery suggestion: {recovery.get('recovery_action')}[/cyan]")
            console.print(f"[dim]  Reasoning: {recovery.get('reasoning')}[/dim]")
            
            # Try fallback if suggested
            if recovery.get('recovery_action') == 'retry' and recovery.get('retry_with_changes'):
                console.print("[cyan]🔄 Retrying with brain-suggested changes...[/cyan]")
                # Implement retry logic here
            
            raise
    
    def _extract_with_intelligence(self, 
                                   file_path: str,
                                   format_info: Dict,
                                   strategy: Dict) -> Any:
        """Execute extraction based on brain's strategy"""
        actions = strategy.get('actions', [])
        
        for action in actions:
            console.print(f"[dim]  Executing: {action}[/dim]")
        
        # Parse based on detected format
        detected_format = format_info.get('answer', '').lower()
        
        if 'csv' in detected_format:
            return self._extract_csv(file_path, strategy)
        elif 'json' in detected_format:
            return self._extract_json(file_path, strategy)
        elif 'excel' in detected_format or 'xlsx' in detected_format:
            return self._extract_excel(file_path, strategy)
        elif 'pdf' in detected_format:
            return self._extract_pdf(file_path, strategy)
        else:
            # Ask brain what to do
            console.print("[yellow]⚠️  Unknown format, asking brain for help...[/yellow]")
            next_action = self.intelligence.decide_next_action(
                tool_name="file_exporter",
                current_state={"file": file_path, "detected": detected_format},
                goal="Extract data from unknown format"
            )
            console.print(f"[cyan]🧠 Brain says: {next_action.get('next_action')}[/cyan]")
            # Implement dynamic action execution
            return {"raw_content": Path(file_path).read_text()}
    
    def _extract_csv(self, file_path: str, strategy: Dict) -> pd.DataFrame:
        """Extract CSV with intelligence-guided parameters"""
        params = strategy.get('parameters', {})
        
        try:
            df = pd.read_csv(
                file_path,
                sep=params.get('sep', ','),
                header=0 if params.get('has_header', True) else None,
                encoding=params.get('encoding', 'utf-8')
            )
            
            # Filter columns if brain suggested specific ones
            if 'columns_to_extract' in strategy:
                columns = strategy['columns_to_extract']
                df = df[[c for c in columns if c in df.columns]]
            
            return df
        except Exception as e:
            console.print(f"[yellow]⚠️  CSV read failed: {e}[/yellow]")
            # Try alternate encoding
            console.print("[cyan]🧠 Trying alternate approach...[/cyan]")
            return pd.read_csv(file_path, encoding='latin-1')
    
    def _extract_json(self, file_path: str, strategy: Dict) -> Any:
        """Extract JSON with intelligence"""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Extract specific keys if brain suggested
        if 'keys_to_extract' in strategy:
            keys = strategy['keys_to_extract']
            if isinstance(data, dict):
                data = {k: v for k, v in data.items() if k in keys}
        
        return data
    
    def _extract_excel(self, file_path: str, strategy: Dict) -> pd.DataFrame:
        """Extract Excel with intelligence"""
        params = strategy.get('parameters', {})
        
        return pd.read_excel(
            file_path,
            sheet_name=params.get('sheet_name', 0),
            header=0 if params.get('has_header', True) else None
        )
    
    def _extract_pdf(self, file_path: str, strategy: Dict) -> Dict:
        """Extract PDF with intelligence"""
        try:
            import PyPDF2
            
            with open(file_path, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                text = ""
                for page in reader.pages:
                    text += page.extract_text() + "\n\n"
            
            return {"text": text, "pages": len(reader.pages)}
        except ImportError:
            console.print("[yellow]⚠️  PyPDF2 not installed, using fallback[/yellow]")
            return {"text": "PDF extraction requires PyPDF2", "pages": 0}
    
    def _export_data(self, data: Any, output_format: str, source_path: str) -> str:
        """Export data to desired format"""
        base_name = Path(source_path).stem
        output_dir = Path(source_path).parent
        
        if output_format == 'csv':
            output_path = output_dir / f"{base_name}_exported.csv"
            if isinstance(data, pd.DataFrame):
                data.to_csv(output_path, index=False)
            elif isinstance(data, dict):
                pd.DataFrame([data]).to_csv(output_path, index=False)
            else:
                raise ValueError(f"Cannot export {type(data)} to CSV")
        
        elif output_format == 'json':
            output_path = output_dir / f"{base_name}_exported.json"
            if isinstance(data, pd.DataFrame):
                data.to_json(output_path, orient='records', indent=2)
            elif isinstance(data, dict):
                with open(output_path, 'w') as f:
                    json.dump(data, f, indent=2)
        
        elif output_format == 'xlsx':
            output_path = output_dir / f"{base_name}_exported.xlsx"
            if isinstance(data, pd.DataFrame):
                data.to_excel(output_path, index=False)
            elif isinstance(data, dict):
                pd.DataFrame([data]).to_excel(output_path, index=False)
        
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
        
        return str(output_path)


class IntelligentAWSCLI:
    """
    Intelligent AWS CLI wrapper that asks brain for help
    """
    
    def __init__(self, intelligence):
        self.intelligence = intelligence
    
    def execute_command(self, 
                       service: str,
                       action: str,
                       context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Execute AWS CLI with intelligence
        
        Args:
            service: AWS service (rds, s3, iam, etc.)
            action: What to do (list-clusters, describe-db-instances, etc.)
            context: Additional context (region, filters, etc.)
        
        Returns:
            Command output with intelligence-enhanced processing
        """
        console.print(f"\n[cyan]☁️  Intelligent AWS CLI[/cyan]")
        console.print(f"[dim]  Service: {service}, Action: {action}[/dim]")
        
        # Ask brain for optimal command
        console.print("[cyan]🧠 Asking brain: What's the best way to do this?[/cyan]")
        command_strategy = self.intelligence.ask(
            question=f"How should I execute AWS CLI for {service} {action}?",
            context={
                "service": service,
                "action": action,
                "context": context or {}
            },
            tool_name="aws_cli"
        )
        
        console.print(f"[green]✓ Strategy: {command_strategy.get('answer')}[/green]")
        
        # Execute with intelligence-suggested parameters
        # Implementation would go here
        
        return command_strategy


class IntelligentEvidenceCollector:
    """
    Evidence collector that asks brain what to collect
    """
    
    def __init__(self, intelligence):
        self.intelligence = intelligence
    
    def collect_for_rfi(self, rfi_code: str, previous_evidence: List[str]) -> Dict[str, Any]:
        """
        Intelligently collect evidence based on previous patterns
        
        Args:
            rfi_code: RFI requirement code
            previous_evidence: List of previous year's evidence files
        
        Returns:
            Collection plan with specific actions
        """
        console.print(f"\n[cyan]📋 Intelligent Evidence Collection for {rfi_code}[/cyan]")
        
        # Ask brain what evidence is needed
        console.print("[cyan]🧠 Analyzing previous evidence patterns...[/cyan]")
        requirements = self.intelligence.understand_evidence_context(
            evidence_files=previous_evidence,
            rfi_code=rfi_code
        )
        
        console.print(f"[green]✓ Evidence type: {requirements.get('answer')}[/green]")
        console.print(f"[dim]  Required content: {requirements.get('additional_context', {}).get('required_content')}[/dim]")
        console.print(f"[dim]  Collection method: {requirements.get('additional_context', {}).get('collection_method')}[/dim]")
        
        return requirements
