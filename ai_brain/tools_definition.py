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
            "name": "replay_evidence_playbook",
            "description": """Replays a stored evidence playbook (generated from prior SharePoint evidence) to collect current-year screenshots/exports automatically.

Provide the fiscal year and RFI code (or let fiscal year default to current). Optional overrides allow switching AWS account/region or specifying an audit period for date filtering.

Use this after building playbooks so the agent can regenerate all proof artifacts in one run.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "fiscal_year": {
                        "type": "string",
                        "description": "Fiscal year of the playbook (e.g., 'FY2024'). Defaults to current year."
                    },
                    "rfi_code": {
                        "type": "string",
                        "description": "RFI/control identifier whose playbook should be replayed."
                    },
                    "aws_account": {
                        "type": "string",
                        "description": "Override AWS profile/account for this run."
                    },
                    "aws_region": {
                        "type": "string",
                        "description": "Override AWS region for this run."
                    },
                    "audit_period": {
                        "type": "string",
                        "description": "Optional audit period label (e.g., 'FY2025', 'Q1-2025') to use for filtering."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date override for date filtering (YYYY-MM-DD)."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date override for date filtering (YYYY-MM-DD)."
                    }
                },
                "required": ["rfi_code"]
            }
        },

        {
            "name": "bulk_aws_export",
            "description": """Runs multiple aws_export_data operations for a list of AWS services and regions in one request.

