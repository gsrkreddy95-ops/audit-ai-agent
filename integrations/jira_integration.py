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
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
from pathlib import Path

from rich.console import Console

console = Console()


class JiraIntegration:
    def _request_jira_search_page(
        self,
        jql_query: str,
        start_at: int,
        max_results: int,
        fields: List[str]
    ) -> Dict[str, Any]:
        """
        Call Jira search endpoint (GET /rest/api/3/search/jql).
        Jira removed the POST /search endpoint for Cloud instances.
        """
        server = self.jira._options['server']
        fields_param = ",".join(fields)
        try:
            params = {
                "jql": jql_query,
                "startAt": start_at,
                "maxResults": max_results,
                "fields": fields_param
            }
            response = self.jira._session.get(
                f"{server}/rest/api/3/search/jql",
                params=params
            )
            if start_at == 0:
                console.print(
                    f"[dim]   API Request: GET /rest/api/3/search/jql (startAt={start_at}, maxResults={max_results})[/dim]"
                )
            response.raise_for_status()
            return response.json()
        except Exception as error:
            console.print(f"[red]❌ Jira search request failed: {error}[/red]")
            raise

    @staticmethod
    def _generate_date_slices(start_date: datetime, end_date: datetime, slice_days: int = 7) -> List[Tuple[datetime, datetime]]:
        """Generate inclusive date slices between start_date and end_date."""
        slices: List[Tuple[datetime, datetime]] = []
        current = start_date
        while current <= end_date:
            slice_end = min(current + timedelta(days=slice_days - 1), end_date)
            slices.append((current, slice_end))
            current = slice_end + timedelta(days=1)
        return slices

    @staticmethod
    def _split_condition_and_order(jql_query: str) -> Tuple[str, str]:
        """Split a JQL string into its filter condition and ORDER BY clause."""
        match = re.search(r'\border\s+by\b', jql_query, re.IGNORECASE)
        if match:
            condition = jql_query[:match.start()].strip()
            order_clause = jql_query[match.start():].strip()
            return condition, order_clause
        return jql_query.strip(), ''

    def _fetch_with_date_slices(
        self,
        condition_jql: str,
        order_clause: str,
        start_date: datetime,
        end_date: datetime
    ) -> List[Dict[str, Any]]:
        """Split the date range into smaller slices and aggregate results."""
        slices = self._generate_date_slices(start_date, end_date)
        total_slices = len(slices)
        console.print(
            f"[yellow]⚠️  Jira returned the 1000-ticket safety cap. "
            f"Applying date slicing across {total_slices} slices to fetch exact results.[/yellow]"
        )
        aggregated: List[Dict[str, Any]] = []
        for idx, (slice_start, slice_end) in enumerate(slices, start=1):
            order_segment = order_clause if order_clause else "ORDER BY created ASC"
            slice_jql = (
                f"({condition_jql}) AND created >= '{slice_start.strftime('%Y-%m-%d')}' "
                f"AND created <= '{slice_end.strftime('%Y-%m-%d')}' {order_segment}"
            )
            console.print(
                f"[cyan]   📅 Slice {idx}/{total_slices}: "
                f"{slice_start.strftime('%Y-%m-%d')} → {slice_end.strftime('%Y-%m-%d')}[/cyan]"
            )
            slice_tickets = self.search_jql(
                jql_query=slice_jql,
                max_results=0,
                paginate=True,
                board_name=None,
                _allow_date_slicing=False
            )
            # If a weekly slice still returns a high count (approaching 1000),
            # fall back to day-bucketing to ensure accuracy and reduce payloads.
            if len(slice_tickets) >= 900:
                console.print(
                    f"[dim]   Slice {idx}: {len(slice_tickets)} tickets near cap. Switching to day slicing.[/dim]"
                )
                slice_tickets = self._fetch_with_day_slices(
                    condition_jql=condition_jql,
                    order_clause=order_segment,
                    week_start=slice_start,
                    week_end=slice_end
                )
            aggregated.extend(slice_tickets)
        return aggregated

    def _fetch_with_day_slices(
        self,
        condition_jql: str,
        order_clause: str,
        week_start: datetime,
        week_end: datetime
    ) -> List[Dict[str, Any]]:
        """Fetch a weekly slice by day to avoid hitting the 1000 cap within a week."""
        day_slices = self._generate_date_slices(week_start, week_end, slice_days=1)
        day_results: List[Dict[str, Any]] = []
        for d_idx, (day_start, day_end) in enumerate(day_slices, start=1):
            day_jql = (
                f"({condition_jql}) AND created >= '{day_start.strftime('%Y-%m-%d')}' "
                f"AND created <= '{day_end.strftime('%Y-%m-%d')}' {order_clause}"
            )
            console.print(
                f"[dim]      📅 Day {d_idx}/{len(day_slices)}: {day_start.strftime('%Y-%m-%d')}[/dim]"
            )
            day_tickets = self.search_jql(
                jql_query=day_jql,
                max_results=0,
                paginate=True,
                board_name=None,
                _allow_date_slicing=False
            )
            day_results.extend(day_tickets)
        return day_results

    # ---------- Intent to JQL builder ----------
    @staticmethod
    def _quote_list(items: Optional[List[str]]) -> Optional[str]:
        if not items:
            return None
        safe = [str(x).strip().replace('"', '\\"') for x in items if str(x).strip()]
        return ", ".join([f"\"{s}\"" for s in safe]) if safe else None

    def build_jql_from_intent(
        self,
        project: Optional[str] = "XDR",
        labels: Optional[List[str]] = None,
        created_start: Optional[str] = None,
        created_end: Optional[str] = None,
        statuses: Optional[List[str]] = None,
        assignee: Optional[str] = None,
        text_contains: Optional[str] = None,
        order_by: Optional[str] = "created ASC",
        board_name: Optional[str] = None
    ) -> str:
        """
        Build robust JQL from natural-language style inputs.
        - Normalizes dates; uses half-open end date if given as inclusive.
        - Uses labels in ("...") for reliability.
        - Adds default project when omitted.
        - Appends ORDER BY (default created ASC).
        """
        clauses: List[str] = []
        if project:
            clauses.append(f"project = {project}")
        if labels:
            quoted = self._quote_list(labels)
            if quoted:
                clauses.append(f"labels in ({quoted})")
        if created_start and created_end:
            # Prefer half-open end date if provided as YYYY-MM-DD; convert to < next-day
            try:
                end_dt = datetime.strptime(created_end, "%Y-%m-%d")
                end_next = end_dt + timedelta(days=1)
                clauses.append(f"created >= '{created_start}'")
                clauses.append(f"created < '{end_next.strftime('%Y-%m-%d')}'")
            except ValueError:
                # Fallback to closed interval
                clauses.append(f"created >= '{created_start}'")
                clauses.append(f"created <= '{created_end}'")
        elif created_start:
            clauses.append(f"created >= '{created_start}'")
        elif created_end:
            try:
                end_dt = datetime.strptime(created_end, "%Y-%m-%d")
                end_next = end_dt + timedelta(days=1)
                clauses.append(f"created < '{end_next.strftime('%Y-%m-%d')}'")
            except ValueError:
                clauses.append(f"created <= '{created_end}'")
        if statuses:
            quoted = self._quote_list(statuses)
            if quoted:
                clauses.append(f"status in ({quoted})")
        if assignee:
            clauses.append(f'assignee = "{assignee}"')
        if text_contains:
            # text ~ operator via text ~ or summary ~; use text ~ for breadth
            safe_text = text_contains.replace('"', '\\"')
            clauses.append(f'text ~ "{safe_text}"')
        base = " AND ".join(clauses) if clauses else ""
        # Merge board filter if provided
        if board_name:
            filter_jql = self._get_board_filter_jql(board_name, self._extract_project_key_from_jql(base))
            if filter_jql:
                base = f"({filter_jql}) AND ({base})" if base else filter_jql
        if order_by:
            return f"{base} ORDER BY {order_by}"
        return base

    @staticmethod
    def _get_created_range(created_rules: Optional[Dict[str, datetime]]) -> Optional[Tuple[datetime, datetime]]:
        """Derive inclusive start/end dates from created rules."""
        if not created_rules:
            return None
        start_date: Optional[datetime] = None
        end_date: Optional[datetime] = None
        if '>=' in created_rules:
            start_date = created_rules['>=']
        elif '>' in created_rules:
            start_date = created_rules['>'] + timedelta(days=1)
        if '<=' in created_rules:
            end_date = created_rules['<=']
        elif '<' in created_rules:
            end_date = created_rules['<'] - timedelta(days=1)
        if start_date and end_date and start_date <= end_date:
            return (start_date, end_date)
        return None

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
        """
        Create Issue objects while keeping raw payload for advanced parsing
        
        Note: Using SimpleIssue fallback for all issues from /search/jql endpoint
        because the jira library's Issue class doesn't work reliably with GET responses
        """
        issues = []
        for issue_data in search_results.get('issues', []):
            # Always use SimpleIssue for reliability with /search/jql GET responses
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
    
    @staticmethod
    def _compact_ticket_for_llm(ticket: Dict[str, Any]) -> Dict[str, Any]:
        """
        Reduce ticket payload size for LLM safety.
        Keeps essential fields only and drops heavy text like description.
        """
        allowed_keys = {
            'key', 'summary', 'status', 'priority', 'assignee', 'reporter',
            'created', 'updated', 'labels', 'issue_type', 'url',
            'fix_versions', 'components', 'due_date', 'status_category'
        }
        compacted: Dict[str, Any] = {}
        for k in allowed_keys:
            if k in ticket:
                compacted[k] = ticket[k]
        # Truncate summary if excessively long
        if 'summary' in compacted and isinstance(compacted['summary'], str) and len(compacted['summary']) > 300:
            compacted['summary'] = compacted['summary'][:300] + '…'
        return compacted
    
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
        raw_payload = getattr(issue, 'raw', None)
        if isinstance(raw_payload, dict):
            return raw_payload.get('fields', {}) or {}
        # Some jira Issue objects expose `.raw` as PropertyHolder (type 'obj').
        if raw_payload is not None and hasattr(raw_payload, '__dict__'):
            maybe_dict = getattr(raw_payload, '__dict__', {})
            if isinstance(maybe_dict, dict):
                fields = maybe_dict.get('fields')
                if isinstance(fields, dict):
                    return fields
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
            return self._normalize_jql_dates(base_jql)
        
        project_hint = self._extract_project_key_from_jql(base_jql)
        board_filter_jql = self._get_board_filter_jql(board_name, project_hint)
        if not board_filter_jql:
            console.print(f"[yellow]⚠️  Could not resolve board '{board_name}'. Using original JQL only.[/yellow]")
            return self._normalize_jql_dates(base_jql)
        
        console.print(f"[dim]   Applying board filter: {board_name}[/dim]")
        if not base_jql:
            return self._normalize_jql_dates(board_filter_jql)
        combined = f"({board_filter_jql}) AND ({base_jql})"
        return self._normalize_jql_dates(combined)
    
    @staticmethod
    def _normalize_jql_dates(jql_query: str) -> str:
        """
        Fix common JQL date formatting issues that break Jira queries.
        
        Jira requires dates in format: 'YYYY-MM-DD' or 'YYYY-MM-DD HH:MM'
        This fixes:
        - Double-quoted dates with time: "2025-06-01" -> '2025-06-01'
        - Ensures proper quote style
        """
        if not jql_query:
            return jql_query
        
        # Pattern: created/updated/resolved >= "YYYY-MM-DD" (with double quotes)
        # Fix: Change to single quotes or remove quotes entirely
        import re
        
        # Replace double-quoted ISO dates with single-quoted ones
        # Matches: created >= "2025-06-01" or created >= "2025-06-01 12:00"
        pattern = r'(created|updated|resolved|due)\s*(>=|<=|>|<|=)\s*"(\d{4}-\d{2}-\d{2}(?:\s+\d{2}:\d{2})?)"'
        normalized = re.sub(pattern, r"\1 \2 '\3'", jql_query, flags=re.IGNORECASE)
        
        if normalized != jql_query:
            console.print(f"[dim]   Normalized JQL dates: {normalized}[/dim]")
        
        return normalized
    
    @staticmethod
    def _parse_jira_datetime(value: Optional[str]) -> Optional[datetime]:
        """Parse Jira date/datetime strings into naive datetime objects."""
        if not value:
            return None
        text = value.strip().strip("\"'")
        
        # Date only
        try:
            if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
                return datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            return None
        
        # Normalize timezone formats (e.g., +0000, Z, +00:00)
        def _normalize_tz(v: str) -> str:
            if v.endswith('Z'):
                return v[:-1] + '+0000'
            if re.search(r'[+-]\d{2}:\d{2}$', v):
                return v[:-3] + v[-2:]
            return v
        
        candidates = [
            "%Y-%m-%dT%H:%M:%S.%f%z",
            "%Y-%m-%dT%H:%M:%S%z",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S",
        ]
        normalized_text = _normalize_tz(text)
        for fmt in candidates:
            try:
                dt = datetime.strptime(normalized_text, fmt)
                return dt.replace(tzinfo=None)
            except ValueError:
                continue
        return None
    
    @staticmethod
    def _extract_post_filters_from_jql(jql_query: str) -> Dict[str, Any]:
        """Extract date/label/project filter constraints from JQL for post-filter validation."""
        filters: Dict[str, Any] = {
            'created': {},
            'labels': set(),
            'project_keys': set()
        }
        if not jql_query:
            return filters
        
        # DEBUG: Log the JQL query being parsed
        console.print(f"[dim]   🔍 Extracting filters from JQL: {jql_query[:100]}...[/dim]")
        
        # Date filters (created field) - handle both single and double quotes
        date_pattern = re.compile(
            r"(created)\s*(>=|<=|>|<|=)\s*['\"]([^'\"]+)['\"]",
            re.IGNORECASE
        )
        for field, op, value in date_pattern.findall(jql_query):
            parsed = JiraIntegration._parse_jira_datetime(value)
            if parsed:
                filters.setdefault(field.lower(), {})[op] = parsed
        
        # Label equality (labels = VALUE) - handle both single and double quotes
        # Pattern 1: Quoted labels: labels = "VALUE" or labels = 'VALUE'
        label_quoted_pattern = re.compile(r"labels\s*=\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)
        for match in label_quoted_pattern.findall(jql_query):
            label = match.strip().lower()
            if label:
                filters['labels'].add(label)
        
        # Pattern 2: Unquoted labels: labels = VALUE
        # Use a more explicit pattern that captures the full label value
        # Match: labels = VALUE where VALUE is alphanumeric + underscore/hyphen
        # Stop when we hit whitespace followed by AND/OR/ORDER or end of string
        label_unquoted_pattern = re.compile(
            r'\blabels\s*=\s*([A-Za-z0-9_\-]+)',
            re.IGNORECASE
        )
        for match in label_unquoted_pattern.finditer(jql_query):
            label_value = match.group(1).strip().lower()
            # Verify this is a real label by checking what follows
            match_end = match.end()
            remaining_text = jql_query[match_end:].strip()
            # If followed by AND, OR, ORDER, or another field, it's a complete label
            # Also accept if it's at the end of the query
            if (not remaining_text or 
                re.match(r'^\s*(AND|OR|ORDER|created|updated|project|labels|status|assignee|reporter|priority|issuetype)', remaining_text, re.IGNORECASE)):
                if label_value and len(label_value) > 1 and label_value not in ['and', 'or', 'not', 'in', 'is', 'was', 'changed', 'created', 'updated']:
                    filters['labels'].add(label_value)
                    console.print(f"[dim]      ✅ Extracted label: '{label_value}' from JQL[/dim]")
        
        # labels in (...) pattern
        label_in_pattern = re.compile(r"labels\s+in\s*\(([^)]+)\)", re.IGNORECASE)
        for group in label_in_pattern.findall(jql_query):
            items = [item.strip().strip('\'"') for item in group.split(',')]
            for item in items:
                if item:
                    filters['labels'].add(item.lower())
        
        # Project filters (project = KEY or project in (KEY1, KEY2))
        project_eq_pattern = re.compile(r"project\s*=\s*['\"]?([A-Z0-9_-]+)['\"]?", re.IGNORECASE)
        for match in project_eq_pattern.findall(jql_query):
            proj = match.strip('\'"').upper()
            if proj:
                filters['project_keys'].add(proj)
        
        project_in_pattern = re.compile(r"project\s+in\s*\(([^)]+)\)", re.IGNORECASE)
        for group in project_in_pattern.findall(jql_query):
            items = [item.strip().strip('\'"') for item in group.split(',')]
            for item in items:
                if item:
                    filters['project_keys'].add(item.upper())
        
        # Clean up empty filters
        if not filters['labels']:
            filters.pop('labels', None)
        if not filters.get('created'):
            filters.pop('created', None)
        if not filters['project_keys']:
            filters.pop('project_keys', None)
        
        # DEBUG: Log final extracted filters
        console.print(f"[dim]   🔍 Extracted filters: created={filters.get('created')}, labels={filters.get('labels')}, project_keys={filters.get('project_keys')}[/dim]")
        
        return filters
    
    def _apply_post_filters(self, tickets: List[Dict[str, Any]], jql_query: str) -> List[Dict[str, Any]]:
        """Apply additional filtering to enforce date/label constraints even if Jira misbehaves."""
        filters = self._extract_post_filters_from_jql(jql_query)
        
        # DEBUG: Log extracted filters
        if filters:
            console.print(f"[dim]   🔍 Post-filter active: {filters}[/dim]")
        else:
            console.print(f"[dim]   ⚠️  No post-filters extracted from JQL (Jira API must be working correctly)[/dim]")
            return tickets
        
        filtered: List[Dict[str, Any]] = []
        dropped_reasons = {'created': 0, 'labels': 0, 'project': 0}
        sample_dropped = []  # Track first few dropped tickets for debugging
        
        for ticket in tickets:
            include = True
            drop_reason = None
            
            # Created date filters
            created_rules = filters.get('created')
            if created_rules:
                created_str = ticket.get('created', '')
                created_dt = self._parse_jira_datetime(created_str)
                if not created_dt:
                    include = False
                    drop_reason = f"created date unparseable: {created_str}"
                    dropped_reasons['created'] += 1
                else:
                    # Compare dates only (ignore time component)
                    created_date = created_dt.date()
                    for op, boundary in created_rules.items():
                        boundary_date = boundary.date() if hasattr(boundary, 'date') else boundary
                        if op == '>=' and created_date < boundary_date:
                            include = False
                            drop_reason = f"created {created_date} < {boundary_date}"
                            dropped_reasons['created'] += 1
                            break
                        elif op == '<=' and created_date > boundary_date:
                            include = False
                            drop_reason = f"created {created_date} > {boundary_date}"
                            dropped_reasons['created'] += 1
                            break
                        elif op == '>' and created_date <= boundary_date:
                            include = False
                            drop_reason = f"created {created_date} <= {boundary_date}"
                            dropped_reasons['created'] += 1
                            break
                        elif op == '<' and created_date >= boundary_date:
                            include = False
                            drop_reason = f"created {created_date} >= {boundary_date}"
                            dropped_reasons['created'] += 1
                            break
                        elif op == '=' and created_date != boundary_date:
                            include = False
                            drop_reason = f"created {created_date} != {boundary_date}"
                            dropped_reasons['created'] += 1
                            break
            
            # Label filters (require all specified labels to be present)
            if include and 'labels' in filters:
                ticket_labels = {label.lower() for label in ticket.get('labels', [])}
                required_labels = filters['labels']
                if not required_labels.issubset(ticket_labels):
                    include = False
                    missing = required_labels - ticket_labels
                    drop_reason = f"missing labels: {missing}"
                    dropped_reasons['labels'] += 1
            
            # Project key filters (ensure ticket key prefix matches, e.g., XDR-12345)
            if include and 'project_keys' in filters:
                key = (ticket.get('key') or '').upper()
                # Only keep tickets whose key starts with one of the project prefixes
                if not any(key.startswith(f"{proj}-") for proj in filters['project_keys']):
                    include = False
                    drop_reason = f"key {key} doesn't match project prefixes {filters['project_keys']}"
                    dropped_reasons['project'] += 1
            
            if include:
                filtered.append(ticket)
            elif len(sample_dropped) < 3:
                sample_dropped.append(f"{ticket.get('key', '?')}: {drop_reason}")
        
        # Always log post-filter results (even if no reduction)
        if len(filtered) != len(tickets):
            console.print(
                f"[yellow]   🔍 Post-filter reduced tickets from {len(tickets)} to {len(filtered)} "
                f"(created drops: {dropped_reasons.get('created', 0)}, "
                f"labels drops: {dropped_reasons.get('labels', 0)}, "
                f"project drops: {dropped_reasons.get('project', 0)})[/yellow]"
            )
            if sample_dropped:
                console.print(f"[dim]      Sample drops: {', '.join(sample_dropped)}[/dim]")
        else:
            console.print(
                f"[yellow]   ⚠️  Post-filter applied but all {len(tickets)} tickets passed filters![/yellow]"
            )
            console.print(f"[dim]      Filters: {filters}[/dim]")
            # Show sample ticket data for debugging
            if tickets:
                sample = tickets[0]
                console.print(f"[dim]      Sample ticket: key={sample.get('key')}, created={sample.get('created')}, labels={sample.get('labels')}[/dim]")
        
        return filtered
    
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
            
            # Execute search using Jira Cloud API
            try:
                response = self.jira._session.get(
                    f"{self.jira._options['server']}/rest/api/3/search/jql",
                    params={
                        'jql': jql,
                        'maxResults': max_results
                    }
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
        max_results: int = 0,
        paginate: bool = True,
        board_name: Optional[str] = None,
        _allow_date_slicing: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Advanced JQL search with automatic pagination
        
        Args:
            jql_query: JQL query string (e.g., 'project = AUDIT AND status = "In Progress"')
            max_results: Maximum number of results (default 0 = fetch ALL matching tickets, no artificial cap)
            paginate: If True, automatically fetch all results using pagination
            board_name: Optional board/dashboard name to auto-apply its saved filter
        
        Returns:
            List of ticket dictionaries
        """
        if not self._check_connection():
            return []
        
        try:
            jql_query = self._augment_jql_with_board_filter(jql_query, board_name)
            condition_jql, order_clause = self._split_condition_and_order(jql_query)
            console.print(f"[cyan]🔍 Executing JQL: {jql_query}[/cyan]")
            
            # Jira API limits to 100 per request, so we need pagination
            if paginate:
                filters_for_slicing = self._extract_post_filters_from_jql(condition_jql)
                created_rules = filters_for_slicing.get('created')
                created_range = self._get_created_range(created_rules)
                safety_enabled = bool(created_range)
                
                # Slice-first mode: when a created date range exists, fetch by weekly slices immediately
                if safety_enabled and _allow_date_slicing:
                    console.print("[dim]   Slice-first: created window detected, fetching weekly slices for accuracy.[/dim]")
                    sliced_tickets = self._fetch_with_date_slices(
                        condition_jql=condition_jql,
                        order_clause=order_clause,
                        start_date=created_range[0],  # type: ignore[index]
                        end_date=created_range[1]     # type: ignore[index]
                    )
                    sliced_tickets = self._apply_post_filters(sliced_tickets, jql_query)
                    # LLM safety: compact ticket payload
                    sliced_tickets = [self._compact_ticket_for_llm(t) for t in sliced_tickets]
                    console.print(f"[green]✅ Found {len(sliced_tickets)} tickets after date slicing[/green]")
                    return sliced_tickets
                
                tickets = []
                start_at = 0
                page_size = 100  # Jira API max per request
                total_fetched = 0
                
                MAX_NO_DATE_RESULTS = 5000
                guard_triggered = False
                
                if safety_enabled:
                    SAFETY_LIMIT = 1000
                    console.print(
                        "[dim]   Created date filter detected. Safety cap set to 1000; "
                        "date slicing will auto-run if Jira ignores filters.[/dim]"
                    )
                else:
                    SAFETY_LIMIT = None
                    console.print(
                        "[dim]   No created date filter detected. Fetching all tickets "
                        "(no safety cap—results may exceed 1000).[/dim]"
                    )
                
                if max_results > 0:
                    effective_max: Optional[int] = max_results
                else:
                    effective_max = SAFETY_LIMIT
                
                console.print(f"[cyan]📄 Fetching results with pagination (max: {effective_max or 'ALL'})...[/cyan]")
                if SAFETY_LIMIT:
                    console.print(
                        f"[dim]   Safety limit: {SAFETY_LIMIT} tickets (post-filter will apply exact JQL constraints)[/dim]"
                    )
                
                total_available = None  # Will be set after first request
                
                while True:
                    # Fetch a page of results using Jira Cloud's new JQL API
                    try:
                        # Determine current page size respecting limits (if any)
                        current_page_size = page_size
                        if effective_max is not None:
                            remaining = effective_max - total_fetched
                            if remaining <= 0:
                                console.print(f"[dim]   Limit reached ({effective_max}). Stopping pagination.[/dim]")
                                break
                            current_page_size = min(page_size, remaining)
                        
                        fields_list = [
                            "key", "summary", "status", "priority", "assignee",
                            "reporter", "created", "updated", "labels", "issuetype",
                            "description", "fixVersions", "components", "duedate"
                        ]
                        search_results = self._request_jira_search_page(
                            jql_query=jql_query,
                            start_at=start_at,
                            max_results=current_page_size,
                            fields=fields_list
                        )
                        
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
                        
                        # DEBUG: Check if date filter is working by inspecting first few tickets
                        if start_at == 0 and page_issues and 'created' in jql_query.lower():
                            console.print(f"[dim]   🔍 DEBUG: Checking if date filter is working...[/dim]")
                            for idx, issue in enumerate(page_issues[:3]):  # Check first 3 tickets
                                created_date = getattr(getattr(issue, 'fields', None), 'created', 'N/A')
                                console.print(f"[dim]      Ticket {idx+1} created: {created_date}[/dim]")
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
                    
                    # SMART EARLY EXIT: If we've fetched way more than expected (3x Jira's reported total),
                    # and Jira is clearly ignoring filters, stop and rely on post-filter
                    if total_available and total_available > 0 and total_fetched > (total_available * 3):
                        console.print(f"[yellow]⚠️  Fetched {total_fetched} tickets but Jira reported total={total_available}[/yellow]")
                        console.print(f"[yellow]   Jira API is ignoring filters. Stopping pagination and applying post-filter...[/yellow]")
                        break
                    
                    # Check stopping conditions
                    # 1. No more results on this page (most reliable indicator)
                    if len(page_issues) < current_page_size:
                        console.print(f"[dim]   Last page reached (got {len(page_issues)} < {current_page_size})[/dim]")
                        break
                    
                    # 2. Reached the total available from Jira (only if total is reliable)
                    if total_available is not None and total_available > 0 and total_fetched >= total_available:
                        console.print(f"[dim]   All available tickets fetched ({total_fetched}/{total_available})[/dim]")
                        break
                    
                    # 3. Hit the safety/user-specified limit
                    if effective_max is not None and total_fetched >= effective_max:
                        console.print(f"[dim]   Limit reached ({total_fetched}/{effective_max})[/dim]")
                        break
                    
                    # 4. Guardrail for unbounded queries without created filters
                    if (
                        not safety_enabled
                        and effective_max is None
                        and total_fetched >= MAX_NO_DATE_RESULTS
                    ):
                        console.print(
                            f"[yellow]⚠️  Retrieved {total_fetched} tickets without a date filter.[/yellow]"
                        )
                        console.print(
                            "[yellow]   For performance reasons, please add a created date range to narrow the results.[/yellow]"
                        )
                        guard_triggered = True
                        break
                    
                    start_at += current_page_size
                
                if (
                    _allow_date_slicing
                    and safety_enabled
                    and effective_max is not None
                    and total_fetched >= effective_max
                ):
                    sliced_tickets = self._fetch_with_date_slices(
                        condition_jql=condition_jql,
                        order_clause=order_clause,
                        start_date=created_range[0],  # type: ignore[index]
                        end_date=created_range[1]     # type: ignore[index]
                    )
                    sliced_tickets = self._apply_post_filters(sliced_tickets, jql_query)
                    # LLM safety: compact ticket payload
                    sliced_tickets = [self._compact_ticket_for_llm(t) for t in sliced_tickets]
                    console.print(
                        f"[green]✅ Found {len(sliced_tickets)} tickets after date slicing[/green]"
                    )
                    return sliced_tickets
                
                tickets = self._apply_post_filters(tickets, jql_query)
                # LLM safety: compact ticket payload
                tickets = [self._compact_ticket_for_llm(t) for t in tickets]
                if guard_triggered:
                    console.print(
                        "[yellow]⚠️  Results truncated at 5,000 tickets due to missing created date filter.[/yellow]"
                    )
                console.print(f"[green]✅ Found {len(tickets)} tickets (fetched all pages)[/green]")
                return tickets
            else:
                # Single request (no pagination) using new Jira Cloud API (POST method)
                try:
                    fields_list = [
                        "key", "summary", "status", "priority", "assignee",
                        "reporter", "created", "updated", "labels", "issuetype",
                        "description", "fixVersions", "components", "duedate"
                    ]
                    page_size = max_results or 50
                    search_results = self._request_jira_search_page(
                        jql_query=jql_query,
                        start_at=0,
                        max_results=page_size,
                        fields=fields_list
                    )
                    issues = self._build_issue_objects(search_results)
                except Exception as e:
                    console.print(f"[red]❌ Error fetching tickets: {e}[/red]")
                    return []
                tickets = [self._build_ticket_dict(issue) for issue in issues]
                
                tickets = self._apply_post_filters(tickets, jql_query)
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
            # Determine base evidence directory
            evidence_base = os.getenv('LOCAL_EVIDENCE_PATH')
            if not evidence_base:
                evidence_base = str(Path.home() / "Documents" / "audit-evidence")
            current_year = os.getenv('SHAREPOINT_CURRENT_YEAR', 'FY2025')
            jira_dir = Path(evidence_base) / current_year / "JIRA_EXPORTS"
            
            # Generate output filename if not provided
            if not output_file:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                output_file = f"jira_tickets_{timestamp}.{output_format}"
            
            output_path = Path(output_file)
            if not output_path.is_absolute():
                output_path = jira_dir / output_path
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

