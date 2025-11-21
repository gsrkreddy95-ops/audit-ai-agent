"""
Agent Database - Persistent Storage for Work Data

This database stores:
- Jira tickets (categorized, searchable)
- AWS resources (tracked over time)
- Audit evidence (organized, queryable)
- Agent memory (preferences, learned facts)
- Task history (for analytics)

The agent can query this to provide intelligent insights like:
- "Show me all prod tickets from last month"
- "Which S3 buckets were created in 2025?"
- "What evidence do I have for RFI-AWS-001?"
- "What tasks failed in the last week?"
"""

import sqlite3
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from rich.console import Console
from contextlib import contextmanager

console = Console()


class AgentDatabase:
    """
    SQLite database for storing agent work data.
    
    Features:
    - Automatic schema creation
    - JSON field support
    - Transaction management
    - Query helpers
    - Full SQL access
    """
    
    def __init__(self, db_path: Optional[str] = None):
        """
        Initialize database connection.
        
        Args:
            db_path: Path to SQLite database file (default: ./agent_data.db)
        """
        if db_path is None:
            db_path = Path(__file__).parent.parent / "agent_data.db"
        
        self.db_path = str(db_path)
        self.conn = None
        self._initialize_database()
    
    def _initialize_database(self):
        """Create database and tables if they don't exist."""
        try:
            self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
            self.conn.row_factory = sqlite3.Row  # Return dict-like rows
            
            cursor = self.conn.cursor()
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            # Table 1: Jira Tickets
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS jira_tickets (
                    ticket_key TEXT PRIMARY KEY,
                    summary TEXT,
                    description TEXT,
                    status TEXT,
                    environment TEXT,  -- prod, non-prod, unknown
                    created_date TEXT,
                    updated_date TEXT,
                    assignee TEXT,
                    reporter TEXT,
                    project TEXT,
                    priority TEXT,
                    issue_type TEXT,
                    labels TEXT,  -- JSON array
                    metadata TEXT,  -- JSON object for extra fields
                    last_synced TEXT
                )
            """)
            
            # Table 2: AWS Resources
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS aws_resources (
                    resource_id TEXT PRIMARY KEY,
                    resource_arn TEXT,
                    resource_type TEXT,  -- ec2, s3, rds, kms, etc.
                    resource_name TEXT,
                    account TEXT,  -- ctr-int, ctr-prod, etc.
                    region TEXT,
                    created_date TEXT,
                    tags TEXT,  -- JSON object
                    metadata TEXT,  -- JSON object
                    last_scanned TEXT,
                    status TEXT  -- active, deleted, etc.
                )
            """)
            
            # Table 3: Audit Evidence
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS audit_evidence (
                    evidence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    rfi_code TEXT,
                    evidence_type TEXT,  -- screenshot, export, document
                    file_path TEXT,
                    file_name TEXT,
                    aws_account TEXT,
                    aws_region TEXT,
                    service TEXT,
                    captured_date TEXT,
                    fiscal_year TEXT,
                    related_ticket TEXT,  -- FK to jira_tickets
                    metadata TEXT,  -- JSON object
                    FOREIGN KEY (related_ticket) REFERENCES jira_tickets(ticket_key)
                )
            """)
            
            # Table 4: Agent Memory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agent_memory (
                    memory_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category TEXT,  -- preference, learned_fact, command_history, etc.
                    key TEXT,
                    value TEXT,
                    context TEXT,  -- JSON object
                    created_date TEXT,
                    last_accessed TEXT,
                    access_count INTEGER DEFAULT 0,
                    UNIQUE(category, key)
                )
            """)
            
            # Table 5: Task History
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS task_history (
                    task_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_request TEXT,
                    task_type TEXT,
                    status TEXT,  -- completed, failed, in_progress
                    duration_seconds REAL,
                    result_summary TEXT,
                    error_message TEXT,
                    created_date TEXT,
                    completed_date TEXT
                )
            """)
            
            # Create indexes for faster queries
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jira_environment ON jira_tickets(environment)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_jira_created ON jira_tickets(created_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_aws_type ON aws_resources(resource_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_aws_account ON aws_resources(account)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_rfi ON audit_evidence(rfi_code)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_evidence_date ON audit_evidence(captured_date)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_memory_category ON agent_memory(category)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_date ON task_history(created_date)")
            
            self.conn.commit()
            console.print(f"[green]✅ Database initialized: {self.db_path}[/green]")
        
        except Exception as e:
            console.print(f"[red]❌ Failed to initialize database: {e}[/red]")
            raise
    
    @contextmanager
    def transaction(self):
        """Context manager for database transactions."""
        try:
            yield self.conn
            self.conn.commit()
        except Exception as e:
            self.conn.rollback()
            raise e
    
    # ==================== JIRA TICKETS ====================
    
    def add_jira_ticket(self, ticket: Dict[str, Any]) -> bool:
        """Add or update a Jira ticket."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO jira_tickets 
                (ticket_key, summary, description, status, environment, created_date, 
                 updated_date, assignee, reporter, project, priority, issue_type, 
                 labels, metadata, last_synced)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                ticket.get('ticket_key'),
                ticket.get('summary'),
                ticket.get('description'),
                ticket.get('status'),
                ticket.get('environment'),
                ticket.get('created_date'),
                ticket.get('updated_date'),
                ticket.get('assignee'),
                ticket.get('reporter'),
                ticket.get('project'),
                ticket.get('priority'),
                ticket.get('issue_type'),
                json.dumps(ticket.get('labels', [])),
                json.dumps(ticket.get('metadata', {})),
                datetime.now().isoformat()
            ))
            self.conn.commit()
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to add ticket: {e}[/red]")
            return False
    
    def get_jira_tickets(self, environment: Optional[str] = None, 
                        project: Optional[str] = None,
                        limit: int = 100) -> List[Dict[str, Any]]:
        """Get Jira tickets with optional filters."""
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM jira_tickets WHERE 1=1"
            params = []
            
            if environment:
                query += " AND environment = ?"
                params.append(environment)
            
            if project:
                query += " AND project = ?"
                params.append(project)
            
            query += " ORDER BY created_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            console.print(f"[red]❌ Failed to get tickets: {e}[/red]")
            return []
    
    # ==================== AWS RESOURCES ====================
    
    def add_aws_resource(self, resource: Dict[str, Any]) -> bool:
        """Add or update an AWS resource."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO aws_resources 
                (resource_id, resource_arn, resource_type, resource_name, account, region,
                 created_date, tags, metadata, last_scanned, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                resource.get('resource_id'),
                resource.get('resource_arn'),
                resource.get('resource_type'),
                resource.get('resource_name'),
                resource.get('account'),
                resource.get('region'),
                resource.get('created_date'),
                json.dumps(resource.get('tags', {})),
                json.dumps(resource.get('metadata', {})),
                datetime.now().isoformat(),
                resource.get('status', 'active')
            ))
            self.conn.commit()
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to add resource: {e}[/red]")
            return False
    
    def get_aws_resources(self, resource_type: Optional[str] = None,
                         account: Optional[str] = None,
                         region: Optional[str] = None,
                         limit: int = 100) -> List[Dict[str, Any]]:
        """Get AWS resources with optional filters."""
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM aws_resources WHERE status = 'active'"
            params = []
            
            if resource_type:
                query += " AND resource_type = ?"
                params.append(resource_type)
            
            if account:
                query += " AND account = ?"
                params.append(account)
            
            if region:
                query += " AND region = ?"
                params.append(region)
            
            query += " ORDER BY created_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            console.print(f"[red]❌ Failed to get resources: {e}[/red]")
            return []
    
    # ==================== AUDIT EVIDENCE ====================
    
    def add_evidence(self, evidence: Dict[str, Any]) -> int:
        """Add audit evidence and return evidence_id."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO audit_evidence 
                (rfi_code, evidence_type, file_path, file_name, aws_account, aws_region,
                 service, captured_date, fiscal_year, related_ticket, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                evidence.get('rfi_code'),
                evidence.get('evidence_type'),
                evidence.get('file_path'),
                evidence.get('file_name'),
                evidence.get('aws_account'),
                evidence.get('aws_region'),
                evidence.get('service'),
                evidence.get('captured_date', datetime.now().isoformat()),
                evidence.get('fiscal_year'),
                evidence.get('related_ticket'),
                json.dumps(evidence.get('metadata', {}))
            ))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            console.print(f"[red]❌ Failed to add evidence: {e}[/red]")
            return -1
    
    def get_evidence(self, rfi_code: Optional[str] = None,
                    fiscal_year: Optional[str] = None,
                    service: Optional[str] = None,
                    limit: int = 100) -> List[Dict[str, Any]]:
        """Get audit evidence with optional filters."""
        try:
            cursor = self.conn.cursor()
            query = "SELECT * FROM audit_evidence WHERE 1=1"
            params = []
            
            if rfi_code:
                query += " AND rfi_code = ?"
                params.append(rfi_code)
            
            if fiscal_year:
                query += " AND fiscal_year = ?"
                params.append(fiscal_year)
            
            if service:
                query += " AND service = ?"
                params.append(service)
            
            query += " ORDER BY captured_date DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            rows = cursor.fetchall()
            
            return [dict(row) for row in rows]
        except Exception as e:
            console.print(f"[red]❌ Failed to get evidence: {e}[/red]")
            return []
    
    # ==================== AGENT MEMORY ====================
    
    def remember(self, category: str, key: str, value: Any, context: Optional[Dict] = None) -> bool:
        """Store something in agent memory."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO agent_memory 
                (category, key, value, context, created_date, last_accessed, access_count)
                VALUES (?, ?, ?, ?, ?, ?, COALESCE((SELECT access_count FROM agent_memory WHERE category=? AND key=?), 0))
            """, (
                category,
                key,
                json.dumps(value) if not isinstance(value, str) else value,
                json.dumps(context or {}),
                datetime.now().isoformat(),
                datetime.now().isoformat(),
                category,
                key
            ))
            self.conn.commit()
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to remember: {e}[/red]")
            return False
    
    def recall(self, category: str, key: str) -> Optional[Any]:
        """Retrieve something from agent memory."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                SELECT value, context FROM agent_memory 
                WHERE category = ? AND key = ?
            """, (category, key))
            row = cursor.fetchone()
            
            if row:
                # Update access count and last accessed
                cursor.execute("""
                    UPDATE agent_memory 
                    SET last_accessed = ?, access_count = access_count + 1
                    WHERE category = ? AND key = ?
                """, (datetime.now().isoformat(), category, key))
                self.conn.commit()
                
                try:
                    return json.loads(row['value'])
                except:
                    return row['value']
            return None
        except Exception as e:
            console.print(f"[red]❌ Failed to recall: {e}[/red]")
            return None
    
    # ==================== TASK HISTORY ====================
    
    def log_task(self, user_request: str, task_type: str, status: str = "in_progress") -> int:
        """Log a new task and return task_id."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                INSERT INTO task_history 
                (user_request, task_type, status, created_date)
                VALUES (?, ?, ?, ?)
            """, (user_request, task_type, status, datetime.now().isoformat()))
            self.conn.commit()
            return cursor.lastrowid
        except Exception as e:
            console.print(f"[red]❌ Failed to log task: {e}[/red]")
            return -1
    
    def update_task(self, task_id: int, status: str, duration: Optional[float] = None,
                   result_summary: Optional[str] = None, error_message: Optional[str] = None) -> bool:
        """Update task status and results."""
        try:
            cursor = self.conn.cursor()
            cursor.execute("""
                UPDATE task_history 
                SET status = ?, duration_seconds = ?, result_summary = ?, 
                    error_message = ?, completed_date = ?
                WHERE task_id = ?
            """, (status, duration, result_summary, error_message, datetime.now().isoformat(), task_id))
            self.conn.commit()
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to update task: {e}[/red]")
            return False
    
    # ==================== ADVANCED QUERIES ====================
    
    def execute_query(self, query: str, params: Optional[Tuple] = None) -> List[Dict[str, Any]]:
        """Execute custom SQL query."""
        try:
            cursor = self.conn.cursor()
            if params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        except Exception as e:
            console.print(f"[red]❌ Query failed: {e}[/red]")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get database statistics."""
        try:
            stats = {}
            cursor = self.conn.cursor()
            
            # Count tickets by environment
            cursor.execute("SELECT environment, COUNT(*) as count FROM jira_tickets GROUP BY environment")
            stats['jira_by_environment'] = {row['environment']: row['count'] for row in cursor.fetchall()}
            
            # Count AWS resources by type
            cursor.execute("SELECT resource_type, COUNT(*) as count FROM aws_resources WHERE status='active' GROUP BY resource_type")
            stats['aws_by_type'] = {row['resource_type']: row['count'] for row in cursor.fetchall()}
            
            # Count evidence by RFI
            cursor.execute("SELECT rfi_code, COUNT(*) as count FROM audit_evidence GROUP BY rfi_code")
            stats['evidence_by_rfi'] = {row['rfi_code']: row['count'] for row in cursor.fetchall()}
            
            # Task success rate
            cursor.execute("SELECT status, COUNT(*) as count FROM task_history GROUP BY status")
            stats['task_by_status'] = {row['status']: row['count'] for row in cursor.fetchall()}
            
            return stats
        except Exception as e:
            console.print(f"[red]❌ Failed to get stats: {e}[/red]")
            return {}
    
    def close(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()


# Global instance
_agent_db = None

def get_agent_database() -> AgentDatabase:
    """Get or create global agent database instance."""
    global _agent_db
    if _agent_db is None:
        _agent_db = AgentDatabase()
    return _agent_db

