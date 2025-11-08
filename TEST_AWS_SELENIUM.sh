#!/bin/bash
# Test AWS sign-in with undetected-chromedriver

cd /Users/krishna/Documents/audit-ai-agent

echo "🧪 Testing AWS sign-in with undetected-chromedriver..."
echo ""

# Activate venv
source venv/bin/activate

# Run test
python3 -c "
from tools.aws_screenshot_selenium import AWSScreenshotSelenium
from rich.console import Console

console = Console()

console.print('[cyan]═══════════════════════════════════════════[/cyan]')
console.print('[cyan]🧪 AWS Sign-In Test (Selenium)[/cyan]')
console.print('[cyan]═══════════════════════════════════════════[/cyan]')
console.print()

# Create tool
tool = AWSScreenshotSelenium(headless=False)

# Connect
if not tool.connect():
    console.print('[red]❌ Failed to launch Chrome[/red]')
    exit(1)

# Navigate to AWS
console.print()
console.print('[cyan]Testing AWS Duo SSO authentication...[/cyan]')
console.print()

if tool.navigate_to_aws_console('us-east-1'):
    console.print()
    console.print('[green]═══════════════════════════════════════════[/green]')
    console.print('[green]✅ SUCCESS! AWS sign-in works![/green]')
    console.print('[green]═══════════════════════════════════════════[/green]')
    console.print()
    console.print('[yellow]Press Enter to close browser...[/yellow]')
    input()
else:
    console.print()
    console.print('[red]═══════════════════════════════════════════[/red]')
    console.print('[red]❌ FAILED: AWS sign-in did not work[/red]')
    console.print('[red]═══════════════════════════════════════════[/red]')
    console.print()

tool.close()
"

echo ""
echo "✅ Test complete!"

