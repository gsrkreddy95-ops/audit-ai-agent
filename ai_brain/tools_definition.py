"""
Tool Definitions for Claude Function Calling
The LLM uses these to decide which tools to call and with what parameters
"""

from typing import List, Dict
from ai_brain.self_healing_tools import get_self_healing_tools
from ai_brain.code_generation_tools import get_code_generation_tools
from ai_brain.orchestrator_tools import get_orchestrator_tools


def get_tool_definitions(read_only_mode: bool = False) -> List[Dict]:
    """
    Define all tools available to the agent
    Claude will read these and decide when to use them
    
    Args:
        read_only_mode: If True, Claude can only read/analyze code, not modify it (default: True)
    """
    
    # NEW: Brain-directed orchestrator tools (USE THESE FIRST!)
    orchestrator_tools = get_orchestrator_tools()
    
    # Core evidence collection tools
    core_tools = [
        {
            "name": "sharepoint_review_evidence",
            "description": """Reviews previous year's audit evidence from SharePoint for a specific RFI.
            
            This tool:
            - Connects to SharePoint (browser-based, user logs in once)
            - Navigates to previous year's RFI folder (e.g., FY2024/XDR Platform/BCR-06.01/)
            - Lists all evidence files (screenshots, PDFs, CSVs, etc.)
            - Analyzes each file to understand what it is (RDS screenshot, IAM export, etc.)
            - Creates a collection plan for current year
            - Returns detailed instructions for collecting similar evidence
            
            Use this when user asks to:
            - "Review evidence for RFI X"
            - "Check previous audit evidence"
            - "What evidence did we collect for RFI X last year?"
            - "Collect evidence for RFI X" (start by reviewing previous year first)
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "rfi_code": {
                        "type": "string",
                        "description": "RFI code (e.g., 'BCR-06.01', '10.1.2.12', 'ISO-27001-A.9.2.1')"
                    },
                    "product": {
                        "type": "string",
                        "description": "Product/platform name (e.g., 'XDR Platform', 'CSE and Orbital', 'DC Controls'). Optional - will search if not provided.",
                        "enum": ["XDR Platform", "XDR", "CSE and Orbital", "CSE", "DC Controls", "SXO", ""]
                    },
                    "year": {
                        "type": "string",
                        "description": "Which year to review (default: FY2024). Use 'FY2024', 'FY2023', etc.",
                        "default": "FY2024"
                    }
                },
                "required": ["rfi_code"]
            }
        },

        {
            "name": "analyze_document_evidence",
            "description": """Deeply analyze evidence documents (PDF, DOCX, CSV, JSON, images) using the LLM brain.

This tool routes files through the Document Intelligence pipeline so the brain can:
- Extract text or tabular structure from multiple formats
- Summarize what the document proves for the audit requirement
- Highlight key entities (accounts, resources, controls)
- Recommend which fresh evidence to gather this year
- Flag stale or missing information for self-healing workflows

Use this after downloading evidence locally or when SharePoint metadata includes local paths. You can pass a single
`file_path` or an array of `files` (objects containing at minimum `name` and `local_path`).""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Local path to a single evidence file (PDF, DOCX, CSV, JSON, image, etc.)."
                    },
                    "files": {
                        "type": "array",
                        "description": "Batch of files with metadata from SharePoint or local storage.",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string"},
                                "local_path": {"type": "string"},
                                "type": {"type": "string"},
                                "size": {"type": "number"}
                            }
                        }
                    },
                    "context": {
                        "type": "string",
                        "description": "Optional natural-language context about the audit requirement or questions for the brain."
                    },
                    "metadata": {
                        "type": "object",
                        "description": "Additional metadata to pass with single file analysis (e.g., SharePoint folder info)."
                    }
                },
                "required": [],
                "additionalProperties": False
            }
        },

        {
            "name": "aws_take_screenshot",
            "description": """Takes screenshots of AWS Console pages with timestamps.
            
            This tool:
            - Opens AWS Console in browser
            - Authenticates with duo-sso if needed (prompts user for MFA)
            - Navigates to specified service/resource
            - Can navigate to specific sections within services (e.g., "Custom Domain Names" in API Gateway)
            - Can select resources from lists/tables
            - Takes scrolling screenshots for long lists (e.g., 87 S3 buckets)
            - Adds timestamp to screenshot
            - Saves to local evidence folder
            
            Supports ALL AWS services (not limited to enum list!):
            RDS, S3, IAM, EC2, VPC, CloudWatch, API Gateway, Lambda, DynamoDB, ECS, EKS, CloudFront, etc.
            
            NEW FEATURES:
            - Universal navigation: Can navigate to ANY AWS service (no predefined list needed!)
            - Section navigation: Navigate to specific pages within a service
            - Resource selection: Automatically select first resource or specific resource by name
            
            Examples:
            1. Navigate to API Gateway → Custom Domain Names → Select first domain
            2. Navigate to RDS → Databases → Select "prod-cluster-01"
            3. Navigate to EC2 → Load Balancers → Select ALB by name
            
            IMPORTANT: Audit evidence requires PRODUCTION accounts only!
            Before using this tool:
            1. Review previous evidence to see which account/region was used
            2. Ask user to confirm production account (ctr-prod, sxo101, sxo202, etc.)
            3. Ask user to confirm AWS region
            4. DO NOT default to ctr-int or test accounts!
            
            Use this when you need to capture AWS Console UI showing:
            - Resource configurations (RDS Multi-AZ, S3 versioning, etc.)
            - Resource lists (IAM users, S3 buckets, EC2 instances)
            - Dashboard views
            - Any AWS Console page
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "AWS service name (e.g., 'rds', 'apigateway', 's3', 'ec2', 'lambda', etc.) - Universal navigator supports ALL AWS services!"
                    },
                    "resource_type": {
                        "type": "string",
                        "description": "Type of resource or page to screenshot (e.g., 'database', 'cluster', 'bucket', 'custom-domain-names', 'load-balancers')"
                    },
                    "section_name": {
                        "type": "string",
                        "description": """Specific section within the service to navigate to (NEW!).
                        Examples:
                        - API Gateway: 'Custom Domain Names', 'APIs', 'VPC Links'
                        - RDS: 'Databases', 'Clusters', 'Snapshots', 'Parameter Groups'
                        - EC2: 'Instances', 'Load Balancers', 'Security Groups', 'Key Pairs'
                        - Lambda: 'Functions', 'Layers', 'Applications'
                        
                        If not provided, navigates to service homepage.
                        """
                    },
                    "resource_name": {
                        "type": "string",
                        "description": """SPECIFIC resource name is REQUIRED for configuration screenshots!
                        Examples:
                        - RDS: 'prod-xdr-cluster-01', 'staging-db-instance' (NEVER use 'database' or 'rds_console')
                        - S3: 'my-audit-bucket', 'backup-storage-bucket' (NEVER use 'bucket' or 's3_console')  
                        - EC2: 'i-0123456789abcdef0' (NEVER use 'instance' or 'ec2_console')
                        - Lambda: 'process-data-function' (NEVER use 'function' or 'lambda_console')
                        - API Gateway: 'api.example.com' (domain name)
                        
                        NEW: Can also be used with section_name to select specific resource after navigating to section.
                        
                        CRITICAL: If you don't know the specific name:
                        1. First use aws_list_resources or list_aws_resources to get available names
                        2. Then call this tool with the EXACT resource name
                        
                        DO NOT use generic names like 'database', 'cluster', 'bucket', 'console', etc.
                        Leave empty ONLY for dashboard/list screenshots (no config tabs).
                        """
                    },
                    "select_first_resource": {
                        "type": "boolean",
                        "description": "If true, automatically selects the first resource in the list after navigating to section (NEW!). Default: false"
                    },
                    "resource_index": {
                        "type": "integer",
                        "description": "Index of resource to select (0 = first, 1 = second, etc.). Only used if select_first_resource is true and resource_name is not provided. Default: 0"
                    },
                    "aws_account": {
                        "type": "string",
                        "description": "AWS PRODUCTION account profile name (REQUIRED - must ask user to confirm!). For audit evidence, use production accounts only: ctr-prod, sxo101, sxo202. DO NOT use ctr-int or ctr-test for audit evidence."
                    },
                    "aws_region": {
                        "type": "string",
                        "description": "AWS region code (REQUIRED - must ask user to confirm!). Common regions: us-east-1 (NAM), eu-west-1 (EU), ap-southeast-1 (APIC). Check previous evidence for which regions were used."
                    },
                    "config_tab": {
                        "type": "string",
                        "description": "Specific configuration tab to show (e.g., 'Configuration', 'Monitoring', 'Logs')"
                    },
                    "rfi_code": {
                        "type": "string",
                        "description": "RFI code to organize evidence under (e.g., 'BCR-06.01')"
                    }
                },
                "required": ["service", "aws_account", "aws_region", "rfi_code"]
            }
        },
        
        {
            "name": "aws_export_data",
            "description": """Exports AWS data to CSV/JSON/XLSX via AWS API (boto3).
            
            This tool:
            - Uses AWS API (not Console)
            - Authenticates with duo-sso if needed
            - Calls AWS API to get resource data
            - Exports to CSV, JSON, or XLSX format
            - Adds timestamp to filename
            - Saves to local evidence folder
            
            IMPORTANT: Audit evidence requires PRODUCTION accounts only!
            Before using this tool, ask user to confirm:
            - Production account (ctr-prod, sxo101, sxo202)
            - AWS region
            
            Use this for exporting lists/data like:
            - IAM users, roles, policies
            - S3 buckets with configurations
            - RDS instances/clusters details
            - EC2 instances with tags
            - Security groups rules
            - CloudTrail events
            - Any structured AWS data
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "AWS service to export from",
                        "enum": ["iam", "s3", "rds", "ec2", "vpc", "cloudtrail", "config"]
                    },
                    "export_type": {
                        "type": "string",
                        "description": "What data to export",
                        "examples": ["users", "roles", "buckets", "instances", "clusters", "security-groups", "events"]
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format",
                        "enum": ["csv", "json", "xlsx"],
                        "default": "csv"
                    },
                    "aws_account": {
                        "type": "string",
                        "description": "AWS PRODUCTION account profile (REQUIRED - must ask user!). For audit evidence: ctr-prod, sxo101, sxo202. DO NOT use ctr-int or ctr-test.",
                        "enum": ["ctr-prod", "sxo101", "sxo202", "ctr-int", "ctr-test"]
                    },
                    "aws_region": {
                        "type": "string",
                        "description": "AWS region code (REQUIRED - must ask user!). Use 'all' for global resources like IAM. Common: us-east-1 (NAM), eu-west-1 (EU), ap-southeast-1 (APIC).",
                        "examples": ["us-east-1", "eu-west-1", "ap-southeast-1", "all"]
                    },
                    "rfi_code": {
                        "type": "string",
                        "description": "RFI code to organize evidence under"
                    }
                },
                "required": ["service", "export_type", "format", "aws_account", "rfi_code"]
            }
        },
        
        {
            "name": "list_aws_resources",
            "description": """Lists AWS resources quickly for viewing (not for evidence collection).
            
            This is a quick lookup tool to see what resources exist.
            For actual evidence collection, use aws_take_screenshot or aws_export_data.
            
            Use this when user asks:
            - "What S3 buckets do we have?"
            - "List RDS clusters in ctr-int"
            - "Show me IAM users"
            - "What EC2 instances are running?"
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": "AWS service",
                        "enum": ["s3", "rds", "iam", "ec2", "vpc", "lambda"]
                    },
                    "aws_account": {
                        "type": "string",
                        "description": "AWS account profile. For quick lookups, any account is fine. For audit evidence collection, use production accounts only.",
                        "enum": ["ctr-int", "ctr-prod", "ctr-test", "sxo101", "sxo202"]
                    },
                    "aws_region": {
                        "type": "string",
                        "description": "AWS region",
                        "default": "us-east-1"
                    }
                },
                "required": ["service", "aws_account"]
            }
        },
        
        {
            "name": "show_local_evidence",
            "description": """Shows summary of evidence collected locally (not yet uploaded to SharePoint).
            
            Displays:
            - Files collected so far
            - Organized by RFI code
            - File sizes and timestamps
            - Ready for user review
            
            Use this when user asks:
            - "What have you collected?"
            - "Show me the evidence"
            - "What files are ready?"
            - After collecting evidence, to show results
            """,
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        },
        
        {
            "name": "upload_to_sharepoint",
            "description": """Uploads collected evidence to SharePoint after user approval.
            
            IMPORTANT: Only call this after:
            1. Evidence has been collected locally
            2. User has reviewed it (via show_local_evidence)
            3. User explicitly approves upload
            
            This tool:
            - Opens SharePoint in browser
            - Navigates to FY2025/[Product]/[RFI_CODE]/
            - Uploads all files from local evidence folder
            - Verifies upload success
            
            Use only when user says:
            - "Yes, upload" (after you asked for approval)
            - "Upload to SharePoint"
            - "Upload the evidence"
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "rfi_code": {
                        "type": "string",
                        "description": "RFI code folder to upload to"
                    },
                    "product": {
                        "type": "string",
                        "description": "Product/platform name"
                    }
                },
                "required": ["rfi_code"]
            }
        },
        
        {
            "name": "learn_from_sharepoint_url",
            "description": """Learns from existing SharePoint evidence by analyzing a SharePoint folder URL.
            
            This is POWERFUL - it makes the agent smart by learning from previous evidence:
            
            The tool:
            1. Takes a SharePoint folder URL (user provides)
            2. Downloads all files (images, PDFs, CSVs, Excel, Word docs, JSON)
            3. Uses Claude to analyze EACH file:
               - Screenshots: Extracts text via OCR, understands what AWS page it is
               - CSVs: Reads data structure, column names, sample rows
               - Excel: Analyzes sheets and data
               - PDFs/Word: Extracts full text content
               - JSON: Parses structure
            4. Creates a detailed collection plan with step-by-step instructions
            5. Saves to knowledge base for future reference
            
            Example user requests:
            - "Learn from this SharePoint folder: https://site.sharepoint.com/.../10.1.2.5"
            - "Analyze evidence at [SharePoint URL]"
            - "Study what we collected last year: [URL]"
            - "I want you to review [SharePoint URL] and collect similar evidence"
            
            Returns:
            - Number of files analyzed
            - Collection tasks with detailed instructions
            - Automation opportunities
            - Time estimate
            - Prerequisites needed
            
            Use this when:
            - User provides a SharePoint URL
            - User asks to "learn from" or "analyze" existing evidence
            - Before collecting evidence, to understand what's needed
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "sharepoint_url": {
                        "type": "string",
                        "description": "Full SharePoint folder URL (e.g., https://company.sharepoint.com/sites/audit/Shared Documents/FY2024/XDR/10.1.2.5)"
                    },
                    "rfi_code": {
                        "type": "string",
                        "description": "RFI code to associate with this learning (e.g., '10.1.2.5', 'BCR-06.01')"
                    }
                },
                "required": ["sharepoint_url", "rfi_code"]
            }
        }
    ]
    
    # REVOLUTIONARY: Dynamic code execution - Claude writes code on the fly!
    dynamic_execution_tools = [
        {
            "name": "execute_python_code",
            "description": """🚀 MOST POWERFUL TOOL: Execute Python code that YOU (Claude) write dynamically.

Use this when the user asks you to do something that doesn't have a pre-built tool, like:
- Generate AWS billing reports
- Analyze data in custom ways
- Create compliance reports
- Process evidence files
- Export data in specific formats
- Integrate with any API
- ANYTHING that Python can do!

You are Claude 3.5 Sonnet - you are EXTREMELY intelligent and can write excellent Python code.
Don't hesitate to use this tool for novel tasks!

Example uses:
- "Generate billing report for ctr-prod account" → Write code to use boto3 Cost Explorer
- "Compare S3 bucket policies across accounts" → Write code to fetch and compare
- "Create Excel report of RDS backups" → Write code to use boto3 + pandas + openpyxl
- "Analyze last year's evidence and create summary" → Write code to process files

The code runs in a safe environment with access to:
- boto3 (AWS SDK)
- pandas (data analysis)
- Common libraries (json, csv, datetime, pathlib, etc.)
- Your agent's codebase (can import from integrations/, evidence_manager/, etc.)

IMPORTANT: 
- Write clear, well-commented code
- Handle errors gracefully
- Print progress updates
- Return/print useful results
- Use boto3 for AWS operations (credentials already configured)
""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "The Python code to execute. Should be complete, runnable code."
                    },
                    "description": {
                        "type": "string",
                        "description": "Brief description of what this code does (for logging)"
                    },
                    "timeout": {
                        "type": "integer",
                        "description": "Max execution time in seconds (default 300 = 5 minutes)",
                        "default": 300
                    }
                },
                "required": ["code", "description"]
            }
        },
        {
            "name": "analyze_past_evidence",
            "description": """📚 Analyze previous years' audit evidence to learn patterns and requirements.

Use this to understand:
- What format evidence should be in (screenshots, CSV, PDF, Word docs)
- What naming conventions were used
- What level of detail auditors expect
- What specific data points were collected
- How evidence was structured and organized

This helps you collect NEW evidence that matches the EXPECTED format.

Example uses:
- "Review SOC2 evidence from last year for BCR-06.01"
- "Learn how we collected RDS evidence in FY2024"
- "Analyze ISO 27001 evidence structure"
- "What format should I use for IAM evidence?"

After analyzing, you'll get:
- File types used (png, csv, pdf, docx, etc.)
- Naming patterns (timestamps, service names, regions, etc.)
- Sample evidence items
- Recommendations for collecting similar evidence

CRITICAL: Always use this BEFORE collecting new evidence so you match the expected format!
""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "evidence_path": {
                        "type": "string",
                        "description": "Path to past evidence. Can be:\n- SharePoint path: 'TD&R Documentation Train 5/TD&R Evidence Collection/FY2024/XDR Platform/BCR-06.01'\n- Local path: '/path/to/evidence/folder'\n- URL: 'https://cisco.sharepoint.com/...'"
                    },
                    "rfi_code": {
                        "type": "string",
                        "description": "Optional RFI code to focus analysis on (e.g., 'BCR-06.01')"
                    },
                    "year": {
                        "type": "string",
                        "description": "Optional year to analyze (e.g., 'FY2024', '2024')"
                    }
                },
                "required": ["evidence_path"]
            }
        },
        
        # === JIRA INTEGRATION TOOLS ===
        {
            "name": "jira_list_tickets",
            "description": """List and filter Jira tickets.
            
            Features:
            - Filter by project, labels, status, assignee, priority, issue type
            - Returns ticket summary with key metadata
            - Can export results to CSV/JSON
            
            Use this to:
            - List all tickets in a project
            - Find tickets by label (e.g., 'security', 'audit')
            - Filter by status (e.g., 'Open', 'In Progress', 'Done')
            - Find tickets assigned to specific person
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project key (e.g., 'AUDIT', 'SEC')"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by labels (e.g., ['security', 'compliance'])"
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by status (e.g., 'Open', 'In Progress', 'Done')"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter by assignee username or email"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority (e.g., 'High', 'Critical')"
                    },
                    "issue_type": {
                        "type": "string",
                        "description": "Filter by issue type (e.g., 'Bug', 'Task', 'Story')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)"
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "If provided, exports results to this format"
                    }
                },
                "required": []
            }
        },
        
        {
            "name": "jira_search_jql",
            "description": """Advanced Jira search using JQL (Jira Query Language).
            
            Use this for complex queries like:
            - 'project = AUDIT AND status = "In Progress" AND priority = High'
            - 'assignee = currentUser() AND created >= -7d'
            - 'labels = security AND updated >= -30d ORDER BY created DESC'
            
            JQL is more powerful than basic filters.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "jql_query": {
                        "type": "string",
                        "description": "JQL query string (e.g., 'project = AUDIT AND status = Open')"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 100)"
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "If provided, exports results to this format"
                    }
                },
                "required": ["jql_query"]
            }
        },
        
        {
            "name": "jira_get_ticket",
            "description": """Get detailed information about a specific Jira ticket.
            
            Returns:
            - Full description
            - Comments
            - Attachments
            - History
            - All metadata
            
            Use this when you need complete ticket details.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "ticket_key": {
                        "type": "string",
                        "description": "Jira ticket key (e.g., 'AUDIT-123', 'SEC-456')"
                    }
                },
                "required": ["ticket_key"]
            }
        },
        
        # === CONFLUENCE INTEGRATION TOOLS ===
        {
            "name": "confluence_search",
            "description": """Search Confluence documents by title or content.
            
            Features:
            - Full-text search across all Confluence spaces
            - Filter by specific space
            - Returns page metadata and URLs
            
            Use this to:
            - Find documentation about specific topics
            - Search for procedures, guidelines, policies
            - Locate audit documentation
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query (searches title and content)"
                    },
                    "space": {
                        "type": "string",
                        "description": "Optional: limit search to specific space key (e.g., 'AUDIT')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)"
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "If provided, exports results to this format"
                    }
                },
                "required": ["query"]
            }
        },
        
        {
            "name": "confluence_get_page",
            "description": """Get full content of a specific Confluence page.
            
            Returns:
            - Page content (HTML)
            - Metadata (author, version, dates)
            - Can convert to Markdown
            
            Use this to:
            - Read full documentation
            - Extract specific procedures
            - Analyze page content
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "page_id": {
                        "type": "string",
                        "description": "Page ID (preferred if known)"
                    },
                    "page_title": {
                        "type": "string",
                        "description": "Page title (requires space parameter)"
                    },
                    "space": {
                        "type": "string",
                        "description": "Space key (required if using page_title)"
                    },
                    "as_markdown": {
                        "type": "boolean",
                        "description": "If true, converts content to Markdown format"
                    }
                },
                "required": []
            }
        },
        
        {
            "name": "confluence_list_space",
            "description": """List all pages in a Confluence space.
            
            Use this to:
            - Get overview of all documentation in a space
            - Find all audit procedures
            - Discover available documents
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "space": {
                        "type": "string",
                        "description": "Space key (e.g., 'AUDIT', 'SEC', 'DOCS')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of pages (default: 100)"
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "If provided, exports results to this format"
                    }
                },
                "required": ["space"]
            }
        },
        
        # === GITHUB INTEGRATION TOOLS ===
        {
            "name": "github_list_prs",
            "description": """List pull requests from a GitHub repository.
            
            Features:
            - Filter by state (open, closed, all)
            - Filter by author
            - Filter by label
            - Returns PR metadata and stats
            
            Use this to:
            - Review recent code changes
            - Find PRs by specific author
            - Analyze PR patterns
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (e.g., 'org/repo' or 'user/repo')"
                    },
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "description": "PR state filter (default: 'all')"
                    },
                    "author": {
                        "type": "string",
                        "description": "Filter by author username"
                    },
                    "label": {
                        "type": "string",
                        "description": "Filter by label"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of PRs (default: 50)"
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "If provided, exports results to this format"
                    }
                },
                "required": ["repo_name"]
            }
        },
        
        {
            "name": "github_get_pr",
            "description": """Get detailed information about a specific pull request.
            
            Returns:
            - Full PR description
            - Comments and reviews
            - Commit details
            - Files changed
            - Merge status
            
            Use this for detailed PR analysis.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (e.g., 'org/repo')"
                    },
                    "pr_number": {
                        "type": "integer",
                        "description": "PR number"
                    }
                },
                "required": ["repo_name", "pr_number"]
            }
        },
        
        {
            "name": "github_search_code",
            "description": """Search code across GitHub repositories.
            
            Use this to:
            - Find specific code patterns
            - Locate function implementations
            - Search for security patterns
            - Analyze code usage
            
            Can filter by repository and language.
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Code search query (e.g., 'def authenticate', 'class Config')"
                    },
                    "repo": {
                        "type": "string",
                        "description": "Limit to specific repository (e.g., 'org/repo')"
                    },
                    "language": {
                        "type": "string",
                        "description": "Limit to specific language (e.g., 'python', 'javascript')"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of results (default: 50)"
                    }
                },
                "required": ["query"]
            }
        },
        
        {
            "name": "github_list_issues",
            "description": """List issues from a GitHub repository.
            
            Features:
            - Filter by state, labels, assignee
            - Returns issue metadata
            - Can export to CSV/JSON
            
            Use this to:
            - Track open issues
            - Find bugs by label
            - Analyze issue patterns
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "repo_name": {
                        "type": "string",
                        "description": "Repository name (e.g., 'org/repo')"
                    },
                    "state": {
                        "type": "string",
                        "enum": ["open", "closed", "all"],
                        "description": "Issue state filter (default: 'all')"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by labels (e.g., ['bug', 'enhancement'])"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Filter by assignee username"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Maximum number of issues (default: 50)"
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "If provided, exports results to this format"
                    }
                },
                "required": ["repo_name"]
            }
        }
    ]
    
    # Self-healing/debugging tools that allow Claude to fix code autonomously
    self_healing_tools = get_self_healing_tools()
    
    # Code generation tools that allow Claude to CREATE NEW CODE on-the-fly
    code_generation_tools = get_code_generation_tools()
    
    # 🔒 READ-ONLY MODE FILTERING
    if read_only_mode:
        # Filter self-healing tools to ONLY read/diagnose, NOT fix
        read_only_self_healing = [
            tool for tool in self_healing_tools 
            if tool['name'] in [
                'read_tool_source',      # ✅ READ: Can read code
                'diagnose_error',        # ✅ ANALYZE: Can diagnose
                'get_browser_screenshot' # ✅ DEBUG: Can see browser state
            ]
        ]
        
        # Filter code generation tools to ONLY search examples, NOT generate/modify
        read_only_code_gen = [
            tool for tool in code_generation_tools
            if tool['name'] in [
                'search_codebase_for_examples'  # ✅ SEARCH: Can learn from existing code
            ]
        ]
        
        # Filter dynamic execution tools - REMOVE execute_python_code
        read_only_dynamic = [
            tool for tool in dynamic_execution_tools
            if tool['name'] in [
                'analyze_past_evidence'  # ✅ ANALYZE: Can learn from past evidence
            ]
        ]
        
        # Combine with FILTERED tools (READ-ONLY)
        all_tools = read_only_dynamic + orchestrator_tools + core_tools + read_only_self_healing + read_only_code_gen
        
        # Add notice to console
        from rich.console import Console
        console = Console()
        console.print("[yellow]🔒 READ-ONLY MODE ENABLED:[/yellow]")
        console.print("[dim]   Claude can read/analyze code but NOT modify it[/dim]")
        console.print("[dim]   Disabled tools: fix_tool_code, generate_new_tool, execute_python_code[/dim]")
    else:
        # FULL ACCESS MODE - All tools available
        all_tools = dynamic_execution_tools + orchestrator_tools + core_tools + self_healing_tools + code_generation_tools
    
    return all_tools


# Export TOOLS constant for convenience
TOOLS = get_tool_definitions()

