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
import re
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
        self.field_map: Dict[str, str] = {}
        self.sprint_field_id: Optional[str] = None
        self.epic_field_id: Optional[str] = None
        self.story_points_field_id: Optional[str] = None
        self.team_field_id: Optional[str] = None
        self.board_filter_cache: Dict[str, str] = {}
        self._field_map_initialized = False
        
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
            self._initialize_field_map()
        except Exception as e:
            console.print(f"[red]❌ Failed to connect to Jira: {e}[/red]")
            self.jira = None
    
    def _check_connection(self) -> bool:
        """Check if Jira connection is active"""
        if not self.jira:
            console.print("[red]❌ Jira not connected! Please check credentials.[/red]")
            return False
        return True
    
    def _initialize_field_map(self) -> None:
        """Fetch Jira field metadata to resolve custom field IDs (sprint, epic, etc.)"""
        if not self.jira:
            return
        if self._field_map_initialized:
            return
        
        try:
            fields = self.jira.fields()
            for field in fields:
                name = (field.get('name') or '').strip().lower()
                field_id = field.get('id')
                if name and field_id:
                    self.field_map[name] = field_id
            
            def lookup(possible_names: List[str]) -> Optional[str]:
                for candidate in possible_names:
                    field_id = self.field_map.get(candidate.lower())
                    if field_id:
                        return field_id
                return None
            
            self.sprint_field_id = lookup(['sprint'])
            self.epic_field_id = lookup(['epic link', 'epic'])
            self.story_points_field_id = lookup(['story points', 'story point estimate', 'story points (legacy)'])
            self.team_field_id = lookup(['team'])
            
            console.print("[dim]🧠 Jira field map initialized:"
                          f" sprint={self.sprint_field_id}, epic={self.epic_field_id},"
                          f" story_points={self.story_points_field_id}[/dim]")
            self._field_map_initialized = True
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not initialize Jira field map: {e}[/yellow]")
    
    def _build_issue_objects(self, search_results: Dict[str, Any]) -> List[Any]:
        """Create Issue objects while keeping raw payload for advanced parsing"""
        issues = []
        for issue_data in search_results.get('issues', []):
            try:
                from jira.resources import Issue
                issue = Issue(self.jira._options, self.jira._session, raw=issue_data)
                issues.append(issue)
            except Exception:
                issues.append(self._create_simple_issue(issue_data))
        return issues
    
    @staticmethod
    def _create_simple_issue(issue_data: Dict[str, Any]):
        """Fallback object that mirrors jira.resources.Issue essentials"""
        class SimpleIssue:
            def __init__(self, data: Dict[str, Any]):
                self.raw = data
                self.key = data.get('key')
                fields_data = data.get('fields', {})
                self.fields = type('obj', (object,), {
                    'summary': fields_data.get('summary', ''),
                    'status': type('obj', (object,), {'name': fields_data.get('status', {}).get('name', 'Unknown')})(),
                    'priority': type('obj', (object,), {'name': fields_data.get('priority', {}).get('name', 'None')})() if fields_data.get('priority') else None,
                    'assignee': type('obj', (object,), {'displayName': fields_data.get('assignee', {}).get('displayName', 'Unassigned')})() if fields_data.get('assignee') else None,
                    'reporter': type('obj', (object,), {'displayName': fields_data.get('reporter', {}).get('displayName', 'Unknown')})() if fields_data.get('reporter') else None,
                    'created': fields_data.get('created', ''),
                    'updated': fields_data.get('updated', ''),
                    'issuetype': type('obj', (object,), {'name': fields_data.get('issuetype', {}).get('name', 'Unknown')})(),
                    'labels': fields_data.get('labels', []),
                    'description': fields_data.get('description', '')
                })()
        return SimpleIssue(issue_data)
    
    @staticmethod
    def _serialize_value_for_export(value: Any) -> Any:
        """Convert complex values to CSV-friendly strings"""
        if isinstance(value, list):
            if all(isinstance(item, (str, int, float)) or item is None for item in value):
                return ', '.join('' if item is None else str(item) for item in value)
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, dict):
            return json.dumps(value, ensure_ascii=False)
        return value
    
    def _build_ticket_dict(self, issue: Any) -> Dict[str, Any]:
        """Create normalized ticket dictionary enriched with advanced metadata"""
        priority_obj = getattr(issue.fields, 'priority', None)
        assignee_obj = getattr(issue.fields, 'assignee', None)
        reporter_obj = getattr(issue.fields, 'reporter', None)
        status_obj = getattr(issue.fields, 'status', None)
        issue_type_obj = getattr(issue.fields, 'issuetype', None)
        
        ticket = {
            'key': issue.key,
            'summary': getattr(issue.fields, 'summary', '') or '',
            'status': getattr(status_obj, 'name', 'Unknown'),
            'priority': getattr(priority_obj, 'name', 'None') if priority_obj else 'None',
            'assignee': getattr(assignee_obj, 'displayName', 'Unassigned') if assignee_obj else 'Unassigned',
            'reporter': getattr(reporter_obj, 'displayName', 'Unknown') if reporter_obj else 'Unknown',
            'created': str(getattr(issue.fields, 'created', '')),
            'updated': str(getattr(issue.fields, 'updated', '')),
            'issue_type': getattr(issue_type_obj, 'name', 'Unknown'),
            'labels': getattr(issue.fields, 'labels', []) or [],
            'description': getattr(issue.fields, 'description', '') or '',
            'url': f"{self.jira_url}/browse/{issue.key}"
        }
        
        raw_fields = self._get_issue_raw_fields(issue)
        ticket.update(self._extract_advanced_fields(raw_fields))
        status_data = raw_fields.get('status') or {}
        status_category = status_data.get('statusCategory') or {}
        ticket['status_category'] = status_category.get('name')
        fix_versions = raw_fields.get('fixVersions') or []
        ticket['fix_versions'] = [fv.get('name') for fv in fix_versions if isinstance(fv, dict) and fv.get('name')]
        components = raw_fields.get('components') or []
        ticket['components'] = [comp.get('name') for comp in components if isinstance(comp, dict) and comp.get('name')]
        ticket['due_date'] = raw_fields.get('duedate')
        
        # Sanitize all values to ensure JSON serialization (convert PropertyHolder objects)
        return self._sanitize_for_json(ticket)
    
    @staticmethod
    def _sanitize_for_json(data: Any) -> Any:
        """Recursively convert all values to JSON-serializable primitives"""
        if isinstance(data, dict):
            return {k: JiraIntegration._sanitize_for_json(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [JiraIntegration._sanitize_for_json(item) for item in data]
        elif isinstance(data, (str, int, float, bool, type(None))):
            return data
        else:
            # Convert any complex objects (like PropertyHolder) to string
            return str(data)
    
    @staticmethod
    def _get_issue_raw_fields(issue: Any) -> Dict[str, Any]:
        """Safely extract raw field payload from Issue or fallback object"""
        if hasattr(issue, 'raw') and isinstance(issue.raw, dict):
            return issue.raw.get('fields', {}) or {}
        return {}
    
    def _extract_advanced_fields(self, raw_fields: Dict[str, Any]) -> Dict[str, Any]:
        """Enrich ticket with sprint, epic, story points, and team info"""
        enrichment: Dict[str, Any] = {
            'sprints': [],
            'current_sprint': None,
            'current_sprint_name': None,
            'current_sprint_goal': None,
            'story_points': None,
            'epic_link': None,
            'team': None
        }
        
        # Story points / epic / team
        if self.story_points_field_id:
            enrichment['story_points'] = raw_fields.get(self.story_points_field_id)
        if self.epic_field_id:
            enrichment['epic_link'] = raw_fields.get(self.epic_field_id)
        if self.team_field_id:
            team = raw_fields.get(self.team_field_id)
            if isinstance(team, dict):
                enrichment['team'] = team.get('name') or team.get('value')
            else:
                enrichment['team'] = team
        
        # Sprint parsing
        sprint_entries = self._get_sprint_entries(raw_fields)
        enrichment['sprints'] = sprint_entries
        if sprint_entries:
            active = next((s for s in sprint_entries if s.get('state') == 'ACTIVE'), None)
            upcoming = next((s for s in sprint_entries if s.get('state') == 'FUTURE'), None)
            latest = sprint_entries[-1]
            chosen = active or upcoming or latest
            if chosen:
                enrichment['current_sprint'] = chosen
                enrichment['current_sprint_name'] = chosen.get('name')
                enrichment['current_sprint_goal'] = chosen.get('goal')
        
        return enrichment
    
    def _get_sprint_entries(self, raw_fields: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Extract structured sprint information from Jira's custom field"""
        if not self.sprint_field_id:
            return []
        
        sprint_field_value = raw_fields.get(self.sprint_field_id)
        if not sprint_field_value:
            return []
        
        entries = sprint_field_value if isinstance(sprint_field_value, list) else [sprint_field_value]
        parsed_entries: List[Dict[str, Any]] = []
        
        for entry in entries:
            parsed = self._parse_single_sprint_entry(entry)
            if parsed:
                parsed_entries.append(parsed)
        
        parsed_entries.sort(key=lambda s: s.get('startDate') or s.get('endDate') or '')
        return parsed_entries
    
    def _parse_single_sprint_entry(self, entry: Any) -> Dict[str, Any]:
        """Convert sprint payload to structured dict"""
        if isinstance(entry, dict):
            return {
                'id': entry.get('id'),
                'name': entry.get('name'),
                'state': entry.get('state'),
                'goal': entry.get('goal'),
                'board_id': entry.get('rapidViewId') or entry.get('originBoardId'),
                'startDate': entry.get('startDate'),
                'endDate': entry.get('endDate'),
                'completeDate': entry.get('completeDate')
            }
        
        if isinstance(entry, str):
            match_section = entry.split('[', 1)[-1].rstrip(']')
            kv_pairs = {}
            for segment in match_section.split(','):
                if '=' not in segment:
                    continue
                key, value = segment.split('=', 1)
                kv_pairs[key.strip()] = value.strip()
            return {
                'id': kv_pairs.get('id'),
                'name': kv_pairs.get('name'),
                'state': kv_pairs.get('state'),
                'goal': kv_pairs.get('goal'),
                'board_id': kv_pairs.get('rapidViewId'),
                'startDate': kv_pairs.get('startDate'),
                'endDate': kv_pairs.get('endDate'),
                'completeDate': kv_pairs.get('completeDate')
            }
        
        return {}
    
    def _augment_jql_with_board_filter(self, jql_query: Optional[str], board_name: Optional[str]) -> str:
        """Combine user JQL with board filter JQL (if board provided)"""
        base_jql = (jql_query or '').strip()
        if not board_name:
            return base_jql
        
        project_hint = self._extract_project_key_from_jql(base_jql)
        board_filter_jql = self._get_board_filter_jql(board_name, project_hint)
        if not board_filter_jql:
            console.print(f"[yellow]⚠️  Could not resolve board '{board_name}'. Using original JQL only.[/yellow]")
            return base_jql
        
        console.print(f"[dim]   Applying board filter: {board_name}[/dim]")
        if not base_jql:
            return board_filter_jql
        return f"({board_filter_jql}) AND ({base_jql})"
    
    @staticmethod
    def _extract_project_key_from_jql(jql_query: str) -> Optional[str]:
        """Best-effort extraction of project key from JQL"""
        pattern = re.compile(r'project\s*=\s*"?([A-Z0-9_-]+)"?', re.IGNORECASE)
        match = pattern.search(jql_query)
        if match:
            return match.group(1)
        return None
    
    def _get_board_filter_jql(self, board_name: str, project_key: Optional[str]) -> Optional[str]:
        """Fetch board filter JQL using Jira Agile API"""
        cache_key = board_name.strip().lower()
        if cache_key in self.board_filter_cache:
            return self.board_filter_cache[cache_key]
        
        try:
            server = self.jira._options['server']
            start_at = 0
            max_results = 50
            normalized_board = cache_key
            found_board = None
            
            console.print(f"[dim]   Resolving board '{board_name}' via Jira Agile API...[/dim]")
            while True:
                params = {
                    'startAt': start_at,
                    'maxResults': max_results
                }
                if project_key:
                    params['projectKeyOrId'] = project_key
                
                boards_resp = self.jira._session.get(
                    f"{server}/rest/agile/1.0/board",
                    params=params
                )
                boards_resp.raise_for_status()
                boards_data = boards_resp.json()
                
                for board in boards_data.get('values', []):
                    if board.get('name', '').strip().lower() == normalized_board:
                        found_board = board
                        break
                
                if found_board or boards_data.get('isLast', True):
                    break
                
                start_at += max_results
            
            if not found_board:
                console.print(f"[yellow]⚠️  Board '{board_name}' not found (project hint: {project_key}).[/yellow]")
                return None
            
            filter_id = found_board.get('filterId')
            if not filter_id:
                console.print(f"[yellow]⚠️  Board '{board_name}' has no filterId.[/yellow]")
                return None
            
            filter_resp = self.jira._session.get(f"{server}/rest/api/3/filter/{filter_id}")
            filter_resp.raise_for_status()
            filter_data = filter_resp.json()
            filter_jql = filter_data.get('jql')
            if filter_jql:
                self.board_filter_cache[cache_key] = filter_jql
            return filter_jql
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to resolve board '{board_name}': {e}[/yellow]")
            return None
    
    def list_tickets(
        self,
        project: Optional[str] = None,
        labels: Optional[List[str]] = None,
        status: Optional[str] = None,
        assignee: Optional[str] = None,
        priority: Optional[str] = None,
        issue_type: Optional[str] = None,
        max_results: int = 50,
        board_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        List Jira tickets with filters
        
        Args:
            project: Project key (e.g., 'AUDIT', 'SEC')
            board_name: Optional Jira board/dashboard name (e.g., 'XDR SRE Sprint')
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
            
            base_jql = ' AND '.join(jql_parts) if jql_parts else ''
            jql = self._augment_jql_with_board_filter(base_jql, board_name)
            if not jql:
                jql = 'ORDER BY created DESC'
            
            console.print(f"[cyan]🔍 Searching Jira with JQL: {jql}[/cyan]")
            
            # Execute search using new Jira Cloud API (POST method)
            try:
                response = self.jira._session.post(
                    f"{self.jira._options['server']}/rest/api/3/search",
                    json={
                        'jql': jql,
                        'maxResults': max_results,
                        'fields': '*all'
                    },
                    headers={'Content-Type': 'application/json'}
                )
                response.raise_for_status()
                search_results = response.json()
                
                issues = self._build_issue_objects(search_results)
            except Exception as e:
                console.print(f"[red]❌ Error searching: {e}[/red]")
                return []
            
            # Format results
            tickets = [self._build_ticket_dict(issue) for issue in issues]
            
            console.print(f"[green]✅ Found {len(tickets)} tickets[/green]")
            return tickets
        
        except Exception as e:
            console.print(f"[red]❌ Error listing tickets: {e}[/red]")
            return []
    
    def search_jql(
        self,
        jql_query: str,
        max_results: int = 1000,
        paginate: bool = True,
        board_name: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Advanced JQL search with automatic pagination
        
        Args:
            jql_query: JQL query string (e.g., 'project = AUDIT AND status = "In Progress"')
            max_results: Maximum number of results (default 1000, use 0 for all)
            paginate: If True, automatically fetch all results using pagination
            board_name: Optional board/dashboard name to auto-apply its saved filter
        
        Returns:
            List of ticket dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            jql_query = self._augment_jql_with_board_filter(jql_query, board_name)
            console.print(f"[cyan]🔍 Executing JQL: {jql_query}[/cyan]")
            
            # Jira API limits to 100 per request, so we need pagination
            if paginate:
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
                        # Determine current page size respecting user max_results limit
                        current_page_size = page_size
                        if max_results > 0:
                            remaining = max_results - total_fetched
                            if remaining <= 0:
                                console.print(f"[dim]   Already fetched requested max results ({max_results}).[/dim]")
                                break
                            current_page_size = min(page_size, remaining)
                        
                        response = self.jira._session.post(
                            f"{self.jira._options['server']}/rest/api/3/search/jql",
                            json={
                                'jql': jql_query,
                                'startAt': start_at,
                                'maxResults': current_page_size,
                                'fields': '*all'
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
                        
                        page_issues = self._build_issue_objects(search_results)
                    except Exception as e:
                        console.print(f"[red]❌ Error fetching page: {e}[/red]")
                        raise
                    
                    if not page_issues:
                        break  # No more results
                    
                    # Process this page
                    for issue in page_issues:
                        ticket = self._build_ticket_dict(issue)
                        tickets.append(ticket)
                        total_fetched += 1
                        
                        # Check if we've hit the max_results limit
                        if max_results > 0 and total_fetched >= max_results:
                            break
                    
                    console.print(f"[dim]   Fetched {total_fetched} tickets so far...[/dim]")
                    
                    # Check stopping conditions
                    # 1. No more results on this page (most reliable indicator)
                    if len(page_issues) < current_page_size:
                        console.print(f"[dim]   Last page reached (got {len(page_issues)} < {current_page_size})[/dim]")
                        break
                    
                    # 2. Reached the total available from Jira (only if total is reliable)
                    if total_available is not None and total_available > 0 and total_fetched >= total_available:
                        console.print(f"[dim]   All available tickets fetched ({total_fetched}/{total_available})[/dim]")
                        break
                    
                    # 3. Hit the user-specified max_results limit
                    if max_results > 0 and total_fetched >= max_results:
                        console.print(f"[dim]   Max results limit reached ({total_fetched}/{max_results})[/dim]")
                        break
                    
                    start_at += current_page_size
                
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
                            'fields': '*all'
                        },
                        headers={'Content-Type': 'application/json'}
                    )
                    response.raise_for_status()
                    search_results = response.json()
                    
                    issues = self._build_issue_objects(search_results)
                except Exception as e:
                    console.print(f"[red]❌ Error fetching tickets: {e}[/red]")
                    return []
                
                tickets = [self._build_ticket_dict(issue) for issue in issues]
                
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
                            row = {k: self._serialize_value_for_export(v) for k, v in ticket.items()}
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

