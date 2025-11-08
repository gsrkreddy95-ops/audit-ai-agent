"""
LLM-Powered Evidence Analyzer
Uses Claude to intelligently analyze previous audit evidence
"""

import os
import json
from typing import Dict, List, Optional
from pathlib import Path
from rich.console import Console
from PIL import Image
import pytesseract
import pandas as pd
from docx import Document
import PyPDF2

console = Console()


class LLMEvidenceAnalyzer:
    """
    Uses Claude (LLM) to intelligently analyze evidence files
    Much smarter than hardcoded pattern matching!
    """
    
    def __init__(self, llm):
        """
        Initialize with LLM instance
        
        Args:
            llm: ChatBedrock or other LangChain LLM instance
        """
        self.llm = llm
        
    def analyze_file(self, file_path: str, file_name: str) -> Dict:
        """
        Analyze a single evidence file using Claude's intelligence
        
        Returns:
            {
                'file_name': str,
                'file_type': str,
                'evidence_type': str,
                'source': str,
                'details': dict,
                'collection_method': str,
                'instructions': str
            }
        """
        file_ext = Path(file_name).suffix.lower().replace('.', '')
        
        console.print(f"[cyan]🧠 Claude analyzing: {file_name}...[/cyan]")
        
        # Extract content based on file type
        content = self._extract_content(file_path, file_ext)
        
        if not content:
            console.print(f"[yellow]⚠️  Could not extract content from {file_name}[/yellow]")
            return self._fallback_analysis(file_name, file_ext)
        
        # Ask Claude to analyze the content
        analysis = self._ask_claude_to_analyze(file_name, file_ext, content)
        
        return analysis
    
    def _extract_content(self, file_path: str, file_ext: str) -> str:
        """Extract content from file based on type"""
        try:
            if not os.path.exists(file_path):
                return ""
            
            # Screenshots: Use OCR
            if file_ext in ['png', 'jpg', 'jpeg']:
                console.print(f"[dim]  📸 Extracting text from image via OCR...[/dim]")
                image = Image.open(file_path)
                text = pytesseract.image_to_string(image)
                return text[:5000]  # Limit to 5000 chars
            
            # CSV: Read structure and sample data
            elif file_ext == 'csv':
                console.print(f"[dim]  📊 Reading CSV structure...[/dim]")
                df = pd.read_csv(file_path)
                
                content = f"CSV File Analysis:\n"
                content += f"Columns: {', '.join(df.columns.tolist())}\n"
                content += f"Row count: {len(df)}\n"
                content += f"\nFirst 5 rows:\n{df.head().to_string()}\n"
                
                # Add summary statistics for key columns
                if 'Region' in df.columns:
                    content += f"\nRegions: {', '.join(df['Region'].unique()[:10])}\n"
                if 'Status' in df.columns:
                    content += f"Statuses: {', '.join(df['Status'].unique()[:10])}\n"
                
                return content[:5000]
            
            # Excel: Similar to CSV
            elif file_ext in ['xlsx', 'xls']:
                console.print(f"[dim]  📊 Reading Excel structure...[/dim]")
                df = pd.read_excel(file_path)
                
                content = f"Excel File Analysis:\n"
                content += f"Columns: {', '.join(df.columns.tolist())}\n"
                content += f"Row count: {len(df)}\n"
                content += f"\nFirst 5 rows:\n{df.head().to_string()}\n"
                
                return content[:5000]
            
            # Word documents: Extract text
            elif file_ext in ['docx', 'doc']:
                console.print(f"[dim]  📄 Reading Word document...[/dim]")
                if file_ext == 'docx':
                    doc = Document(file_path)
                    text = '\n'.join([para.text for para in doc.paragraphs])
                    return text[:5000]
                else:
                    return ""  # .doc format requires different library
            
            # JSON: Parse and format
            elif file_ext == 'json':
                console.print(f"[dim]  📋 Reading JSON structure...[/dim]")
                with open(file_path, 'r') as f:
                    data = json.load(f)
                return json.dumps(data, indent=2)[:5000]
            
            # PDF files: Extract text from all pages
            elif file_ext == 'pdf':
                console.print(f"[dim]  📄 Reading PDF document...[/dim]")
                text = ""
                with open(file_path, 'rb') as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    num_pages = len(pdf_reader.pages)
                    console.print(f"[dim]  📄 PDF has {num_pages} pages, extracting text...[/dim]")
                    
                    # Extract text from first 10 pages (to avoid too much content)
                    for i in range(min(10, num_pages)):
                        page = pdf_reader.pages[i]
                        text += page.extract_text() + "\n\n"
                
                return text[:10000]  # Limit to 10000 chars for PDFs
            
            # Text files
            elif file_ext == 'txt':
                with open(file_path, 'r') as f:
                    return f.read()[:5000]
            
            return ""
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Content extraction failed: {e}[/yellow]")
            return ""
    
    def _ask_claude_to_analyze(self, file_name: str, file_ext: str, content: str) -> Dict:
        """Ask Claude to analyze the evidence and provide collection instructions"""
        
        prompt = f"""You are analyzing previous audit evidence to understand what was collected and how to collect similar evidence for the current year.

**FILE NAME:** {file_name}
**FILE TYPE:** {file_ext}

**FILE CONTENT:**
```
{content}
```

Please analyze this evidence and provide:

1. **Evidence Type**: What kind of evidence is this? (screenshot, data_export, document, etc.)
2. **Source**: Where was this collected from? (aws_console, aws_api, jira, confluence, manual, etc.)
3. **Service/Tool**: What AWS service or tool? (RDS, S3, IAM, EC2, etc.)
4. **Specific Details**: Extract specific details like:
   - AWS region (if visible)
   - Resource names (cluster names, bucket names, etc.)
   - Configuration tabs or pages shown
   - Data fields/columns present
   - Date ranges or time periods
5. **Collection Method**: How should this be collected? (screenshot, api_export, manual_document, etc.)
6. **Detailed Instructions**: Provide SPECIFIC, step-by-step instructions for collecting similar evidence for the current year. Be as detailed as possible!

Respond in JSON format:
{{
  "evidence_type": "screenshot|data_export|document|explanation",
  "source": "aws_console|aws_api|jira|confluence|manual",
  "service": "RDS|S3|IAM|EC2|etc",
  "details": {{
    "aws_region": "us-east-1",
    "resource_name": "conure",
    "page_or_tab": "Connectivity & security",
    "columns": ["BucketName", "Region"],
    "row_count": 87,
    "any_other_relevant_details": "..."
  }},
  "collection_method": "screenshot|api_export|manual",
  "instructions": "Detailed step-by-step instructions here..."
}}

Be VERY specific in your instructions. If it's a screenshot, mention exactly which AWS console page, which tabs to click, what should be visible. If it's data export, mention exact API calls or CLI commands needed."""

        try:
            # Invoke Claude
            response = self.llm.invoke(prompt)

            # Extract text content
            if hasattr(response, 'content'):
                response_text = response.content
            else:
                response_text = str(response)

            # Sanitize response to avoid JSON control character issues
            import re
            cleaned = response_text.strip()
            cleaned = cleaned.replace('\r\n', '\n').replace('\r', '\n')
            cleaned = re.sub(r"```(?:json)?", "", cleaned)  # remove fenced code markers
            cleaned = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", cleaned)  # strip control chars

            # Extract first JSON object or array
            json_match = re.search(r"(\{.*?\})|(\[.*?\])", cleaned, re.DOTALL)
            analysis_dict = {}
            parse_errors = []
            if json_match:
                json_candidate = json_match.group(0)

                # Heuristic fixes: remove trailing commas, balance quotes
                json_candidate = re.sub(r",\s*([}\]])", r"\1", json_candidate)
                if json_candidate.count('"') % 2 != 0:
                    json_candidate += '"'

                attempts = [json_candidate]
                # Attempt with quoted keys if unquoted
                attempts.append(re.sub(r"(\{|,)(\s*)([A-Za-z0-9_]+)(\s*):", r"\1\2""\3""\4:", json_candidate))

                for attempt in attempts:
                    try:
                        analysis_dict = json.loads(attempt)
                        break
                    except json.JSONDecodeError as e:
                        parse_errors.append(str(e))
            else:
                parse_errors.append("No JSON structure detected")

            if not analysis_dict:
                # Fallback to embedding instructions only
                analysis_dict = {
                    "evidence_type": "unknown",
                    "source": "unknown",
                    "service": "unknown",
                    "details": {},
                    "collection_method": "manual",
                    "instructions": cleaned[:1200]
                }
                if parse_errors:
                    analysis_dict['details']['json_parse_errors'] = parse_errors[:3]

            # Build result
            result = {
                'file_name': file_name,
                'file_type': file_ext,
                'evidence_type': analysis_dict.get('evidence_type', 'unknown'),
                'source': analysis_dict.get('source', 'unknown'),
                'details': analysis_dict.get('details', {}),
                'collection_method': analysis_dict.get('collection_method', 'manual'),
                'instructions': analysis_dict.get('instructions', 'See Claude analysis')
            }

            # Add service to details if not there
            if 'service' not in result['details']:
                result['details']['service'] = analysis_dict.get('service', 'unknown')

            console.print(f"[green]✅ Claude analysis complete for {file_name}[/green]")

            return result

        except Exception as e:
            console.print(f"[red]❌ Claude analysis failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return self._fallback_analysis(file_name, file_ext)
    
    def _fallback_analysis(self, file_name: str, file_ext: str) -> Dict:
        """Fallback analysis if Claude fails"""
        return {
            'file_name': file_name,
            'file_type': file_ext,
            'evidence_type': 'unknown',
            'source': 'unknown',
            'details': {},
            'collection_method': 'manual',
            'instructions': f"Manual collection needed for: {file_name}"
        }
    
    def analyze_rfi_folder(self, files: List[Dict]) -> Dict:
        """
        Analyze all files in an RFI folder and create collection plan
        Uses Claude to understand the overall evidence pattern
        
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
        console.print(f"\n[cyan]🧠 Claude analyzing {len(files)} files in RFI folder...[/cyan]\n")
        
        by_type = {}
        collection_tasks = []
        
        # Analyze each file
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
            
            # Analyze with Claude
            local_path = file.get('local_path', '')
            if local_path and os.path.exists(local_path):
                analysis = self.analyze_file(local_path, file_name)
            else:
                analysis = self._fallback_analysis(file_name, file_ext)
            
            collection_tasks.append({
                'file_name': file_name,
                'analysis': analysis
            })
        
        # Generate summary with Claude
        summary = self._generate_summary_with_claude(by_type, collection_tasks)
        
        return {
            'total_files': len(files),
            'by_type': by_type,
            'collection_tasks': collection_tasks,
            'summary': summary
        }
    
    def _generate_summary_with_claude(self, by_type: Dict, collection_tasks: List[Dict]) -> str:
        """Ask Claude to generate an overall summary of the evidence collection plan"""
        
        # Prepare analysis summary for Claude
        task_summary = []
        for task in collection_tasks:
            analysis = task['analysis']
            task_summary.append({
                'file': task['file_name'],
                'type': analysis['evidence_type'],
                'source': analysis['source'],
                'service': analysis['details'].get('service', 'unknown'),
                'instructions': analysis['instructions'][:200]  # Truncate for summary
            })
        
        prompt = f"""You are reviewing the analysis of {len(collection_tasks)} audit evidence files.

**FILE TYPE BREAKDOWN:**
{json.dumps(by_type, indent=2)}

**ANALYSIS RESULTS:**
{json.dumps(task_summary, indent=2)}

Please provide a concise summary that includes:
1. What types of evidence were collected (screenshots, exports, documents)
2. What AWS services or tools are involved
3. The primary format (e.g., "mostly screenshots" or "mostly CSV exports")
4. A brief collection plan overview

Keep it under 500 words, format in markdown."""

        try:
            response = self.llm.invoke(prompt)
            if hasattr(response, 'content'):
                summary_text = response.content
            else:
                summary_text = str(response)
            
            return summary_text
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Claude summary generation failed: {e}[/yellow]")
            
            # Fallback summary
            summary_lines = [f"📁 **Found {len(collection_tasks)} files:**\n"]
            for ext, file_list in by_type.items():
                summary_lines.append(f"  • {len(file_list)} {ext.upper()} files")
            
            return '\n'.join(summary_lines)

