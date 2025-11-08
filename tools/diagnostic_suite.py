#!/usr/bin/env python3
"""
Comprehensive Diagnostic Suite for Evidence Collection
Tests navigation, clicking, waiting, and screenshot capture across all scenarios
"""

import sys
import os
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import json

# Add parent directory
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from tools.universal_screenshot_enhanced import UniversalScreenshotEnhanced, ClickStrategy, WaitCondition
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.markdown import Markdown

console = Console()


class DiagnosticSuite:
    """Comprehensive diagnostic suite for screenshot capture"""
    
    def __init__(self):
        self.tool = None
        self.results = []
        self.test_config = {
            'aws_region': 'us-east-1',
            'test_rds_cluster': None,  # Will be filled by user
            'test_s3_bucket': None,
            'test_ec2_instance': None,
        }
    
    def initialize(self) -> bool:
        """Initialize diagnostic tool"""
        try:
            console.print(Panel(
                "[bold cyan]🧪 Evidence Collection Diagnostic Suite[/bold cyan]\n"
                "Testing navigation, clicking, waiting, and screenshot capture",
                expand=False
            ))
            
            console.print("\n[cyan]🔄 Initializing tool...[/cyan]")
            self.tool = UniversalScreenshotEnhanced(headless=False, timeout=20)
            
            if not self.tool.connect():
                console.print("[red]❌ Failed to initialize tool[/red]")
                return False
            
            console.print("[green]✅ Tool initialized[/green]")
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Initialization failed: {e}[/red]")
            return False
    
    def test_basic_navigation(self) -> bool:
        """Test 1: Basic navigation and page load"""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Test 1: Basic Navigation & Page Load[/bold cyan]")
        console.print("="*60)
        
        try:
            test_url = "https://www.google.com"
            console.print(f"[cyan]Testing URL: {test_url}[/cyan]")
            
            success = self.tool.navigate_to_url(test_url)
            
            if success:
                current_url = self.tool.get_current_url()
                title = self.tool.get_page_title()
                
                console.print(f"[green]✅ Navigation successful[/green]")
                console.print(f"   Current URL: {current_url}")
                console.print(f"   Page Title: {title}")
                
                self.results.append(("Basic Navigation", "✅ PASS"))
                return True
            else:
                self.results.append(("Basic Navigation", "❌ FAIL"))
                return False
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            self.results.append(("Basic Navigation", "❌ FAIL"))
            return False
    
    def test_wait_conditions(self) -> bool:
        """Test 2: Various wait conditions"""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Test 2: Wait Conditions[/bold cyan]")
        console.print("="*60)
        
        try:
            test_url = "https://www.wikipedia.org"
            console.print(f"[cyan]Loading: {test_url}[/cyan]")
            self.tool.navigate_to_url(test_url)
            time.sleep(3)
            
            # Test 2a: Text presence wait
            console.print("\n[cyan]2a. Testing text presence wait...[/cyan]")
            success_text = self.tool.wait_for(
                WaitCondition.TEXT,
                text="Wikipedia"
            )
            
            if success_text:
                console.print("[green]✅ Text wait successful[/green]")
            else:
                console.print("[yellow]⚠️  Text wait timeout[/yellow]")
            
            # Test 2b: URL contains wait (already at page)
            console.print("\n[cyan]2b. Testing URL contains...[/cyan]")
            success_url = self.tool.wait_for(
                WaitCondition.URL_CONTAINS,
                url_part="wikipedia"
            )
            
            if success_url:
                console.print("[green]✅ URL wait successful[/green]")
            else:
                console.print("[yellow]⚠️  URL wait failed[/yellow]")
            
            if success_text and success_url:
                self.results.append(("Wait Conditions", "✅ PASS"))
                return True
            else:
                self.results.append(("Wait Conditions", "⚠️  PARTIAL"))
                return True  # Partial pass
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            self.results.append(("Wait Conditions", "❌ FAIL"))
            return False
    
    def test_element_finding(self) -> bool:
        """Test 3: Finding elements intelligently"""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Test 3: Intelligent Element Finding[/bold cyan]")
        console.print("="*60)
        
        try:
            test_url = "https://example.com"
            console.print(f"[cyan]Loading: {test_url}[/cyan]")
            self.tool.navigate_to_url(test_url)
            time.sleep(2)
            
            # Find element with text
            console.print("\n[cyan]3a. Finding element by text ('More information')...[/cyan]")
            result = self.tool.find_element_intelligent("More information")
            
            if result:
                console.print("[green]✅ Element found[/green]")
                success_find = True
            else:
                console.print("[yellow]⚠️  Element not found (might not exist on page)[/yellow]")
                success_find = False
            
            self.results.append(("Element Finding", "✅ PASS" if success_find else "⚠️  PARTIAL"))
            return success_find or True  # Pass even if element doesn't exist on page
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            self.results.append(("Element Finding", "❌ FAIL"))
            return False
    
    def test_click_strategies(self) -> bool:
        """Test 4: Different click strategies"""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Test 4: Click Strategies[/bold cyan]")
        console.print("="*60)
        
        try:
            test_url = "https://www.wikipedia.org"
            console.print(f"[cyan]Loading: {test_url}[/cyan]")
            self.tool.navigate_to_url(test_url)
            time.sleep(3)
            
            # Test direct click
            console.print("\n[cyan]4a. Testing direct click on search input...[/cyan]")
            success_direct = self.tool.click_element(
                "//input[@id='searchInput']",
                strategy=ClickStrategy.DIRECT,
                description="search input"
            )
            
            if success_direct:
                console.print("[green]✅ Direct click successful[/green]")
            
            # Type in search
            if success_direct:
                console.print("\n[cyan]4b. Testing keyboard input...[/cyan]")
                self.tool.driver.find_element("xpath", "//input[@id='searchInput']").send_keys("Python")
                time.sleep(1)
                console.print("[green]✅ Keyboard input successful[/green]")
            
            self.results.append(("Click Strategies", "✅ PASS" if success_direct else "❌ FAIL"))
            return success_direct
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            self.results.append(("Click Strategies", "❌ FAIL"))
            return False
    
    def test_screenshot_capture(self) -> bool:
        """Test 5: Screenshot capture"""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Test 5: Screenshot Capture[/bold cyan]")
        console.print("="*60)
        
        try:
            test_url = "https://example.com"
            console.print(f"[cyan]Loading: {test_url}[/cyan]")
            self.tool.navigate_to_url(test_url)
            time.sleep(2)
            
            console.print("\n[cyan]Capturing screenshot...[/cyan]")
            screenshot_path = self.tool.capture_screenshot(
                "test_example_com",
                wait_time=1,
                scroll_before=True
            )
            
            if screenshot_path and os.path.exists(screenshot_path):
                size_mb = os.path.getsize(screenshot_path) / 1024 / 1024
                console.print(f"[green]✅ Screenshot captured[/green]")
                console.print(f"   File: {screenshot_path}")
                console.print(f"   Size: {size_mb:.2f} MB")
                
                self.results.append(("Screenshot Capture", "✅ PASS"))
                return True
            else:
                console.print("[red]❌ Screenshot file not created[/red]")
                self.results.append(("Screenshot Capture", "❌ FAIL"))
                return False
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            self.results.append(("Screenshot Capture", "❌ FAIL"))
            return False
    
    def test_aws_authentication(self) -> bool:
        """Test 6: AWS authentication and Duo"""
        console.print("\n" + "="*60)
        console.print("[bold cyan]Test 6: AWS Authentication[/bold cyan]")
        console.print("="*60)
        
        try:
            duo_url = "https://sso-dbbfec7f.sso.duosecurity.com/saml2/sp/DIRGUUDMLYKC10GOCNOR/sso"
            
            console.print(f"[cyan]Navigating to Duo SSO...[/cyan]")
            console.print(f"[yellow]⏳ Waiting for authentication (60 seconds)...[/yellow]")
            console.print("[yellow]   1. Approve Duo push on your phone[/yellow]")
            console.print("[green]   2. CHECK 'Trust this browser'[/green]")
            console.print("[yellow]   3. Click AWS account when list appears[/yellow]")
            
            self.tool.navigate_to_url(duo_url, wait_for_load=False)
            
            # Wait for AWS console
            start_time = time.time()
            authenticated = False
            
            while time.time() - start_time < 60:
                current_url = self.tool.get_current_url()
                
                if 'console.aws.amazon.com' in current_url:
                    console.print(f"[green]✅ AWS Console reached![/green]")
                    authenticated = True
                    break
                
                time.sleep(2)
            
            if authenticated:
                self.results.append(("AWS Authentication", "✅ PASS"))
                return True
            else:
                console.print("[yellow]⚠️  Authentication not completed in time[/yellow]")
                console.print(f"   Current URL: {self.tool.get_current_url()}")
                self.results.append(("AWS Authentication", "⚠️  TIMEOUT"))
                return False
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            self.results.append(("AWS Authentication", "❌ FAIL"))
            return False
    
    def test_rds_navigation(self, cluster_name: str) -> bool:
        """Test 7: RDS specific navigation and cluster access"""
        console.print("\n" + "="*60)
        console.print(f"[bold cyan]Test 7: RDS Navigation (Cluster: {cluster_name})[/bold cyan]")
        console.print("="*60)
        
        try:
            region = self.test_config['aws_region']
            
            # Test 7a: Navigate to RDS console
            console.print("\n[cyan]7a. Navigating to RDS console...[/cyan]")
            rds_url = f"https://{region}.console.aws.amazon.com/rds/home?region={region}#databases:"
            
            if not self.tool.navigate_to_url(rds_url):
                console.print("[red]❌ RDS navigation failed[/red]")
                self.results.append(("RDS Navigation", "❌ FAIL"))
                return False
            
            time.sleep(3)
            console.print("[green]✅ RDS console loaded[/green]")
            
            # Test 7b: Find cluster in page
            console.print(f"\n[cyan]7b. Looking for cluster '{cluster_name}'...[/cyan]")
            
            page_source = self.tool.driver.page_source.lower()
            cluster_found = cluster_name.lower() in page_source
            
            if cluster_found:
                console.print(f"[green]✅ Cluster found in page source[/green]")
            else:
                console.print(f"[yellow]⚠️  Cluster not in page source[/yellow]")
                console.print("[yellow]   Try: aws rds describe-db-clusters --region " + region + "[/yellow]")
            
            # Test 7c: Try direct URL navigation
            console.print(f"\n[cyan]7c. Navigating directly to cluster...[/cyan]")
            direct_url = f"https://{region}.console.aws.amazon.com/rds/home?region={region}#database:id={cluster_name}"
            console.print(f"[dim]URL: {direct_url}[/dim]")
            
            self.tool.navigate_to_url(direct_url)
            time.sleep(4)
            
            # Check result
            current_url = self.tool.get_current_url()
            page_source = self.tool.driver.page_source
            
            cluster_in_url = cluster_name.lower() in current_url.lower()
            cluster_in_page = cluster_name.lower() in page_source.lower()
            
            console.print(f"\n[cyan]7d. Verification:[/cyan]")
            console.print(f"   Cluster in URL: {'✅ YES' if cluster_in_url else '❌ NO'}")
            console.print(f"   Cluster in page: {'✅ YES' if cluster_in_page else '❌ NO'}")
            
            # Test 7e: Try to find cluster in table
            if not cluster_in_page:
                console.print(f"\n[cyan]7e. Searching table for cluster...[/cyan]")
                table_selector = self.tool.find_table_row_by_text(cluster_name)
                
                if table_selector:
                    console.print("[green]✅ Found in table[/green]")
                    cluster_in_page = True
                else:
                    console.print("[yellow]⚠️  Not found in table[/yellow]")
            
            if cluster_in_url or cluster_in_page:
                self.results.append(("RDS Navigation", "✅ PASS"))
                return True
            else:
                console.print("[yellow]⚠️  Could not navigate to specific cluster[/yellow]")
                console.print("   This is expected if cluster doesn't exist or cluster name is incorrect")
                self.results.append(("RDS Navigation", "⚠️  PARTIAL"))
                return True  # Partial pass
            
        except Exception as e:
            console.print(f"[red]❌ Test failed: {e}[/red]")
            self.results.append(("RDS Navigation", "❌ FAIL"))
            return False
    
    def run_all_diagnostics(self) -> None:
        """Run all diagnostic tests"""
        if not self.initialize():
            console.print("[red]❌ Failed to initialize - exiting[/red]")
            return
        
        try:
            # Run basic tests
            self.test_basic_navigation()
            self.test_wait_conditions()
            self.test_element_finding()
            self.test_click_strategies()
            self.test_screenshot_capture()
            
            # Ask for AWS resources
            console.print("\n" + "="*60)
            console.print("[bold cyan]Optional AWS Tests[/bold cyan]")
            console.print("="*60)
            
            try:
                use_aws = console.input("\n[cyan]Test AWS resources? (y/n): [/cyan]").lower() == 'y'
                
                if use_aws:
                    # AWS auth test
                    if self.test_aws_authentication():
                        # RDS test
                        cluster_name = console.input("\n[cyan]RDS cluster name to test: [/cyan]")
                        if cluster_name:
                            self.test_rds_navigation(cluster_name)
            except KeyboardInterrupt:
                console.print("\n[yellow]⏸️  AWS tests skipped by user[/yellow]")
            
        except KeyboardInterrupt:
            console.print("\n[yellow]⏸️  Diagnostic suite interrupted by user[/yellow]")
        finally:
            self.print_summary()
            self.tool.close()
    
    def print_summary(self) -> None:
        """Print test results summary"""
        console.print("\n" + "="*60)
        console.print("[bold cyan]📊 Diagnostic Results[/bold cyan]")
        console.print("="*60)
        
        if not self.results:
            console.print("[yellow]No tests were run[/yellow]")
            return
        
        table = Table(show_header=True, title="Test Results")
        table.add_column("Test", style="cyan")
        table.add_column("Result", style="green")
        
        for test_name, result in self.results:
            table.add_row(test_name, result)
        
        console.print(table)
        
        # Summary statistics
        passed = sum(1 for _, result in self.results if "✅" in result)
        total = len(self.results)
        
        console.print(f"\n[bold]Summary: {passed}/{total} tests passed[/bold]")
        
        if passed == total:
            console.print("[bold green]🎉 All tests passed![/bold green]")
        elif passed >= total * 0.75:
            console.print("[bold yellow]✓ Most tests passed - tool is mostly functional[/bold yellow]")
        else:
            console.print("[bold red]⚠️  Multiple tests failed - check configuration[/bold red]")


def main():
    """Main entry point"""
    diagnostic = DiagnosticSuite()
    diagnostic.run_all_diagnostics()


if __name__ == "__main__":
    main()
