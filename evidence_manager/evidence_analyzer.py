"""
Evidence Analyzer - Reviews previous year's evidence and learns patterns
Analyzes screenshots, PDFs, CSVs, Excel, JSON, etc. to understand what was collected
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import pandas as pd
import json
from PIL import Image
import pytesseract  # OCR for screenshots
from PyPDF2 import PdfReader
from rich.console import Console
from rich.table import Table

console = Console()


class EvidenceAnalyzer:
    """
    Analyzes previous audit evidence to understand collection patterns
    Determines what needs to be collected for current year
    """
    
    def __init__(self, sharepoint_integration):
        self.sharepoint = sharepoint_integration
        self.evidence_patterns = {}
    
    def analyze_rfi_folder(self, rfi_code: str, product: Optional[str] = None, 
                          previous_year: str = "FY24") -> Dict[str, Any]:
        """
        Analyze previous year's evidence in RFI folder
        Returns: Pattern of what was collected and how to replicate
        
        Example:
        {
            'rfi_code': '10.1.2.12',
            'product': 'XDR',
            'previous_year': 'FY24',
            'evidence_found': [
                {
                    'file_name': 'aws_ctr-int_rds_prod-cluster_config_2024-03-15_10-30-00.png',
                    'type': 'screenshot',
                    'source': 'aws',
                    'service': 'rds',
                    'resource': 'prod-cluster',
                    'account': 'ctr-int',
                    'region': 'us-east-1',
                    'timestamp': '2024-03-15 10:30:00',
                    'content_analysis': 'RDS cluster configuration page',
                    'replication_instruction': {
                        'action': 'screenshot',
                        'target': 'aws_console',
                        'service': 'rds',
                        'page': 'cluster_configuration',
                        'resource': 'prod-cluster',
                        'account': 'ctr-int'
                    }
                },
                {
                    'file_name': 'iam_users_all_accounts_2024-03-15.xlsx',
                    'type': 'data_export',
                    'source': 'aws',
                    'service': 'iam',
                    'format': 'excel',
                    'accounts': ['ctr-int', 'ctr-prod', 'sxo101'],
                    'timestamp': '2024-03-15',
                    'content_analysis': 'IAM users across 3 accounts',
                    'replication_instruction': {
                        'action': 'export',
                        'target': 'aws_api',
                        'service': 'iam',
                        'function': 'list_users',
                        'accounts': ['ctr-int', 'ctr-prod', 'sxo101'],
                        'format': 'excel'
                    }
                }
            ],
            'collection_summary': {
                'total_files': 15,
                'screenshots': 8,
                'excel_exports': 5,
                'pdfs': 2,
                'services_covered': ['aws-rds', 'aws-iam', 'pagerduty'],
                'recommended_replication': [
                    'Collect RDS screenshots from ctr-int',
                    'Export IAM users from 3 accounts',
                    'Get PagerDuty incidents from Q1'
                ]
            }
        }
        """
        console.print(f"\n[cyan]🔍 Analyzing RFI {rfi_code} evidence from {previous_year}...[/cyan]")
        
        # Find RFI folder in SharePoint
        rfi_folder = self.sharepoint.find_rfi_folder(rfi_code, product)
        
        if not rfi_folder:
            console.print(f"[yellow]⚠️  RFI folder {rfi_code} not found[/yellow]")
            return {}
        
        # Get metadata of previous year's evidence (DO NOT DOWNLOAD FILES)
        evidence_metadata = self._get_previous_evidence_metadata(rfi_folder, previous_year)
        
        if not evidence_metadata:
            console.print(f"[yellow]⚠️  No {previous_year} evidence found in RFI {rfi_code}[/yellow]")
            return {}
        
        # Analyze each file's metadata (filename, type, size)
        analyzed_evidence = []
        for file_meta in evidence_metadata:
            analysis = self._analyze_evidence_metadata(file_meta)
            if analysis:
                analyzed_evidence.append(analysis)
        
        # Generate collection summary and replication instructions
        summary = self._generate_collection_summary(analyzed_evidence)
        
        result = {
            'rfi_code': rfi_code,
            'product': product,
            'previous_year': previous_year,
            'evidence_found': analyzed_evidence,
            'collection_summary': summary
        }
        
        # Display summary
        self._display_analysis_summary(result)
        
        return result
    
    def _get_previous_evidence_metadata(self, rfi_folder: Dict, previous_year: str) -> List[Dict]:
        """
        Get metadata of previous year's evidence from SharePoint (DO NOT DOWNLOAD)
        Only fetch filenames, types, sizes, upload dates - NOT the actual files
        Returns: List of file metadata
        """
        # Call SharePoint API to LIST files (not download)
        # Get: filename, file_type, size, modified_date, uploaded_by
        
        console.print(f"[cyan]📋 Fetching FY{previous_year} evidence metadata (not downloading files)...[/cyan]")
        
        # TODO: Implement SharePoint file listing API
        # Example result:
        # [
        #     {
        #         'name': 'XDR_KMS_Keys_Generated_2024-03-15.png',
        #         'type': 'image/png',
        #         'size': 245678,
        #         'modified': '2024-03-15T10:30:00Z'
        #     },
        #     {
        #         'name': 'insights_ismap.docx',
        #         'type': 'application/docx',
        #         'size': 15234,
        #         'modified': '2024-03-18T14:20:00Z'
        #     }
        # ]
        
        console.print(f"[yellow]⚠️  SharePoint metadata listing not yet implemented[/yellow]")
        return []
    
    def _analyze_evidence_metadata(self, file_meta: Dict) -> Optional[Dict]:
        """
        Analyze evidence file metadata ONLY (no file download)
        Parse filename to understand what needs to be collected
        
        Args:
            file_meta: {'name': '...', 'type': '...', 'size': ..., 'modified': '...'}
        """
        file_name = file_meta.get('name', '')
        file_type = file_meta.get('type', '')
        file_size = file_meta.get('size', 0)
        
        # Determine file extension from name or type
        file_ext = Path(file_name).suffix.lower()
        
        analysis = {
            'file_name': file_name,
            'file_type': file_ext,
            'file_size': file_size,
            'timestamp': self._extract_timestamp_from_filename(file_name)
        }
        
        # Analyze based on file type (METADATA ONLY - NO FILE DOWNLOAD)
        if file_ext in ['.png', '.jpg', '.jpeg', '.sh']:
            # Screenshot - parse filename pattern
            analysis.update(self._analyze_screenshot_metadata(file_name))
        
        elif file_ext in ['.xlsx', '.xls', '.csv']:
            # Data export - parse filename pattern
            analysis.update(self._analyze_export_metadata(file_name))
        
        elif file_ext in ['.pdf']:
            # PDF document - parse filename
            analysis.update(self._analyze_pdf_metadata(file_name))
        
        elif file_ext in ['.docx', '.doc']:
            # Word document - likely explanation or policy
            analysis.update(self._analyze_word_metadata(file_name))
        
        elif file_ext == '.json':
            # JSON export - parse filename
            analysis.update(self._analyze_json_metadata(file_name))
        
        else:
            analysis['type'] = 'unknown'
            analysis['replication_instruction'] = None
        
        return analysis
    
    def _analyze_screenshot_metadata(self, file_name: str) -> Dict:
        """
        Analyze screenshot metadata from filename ONLY (no file download, no OCR)
        Parse filename pattern to understand what needs to be collected
        
        Example patterns:
        - XDR_KMS_Keys_Generated_2024-03-15.png
        - aws_ctr-int_rds_prod-cluster_config_2024-03-15_10-30-00.png
        - XDR_Platform_KMS_Keys_History_June_1_Aug_31.docx (screenshot as doc)
        """
        
        # Pattern 1: Product_Service_Description_Date.ext
        # Example: XDR_KMS_Keys_Generated_2024-03-15.png
        pattern1 = r'([A-Z]+)_([A-Z\-]+)_([A-Za-z_\-]+)_(\d{4}-\d{2}-\d{2})'
        match1 = re.match(pattern1, file_name)
        
        if match1:
            product, service, description, date = match1.groups()
            return {
                'type': 'screenshot',
                'product': product,
                'service': service,
                'description': description.replace('_', ' '),
                'collection_date': date,
                'content_analysis': f'{product} {service} - {description.replace("_", " ")}',
                'replication_instruction': {
                    'action': 'screenshot',
                    'target': 'console_or_api',
                    'product': product,
                    'service': service,
                    'description': description,
                    'collect_fresh': True,  # Always collect fresh, never copy
                    'naming_pattern': f'{product}_{service}_{description}_{{timestamp}}'
                }
            }
        
        # Pattern 2: aws_account_service_resource_page_timestamp.ext
        pattern2 = r'([a-z]+)_([a-z\-]+)_([a-z0-9\-]+)_([a-z0-9\-]+)_([a-z_]+)_(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'
        match = re.match(pattern2, file_name)
        
        if match:
            source, account, service, resource, page, timestamp = match.groups()
            
            return {
                'type': 'screenshot',
                'source': source,
                'account': account,
                'service': service,
                'resource': resource,
                'page': page,
                'content_analysis': f'{service.upper()} {page.replace("_", " ")} for {resource}',
                'replication_instruction': {
                    'action': 'screenshot',
                    'target': f'{source}_console',
                    'service': service,
                    'resource': resource,
                    'page': page,
                    'account': account
                }
            }
        
        # Fallback: Try OCR to understand content
        try:
            img = Image.open(file_path)
            text = pytesseract.image_to_string(img)
            
            # Detect service from OCR text
            service = self._detect_service_from_text(text)
            
            return {
                'type': 'screenshot',
                'content_analysis': f'Screenshot containing: {service}',
                'ocr_text': text[:200],  # First 200 chars
                'replication_instruction': {
                    'action': 'screenshot',
                    'target': 'manual_review_needed',
                    'note': 'Could not automatically parse filename'
                }
            }
        except Exception as e:
            console.print(f"[yellow]⚠️  OCR failed for {file_name}: {e}[/yellow]")
            return {'type': 'screenshot', 'content_analysis': 'Unknown'}
    
    def _analyze_excel(self, file_path: str) -> Dict:
        """
        Analyze Excel file to determine what data was exported
        """
        try:
            # Read Excel file
            df = pd.read_excel(file_path, sheet_name=0)
            
            # Get sheet names
            xls = pd.ExcelFile(file_path)
            sheet_names = xls.sheet_names
            
            # Analyze columns to determine data type
            columns = df.columns.tolist()
            num_rows = len(df)
            
            # Detect what kind of data this is
            data_type = self._detect_data_type_from_columns(columns)
            
            # Parse filename for metadata
            file_name = Path(file_path).name
            service = self._extract_service_from_filename(file_name)
            accounts = self._extract_accounts_from_excel(df)
            
            return {
                'type': 'data_export',
                'format': 'excel',
                'source': 'aws' if 'aws' in file_name.lower() else 'unknown',
                'service': service,
                'data_type': data_type,
                'num_sheets': len(sheet_names),
                'num_rows': num_rows,
                'columns': columns,
                'accounts': accounts,
                'content_analysis': f'{data_type} data export with {num_rows} rows',
                'replication_instruction': {
                    'action': 'export',
                    'target': 'api',
                    'service': service,
                    'data_type': data_type,
                    'accounts': accounts,
                    'format': 'excel'
                }
            }
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Excel analysis failed: {e}[/yellow]")
            return {'type': 'data_export', 'format': 'excel', 'content_analysis': 'Unknown'}
    
    def _analyze_csv(self, file_path: str) -> Dict:
        """Analyze CSV file"""
        try:
            df = pd.read_csv(file_path)
            return self._analyze_dataframe(df, file_path, 'csv')
        except Exception as e:
            return {'type': 'data_export', 'format': 'csv', 'error': str(e)}
    
    def _analyze_pdf(self, file_path: str) -> Dict:
        """Analyze PDF document"""
        try:
            reader = PdfReader(file_path)
            num_pages = len(reader.pages)
            
            # Extract first page text
            first_page_text = reader.pages[0].extract_text()
            
            # Determine document type
            doc_type = self._detect_document_type_from_text(first_page_text)
            
            return {
                'type': 'document',
                'format': 'pdf',
                'num_pages': num_pages,
                'doc_type': doc_type,
                'content_analysis': f'{doc_type} PDF with {num_pages} pages',
                'replication_instruction': {
                    'action': 'export_pdf',
                    'target': 'confluence_or_github',
                    'doc_type': doc_type
                }
            }
        
        except Exception as e:
            return {'type': 'document', 'format': 'pdf', 'error': str(e)}
    
    def _analyze_json(self, file_path: str) -> Dict:
        """Analyze JSON file"""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Determine what kind of JSON data this is
            keys = list(data.keys()) if isinstance(data, dict) else []
            
            return {
                'type': 'data_export',
                'format': 'json',
                'keys': keys,
                'content_analysis': f'JSON data with keys: {", ".join(keys[:5])}',
                'replication_instruction': {
                    'action': 'export',
                    'format': 'json'
                }
            }
        
        except Exception as e:
            return {'type': 'data_export', 'format': 'json', 'error': str(e)}
    
    def _extract_timestamp_from_filename(self, filename: str) -> Optional[str]:
        """Extract timestamp from filename"""
        # Pattern 1: YYYY-MM-DD_HH-MM-SS
        pattern1 = r'(\d{4}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})'
        
        # Pattern 2: YYYY-MM-DD
        pattern2 = r'(\d{4}-\d{2}-\d{2})'
        
        match = re.search(pattern1, filename) or re.search(pattern2, filename)
        return match.group(1) if match else None
    
    def _detect_service_from_text(self, text: str) -> str:
        """Detect service from OCR text"""
        text_lower = text.lower()
        
        services = {
            'rds': ['rds', 'relational database', 'database cluster'],
            'ec2': ['ec2', 'instances', 'elastic compute'],
            'iam': ['iam', 'identity', 'access management', 'users', 'roles'],
            's3': ['s3', 'bucket', 'simple storage'],
            'cloudtrail': ['cloudtrail', 'trail', 'logging'],
            'pagerduty': ['pagerduty', 'incident', 'on-call'],
            'datadog': ['datadog', 'monitoring', 'metrics'],
            'kibana': ['kibana', 'elasticsearch', 'logs']
        }
        
        for service, keywords in services.items():
            if any(keyword in text_lower for keyword in keywords):
                return service
        
        return 'unknown'
    
    def _detect_data_type_from_columns(self, columns: List[str]) -> str:
        """Detect data type from Excel/CSV columns"""
        columns_lower = [col.lower() for col in columns]
        
        if any('user' in col for col in columns_lower):
            if any('mfa' in col or 'accesskey' in col for col in columns_lower):
                return 'iam_users'
        
        if any('instance' in col for col in columns_lower):
            if any('db' in col or 'cluster' in col for col in columns_lower):
                return 'rds_instances'
            else:
                return 'ec2_instances'
        
        if any('bucket' in col for col in columns_lower):
            return 's3_buckets'
        
        if any('incident' in col for col in columns_lower):
            return 'incidents'
        
        return 'unknown'
    
    def _extract_service_from_filename(self, filename: str) -> str:
        """Extract service name from filename"""
        filename_lower = filename.lower()
        
        if 'rds' in filename_lower:
            return 'rds'
        elif 'iam' in filename_lower:
            return 'iam'
        elif 'ec2' in filename_lower:
            return 'ec2'
        elif 's3' in filename_lower:
            return 's3'
        elif 'pagerduty' in filename_lower or 'incident' in filename_lower:
            return 'pagerduty'
        
        return 'unknown'
    
    def _extract_accounts_from_excel(self, df: pd.DataFrame) -> List[str]:
        """Extract AWS account names from Excel data"""
        if 'Account' in df.columns:
            return df['Account'].unique().tolist()
        return []
    
    def _detect_document_type_from_text(self, text: str) -> str:
        """Detect document type from PDF text"""
        text_lower = text.lower()
        
        if 'policy' in text_lower or 'procedure' in text_lower:
            return 'policy_document'
        elif 'runbook' in text_lower or 'playbook' in text_lower:
            return 'runbook'
        elif 'incident' in text_lower:
            return 'incident_report'
        
        return 'document'
    
    def _analyze_dataframe(self, df: pd.DataFrame, file_path: str, format: str) -> Dict:
        """Generic dataframe analysis"""
        columns = df.columns.tolist()
        num_rows = len(df)
        data_type = self._detect_data_type_from_columns(columns)
        
        return {
            'type': 'data_export',
            'format': format,
            'data_type': data_type,
            'num_rows': num_rows,
            'columns': columns,
            'content_analysis': f'{data_type} with {num_rows} rows'
        }
    
    def _generate_collection_summary(self, analyzed_evidence: List[Dict]) -> Dict:
        """Generate summary of what was collected"""
        total_files = len(analyzed_evidence)
        
        # Count by type
        screenshots = sum(1 for e in analyzed_evidence if e.get('type') == 'screenshot')
        excel_exports = sum(1 for e in analyzed_evidence if e.get('format') == 'excel')
        csv_exports = sum(1 for e in analyzed_evidence if e.get('format') == 'csv')
        pdfs = sum(1 for e in analyzed_evidence if e.get('format') == 'pdf')
        
        # Extract services covered
        services_covered = set()
        for evidence in analyzed_evidence:
            if 'service' in evidence:
                service = evidence.get('source', 'unknown') + '-' + evidence['service']
                services_covered.add(service)
        
        # Generate replication recommendations
        recommendations = []
        for evidence in analyzed_evidence:
            if 'replication_instruction' in evidence and evidence['replication_instruction']:
                instr = evidence['replication_instruction']
                if instr.get('action') == 'screenshot':
                    rec = f"Screenshot: {instr.get('service')} {instr.get('page')} for {instr.get('resource')}"
                    recommendations.append(rec)
                elif instr.get('action') == 'export':
                    rec = f"Export: {instr.get('service')} {instr.get('data_type')} to {instr.get('format')}"
                    recommendations.append(rec)
        
        return {
            'total_files': total_files,
            'screenshots': screenshots,
            'excel_exports': excel_exports,
            'csv_exports': csv_exports,
            'pdfs': pdfs,
            'services_covered': list(services_covered),
            'recommended_replication': recommendations[:10]  # Top 10
        }
    
    def _display_analysis_summary(self, result: Dict):
        """Display analysis summary in nice format"""
        console.print(f"\n[green]✅ Analysis Complete for RFI {result['rfi_code']}[/green]\n")
        
        summary = result['collection_summary']
        
        # Create table
        table = Table(title="Evidence Summary")
        table.add_column("Category", style="cyan")
        table.add_column("Count", style="magenta")
        
        table.add_row("Total Files", str(summary['total_files']))
        table.add_row("Screenshots", str(summary['screenshots']))
        table.add_row("Excel Exports", str(summary['excel_exports']))
        table.add_row("CSV Exports", str(summary['csv_exports']))
        table.add_row("PDF Documents", str(summary['pdfs']))
        
        console.print(table)
        
        # Services covered
        console.print(f"\n[cyan]📊 Services Covered:[/cyan]")
        for service in summary['services_covered']:
            console.print(f"  - {service}")
        
        # Recommendations
        console.print(f"\n[cyan]🎯 Replication Recommendations:[/cyan]")
        for i, rec in enumerate(summary['recommended_replication'][:5], 1):
            console.print(f"  {i}. {rec}")