Provide services like ["rds","s3","kms"] and regions ["us-east-1","eu-west-1"]. The tool automatically selects sensible export types (clusters, buckets, keys, etc.) if you don’t specify one, and aggregates successes/failures so the agent doesn’t stop at the first error.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "services": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of AWS services to export (e.g., ['rds','s3','kms']). Comma-separated string also supported."
                    },
                    "aws_regions": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "AWS regions to collect from (e.g., ['us-east-1','eu-west-1'])."
                    },
                    "aws_account": {
                        "type": "string",
                        "description": "AWS account/profile to use (e.g., 'ctr-prod')."
                    },
                    "format": {
                        "type": "string",
                        "enum": ["csv", "json"],
                        "description": "Export format (default: csv)."
                    },
                    "export_type": {
                        "type": "string",
                        "description": "Optional override export_type (applied to all services)."
                    },
                    "rfi_code": {
                        "type": "string",
                        "description": "Optional RFI code for evidence storage (default: AUDIT-EXPORT)."
                    },
                    "filter_by_date": {
                        "type": "boolean",
                        "description": "Enable date filtering (requires audit_period or start/end dates)."
                    },
                    "audit_period": {
                        "type": "string",
                        "description": "Audit period label (e.g., 'FY2025', 'Q1-2025')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Custom range start date (YYYY-MM-DD)."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "Custom range end date (YYYY-MM-DD)."
                    },
                    "date_field": {
                        "type": "string",
                        "description": "Specific date column to filter by (falls back to service defaults)."
                    }
                },
                "required": ["services", "aws_regions", "aws_account"]
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
            "name": "aws_console_action",
            "description": """🎯 AWS CONSOLE - Universal tool for BROWSER-BASED AWS Console actions.
            
            ⚠️⚠️⚠️ CRITICAL: ONLY USE THIS TOOL FOR SCREENSHOTS! ⚠️⚠️⚠️
            
            This tool opens a BROWSER and requires visual interaction.
            
            ✅ USE aws_console_action FOR:
            - Taking SCREENSHOTS of AWS Console pages
            - Capturing VISUAL evidence from AWS Console UI
            - Documenting console configurations visually
            
            ❌ DO NOT USE aws_console_action FOR:
            - Exporting CSV/JSON data → Use aws_export_data instead (no browser needed!)
            - Listing resources → Use list_aws_resources instead (no browser needed!)
            - Just "signing in" before an export → Skip! aws_export_data uses AWS CLI credentials directly
            
            🔑 KEY RULE:
            If user says "sign in and export" or "authenticate and export CSV/JSON":
            → SKIP aws_console_action entirely
            → Go DIRECTLY to aws_export_data (it handles authentication via AWS CLI/boto3)
            
            This tool handles:
            1. 📸 Screenshots (capture evidence when requested)
            2. 🧭 Navigation (go to service/section for screenshots)
            3. 🔄 Pagination (capture all pages visually)
            4. 📅 Filtering (by date/audit period for visual evidence)
            
            ⚠️  USAGE RULES:
            - If user says "screenshot", "capture", "document", "show me" → Use this tool with capture_screenshot=true
            - If user says "export CSV" or "export JSON" → DO NOT use this tool! Use aws_export_data instead
            - If user says "list resources" → DO NOT use this tool! Use list_aws_resources instead
            - DO NOT use this for authentication before API-based exports!
            
            EXAMPLES:
            
            Example 1 - CORRECT: Screenshot Request:
            User: "take screenshot of KMS keys in ctr-prod us-east-1"
            → Use aws_console_action with capture_screenshot=true
            
            Example 2 - WRONG: Export Request:
            User: "export KMS keys to CSV from ctr-prod"
            → DO NOT use aws_console_action! Use aws_export_data instead
            
            Example 3 - WRONG: "Sign in and export":
            User: "sign into ctr-int and export secrets to CSV"
            → DO NOT use aws_console_action at all!
            → Go directly to aws_export_data (handles auth internally)
            
            Example 4 - CORRECT: Visual Documentation:
            User: "show me the RDS backup configuration for prod-cluster"
            → Use aws_console_action with capture_screenshot=true
            
            This tool:
            - Opens AWS Console in browser (persistent session)
            - Authenticates with duo-sso if needed (prompts user for MFA once)
            - Navigates to ANY AWS service (universal navigator)
            - Navigates to specific sections (e.g., "Custom Domain Names")
            - Optionally captures screenshots (only if requested!)
            - Optionally exports data (CSV, JSON, PDF)
            - Supports pagination (capture all pages)
            - Supports date filtering (by audit period)
            - Validates outputs (confidence scoring)
            
            Supports ALL AWS services:
            RDS, S3, IAM, EC2, VPC, CloudWatch, API Gateway, Lambda, DynamoDB, ECS, EKS, 
            CloudFront, Bedrock, KMS, Secrets Manager, Config, CloudTrail, etc.
            
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
                    "capture_all_pages": {
                        "type": "boolean",
                        "description": """🔄 PAGINATION SUPPORT (NEW!): Automatically capture ALL pages if the service displays paginated results.
                        
                        When enabled:
                        - Detects pagination controls (1, 2, 3, Next, Load More, etc.)
                        - Automatically clicks through ALL pages
                        - Takes a screenshot of EACH page
                        - Counts total items captured
                        - Works for ALL AWS services (KMS keys, Secrets Manager secrets, S3 buckets, RDS instances, etc.)
                        
                        Examples:
                        - KMS has 20 keys across 2 pages → captures both pages
                        - Secrets Manager has 80 secrets across 8 pages → captures all 8
                        - S3 has 300 buckets → captures all pages automatically
                        
                        Set to true when user asks for "all" items, "complete list", or when pagination indicators are visible.
                        Default: false (captures only first page)
                        """
                    },
                    "max_pages": {
                        "type": "integer",
                        "description": "Safety limit for pagination. Maximum number of pages to capture. Default: 50. Use higher values (e.g., 100) if user explicitly requests it."
                    },
                    "filter_by_date": {
                        "type": "boolean",
                        "description": """📅 DATE FILTERING (NEW!): Filter resources by audit period or date range.
                        
                        CRITICAL FOR AUDIT COMPLIANCE:
                        Audits typically cover a specific time period (e.g., FY2025: Jan 1 - Dec 31, 2025).
                        Only resources created/modified during that period should be captured.
                        
                        When enabled:
                        - Filters resources by creation date, modification date, or other date columns
                        - Hides resources outside the audit period
                        - Highlights resources within the audit period (green background)
                        - Shows "X out of Y resources" in the screenshot
                        - Works for ALL AWS services (KMS, Secrets Manager, S3, EC2, RDS, Lambda, etc.)
                        
                        Examples:
                        - "Show me KMS keys created in FY2025" → filter_by_date=True, audit_period="FY2025"
                        - "Secrets modified between Jan-Jun 2025" → filter_by_date=True, start_date="2025-01-01", end_date="2025-06-30"
                        - "S3 buckets created in Q1 2025" → filter_by_date=True, audit_period="Q1-2025"
                        
                        Set to true when user mentions:
                        - Audit period, fiscal year, quarter
                        - Date range, "created in", "modified during"
                        - "FY2025", "2025", "Q1-2025", etc.
                        - "Last year", "this year", "last quarter"
                        
                        Default: false (shows all resources regardless of date)
                        """
                    },
                    "audit_period": {
                        "type": "string",
                        "description": """Audit period for date filtering (used with filter_by_date=True).
                        
                        Supported formats:
                        - "FY2025" → Jan 1, 2025 to Dec 31, 2025
                        - "FY2024" → Jan 1, 2024 to Dec 31, 2024
                        - "Q1-2025" → Jan 1, 2025 to Mar 31, 2025
                        - "Q2-2025" → Apr 1, 2025 to Jun 30, 2025
                        - "Q3-2025" → Jul 1, 2025 to Sep 30, 2025
                        - "Q4-2025" → Oct 1, 2025 to Dec 31, 2025
                        - "2025" → Jan 1, 2025 to Dec 31, 2025
                        
                        Default: Current year
                        """
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for custom date range filtering (YYYY-MM-DD format). Example: '2025-01-01'. Takes precedence over audit_period if provided."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for custom date range filtering (YYYY-MM-DD format). Example: '2025-12-31'. Must be used with start_date."
                    },
                    "date_column": {
                        "type": "string",
                        "description": """Specific date column to filter by (optional - auto-detects if not provided).
                        
                        Common date columns:
                        - KMS: "Creation date"
                        - Secrets Manager: "Last modified", "Last accessed"
                        - S3: "Creation date"
                        - RDS: "Creation time"
                        - EC2: "Launch time"
                        - Lambda: "Last modified"
                        - IAM: "Created"
                        
                        If not provided, agent will auto-detect the appropriate date column.
                        """
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
                    },
                    "capture_screenshot": {
                        "type": "boolean",
                        "description": """🎯 CAPTURE SCREENSHOT? (Default: false)
                        
                        ⚠️  CRITICAL: Only set to true if user EXPLICITLY requests screenshot/capture/evidence!
                        
                        When to set TRUE:
                        ✅ "take screenshot of..."
                        ✅ "capture..."
                        ✅ "document..."
                        ✅ "collect evidence for..."
                        ✅ "save proof of..."
                        
                        When to set FALSE (just navigate):
                        ❌ "go to..."
                        ❌ "navigate to..."
                        ❌ "open..."
                        ❌ "show me..."
                        ❌ "check..."
                        
                        Default: false (navigate only, no screenshot)
                        """
                    },
                    "export_format": {
                        "type": "string",
                        "description": """📊 EXPORT FORMAT (Optional)
                        
                        Set this when user requests data export:
                        - "csv" → Export to CSV file
                        - "json" → Export to JSON file
                        - "pdf" → Export to PDF (if supported)
                        
                        Examples:
                        - "export S3 buckets to CSV" → export_format="csv"
                        - "save IAM users as JSON" → export_format="json"
                        
                        If set, tool will export data instead of/in addition to screenshot.
                        Leave empty for navigation or screenshot only.
                        """,
                        "enum": ["csv", "json", "pdf", ""]
                    }
                },
                "required": ["service", "aws_account", "aws_region"]
            }
        },
        
        {
            "name": "aws_export_data",
            "description": """🚀 UNIVERSAL AWS Export - Supports 100+ AWS Services!
            
            Exports AWS data to CSV/JSON via AWS API (boto3) with COMPLETE configuration details.
            
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            🎯 AUTOMATIC TOOL SELECTION (You don't need to choose!)
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            For IAM, S3, RDS, EC2:
            ✅ Uses ENHANCED DETAILED EXPORTER
            ✅ 17-33 fields per resource
            ✅ Encryption status, backup config, security settings
            ✅ Network details, tags, ARNs, metadata
            
            For ALL other services (Lambda, DynamoDB, ECS, EKS, etc.):
            ✅ Uses COMPREHENSIVE COLLECTOR  
            ✅ 100+ AWS services supported
            ✅ Complete resource configurations
            ✅ Automatic API discovery
            
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            📦 SUPPORTED SERVICES (100+)
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            COMPUTE: ec2, lambda, ecs, eks, batch, lightsail
            STORAGE: s3, ebs, efs, fsx, backup, glacier
            DATABASE: rds, dynamodb, redshift, neptune, documentdb, elasticache
            NETWORKING: vpc, elb, cloudfront, route53, apigateway, directconnect
            SECURITY: iam, kms, secretsmanager, waf, shield, guardduty, macie
            MONITORING: cloudwatch, cloudtrail, config, xray
            ANALYTICS: athena, emr, kinesis, glue, quicksight
            ML/AI: sagemaker, comprehend, rekognition, textract
            MESSAGING: sns, sqs, eventbridge, mq
            DEVELOPER: codecommit, codebuild, codedeploy, codepipeline
            MANAGEMENT: cloudformation, ssm, organizations, control-tower
            
            And 70+ more services!
            
            ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
            
            IMPORTANT: Default to production accounts for audit evidence (ctr-prod, sxo101, sxo202).
            ✅ HOWEVER: If the user explicitly says to use ctr-int/ctr-test/non-prod for testing or experiments,
              honor that immediately without re-confirming over and over. Assume they understand the risk.
            
            AUTHENTICATION:
            - Automatically uses duo-sso if credentials needed
            - Works with federated SSO accounts
            
            WHAT IT EXPORTS:
            ✅ Complete resource configurations
            ✅ Encryption status (ALWAYS included)
            ✅ Backup configuration (ALWAYS included)  
            ✅ Security settings (ALWAYS included)
            ✅ Network/endpoint details (ALWAYS included)
            ✅ Tags, ARNs, metadata (ALWAYS included)
            
            EXAMPLES:
            - IAM users: MFA status, access keys, policies
            - S3 buckets: Encryption, versioning, public access blocks
            - RDS clusters: Backup retention, encryption, endpoints
            - Lambda functions: Runtime, memory, environment vars
            - DynamoDB tables: Capacity, encryption, streams
            - ECS clusters: Services, tasks, container configs
            """,
            "input_schema": {
                "type": "object",
                "properties": {
                    "service": {
                        "type": "string",
                        "description": """AWS service to export from (supports 100+ services!)
                        
CRITICAL SERVICE NAMES (use exact strings):
- IAM: "iam"
- S3: "s3"  
- RDS: "rds"
- EC2: "ec2"
- KMS (Key Management): "kms"
- Secrets Manager: "secretsmanager" ⚠️ NOT "secrets"
- Lambda: "lambda"
- DynamoDB: "dynamodb"
- ECS: "ecs"
- Auto Scaling: "autoscaling"
- CloudTrail: "cloudtrail"
- Config: "config"

If the user says "secrets manager" or "secrets", use "secretsmanager".""",
                        "examples": ["iam", "s3", "rds", "ec2", "lambda", "dynamodb", "ecs", "eks", "vpc", "kms", "secretsmanager", "autoscaling", "cloudtrail", "config"]
                    },
                    "export_type": {
                        "type": "string",
                        "description": """What data to export (resource type within the service)

Common export types by service:
- iam: "users", "roles", "policies", "groups"
- s3: "buckets"
- rds: "clusters", "instances", "snapshots"
- ec2: "instances", "volumes", "security-groups", "vpcs"
- kms: "keys", "aliases"
- secretsmanager: "secrets" ⚠️ (the export_type is "secrets", but service is "secretsmanager")
- lambda: "functions"
- dynamodb: "tables"
- autoscaling: "groups", "policies"
- cloudtrail: "trails", "events"

If unsure, use "all" to export all available resource types.""",
                        "examples": ["users", "roles", "buckets", "instances", "clusters", "keys", "secrets", "functions", "tables", "groups", "trails", "all"]
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format",
                        "enum": ["csv", "json", "xlsx"],
                        "default": "csv"
                    },
                    "filter_by_date": {
                        "type": "boolean",
                        "description": "Set true to filter results within a specific date range."
                    },
                    "audit_period": {
                        "type": "string",
                        "description": "Optional label describing the audit period (e.g., 'FY2025')."
                    },
                    "start_date": {
                        "type": "string",
                        "description": "Start date for filtering (YYYY-MM-DD or ISO8601)."
                    },
                    "end_date": {
                        "type": "string",
                        "description": "End date for filtering (YYYY-MM-DD or ISO8601)."
                    },
                    "date_field": {
                        "type": "string",
                        "description": "Override the date field to filter on (defaults per service/resource)."
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
        ,
        {
            "name": "list_pending_enhancements",
            "description": """Lists all enhancement proposals generated by Meta-Intelligence that are waiting for human approval.

Use this immediately after the agent reports a pending fix so you can review:
- Why the fix is needed
- Which files/operations are proposed
- Suggested test plan

Call this tool before approving or rejecting a fix so you understand the exact code changes.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "enum": ["pending", "applied"],
                        "description": "Filter by status. Default: pending"
                    }
                },
                "required": []
            }
        },
        {
            "name": "apply_pending_enhancement",
            "description": """Applies an auto-generated fix AFTER you explicitly approve it in chat.

Provide the proposal_id returned by list_pending_enhancements or from the tool result that reported the failure.
The enhancement manager will apply the patch (search/replace/create) and return success/failure details.""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "proposal_id": {
                        "type": "string",
                        "description": "ID of the enhancement proposal to apply (e.g., 'd2b6f8d4-...')"
                    }
                },
                "required": ["proposal_id"]
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
                    "board_name": {
                        "type": "string",
                        "description": "Optional board/dashboard name (e.g., 'XDR SRE Sprint') to auto-apply that board's filter"
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
            "description": """Advanced Jira search using JQL (Jira Query Language) with AUTOMATIC PAGINATION.
            
            ✨ PAGINATION: Automatically fetches ALL matching tickets across multiple pages!
            - Jira API limits to 100 per request
            - This tool automatically paginates to get ALL results that match your JQL
            - By default, fetches ALL tickets (no artificial limit)
            - Set max_results only if you need a hard cap
            
            Use this for complex queries like:
            - 'project = AUDIT AND status = "In Progress" AND priority = High'
            - 'assignee = currentUser() AND created >= -7d'
            - 'labels = security AND updated >= -30d ORDER BY created DESC'
            - 'project = XDR AND labels = STE AND status not in (Done, Completed)'
            
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
                        "description": "Maximum number of results (default: 0 = fetch ALL matching tickets). Only set this if you need a hard cap (e.g., 100, 500). Leave unset or use 0 for complete results."
                    },
                    "paginate": {
                        "type": "boolean",
                        "description": "Enable automatic pagination (default: true)"
                    },
                    "board_name": {
                        "type": "string",
                        "description": "Optional board/dashboard name (e.g., 'XDR SRE Sprint', 'XDR Platform Ops')"
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
            "name": "jira_search_intent",
            "description": """Natural-language Jira search that builds the correct JQL for you and fetches accurate results.

Say things like:
- "Filter XDR tickets with label TDR_ACCESS between 2025-06-01 and 2025-09-01"
- "Tickets with labels STE and TDR_ACCESS created in July 2025"
- "Bugs assigned to alice in last 30 days"

The agent will:
- Build robust JQL (labels in ("..."), half-open end date, ORDER BY created ASC)
- Apply board filter JQL if you pass a board_name
- Run slice-first weekly (and day-level if needed) to avoid Jira's 100/1000 caps
- Compact payloads for LLM safety; export full dataset if requested""",
            "input_schema": {
                "type": "object",
                "properties": {
                    "project": {
                        "type": "string",
                        "description": "Project key (default: XDR)"
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Labels to include (e.g., ['TDR_ACCESS','STE'])"
                    },
                    "created_start": {
                        "type": "string",
                        "description": "Start date (YYYY-MM-DD)"
                    },
                    "created_end": {
                        "type": "string",
                        "description": "Inclusive end date (YYYY-MM-DD). Will be converted to half-open internally."
                    },
                    "statuses": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Filter by statuses (e.g., ['In Progress','Open'])"
                    },
                    "assignee": {
                        "type": "string",
                        "description": "Assignee username/email"
                    },
                    "text_contains": {
                        "type": "string",
                        "description": "Full-text contains (applies to text/summary)"
                    },
                    "order_by": {
                        "type": "string",
                        "description": "ORDER BY clause (default: 'created ASC')",
                        "default": "created ASC"
                    },
                    "board_name": {
                        "type": "string",
                        "description": "Optional board name to merge its saved filter JQL"
                    },
                    "max_results": {
                        "type": "integer",
                        "description": "Hard cap on total results (default: 0 = all)"
                    },
                    "paginate": {
                        "type": "boolean",
                        "description": "Enable pagination (default: true)"
                    },
                    "export_format": {
                        "type": "string",
                        "enum": ["json", "csv"],
                        "description": "If provided, exports full results to this format"
                    }
                },
                "required": []
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
    
    approval_locked_tools = {"apply_pending_enhancement"}

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
        
        filtered_core_tools = [
            tool for tool in core_tools if tool['name'] not in approval_locked_tools
        ]
        # Combine with FILTERED tools (READ-ONLY)
        all_tools = read_only_dynamic + orchestrator_tools + filtered_core_tools + read_only_self_healing + read_only_code_gen
        
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
# 🔓 SELF-HEALING ENABLED: Agent can now fix code autonomously!
TOOLS = get_tool_definitions(read_only_mode=False)

