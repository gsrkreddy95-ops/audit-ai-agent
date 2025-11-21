"""
Database Query Tool - Let the agent query its own database

The agent can use this to:
- Search past Jira tickets
- Find AWS resources
- Look up audit evidence
- Recall preferences/facts
- Analyze task history

Examples:
- "Show me all prod tickets from last month"
- "Which S3 buckets were created in 2025?"
- "What evidence do I have for AWS-RDS?"
- "What's my success rate on screenshot tasks?"
"""

from typing import Dict, List, Optional, Any
from rich.console import Console
from ai_brain.agent_database import get_agent_database

console = Console()


def query_agent_database(
    query_type: str,
    filters: Optional[Dict[str, str]] = None,
    custom_sql: Optional[str] = None,
    limit: int = 100
) -> Dict[str, Any]:
    """
    Query the agent's persistent database.
    
    Args:
        query_type: Type of query - one of:
            - "jira_tickets" - Search Jira tickets
            - "aws_resources" - Search AWS resources
            - "audit_evidence" - Search audit evidence
            - "agent_memory" - Recall stored facts/preferences
            - "task_history" - Get task execution history
            - "statistics" - Get database statistics
            - "custom" - Run custom SQL query
        
        filters: Optional filters for the query:
            For jira_tickets: {"environment": "prod", "project": "SBG"}
            For aws_resources: {"resource_type": "s3", "account": "ctr-prod", "region": "us-east-1"}
            For audit_evidence: {"rfi_code": "AWS-001", "fiscal_year": "FY2025", "service": "rds"}
            For agent_memory: {"category": "preference", "key": "default_region"}
        
        custom_sql: Custom SQL query (only if query_type="custom")
        limit: Maximum number of results to return
    
    Returns:
        {
            "success": bool,
            "query_type": str,
            "results": list,  # Query results
            "count": int,  # Number of results
            "error": str  # Error message if failed
        }
    """
    try:
        db = get_agent_database()
        filters = filters or {}
        results = []
        
        console.print(f"[cyan]🔍 Querying database: {query_type}[/cyan]")
        if filters:
            console.print(f"[dim]Filters: {filters}[/dim]")
        
        if query_type == "jira_tickets":
            results = db.get_jira_tickets(
                environment=filters.get("environment"),
                project=filters.get("project"),
                limit=limit
            )
        
        elif query_type == "aws_resources":
            results = db.get_aws_resources(
                resource_type=filters.get("resource_type"),
                account=filters.get("account"),
                region=filters.get("region"),
                limit=limit
            )
        
        elif query_type == "audit_evidence":
            results = db.get_evidence(
                rfi_code=filters.get("rfi_code"),
                fiscal_year=filters.get("fiscal_year"),
                service=filters.get("service"),
                limit=limit
            )
        
        elif query_type == "agent_memory":
            category = filters.get("category")
            key = filters.get("key")
            if category and key:
                value = db.recall(category, key)
                results = [{"category": category, "key": key, "value": value}] if value else []
            else:
                return {
                    "success": False,
                    "query_type": query_type,
                    "results": [],
                    "count": 0,
                    "error": "agent_memory query requires 'category' and 'key' filters"
                }
        
        elif query_type == "task_history":
            # Query recent tasks
            query = """
                SELECT * FROM task_history 
                WHERE 1=1
            """
            params = []
            
            if "status" in filters:
                query += " AND status = ?"
                params.append(filters["status"])
            
            if "task_type" in filters:
                query += " AND task_type = ?"
                params.append(filters["task_type"])
            
            query += " ORDER BY created_date DESC LIMIT ?"
            params.append(limit)
            
            results = db.execute_query(query, tuple(params))
        
        elif query_type == "statistics":
            stats = db.get_statistics()
            results = [stats]
        
        elif query_type == "custom":
            if not custom_sql:
                return {
                    "success": False,
                    "query_type": query_type,
                    "results": [],
                    "count": 0,
                    "error": "custom query requires 'custom_sql' parameter"
                }
            console.print(f"[yellow]⚠️  Executing custom SQL: {custom_sql}[/yellow]")
            results = db.execute_query(custom_sql)
        
        else:
            return {
                "success": False,
                "query_type": query_type,
                "results": [],
                "count": 0,
                "error": f"Unknown query_type: {query_type}"
            }
        
        console.print(f"[green]✅ Found {len(results)} results[/green]")
        
        return {
            "success": True,
            "query_type": query_type,
            "results": results,
            "count": len(results),
            "error": ""
        }
    
    except Exception as e:
        console.print(f"[red]❌ Database query failed: {e}[/red]")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "query_type": query_type,
            "results": [],
            "count": 0,
            "error": str(e)
        }


def store_in_database(
    data_type: str,
    data: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Store data in the agent's database.
    
    Args:
        data_type: Type of data - one of:
            - "jira_ticket" - Store Jira ticket
            - "aws_resource" - Store AWS resource
            - "audit_evidence" - Store audit evidence
            - "agent_memory" - Remember something
            - "task" - Log a task
        
        data: Data to store (varies by type)
    
    Returns:
        {
            "success": bool,
            "data_type": str,
            "stored_id": int or str,  # ID of stored record
            "error": str
        }
    """
    try:
        db = get_agent_database()
        console.print(f"[cyan]💾 Storing {data_type} in database...[/cyan]")
        
        if data_type == "jira_ticket":
            success = db.add_jira_ticket(data)
            return {
                "success": success,
                "data_type": data_type,
                "stored_id": data.get("ticket_key"),
                "error": "" if success else "Failed to store ticket"
            }
        
        elif data_type == "aws_resource":
            success = db.add_aws_resource(data)
            return {
                "success": success,
                "data_type": data_type,
                "stored_id": data.get("resource_id"),
                "error": "" if success else "Failed to store resource"
            }
        
        elif data_type == "audit_evidence":
            evidence_id = db.add_evidence(data)
            success = evidence_id > 0
            return {
                "success": success,
                "data_type": data_type,
                "stored_id": evidence_id,
                "error": "" if success else "Failed to store evidence"
            }
        
        elif data_type == "agent_memory":
            category = data.get("category")
            key = data.get("key")
            value = data.get("value")
            context = data.get("context")
            
            if not all([category, key, value]):
                return {
                    "success": False,
                    "data_type": data_type,
                    "stored_id": None,
                    "error": "agent_memory requires category, key, and value"
                }
            
            success = db.remember(category, key, value, context)
            return {
                "success": success,
                "data_type": data_type,
                "stored_id": f"{category}.{key}",
                "error": "" if success else "Failed to remember"
            }
        
        elif data_type == "task":
            task_id = db.log_task(
                user_request=data.get("user_request", ""),
                task_type=data.get("task_type", "unknown"),
                status=data.get("status", "in_progress")
            )
            success = task_id > 0
            return {
                "success": success,
                "data_type": data_type,
                "stored_id": task_id,
                "error": "" if success else "Failed to log task"
            }
        
        else:
            return {
                "success": False,
                "data_type": data_type,
                "stored_id": None,
                "error": f"Unknown data_type: {data_type}"
            }
    
    except Exception as e:
        console.print(f"[red]❌ Failed to store data: {e}[/red]")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "data_type": data_type,
            "stored_id": None,
            "error": str(e)
        }

