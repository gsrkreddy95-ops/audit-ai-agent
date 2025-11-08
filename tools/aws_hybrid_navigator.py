"""
AWS Hybrid Navigator - Uses undetected-chromedriver + Playwright APIs

BEST OF BOTH WORLDS:
- undetected-chromedriver: Bypasses bot detection (works with Duo SSO!)
- Playwright CDP: Superior element finding and clicking

This gives you:
✅ Duo SSO authentication working (undetected-chromedriver)
✅ Reliable element finding (Playwright)
✅ Human-like clicking (Playwright)
✅ Auto-waiting (Playwright)
"""

import time
import os
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import undetected_chromedriver as uc
from playwright.sync_api import sync_playwright, Page
from rich.console import Console

console = Console()


class AWSHybridNavigator:
    """
    Hybrid navigator: undetected-chromedriver + Playwright
    
    Uses undetected-chromedriver to launch Chrome (bypasses detection)
    Then connects Playwright to it (for better automation)
    """
    
    def __init__(self, region: str = 'us-east-1', headless: bool = False):
        """
        Initialize hybrid navigator
        
        Args:
            region: AWS region
            headless: Run browser in headless mode (not recommended for Duo)
        """
        self.region = region
        self.headless = headless
        
        # undetected-chromedriver components
        self.driver = None
        self.driver_pid = None
        
        # Playwright components
        self.playwright = None
        self.browser = None
        self.page = None
        
        console.print(f"[cyan]🎭 Initializing Hybrid Navigator (undetected-chrome + Playwright)[/cyan]")
        console.print(f"[dim]   Region: {region}[/dim]")
    
    def launch(self) -> bool:
        """Launch Chrome with undetected-chromedriver, then connect Playwright"""
        try:
            console.print("[cyan]🚀 Step 1: Launching Chrome with undetected-chromedriver...[/cyan]")
            
            # User data directory (persistent session)
            user_data_dir = Path.home() / '.audit-agent-hybrid-chrome'
            user_data_dir.mkdir(exist_ok=True)
            
            # Launch Chrome with undetected-chromedriver
            options = uc.ChromeOptions()
            options.add_argument(f'--user-data-dir={user_data_dir}')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--window-size=1920,1080')
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # Enable remote debugging (for Playwright connection!)
            options.add_argument('--remote-debugging-port=9222')
            
            self.driver = uc.Chrome(options=options, version_main=None)
            console.print("[green]✅ Chrome launched with undetected-chromedriver[/green]")
            
            # Get debugging URL
            time.sleep(2)  # Wait for Chrome to fully start
            
            # Connect Playwright to the Chrome instance
            console.print("[cyan]🎭 Step 2: Connecting Playwright to Chrome...[/cyan]")
            
            self.playwright = sync_playwright().start()
            
            # Connect to the Chrome instance via CDP
            try:
                self.browser = self.playwright.chromium.connect_over_cdp('http://localhost:9222')
                console.print("[green]✅ Playwright connected to Chrome![/green]")
                
                # Get the page
                contexts = self.browser.contexts
                if contexts:
                    pages = contexts[0].pages
                    if pages:
                        self.page = pages[0]
                    else:
                        self.page = contexts[0].new_page()
                else:
                    console.print("[yellow]⚠️  No context found, creating new one...[/yellow]")
                    context = self.browser.new_context(viewport={'width': 1920, 'height': 1080})
                    self.page = context.new_page()
                
                # Set longer timeout for AWS Console
                self.page.set_default_timeout(60000)  # 60 seconds
                
                console.print("[green]✅ Playwright page ready[/green]")
                console.print("[bold green]🎉 Hybrid navigator ready! Best of both worlds![/bold green]")
                return True
            
            except Exception as e:
                console.print(f"[yellow]⚠️  Playwright connection failed: {e}[/yellow]")
                console.print("[yellow]   Will use Selenium-only mode[/yellow]")
                return True  # Still return True, we have Selenium
        
        except Exception as e:
            console.print(f"[red]❌ Failed to launch hybrid navigator: {e}[/red]")
            return False
    
    def navigate_to_url(self, url: str) -> bool:
        """Navigate to URL (uses Playwright if available, otherwise Selenium)"""
        try:
            if self.page:
                console.print(f"[cyan]🔗 Navigating to: {url} (Playwright)[/cyan]")
                self.page.goto(url, wait_until='domcontentloaded', timeout=30000)
                time.sleep(2)
                return True
            elif self.driver:
                console.print(f"[cyan]🔗 Navigating to: {url} (Selenium)[/cyan]")
                self.driver.get(url)
                time.sleep(3)
                return True
            return False
        except Exception as e:
            console.print(f"[yellow]⚠️  Navigation failed: {e}[/yellow]")
            return False
    
    def click_element_intelligent(self, text: str = None, selector: str = None) -> bool:
        """
        Click element using Playwright (much more reliable!)
        
        Args:
            text: Text to search for (e.g., "Sign in", "Configuration")
            selector: CSS selector (fallback)
        
        Returns:
            True if clicked successfully
        """
        try:
            if not self.page:
                console.print("[yellow]⚠️  Playwright not connected, using Selenium fallback[/yellow]")
                return self._click_selenium_fallback(text, selector)
            
            console.print(f"[cyan]🖱️  Clicking element (Playwright): {text or selector}[/cyan]")
            
            # Try text-based locator first (most human-like!)
            if text:
                try:
                    # Try exact text
                    locator = self.page.locator(f'text="{text}"').first
                    if locator.is_visible(timeout=5000):
                        locator.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        locator.click()
                        console.print(f"[green]✅ Clicked '{text}' (exact match)[/green]")
                        return True
                except:
                    # Try partial text
                    try:
                        locator = self.page.locator(f'text=/{text}/i').first
                        if locator.is_visible(timeout=5000):
                            locator.scroll_into_view_if_needed()
                            time.sleep(0.3)
                            locator.click()
                            console.print(f"[green]✅ Clicked '{text}' (partial match)[/green]")
                            return True
                    except:
                        pass
            
            # Try selector
            if selector:
                try:
                    locator = self.page.locator(selector).first
                    if locator.is_visible(timeout=5000):
                        locator.scroll_into_view_if_needed()
                        time.sleep(0.3)
                        locator.click()
                        console.print(f"[green]✅ Clicked element by selector[/green]")
                        return True
                except:
                    pass
            
            console.print(f"[yellow]⚠️  Could not find element to click[/yellow]")
            return False
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Click failed: {e}[/yellow]")
            return False
    
    def _click_selenium_fallback(self, text: str = None, selector: str = None) -> bool:
        """Fallback to Selenium clicking if Playwright not available"""
        try:
            if not self.driver:
                return False
            
            from selenium.webdriver.common.by import By
            
            console.print(f"[dim]Using Selenium fallback for clicking[/dim]")
            
            if text:
                try:
                    element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{text}')]")
                    element.click()
                    return True
                except:
                    pass
            
            if selector:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    element.click()
                    return True
                except:
                    pass
            
            return False
        except:
            return False
    
    def find_and_click_cluster(self, cluster_name: str) -> bool:
        """
        Find and click RDS cluster link (uses Playwright's smart finding!)
        
        This is MUCH more reliable than Selenium XPath!
        """
        try:
            if not self.page:
                console.print("[yellow]⚠️  Playwright not available, using Selenium[/yellow]")
                return False
            
            console.print(f"[cyan]🔍 Looking for cluster: {cluster_name}[/cyan]")
            
            # Strategy 1: Find link containing cluster name
            try:
                locator = self.page.locator(f'a:has-text("{cluster_name}")').first
                if locator.is_visible(timeout=5000):
                    console.print(f"[green]✓ Found cluster link[/green]")
                    locator.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    locator.click()
                    console.print(f"[green]✅ Clicked cluster link![/green]")
                    return True
            except Exception as e:
                console.print(f"[dim]Strategy 1 failed: {e}[/dim]")
            
            # Strategy 2: Find any element containing cluster name, then find parent link
            try:
                locator = self.page.locator(f'text=/{cluster_name}/i').first
                parent_link = locator.locator('xpath=ancestor::a').first
                if parent_link.is_visible(timeout=5000):
                    console.print(f"[green]✓ Found cluster via parent link[/green]")
                    parent_link.scroll_into_view_if_needed()
                    time.sleep(0.5)
                    parent_link.click()
                    console.print(f"[green]✅ Clicked cluster link![/green]")
                    return True
            except Exception as e:
                console.print(f"[dim]Strategy 2 failed: {e}[/dim]")
            
            # Strategy 3: JavaScript search
            try:
                console.print(f"[dim]Trying JavaScript search...[/dim]")
                result = self.page.evaluate("""
                    (clusterName) => {
                        const links = document.querySelectorAll('a');
                        for (const link of links) {
                            if (link.textContent.includes(clusterName) || 
                                (link.href && link.href.includes(clusterName))) {
                                link.scrollIntoView({block: 'center'});
                                return {success: true, text: link.textContent};
                            }
                        }
                        return {success: false};
                    }
                """, cluster_name)
                
                if result and result.get('success'):
                    # Now click it with Playwright
                    locator = self.page.locator(f'a:has-text("{result.get("text", cluster_name)}")').first
                    locator.click()
                    console.print(f"[green]✅ Clicked cluster via JavaScript search![/green]")
                    return True
            except Exception as e:
                console.print(f"[dim]Strategy 3 failed: {e}[/dim]")
            
            console.print(f"[red]❌ Could not find cluster '{cluster_name}'[/red]")
            return False
        
        except Exception as e:
            console.print(f"[red]❌ Find and click failed: {e}[/red]")
            return False
    
    def capture_screenshot(self, name: str = None) -> Optional[str]:
        """
        Capture screenshot (uses Playwright if available, otherwise Selenium)
        
        Playwright screenshots are better quality!
        """
        try:
            if not name:
                name = f"aws_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            screenshot_dir = Path.home() / 'Desktop' / 'aws_screenshots'
            screenshot_dir.mkdir(exist_ok=True)
            screenshot_path = screenshot_dir / f"{name}.png"
            
            console.print(f"[cyan]📸 Capturing screenshot...[/cyan]")
            
            if self.page:
                # Playwright screenshot (better!)
                self.page.screenshot(path=str(screenshot_path), full_page=True)
                console.print("[dim]Using Playwright screenshot (better quality!)[/dim]")
            elif self.driver:
                # Selenium screenshot (fallback)
                self.driver.save_screenshot(str(screenshot_path))
                console.print("[dim]Using Selenium screenshot (fallback)[/dim]")
            else:
                console.print("[red]❌ No browser available[/red]")
                return None
            
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
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S %Z')
            
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                font = ImageFont.load_default()
            
            text_bbox = draw.textbbox((0, 0), timestamp, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            x = img.width - text_width - 30
            y = img.height - text_height - 30
            
            padding = 15
            draw.rectangle(
                [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                fill=(0, 0, 0, 180)
            )
            
            draw.text((x + 2, y + 2), timestamp, fill=(0, 0, 0, 255), font=font)
            draw.text((x, y), timestamp, fill=(255, 255, 255, 255), font=font)
            
            img.save(screenshot_path)
        except Exception as e:
            console.print(f"[dim]Could not add timestamp: {e}[/dim]")
    
    def wait_for_duo_auth(self, account_name: str, wait_timeout: int = 300) -> bool:
        """
        Wait for Duo authentication and auto-select account
        
        Uses undetected-chromedriver for auth (bypasses detection!)
        Then uses Playwright for clicking (more reliable!)
        """
        try:
            console.print(f"[cyan]🔐 Waiting for Duo authentication...[/cyan]")
            console.print(f"[yellow]⏳ Please approve Duo push and select account[/yellow]")
            
            start_time = time.time()
            account_selected = False
            
            while time.time() - start_time < wait_timeout:
                try:
                    current_url = self.driver.current_url if self.driver else ""
                    
                    # Check if we reached AWS Console
                    if 'console.aws.amazon.com' in current_url and 'signin' not in current_url:
                        console.print("[green]✅ Successfully signed in to AWS Console[/green]")
                        return True
                    
                    # AWS SAML role selection
                    if 'signin.aws' in current_url and 'saml' in current_url and not account_selected:
                        console.print("[yellow]📋 AWS SAML role selection page[/yellow]")
                        
                        if account_name and self.page:
                            # Use Playwright for clicking (much more reliable!)
                            console.print(f"[cyan]🔑 Selecting '{account_name}' role with Playwright...[/cyan]")
                            
                            # Try to click Admin radio button
                            if self.click_element_intelligent(text="Admin"):
                                time.sleep(1)
                                
                                # Click Sign in button
                                if self.click_element_intelligent(text="Sign in"):
                                    account_selected = True
                                    console.print("[green]✅ Role selected and signing in![/green]")
                                    time.sleep(3)
                    
                    time.sleep(2)
                
                except Exception as e:
                    console.print(f"[dim]Wait loop: {e}[/dim]")
                    time.sleep(2)
            
            console.print("[yellow]⏱️  Timeout waiting for authentication[/yellow]")
            return False
        
        except Exception as e:
            console.print(f"[red]❌ Auth failed: {e}[/red]")
            return False
    
    def close(self):
        """Close browser"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            if self.driver:
                self.driver.quit()
            console.print("[cyan]👋 Hybrid navigator closed[/cyan]")
        except:
            pass


if __name__ == "__main__":
    # Test the hybrid navigator
    console.print("[bold cyan]Testing AWS Hybrid Navigator...[/bold cyan]\n")
    
    nav = AWSHybridNavigator(region='us-east-1', headless=False)
    
    if nav.launch():
        console.print("\n[green]✅ Hybrid navigator launched successfully![/green]")
        console.print("[yellow]🎉 You have undetected-chrome + Playwright power![/yellow]")
        console.print("[yellow]Test complete. Close this script when done.[/yellow]")
        
        input("\nPress Enter to close...")
        nav.close()

