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

import re
import time
from typing import Optional, Dict
from urllib.parse import urlparse, parse_qs
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
    _last_authenticated_account = None
    _last_authenticated_region = None

    @classmethod
    def _is_invalid_session_error(cls, error: Exception) -> bool:
        """Return True if the exception looks like a stale/invalid browser session."""
        message = str(error).lower()
        return any(keyword in message for keyword in [
            "invalid session id",
            "target window already closed",
            "chrome not reachable",
            "webview not found",
            "session deleted because",
            "disconnected"
        ])

    @classmethod
    def _teardown_browser_instance(cls):
        """Close the current browser instance and reset cached state."""
        if cls._browser_instance:
            try:
                cls._browser_instance.close()
            except Exception:
                pass
        cls._browser_instance = None
        cls._authenticated_accounts.clear()
        cls._current_region = None
        cls._current_service = None
        cls._navigation_history.clear()

    @classmethod
    def _handle_invalid_session(cls, message: str, error: Optional[Exception] = None):
        """Log session loss and reset the cached browser so a fresh one can be created."""
        console.print(f"[yellow]⚠️  {message}[/yellow]")
        if error and not cls._is_invalid_session_error(error):
            console.print(f"[yellow]   Details: {error}[/yellow]")
        cls._teardown_browser_instance()

    @classmethod
    def _ensure_browser_session_valid(cls) -> bool:
        """Verify that the cached browser session is still alive."""
        browser = cls._browser_instance
        if not browser:
            return False

        driver = getattr(browser, 'driver', None)
        if not driver:
            cls._handle_invalid_session("Browser driver is missing; refreshing session...", error=None)
            return False

        session_id = getattr(driver, 'session_id', None)
        if not session_id:
            cls._handle_invalid_session("Browser session no longer has a valid session_id; refreshing...", error=None)
            return False

        try:
            driver.execute_script("return document.readyState")
            return True
        except Exception as exc:
            if cls._is_invalid_session_error(exc):
                cls._handle_invalid_session("Persistent browser session expired; relaunching before continuing...", exc)
            else:
                cls._handle_invalid_session("Browser health check failed; recreating session...", exc)
            return False
    
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
            cls._teardown_browser_instance()

        if cls._browser_instance and not cls._ensure_browser_session_valid():
            console.print("[yellow]🔄 Re-launching browser session after health check failure...[/yellow]")

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
                cls._authenticated_accounts.add(account)
                cls._last_authenticated_account = account
                console.print(f"[green]✅ Already on AWS Console for {account}! (Session active)[/green]")
                cls._refresh_current_region(reason="existing session")
                cls._dismiss_cookie_banner()
                return True
        except Exception:
            pass

        # Check if already authenticated to this account (from previous session)
        if account in cls._authenticated_accounts:
            console.print(f"[dim]✓ Already authenticated to {account}[/dim]")
            cls._last_authenticated_account = account
            cls._refresh_current_region(reason="cached authentication")
            cls._dismiss_cookie_banner()
            return True

        console.print(f"[cyan]🔐 Authenticating to AWS account: {account}[/cyan]")

        # Perform Duo SSO authentication
        if browser.authenticate_aws_duo_sso(account_name=account):
            cls._authenticated_accounts.add(account)
            cls._last_authenticated_account = account
            console.print(f"[green]✅ Authenticated to {account} successfully![/green]")
            cls._refresh_current_region(reason="post-authentication")
            cls._dismiss_cookie_banner()
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
    def navigate_to_service_via_search(cls, service_name: str, wait_time: int = 3, allow_retry: bool = True) -> bool:
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
                return cls.navigate_to_service_direct(service_name, allow_retry=allow_retry)
        
        except Exception as e:
            if cls._is_invalid_session_error(e):
                cls._handle_invalid_session("Search navigation failed because the browser session ended unexpectedly.", e)
                if allow_retry and cls._last_authenticated_account:
                    console.print(f"[cyan]🔁 Restoring AWS session before retrying navigation to {service_name}...[/cyan]")
                    if cls.authenticate_aws(account=cls._last_authenticated_account, region=cls._last_authenticated_region or cls._current_region or "us-east-1"):
                        return cls.navigate_to_service_via_search(service_name, wait_time=wait_time, allow_retry=False)
                return False

            console.print(f"[red]❌ Search navigation failed: {e}[/red]")
            # Fallback to direct URL
            return cls.navigate_to_service_direct(service_name, allow_retry=allow_retry)
    
    @classmethod
    def navigate_to_service_direct(cls, service_name: str, allow_retry: bool = True) -> bool:
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
        try:
            browser.driver.get(url)
            time.sleep(3)
        except Exception as e:
            if cls._is_invalid_session_error(e):
                cls._handle_invalid_session("Direct navigation failed because the browser session ended.", e)
                if allow_retry and cls._last_authenticated_account:
                    console.print(f"[cyan]🔁 Recovering AWS session before retrying direct navigation to {service_name}...[/cyan]")
                    if cls.authenticate_aws(account=cls._last_authenticated_account, region=cls._last_authenticated_region or cls._current_region or "us-east-1"):
                        return cls.navigate_to_service_direct(service_name, allow_retry=False)
                return False

            console.print(f"[red]❌ Direct navigation to {service_name} failed: {e}[/red]")
            return False

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
        try:
            browser.driver.back()
            time.sleep(2)
        except Exception as e:
            if cls._is_invalid_session_error(e):
                cls._handle_invalid_session("Unable to go back because the browser session ended.", e)
                if cls._last_authenticated_account:
                    console.print("[cyan]🔁 Session restore required; re-authenticating before continuing back navigation...[/cyan]")
                    if cls.authenticate_aws(account=cls._last_authenticated_account, region=cls._last_authenticated_region or cls._current_region or "us-east-1"):
                        return True
                return False

            console.print(f"[red]❌ Failed to navigate back: {e}[/red]")
            return False

        return True
    
    @classmethod
    def go_forward(cls) -> bool:
        """Navigate forward (like clicking browser forward button)"""
        browser = cls.get_browser()
        if not browser or not browser.driver:
            return False

        console.print("[cyan]➡️  Going forward...[/cyan]")
        try:
            browser.driver.forward()
            time.sleep(2)
        except Exception as e:
            if cls._is_invalid_session_error(e):
                cls._handle_invalid_session("Unable to go forward because the browser session ended.", e)
                if cls._last_authenticated_account:
                    console.print("[cyan]🔁 Session restore required; re-authenticating before continuing forward navigation...[/cyan]")
                    if cls.authenticate_aws(account=cls._last_authenticated_account, region=cls._last_authenticated_region or cls._current_region or "us-east-1"):
                        return True
                return False

            console.print(f"[red]❌ Failed to navigate forward: {e}[/red]")
            return False

        return True
    
    @classmethod
    def change_region(cls, new_region: str, allow_retry: bool = True) -> bool:
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
                    return cls._change_region_selenium(browser, new_region, allow_retry=allow_retry)
                
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
                    return cls._change_region_selenium(browser, new_region, allow_retry=allow_retry)
                
                # Wait for region change to take effect and verify
                for _ in range(10):
                    time.sleep(1)
                    detected = cls._detect_current_region(browser)
                    if detected == new_region:
                        cls._current_region = detected
                        cls._last_authenticated_region = detected
                        cls._dismiss_cookie_banner(browser)
                        console.print(f"[bold green]✅ Successfully changed to region: {new_region}[/bold green]")
                        return True

                detected = cls._detect_current_region(browser)
                console.print(f"[yellow]⚠️  Region change verification failed (detected: {detected or 'unknown'})[/yellow]")
                if detected:
                    cls._current_region = detected
                    cls._last_authenticated_region = detected
                return False
            
            except Exception as e:
                console.print(f"[yellow]⚠️  Playwright region change failed: {e}[/yellow]")
                console.print("[yellow]   Trying Selenium fallback...[/yellow]")
                return cls._change_region_selenium(browser, new_region, allow_retry=allow_retry)

        # Strategy 2: Selenium fallback
        return cls._change_region_selenium(browser, new_region, allow_retry=allow_retry)

    @classmethod
    def _change_region_selenium(cls, browser, new_region: str, allow_retry: bool = True) -> bool:
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
            
            # Wait for region change to complete and verify using detection
            detected = None
            for _ in range(12):
                time.sleep(1)
                detected = cls._detect_current_region(browser)
                if detected == new_region:
                    cls._current_region = detected
                    cls._dismiss_cookie_banner(browser)
                    console.print(f"[green]✅ Region changed to {new_region} (Selenium)[/green]")
                    cls._last_authenticated_region = new_region
                    return True

            console.print(f"[yellow]⚠️  Unable to confirm region change to {new_region} (detected: {detected or 'unknown'})[/yellow]")
            if detected:
                cls._current_region = detected
                cls._last_authenticated_region = detected
            return False

        except Exception as e:
            if cls._is_invalid_session_error(e):
                cls._handle_invalid_session("Selenium region change failed because the browser session was lost.", e)
                if allow_retry and cls._last_authenticated_account:
                    console.print(f"[cyan]🔁 Attempting automatic AWS re-authentication for {cls._last_authenticated_account}...[/cyan]")
                    if cls.authenticate_aws(account=cls._last_authenticated_account, region=new_region):
                        return cls.change_region(new_region, allow_retry=False)
                return False

            console.print(f"[red]❌ Selenium region change failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False

    @classmethod
    def _extract_region_from_url(cls, url: Optional[str]) -> Optional[str]:
        """Extract region code from an AWS Console URL if present"""
        if not url:
            return None

        try:
            parsed = urlparse(url)
        except Exception:
            return None

        # Check subdomain (e.g., eu-west-1.console.aws.amazon.com)
        host_parts = parsed.netloc.split('.') if parsed.netloc else []
        if host_parts:
            candidate = host_parts[0]
            if re.fullmatch(r"[a-z]{2}-[a-z0-9-]+-[0-9]", candidate):
                return candidate

        # Check query parameters
        query_regions = parse_qs(parsed.query or "").get('region')
        if query_regions:
            return query_regions[0]

        # Check hash fragment (some consoles include region there)
        fragment = parsed.fragment or ''
        match = re.search(r'region=([a-z0-9-]+)', fragment)
        if match:
            return match.group(1)

        return None

    @classmethod
    def _detect_current_region(cls, browser=None) -> Optional[str]:
        """Detect the currently active AWS region"""
        browser = browser or cls._browser_instance
        driver = getattr(browser, 'driver', None)
        if not driver:
            return None

        # First, try to extract from URL
        try:
            url = driver.current_url
            region = cls._extract_region_from_url(url)
            if region:
                return region
        except Exception:
            pass

        # Fallback: inspect region selector via JavaScript
        try:
            region = driver.execute_script("""
                try {
                    var selectors = [
                        '[data-testid="awsc-nav-region-menu-button"]',
                        'button[aria-label*="region" i]',
                        '#regionMenuButton'
                    ];

                    for (var i = 0; i < selectors.length; i++) {
                        var el = document.querySelector(selectors[i]);
                        if (!el) { continue; }

                        if (el.dataset) {
                            if (el.dataset.region) { return el.dataset.region; }
                            if (el.dataset.regionCode) { return el.dataset.regionCode; }
                        }

                        var label = (el.getAttribute('aria-label') || '').toLowerCase();
                        var text = (el.innerText || el.textContent || '').toLowerCase();
                        var combined = label + ' ' + text;
                        var match = combined.match(/([a-z]{2}-[a-z0-9-]+-[0-9])/);
                        if (match && match[1]) { return match[1]; }
                    }

                    var menu = document.querySelector('[data-region] [aria-current="true"], [role="menu"] [aria-current="true"]');
                    if (menu) {
                        var attrs = [menu.getAttribute('data-region'), menu.getAttribute('aria-label'), menu.innerText];
                        for (var j = 0; j < attrs.length; j++) {
                            var value = (attrs[j] || '').toLowerCase();
                            var match = value.match(/([a-z]{2}-[a-z0-9-]+-[0-9])/);
                            if (match && match[1]) { return match[1]; }
                        }
                    }
                } catch (err) {
                    console.warn('Region detection error', err);
                }
                return null;
            """)
            if region:
                return region
        except Exception:
            pass

        return None

    @classmethod
    def _refresh_current_region(cls, reason: str = "", browser=None) -> Optional[str]:
        """Update the cached region based on the active console view"""
        browser = browser or cls._browser_instance
        detected = cls._detect_current_region(browser)

        if detected:
            if cls._current_region != detected:
                note = f" ({reason})" if reason else ""
                console.print(f"[cyan]🧭 Detected active AWS region: {detected}{note}[/cyan]")
            cls._current_region = detected
            cls._last_authenticated_region = detected
        elif reason:
            console.print(f"[yellow]⚠️  Unable to detect AWS region{f' ({reason})' if reason else ''}[/yellow]")

        return detected

    @classmethod
    def _dismiss_cookie_banner(cls, browser=None) -> bool:
        """Automatically accept AWS cookie consent banner if present"""
        browser = browser or cls._browser_instance
        driver = getattr(browser, 'driver', None)
        if not driver:
            return False

        try:
            clicked = driver.execute_script("""
                try {
                    var keywords = arguments[0];
                    var selectors = [
                        '[data-testid="awsui-dialog__acknowledge-button"]',
                        '[data-testid*="cookie"][data-action*="accept" i]',
                        'button', 'a', '[role="button"]', 'input[type="submit"]'
                    ];

                    var seen = new Set();
                    function matches(el) {
                        if (!el || seen.has(el)) { return null; }
                        seen.add(el);
                        var text = (el.innerText || el.textContent || el.value || '').trim().toLowerCase();
                        if (!text) { return null; }
                        for (var i = 0; i < keywords.length; i++) {
                            if (text.includes(keywords[i])) {
                                return text;
                            }
                        }
                        return null;
                    }

                    function tryClick(elements) {
                        if (!elements) { return null; }
                        for (var i = 0; i < elements.length; i++) {
                            var label = matches(elements[i]);
                            if (label) {
                                elements[i].click();
                                return label;
                            }
                        }
                        return null;
                    }

                    // Direct buttons
                    for (var s = 0; s < selectors.length; s++) {
                        var found = tryClick(document.querySelectorAll(selectors[s]));
                        if (found) { return found; }
                    }

                    // Banner-specific containers
                    var banner = document.querySelector('[data-testid*="cookie"], [aria-label*="cookie" i], [id*="cookie"]');
                    if (banner) {
                        var result = tryClick(banner.querySelectorAll('button, a, [role="button"], input[type="submit"]'));
                        if (result) { return result; }
                    }
                } catch (err) {
                    console.warn('Cookie banner detection error', err);
                }
                return null;
            """, [
                'accept all', 'accept', 'allow all', 'got it', 'agree', 'i understand', 'ok'
            ])

            if clicked:
                text = str(clicked).strip()
                console.print(f"[green]🍪 Accepted AWS cookie banner ({text})[/green]")
                return True
        except Exception:
            return False

        return False

    @classmethod
    def close_browser(cls):
        """
        Close the browser session (should only be called at the end or on explicit request).
        """
        if cls._browser_instance:
            console.print("[yellow]🔒 Closing browser session...[/yellow]")
            cls._teardown_browser_instance()
            console.print("[green]✅ Browser session closed[/green]")
    
    @classmethod
    def get_status(cls) -> Dict:
        """Get current session status"""
        return {
            "browser_active": cls._browser_instance is not None,
            "authenticated_accounts": list(cls._authenticated_accounts),
            "current_region": cls._current_region,
            "last_authenticated_account": cls._last_authenticated_account,
            "last_authenticated_region": cls._last_authenticated_region,
            "current_service": cls._current_service,
            "navigation_history": cls._navigation_history
        }

