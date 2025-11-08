"""
SharePoint Evidence Learner
Downloads evidence from SharePoint, analyzes with Claude, creates collection templates
"""

import os
import json
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from integrations.sharepoint_browser import SharePointBrowserAccess
from evidence_manager.llm_evidence_analyzer import LLMEvidenceAnalyzer

console = Console()


class SharePointEvidenceLearner:
    """
    Learns from existing SharePoint evidence to understand what to collect
    """
    
    def __init__(self, llm, sharepoint_url: str = None):
        """
        Initialize learner
        
        Args:
            llm: LangChain LLM instance (Claude)
            sharepoint_url: Optional SharePoint folder URL to learn from
        """
        self.llm = llm
        self.analyzer = LLMEvidenceAnalyzer(llm)
        self.sharepoint_url = sharepoint_url or os.getenv('SHAREPOINT_EVIDENCE_URL')
        self.temp_download_dir = Path.home() / "Documents" / "audit-evidence" / "_learning_cache"
        self.temp_download_dir.mkdir(parents=True, exist_ok=True)
        
        # Knowledge base - stores what we learn
        self.knowledge_base_file = Path(__file__).parent / "evidence_knowledge_base.json"
        self.knowledge_base = self._load_knowledge_base()
    
    def learn_from_sharepoint_url(self, sharepoint_url: str, rfi_code: str = None) -> Dict:
        """
        Learn from a SharePoint folder URL
        
        Args:
            sharepoint_url: SharePoint folder URL (e.g., https://site.sharepoint.com/.../RFI-10.1.2.5)
            rfi_code: Optional RFI code to associate with this learning
        
        Returns:
            Learning summary with collection instructions
        """
        console.print(f"\n[bold cyan]🎓 Learning from SharePoint Evidence[/bold cyan]")
        console.print(f"[cyan]URL: {sharepoint_url}[/cyan]\n")
        
        try:
            # Decode HTML entities in URL (e.g., %26 or &amp; -> &)
            import html
            from urllib.parse import unquote
            sharepoint_url = html.unescape(unquote(sharepoint_url))
            
            # Browse SharePoint and list files
            console.print("[yellow]🌐 Connecting to SharePoint...[/yellow]")
            browser = SharePointBrowserAccess()
            
            # Connect to SharePoint
            if not browser.connect():
                return {"status": "error", "message": "Failed to connect to SharePoint"}
            
            # Navigate to URL
            console.print(f"[cyan]📂 Navigating to folder...[/cyan]")
            browser.page.goto(sharepoint_url, timeout=30000)
            time.sleep(3)
            
            # Get list of files
            files = browser.list_files_in_current_folder()

            # Filter out SharePoint UI artifact rows (row-selection-*) if any slipped through
            import re
            artifact_pat = re.compile(r'^row-selection(-header)?$|^row-selection-\d+$', re.I)
            original_count = len(files)
            files = [f for f in files if not artifact_pat.match(f.get('name',''))]
            removed = original_count - len(files)
            if removed > 0:
                console.print(f"[yellow]⚠️  Filtered out {removed} artifact rows (internal selection markers)" )
            
            if not files:
                console.print("[red]❌ No files found in SharePoint folder[/red]")
                return {"status": "error", "message": "No files found"}
            
            console.print(f"[green]✅ Found {len(files)} files[/green]\n")
            
            # Download files for analysis
            downloaded_files = []
            
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                task = progress.add_task(f"Downloading files...", total=len(files))
                
                for file_info in files:
                    if file_info['type'] == 'folder':
                        continue
                    
                    file_name = file_info['name']
                    local_path = self.temp_download_dir / file_name
                    
                    # Download file (pass direct URL if available for reliability)
                    success = browser.download_file(file_name, str(local_path), file_url=file_info.get('url'))
                    
                    if success:
                        downloaded_files.append({
                            'name': file_name,
                            'local_path': str(local_path),
                            'url': file_info.get('url', ''),
                            'modified': file_info.get('modified', '')
                        })
                    
                    progress.update(task, advance=1)
            
            browser.disconnect()
            
            console.print(f"[green]✅ Downloaded {len(downloaded_files)} files[/green]\n")
            
            # Analyze downloaded files with Claude
            console.print("[cyan]🧠 Analyzing with Claude...[/cyan]\n")
            
            analysis_results = []
            for file_info in downloaded_files:
                analysis = self.analyzer.analyze_file(
                    file_path=file_info['local_path'],
                    file_name=file_info['name']
                )
                analysis_results.append(analysis)
            
            # Generate overall summary
            console.print("\n[cyan]🧠 Generating collection plan...[/cyan]\n")
            collection_plan = self._generate_collection_plan(analysis_results, rfi_code)
            
            # Save to knowledge base
            self._save_to_knowledge_base(rfi_code, collection_plan, analysis_results)
            
            # Display summary
            self._display_learning_summary(collection_plan, analysis_results)
            
            return {
                "status": "success",
                "rfi_code": rfi_code,
                "files_analyzed": len(analysis_results),
                "collection_plan": collection_plan,
                "analysis_results": analysis_results
            }
            
        except Exception as e:
            console.print(f"[red]❌ Learning failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {"status": "error", "message": str(e)}
    
    def _generate_collection_plan(self, analysis_results: List[Dict], rfi_code: str) -> Dict:
        """
        Use Claude to generate an overall collection plan based on all analyzed files
        """
        
        # Prepare summary for Claude
        files_summary = []
        for analysis in analysis_results:
            files_summary.append({
                'file_name': analysis['file_name'],
                'evidence_type': analysis['evidence_type'],
                'source': analysis['source'],
                'details': analysis['details'],
                'collection_method': analysis['collection_method']
            })
        
        prompt = f"""You are creating an evidence collection plan for RFI {rfi_code or 'Unknown'} based on analysis of previous year's evidence.

**ANALYZED FILES:**
{json.dumps(files_summary, indent=2)}

Please create a comprehensive collection plan that includes:

1. **Overview**: Brief summary of what evidence is needed
2. **Evidence Types**: Break down by type (screenshots, exports, documents)
3. **AWS Services**: List all AWS services involved
4. **Step-by-Step Collection Tasks**: Detailed tasks in order of execution
5. **Automation Opportunities**: What can be automated vs manual
6. **Estimated Time**: Time to collect all evidence
7. **Prerequisites**: What access/permissions needed

Format as JSON:
{{
  "overview": "Brief summary...",
  "evidence_types": {{
    "screenshots": 12,
    "data_exports": 5,
    "documents": 2
  }},
  "aws_services": ["RDS", "S3", "IAM"],
  "collection_tasks": [
    {{
      "task_id": 1,
      "description": "Capture RDS cluster configuration screenshots",
      "evidence_type": "screenshot",
      "aws_service": "RDS",
      "automation": "automated",
      "instructions": "Detailed steps...",
      "expected_files": ["rds_cluster_config.png", "rds_backups.png"]
    }}
  ],
  "automation_summary": {{
    "automated": 15,
    "manual": 4
  }},
  "estimated_time_minutes": 20,
  "prerequisites": ["AWS Console access", "us-east-1 region access"]
}}
"""
        
        try:
            response = self.llm.invoke(prompt)
            response_text = response.content if hasattr(response, 'content') else str(response)
            
            # Extract JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                plan = json.loads(json_match.group())
                return plan
            else:
                return {"error": "Failed to parse Claude's response"}
                
        except Exception as e:
            console.print(f"[yellow]⚠️ Collection plan generation failed: {e}[/yellow]")
            return {
                "overview": f"Collection plan for {len(analysis_results)} files",
                "error": str(e)
            }
    
    def _save_to_knowledge_base(self, rfi_code: str, collection_plan: Dict, analysis_results: List[Dict]):
        """Save learning to knowledge base for future use"""
        
        if rfi_code:
            self.knowledge_base[rfi_code] = {
                "learned_at": datetime.now().isoformat(),
                "files_analyzed": len(analysis_results),
                "collection_plan": collection_plan,
                "analysis_summary": analysis_results
            }
            
            # Save to file
            with open(self.knowledge_base_file, 'w') as f:
                json.dump(self.knowledge_base, f, indent=2)
            
            console.print(f"[green]💾 Saved to knowledge base: {rfi_code}[/green]")
    
    def _load_knowledge_base(self) -> Dict:
        """Load existing knowledge base"""
        if self.knowledge_base_file.exists():
            with open(self.knowledge_base_file, 'r') as f:
                return json.load(f)
        return {}
    
    def get_collection_plan_for_rfi(self, rfi_code: str) -> Optional[Dict]:
        """
        Retrieve learned collection plan for an RFI
        
        Args:
            rfi_code: RFI code to look up
        
        Returns:
            Collection plan or None if not found
        """
        if rfi_code in self.knowledge_base:
            return self.knowledge_base[rfi_code]['collection_plan']
        return None
    
    def _display_learning_summary(self, collection_plan: Dict, analysis_results: List[Dict]):
        """Display learning summary in rich format"""
        
        console.print("\n" + "="*80)
        console.print("[bold green]📚 LEARNING SUMMARY[/bold green]")
        console.print("="*80 + "\n")
        
        # Overview
        if 'overview' in collection_plan:
            console.print(f"[bold]Overview:[/bold]")
            console.print(f"{collection_plan['overview']}\n")
        
        # Evidence breakdown
        if 'evidence_types' in collection_plan:
            console.print(f"[bold]Evidence Types:[/bold]")
            for etype, count in collection_plan['evidence_types'].items():
                console.print(f"  • {etype}: {count} files")
            console.print()
        
        # AWS Services
        if 'aws_services' in collection_plan:
            console.print(f"[bold]AWS Services:[/bold]")
            console.print(f"  {', '.join(collection_plan['aws_services'])}\n")
        
        # Collection tasks
        if 'collection_tasks' in collection_plan:
            console.print(f"[bold]Collection Tasks:[/bold]")
            
            table = Table(title="Evidence Collection Tasks")
            table.add_column("#", style="cyan", width=5)
            table.add_column("Task", style="white", width=40)
            table.add_column("Service", style="yellow", width=10)
            table.add_column("Type", style="green", width=12)
            table.add_column("Auto", style="magenta", width=8)
            
            for task in collection_plan['collection_tasks']:
                table.add_row(
                    str(task.get('task_id', '?')),
                    task.get('description', '')[:40],
                    task.get('aws_service', ''),
                    task.get('evidence_type', ''),
                    "✅" if task.get('automation') == 'automated' else "👤"
                )
            
            console.print(table)
            console.print()
        
        # Automation summary
        if 'automation_summary' in collection_plan:
            auto = collection_plan['automation_summary']
            console.print(f"[bold]Automation:[/bold]")
            console.print(f"  ✅ Automated: {auto.get('automated', 0)}")
            console.print(f"  👤 Manual: {auto.get('manual', 0)}\n")
        
        # Time estimate
        if 'estimated_time_minutes' in collection_plan:
            time_min = collection_plan['estimated_time_minutes']
            console.print(f"[bold]Estimated Time:[/bold] {time_min} minutes\n")
        
        console.print("="*80 + "\n")
    
    def list_learned_rfis(self):
        """Display all RFIs in knowledge base"""
        if not self.knowledge_base:
            console.print("[yellow]📚 Knowledge base is empty. Learn from SharePoint first![/yellow]")
            return
        
        console.print("\n[bold cyan]📚 Knowledge Base[/bold cyan]\n")
        
        table = Table(title="Learned RFIs")
        table.add_column("RFI Code", style="cyan")
        table.add_column("Files Analyzed", style="yellow")
        table.add_column("Tasks", style="green")
        table.add_column("Learned At", style="dim")
        
        for rfi_code, data in self.knowledge_base.items():
            plan = data.get('collection_plan', {})
            tasks = len(plan.get('collection_tasks', []))
            
            table.add_row(
                rfi_code,
                str(data.get('files_analyzed', 0)),
                str(tasks),
                data.get('learned_at', '')[:10]
            )
        
        console.print(table)
        console.print()


# Example usage
if __name__ == "__main__":
    from ai_brain.llm_config import LLMFactory
    
    console.print("[bold cyan]🎓 SharePoint Evidence Learner Test[/bold cyan]\n")
    
    # Initialize LLM
    llm = LLMFactory.create_llm()
    
    # Create learner
    learner = SharePointEvidenceLearner(llm)
    
    # Example: Learn from SharePoint URL
    # sharepoint_url = "https://yourcompany.sharepoint.com/sites/audit/Shared%20Documents/FY2025/10.1.2.5"
    # result = learner.learn_from_sharepoint_url(sharepoint_url, rfi_code="10.1.2.5")
    
    # Show what we've learned
    learner.list_learned_rfis()
