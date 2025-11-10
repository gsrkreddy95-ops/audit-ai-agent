"""
Jira Integration - List, Filter, Search, and Export Jira Tickets

Features:
- List tickets by project, labels, status, assignee, priority
- Advanced JQL search
- Export tickets to CSV/JSON
- Get ticket details, comments, history
- Filter and analyze tickets
"""

import os
import json
import csv
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path

from rich.console import Console

console = Console()


class JiraIntegration:
    """Jira API Integration for ticket management"""
    
    def __init__(self, jira_url: Optional[str] = None, email: Optional[str] = None, api_token: Optional[str] = None):
        """
        Initialize Jira integration
        
        Args:
            jira_url: Jira instance URL (e.g., https://your-domain.atlassian.net)
            email: Your Jira email
            api_token: Your Jira API token (create at https://id.atlassian.com/manage/api-tokens)
        """
        from dotenv import load_dotenv
        load_dotenv()
        
        self.jira_url = jira_url or os.getenv('JIRA_URL')
        self.email = email or os.getenv('JIRA_EMAIL')
        self.api_token = api_token or os.getenv('JIRA_API_TOKEN')
        
        if not all([self.jira_url, self.email, self.api_token]):
            console.print("[yellow]⚠️  Jira credentials not found in environment![/yellow]")
            console.print("[yellow]   Please set JIRA_URL, JIRA_EMAIL, JIRA_API_TOKEN in .env file[/yellow]")
            self.jira = None
            return
        
        try:
            from jira import JIRA
            self.jira = JIRA(
                server=self.jira_url,
                basic_auth=(self.email, self.api_token)
            )
            console.print(f"[green]✅ Connected to Jira: {self.jira_url}[/green]")
        except Exception as e:
            console.print(f"[red]❌ Failed to connect to Jira: {e}[/red]")
            self.jira = None
    
    def _check_connection(self) -> bool:
        """Check if Jira connection is active"""
        if not self.jira:
            console.print("[red]❌ Jira not connected! Please check credentials.[/red]")
            return False
        return True
    
    def list_tickets(
        self,
        project: Optional[str] = None,
        labels: Optional[List[str]] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        List Jira tickets with filters
        
        Args:
            project: Project key (e.g., 'AUDIT', 'SEC')
            labels: List of labels to filter by
            status: Status filter (e.g., 'Open', 'In Progress', 'Done')
            assignee: Assignee username or email
            priority: Priority filter (e.g., 'High', 'Critical')
            issue_type: Issue type (e.g., 'Bug', 'Task', 'Story')
            max_results: Maximum number of results to return
        
        Returns:
            List of ticket dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            # Build JQL query
            jql_parts = []
            
            if project:
                jql_parts.append(f'project = "{project}"')
            
            if labels:
                label_query = ' OR '.join([f'labels = "{label}"' for label in labels])
                jql_parts.append(f'({label_query})')
            
            if status:
                jql_parts.append(f'status = "{status}"')
            
            if assignee:
                jql_parts.append(f'assignee = "{assignee}"')
            
            if priority:
                jql_parts.append(f'priority = "{priority}"')
            
            if issue_type:
                jql_parts.append(f'issuetype = "{issue_type}"')
            
            jql = ' AND '.join(jql_parts) if jql_parts else 'ORDER BY created DESC'
            
            console.print(f"[cyan]🔍 Searching Jira with JQL: {jql}[/cyan]")
            
            # Execute search using new Jira Cloud API (POST method)
            try:
                response = self.jira._session.post(
                    f"{self.jira._options['server']}/rest/api/3/search/jql",
                    json={
                        'jql': jql,
                        'maxResults': max_results,
                        'fields': ['*all']
                    },
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                search_results = response.json()
                
                # Convert raw JSON to Issue objects
                issues = []
                for issue_data in search_results.get('issues', []):
                    try:
                        from jira.resources import Issue
                        issue = Issue(self.jira._options, self.jira._session, raw=issue_data)
                        issues.append(issue)
                    except Exception:
                        # Fallback
                        class SimpleIssue:
                            def __init__(self, data):
                                self.key = data.get('key')
                                self.fields = type('obj', (object,), {
                                    'summary': data.get('fields', {}).get('summary', ''),
                                    'status': type('obj', (object,), {'name': data.get('fields', {}).get('status', {}).get('name', 'Unknown')})(),
                                    'priority': type('obj', (object,), {'name': data.get('fields', {}).get('priority', {}).get('name', 'None')})() if data.get('fields', {}).get('priority') else None,
                                    'assignee': type('obj', (object,), {'displayName': data.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned')})() if data.get('fields', {}).get('assignee') else None,
                                    'reporter': type('obj', (object,), {'displayName': data.get('fields', {}).get('reporter', {}).get('displayName', 'Unknown')})() if data.get('fields', {}).get('reporter') else None,
                                    'created': data.get('fields', {}).get('created', ''),
                                    'updated': data.get('fields', {}).get('updated', ''),
                                    'issuetype': type('obj', (object,), {'name': data.get('fields', {}).get('issuetype', {}).get('name', 'Unknown')})(),
                                    'labels': data.get('fields', {}).get('labels', []),
                                    'description': data.get('fields', {}).get('description', '')
                                })()
                        issue = SimpleIssue(issue_data)
                        issues.append(issue)
            except Exception as e:
                console.print(f"[red]❌ Error searching: {e}[/red]")
                return []
            
            # Format results
            tickets = []
            for issue in issues:
                ticket = {
                    'key': issue.key,
                    'summary': issue.fields.summary,
                    'status': issue.fields.status.name,
                    'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                    'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                    'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                    'created': str(issue.fields.created),
                    'updated': str(issue.fields.updated),
                    'issue_type': issue.fields.issuetype.name,
                    'labels': issue.fields.labels,
                    'description': issue.fields.description or '',
                    'url': f"{self.jira_url}/browse/{issue.key}"
                }
                tickets.append(ticket)
            
            console.print(f"[green]✅ Found {len(tickets)} tickets[/green]")
            return tickets
        
        except Exception as e:
            console.print(f"[red]❌ Error listing tickets: {e}[/red]")
            return []
    
    def search_jql(self, jql_query: str, max_results: int = 1000, paginate: bool = True) -> List[Dict[str, Any]]:
        """
        Advanced JQL search with automatic pagination
        
        Args:
            jql_query: JQL query string (e.g., 'project = AUDIT AND status = "In Progress"')
            max_results: Maximum number of results (default 1000, use 0 for all)
            paginate: If True, automatically fetch all results using pagination
        
        Returns:
            List of ticket dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            console.print(f"[cyan]🔍 Executing JQL: {jql_query}[/cyan]")
            
            # Jira API limits to 100 per request, so we need pagination
            if paginate and (max_results == 0 or max_results > 100):
                tickets = []
                start_at = 0
                page_size = 100  # Jira API max per request
                total_fetched = 0
                
                console.print(f"[cyan]📄 Fetching results with pagination (max: {max_results if max_results > 0 else 'all'})...[/cyan]")
                
                total_available = None  # Will be set after first request
                
                while True:
                    # Fetch a page of results using Jira Cloud's new JQL API
                    try:
                        # NOTE: /search/jql is a POST endpoint with JSON body
                        response = self.jira._session.post(
                            f"{self.jira._options['server']}/rest/api/3/search/jql",
                            json={
                                'jql': jql_query,
                                'startAt': start_at,
                                'maxResults': page_size,
                                'fields': ['*all']
                            },
                            headers={'Content-Type': 'application/json'}
                        )
                        
                        # DEBUG: Log the request details
                        if start_at == 0:
                            console.print(f"[dim]   API Request: POST /rest/api/3/search/jql[/dim]")
                            console.print(f"[dim]   JQL: {jql_query}[/dim]")
                        response.raise_for_status()
                        search_results = response.json()
                        
                        # Check total available results from Jira
                        # NOTE: Jira Cloud's /search/jql API sometimes returns total=0 incorrectly
                        # We'll trust it only if it's non-zero or if no results are returned
                        if total_available is None:
                            reported_total = search_results.get('total', 0)
                            num_issues_in_response = len(search_results.get('issues', []))
                            
                            # If Jira reports 0 but returns results, it's a bug - ignore the total
                            if reported_total == 0 and num_issues_in_response > 0:
                                console.print(f"[yellow]⚠️  Jira reported total=0 but returned {num_issues_in_response} issues (known API bug)[/yellow]")
                                console.print(f"[dim]   Will paginate until no more results...[/dim]")
                                total_available = -1  # Signal to ignore total and rely on page size
                            else:
                                total_available = reported_total
                                console.print(f"[dim]   Total matching tickets in Jira: {total_available}[/dim]")
                                
                                # Adjust max_results if it exceeds what's actually available
                                if max_results == 0 or max_results > total_available:
                                    effective_max = total_available
                                else:
                                    effective_max = max_results
                                console.print(f"[dim]   Will fetch up to: {effective_max} tickets[/dim]")
                        
                        # Convert raw JSON to Issue objects (match old API behavior)
                        page_issues = []
                        for issue_data in search_results.get('issues', []):
                            try:
                                from jira.resources import Issue
                                issue = Issue(self.jira._options, self.jira._session, raw=issue_data)
                                page_issues.append(issue)
                            except Exception:
                                # Fallback: manually create a simple object
                                class SimpleIssue:
                                    def __init__(self, data):
                                        self.key = data.get('key')
                                        self.fields = type('obj', (object,), {
                                            'summary': data.get('fields', {}).get('summary', ''),
                                            'status': type('obj', (object,), {'name': data.get('fields', {}).get('status', {}).get('name', 'Unknown')})(),
                                            'priority': type('obj', (object,), {'name': data.get('fields', {}).get('priority', {}).get('name', 'None')})() if data.get('fields', {}).get('priority') else None,
                                            'assignee': type('obj', (object,), {'displayName': data.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned')})() if data.get('fields', {}).get('assignee') else None,
                                            'reporter': type('obj', (object,), {'displayName': data.get('fields', {}).get('reporter', {}).get('displayName', 'Unknown')})() if data.get('fields', {}).get('reporter') else None,
                                            'created': data.get('fields', {}).get('created', ''),
                                            'updated': data.get('fields', {}).get('updated', ''),
                                            'issuetype': type('obj', (object,), {'name': data.get('fields', {}).get('issuetype', {}).get('name', 'Unknown')})(),
                                            'labels': data.get('fields', {}).get('labels', []),
                                            'description': data.get('fields', {}).get('description', '')
                                        })()
                                issue = SimpleIssue(issue_data)
                                page_issues.append(issue)
                    except Exception as e:
                        console.print(f"[red]❌ Error fetching page: {e}[/red]")
                        raise
                    
                    if not page_issues:
                        break  # No more results
                    
                    # Process this page
                    for issue in page_issues:
                        ticket = {
                            'key': issue.key,
                            'summary': issue.fields.summary,
                            'status': issue.fields.status.name,
                            'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                            'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                            'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                            'created': str(issue.fields.created),
                            'updated': str(issue.fields.updated),
                            'issue_type': issue.fields.issuetype.name,
                            'labels': issue.fields.labels,
                            'url': f"{self.jira_url}/browse/{issue.key}"
                        }
                        tickets.append(ticket)
                        total_fetched += 1
                        
                        # Check if we've hit the max_results limit
                        if max_results > 0 and total_fetched >= max_results:
                            break
                    
                    console.print(f"[dim]   Fetched {total_fetched} tickets so far...[/dim]")
                    
                    # Check stopping conditions
                    # 1. No more results on this page (most reliable indicator)
                    if len(page_issues) < page_size:
                        console.print(f"[dim]   Last page reached (got {len(page_issues)} < {page_size})[/dim]")
                        break
                    
                    # 2. Reached the total available from Jira (only if total is reliable)
                    if total_available is not None and total_available > 0 and total_fetched >= total_available:
                        console.print(f"[dim]   All available tickets fetched ({total_fetched}/{total_available})[/dim]")
                        break
                    
                    # 3. Hit the user-specified max_results limit
                    if max_results > 0 and total_fetched >= max_results:
                        console.print(f"[dim]   Max results limit reached ({total_fetched}/{max_results})[/dim]")
                        break
                    
                    start_at += page_size
                
                console.print(f"[green]✅ Found {len(tickets)} tickets (fetched all pages)[/green]")
                return tickets
            else:
                # Single request (no pagination) using new Jira Cloud API (POST method)
                try:
                    response = self.jira._session.post(
                        f"{self.jira._options['server']}/rest/api/3/search/jql",
                        json={
                            'jql': jql_query,
                            'maxResults': max_results,
                            'fields': ['*all']
                        },
                        headers={'Content-Type': 'application/json'}
                    )
                    response.raise_for_status()
                    search_results = response.json()
                    
                    # Convert raw JSON to Issue objects
                    issues = []
                    for issue_data in search_results.get('issues', []):
                        try:
                            from jira.resources import Issue
                            issue = Issue(self.jira._options, self.jira._session, raw=issue_data)
                            issues.append(issue)
                        except Exception:
                            # Fallback: manually create a simple object
                            class SimpleIssue:
                                def __init__(self, data):
                                    self.key = data.get('key')
                                    self.fields = type('obj', (object,), {
                                        'summary': data.get('fields', {}).get('summary', ''),
                                        'status': type('obj', (object,), {'name': data.get('fields', {}).get('status', {}).get('name', 'Unknown')})(),
                                        'priority': type('obj', (object,), {'name': data.get('fields', {}).get('priority', {}).get('name', 'None')})() if data.get('fields', {}).get('priority') else None,
                                        'assignee': type('obj', (object,), {'displayName': data.get('fields', {}).get('assignee', {}).get('displayName', 'Unassigned')})() if data.get('fields', {}).get('assignee') else None,
                                        'reporter': type('obj', (object,), {'displayName': data.get('fields', {}).get('reporter', {}).get('displayName', 'Unknown')})() if data.get('fields', {}).get('reporter') else None,
                                        'created': data.get('fields', {}).get('created', ''),
                                        'updated': data.get('fields', {}).get('updated', ''),
                                        'issuetype': type('obj', (object,), {'name': data.get('fields', {}).get('issuetype', {}).get('name', 'Unknown')})(),
                                        'labels': data.get('fields', {}).get('labels', []),
                                        'description': data.get('fields', {}).get('description', '')
                                    })()
                            issue = SimpleIssue(issue_data)
                            issues.append(issue)
                except Exception as e:
                    console.print(f"[red]❌ Error fetching tickets: {e}[/red]")
                    return []
                
                tickets = []
                for issue in issues:
                    ticket = {
                        'key': issue.key,
                        'summary': issue.fields.summary,
                        'status': issue.fields.status.name,
                        'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                        'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                        'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                        'created': str(issue.fields.created),
                        'updated': str(issue.fields.updated),
                        'issue_type': issue.fields.issuetype.name,
                        'labels': issue.fields.labels,
                        'url': f"{self.jira_url}/browse/{issue.key}"
                    }
                    tickets.append(ticket)
                
                console.print(f"[green]✅ Found {len(tickets)} tickets[/green]")
                return tickets
        
        except Exception as e:
            console.print(f"[red]❌ JQL search failed: {e}[/red]")
            return []
    
    def get_ticket(self, ticket_key: str) -> Optional[Dict[str, Any]]:
        """
        Get detailed ticket information
        
        Args:
            ticket_key: Jira ticket key (e.g., 'AUDIT-123')
        
        Returns:
            Ticket dictionary with full details
        """
        if not self._check_connection():
            return None
        
        try:
            console.print(f"[cyan]📋 Fetching ticket: {ticket_key}[/cyan]")
            
            issue = self.jira.issue(ticket_key)
            
            # Get comments
            comments = []
            for comment in issue.fields.comment.comments:
                comments.append({
                    'author': comment.author.displayName,
                    'created': str(comment.created),
                    'body': comment.body
                })
            
            # Get attachments
            attachments = []
            for attachment in issue.fields.attachment:
                attachments.append({
                    'filename': attachment.filename,
                    'size': attachment.size,
                    'url': attachment.content
                })
            
            ticket = {
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': issue.fields.description or '',
                'status': issue.fields.status.name,
                'priority': issue.fields.priority.name if issue.fields.priority else 'None',
                'assignee': issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned',
                'reporter': issue.fields.reporter.displayName if issue.fields.reporter else 'Unknown',
                'created': str(issue.fields.created),
                'updated': str(issue.fields.updated),
                'resolved': str(issue.fields.resolutiondate) if issue.fields.resolutiondate else None,
                'issue_type': issue.fields.issuetype.name,
                'labels': issue.fields.labels,
                'components': [c.name for c in issue.fields.components],
                'comments': comments,
                'attachments': attachments,
                'url': f"{self.jira_url}/browse/{issue.key}"
            }
            
            console.print(f"[green]✅ Retrieved ticket: {ticket_key}[/green]")
            return ticket
        
        except Exception as e:
            console.print(f"[red]❌ Error fetching ticket: {e}[/red]")
            return None
    
    def export_tickets(
        self,
        tickets: List[Dict[str, Any]],
        output_format: str = 'csv',
        output_file: Optional[str] = None
    ) -> str:
        """
        Export tickets to CSV or JSON
        
        Args:
            tickets: List of ticket dictionaries
            output_format: 'csv' or 'json'
            output_file: Output file path (auto-generated if not provided)
        
        Returns:
            Path to exported file
        """
        if not tickets:
            console.print("[yellow]⚠️  No tickets to export[/yellow]")
            return ""
        
        try:
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"jira_tickets_{timestamp}.{output_format}"
            
            output_path = Path(output_file)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            if output_format == 'csv':
                # Export to CSV
                with open(output_path, 'w', newline='', encoding='utf-8') as f:
                    if tickets:
                        # Use all keys from first ticket
                        fieldnames = list(tickets[0].keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        
                        for ticket in tickets:
                            # Convert lists to strings for CSV
                            row = {k: (', '.join(v) if isinstance(v, list) else v) for k, v in ticket.items()}
                            writer.writerow(row)
                
                console.print(f"[green]✅ Exported {len(tickets)} tickets to CSV: {output_path}[/green]")
            
            elif output_format == 'json':
                # Export to JSON
                with open(output_path, 'w', encoding='utf-8') as f:
                    json.dump(tickets, f, indent=2, ensure_ascii=False)
                
                console.print(f"[green]✅ Exported {len(tickets)} tickets to JSON: {output_path}[/green]")
            
            else:
                console.print(f"[red]❌ Unsupported format: {output_format}[/red]")
                return ""
            
            return str(output_path)
        
        except Exception as e:
            console.print(f"[red]❌ Export failed: {e}[/red]")
            return ""
    
    def get_projects(self) -> List[Dict[str, str]]:
        """
        Get list of all Jira projects
        
        Returns:
            List of project dictionaries with key and name
        """
        if not self._check_connection():
            return []
        
        try:
            projects = self.jira.projects()
            return [{'key': p.key, 'name': p.name} for p in projects]
        except Exception as e:
            console.print(f"[red]❌ Error fetching projects: {e}[/red]")
            return []


# Example usage
if __name__ == "__main__":
    # Initialize Jira
    jira_client = JiraIntegration()
    
    # List tickets
    tickets = jira_client.list_tickets(project="AUDIT", status="Open", max_results=10)
    
    # Export to CSV
    if tickets:
        jira_client.export_tickets(tickets, output_format='csv', output_file='audit_tickets.csv')
    
    # Search with JQL
    tickets = jira_client.search_jql('project = AUDIT AND labels = "security" ORDER BY created DESC')
    
    # Get specific ticket
    ticket = jira_client.get_ticket('AUDIT-123')

