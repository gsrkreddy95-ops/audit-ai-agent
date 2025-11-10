"""
Tool Executor - Executes tools that Claude decides to call
"""

import os
import time  # ← SELF-HEAL FIX: Added for time.sleep() calls
from dataclasses import asdict
from typing import Dict, Any
from datetime import datetime
from rich.console import Console
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from integrations.sharepoint_browser import SharePointBrowserAccess
from evidence_manager.local_evidence_manager import LocalEvidenceManager
from evidence_manager.evidence_analyzer_v2 import EvidenceAnalyzerV2
from evidence_manager.llm_evidence_analyzer import LLMEvidenceAnalyzer
from evidence_manager.sharepoint_evidence_learner import SharePointEvidenceLearner
from evidence_manager.document_intelligence import DocumentIntelligence
from tools.universal_screenshot_enhanced import UniversalScreenshotEnhanced, ClickStrategy
from tools.rds_navigator_enhanced import RDSNavigatorEnhanced
from ai_brain.browser_session_manager import BrowserSessionManager  # ← ADDED FOR aws_console_action
from tools.aws_export_tool import export_aws_data
from tools.aws_list_tool import (
    list_s3_buckets, list_rds_instances, list_rds_clusters,
    list_iam_users, list_ec2_instances, list_lambda_functions, list_vpc_resources
)
from tools.sharepoint_upload_tool import upload_to_sharepoint, batch_upload_from_rfi_folder
from ai_brain.universal_intelligence import UniversalIntelligence
from ai_brain.intelligent_tools import IntelligentFileExporter, IntelligentAWSCLI, IntelligentEvidenceCollector
from ai_brain.orchestrator import AIOrchestrator

console = Console()


