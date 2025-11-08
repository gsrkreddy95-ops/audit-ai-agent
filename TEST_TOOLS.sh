#!/bin/bash

# Test Tools - Verify all tools are properly integrated

cd /Users/krishna/Documents/audit-ai-agent
source venv/bin/activate

echo "🧪 Testing Tool Implementations..."
echo ""

python3 << 'EOF'
import sys
sys.path.append('/Users/krishna/Documents/audit-ai-agent')

from rich.console import Console
console = Console()

# Test 1: Check imports
console.print("[bold cyan]Test 1: Checking tool imports...[/bold cyan]")
try:
    from tools.aws_screenshot_tool import capture_aws_screenshot
    console.print("  ✅ aws_screenshot_tool imported")
except Exception as e:
    console.print(f"  ❌ aws_screenshot_tool: {e}")

try:
    from tools.aws_export_tool import export_aws_data
    console.print("  ✅ aws_export_tool imported")
except Exception as e:
    console.print(f"  ❌ aws_export_tool: {e}")

try:
    from tools.aws_list_tool import list_s3_buckets
    console.print("  ✅ aws_list_tool imported")
except Exception as e:
    console.print(f"  ❌ aws_list_tool: {e}")

try:
    from tools.sharepoint_upload_tool import upload_to_sharepoint
    console.print("  ✅ sharepoint_upload_tool imported")
except Exception as e:
    console.print(f"  ❌ sharepoint_upload_tool: {e}")

console.print()

# Test 2: Check tool executor
console.print("[bold cyan]Test 2: Checking tool executor integration...[/bold cyan]")
try:
    from ai_brain.tool_executor import ToolExecutor
    from evidence_manager.local_evidence_manager import LocalEvidenceManager
    
    evidence_mgr = LocalEvidenceManager()
    executor = ToolExecutor(evidence_mgr)
    
    console.print("  ✅ ToolExecutor initialized")
    
    # Check method exists
    if hasattr(executor, '_execute_aws_export'):
        console.print("  ✅ _execute_aws_export method exists")
    else:
        console.print("  ❌ _execute_aws_export method missing")
    
    if hasattr(executor, '_execute_aws_screenshot'):
        console.print("  ✅ _execute_aws_screenshot method exists")
    else:
        console.print("  ❌ _execute_aws_screenshot method missing")
    
except Exception as e:
    console.print(f"  ❌ Tool executor: {e}")
    import traceback
    traceback.print_exc()

console.print()

# Test 3: Check intelligent agent
console.print("[bold cyan]Test 3: Checking intelligent agent...[/bold cyan]")
try:
    from ai_brain.intelligent_agent import IntelligentAgent
    console.print("  ✅ IntelligentAgent imported")
    
    # Check if tools are defined
    from ai_brain.tools_definition import TOOLS
    console.print(f"  ✅ Found {len(TOOLS)} tool definitions")
    
    for tool in TOOLS:
        console.print(f"     • {tool['name']}")
    
except Exception as e:
    console.print(f"  ❌ Intelligent agent: {e}")
    import traceback
    traceback.print_exc()

console.print()

# Test 4: Check AWS credentials
console.print("[bold cyan]Test 4: Checking AWS credentials...[/bold cyan]")
try:
    import boto3
    
    # Try to get credentials
    session = boto3.Session()
    credentials = session.get_credentials()
    
    if credentials:
        console.print("  ✅ AWS credentials found")
        console.print(f"     Access Key: {credentials.access_key[:10]}...")
    else:
        console.print("  ⚠️  No AWS credentials found")
        console.print("     Run 'duo-sso' to authenticate")
    
except Exception as e:
    console.print(f"  ❌ AWS check failed: {e}")

console.print()
console.print("[bold green]✅ Tool verification complete![/bold green]")
console.print()
console.print("[yellow]If AWS credentials are missing, run: duo-sso[/yellow]")
console.print("[yellow]Then start the agent with: ./QUICK_START.sh[/yellow]")

EOF

