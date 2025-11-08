#!/usr/bin/env python3
"""
Quick Test of Universal Screenshot Tool
Validates basic functionality without interactive waits
"""

import sys
import os

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.universal_screenshot_enhanced import UniversalScreenshotEnhanced, ClickStrategy, WaitCondition
from rich.console import Console
from rich.panel import Panel
import time

console = Console()


def test_basic_functionality():
    """Test basic tool functionality"""
    
    console.print(Panel(
        "[bold cyan]🧪 Universal Screenshot Tool - Quick Test[/bold cyan]\n"
        "Testing basic functionality",
        expand=False
    ))
    
    tool = UniversalScreenshotEnhanced(headless=True, timeout=15)
    
    try:
        # Test 1: Connection
        console.print("\n[bold cyan]Test 1: Browser Connection[/bold cyan]")
        console.print("[cyan]Connecting to browser...[/cyan]")
        
        if tool.connect():
            console.print("[green]✅ Browser connected[/green]")
        else:
            console.print("[red]❌ Connection failed[/red]")
            return False
        
        # Test 2: Basic navigation
        console.print("\n[bold cyan]Test 2: Navigation[/bold cyan]")
        console.print("[cyan]Navigating to example.com...[/cyan]")
        
        if tool.navigate_to_url("https://example.com"):
            console.print("[green]✅ Navigation successful[/green]")
            console.print(f"   Title: {tool.get_page_title()}")
        else:
            console.print("[red]❌ Navigation failed[/red]")
            return False
        
        # Test 3: Element finding
        console.print("\n[bold cyan]Test 3: Element Finding[/bold cyan]")
        console.print("[cyan]Finding element with text 'More'...[/cyan]")
        
        result = tool.find_element_intelligent("More")
        if result:
            console.print("[green]✅ Element found[/green]")
        else:
            console.print("[yellow]⚠️  Element not found (expected for example.com)[/yellow]")
        
        # Test 4: Screenshot capture
        console.print("\n[bold cyan]Test 4: Screenshot Capture[/bold cyan]")
        console.print("[cyan]Capturing screenshot...[/cyan]")
        
        screenshot_path = tool.capture_screenshot("quick_test", wait_time=1, scroll_before=False)
        
        if screenshot_path and os.path.exists(screenshot_path):
            size_mb = os.path.getsize(screenshot_path) / 1024 / 1024
            console.print("[green]✅ Screenshot captured[/green]")
            console.print(f"   File: {screenshot_path}")
            console.print(f"   Size: {size_mb:.2f} MB")
        else:
            console.print("[red]❌ Screenshot capture failed[/red]")
            return False
        
        # Test 5: Diagnostics
        console.print("\n[bold cyan]Test 5: Navigation History[/bold cyan]")
        tool.print_diagnostics()
        
        console.print("\n[bold green]✅ All tests completed successfully![/bold green]")
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        tool.close()


def test_rds_navigator():
    """Test RDS Navigator independently"""
    
    console.print("\n" + "="*60)
    console.print(Panel(
        "[bold cyan]🧪 RDS Navigator Test[/bold cyan]",
        expand=False
    ))
    
    from tools.rds_navigator_enhanced import RDSNavigatorEnhanced
    
    tool = UniversalScreenshotEnhanced(headless=True, timeout=15)
    
    try:
        if not tool.connect():
            console.print("[red]❌ Failed to connect browser[/red]")
            return False
        
        console.print("[green]✅ Browser connected[/green]")
        
        # Create navigator
        navigator = RDSNavigatorEnhanced(tool)
        
        console.print(f"[cyan]Region: {navigator.region}[/cyan]")
        console.print(f"[cyan]Status: {navigator.get_status()}[/cyan]")
        
        console.print("[green]✅ RDS Navigator initialized[/green]")
        
        return True
        
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        tool.close()


if __name__ == "__main__":
    console.print("[bold cyan]🚀 Starting Quick Tests[/bold cyan]\n")
    
    # Run tests
    basic_ok = test_basic_functionality()
    rds_ok = test_rds_navigator()
    
    console.print("\n" + "="*60)
    console.print("[bold cyan]📊 Summary[/bold cyan]")
    console.print(f"Basic Functionality: {'✅ PASS' if basic_ok else '❌ FAIL'}")
    console.print(f"RDS Navigator: {'✅ PASS' if rds_ok else '❌ FAIL'}")
    console.print("="*60)
    
    if basic_ok and rds_ok:
        console.print("\n[bold green]🎉 All tests passed![/bold green]")
        sys.exit(0)
    else:
        console.print("\n[bold red]❌ Some tests failed[/bold red]")
        sys.exit(1)
