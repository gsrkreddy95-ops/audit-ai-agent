"""
Evidence Replicator - Collects current year's evidence based on previous year's patterns
Ensures all evidence has proper timestamps
"""

import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn

console = Console()


class EvidenceReplicator:
    """
    Replicates evidence collection based on analysis of previous year
    Ensures proper timestamps on all collected evidence
    """
    
    def __init__(self, aws_integration, sharepoint_integration, 
                 auth_manager, screenshot_collector=None):
        self.aws = aws_integration
        self.sharepoint = sharepoint_integration
        self.auth = auth_manager
        self.screenshot_collector = screenshot_collector
        self.collected_evidence = []
    
    def replicate_rfi_evidence(self, analysis_result: Dict, 
                              current_year: str = "FY25",
                              auto_upload: bool = True) -> Dict:
        """
        Replicate evidence collection based on analysis of previous year
        
        Args:
            analysis_result: Output from EvidenceAnalyzer.analyze_rfi_folder()
            current_year: Current audit year
            auto_upload: Automatically upload to SharePoint
        
        Returns:
            {
                'rfi_code': '10.1.2.12',
                'current_year': 'FY25',
                'collected_evidence': [
                    {
                        'original_file': 'aws_ctr-int_rds_prod-cluster_2024-03-15.png',
                        'new_file': 'aws_ctr-int_rds_prod-cluster_2025-11-06_15-30-45.png',
                        'type': 'screenshot',
                        'timestamp': '2025-11-06 15:30:45',
                        'status': 'collected',
                        'uploaded': True,
                        'sharepoint_url': '...'
                    }
                ],
                'success_count': 15,
                'failure_count': 0,
                'summary': '...'
            }
        """
        rfi_code = analysis_result['rfi_code']
        product = analysis_result.get('product')
        evidence_patterns = analysis_result['evidence_found']
        
        console.print(f"\n[cyan]🔄 Replicating evidence for RFI {rfi_code} ({current_year})...[/cyan]")
        
        collected = []
        success_count = 0
        failure_count = 0
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Collecting evidence...", total=len(evidence_patterns))
            
            for pattern in evidence_patterns:
                try:
                    # Replicate this piece of evidence
                    result = self._replicate_single_evidence(pattern, current_year)
                    
                    if result:
                        collected.append(result)
                        success_count += 1
                        
                        # Auto-upload to SharePoint if enabled
                        if auto_upload and result.get('local_path'):
                            upload_success, sp_url = self.sharepoint.upload_evidence(
                                result['local_path'],
                                rfi_code,
                                product
                            )
                            result['uploaded'] = upload_success
                            result['sharepoint_url'] = sp_url
                    else:
                        failure_count += 1
                    
                    progress.update(task, advance=1)
                
                except Exception as e:
                    console.print(f"[red]❌ Failed to replicate {pattern.get('file_name')}: {e}[/red]")
                    failure_count += 1
                    progress.update(task, advance=1)
        
        # Generate summary
        summary = self._generate_replication_summary(collected, success_count, failure_count)
        
        result = {
            'rfi_code': rfi_code,
            'product': product,
            'current_year': current_year,
            'collected_evidence': collected,
            'success_count': success_count,
            'failure_count': failure_count,
            'summary': summary
        }
        
        self._display_replication_summary(result)
        
        return result
    
    def _replicate_single_evidence(self, pattern: Dict, current_year: str) -> Optional[Dict]:
        """
        Replicate a single piece of evidence based on pattern
        Returns: Evidence metadata with timestamp
        """
        replication_instr = pattern.get('replication_instruction')
        
        if not replication_instr:
            console.print(f"[yellow]⚠️  No replication instructions for {pattern.get('file_name')}[/yellow]")
            return None
        
        action = replication_instr.get('action')
        
        if action == 'screenshot':
            return self._replicate_screenshot(pattern, replication_instr, current_year)
        
        elif action == 'export':
            return self._replicate_export(pattern, replication_instr, current_year)
        
        elif action == 'export_pdf':
            return self._replicate_pdf_export(pattern, replication_instr, current_year)
        
        else:
            console.print(f"[yellow]⚠️  Unknown action: {action}[/yellow]")
            return None
    
    def _replicate_screenshot(self, pattern: Dict, instruction: Dict, current_year: str) -> Optional[Dict]:
        """Take screenshot based on instruction with timestamp"""
        if not self.screenshot_collector:
            console.print("[yellow]⚠️  Screenshot collector not initialized[/yellow]")
            return {
                'original_file': pattern.get('file_name'),
                'type': 'screenshot',
                'status': 'skipped',
                'reason': 'Screenshot collector not available'
            }
        
        # Extract details
        service = instruction.get('service')
        resource = instruction.get('resource')
        page = instruction.get('page')
        account = instruction.get('account')
        
        # Ensure authentication
        if account:
            if not self.auth.ensure_aws_auth(account):
                return {
                    'original_file': pattern.get('file_name'),
                    'type': 'screenshot',
                    'status': 'failed',
                    'reason': 'Authentication failed'
                }
        
        # Take screenshot
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            screenshot_path = self.screenshot_collector.capture_aws_console(
                service=service,
                resource=resource,
                page=page,
                account=account,
                timestamp=timestamp
            )
            
            if screenshot_path:
                return {
                    'original_file': pattern.get('file_name'),
                    'new_file': Path(screenshot_path).name,
                    'local_path': screenshot_path,
                    'type': 'screenshot',
                    'service': service,
                    'resource': resource,
                    'account': account,
                    'timestamp': timestamp,
                    'status': 'collected'
                }
        
        except Exception as e:
            console.print(f"[red]❌ Screenshot failed: {e}[/red]")
        
        return None
    
    def _replicate_export(self, pattern: Dict, instruction: Dict, current_year: str) -> Optional[Dict]:
        """Export data based on instruction with timestamp"""
        service = instruction.get('service')
        data_type = instruction.get('data_type')
        accounts = instruction.get('accounts', [])
        export_format = instruction.get('format', 'excel')
        
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        # Determine which integration to use
        if service in ['rds', 'iam', 'ec2', 's3', 'cloudtrail']:
            return self._export_aws_data(service, data_type, accounts, export_format, timestamp)
        
        elif service == 'pagerduty':
            return self._export_pagerduty_data(data_type, export_format, timestamp)
        
        elif service == 'datadog':
            return self._export_datadog_data(data_type, export_format, timestamp)
        
        else:
            console.print(f"[yellow]⚠️  Service {service} not yet supported[/yellow]")
            return {
                'original_file': pattern.get('file_name'),
                'type': 'export',
                'service': service,
                'status': 'skipped',
                'reason': f'Service {service} not implemented'
            }
    
    def _export_aws_data(self, service: str, data_type: str, accounts: List[str], 
                        export_format: str, timestamp: str) -> Optional[Dict]:
        """Export AWS data with timestamp"""
        try:
            # Ensure AWS authentication
            if not self.auth.ensure_aws_auth(accounts[0] if accounts else 'ctr-int'):
                return None
            
            # Export based on service
            if service == 'rds':
                if not accounts:
                    accounts = self.aws.accounts
                output_file = self.aws.export_rds_instances(
                    accounts=accounts,
                    output_file=f"rds_instances_all_accounts_{timestamp}.xlsx"
                )
            
            elif service == 'iam':
                if not accounts:
                    accounts = self.aws.accounts
                output_file = self.aws.export_iam_users(
                    accounts=accounts,
                    output_file=f"iam_users_all_accounts_{timestamp}.xlsx"
                )
            
            elif service == 'ec2':
                # TODO: Implement EC2 export
                output_file = f"ec2_instances_{timestamp}.xlsx"
            
            elif service == 's3':
                # TODO: Implement S3 export
                output_file = f"s3_buckets_{timestamp}.xlsx"
            
            else:
                return None
            
            if output_file and os.path.exists(output_file):
                return {
                    'new_file': Path(output_file).name,
                    'local_path': output_file,
                    'type': 'export',
                    'service': service,
                    'data_type': data_type,
                    'accounts': accounts,
                    'format': export_format,
                    'timestamp': timestamp,
                    'status': 'collected'
                }
        
        except Exception as e:
            console.print(f"[red]❌ AWS export failed: {e}[/red]")
        
        return None
    
    def _export_pagerduty_data(self, data_type: str, export_format: str, timestamp: str) -> Optional[Dict]:
        """Export PagerDuty data with timestamp"""
        # TODO: Implement PagerDuty integration
        return {
            'new_file': f"pagerduty_{data_type}_{timestamp}.{export_format}",
            'type': 'export',
            'service': 'pagerduty',
            'data_type': data_type,
            'timestamp': timestamp,
            'status': 'skipped',
            'reason': 'PagerDuty integration not yet implemented'
        }
    
    def _export_datadog_data(self, data_type: str, export_format: str, timestamp: str) -> Optional[Dict]:
        """Export Datadog data with timestamp"""
        # TODO: Implement Datadog integration
        return {
            'new_file': f"datadog_{data_type}_{timestamp}.{export_format}",
            'type': 'export',
            'service': 'datadog',
            'data_type': data_type,
            'timestamp': timestamp,
            'status': 'skipped',
            'reason': 'Datadog integration not yet implemented'
        }
    
    def _replicate_pdf_export(self, pattern: Dict, instruction: Dict, current_year: str) -> Optional[Dict]:
        """Export PDF document with timestamp"""
        # TODO: Implement PDF export (Confluence, GitHub)
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        
        return {
            'original_file': pattern.get('file_name'),
            'new_file': f"document_{timestamp}.pdf",
            'type': 'document',
            'format': 'pdf',
            'timestamp': timestamp,
            'status': 'skipped',
            'reason': 'PDF export not yet implemented'
        }
    
    def _generate_replication_summary(self, collected: List[Dict], 
                                     success_count: int, failure_count: int) -> str:
        """Generate human-readable summary"""
        total = success_count + failure_count
        
        summary_lines = [
            f"Collection Complete:",
            f"  ✅ Successful: {success_count}/{total}",
            f"  ❌ Failed: {failure_count}/{total}",
            f"",
            f"Evidence Collected:"
        ]
        
        # Group by type
        screenshots = [c for c in collected if c.get('type') == 'screenshot']
        exports = [c for c in collected if c.get('type') == 'export']
        documents = [c for c in collected if c.get('type') == 'document']
        
        if screenshots:
            summary_lines.append(f"  📸 Screenshots: {len(screenshots)}")
        if exports:
            summary_lines.append(f"  📊 Data Exports: {len(exports)}")
        if documents:
            summary_lines.append(f"  📄 Documents: {len(documents)}")
        
        return "\n".join(summary_lines)
    
    def _display_replication_summary(self, result: Dict):
        """Display replication summary"""
        console.print(f"\n[green]✅ Evidence Replication Complete for RFI {result['rfi_code']}[/green]\n")
        console.print(result['summary'])
        
        # Show uploaded files
        uploaded = [e for e in result['collected_evidence'] if e.get('uploaded')]
        if uploaded:
            console.print(f"\n[cyan]☁️  Uploaded to SharePoint:[/cyan]")
            for evidence in uploaded[:5]:  # Show first 5
                console.print(f"  ✅ {evidence.get('new_file')}")
            if len(uploaded) > 5:
                console.print(f"  ... and {len(uploaded) - 5} more files")

