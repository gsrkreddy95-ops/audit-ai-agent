"""
Confluence Integration - Search, Analyze, and Export Confluence Documents

Features:
- Search documents by title, content, space, labels
- Get page content and metadata
- List all pages in a space
- Export pages to markdown, PDF, JSON
- Analyze document structure
- Get page history and comments
"""

import os
import json
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()


class ConfluenceIntegration:
    """Confluence API Integration for document management"""
    
    def __init__(self, confluence_url: Optional[str] = None, email: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize Confluence integration
        
        Args:
            confluence_url: Confluence instance URL (e.g., https://your-domain.atlassian.net/wiki)
            email: Your Confluence email
            api_token: Your Confluence API token (same as Jira token for Atlassian)
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        self.confluence_url = confluence_url or os.getenv('CONFLUENCE_URL')
        self.email = email or os.getenv('CONFLUENCE_EMAIL')
        self.api_token = api_token or os.getenv('CONFLUENCE_API_TOKEN')
        
        if not all([self.confluence_url, self.email, self.api_token]):
            console.print("[yellow]⚠️  Confluence credentials not found in environment![/yellow]")
            console.print("[yellow]   Please set CONFLUENCE_URL, CONFLUENCE_EMAIL, CONFLUENCE_API_TOKEN in .env file[/yellow]")
            self.confluence = None
            return
        
        try:
            from atlassian import Confluence
            self.confluence = Confluence(
                url=self.confluence_url,
                username=self.email,
                password=self.api_token,
                cloud=True
            )
            console.print(f"[green]✅ Connected to Confluence: {self.confluence_url}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to connect to Confluence: {e}[/red]")
            self.confluence = None
    
    def _check_connection(self) -> bool:
        """Check if Confluence connection is active"""
        if not self.confluence:
            console.print("[red]❌ Confluence not connected! Please check credentials.[/red]")
            return False
        return True
    
    def search_documents(
        self,
        query: str,
        space: Optional[str] = None,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search Confluence documents
        
        Args:
            query: Search query (searches title and content)
            space: Limit search to specific space key
            limit: Maximum number of results
        
        Returns:
            List of page dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            # Build CQL query
            cql = f'text ~ "{query}"'
            if space:
                cql += f' AND space = "{space}"'
            
            console.print(f"[cyan]🔍 Searching Confluence: {cql}[/cyan]")
            
            # Execute search
            results = self.confluence.cql(cql, limit=limit)
            
            # Format results
            pages = []
            for result in results.get('results', []):
                page = {
                    'id': result.get('content', {}).get('id'),
                    'title': result.get('title'),
                    'space': result.get('space', {}).get('key'),
                    'space_name': result.get('space', {}).get('name'),
                    'type': result.get('content', {}).get('type'),
                    'url': f"{self.confluence_url}{result.get('url', '')}",
                    'last_modified': result.get('lastModified'),
                }
                pages.append(page)
            
            console.print(f"[green]✅ Found {len(pages)} pages[/green]")
            return pages
        
        except Exception as e:
            console.print(f"[red]❌ Search failed: {e}[/red]")
            return []
    
    def get_page(
        self,
        page_id: Optional[str] = None,
        page_title: Optional[str] = None,
        space: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Get page content and metadata
        
        Args:
            page_id: Page ID (preferred if known)
            page_title: Page title (requires space parameter)
            space: Space key (required if using page_title)
        
        Returns:
            Page dictionary with full content
        """
        if not self._check_connection():
            return None
        
        try:
            if page_id:
                console.print(f"[cyan]📄 Fetching page by ID: {page_id}[/cyan]")
                page = self.confluence.get_page_by_id(page_id, expand='body.storage,version,space')
            elif page_title and space:
                console.print(f"[cyan]📄 Fetching page: {page_title} in {space}[/cyan]")
                page = self.confluence.get_page_by_title(space, page_title, expand='body.storage,version,space')
            else:
                console.print("[red]❌ Must provide page_id or (page_title + space)[/red]")
                return None
            
            if not page:
                console.print("[yellow]⚠️  Page not found[/yellow]")
                return None
            
            # Format page data
            page_data = {
                'id': page.get('id'),
                'title': page.get('title'),
                'space': page.get('space', {}).get('key'),
                'space_name': page.get('space', {}).get('name'),
                'type': page.get('type'),
                'content_html': page.get('body', {}).get('storage', {}).get('value', ''),
                'version': page.get('version', {}).get('number'),
                'created_by': page.get('version', {}).get('by', {}).get('displayName'),
                'created_date': page.get('version', {}).get('when'),
                'url': f"{self.confluence_url}/pages/viewpage.action?pageId={page.get('id')}",
            }
            
            console.print(f"[green]✅ Retrieved page: {page_data['title']}[/green]")
            return page_data
        
        except Exception as e:
            console.print(f"[red]❌ Error fetching page: {e}[/red]")
            return None
    
    def list_space_pages(self, space: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        List all pages in a Confluence space
        
        Args:
            space: Space key
            limit: Maximum number of pages to retrieve
        
        Returns:
            List of page dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            console.print(f"[cyan]📚 Listing pages in space: {space}[/cyan]")
            
            # Get all pages in space
            pages = self.confluence.get_all_pages_from_space(space, start=0, limit=limit)
            
            # Format results
            page_list = []
            for page in pages:
                page_data = {
                    'id': page.get('id'),
                    'title': page.get('title'),
                    'space': space,
                    'type': page.get('type'),
                    'url': f"{self.confluence_url}/pages/viewpage.action?pageId={page.get('id')}",
                }
                page_list.append(page_data)
            
            console.print(f"[green]✅ Found {len(page_list)} pages in {space}[/green]")
            return page_list
        
        except Exception as e:
            console.print(f"[red]❌ Error listing pages: {e}[/red]")
            return []
    
    def get_page_content_as_markdown(self, page_id: str) -> str:
        """
        Get page content converted to Markdown
        
        Args:
            page_id: Page ID
        
        Returns:
            Markdown content
        """
        if not self._check_connection():
            return ""
        
        try:
            page = self.get_page(page_id=page_id)
            if not page:
                return ""
            
            # Basic HTML to Markdown conversion
            import re
            content = page.get('content_html', '')
            
            # Remove HTML tags (basic conversion)
            content = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1\n', content)
            content = re.sub(r'<h2[^>]*>(.*?)</h2>', r'## \1\n', content)
            content = re.sub(r'<h3[^>]*>(.*?)</h3>', r'### \1\n', content)
            content = re.sub(r'<p[^>]*>(.*?)</p>', r'\1\n\n', content)
            content = re.sub(r'<strong[^>]*>(.*?)</strong>', r'**\1**', content)
            content = re.sub(r'<em[^>]*>(.*?)</em>', r'*\1*', content)
            content = re.sub(r'<code[^>]*>(.*?)</code>', r'`\1`', content)
            content = re.sub(r'<[^>]+>', '', content)  # Remove remaining tags
            
            return content
        
        except Exception as e:
            console.print(f"[red]❌ Error converting to markdown: {e}[/red]")
            return ""
    
    def export_pages(
        self,
        pages: List[Dict[str, Any]],
        output_format: str = 'json',
        output_file: Optional[str] = None,
        include_content: bool = False
    ) -> str:
        """
        Export pages to JSON or CSV
        
        Args:
            pages: List of page dictionaries
            output_format: 'json' or 'csv'
            output_file: Output file path
            include_content: If True, fetches and includes full page content
        
        Returns:
            Path to exported file
        """
        if not pages:
            console.print("[yellow]⚠️  No pages to export[/yellow]")
            return ""
        
        try:
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"confluence_pages_{timestamp}.{output_format}"
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Fetch full content if requested
            if include_content:
                console.print("[cyan]📥 Fetching full page content...[/cyan]")
                enriched_pages = []
                for page in pages:
                    full_page = self.get_page(page_id=page.get('id'))
                    if full_page:
                        enriched_pages.append(full_page)
                pages = enriched_pages
            
            if output_format == 'json':
                # Export to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(pages, f, indent=2, ensure_ascii=False)
                
                console.print(f"[green]✅ Exported {len(pages)} pages to JSON: {output_path}[/green]")
            
            elif output_format == 'csv':
                # Export to CSV
                import csv
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if pages:
                        fieldnames = list(pages[0].keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        writer.writerows(pages)
                
                console.print(f"[green]✅ Exported {len(pages)} pages to CSV: {output_path}[/green]")
            
            else:
                console.print(f"[red]❌ Unsupported format: {output_format}[/red]")
                return ""
            
            return str(output_path)
        
        except Exception as e:
            console.print(f"[red]❌ Export failed: {e}[/red]")
            return ""
    
    def get_spaces(self) -> List[Dict[str, str]]:
        """
        Get list of all Confluence spaces
        
        Returns:
            List of space dictionaries with key and name
        """
        if not self._check_connection():
            return []
        
        try:
            spaces = self.confluence.get_all_spaces(limit=100)
            return [
                {'key': s.get('key'), 'name': s.get('name'), 'type': s.get('type')}
                for s in spaces.get('results', [])
            ]
        except Exception as e:
            console.print(f"[red]❌ Error fetching spaces: {e}[/red]")
            return []


# Example usage
if __name__ == "__main__":
    # Initialize Confluence
    confluence_client = ConfluenceIntegration()
    
    # Search documents
    pages = confluence_client.search_documents("audit procedures", space="AUDIT", limit=10)
    
    # Export to JSON
    if pages:
        confluence_client.export_pages(pages, output_format='json', output_file='audit_docs.json')
    
    # Get specific page
    page = confluence_client.get_page(page_title="Security Guidelines", space="SEC")
    
    # List all pages in a space
    pages = confluence_client.list_space_pages("AUDIT")

