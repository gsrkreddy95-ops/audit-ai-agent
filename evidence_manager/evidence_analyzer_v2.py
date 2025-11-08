"""
Evidence Analyzer V2 - Analyzes previous evidence and determines collection strategy
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from pathlib import Path
from rich.console import Console
from PIL import Image
import pytesseract

console = Console()


class EvidenceAnalyzerV2:
    """
    Analyzes previous audit evidence to understand what needs to be collected
    """
    
    def __init__(self):
        self.evidence_types = {
            'png': self._analyze_screenshot,
            'jpg': self._analyze_screenshot,
            'jpeg': self._analyze_screenshot,
            'pdf': self._analyze_pdf,
            'csv': self._analyze_csv,
            'json': self._analyze_json,
            'xlsx': self._analyze_excel,
            'xls': self._analyze_excel,
            'docx': self._analyze_word,
            'doc': self._analyze_word,
        }
    
    def analyze_file(self, file_path: str, file_name: str) -> Dict:
        """
        Analyze a single evidence file and determine collection strategy
        
        Returns:
            {
                'file_name': str,
                'file_type': str,
                'evidence_type': str,  # 'aws_screenshot', 'aws_export', 'document', etc.
                'source': str,  # 'aws_console', 'aws_api', 'jira', etc.
                'details': dict,  # Specific details about what to collect
                'collection_method': str,  # 'screenshot', 'api_export', 'manual', etc.
                'instructions': str  # Human-readable instructions
            }
        """
        file_ext = Path(file_name).suffix.lower().replace('.', '')
        
        if file_ext not in self.evidence_types:
            return {
                'file_name': file_name,
                'file_type': file_ext,
                'evidence_type': 'unknown',
                'source': 'unknown',
                'details': {},
                'collection_method': 'manual',
                'instructions': f"Unknown file type: {file_ext}"
            }
        
        analyzer = self.evidence_types[file_ext]
        return analyzer(file_path, file_name)
    
    def _analyze_screenshot(self, file_path: str, file_name: str) -> Dict:
        """Analyze screenshot to determine what AWS resource/page it shows"""
        console.print(f"[cyan]🔍 Analyzing screenshot: {file_name}...[/cyan]")
        
        result = {
            'file_name': file_name,
            'file_type': 'png',
            'evidence_type': 'screenshot',
            'source': 'unknown',
            'details': {},
            'collection_method': 'screenshot',
            'instructions': ''
        }
        
        # Analyze filename patterns
        name_lower = file_name.lower()
        
        # RDS patterns
        if 'rds' in name_lower:
            result['source'] = 'aws_console'
            result['details']['service'] = 'rds'
            
            # Determine cluster type
            if 'aurora' in name_lower:
                result['details']['cluster_type'] = 'aurora'
            elif 'conure' in name_lower:
                result['details']['cluster_type'] = 'conure'
            elif 'iroh' in name_lower:
                result['details']['cluster_type'] = 'iroh'
            
            # Determine region
            if 'apic' in name_lower:
                result['details']['region'] = 'apic'
                result['details']['aws_region'] = 'ap-southeast-1'  # Singapore
            elif 'eu' in name_lower:
                result['details']['region'] = 'eu'
                result['details']['aws_region'] = 'eu-west-1'  # Ireland
            elif 'nam' in name_lower:
                result['details']['region'] = 'nam'
                result['details']['aws_region'] = 'us-east-1'  # N. Virginia
            
            # Determine what aspect
            if 'multi az' in name_lower or 'multiaz' in name_lower:
                result['details']['aspect'] = 'multi_az_enabled'
                result['details']['aws_page'] = 'Configuration tab, Multi-AZ section'
            elif 'dashboard' in name_lower:
                result['details']['aspect'] = 'dashboard'
                result['details']['aws_page'] = 'RDS Dashboard'
            
            # Generate instructions
            cluster = result['details'].get('cluster_type', 'unknown').upper()
            region = result['details'].get('region', 'unknown').upper()
            aws_region = result['details'].get('aws_region', 'unknown')
            aspect = result['details'].get('aspect', 'configuration')
            
            result['instructions'] = (
                f"Take screenshot of RDS {cluster} cluster in {region} ({aws_region})\n"
                f"Navigate to: AWS Console > RDS > Databases > {cluster} > {aspect}\n"
                f"Ensure Multi-AZ status is visible"
            )
        
        # S3 patterns
        elif 's3' in name_lower:
            result['source'] = 'aws_console'
            result['details']['service'] = 's3'
            
            if 'bucket' in name_lower or 'list' in name_lower:
                result['details']['aspect'] = 'bucket_list'
                result['instructions'] = (
                    "Take scrolling screenshot of S3 bucket list\n"
                    "Navigate to: AWS Console > S3 > Buckets\n"
                    "Capture all buckets with scrolling"
                )
            elif 'versioning' in name_lower:
                result['details']['aspect'] = 'versioning'
                result['instructions'] = "Screenshot S3 bucket versioning configuration"
            elif 'encryption' in name_lower:
                result['details']['aspect'] = 'encryption'
                result['instructions'] = "Screenshot S3 bucket encryption settings"
        
        # IAM patterns
        elif 'iam' in name_lower:
            result['source'] = 'aws_console'
            result['details']['service'] = 'iam'
            
            if 'user' in name_lower:
                result['details']['aspect'] = 'users'
                result['instructions'] = (
                    "Take screenshot of IAM users list\n"
                    "Navigate to: AWS Console > IAM > Users"
                )
            elif 'role' in name_lower:
                result['details']['aspect'] = 'roles'
                result['instructions'] = "Screenshot IAM roles list"
            elif 'policy' in name_lower:
                result['details']['aspect'] = 'policies'
                result['instructions'] = "Screenshot IAM policies"
        
        # EC2 patterns
        elif 'ec2' in name_lower:
            result['source'] = 'aws_console'
            result['details']['service'] = 'ec2'
            
            if 'instance' in name_lower:
                result['details']['aspect'] = 'instances'
                result['instructions'] = "Screenshot EC2 instances list"
            elif 'security' in name_lower and 'group' in name_lower:
                result['details']['aspect'] = 'security_groups'
                result['instructions'] = "Screenshot EC2 security groups"
        
        # VPC patterns
        elif 'vpc' in name_lower:
            result['source'] = 'aws_console'
            result['details']['service'] = 'vpc'
            result['instructions'] = "Screenshot VPC configuration"
        
        # CloudWatch patterns
        elif 'cloudwatch' in name_lower:
            result['source'] = 'aws_console'
            result['details']['service'] = 'cloudwatch'
            result['instructions'] = "Screenshot CloudWatch dashboard/alarms"
        
        # If still unknown, try OCR
        if result['source'] == 'unknown' and os.path.exists(file_path):
            try:
                console.print(f"[yellow]Attempting OCR on {file_name}...[/yellow]")
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                
                # Look for AWS service names in OCR text
                text_lower = text.lower()
                if 'rds' in text_lower or 'database' in text_lower:
                    result['source'] = 'aws_console'
                    result['details']['service'] = 'rds'
                    result['instructions'] = "Screenshot RDS resource (identified via OCR)"
                elif 's3' in text_lower:
                    result['source'] = 'aws_console'
                    result['details']['service'] = 's3'
                elif 'iam' in text_lower:
                    result['source'] = 'aws_console'
                    result['details']['service'] = 'iam'
                
                console.print(f"[green]✅ OCR analysis complete[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️ OCR failed: {e}[/yellow]")
        
        return result
    
    def _analyze_pdf(self, file_path: str, file_name: str) -> Dict:
        """Analyze PDF document"""
        return {
            'file_name': file_name,
            'file_type': 'pdf',
            'evidence_type': 'document',
            'source': 'manual',
            'details': {},
            'collection_method': 'document_export',
            'instructions': f"Export/generate PDF similar to: {file_name}"
        }
    
    def _analyze_csv(self, file_path: str, file_name: str) -> Dict:
        """Analyze CSV export"""
        name_lower = file_name.lower()
        
        result = {
            'file_name': file_name,
            'file_type': 'csv',
            'evidence_type': 'data_export',
            'source': 'aws_api',
            'details': {},
            'collection_method': 'api_export',
            'instructions': ''
        }
        
        # Determine what data
        if 'user' in name_lower or 'iam' in name_lower:
            result['details']['export_type'] = 'iam_users'
            result['instructions'] = "Export IAM users to CSV via AWS API"
        elif 's3' in name_lower and 'bucket' in name_lower:
            result['details']['export_type'] = 's3_buckets'
            result['instructions'] = "Export S3 buckets list to CSV"
        elif 'rds' in name_lower or 'database' in name_lower:
            result['details']['export_type'] = 'rds_instances'
            result['instructions'] = "Export RDS instances/clusters to CSV"
        elif 'ec2' in name_lower:
            result['details']['export_type'] = 'ec2_instances'
            result['instructions'] = "Export EC2 instances to CSV"
        
        return result
    
    def _analyze_json(self, file_path: str, file_name: str) -> Dict:
        """Analyze JSON export"""
        return {
            'file_name': file_name,
            'file_type': 'json',
            'evidence_type': 'api_export',
            'source': 'api',
            'details': {},
            'collection_method': 'api_call',
            'instructions': f"Export data to JSON format similar to: {file_name}"
        }
    
    def _analyze_excel(self, file_path: str, file_name: str) -> Dict:
        """Analyze Excel export"""
        return {
            'file_name': file_name,
            'file_type': 'xlsx',
            'evidence_type': 'data_export',
            'source': 'export',
            'details': {},
            'collection_method': 'export',
            'instructions': f"Export data to Excel format similar to: {file_name}"
        }
    
    def _analyze_word(self, file_path: str, file_name: str) -> Dict:
        """Analyze Word document"""
        return {
            'file_name': file_name,
            'file_type': 'docx',
            'evidence_type': 'explanation',
            'source': 'manual',
            'details': {},
            'collection_method': 'document',
            'instructions': f"Create explanation document (Word) - verify conditions and generate new explanation"
        }
    
    def analyze_rfi_folder(self, files: List[Dict]) -> Dict:
        """
        Analyze all files in an RFI folder and create collection plan
        
        Args:
            files: List of {name, type, modified, url, local_path (optional)}
        
        Returns:
            {
                'total_files': int,
                'by_type': dict,
                'collection_tasks': list,
                'summary': str
            }
        """
        console.print(f"\n[cyan]📊 Analyzing {len(files)} files...[/cyan]\n")
        
        by_type = {}
        collection_tasks = []
        
        for file in files:
            file_name = file['name']
            file_ext = Path(file_name).suffix.lower().replace('.', '')
            
            # Skip folders
            if file['type'] == 'folder':
                continue
            
            # Count by type
            if file_ext not in by_type:
                by_type[file_ext] = []
            by_type[file_ext].append(file_name)
            
            # Analyze file with actual content if local_path is available
            local_path = file.get('local_path', '')
            if local_path and os.path.exists(local_path):
                console.print(f"[dim]  📄 Analyzing: {file_name}...[/dim]")
                analysis = self.analyze_file(local_path, file_name)
            else:
                # Fallback to filename-based analysis
                console.print(f"[dim]  📄 Filename-based analysis: {file_name}...[/dim]")
                analysis = self.analyze_file('', file_name)
            
            collection_tasks.append({
                'file_name': file_name,
                'analysis': analysis
            })
        
        # Generate summary
        summary_lines = [
            f"📁 **Found {len(files)} files:**",
            ""
        ]
        
        for ext, file_list in by_type.items():
            summary_lines.append(f"  • {len(file_list)} {ext.upper()} files")
        
        # Determine primary format
        if by_type:
            primary_format = max(by_type.items(), key=lambda x: len(x[1]))
            format_name = primary_format[0].upper()
            format_count = len(primary_format[1])
            
            summary_lines.append("")
            summary_lines.append("⚠️ **IMPORTANT - Match Previous Format:**")
            
            if format_name in ['PNG', 'JPG', 'JPEG']:
                summary_lines.append(f"  ✅ Primary format: SCREENSHOTS ({format_count} {format_name} files)")
                summary_lines.append(f"  🎯 You MUST collect: AWS Console Screenshots")
                summary_lines.append(f"  ❌ Do NOT collect: CSV exports, JSON exports, or other formats")
            elif format_name in ['CSV', 'XLSX', 'XLS']:
                summary_lines.append(f"  ✅ Primary format: DATA EXPORTS ({format_count} {format_name} files)")
                summary_lines.append(f"  🎯 You MUST collect: API data exports as CSV/Excel")
                summary_lines.append(f"  ❌ Do NOT collect: Screenshots or other formats")
            elif format_name in ['DOCX', 'DOC']:
                summary_lines.append(f"  ✅ Primary format: DOCUMENTS ({format_count} Word files)")
                summary_lines.append(f"  🎯 You MUST collect: Word documents with similar content")
                summary_lines.append(f"  ❌ Do NOT collect: Screenshots, CSV, or other formats")
            elif format_name == 'PDF':
                summary_lines.append(f"  ✅ Primary format: PDF ({format_count} files)")
                summary_lines.append(f"  🎯 You MUST collect: PDF exports or documents")
                summary_lines.append(f"  ❌ Do NOT collect: Screenshots, CSV, or other formats")
        
        summary_lines.append("")
        summary_lines.append("🎯 **Collection Strategy:**")
        summary_lines.append("")
        
        # Group by source
        by_source = {}
        for task in collection_tasks:
            source = task['analysis']['source']
            if source not in by_source:
                by_source[source] = []
            by_source[source].append(task)
        
        for source, tasks in by_source.items():
            summary_lines.append(f"  **{source.upper()}:** {len(tasks)} items")
            for task in tasks[:3]:  # Show first 3
                summary_lines.append(f"    - {task['analysis']['instructions'][:80]}...")
            if len(tasks) > 3:
                summary_lines.append(f"    ... and {len(tasks) - 3} more")
            summary_lines.append("")
        
        return {
            'total_files': len(files),
            'by_type': by_type,
            'collection_tasks': collection_tasks,
            'summary': '\n'.join(summary_lines)
        }