class ToolExecutor:
    """
    Executes tools that the LLM (Claude) decides to call
    NOW WITH AI ORCHESTRATOR - brain directs ALL tools from the start!
    
    Architecture:
    1. Brain analyzes previous evidence (from SharePoint)
    2. Brain creates detailed execution plan
    3. Brain monitors and directs tool execution
    4. Tools execute brain's commands (not decide themselves)
    """
    def __init__(self, evidence_manager: LocalEvidenceManager, llm=None):
        self.evidence_manager = evidence_manager
        self.sharepoint = None
        self.llm = llm
        self.document_intelligence = DocumentIntelligence(llm)
        # Reusable AWS browser session (UniversalScreenshotEnhanced) for non-RDS services
        self._aws_universal_session = None
        self._aws_session_account = None
        self._aws_session_region = None
        
        # Initialize Universal Intelligence Hub
        if llm:
            console.print("[cyan]🧠 Initializing AI Brain Orchestrator...[/cyan]")
            self.intelligence = UniversalIntelligence(llm)
            console.print("[green]✅ Universal Intelligence active - ALL tools can query the brain![/green]")
            
            # Initialize AI Orchestrator - the brain that directs everything
            self.orchestrator = AIOrchestrator(
                llm,
                evidence_manager,
                self,
                document_intelligence=self.document_intelligence,
            )
            console.print("[green]✅ AI Orchestrator active - brain will analyze evidence and direct tools![/green]")
            
            # Initialize intelligent tool wrappers
            self.file_exporter = IntelligentFileExporter(self.intelligence)
            self.aws_cli = IntelligentAWSCLI(self.intelligence)
            self.evidence_collector = IntelligentEvidenceCollector(self.intelligence)
            
            # Use LLM-powered analyzer
            console.print("[cyan]✅ Using LLM-powered evidence analyzer (Claude)[/cyan]")
            self.analyzer = LLMEvidenceAnalyzer(llm)
            self.learner = SharePointEvidenceLearner(llm)
        else:
            console.print("[yellow]⚠️  No LLM configured - tools will use fallback logic[/yellow]")
            self.intelligence = None
            self.orchestrator = None
            self.file_exporter = None
            self.aws_cli = None
            self.evidence_collector = None
            self.analyzer = EvidenceAnalyzerV2()
            self.learner = None
    
    def execute_tool(self, tool_name: str, tool_input: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a tool and return results
        
        Args:
            tool_name: Name of tool to execute
            tool_input: Parameters for the tool
        
        Returns:
            Dict with 'status' and 'result' or 'error'
        """
        
        console.print(f"\n[cyan]🔧 Executing: {tool_name}[/cyan]")
        
        try:
            if tool_name == "sharepoint_review_evidence":
                return self._execute_sharepoint_review(tool_input)
            
            elif tool_name == "aws_console_action":
                return self._execute_aws_console_action(tool_input)
            
            elif tool_name == "aws_navigate":
                # Legacy support - redirect to aws_console_action with capture_screenshot=false
                tool_input["capture_screenshot"] = False
                return self._execute_aws_console_action(tool_input)
            
            elif tool_name == "aws_take_screenshot":
                # Legacy support - redirect to aws_console_action with capture_screenshot=true
                tool_input["capture_screenshot"] = True
                return self._execute_aws_console_action(tool_input)
            
            elif tool_name == "aws_export_data":
                return self._execute_aws_export(tool_input)
            
            elif tool_name == "list_aws_resources":
                return self._execute_list_aws(tool_input)
            
            elif tool_name == "show_local_evidence":
                return self._execute_show_evidence(tool_input)
            
            elif tool_name == "upload_to_sharepoint":
                return self._execute_upload(tool_input)

            elif tool_name == "learn_from_sharepoint_url":
                return self._execute_learn_from_sharepoint(tool_input)

            elif tool_name == "analyze_document_evidence":
                return self._execute_analyze_document_evidence(tool_input)

            # Self-healing/debugging tools
            elif tool_name == "read_tool_source":
                return self._execute_read_tool_source(tool_input)
            
            elif tool_name == "diagnose_error":
                return self._execute_diagnose_error(tool_input)
            
            elif tool_name == "fix_tool_code":
                return self._execute_fix_tool_code(tool_input)
            
            elif tool_name == "test_tool":
                return self._execute_test_tool(tool_input)
            
            elif tool_name == "get_browser_screenshot":
                return self._execute_browser_screenshot(tool_input)
            
            # Code generation tools
            elif tool_name == "generate_new_tool":
                return self._execute_generate_tool(tool_input)
            
            elif tool_name == "add_functionality_to_tool":
                return self._execute_add_functionality(tool_input)
            
            elif tool_name == "implement_missing_function":
                return self._execute_implement_function(tool_input)
            
            elif tool_name == "search_implementation_examples":
                return self._execute_search_examples(tool_input)
            
            # NEW: Intelligent tool methods
            elif tool_name == "intelligent_file_export":
                return self._execute_intelligent_export(tool_input)
            
            elif tool_name == "intelligent_aws_cli":
                return self._execute_intelligent_aws_cli(tool_input)
            
            elif tool_name == "intelligent_evidence_collection":
                return self._execute_intelligent_evidence_collection(tool_input)
            
            # NEW: Orchestrator methods - brain directs from the start
            elif tool_name == "orchestrator_analyze_and_plan":
                return self._execute_orchestrator_analyze(tool_input)
            
            elif tool_name == "orchestrator_execute_plan":
                return self._execute_orchestrator_execute(tool_input)
            
            # REVOLUTIONARY: Dynamic code execution - Claude writes code on the fly!
            elif tool_name == "execute_python_code":
                return self._execute_python_code(tool_input)
            
            elif tool_name == "analyze_past_evidence":
                return self._execute_analyze_past_evidence(tool_input)
            
            # === JIRA INTEGRATION TOOLS ===
            elif tool_name == "jira_list_tickets":
                return self._execute_jira_list_tickets(tool_input)
            
            elif tool_name == "jira_search_jql":
                return self._execute_jira_search_jql(tool_input)
            
            elif tool_name == "jira_get_ticket":
                return self._execute_jira_get_ticket(tool_input)
            
            # === CONFLUENCE INTEGRATION TOOLS ===
            elif tool_name == "confluence_search":
                return self._execute_confluence_search(tool_input)
            
            elif tool_name == "confluence_get_page":
                return self._execute_confluence_get_page(tool_input)
            
            elif tool_name == "confluence_list_space":
                return self._execute_confluence_list_space(tool_input)
            
            # === GITHUB INTEGRATION TOOLS ===
            elif tool_name == "github_list_prs":
                return self._execute_github_list_prs(tool_input)
            
            elif tool_name == "github_get_pr":
                return self._execute_github_get_pr(tool_input)
            
            elif tool_name == "github_search_code":
                return self._execute_github_search_code(tool_input)
            
            elif tool_name == "github_list_issues":
                return self._execute_github_list_issues(tool_input)
            
            else:
                return {
                    "status": "error",
                    "error": f"Unknown tool: {tool_name}"
                }
        
        except Exception as e:
            console.print(f"[red]❌ Tool execution failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _execute_sharepoint_review(self, params: Dict) -> Dict:
        """Execute SharePoint evidence review"""
        rfi_code = params.get('rfi_code')
        product = params.get('product', '')
        year = params.get('year', 'FY2024')
        
        if not rfi_code:
            return {"status": "error", "error": "Missing rfi_code parameter"}
        
        console.print(f"[cyan]📂 Reviewing {year} evidence for RFI {rfi_code}...[/cyan]")
        
        try:
            # Initialize SharePoint if needed
            if not self.sharepoint:
                console.print("[yellow]💡 Opening SharePoint with Playwright...[/yellow]")
                self.sharepoint = SharePointBrowserAccess(headless=False)
                if not self.sharepoint.connect():
                    return {"status": "error", "error": "Failed to connect to SharePoint"}
            
            # Build path
            base_path = os.getenv('SHAREPOINT_BASE_PATH', 'TD&R Documentation Train 5/TD&R Evidence Collection')
            if product:
                folder_path = f"{base_path}/{year}/{product}/{rfi_code}"
            else:
                folder_path = f"{base_path}/{year}/{rfi_code}"
            
            # Navigate and list files
            if self.sharepoint.navigate_to_path(folder_path):
                files = self.sharepoint.list_folder_contents()
                
                if not files:
                    return {
                        "status": "success",
                        "result": {
                            "found": False,
                            "message": f"RFI folder exists but is empty: {folder_path}",
                            "recommendation": "No previous evidence found. You should collect new evidence for this RFI."
                        }
                    }
                
                # Download files to temp directory for analysis
                import tempfile
                temp_dir = tempfile.mkdtemp(prefix=f"sharepoint_{rfi_code}_")
                console.print(f"[cyan]📥 Downloading files for analysis...[/cyan]")
                
                downloaded_files = self.sharepoint.download_all_files(temp_dir)
                
                if not downloaded_files or not any(f['success'] for f in downloaded_files):
                    return {
                        "status": "error",
                        "error": "Failed to download files from SharePoint"
                    }
                
                # Analyze actual file contents
                console.print(f"[cyan]🧠 Analyzing file contents...[/cyan]")
                
                # Prepare file list with local paths for analyzer
                files_for_analysis = []
                for file_info in downloaded_files:
                    if file_info['success'] and file_info['local_path']:
                        files_for_analysis.append({
                            'name': file_info['name'],
                            'local_path': file_info['local_path'],
                            'type': 'file'
                        })
                
                analysis = self.analyzer.analyze_rfi_folder(files_for_analysis)
                
                # Create local folder
                local_dir = self.evidence_manager.get_rfi_directory(rfi_code)
                
                # Clean up temp directory after analysis
                import shutil
                try:
                    shutil.rmtree(temp_dir)
                except:
                    pass  # Ignore cleanup errors
                
                return {
                    "status": "success",
                    "result": {
                        "found": True,
                        "file_count": len(files),
                        "files": [f['name'] for f in files],
                        "analysis": {
                            "total_files": analysis['total_files'],
                            "by_type": analysis['by_type'],
                            "aws_console_tasks": sum(1 for t in analysis['collection_tasks'] if t['analysis']['source'] == 'aws_console'),
                            "aws_api_tasks": sum(1 for t in analysis['collection_tasks'] if t['analysis']['source'] == 'aws_api'),
                            "manual_tasks": sum(1 for t in analysis['collection_tasks'] if t['analysis']['source'] == 'manual'),
                            "collection_plan": [
                                {
                                    "file": t['file_name'],
                                    "source": t['analysis']['source'],
                                    "instructions": t['analysis']['instructions']
                                }
                                for t in analysis['collection_tasks'][:5]  # First 5 for summary
                            ]
                        },
                        "local_folder": str(local_dir),
                        "summary": f"Found {len(files)} files from {year}/{product or ''}/{rfi_code}"
                    }
                }
            else:
                # Navigation failed - folder doesn't exist or access denied
                local_dir = self.evidence_manager.get_rfi_directory(rfi_code)
                return {
                    "status": "success",
                    "result": {
                        "found": False,
                        "message": f"RFI folder not found: {rfi_code} in {year}/{product if product else '(root)'}",
                        "local_folder": str(local_dir),
                        "recommendation": "This RFI doesn't exist in the previous year or the folder structure is different. You should collect new evidence for this RFI without referencing previous years.",
                        "note": "No 404 error shown - handled gracefully"
                    }
                }
        
        except Exception as e:
            return {"status": "error", "error": f"SharePoint review failed: {str(e)}"}
    
    def _execute_aws_console_action(self, params: Dict) -> Dict:
        """
        🎯 UNIVERSAL AWS CONSOLE TOOL
        
        Handles:
        1. Navigation only (capture_screenshot=false)
        2. Navigation + Screenshot (capture_screenshot=true)
        3. Navigation + Export (export_format set)
        """
        # Check what action is requested
        capture_screenshot = params.get("capture_screenshot", False)
        export_format = params.get("export_format", "")
        
        if capture_screenshot:
            console.print("\n[bold cyan]📸 AWS Console Action: NAVIGATE + SCREENSHOT[/bold cyan]")
        elif export_format:
            console.print(f"\n[bold cyan]📊 AWS Console Action: NAVIGATE + EXPORT ({export_format.upper()})[/bold cyan]")
        else:
            console.print("\n[bold cyan]🧭 AWS Console Action: NAVIGATE ONLY[/bold cyan]")
        
        service = params.get("service", "").lower()
        account = params.get("aws_account")
        region = params.get("aws_region")
        section_name = params.get("section_name")
        
        console.print(f"   Service: {service.upper()}")
        console.print(f"   Account: {account}")
        console.print(f"   Region: {region}")
        if section_name:
            console.print(f"   Section: {section_name}")
        
        try:
            # Authenticate to AWS account using BrowserSessionManager
            # Note: authenticate_aws takes region as second parameter
            if not BrowserSessionManager.authenticate_aws(account, region):
                return {
                    "status": "error",
                    "error": f"Failed to authenticate to AWS account: {account}"
                }
            
            # Check current region and change if needed
            # Note: _current_region is a private class variable, but we can access it
            current_region = BrowserSessionManager._current_region
            if current_region and current_region != region:
                console.print(f"[cyan]🌍 Switching region: {current_region} → {region}[/cyan]")
                if not BrowserSessionManager.change_region(region):
                    console.print(f"[yellow]⚠️  Region switch may have failed, continuing...[/yellow]")
            
            # Get universal navigator
            universal_nav = BrowserSessionManager.get_universal_navigator()
            if not universal_nav:
                return {
                    "status": "error",
                    "error": "Failed to get universal navigator"
                }
            
            # Special case: If service is "console", "home", or "aws", skip navigation (already on console)
            skip_navigation = service in ["console", "home", "aws", "aws-console", ""]
            
            if skip_navigation:
                console.print(f"\n[green]✅ Already on AWS Console home page[/green]")
                console.print(f"[dim]   (No specific service navigation needed)[/dim]")
            else:
                # Navigate to service
                console.print(f"\n[cyan]🚀 Navigating to {service.upper()}...[/cyan]")
                if not universal_nav.navigate_to_service(service, use_search=True):
                    return {
                        "status": "error",
                        "error": f"Failed to navigate to {service}"
                    }
                
                console.print(f"[green]✅ Navigated to {service.upper()}[/green]")
            
            # Navigate to section if specified
            if section_name:
                console.print(f"[cyan]🧭 Navigating to section: '{section_name}'...[/cyan]")
                section_success = universal_nav.navigate_to_section(
                    section_name=section_name
                )
                
                if section_success:
                    console.print(f"[green]✅ Navigated to section: {section_name}[/green]")
                else:
                    console.print(f"[yellow]⚠️  Failed to navigate to section '{section_name}'[/yellow]")
            
            # Get current URL from browser
            browser = BrowserSessionManager.get_browser()
            current_url = browser.driver.current_url if browser else "Unknown"
            
            # Now decide what action to take
            if export_format:
                # TODO: Implement export logic
                console.print(f"\n[yellow]⚠️  Export feature coming soon![/yellow]")
                console.print(f"[yellow]   For now, use aws_export_data tool for API-based exports[/yellow]")
                return {
                    "status": "partial_success",
                    "message": f"Navigated to {service.upper()}, but export not yet implemented",
                    "current_url": current_url,
                    "service": service,
                    "account": account,
                    "region": region
                }
            
            elif capture_screenshot:
                # Capture screenshot
                console.print(f"\n[bold cyan]📸 Capturing screenshot...[/bold cyan]")
                
                # Delegate to existing screenshot logic
                return self._execute_aws_screenshot(params)
            
            else:
                # Navigation only - just confirm and return
                console.print(f"\n[bold green]✅ NAVIGATION COMPLETE![/bold green]")
                console.print(f"[green]   Current URL: {current_url}[/green]")
                console.print(f"[green]   Browser remains open for further commands[/green]\n")
                
                return {
                    "status": "success",
                    "message": f"Successfully navigated to {service.upper()} in {account} ({region})",
                    "current_url": current_url,
                    "service": service,
                    "account": account,
                    "region": region,
                    "section": section_name,
                    "browser_open": True,
                    "action": "navigate_only"
                }
            
        except Exception as e:
            console.print(f"[red]❌ Console action failed: {e}[/red]")
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
            return {
                "status": "error",
                "error": f"Console action failed: {str(e)}"
            }
    
    def _execute_aws_navigate(self, params: Dict) -> Dict:
        """
        🧭 Navigate to AWS Console WITHOUT capturing screenshot
        
        This is used when user just wants to browse/navigate, not capture evidence.
        """
        console.print("\n[bold cyan]🧭 Navigating to AWS Console...[/bold cyan]")
        
        service = params.get("service", "").lower()
        account = params.get("aws_account")
        region = params.get("aws_region")
        section_name = params.get("section_name")
        
        console.print(f"   Service: {service.upper()}")
        console.print(f"   Account: {account}")
        console.print(f"   Region: {region}")
        if section_name:
            console.print(f"   Section: {section_name}")
        
        try:
            # Get browser session
            browser = BrowserSessionManager.get_browser()
            if not browser:
                return {
                    "status": "error",
                    "error": "Failed to initialize browser session"
                }
            
            # Authenticate to AWS
            if not browser.authenticate_aws(account):
                return {
                    "status": "error",
                    "error": f"Failed to authenticate to AWS account: {account}"
                }
            
            # Change region if needed
            current_region = browser.get_current_region()
            if current_region != region:
                console.print(f"[cyan]🌍 Switching region: {current_region} → {region}[/cyan]")
                if not browser.change_region(region):
                    console.print(f"[yellow]⚠️  Region switch may have failed, continuing...[/yellow]")
            
            # Get universal navigator
            universal_nav = BrowserSessionManager.get_universal_navigator()
            if not universal_nav:
                return {
                    "status": "error",
                    "error": "Failed to get universal navigator"
                }
            
            # Navigate to service
            console.print(f"\n[cyan]🚀 Navigating to {service.upper()}...[/cyan]")
            if not universal_nav.navigate_to_service(service, use_search=True):
                return {
                    "status": "error",
                    "error": f"Failed to navigate to {service}"
                }
            
            console.print(f"[green]✅ Navigated to {service.upper()}[/green]")
            
            # Navigate to section if specified
            if section_name:
                console.print(f"[cyan]🧭 Navigating to section: '{section_name}'...[/cyan]")
                section_success = universal_nav.navigate_to_section(
                    section_name=section_name
                )
                
                if section_success:
                    console.print(f"[green]✅ Navigated to section: {section_name}[/green]")
                else:
                    console.print(f"[yellow]⚠️  Failed to navigate to section '{section_name}'[/yellow]")
            
            # Get current URL
            current_url = browser.driver.current_url
            
            # Success!
            console.print(f"\n[bold green]✅ NAVIGATION COMPLETE![/bold green]")
            console.print(f"[green]   Current URL: {current_url}[/green]")
            console.print(f"[green]   Browser remains open for further commands[/green]\n")
            
            return {
                "status": "success",
                "message": f"Successfully navigated to {service.upper()} in {account} ({region})",
                "current_url": current_url,
                "service": service,
                "account": account,
                "region": region,
                "section": section_name,
                "browser_open": True
            }
            
        except Exception as e:
            console.print(f"[red]❌ Navigation failed: {e}[/red]")
            return {
                "status": "error",
                "error": f"Navigation failed: {str(e)}"
            }
    
    def _execute_aws_screenshot(self, params: Dict) -> Dict:
        """
        Execute AWS screenshot capture using PERSISTENT browser session.
        
        NOW USES BROWSER SESSION MANAGER:
        - ONE browser for all screenshots (no multiple Duo auths!)
        - Smart navigation using AWS Console search
        - Browser back/forward buttons
        - Reuses authenticated session
        """
        from ai_brain.browser_session_manager import BrowserSessionManager
        
        try:
            service = params.get('service')
            account = params.get('aws_account')
            region = params.get('aws_region')
            resource_name = params.get('resource_name', '')
            resource_type = params.get('resource_type', '')
            config_tab = params.get('config_tab', '')
            rfi_code = params.get('rfi_code', 'unknown')
            role_name = params.get('aws_role') or params.get('role_name')
            profile_name = params.get('aws_profile') or params.get('profile')
            
            # NEW: Section navigation parameters
            section_name = params.get('section_name', '')
            select_first_resource = params.get('select_first_resource', False)
            resource_index = params.get('resource_index', 0)
            capture_all_pages = params.get('capture_all_pages', False)  # 🔄 PAGINATION
            max_pages = params.get('max_pages', 50)  # 🔄 PAGINATION
            filter_by_date = params.get('filter_by_date', False)  # 📅 DATE FILTER
            audit_period = params.get('audit_period', '')  # 📅 DATE FILTER
            start_date = params.get('start_date', '')  # 📅 DATE FILTER
            end_date = params.get('end_date', '')  # 📅 DATE FILTER
            date_column = params.get('date_column', '')  # 📅 DATE FILTER
            
            # Decode HTML entities (e.g., &amp; -> &)
            if config_tab:
                import html
                config_tab = html.unescape(config_tab)
            
            if not all([service, account, region]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: service, aws_account, aws_region"
                }
            
            # Create output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            resource_part = f"_{resource_name}" if resource_name else f"_{resource_type}" if resource_type else ""
            filename = f"{service}{resource_part}_{region}_{timestamp}.png"
            
            # Get RFI directory
            rfi_dir = self.evidence_manager.get_rfi_directory(rfi_code)
            output_path = str(rfi_dir / filename)
            
            console.print(f"\n[cyan]📸 Taking AWS Console screenshot with intelligent agent...[/cyan]")
            console.print(f"[cyan]   Service: {service.upper()}[/cyan]")
            console.print(f"[cyan]   Account: {account}[/cyan]")
            console.print(f"[cyan]   Region: {region}[/cyan]")
            if resource_name:
                console.print(f"[cyan]   Resource: {resource_name}[/cyan]")
            if config_tab:
                console.print(f"[cyan]   Tab: {config_tab}[/cyan]")
            console.print(f"[cyan]   Output: {filename}[/cyan]")
            console.print(f"[cyan]   🔧 Using enhanced navigator with self-healing[/cyan]\n")
            
            # Use PERSISTENT browser session (NO MORE MULTIPLE BROWSER LAUNCHES!)
            navigator = None
            screenshot_path = None
            
            try:
                # Get or create persistent browser session
                browser = BrowserSessionManager.get_browser()
                if not browser:
                    return {
                        "status": "error",
                        "error": "Failed to get browser session"
                    }
                
                # Authenticate to AWS (only if not already authenticated)
                if not BrowserSessionManager.authenticate_aws(account=account, region=region):
                    return {
                        "status": "error",
                        "error": "Failed to authenticate to AWS"
                    }
                
                # Change region if needed
                if BrowserSessionManager._current_region != region:
                    BrowserSessionManager.change_region(region)
                
                # For RDS, use DIRECT URL navigation (much more reliable!)
                if service.lower() == 'rds':
                    console.print(f"[yellow]🚀 Using RDS Navigator Enhanced[/yellow]")
                    
                    # Pass the persistent browser to RDS navigator
                    navigator = RDSNavigatorEnhanced(browser)
                    
                    # Ensure correct region
                    try:
                        navigator.set_region(region)
                    except Exception:
                        pass
                    
                    # Navigate and capture
                    if resource_name:
                        # Capture specific cluster
                        screenshot_path = navigator.capture_cluster_screenshot(
                            cluster_name=resource_name,
                            tab=config_tab or 'Configuration'
                        )
                    else:
                        # Capture RDS overview
                        navigator.navigate_to_clusters_list()
                        screenshot_path = browser.capture_screenshot(
                            name=filename.replace('.png', '')
                        )
                else:
                    # For all other services, use DIRECT URL navigation
                    console.print(f"[cyan]📸 Capturing {service.upper()} screenshot (DIRECT URL NAVIGATION!)[/cyan]")
                    
                    # Build direct URL to service console
                    service_urls = {
                        's3': f'https://s3.console.aws.amazon.com/s3/buckets?region={region}',
                        'ec2': f'https://{region}.console.aws.amazon.com/ec2/home?region={region}#Instances:',
                        'lambda': f'https://{region}.console.aws.amazon.com/lambda/home?region={region}#/functions',
                        'iam': f'https://console.aws.amazon.com/iam/home#/users',
                        'cloudwatch': f'https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}',
                        'dynamodb': f'https://{region}.console.aws.amazon.com/dynamodbv2/home?region={region}#tables',
                        'sns': f'https://{region}.console.aws.amazon.com/sns/v3/home?region={region}#/topics',
                        'sqs': f'https://{region}.console.aws.amazon.com/sqs/v2/home?region={region}#/queues',
                    }
                    
                    service_url = service_urls.get(service.lower())
                    if service_url:
                        console.print(f"[cyan]🔗 Navigating directly to {service.upper()} console...[/cyan]")
                        browser.navigate_to_url(service_url)
                        time.sleep(3)  # Wait for page load
                    else:
                        # Use UNIVERSAL NAVIGATOR for ALL other services!
                        console.print(f"[yellow]🔍 Using Universal Navigator for {service.upper()}...[/yellow]")
                        universal_nav = BrowserSessionManager.get_universal_navigator()
                        if universal_nav:
                            # Navigate to service (works for ANY service!)
                            if not universal_nav.navigate_to_service(service, use_search=True):
                                console.print(f"[red]❌ Failed to navigate to {service}[/red]")
                                return {
                                    "status": "error",
                                    "error": f"Failed to navigate to {service}"
                                }
                            
                            # NEW: Navigate to specific section if specified
                            if section_name:
                                console.print(f"[cyan]🧭 Navigating to section: '{section_name}'...[/cyan]")
                                section_success = universal_nav.navigate_to_section(
                                    section_name=section_name,
                                    click_first_resource=select_first_resource,
                                    resource_name=resource_name,
                                    resource_index=resource_index
                                )
                                
                                if section_success:
                                    console.print(f"[green]✅ Navigated to section: {section_name}[/green]")
                                    time.sleep(3)  # Extra wait for section content to load
                                else:
                                    console.print(f"[yellow]⚠️  Failed to navigate to section '{section_name}'[/yellow]")
                                    console.print(f"[yellow]   Current URL: {browser.driver.current_url}[/yellow]")
                                    
                                    # Verify we're still on the service (not back on homepage)
                                    current_url = browser.driver.current_url
                                    if '/console/home' in current_url or service.lower() not in current_url.lower():
                                        console.print(f"[red]❌ Navigated away from {service}! Attempting to recover...[/red]")
                                        # Try to navigate back to the service
                                        if not universal_nav.navigate_to_service(service, use_search=True):
                                            return {
                                                "status": "error",
                                                "error": f"Lost navigation to {service} and could not recover"
                                            }
                                        time.sleep(2)
                        else:
                            console.print(f"[red]❌ Universal navigator not available[/red]")
                            return {
                                "status": "error",
                                "error": "Universal navigator not available"
                            }

                    # Navigate to specific resource if specified (and section_name not used)
                    if resource_name and not section_name:
                        console.print(f"[yellow]🔍 Searching for resource: {resource_name}[/yellow]")
                        # Try to find and click the resource
                        element = browser.find_element_intelligent(resource_name)
                        if element:
                            console.print(f"[green]✅ Found resource, opening details...[/green]")
                            from tools.universal_screenshot_enhanced import ClickStrategy
                            
                            # FIX: find_element_intelligent returns (By, selector) tuple
                            # but click_element expects just the selector string
                            if isinstance(element, tuple) and len(element) == 2:
                                # Extract just the selector string from the tuple
                                selector_string = element[1]
                                browser.click_element(selector_string, strategy=ClickStrategy.JAVASCRIPT, description=f"Open {resource_name}")
                            else:
                                # If it's already a string, use it directly
                                browser.click_element(element, strategy=ClickStrategy.JAVASCRIPT, description=f"Open {resource_name}")
                            time.sleep(2)
                        else:
                            console.print(f"[yellow]⚠️  Resource '{resource_name}' not found; capturing overview[/yellow]")

                    # Navigate to specific tab if specified
                    if config_tab:
                        console.print(f"[bold cyan]🖱️  Clicking tab '{config_tab}'[/bold cyan]")
                        from tools.aws_tab_navigator import AWSTabNavigator
                        tab_nav = AWSTabNavigator(browser.driver)
                        if tab_nav.find_and_click_tab(config_tab):
                            console.print(f"[green]✅ Successfully navigated to '{config_tab}' tab[/green]")
                            time.sleep(2)
                        else:
                            console.print(f"[yellow]⚠️  Tab '{config_tab}' not found, capturing current view[/yellow]")

                    # 📅 DATE FILTERING (NEW!)
                    if filter_by_date:
                        console.print(f"\n[bold yellow]📅 DATE FILTERING ENABLED[/bold yellow]")
                        
                        # Import date filter
                        from tools.aws_date_filter import AWSDateFilter
                        date_filter = AWSDateFilter(browser.driver)
                        
                        # Apply filter (passing service for smart column detection)
                        filter_params = {
                            "audit_period": audit_period or "FY2025",
                            "start_date": start_date or None,
                            "end_date": end_date or None,
                            "date_column": date_column or None,
                            "service": service  # 🎯 Pass service for smart detection
                        }
                        
                        filter_result = date_filter.filter_by_audit_period(**filter_params)
                        
                        if filter_result["status"] == "success":
                            console.print(f"[green]✅ Date filter applied successfully![/green]")
                            console.print(f"[green]   Filtered: {filter_result['filtered_count']} resources[/green]")
                            console.print(f"[green]   Total: {filter_result['total_count']} resources[/green]")
                            console.print(f"[green]   Period: {filter_result['start_date']} to {filter_result['end_date']}[/green]\n")
                            
                            # Wait for visual update
                            time.sleep(1)
                        else:
                            console.print(f"[yellow]⚠️  Date filter failed: {filter_result.get('error', 'Unknown error')}[/yellow]")
                            console.print(f"[yellow]   Continuing without filter...[/yellow]\n")

                    # 🔄 PAGINATION HANDLING (NEW!)
                    if capture_all_pages:
                        console.print(f"\n[bold yellow]🔄 PAGINATION MODE ENABLED[/bold yellow]")
                        console.print(f"[yellow]   Will capture ALL pages (max: {max_pages})[/yellow]\n")
                        
                        # Get universal navigator for pagination
                        universal_nav = BrowserSessionManager.get_universal_navigator()
                        if universal_nav:
                            # Create screenshot callback for pagination
                            page_screenshots = []
                            
                            def pagination_screenshot_callback(page_num):
                                """Callback function for each page screenshot"""
                                page_filename = filename.replace('.png', f'_page{page_num}.png')
                                page_path = browser.capture_screenshot(name=page_filename.replace('.png', ''))
                                
                                if page_path and os.path.exists(page_path):
                                    # Read and save to evidence manager
                                    with open(page_path, 'rb') as f:
                                        file_content = f.read()
                                    
                                    # Save to evidence folder
                                    success, final_path, message = self.evidence_manager.save_evidence(
                                        file_content=file_content,
                                        file_name=page_filename,
                                        rfi_code=rfi_code
                                    )
                                    
                                    if success and final_path:
                                        page_screenshots.append(final_path)
                                        return final_path
                                
                                return None
                            
                            # Handle pagination
                            pagination_results = universal_nav.handle_pagination(
                                screenshot_callback=pagination_screenshot_callback,
                                max_pages=max_pages
                            )
                            
                            # Return pagination results
                            if pagination_results.get('screenshots'):
                                console.print(f"\n[bold green]✅ PAGINATION COMPLETE![/bold green]")
                                console.print(f"[green]   Total Pages: {pagination_results['total_pages']}[/green]")
                                console.print(f"[green]   Screenshots: {len(pagination_results['screenshots'])}[/green]")
                                console.print(f"[green]   Items: {pagination_results['items_captured']}[/green]\n")
                                
                                return {
                                    "status": "success",
                                    "message": f"Captured {pagination_results['total_pages']} pages with {pagination_results['items_captured']} items",
                                    "screenshots": pagination_results['screenshots'],
                                    "total_pages": pagination_results['total_pages'],
                                    "items_captured": pagination_results['items_captured'],
                                    "pagination_type": pagination_results['pagination_type'],
                                    "service": service,
                                    "account": account,
                                    "region": region
                                }
                        else:
                            console.print(f"[yellow]⚠️  Pagination requested but navigator unavailable, capturing single page[/yellow]")

                    # Final screenshot (single page mode)
                    screenshot_path = browser.capture_screenshot(name=filename.replace('.png',''))
                
                # Verify screenshot was captured
                if screenshot_path and os.path.exists(screenshot_path):
                    console.print(f"[green]✅ Screenshot captured (temp): {screenshot_path}[/green]")
                    
                    # 🔍 SELF-VALIDATION (NEW!)
                    console.print(f"\n[bold yellow]🔍 Validating evidence quality...[/bold yellow]")
                    from tools.evidence_validator import EvidenceValidator
                    
                    validator = EvidenceValidator(driver=browser.driver)
                    validation_result = validator.validate_screenshot_evidence(
                        screenshot_path=screenshot_path,
                        expected_service=service,
                        expected_content=None,  # Optional: can add expected text
                        current_url=browser.driver.current_url
                    )
                    
                    # If validation fails, suggest retry
                    if not validation_result["valid"]:
                        console.print(f"\n[bold red]⚠️  EVIDENCE QUALITY ISSUE DETECTED![/bold red]")
                        console.print(f"[red]   Confidence: {validation_result['confidence']*100:.0f}%[/red]")
                        console.print(f"[red]   Issues: {len(validation_result['issues'])}[/red]\n")
                        
                        # Get retry suggestions
                        retry_strategy = validator.suggest_retry_strategy(validation_result, service)
                        
                        if retry_strategy["should_retry"]:
                            console.print(f"[yellow]💡 Retry Strategy: {retry_strategy['strategy']}[/yellow]")
                            console.print(f"[yellow]   Should we retry with improved parameters? (Agent will decide)[/yellow]\n")
                            
                            # Agent can decide to retry automatically here
                            # For now, continue with warning
                            console.print(f"[yellow]⚠️  Proceeding with current screenshot, but quality may be compromised[/yellow]\n")
                    else:
                        console.print(f"\n[bold green]✅ EVIDENCE VALIDATED (Confidence: {validation_result['confidence']*100:.0f}%)[/bold green]\n")
                    
                    # Read and save to evidence manager
                    with open(screenshot_path, 'rb') as f:
                        file_content = f.read()
                    
                    # Save to evidence folder and get final path
                    success, final_path, message = self.evidence_manager.save_evidence(
                        file_content=file_content,
                        file_name=filename,
                        rfi_code=rfi_code
                    )
                    
                    if success and final_path:
                        console.print(f"[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
                        console.print(f"[bold green]📸 SCREENSHOT SAVED SUCCESSFULLY![/bold green]")
                        console.print(f"[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
                        console.print(f"[bold white]📁 Full Path:[/bold white] {final_path}")
                        console.print(f"[bold white]📂 Directory:[/bold white] {os.path.dirname(final_path)}")
                        console.print(f"[bold white]📄 Filename:[/bold white] {filename}")
                        console.print(f"[bold white]🏷️  RFI Code:[/bold white] {rfi_code}")
                        console.print(f"[bold white]🌍 Region:[/bold white] {region}")
                        console.print(f"[bold white]☁️  Service:[/bold white] {service.upper()}")
                        console.print(f"[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
                    else:
                        console.print(f"[yellow]⚠️  Evidence save warning: {message}[/yellow]")
                    
                    return {
                        "status": "success",
                        "result": {
                            "message": f"Screenshot captured successfully using enhanced navigator",
                            "filename": filename,
                            "service": service,
                            "region": region,
                            "timestamp": timestamp,
                            "temp_path": screenshot_path,
                            "final_path": final_path,
                            "navigator_type": "RDS Enhanced" if service.lower() == 'rds' else "Universal Enhanced",
                            "self_healing_used": True,
                            # 🔍 VALIDATION RESULTS (NEW!)
                            "validation": {
                                "performed": True,
                                "valid": validation_result.get("valid", False),
                                "confidence": validation_result.get("confidence", 0.0),
                                "issues": validation_result.get("issues", []),
                                "checks": validation_result.get("checks", {})
                            }
                        }
                    }
                else:
                    console.print(f"[red]❌ Screenshot not found at: {screenshot_path}[/red]")
                    return {
                        "status": "error",
                        "error": "Screenshot file not created"
                    }
                    
            finally:
                # Always clean up browser
                if navigator:
                    try:
                        navigator.disconnect()
                    except:
                        pass
        
        except Exception as e:
            console.print(f"[red]❌ Enhanced screenshot error: {e}[/red]")
            import traceback
            traceback.print_exc()
            
            # Fallback to old method if enhanced fails
            console.print(f"[yellow]⚠️ Falling back to legacy screenshot method...[/yellow]")
            try:
                result = capture_aws_screenshot(
                    service=service,
                    resource_identifier=resource_name or f"{service}_console",
                    aws_account=account,
                    aws_region=region,
                    tab=config_tab
                )
                
                if result.get('status') == 'success':
                    screenshot_path = result.get('file_path')
                    if screenshot_path and os.path.exists(screenshot_path):
                        with open(screenshot_path, 'rb') as f:
                            file_content = f.read()
                        
                        # Save to evidence folder and get final path
                        success, final_path, message = self.evidence_manager.save_evidence(
                            file_content=file_content,
                            file_name=filename,
                            rfi_code=rfi_code
                        )
                        
                        if success and final_path:
                            console.print(f"[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
                            console.print(f"[bold green]📸 SCREENSHOT SAVED SUCCESSFULLY! (Fallback)[/bold green]")
                            console.print(f"[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
                            console.print(f"[bold white]📁 Full Path:[/bold white] {final_path}")
                            console.print(f"[bold white]📂 Directory:[/bold white] {os.path.dirname(final_path)}")
                            console.print(f"[bold white]📄 Filename:[/bold white] {filename}")
                            console.print(f"[bold white]🏷️  RFI Code:[/bold white] {rfi_code}")
                            console.print(f"[bold white]🌍 Region:[/bold white] {region}")
                            console.print(f"[bold white]☁️  Service:[/bold white] {service.upper()}")
                            console.print(f"[bold green]━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━[/bold green]")
                        
                        try:
                            os.remove(screenshot_path)
                        except:
                            pass
                        
                        return {
                            "status": "success",
                            "result": {
                                "message": f"Screenshot captured (fallback method)",
                                "filename": filename,
                                "final_path": final_path,
                                "service": service,
                                "region": region,
                                "timestamp": timestamp
                            }
                        }
            except:
                pass
            
            return {
                "status": "error",
                "error": f"Screenshot failed: {str(e)}"
            }
    
    def _execute_aws_export(self, params: Dict) -> Dict:
        """Execute AWS data export"""
        try:
            service = params.get('service')
            export_type = params.get('export_type')
            format_type = params.get('format', 'csv')
            account = params.get('aws_account')
            region = params.get('aws_region')
            rfi_code = params.get('rfi_code', 'unknown')
            
            if not all([service, export_type, account, region]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: service, export_type, aws_account, aws_region"
                }
            
            # Create output filename
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{service}_{export_type}_{region}_{timestamp}.{format_type}"
            
            # Get RFI directory
            rfi_dir = self.evidence_manager.get_rfi_directory(rfi_code)
            output_path = str(rfi_dir / filename)
            
            console.print(f"\n[cyan]📊 Exporting AWS data...[/cyan]")
            console.print(f"[cyan]   Service: {service.upper()}[/cyan]")
            console.print(f"[cyan]   Export Type: {export_type}[/cyan]")
            console.print(f"[cyan]   Account: {account}[/cyan]")
            console.print(f"[cyan]   Region: {region}[/cyan]")
            console.print(f"[cyan]   Format: {format_type.upper()}[/cyan]")
            console.print(f"[cyan]   Output: {filename}[/cyan]\n")
            
            # Export data
            success = export_aws_data(
                service=service,
                export_type=export_type,
                format=format_type,
                aws_account=account,
                aws_region=region,
                output_path=output_path
            )
            
            if success:
                # Track in evidence manager
                with open(output_path, 'rb') as f:
                    file_content = f.read()
                
                self.evidence_manager.save_evidence(
                    file_content=file_content,
                    file_name=filename,
                    rfi_code=rfi_code
                )
                
                return {
                    "status": "success",
                    "result": {
                        "message": f"Data exported successfully",
                        "filename": filename,
                        "output_path": output_path,
                        "service": service,
                        "export_type": export_type,
                        "format": format_type,
                        "timestamp": timestamp
                    }
                }
            else:
                return {
                    "status": "error",
                    "error": "Data export failed. Check output for details."
                }
        
        except Exception as e:
            console.print(f"[red]❌ Export error: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Export failed: {str(e)}"
            }
    
    def _execute_list_aws(self, params: Dict) -> Dict:
        """Execute AWS resource listing"""
        try:
            service = params.get('service')
            account = params.get('aws_account')
            region = params.get('aws_region', 'us-east-1')
            
            if not all([service, account]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: service, aws_account"
                }
            
            console.print(f"\n[cyan]📋 Listing AWS resources...[/cyan]")
            console.print(f"[cyan]   Service: {service.upper()}[/cyan]")
            console.print(f"[cyan]   Account: {account}[/cyan]")
            console.print(f"[cyan]   Region: {region}[/cyan]\n")
            
            # Call appropriate listing function
            result = None
            
            if service == 's3':
                result = list_s3_buckets(account, region)
            elif service == 'rds':
                # List both instances and clusters
                instances = list_rds_instances(account, region)
                clusters = list_rds_clusters(account, region)
                result = {
                    'instances': instances,
                    'clusters': clusters,
                    'total': len(instances) + len(clusters)
                }
            elif service == 'iam':
                result = list_iam_users(account)
            elif service == 'ec2':
                result = list_ec2_instances(account, region)
            elif service == 'lambda':
                result = list_lambda_functions(account, region)
            elif service == 'vpc':
                result = list_vpc_resources(account, region)
            else:
                return {
                    "status": "error",
                    "error": f"Unsupported service: {service}"
                }
            
            return {
                "status": "success",
                "result": {
                    "message": f"Listed {service.upper()} resources",
                    "service": service,
                    "account": account,
                    "region": region,
                    "data": result
                }
            }
        
        except Exception as e:
            console.print(f"[red]❌ List error: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"List failed: {str(e)}"
            }
    
    def _execute_show_evidence(self, params: Dict) -> Dict:
        """Show local evidence summary"""
        try:
            rfi_code = params.get('rfi_code', None)
            
            # Get collected evidence using the correct method
            collected = self.evidence_manager.list_collected_evidence(rfi_code=rfi_code)
            
            if not collected:
                return {
                    "status": "success",
                    "result": {
                        "files": {},
                        "count": 0,
                        "message": "No evidence collected yet",
                        "local_folder": str(self.evidence_manager.evidence_dir)
                    }
                }
            
            # Count total files across all RFIs
            total_files = sum(len(files) for files in collected.values())
            
            # Format for Claude
            files_by_rfi = {}
            for rfi, files in collected.items():
                files_by_rfi[rfi] = [
                    {
                        "name": f['name'],
                        "size": f['size'],
                        "type": f['type'],
                        "modified": f['modified']
                    }
                    for f in files
                ]
            
            return {
                "status": "success",
                "result": {
                    "files_by_rfi": files_by_rfi,
                    "total_files": total_files,
                    "rfis": list(collected.keys()),
                    "local_folder": str(self.evidence_manager.evidence_dir),
                    "message": f"Found {total_files} files across {len(collected)} RFIs"
                }
            }
        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    
    def _execute_upload(self, params: Dict) -> Dict:
        """Execute SharePoint upload"""
        try:
            # Check if user has approved upload
            if not self.evidence_manager.prompt_for_upload_approval():
                return {
                    "status": "cancelled",
                    "message": "Upload cancelled by user"
                }
            
            # Get files to upload (returns dict of {rfi_code: [file_paths]})
            by_rfi = self.evidence_manager.get_upload_ready_files()
            
            if not by_rfi:
                return {
                    "status": "error",
                    "error": "No files collected to upload"
                }
            
            # Upload each RFI folder
            results = []
            for rfi_code, file_paths in by_rfi.items():
                console.print(f"\n[cyan]📤 Uploading {len(file_paths)} files for RFI {rfi_code}...[/cyan]")
                
                # Get product from params if provided
                product = params.get('product', '')
                year = os.getenv('SHAREPOINT_CURRENT_YEAR', 'FY2025')
                
                success, message = upload_to_sharepoint(
                    local_files=file_paths,
                    rfi_code=rfi_code,
                    product=product,
                    year=year
                )
                
                results.append({
                    'rfi_code': rfi_code,
                    'success': success,
                    'message': message,
                    'file_count': len(file_paths)
                })
            
            # Check if all succeeded
            all_success = all(r['success'] for r in results)
            
            if all_success:
                # Clear uploaded files from each RFI
                for rfi_code, file_paths in by_rfi.items():
                    self.evidence_manager.clear_uploaded_evidence(rfi_code, file_paths)
                
                return {
                    "status": "success",
                    "result": {
                        "message": "All files uploaded successfully",
                        "uploads": results
                    }
                }
            else:
                return {
                    "status": "partial_success",
                    "result": {
                        "message": "Some uploads failed",
                        "uploads": results
                    }
                }
        
        except Exception as e:
            console.print(f"[red]❌ Upload error: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Upload failed: {str(e)}"
            }
    
    def _execute_learn_from_sharepoint(self, params: Dict) -> Dict:
        """Execute learning from SharePoint URL"""
        try:
            sharepoint_url = params.get('sharepoint_url')
            rfi_code = params.get('rfi_code')
            
            if not sharepoint_url or not rfi_code:
                return {
                    "status": "error",
                    "error": "Missing required parameters: sharepoint_url and rfi_code"
                }
            
            # Check if learner is available (requires LLM)
            if not self.learner:
                return {
                    "status": "error",
                    "error": "Learning capability requires LLM (Claude). Please configure LLM_PROVIDER."
                }
            
            console.print(f"\n[bold cyan]🎓 Learning from SharePoint Evidence[/bold cyan]")
            console.print(f"[cyan]URL: {sharepoint_url}[/cyan]")
            console.print(f"[cyan]RFI: {rfi_code}[/cyan]\n")
            
            # Use learner to analyze SharePoint folder
            result = self.learner.learn_from_sharepoint_url(sharepoint_url, rfi_code)
            
            if result['status'] == 'success':
                plan = result['collection_plan']
                
                # Format response for Claude
                return {
                    "status": "success",
                    "result": {
                        "rfi_code": rfi_code,
                        "files_analyzed": result['files_analyzed'],
                        "overview": plan.get('overview', 'Learning complete'),
                        "evidence_types": plan.get('evidence_types', {}),
                        "aws_services": plan.get('aws_services', []),
                        "collection_tasks": [
                            {
                                "task_id": task.get('task_id'),
                                "description": task.get('description'),
                                "aws_service": task.get('aws_service'),
                                "evidence_type": task.get('evidence_type'),
                                "automation": task.get('automation'),
                                "instructions": task.get('instructions')
                            }
                            for task in plan.get('collection_tasks', [])
                        ],
                        "automation_summary": plan.get('automation_summary', {}),
                        "estimated_time_minutes": plan.get('estimated_time_minutes', 0),
                        "prerequisites": plan.get('prerequisites', []),
                        "message": f"✅ Learned from {result['files_analyzed']} files. Collection plan created and saved to knowledge base."
                    }
                }
            else:
                return {
                    "status": "error",
                    "error": result.get('message', 'Learning failed')
                }
        
        except Exception as e:
            console.print(f"[red]❌ Learning failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Learning failed: {str(e)}"
            }

    def _execute_analyze_document_evidence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Use DocumentIntelligence to reason about evidence files."""

        if not self.document_intelligence:
            return {
                "status": "error",
                "error": "Document intelligence module not available"
            }

        file_path = params.get('file_path')
        files = params.get('files')
        context = params.get('context')
        metadata = params.get('metadata') or {}

        try:
            if file_path:
                insight = self.document_intelligence.analyze_document(
                    file_path,
                    metadata=metadata,
                    context=context,
                )
                return {
                    "status": "success",
                    "analysis": asdict(insight)
                }

            if files:
                summary, insights = self.document_intelligence.build_brief_summary(
                    files,
                    context=context,
                )
                return {
                    "status": "success",
                    "summary": summary,
                    "insights": [asdict(item) for item in insights]
                }

            return {
                "status": "error",
                "error": "Provide either file_path or files for analysis"
            }

        except Exception as exc:
            console.print(f"[red]❌ Document analysis failed: {exc}[/red]")
            return {
                "status": "error",
                "error": f"Document analysis failed: {exc}"
            }

    def _execute_read_tool_source(self, params: Dict) -> Dict:
        """Execute read_tool_source - Read source code of a tool"""
        from ai_brain.self_healing_tools import read_tool_source_code
        
        tool_name = params.get('tool_name')
        section = params.get('section')
        
        console.print(f"[cyan]📖 Reading source code for: {tool_name}[/cyan]")
        if section:
            console.print(f"[dim]   Focusing on section: {section}[/dim]")
        
        result = read_tool_source_code(tool_name, section)
        
        if result['status'] == 'success':
            console.print(f"[green]✅ Read {result['total_lines']} lines from {result['source_file']}[/green]")
            
            # Provide context about the architecture
            if tool_name == "aws_take_screenshot":
                console.print("[bold cyan]📚 Architecture Context:[/bold cyan]")
                console.print("[dim]   This tool uses a HYBRID approach:[/dim]")
                console.print("[dim]   • undetected-chromedriver (Selenium) for browser launch[/dim]")
                console.print("[dim]   • Playwright (via CDP) for element interaction[/dim]")
                console.print("[dim]   • Browser session managed by BrowserSessionManager[/dim]")
                console.print("[dim]   • RDS navigation handled by RDSNavigatorEnhanced[/dim]")
        else:
            console.print(f"[yellow]⚠️  Could not read source: {result.get('error', 'Unknown error')}[/yellow]")
            if 'available_tools' in result:
                console.print(f"[dim]   Available tools: {', '.join(result['available_tools'])}[/dim]")
        
        return result
    
    def _execute_diagnose_error(self, params: Dict) -> Dict:
        """Execute diagnose_error - Analyze an error"""
        from ai_brain.self_healing_tools import diagnose_error_context
        
        error_message = params.get('error_message')
        tool_name = params.get('tool_name')
        parameters = params.get('parameters', {})
        
        console.print(f"[cyan]🔍 Diagnosing error in: {tool_name}[/cyan]")
        console.print(f"[dim]   Error: {error_message[:100]}...[/dim]")
        
        result = diagnose_error_context(error_message, tool_name, parameters)
        
        if result['status'] == 'success':
            console.print(f"[green]✅ Diagnosis complete[/green]")
            if 'error_analysis' in result:
                error_type = result['error_analysis'].get('type', 'Unknown')
                console.print(f"[yellow]   Error Type: {error_type}[/yellow]")
        
        return result
    
    def _execute_fix_tool_code(self, params: Dict) -> Dict:
        """Execute fix_tool_code - Fix a bug in tool code"""
        from ai_brain.self_healing_tools import fix_tool_code_with_validation
        
        tool_name = params.get('tool_name')
        issue = params.get('issue')
        old_code = params.get('old_code')
        new_code = params.get('new_code')
        
        console.print(f"[cyan]🔧 Fixing tool: {tool_name}[/cyan]")
        console.print(f"[yellow]   Issue: {issue}[/yellow]")
        
        result = fix_tool_code_with_validation(tool_name, issue, old_code, new_code)
        
        return result
    
    def _execute_test_tool(self, params: Dict) -> Dict:
        """Execute test_tool - Test a tool after fixing"""
        from ai_brain.self_healing_tools import test_tool_functionality
        
        tool_name = params.get('tool_name')
        test_parameters = params.get('test_parameters')
        
        result = test_tool_functionality(tool_name, test_parameters)
        
        return result
    
    def _execute_browser_screenshot(self, params: Dict) -> Dict:
        """Execute get_browser_screenshot - Capture browser state for debugging"""
        from ai_brain.self_healing_tools import capture_browser_debug_screenshot
        
        context = params.get('context')
        
        result = capture_browser_debug_screenshot(context)
        
        return result
    
    def _execute_generate_tool(self, params: Dict) -> Dict:
        """Execute generate_new_tool - Generate a completely new tool"""
        from ai_brain.code_generation_tools import generate_new_tool_implementation
        
        tool_name = params.get('tool_name')
        description = params.get('description')
        functionality = params.get('functionality')
        parameters = params.get('parameters')
        aws_services = params.get('aws_services')
        libraries_needed = params.get('libraries_needed')
        
        result = generate_new_tool_implementation(
            tool_name=tool_name,
            description=description,
            functionality=functionality,
            parameters=parameters,
            aws_services=aws_services,
            libraries_needed=libraries_needed
        )
        
        return result
    
    def _execute_add_functionality(self, params: Dict) -> Dict:
        """Execute add_functionality_to_tool - Extend an existing tool"""
        from ai_brain.code_generation_tools import add_functionality_to_existing_tool
        
        existing_tool = params.get('existing_tool')
        new_functionality = params.get('new_functionality')
        implementation_details = params.get('implementation_details')
        code_to_add = params.get('code_to_add')
        insertion_point = params.get('insertion_point')
        
        result = add_functionality_to_existing_tool(
            existing_tool=existing_tool,
            new_functionality=new_functionality,
            implementation_details=implementation_details,
            code_to_add=code_to_add,
            insertion_point=insertion_point
        )
        
        return result
    
    def _execute_implement_function(self, params: Dict) -> Dict:
        """Execute implement_missing_function - Implement a missing function"""
        from ai_brain.code_generation_tools import implement_missing_function_logic
        
        file_path = params.get('file_path')
        function_name = params.get('function_name')
        function_purpose = params.get('function_purpose')
        function_signature = params.get('function_signature')
        implementation = params.get('implementation')
        
        result = implement_missing_function_logic(
            file_path=file_path,
            function_name=function_name,
            function_purpose=function_purpose,
            function_signature=function_signature,
            implementation=implementation
        )
        
        return result
    
    def _execute_search_examples(self, params: Dict) -> Dict:
        """Execute search_implementation_examples - Find code examples"""
        from ai_brain.code_generation_tools import search_codebase_for_examples
        
        search_pattern = params.get('search_pattern')
        context = params.get('context')
        file_type = params.get('file_type', '.py')
        
        result = search_codebase_for_examples(
            search_pattern=search_pattern,
            context=context,
            file_type=file_type
        )
        
        return result
    
    def _execute_intelligent_export(self, params: Dict) -> Dict:
        """Execute intelligent file export with brain-powered decisions"""
        if not self.file_exporter:
            return {
                "status": "error",
                "error": "Intelligent file export requires LLM. Please configure LLM_PROVIDER."
            }
        
        try:
            file_path = params.get('file_path')
            output_format = params.get('output_format', 'csv')
            extraction_goal = params.get('extraction_goal')
            
            if not file_path:
                return {
                    "status": "error",
                    "error": "Missing required parameter: file_path"
                }
            
            console.print(f"[bold cyan]🧠 Intelligent File Export[/bold cyan]")
            console.print(f"[cyan]   File: {file_path}[/cyan]")
            console.print(f"[cyan]   Format: {output_format}[/cyan]")
            if extraction_goal:
                console.print(f"[cyan]   Goal: {extraction_goal}[/cyan]")
            
            output_path = self.file_exporter.export_file(
                file_path=file_path,
                output_format=output_format,
                extraction_goal=extraction_goal
            )
            
            return {
                "status": "success",
                "result": {
                    "message": "File exported with brain-powered intelligence",
                    "output_path": output_path,
                    "intelligence_used": True
                }
            }
        
        except Exception as e:
            console.print(f"[red]❌ Intelligent export failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Export failed: {str(e)}"
            }
    
    def _execute_intelligent_aws_cli(self, params: Dict) -> Dict:
        """Execute AWS CLI with brain-powered optimization"""
        if not self.aws_cli:
            return {
                "status": "error",
                "error": "Intelligent AWS CLI requires LLM. Please configure LLM_PROVIDER."
            }
        
        try:
            service = params.get('service')
            action = params.get('action')
            context = params.get('context', {})
            
            if not all([service, action]):
                return {
                    "status": "error",
                    "error": "Missing required parameters: service, action"
                }
            
            result = self.aws_cli.execute_command(
                service=service,
                action=action,
                context=context
            )
            
            return {
                "status": "success",
                "result": result
            }
        
        except Exception as e:
            console.print(f"[red]❌ Intelligent AWS CLI failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"AWS CLI failed: {str(e)}"
            }
    
    def _execute_intelligent_evidence_collection(self, params: Dict) -> Dict:
        """Execute intelligent evidence collection with brain analysis"""
        if not self.evidence_collector:
            return {
                "status": "error",
                "error": "Intelligent evidence collection requires LLM. Please configure LLM_PROVIDER."
            }
        
        try:
            rfi_code = params.get('rfi_code')
            previous_evidence = params.get('previous_evidence', [])
            
            if not rfi_code:
                return {
                    "status": "error",
                    "error": "Missing required parameter: rfi_code"
                }
            
            requirements = self.evidence_collector.collect_for_rfi(
                rfi_code=rfi_code,
                previous_evidence=previous_evidence
            )
            
            return {
                "status": "success",
                "result": requirements
            }
        
        except Exception as e:
            console.print(f"[red]❌ Intelligent evidence collection failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Collection failed: {str(e)}"
            }
    
    def _execute_orchestrator_analyze(self, params: Dict) -> Dict:
        """Execute orchestrator analysis and planning"""
        if not self.orchestrator:
            return {
                "status": "error",
                "error": "AI Orchestrator requires LLM. Please configure LLM_PROVIDER."
            }
        
        try:
            rfi_code = params.get('rfi_code')
            previous_evidence = params.get('previous_evidence_files', [])
            
            if not rfi_code:
                return {
                    "status": "error",
                    "error": "Missing required parameter: rfi_code"
                }
            
            console.print(f"[bold cyan]🧠 Orchestrator Analyzing Evidence for {rfi_code}[/bold cyan]")
            
            result = self.orchestrator.analyze_and_plan(
                rfi_code=rfi_code,
                previous_evidence_files=previous_evidence
            )
            
            return result
        
        except Exception as e:
            console.print(f"[red]❌ Orchestrator analysis failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Analysis failed: {str(e)}"
            }
    
    def _execute_orchestrator_execute(self, params: Dict) -> Dict:
        """Execute orchestrator's plan"""
        if not self.orchestrator:
            return {
                "status": "error",
                "error": "AI Orchestrator requires LLM. Please configure LLM_PROVIDER."
            }
        
        try:
            plan = params.get('plan')  # Optional - uses stored plan if not provided
            
            console.print(f"[bold green]🚀 Orchestrator Executing Plan[/bold green]")
            
            result = self.orchestrator.execute_plan(plan=plan)
            
            return result
        
        except Exception as e:
            console.print(f"[red]❌ Orchestrator execution failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Execution failed: {str(e)}"
            }
    
    def _execute_python_code(self, params: dict) -> dict:
        """Execute Python code written by Claude dynamically"""
        from ai_brain.dynamic_code_executor import execute_python_code
        
        try:
            code = params.get('code', '')
            description = params.get('description', 'Dynamic code execution')
            timeout = params.get('timeout', 300)
            
            console.print(f"[bold cyan]🧠 Claude-Generated Code Execution[/bold cyan]")
            console.print(f"[dim]Description: {description}[/dim]")
            
            result = execute_python_code(
                code=code,
                description=description,
                timeout=timeout
            )
            
            if result['success']:
                return {
                    "status": "success",
                    "result": result['output'],
                    "execution_time": result['execution_time']
                }
            else:
                return {
                    "status": "error",
                    "error": result['error'],
                    "partial_output": result.get('output', ''),
                    "execution_time": result['execution_time']
                }
        
        except Exception as e:
            console.print(f"[red]❌ Code execution failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Code execution failed: {str(e)}"
            }
    
    def _execute_analyze_past_evidence(self, params: dict) -> dict:
        """Analyze past evidence to learn patterns"""
        from ai_brain.dynamic_code_executor import analyze_past_evidence
        
        try:
            evidence_path = params.get('evidence_path', '')
            rfi_code = params.get('rfi_code')
            year = params.get('year')
            
            console.print(f"[bold cyan]📚 Analyzing Past Evidence[/bold cyan]")
            console.print(f"[dim]Path: {evidence_path}[/dim]")
            
            result = analyze_past_evidence(
                evidence_path=evidence_path,
                rfi_code=rfi_code,
                year=year
            )
            
            if result['success']:
                return {
                    "status": "success",
                    "patterns": result['patterns'],
                    "examples": result['examples'],
                    "recommendations": result['recommendations'],
                    "total_items": result.get('total_items', 0)
                }
            else:
                return {
                    "status": "error",
                    "error": result['error']
                }
        
        except Exception as e:
            console.print(f"[red]❌ Evidence analysis failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return {
                "status": "error",
                "error": f"Evidence analysis failed: {str(e)}"
            }
    
    # === JIRA INTEGRATION IMPLEMENTATIONS ===
    def _execute_jira_list_tickets(self, params: Dict) -> Dict:
        """Execute Jira list tickets"""
        try:
            from integrations import JiraIntegration
            
            jira = JiraIntegration()
            if not jira.jira:
                return {"status": "error", "error": "Jira not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            tickets = jira.list_tickets(
                project=params.get('project'),
                labels=params.get('labels'),
                status=params.get('status'),
                assignee=params.get('assignee'),
                priority=params.get('priority'),
                issue_type=params.get('issue_type'),
                max_results=params.get('max_results', 50)
            )
            
            # Export if requested
            export_format = params.get('export_format')
            export_path = ""
            if export_format and tickets:
                export_path = jira.export_tickets(tickets, output_format=export_format)
            
            return {
                "status": "success",
                "result": {
                    "tickets": tickets,
                    "count": len(tickets),
                    "export_path": export_path
                }
            }
        except Exception as e:
            console.print(f"[red]❌ Jira list tickets failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def _execute_jira_search_jql(self, params: Dict) -> Dict:
        """Execute Jira JQL search"""
        try:
            from integrations import JiraIntegration
            
            jira = JiraIntegration()
            if not jira.jira:
                return {"status": "error", "error": "Jira not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            tickets = jira.search_jql(
                jql_query=params.get('jql_query'),
                max_results=params.get('max_results', 100)
            )
            
            # Export if requested
            export_format = params.get('export_format')
            export_path = ""
            if export_format and tickets:
                export_path = jira.export_tickets(tickets, output_format=export_format)
            
            return {
                "status": "success",
                "result": {
                    "tickets": tickets,
                    "count": len(tickets),
                    "export_path": export_path
                }
            }
        except Exception as e:
            console.print(f"[red]❌ Jira JQL search failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def _execute_jira_get_ticket(self, params: Dict) -> Dict:
        """Execute Jira get ticket"""
        try:
            from integrations import JiraIntegration
            
            jira = JiraIntegration()
            if not jira.jira:
                return {"status": "error", "error": "Jira not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            ticket = jira.get_ticket(ticket_key=params.get('ticket_key'))
            
            if not ticket:
                return {"status": "error", "error": f"Ticket {params.get('ticket_key')} not found"}
            
            return {
                "status": "success",
                "result": ticket
            }
        except Exception as e:
            console.print(f"[red]❌ Jira get ticket failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    # === CONFLUENCE INTEGRATION IMPLEMENTATIONS ===
    def _execute_confluence_search(self, params: Dict) -> Dict:
        """Execute Confluence search"""
        try:
            from integrations import ConfluenceIntegration
            
            confluence = ConfluenceIntegration()
            if not confluence.confluence:
                return {"status": "error", "error": "Confluence not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            pages = confluence.search_documents(
                query=params.get('query'),
                space=params.get('space'),
                limit=params.get('limit', 50)
            )
            
            # Export if requested
            export_format = params.get('export_format')
            export_path = ""
            if export_format and pages:
                export_path = confluence.export_pages(pages, output_format=export_format)
            
            return {
                "status": "success",
                "result": {
                    "pages": pages,
                    "count": len(pages),
                    "export_path": export_path
                }
            }
        except Exception as e:
            console.print(f"[red]❌ Confluence search failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def _execute_confluence_get_page(self, params: Dict) -> Dict:
        """Execute Confluence get page"""
        try:
            from integrations import ConfluenceIntegration
            
            confluence = ConfluenceIntegration()
            if not confluence.confluence:
                return {"status": "error", "error": "Confluence not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            page = confluence.get_page(
                page_id=params.get('page_id'),
                page_title=params.get('page_title'),
                space=params.get('space')
            )
            
            if not page:
                return {"status": "error", "error": "Page not found"}
            
            # Convert to markdown if requested
            if params.get('as_markdown'):
                markdown = confluence.get_page_content_as_markdown(page.get('id'))
                page['content_markdown'] = markdown
            
            return {
                "status": "success",
                "result": page
            }
        except Exception as e:
            console.print(f"[red]❌ Confluence get page failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def _execute_confluence_list_space(self, params: Dict) -> Dict:
        """Execute Confluence list space"""
        try:
            from integrations import ConfluenceIntegration
            
            confluence = ConfluenceIntegration()
            if not confluence.confluence:
                return {"status": "error", "error": "Confluence not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            pages = confluence.list_space_pages(
                space=params.get('space'),
                limit=params.get('limit', 100)
            )
            
            # Export if requested
            export_format = params.get('export_format')
            export_path = ""
            if export_format and pages:
                export_path = confluence.export_pages(pages, output_format=export_format)
            
            return {
                "status": "success",
                "result": {
                    "pages": pages,
                    "count": len(pages),
                    "export_path": export_path
                }
            }
        except Exception as e:
            console.print(f"[red]❌ Confluence list space failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    # === GITHUB INTEGRATION IMPLEMENTATIONS ===
    def _execute_github_list_prs(self, params: Dict) -> Dict:
        """Execute GitHub list PRs"""
        try:
            from integrations import GitHubIntegration
            
            github = GitHubIntegration()
            if not github.github:
                return {"status": "error", "error": "GitHub not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            prs = github.list_pull_requests(
                repo_name=params.get('repo_name'),
                state=params.get('state', 'all'),
                author=params.get('author'),
                label=params.get('label'),
                limit=params.get('limit', 50)
            )
            
            # Export if requested
            export_format = params.get('export_format')
            export_path = ""
            if export_format and prs:
                export_path = github.export_data(prs, output_format=export_format)
            
            return {
                "status": "success",
                "result": {
                    "pull_requests": prs,
                    "count": len(prs),
                    "export_path": export_path
                }
            }
        except Exception as e:
            console.print(f"[red]❌ GitHub list PRs failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def _execute_github_get_pr(self, params: Dict) -> Dict:
        """Execute GitHub get PR"""
        try:
            from integrations import GitHubIntegration
            
            github = GitHubIntegration()
            if not github.github:
                return {"status": "error", "error": "GitHub not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            pr = github.get_pull_request(
                repo_name=params.get('repo_name'),
                pr_number=params.get('pr_number')
            )
            
            if not pr:
                return {"status": "error", "error": f"PR #{params.get('pr_number')} not found"}
            
            return {
                "status": "success",
                "result": pr
            }
        except Exception as e:
            console.print(f"[red]❌ GitHub get PR failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def _execute_github_search_code(self, params: Dict) -> Dict:
        """Execute GitHub code search"""
        try:
            from integrations import GitHubIntegration
            
            github = GitHubIntegration()
            if not github.github:
                return {"status": "error", "error": "GitHub not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            results = github.search_code(
                query=params.get('query'),
                repo=params.get('repo'),
                language=params.get('language'),
                limit=params.get('limit', 50)
            )
            
            return {
                "status": "success",
                "result": {
                    "results": results,
                    "count": len(results)
                }
            }
        except Exception as e:
            console.print(f"[red]❌ GitHub code search failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def _execute_github_list_issues(self, params: Dict) -> Dict:
        """Execute GitHub list issues"""
        try:
            from integrations import GitHubIntegration
            
            github = GitHubIntegration()
            if not github.github:
                return {"status": "error", "error": "GitHub not connected. Please check INTEGRATION_SETUP_GUIDE.md"}
            
            issues = github.list_issues(
                repo_name=params.get('repo_name'),
                state=params.get('state', 'all'),
                labels=params.get('labels'),
                assignee=params.get('assignee'),
                limit=params.get('limit', 50)
            )
            
            # Export if requested
            export_format = params.get('export_format')
            export_path = ""
            if export_format and issues:
                export_path = github.export_data(issues, output_format=export_format)
            
            return {
                "status": "success",
                "result": {
                    "issues": issues,
                    "count": len(issues),
                    "export_path": export_path
                }
            }
        except Exception as e:
            console.print(f"[red]❌ GitHub list issues failed: {e}[/red]")
            return {"status": "error", "error": str(e)}
    
    def cleanup(self):
        """Cleanup resources"""
        from ai_brain.browser_session_manager import BrowserSessionManager
        
        # Close SharePoint
        if self.sharepoint:
            self.sharepoint.close()
        
        # Close persistent browser session
        BrowserSessionManager.close_browser()

