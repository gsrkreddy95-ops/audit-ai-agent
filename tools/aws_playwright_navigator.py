"""
AWS Playwright Navigator - Human-like browser automation for AWS Console

Uses Playwright (instead of Selenium) for:
- More reliable element finding
- Better handling of dynamic content
- Human-like clicking and navigation
- Built-in waiting and retries
- Better screenshot capabilities

This is a COMPLETE replacement for Selenium-based AWS navigation.
Playwright is much more reliable for modern web apps like AWS Console!
"""

import time
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime
from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from rich.console import Console

console = Console()


class AWSPlaywrightNavigator:
    """
    Human-like AWS Console navigator using Playwright
    
    Much more reliable than Selenium for modern web apps!
    """
    
    def __init__(self, region: str = 'us-east-1', headless: bool = False):
        """
        Initialize Playwright-based AWS navigator
        
        Args:
            region: AWS region (default: us-east-1)
            headless: Run browser in headless mode (default: False for debugging)
        """
        self.region = region
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        
        # User data directory for persistent sessions (saves cookies!)
        self.user_data_dir = Path.home() / '.audit-agent-aws-playwright'
        self.user_data_dir.mkdir(exist_ok=True)
        
        console.print(f"[cyan]🎭 Initializing Playwright AWS Navigator[/cyan]")
        console.print(f"[dim]   Region: {region}[/dim]")
        console.print(f"[dim]   Headless: {headless}[/dim]")
    
    def launch(self) -> bool:
        """Launch Playwright browser with persistent context"""
        try:
            console.print("[cyan]🚀 Launching Playwright browser...[/cyan]")
            
            self.playwright = sync_playwright().start()
            
            # Launch Chromium with persistent context (saves cookies!)
            self.context = self.playwright.chromium.launch_persistent_context(
                user_data_dir=str(self.user_data_dir),
                headless=self.headless,
                args=[
                    '--disable-blink-features=AutomationControlled',  # Avoid detection
                    '--no-sandbox',
                    '--disable-dev-shm-usage',
                ],
                viewport={'width': 1920, 'height': 1080},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            )
            
            # Get the first page (or create new one)
            if self.context.pages:
                self.page = self.context.pages[0]
            else:
                self.page = self.context.new_page()
            
            # Set longer timeouts (AWS console can be slow)
            self.page.set_default_timeout(60000)  # 60 seconds
            
            console.print("[green]✅ Playwright browser ready[/green]")
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Failed to launch Playwright: {e}[/red]")
            return False
    
    def authenticate_duo_sso(self, duo_url: str, account_name: str, wait_timeout: int = 300) -> bool:
        """
        Authenticate via Duo SSO and auto-select AWS account
        
        Args:
            duo_url: Duo SSO URL
            account_name: AWS account to select (e.g., 'ctr-prod')
            wait_timeout: Max seconds to wait (default: 5 minutes)
        
        Returns:
            True if successful
        """
        try:
            console.print(f"[cyan]🔐 Authenticating via Duo SSO...[/cyan]")
            console.print(f"[cyan]   Target account: {account_name}[/cyan]")
            
            # Navigate to Duo URL
            self.page.goto(duo_url, wait_until='domcontentloaded', timeout=30000)
            
            console.print("[yellow]⏳ Waiting for Duo authentication...[/yellow]")
            console.print("[dim]   1. Approve Duo push on your phone[/dim]")
            console.print("[dim]   2. ⭐ CHECK 'Trust this browser' ⭐[/dim]")
            console.print("[dim]   3. Agent will auto-select account and role[/dim]")
            
            start_time = time.time()
            account_selected = False
            role_selection_failed = False
            
            while time.time() - start_time < wait_timeout:
                try:
                    current_url = self.page.url
                    
                    # Check if we reached AWS Console (success!)
                    if 'console.aws.amazon.com' in current_url and 'signin' not in current_url:
                        console.print("[green]✅ Successfully signed in to AWS Console[/green]")
                        return True
                    
                    # AWS SAML role selection page
                    if 'signin.aws' in current_url and 'saml' in current_url and not account_selected:
                        console.print("[yellow]📋 AWS SAML role selection page detected[/yellow]")
                        
                        if account_name and not role_selection_failed:
                            console.print(f"[cyan]🔑 Auto-selecting role for '{account_name}'...[/cyan]")
                            
                            if self._select_role_playwright(account_name):
                                account_selected = True
                                console.print("[green]✅ Role selected and signed in![/green]")
                                time.sleep(3)
                            else:
                                console.print("[yellow]⚠️  Role selection failed, please select manually[/yellow]")
                                role_selection_failed = True
                    
                    # AWS SSO portal (account list)
                    elif ('awsapps.com' in current_url or 'portal.sso' in current_url) and not account_selected:
                        console.print("[yellow]📋 AWS SSO portal detected[/yellow]")
                        
                        if account_name:
                            console.print(f"[cyan]Selecting account: {account_name}[/cyan]")
                            
                            if self._select_account_playwright(account_name):
                                console.print(f"[green]✅ Selected account '{account_name}'[/green]")
                                account_selected = True
                                time.sleep(3)
                    
                    time.sleep(2)
                
                except Exception as e:
                    console.print(f"[dim]Wait loop error: {e}[/dim]")
                    time.sleep(2)
            
            console.print("[yellow]⏱️  Timeout waiting for authentication[/yellow]")
            return False
        
        except Exception as e:
            console.print(f"[red]❌ Duo SSO authentication failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    def _select_account_playwright(self, account_name: str) -> bool:
        """Select AWS account on SSO portal using Playwright"""
        try:
            # Wait a moment for page to load
            time.sleep(2)
            
            # Try to find account by text
            account_selector = f"text={account_name}"
            
            try:
                # Wait for account to be visible
                self.page.wait_for_selector(account_selector, timeout=5000)
                
                # Click account
                self.page.click(account_selector)
                console.print(f"[green]✅ Clicked account '{account_name}'[/green]")
                return True
            
            except:
                console.print(f"[yellow]⚠️  Could not find account '{account_name}' by text[/yellow]")
                return False
        
        except Exception as e:
            console.print(f"[red]❌ Account selection failed: {e}[/red]")
            return False
    
    def _select_role_playwright(self, account_name: str) -> bool:
        """
        Select role on SAML page using Playwright
        
        Playwright is MUCH better at handling dynamic forms!
        """
        try:
            console.print("[cyan]🎭 Using Playwright for role selection (more reliable!)[/cyan]")
            
            # Wait for page to be ready
            time.sleep(2)
            
            # Find the account section
            account_text = f"Account: {account_name}"
            
            # Try to find radio button for Admin role under this account
            # Playwright can handle complex selectors much better!
            
            # Strategy 1: Use text content to find the right section
            try:
                # Find all radio buttons
                radio_buttons = self.page.locator('input[type="radio"][name="roleIndex"]').all()
                
                console.print(f"[dim]Found {len(radio_buttons)} radio buttons[/dim]")
                
                for radio in radio_buttons:
                    # Get parent element text
                    parent = radio.locator('xpath=..')
                    parent_text = parent.text_content()
                    
                    # Check if this is under the right account
                    if account_name in parent_text or account_text in parent_text:
                        # Check if this is Admin role
                        if 'Admin' in parent_text and 'ROAdmin' not in parent_text:
                            console.print(f"[green]✅ Found Admin role for {account_name}[/green]")
                            
                            # Scroll into view
                            radio.scroll_into_view_if_needed()
                            time.sleep(0.5)
                            
                            # Click radio button
                            radio.click(force=True)
                            console.print("[green]✅ Clicked Admin radio button[/green]")
                            
                            # Now find and click Sign in button
                            time.sleep(1)
                            
                            # Scroll to bottom to ensure button is visible
                            self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(1)
                            
                            # Find Sign in button - Playwright is much better at this!
                            signin_button = self.page.locator('button:has-text("Sign in"), input[type="submit"][value*="Sign"]').first
                            
                            if signin_button.is_visible():
                                signin_button.scroll_into_view_if_needed()
                                time.sleep(0.5)
                                signin_button.click()
                                console.print("[green]✅ Clicked Sign in button![/green]")
                                return True
                            else:
                                console.print("[yellow]⚠️  Sign in button not visible[/yellow]")
                                return False
                
                console.print(f"[yellow]⚠️  Could not find Admin role for '{account_name}'[/yellow]")
                return False
            
            except Exception as e:
                console.print(f"[yellow]⚠️  Role selection error: {e}[/yellow]")
                return False
        
        except Exception as e:
            console.print(f"[red]❌ Role selection failed: {e}[/red]")
            return False
    
    def navigate_to_service(self, service: str, use_direct_url: bool = True) -> bool:
        """
        Navigate to AWS service console
        
        Args:
            service: Service name (e.g., 'rds', 's3', 'ec2')
            use_direct_url: Use direct URL (recommended) or search
        
        Returns:
            True if successful
        """
        try:
            service = service.lower()
            
            if use_direct_url:
                # Build direct URL
                service_urls = {
                    'rds': f'https://{self.region}.console.aws.amazon.com/rds/home?region={self.region}#databases:',
                    's3': f'https://s3.console.aws.amazon.com/s3/buckets?region={self.region}',
                    'ec2': f'https://{self.region}.console.aws.amazon.com/ec2/home?region={self.region}#Instances:',
                    'lambda': f'https://{self.region}.console.aws.amazon.com/lambda/home?region={self.region}#/functions',
                    'iam': 'https://console.aws.amazon.com/iam/home#/users',
                    'cloudwatch': f'https://{self.region}.console.aws.amazon.com/cloudwatch/home?region={self.region}',
                    'dynamodb': f'https://{self.region}.console.aws.amazon.com/dynamodbv2/home?region={self.region}#tables',
                    'sns': f'https://{self.region}.console.aws.amazon.com/sns/v3/home?region={self.region}#/topics',
                    'sqs': f'https://{self.region}.console.aws.amazon.com/sqs/v2/home?region={self.region}#/queues',
                }
                
                url = service_urls.get(service)
                if url:
                    console.print(f"[cyan]🔗 Navigating to {service.upper()} console...[/cyan]")
                    self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                    time.sleep(3)
                    console.print(f"[green]✅ Navigated to {service.upper()}[/green]")
                    return True
                else:
                    console.print(f"[yellow]⚠️  No direct URL for {service}[/yellow]")
                    return False
            
            return False
        
        except Exception as e:
            console.print(f"[red]❌ Navigation failed: {e}[/red]")
            return False
    
    def click_element(self, selector: str, description: str = "element") -> bool:
        """Click element with human-like behavior"""
        try:
            console.print(f"[cyan]🖱️  Clicking {description}...[/cyan]")
            
            # Wait for element
            self.page.wait_for_selector(selector, timeout=10000)
            
            # Scroll into view
            element = self.page.locator(selector).first
            element.scroll_into_view_if_needed()
            time.sleep(0.3)  # Human-like pause
            
            # Click
            element.click()
            
            console.print(f"[green]✅ Clicked {description}[/green]")
            return True
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not click {description}: {e}[/yellow]")
            return False
    
    def go_back(self) -> bool:
        """Navigate back (like browser back button)"""
        try:
            console.print("[cyan]⬅️  Going back...[/cyan]")
            self.page.go_back(wait_until='domcontentloaded')
            time.sleep(1)
            return True
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not go back: {e}[/yellow]")
            return False
    
    def go_forward(self) -> bool:
        """Navigate forward (like browser forward button)"""
        try:
            console.print("[cyan]➡️  Going forward...[/cyan]")
            self.page.go_forward(wait_until='domcontentloaded')
            time.sleep(1)
            return True
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not go forward: {e}[/yellow]")
            return False
    
    def capture_screenshot(self, name: str = None) -> Optional[str]:
        """
        Capture screenshot with timestamp
        
        Args:
            name: Optional name for screenshot
        
        Returns:
            Path to screenshot file
        """
        try:
            if not name:
                name = f"aws_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            screenshot_dir = Path.home() / 'Desktop' / 'aws_screenshots'
            screenshot_dir.mkdir(exist_ok=True)
            
            screenshot_path = screenshot_dir / f"{name}.png"
            
            console.print(f"[cyan]📸 Capturing screenshot...[/cyan]")
            
            # Playwright's screenshot is much better!
            self.page.screenshot(path=str(screenshot_path), full_page=True)
            
            # Add timestamp
            self._add_timestamp(screenshot_path)
            
            console.print(f"[green]✅ Screenshot saved: {screenshot_path}[/green]")
            return str(screenshot_path)
        
        except Exception as e:
            console.print(f"[red]❌ Screenshot failed: {e}[/red]")
            return None
    
    def _add_timestamp(self, screenshot_path: Path):
        """Add timestamp to screenshot"""
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            img = Image.open(screenshot_path)
            draw = ImageDraw.Draw(img)
            
            # Timestamp text
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')
            
            # Try to use a nice font
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                font = ImageFont.load_default()
            
            # Position (bottom right)
            text_bbox = draw.textbbox((0, 0), timestamp, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = img.width - text_width - 30
            y = img.height - text_height - 30
            
            # Draw background
            padding = 15
            draw.rectangle(
                [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                fill=(0, 0, 0, 180)
            )
            
            # Draw text with shadow
            draw.text((x + 2, y + 2), timestamp, fill=(0, 0, 0, 255), font=font)
            draw.text((x, y), timestamp, fill=(255, 255, 255, 255), font=font)
            
            img.save(screenshot_path)
        
        except Exception as e:
            console.print(f"[dim]Could not add timestamp: {e}[/dim]")
    
    def close(self):
        """Close browser"""
        try:
            if self.context:
                self.context.close()
            if self.playwright:
                self.playwright.stop()
            console.print("[cyan]👋 Playwright browser closed[/cyan]")
        except:
            pass


if __name__ == "__main__":
    # Test the Playwright navigator
    console.print("[bold cyan]Testing AWS Playwright Navigator...[/bold cyan]\n")
    
    nav = AWSPlaywrightNavigator(region='us-east-1', headless=False)
    
    if nav.launch():
        console.print("\n[green]✅ Playwright launched successfully![/green]")
        console.print("[yellow]Test complete. Close this script when done.[/yellow]")
        
        # Keep browser open for testing
        input("\nPress Enter to close...")
        
        nav.close()

