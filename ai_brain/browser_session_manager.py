"""
Browser Session Manager - Maintains ONE browser session for multiple operations

This prevents the annoying problem of opening a new browser for each screenshot,
which requires multiple Duo authentications!

Key features:
- ONE browser session for all operations
- Persistent across multiple requests
- Smart navigation using AWS Console search
- Use browser back/forward buttons
- Only closes when explicitly requested
"""

import time
from typing import Optional, Dict
from rich.console import Console

console = Console()


class BrowserSessionManager:
    """
    Singleton-like manager that maintains ONE browser session for the entire agent lifecycle.
    
    This ensures:
    1. ONE Duo authentication for all screenshots
    2. Faster navigation (no repeated browser launches)
    3. Can use browser back/forward buttons
    4. Can use AWS Console search bar
    5. Can use "Recently viewed" services
    """
    
    # Class-level variables (shared across all instances)
    _browser_instance = None
    _authenticated_accounts = set()  # Track which AWS accounts are authenticated
    _current_region = None
    _current_service = None
    _navigation_history = []
    
    def __init__(self):
        """Initialize manager (reuses existing browser if available)"""
        pass
    
    @classmethod
    def get_browser(cls, force_new: bool = False):
        """
        Get the existing browser instance or create a new one.
        
        Args:
            force_new: If True, closes existing browser and creates new one
        
        Returns:
            Browser instance (UniversalScreenshotEnhanced)
        """
        if force_new and cls._browser_instance:
            console.print("[yellow]🔄 Closing existing browser to create fresh session...[/yellow]")
            try:
                cls._browser_instance.close()
            except:
                pass
            cls._browser_instance = None
            cls._authenticated_accounts.clear()
            cls._current_region = None
            cls._current_service = None
            cls._navigation_history.clear()
        
        if cls._browser_instance is None:
            from tools.universal_screenshot_enhanced import UniversalScreenshotEnhanced
            
            console.print("[bold cyan]🚀 Launching NEW browser session (will be reused!)[/bold cyan]")
            browser = UniversalScreenshotEnhanced(headless=False, timeout=180, debug=True)
            
            if browser.connect():
                cls._browser_instance = browser
                console.print("[green]✅ Browser session ready (will persist for multiple operations!)[/green]")
            else:
                console.print("[red]❌ Failed to launch browser[/red]")
                return None
        else:
            console.print("[dim]♻️  Reusing existing browser session (no new Duo auth needed!)[/dim]")
        
        return cls._browser_instance
    
    @classmethod
    def authenticate_aws(cls, account: str, region: str = "us-east-1") -> bool:
        """
        Authenticate to AWS (only if not already authenticated).
        
        Args:
            account: AWS account name (e.g., 'ctr-prod')
            region: AWS region
        
        Returns:
            True if authenticated (or already was)
        """
        browser = cls.get_browser()
        if not browser:
            return False
        
        # ROBUST CHECK: Verify if actually on AWS Console (not just flag)
        try:
            current_url = browser.driver.current_url if browser.driver else None
            if current_url and 'console.aws.amazon.com' in current_url:
                # Already on AWS Console - mark as authenticated and return
                cls._authenticated_accounts.add(account)
                cls._current_region = region
                console.print(f"[green]✅ Already on AWS Console for {account}! (Session active)[/green]")
                return True
        except:
            pass
        
        # Check if already authenticated to this account (from previous session)
        if account in cls._authenticated_accounts:
            console.print(f"[dim]✓ Already authenticated to {account}[/dim]")
            return True
        
        console.print(f"[cyan]🔐 Authenticating to AWS account: {account}[/cyan]")
        
        # Perform Duo SSO authentication
        if browser.authenticate_aws_duo_sso(account_name=account):
            cls._authenticated_accounts.add(account)
            cls._current_region = region
            console.print(f"[green]✅ Authenticated to {account} successfully![/green]")
            return True
        else:
            console.print(f"[red]❌ Authentication to {account} failed[/red]")
            return False
    
    @classmethod
    def get_universal_navigator(cls):
        """
        Get universal AWS service navigator.
        
        This navigator supports ALL AWS services with human-like behavior!
        
        Returns:
            AWSUniversalServiceNavigator instance
        """
        browser = cls.get_browser()
        if not browser:
            return None
        
        from tools.aws_universal_service_navigator import AWSUniversalServiceNavigator
        
        region = cls._current_region or "us-east-1"
        navigator = AWSUniversalServiceNavigator(browser.driver, region)
        
        return navigator
    
    @classmethod
    def navigate_to_service_via_search(cls, service_name: str, wait_time: int = 3) -> bool:
        """
        Navigate to AWS service using the search bar (just like a human would!).
        
        This is MUCH better than direct URLs because:
        - Faster (no page reload)
        - Uses existing session
        - Just like manual navigation
        
        Args:
            service_name: Service to search for (e.g., 'RDS', 'EC2', 'S3')
            wait_time: Seconds to wait after navigation
        
        Returns:
            True if navigation successful
        """
        browser = cls.get_browser()
        if not browser or not browser.driver:
            console.print("[red]❌ No browser available[/red]")
            return False
        
        try:
            console.print(f"[cyan]🔍 Navigating to {service_name} using AWS Console search...[/cyan]")
            
            # Use JavaScript to open search and navigate (fastest method!)
            browser.driver.execute_script("""
                // Open AWS Console search
                var searchButton = document.querySelector('[data-testid="awsc-nav-search-button"]') ||
                                 document.querySelector('[aria-label="Search"]') ||
                                 document.querySelector('button[aria-label*="Search"]');
                
                if (searchButton) {
                    searchButton.click();
                    
                    // Wait a moment for search box to appear
                    setTimeout(function() {
                        var searchInput = document.querySelector('input[type="search"]') ||
                                        document.querySelector('[data-testid="search-input"]') ||
                                        document.querySelector('input[placeholder*="Search"]');
                        
                        if (searchInput) {
                            searchInput.value = arguments[0];
                            searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                            
                            // Wait for results and click first one
                            setTimeout(function() {
                                var firstResult = document.querySelector('[data-testid="search-result"]') ||
                                                document.querySelector('a[href*="console.aws"]');
                                if (firstResult) {
                                    firstResult.click();
                                }
                            }, 500);
                        }
                    }, 500);
                }
            """, service_name)
            
            time.sleep(wait_time)
            
            # Verify navigation
            current_url = browser.driver.current_url
            if service_name.lower() in current_url.lower():
                console.print(f"[green]✅ Navigated to {service_name}[/green]")
                cls._current_service = service_name
                cls._navigation_history.append(service_name)
                return True
            else:
                console.print(f"[yellow]⚠️  Search may not have worked, current URL: {current_url}[/yellow]")
                # Try direct URL as fallback
                return cls.navigate_to_service_direct(service_name)
        
        except Exception as e:
            console.print(f"[red]❌ Search navigation failed: {e}[/red]")
            # Fallback to direct URL
            return cls.navigate_to_service_direct(service_name)
    
    @classmethod
    def navigate_to_service_direct(cls, service_name: str) -> bool:
        """
        Navigate to service using direct URL (fallback method).
        
        Args:
            service_name: Service name (e.g., 'RDS', 'EC2')
        
        Returns:
            True if successful
        """
        browser = cls.get_browser()
        if not browser or not browser.driver:
            return False
        
        region = cls._current_region or "us-east-1"
        service_lower = service_name.lower()
        
        # Build URL
        url = f"https://{region}.console.aws.amazon.com/{service_lower}/home?region={region}"
        
        console.print(f"[cyan]🔗 Navigating to {service_name} via URL...[/cyan]")
        browser.driver.get(url)
        time.sleep(3)
        
        cls._current_service = service_name
        cls._navigation_history.append(service_name)
        return True
    
    @classmethod
    def go_back(cls) -> bool:
        """Navigate back (like clicking browser back button)"""
        browser = cls.get_browser()
        if not browser or not browser.driver:
            return False
        
        console.print("[cyan]⬅️  Going back...[/cyan]")
        browser.driver.back()
        time.sleep(2)
        return True
    
    @classmethod
    def go_forward(cls) -> bool:
        """Navigate forward (like clicking browser forward button)"""
        browser = cls.get_browser()
        if not browser or not browser.driver:
            return False
        
        console.print("[cyan]➡️  Going forward...[/cyan]")
        browser.driver.forward()
        time.sleep(2)
        return True
    
    @classmethod
    def change_region(cls, new_region: str) -> bool:
        """
        Change AWS region using the region selector.
        
        NOW USES HYBRID APPROACH:
        - Try Playwright (if available) - more reliable!
        - Fallback to Selenium JavaScript
        
        Args:
            new_region: Region to switch to (e.g., 'us-west-2', 'eu-west-1')
        
        Returns:
            True if successful
        """
        browser = cls.get_browser()
        if not browser:
            console.print("[red]❌ No browser session available[/red]")
            return False
        
        console.print(f"[bold cyan]🌍 Changing AWS region: {cls._current_region or 'unknown'} → {new_region}[/bold cyan]")
        
        # Strategy 1: Try Playwright (if hybrid navigator)
        if hasattr(browser, 'page') and browser.page:
            try:
                console.print("[dim]Using Playwright for region change (more reliable!)[/dim]")
                
                # Click region selector button
                region_button_selectors = [
                    '[data-testid="awsc-nav-region-menu-button"]',
                    'button[aria-label*="region"]',
                    '#regionMenuButton'
                ]
                
                clicked_button = False
                for selector in region_button_selectors:
                    try:
                        locator = browser.page.locator(selector).first
                        if locator.is_visible(timeout=2000):
                            locator.click()
                            clicked_button = True
                            console.print(f"[dim]Clicked region button using selector: {selector}[/dim]")
                            break
                    except:
                        continue
                
                if not clicked_button:
                    console.print("[yellow]⚠️  Could not click region button, trying Selenium fallback...[/yellow]")
                    return cls._change_region_selenium(browser, new_region)
                
                # Wait for dropdown to open
                time.sleep(1)
                
                # Find and click the target region
                region_clicked = False
                region_selectors = [
                    f'[data-region="{new_region}"]',
                    f'button:has-text("{new_region}")',
                    f'[aria-label*="{new_region}"]'
                ]
                
                for selector in region_selectors:
                    try:
                        locator = browser.page.locator(selector).first
                        if locator.is_visible(timeout=2000):
                            locator.click()
                            region_clicked = True
                            console.print(f"[dim]Clicked region option using selector: {selector}[/dim]")
                            break
                    except:
                        continue
                
                if not region_clicked:
                    console.print("[yellow]⚠️  Could not click region option, trying Selenium fallback...[/yellow]")
                    return cls._change_region_selenium(browser, new_region)
                
                time.sleep(3)  # Wait for page reload
                cls._current_region = new_region
                console.print(f"[bold green]✅ Successfully changed to region: {new_region}[/bold green]")
                return True
            
            except Exception as e:
                console.print(f"[yellow]⚠️  Playwright region change failed: {e}[/yellow]")
                console.print("[yellow]   Trying Selenium fallback...[/yellow]")
                return cls._change_region_selenium(browser, new_region)
        
        # Strategy 2: Selenium fallback
        return cls._change_region_selenium(browser, new_region)
    
    @classmethod
    def _change_region_selenium(cls, browser, new_region: str) -> bool:
        """Selenium fallback for region changing"""
        try:
            if not browser.driver:
                return False
            
            console.print("[dim]Using Selenium for region change[/dim]")
            
            # Fixed JavaScript - properly captures the region variable!
            browser.driver.execute_script("""
                var targetRegion = arguments[0];
                console.log('=== Region Change (Selenium) ===');
                console.log('Target region:', targetRegion);
                
                // Find and click region selector
                var regionButton = document.querySelector('[data-testid="awsc-nav-region-menu-button"]') ||
                                 document.querySelector('button[aria-label*="region"]') ||
                                 document.querySelector('#regionMenuButton');
                
                if (regionButton) {
                    console.log('Clicking region selector...');
                    regionButton.click();
                    
                    // Use captured variable in setTimeout!
                    setTimeout(function() {
                        console.log('Looking for region:', targetRegion);
                        
                        // Try multiple selectors
                        var regionOption = document.querySelector('[data-region="' + targetRegion + '"]');
                        
                        if (!regionOption) {
                            // Try aria-label
                            var buttons = document.querySelectorAll('button[aria-label]');
                            for (var i = 0; i < buttons.length; i++) {
                                if (buttons[i].getAttribute('aria-label').includes(targetRegion)) {
                                    regionOption = buttons[i];
                                    break;
                                }
                            }
                        }
                        
                        if (!regionOption) {
                            // Try text content
                            var allButtons = document.querySelectorAll('button');
                            for (var j = 0; j < allButtons.length; j++) {
                                if ((allButtons[j].textContent || '').includes(targetRegion)) {
                                    regionOption = allButtons[j];
                                    break;
                                }
                            }
                        }
                        
                        if (regionOption) {
                            console.log('Found region option, clicking...');
                            regionOption.click();
                        } else {
                            console.log('ERROR: Region option not found for:', targetRegion);
                        }
                    }, 1000);  // Increased timeout for dropdown to fully open
                }
            """, new_region)
            
            time.sleep(4)  # Wait for region change to complete
            cls._current_region = new_region
            console.print(f"[green]✅ Region changed to {new_region} (Selenium)[/green]")
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Selenium region change failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    @classmethod
    def close_browser(cls):
        """
        Close the browser session (should only be called at the end or on explicit request).
        """
        if cls._browser_instance:
            console.print("[yellow]🔒 Closing browser session...[/yellow]")
            try:
                cls._browser_instance.close()
            except:
                pass
            cls._browser_instance = None
            cls._authenticated_accounts.clear()
            cls._current_region = None
            cls._current_service = None
            cls._navigation_history.clear()
            console.print("[green]✅ Browser session closed[/green]")
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get current session status"""
        return {
            "browser_active": cls._browser_instance is not None,
            "authenticated_accounts": list(cls._authenticated_accounts),
            "current_region": cls._current_region,
            "current_service": cls._current_service,
            "navigation_history": cls._navigation_history
        }

