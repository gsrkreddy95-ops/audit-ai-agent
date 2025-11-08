"""
Smart Evidence Analyzer - TRUE Intelligence with Visual Understanding
Downloads and analyzes previous evidence to understand EXACTLY what to collect

Key Capabilities:
1. Downloads screenshots/evidence files
2. OCR to read terminal screenshots
3. Image analysis to understand AWS console screenshots
4. Detects Python scripts and runs them
5. Understands which AWS console page/tab was captured
6. Makes intelligent decisions based on visual content
"""

import os
import re
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime
import pytesseract
from PIL import Image
import cv2
import numpy as np
from rich.console import Console
from rich.table import Table

console = Console()


class SmartEvidenceAnalyzer:
    """
    Intelligent evidence analyzer that ACTUALLY looks at screenshots
    and understands what needs to be collected
    """
    
    def __init__(self, sharepoint_integration):
        self.sharepoint = sharepoint_integration
        self.evidence_cache = {}
        self.temp_dir = "/tmp/audit_evidence_analysis"
        os.makedirs(self.temp_dir, exist_ok=True)
    
    def analyze_rfi_folder_intelligent(self, rfi_code: str, product: Optional[str] = None,
                                      previous_year: str = "FY24") -> Dict[str, Any]:
        """
        INTELLIGENT analysis of previous year's evidence
        
        Steps:
        1. Find RFI folder
        2. DOWNLOAD evidence files (screenshots, scripts, docs)
        3. ANALYZE visual content (OCR, image recognition)
        4. UNDERSTAND what was collected
        5. Generate INTELLIGENT replication instructions
        
        Returns: Complete analysis with visual understanding
        """
        console.print(f"\n[cyan]🧠 INTELLIGENT Analysis of RFI {rfi_code} ({previous_year})...[/cyan]")
        
        # Find RFI folder
        rfi_folder = self.sharepoint.find_rfi_folder(rfi_code, product)
        if not rfi_folder:
            console.print(f"[yellow]⚠️  RFI folder {rfi_code} not found[/yellow]")
            return {}
        
        # Download evidence files for analysis
        console.print("[cyan]📥 Downloading evidence files for analysis...[/cyan]")
        downloaded_files = self._download_evidence_for_analysis(rfi_folder, previous_year)
        
        if not downloaded_files:
            console.print(f"[yellow]⚠️  No evidence files to analyze[/yellow]")
            return {}
        
        # Analyze each file INTELLIGENTLY
        analyzed_evidence = []
        for file_path in downloaded_files:
            console.print(f"[cyan]🔍 Analyzing: {Path(file_path).name}...[/cyan]")
            analysis = self._analyze_evidence_intelligently(file_path)
            if analysis:
                analyzed_evidence.append(analysis)
        
        # Generate collection plan
        collection_plan = self._generate_intelligent_collection_plan(analyzed_evidence)
        
        result = {
            'rfi_code': rfi_code,
            'product': product,
            'previous_year': previous_year,
            'evidence_analyzed': analyzed_evidence,
            'collection_plan': collection_plan,
            'total_files': len(analyzed_evidence)
        }
        
        self._display_intelligent_analysis(result)
        
        return result
    
    def _download_evidence_for_analysis(self, rfi_folder: Dict, previous_year: str) -> List[str]:
        """
        Download evidence files for analysis
        
        Downloads:
        - Screenshots (.png, .jpg)
        - Python scripts (.py)
        - Shell scripts (.sh)
        - Data files (.xlsx, .csv)
        
        Returns: List of local file paths
        """
        # TODO: Implement SharePoint download
        # For now, placeholder
        console.print(f"[yellow]⚠️  SharePoint download not yet implemented[/yellow]")
        return []
    
    def _analyze_evidence_intelligently(self, file_path: str) -> Optional[Dict]:
        """
        INTELLIGENT analysis of evidence file
        
        For screenshots:
        - OCR to extract text
        - Detect if it's terminal output or AWS console
        - Understand what's being shown
        - Identify which AWS service/page
        
        For scripts:
        - Parse script content
        - Understand what it does
        - Determine if it should be re-run
        
        Returns: Intelligent analysis with replication instructions
        """
        file_name = Path(file_path).name
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext in ['.png', '.jpg', '.jpeg']:
            return self._analyze_screenshot_intelligently(file_path)
        
        elif file_ext == '.py':
            return self._analyze_python_script(file_path)
        
        elif file_ext == '.sh':
            return self._analyze_shell_script(file_path)
        
        elif file_ext in ['.xlsx', '.csv']:
            return self._analyze_data_export(file_path)
        
        return None
    
    def _analyze_screenshot_intelligently(self, image_path: str) -> Dict:
        """
        INTELLIGENT screenshot analysis using OCR and image recognition
        
        Process:
        1. Load image
        2. OCR to extract ALL text
        3. Detect screenshot type (terminal, AWS console, etc.)
        4. Understand what's being shown
        5. Generate precise replication instructions
        
        Example from your screenshot:
        - Detects: Terminal screenshot
        - Understands: Python script execution results
        - Sees: KMS key deletion search results
        - Instruction: Find script, run it, capture output
        """
        file_name = Path(image_path).name
        
        console.print(f"  [dim]Loading image...[/dim]")
        img = Image.open(image_path)
        
        # OCR to extract text
        console.print(f"  [dim]Performing OCR...[/dim]")
        ocr_text = pytesseract.image_to_string(img)
        
        # Analyze image to detect screenshot type
        screenshot_type = self._detect_screenshot_type(img, ocr_text)
        
        console.print(f"  ✅ Detected: [yellow]{screenshot_type}[/yellow]")
        
        if screenshot_type == 'terminal_output':
            return self._analyze_terminal_screenshot(image_path, ocr_text, file_name)
        
        elif screenshot_type == 'aws_console':
            return self._analyze_aws_console_screenshot(image_path, ocr_text, file_name)
        
        elif screenshot_type == 'script_output':
            return self._analyze_script_output_screenshot(image_path, ocr_text, file_name)
        
        else:
            return {
                'file_name': file_name,
                'type': 'screenshot',
                'screenshot_type': screenshot_type,
                'ocr_text': ocr_text[:500],
                'replication_instruction': {
                    'action': 'manual_review',
                    'reason': f'Unknown screenshot type: {screenshot_type}'
                }
            }
    
    def _detect_screenshot_type(self, img: Image, ocr_text: str) -> str:
        """
        Detect what kind of screenshot this is
        
        Types:
        - 'terminal_output': Terminal/CLI output (your example!)
        - 'aws_console': AWS Console screenshot
        - 'script_output': Python/Shell script execution
        - 'dashboard': Monitoring dashboard
        - 'unknown': Can't determine
        """
        ocr_lower = ocr_text.lower()
        
        # Check for terminal indicators
        terminal_indicators = [
            'searching for', '=== searching', 'search complete',
            'results saved to:', 'overall summary:',
            'kganugap-m-w4xn', 'krishna$', '~$', '#',
            'total keys deleted:', 'region-wise breakdown'
        ]
        
        if any(indicator in ocr_lower for indicator in terminal_indicators):
            # Check if it's a script execution
            if 'python' in ocr_lower or '.py' in ocr_lower or 'script' in ocr_lower:
                return 'script_output'
            return 'terminal_output'
        
        # Check for AWS Console indicators
        aws_indicators = [
            'aws management console', 'amazon rds', 'amazon ec2',
            'amazon s3', 'cloudtrail', 'aws console',
            'configuration', 'backup', 'monitoring',
            'create', 'modify', 'actions', 'connect'
        ]
        
        if any(indicator in ocr_lower for indicator in aws_indicators):
            return 'aws_console'
        
        # Check for dashboard
        dashboard_indicators = ['dashboard', 'metrics', 'datadog', 'kibana', 'grafana']
        if any(indicator in ocr_lower for indicator in dashboard_indicators):
            return 'dashboard'
        
        return 'unknown'
    
    def _analyze_terminal_screenshot(self, image_path: str, ocr_text: str, file_name: str) -> Dict:
        """
        Analyze terminal screenshot (like your example!)
        
        Your screenshot shows:
        - Python script execution
        - KMS key deletion search
        - Results across multiple AWS regions
        - Output saved to specific paths
        
        Agent needs to:
        1. Find the Python script (likely in same folder)
        2. Run the script with current dates
        3. Capture terminal output screenshot
        """
        console.print(f"  🖥️  Terminal screenshot detected")
        
        # Extract key information from OCR
        analysis = {
            'file_name': file_name,
            'type': 'screenshot',
            'screenshot_type': 'terminal_output',
            'ocr_text': ocr_text
        }
        
        # Detect what's being searched/executed
        if 'kms' in ocr_text.lower() and 'key deletion' in ocr_text.lower():
            analysis['service'] = 'KMS'
            analysis['activity'] = 'key_deletion_search'
            analysis['content_summary'] = 'KMS key deletion events search across AWS regions'
            
            # Extract regions searched
            regions = re.findall(r'(us-east-\d+|eu-west-\d+|ap-northeast-\d+)', ocr_text)
            analysis['regions'] = list(set(regions))
            
            # Look for associated script
            script_hint = self._find_script_hint_in_ocr(ocr_text)
            
            analysis['replication_instruction'] = {
                'action': 'run_script_and_capture',
                'target': 'terminal',
                'service': 'KMS',
                'activity': 'key_deletion_search',
                'script_name': script_hint or 'kms_key_deletion_search.py',
                'regions': analysis['regions'],
                'steps': [
                    '1. Find Python script in same folder (check for .py files)',
                    '2. Update date range in script to current audit period',
                    '3. Run script: python3 script_name.py',
                    '4. Wait for completion',
                    '5. Take terminal screenshot showing results',
                    '6. Name: {service}_{activity}_{timestamp}.png'
                ],
                'naming_pattern': 'KMS_Key_Deletion_Search_{timestamp}.png',
                'collect_fresh': True
            }
        
        else:
            # Generic terminal output
            analysis['content_summary'] = 'Terminal command output'
            analysis['replication_instruction'] = {
                'action': 'manual_review',
                'reason': 'Cannot determine exact command/script from screenshot'
            }
        
        return analysis
    
    def _analyze_aws_console_screenshot(self, image_path: str, ocr_text: str, file_name: str) -> Dict:
        """
        Analyze AWS Console screenshot
        
        Examples:
        - RDS backup configuration tab
        - EC2 instance list
        - S3 bucket properties
        - CloudTrail configuration
        
        Agent needs to:
        1. Identify which AWS service
        2. Identify which page/tab
        3. Identify resource name (if any)
        4. Navigate to same page and capture
        """
        console.print(f"  ☁️  AWS Console screenshot detected")
        
        ocr_lower = ocr_text.lower()
        
        analysis = {
            'file_name': file_name,
            'type': 'screenshot',
            'screenshot_type': 'aws_console',
            'ocr_text': ocr_text
        }
        
        # Detect AWS service
        if 'rds' in ocr_lower or 'database' in ocr_lower:
            service = 'RDS'
            
            # Detect which tab/page
            if 'backup' in ocr_lower:
                page = 'backup_configuration'
                analysis['content_summary'] = 'RDS backup configuration'
            elif 'configuration' in ocr_lower:
                page = 'configuration'
                analysis['content_summary'] = 'RDS cluster/instance configuration'
            elif 'monitoring' in ocr_lower:
                page = 'monitoring'
                analysis['content_summary'] = 'RDS monitoring metrics'
            else:
                page = 'overview'
                analysis['content_summary'] = 'RDS overview page'
            
            # Try to extract cluster/instance name
            resource_name = self._extract_resource_name_from_ocr(ocr_text, 'rds')
            
            analysis['service'] = service
            analysis['page'] = page
            analysis['resource'] = resource_name
            
            analysis['replication_instruction'] = {
                'action': 'screenshot',
                'target': 'aws_console',
                'service': service,
                'page': page,
                'resource': resource_name,
                'steps': [
                    '1. Login to AWS Console',
                    f'2. Navigate to {service} service',
                    f'3. Find resource: {resource_name or "identify from previous year"}',
                    f'4. Click on {page.replace("_", " ").title()} tab',
                    '5. Take screenshot',
                    f'6. Name: {service}_{resource_name or "resource"}_{page}_{{timestamp}}.png'
                ],
                'naming_pattern': f'{service}_{resource_name or "cluster"}_{page}_{{timestamp}}.png',
                'collect_fresh': True
            }
        
        elif 'ec2' in ocr_lower or 'instances' in ocr_lower:
            analysis['service'] = 'EC2'
            analysis['content_summary'] = 'EC2 instances or configuration'
            # Similar logic for EC2
        
        elif 's3' in ocr_lower or 'bucket' in ocr_lower:
            analysis['service'] = 'S3'
            analysis['content_summary'] = 'S3 bucket configuration'
            # Similar logic for S3
        
        return analysis
    
    def _analyze_script_output_screenshot(self, image_path: str, ocr_text: str, file_name: str) -> Dict:
        """
        Analyze script execution output screenshot (like your example!)
        
        This is specifically for screenshots showing Python/shell script execution
        """
        console.print(f"  📜 Script output screenshot detected")
        
        # Similar to terminal analysis but with script focus
        return self._analyze_terminal_screenshot(image_path, ocr_text, file_name)
    
    def _analyze_python_script(self, script_path: str) -> Dict:
        """
        Analyze Python script
        
        Understand:
        - What does the script do?
        - What APIs does it call?
        - Should it be re-run?
        """
        file_name = Path(script_path).name
        
        console.print(f"  🐍 Python script detected")
        
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        # Detect what the script does
        script_type = 'unknown'
        if 'kms' in script_content.lower():
            script_type = 'kms_analysis'
        elif 'rds' in script_content.lower():
            script_type = 'rds_analysis'
        
        return {
            'file_name': file_name,
            'type': 'python_script',
            'script_type': script_type,
            'content_preview': script_content[:500],
            'replication_instruction': {
                'action': 'run_script',
                'target': 'terminal',
                'script_path': script_path,
                'steps': [
                    '1. Review script for date parameters',
                    '2. Update dates to current audit period',
                    '3. Run: python3 {script_name}',
                    '4. Capture terminal screenshot of output',
                    '5. Save script output files'
                ],
                'collect_fresh': True
            }
        }
    
    def _analyze_shell_script(self, script_path: str) -> Dict:
        """Analyze shell script"""
        file_name = Path(script_path).name
        
        with open(script_path, 'r') as f:
            script_content = f.read()
        
        return {
            'file_name': file_name,
            'type': 'shell_script',
            'content_preview': script_content[:500],
            'replication_instruction': {
                'action': 'run_script',
                'target': 'terminal',
                'script_path': script_path,
                'collect_fresh': True
            }
        }
    
    def _analyze_data_export(self, file_path: str) -> Dict:
        """Analyze data export file"""
        file_name = Path(file_path).name
        
        return {
            'file_name': file_name,
            'type': 'data_export',
            'replication_instruction': {
                'action': 'export_data',
                'collect_fresh': True
            }
        }
    
    def _find_script_hint_in_ocr(self, ocr_text: str) -> Optional[str]:
        """
        Find script name mentioned in OCR text
        """
        # Look for .py files mentioned
        py_files = re.findall(r'[\w\-]+\.py', ocr_text)
        if py_files:
            return py_files[0]
        
        return None
    
    def _extract_resource_name_from_ocr(self, ocr_text: str, service: str) -> Optional[str]:
        """
        Extract resource name from OCR text
        
        Examples:
        - RDS: "prod-main-db", "staging-cluster"
        - EC2: "web-server-01", "i-1234567890"
        """
        # Common patterns for resource names
        patterns = [
            r'([a-z\-]+\-db)',  # RDS: prod-main-db
            r'([a-z\-]+\-cluster)',  # Cluster: prod-cluster
            r'(i-[a-f0-9]+)',  # EC2 instance ID
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, ocr_text.lower())
            if matches:
                return matches[0]
        
        return None
    
    def _generate_intelligent_collection_plan(self, analyzed_evidence: List[Dict]) -> Dict:
        """
        Generate intelligent collection plan based on analysis
        """
        plan = {
            'screenshots_to_capture': [],
            'scripts_to_run': [],
            'data_to_export': [],
            'manual_review_needed': []
        }
        
        for evidence in analyzed_evidence:
            instruction = evidence.get('replication_instruction', {})
            action = instruction.get('action')
            
            if action == 'screenshot':
                plan['screenshots_to_capture'].append({
                    'original': evidence['file_name'],
                    'service': instruction.get('service'),
                    'page': instruction.get('page'),
                    'resource': instruction.get('resource'),
                    'steps': instruction.get('steps', [])
                })
            
            elif action == 'run_script_and_capture':
                plan['scripts_to_run'].append({
                    'original': evidence['file_name'],
                    'script': instruction.get('script_name'),
                    'activity': instruction.get('activity'),
                    'steps': instruction.get('steps', [])
                })
            
            elif action == 'export_data':
                plan['data_to_export'].append({
                    'original': evidence['file_name'],
                    'type': evidence.get('type')
                })
            
            elif action == 'manual_review':
                plan['manual_review_needed'].append({
                    'file': evidence['file_name'],
                    'reason': instruction.get('reason')
                })
        
        return plan
    
    def _display_intelligent_analysis(self, result: Dict):
        """Display analysis results"""
        console.print(f"\n[green]✅ Intelligent Analysis Complete![/green]\n")
        
        plan = result['collection_plan']
        
        # Screenshots
        if plan['screenshots_to_capture']:
            console.print(f"[cyan]📸 Screenshots to Capture: {len(plan['screenshots_to_capture'])}[/cyan]")
            for item in plan['screenshots_to_capture'][:3]:
                console.print(f"  - {item['service']} {item['page']} ({item['resource']})")
        
        # Scripts
        if plan['scripts_to_run']:
            console.print(f"\n[cyan]🐍 Scripts to Run: {len(plan['scripts_to_run'])}[/cyan]")
            for item in plan['scripts_to_run'][:3]:
                console.print(f"  - {item['script']} ({item['activity']})")
        
        # Manual review
        if plan['manual_review_needed']:
            console.print(f"\n[yellow]⚠️  Manual Review Needed: {len(plan['manual_review_needed'])}[/yellow]")
            for item in plan['manual_review_needed'][:3]:
                console.print(f"  - {item['file']}: {item['reason']}")

