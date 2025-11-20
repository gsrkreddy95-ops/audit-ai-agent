"""
Universal Enhanced Screenshot Tool - For All Evidence Collection
Intelligent navigation, multiple click strategies, smart waits, robust error handling
Works across AWS, Azure, Kubernetes, Datadog, Splunk, ServiceNow, etc.
"""

import os
import time
import re
import base64
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Optional, Tuple, List, Callable, TYPE_CHECKING
from enum import Enum
from urllib.parse import urlparse
import io
from rich.prompt import Prompt

try:
    import undetected_chromedriver as uc
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.common.action_chains import ActionChains
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import (
        TimeoutException, NoSuchElementException, 
        StaleElementReferenceException, ElementClickInterceptedException
    )
    SELENIUM_AVAILABLE = True
    print("[DEBUG] Selenium imports successful")
except ImportError as e:
    SELENIUM_AVAILABLE = False
    print(f"⚠️  Selenium import failed: {e}")

# Playwright for advanced element interaction
try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
    print("[DEBUG] Playwright available for advanced interactions")
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("[DEBUG] Playwright not available (optional)")

# AWS Federation authentication (bypasses SAML button!)
try:
    from tools.aws_federation_auth import AWSFederationAuth
    FEDERATION_AVAILABLE = True
    print("[DEBUG] AWS Federation authentication available")
except ImportError:
    FEDERATION_AVAILABLE = False
    print("[DEBUG] AWS Federation not available (optional)")
    # Provide dummy classes for type hints
    class By:
        XPATH = "xpath"
        CSS_SELECTOR = "css"
        ID = "id"
        CLASS_NAME = "class"
    
    class Keys:
        ENTER = "enter"
        RETURN = "return"

from PIL import Image, ImageDraw, ImageFont
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


class ClickStrategy(Enum):
    """Different strategies for clicking elements"""
    DIRECT = "direct"  # Standard Selenium click
    JAVASCRIPT = "javascript"  # JavaScript-based click
    ACTION_CHAIN = "action_chain"  # ActionChains click
    FOCUS_AND_ENTER = "focus_and_enter"  # Focus + press Enter
    JAVASCRIPT_DOUBLE_CLICK = "javascript_double_click"  # JavaScript double-click
    TAB_AND_ENTER = "tab_and_enter"  # Tab navigation + Enter


class WaitCondition(Enum):
    """Different conditions to wait for"""
    PRESENCE = "presence"  # Element exists
    VISIBILITY = "visibility"  # Element is visible
    CLICKABILITY = "clickability"  # Element is clickable
    TEXT = "text"  # Specific text appears
    URL_CONTAINS = "url_contains"  # URL contains string
    URL_CHANGES = "url_changes"  # URL changes from initial
    ATTRIBUTE = "attribute"  # Element attribute equals value
    ELEMENT_GONE = "element_gone"  # Element disappears


class UniversalScreenshotEnhanced:
    """Universal screenshot tool with intelligent navigation.

    Added optional 'debug' flag (previous calls passed debug=True and caused a TypeError).
    Accept and store arbitrary **kwargs for forward compatibility so future flags
    don't break constructor (e.g., tracing, profiling). Unknown kwargs are ignored.
    """
    
    def __init__(self, headless: bool = False, timeout: int = 20, debug: bool = False, persistent_profile: bool = False, profile_dir: Optional[str] = None, **kwargs):
        self.headless = headless
        self.timeout = timeout
        self.debug = debug
        self.persistent_profile = persistent_profile  # NEW: Control cookie persistence
        self.driver = None
        self.wait = None
        
        # Support custom profile directory for multi-account sessions
        if profile_dir:
            self.user_data_dir = profile_dir
            if self.debug:
                console.print(f"[dim]📂 Using custom profile: {self.user_data_dir}[/dim]")
        elif self.persistent_profile:
            self.user_data_dir = os.path.expanduser('~/.audit-agent-universal-selenium')
            if self.debug:
                console.print(f"[dim]📂 Using persistent profile: {self.user_data_dir}[/dim]")
        else:
            self.user_data_dir = None  # Use temporary profile
            if self.debug:
                console.print(f"[dim]🔄 Using temporary profile (fresh session each run)[/dim]")
        
        self.click_history = []  # Track what we clicked
        self.navigation_history = []  # Track navigation
        self._extra_config = kwargs  # Preserve for inspection/logging if needed
        
        # Playwright attributes (for advanced element interaction)
        self.playwright = None
        self.browser_pw = None
        self.page = None
        self.last_role_selected: Optional[str] = None
        
        # AWS Federation attributes (bypasses SAML sign-in button!)
        self.federation_auth = None
        self.use_federation = FEDERATION_AVAILABLE  # Use Federation if available
        
        if self.debug:
            console.print(f"[dim]🛠️ UniversalScreenshotEnhanced initialized (debug mode, timeout={timeout})[/dim]")
            if self.use_federation:
                console.print(f"[dim]🎫 AWS Federation authentication enabled (bypasses SAML button!)[/dim]")
        
    def connect(self, browser_type: str = 'chrome') -> bool:
        """Launch browser"""
        try:
            console.print(f"[cyan]🌐 Launching {browser_type} for evidence collection...[/cyan]")
            
            if browser_type.lower() == 'chrome':
                options = uc.ChromeOptions()
                if self.headless:
                    options.add_argument('--headless=new')
                
                # Only use persistent profile if requested (default: temporary profile)
                if self.user_data_dir:
                    options.add_argument(f'--user-data-dir={self.user_data_dir}')
                    console.print(f"[dim]   Using persistent profile (cookies saved)[/dim]")
                else:
                    # Use temporary profile - no cookie persistence!
                    console.print(f"[dim]   Using temporary profile (no cookie persistence)[/dim]")
                
                options.add_argument('--window-size=1920,1080')
                options.add_argument('--start-maximized')
                options.add_argument('--disable-blink-features=AutomationControlled')
                options.add_argument('--disable-web-resources')
                options.add_argument('--no-sandbox')  # Helps with launch issues
                options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
                options.add_argument('--remote-debugging-port=9222')  # Enable CDP for Playwright
                
                try:
                    self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
                except Exception as chrome_error:
                    console.print(f"[yellow]⚠️  Chrome launch failed: {str(chrome_error)[:100]}[/yellow]")
                    console.print(f"[cyan]💡 Trying with fresh profile...[/cyan]")
                    
                    # Try without user data dir (fresh profile)
                    options = uc.ChromeOptions()
                    if self.headless:
                        options.add_argument('--headless=new')
                    options.add_argument('--window-size=1920,1080')
                    options.add_argument('--start-maximized')
                    options.add_argument('--no-sandbox')
                    options.add_argument('--disable-dev-shm-usage')
                    options.add_argument('--remote-debugging-port=9222')  # Enable CDP for Playwright
                    
                    self.driver = uc.Chrome(options=options, version_main=None, use_subprocess=True)
            else:
                console.print(f"[red]❌ Browser type '{browser_type}' not supported[/red]")
                return False
            
            if not self.driver:
                console.print(f"[red]❌ Browser driver is None[/red]")
                return False
            
            self.wait = WebDriverWait(self.driver, self.timeout)
            console.print(f"[green]✅ Browser ready (timeout: {self.timeout}s)[/green]")
            
            # Connect Playwright for advanced element interaction
            self._connect_playwright_via_cdp()
            
            # Initialize AWS Federation authentication (if available)
            if FEDERATION_AVAILABLE and self.use_federation:
                self.federation_auth = AWSFederationAuth(self.driver, debug=self.debug)
                if self.debug:
                    console.print(f"[dim]🎫 AWS Federation authentication initialized[/dim]")
            
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Browser launch failed: {e}[/red]")
            console.print(f"[yellow]💡 Tip: Close any existing Chrome windows and try again[/yellow]")
            self.driver = None
            return False
    
    def _connect_playwright_via_cdp(self):
        """Connect Playwright to the running Chrome via CDP for advanced interactions"""
        if not PLAYWRIGHT_AVAILABLE:
            if self.debug:
                console.print("[dim]Playwright not available (optional)[/dim]")
            return
        
        try:
            # Get CDP endpoint from Selenium
            if not self.driver:
                return
            
            # Connect Playwright to existing Chrome
            self.playwright = sync_playwright().start()
            
            # Connect to the existing browser via CDP with retry
            # undetected-chromedriver doesn't expose CDP URL directly,
            # so we connect to default debugging port 9222
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    console.print(f"[dim]🎭 Connecting Playwright to Chrome (attempt {attempt + 1}/{max_retries})...[/dim]")
                    self.browser_pw = self.playwright.chromium.connect_over_cdp("http://localhost:9222")
                    contexts = self.browser_pw.contexts
                    if contexts:
                        self.page = contexts[0].pages[0] if contexts[0].pages else None
                        if self.page:
                            console.print(f"[green]✅ Playwright connected via CDP![/green]")
                            return
                except Exception as e:
                    if attempt < max_retries - 1:
                        console.print(f"[yellow]⚠️  Attempt {attempt + 1} failed, retrying...[/yellow]")
                        time.sleep(2)
                    else:
                        if self.debug:
                            console.print(f"[dim]Playwright CDP connection failed after {max_retries} attempts: {e}[/dim]")
        except Exception as e:
            if self.debug:
                console.print(f"[dim]Playwright connection setup failed: {e}[/dim]")
    
    def _get_current_playwright_page(self):
        """Get the current active Playwright page (handles navigation)"""
        if not PLAYWRIGHT_AVAILABLE or not self.browser_pw:
            return None
        
        try:
            # Get all contexts and find the active page
            contexts = self.browser_pw.contexts
            if contexts:
                for context in contexts:
                    pages = context.pages
                    if pages:
                        # Return the last page (most recently active)
                        return pages[-1]
        except:
            pass
        
        return None
    
    # ==================== AWS DUO SSO AUTHENTICATION (NEW FEDERATION APPROACH!) ====================
    def authenticate_aws_duo_sso_with_federation(
        self,
        destination_url: str,
        duo_url: str = None,
        wait_timeout: int = 300,
        account_name: str = None
    ) -> bool:
        """
        NEW APPROACH: Authenticate to AWS using Federation API (bypasses SAML button!).
        
        This is the industry-standard approach that:
        1. Completes Duo authentication
        2. Extracts SAML assertion
        3. Uses AWS Federation API to get direct console URL
        4. Navigates directly to destination (no button clicking!)
        
        Args:
            destination_url: Target AWS console page (e.g., RDS clusters page)
            duo_url: Duo SSO URL (default: CTR Duo)
            wait_timeout: Max seconds to wait for Duo auth
            account_name: AWS account name (for logging)
        
        Returns:
            True if successfully authenticated and navigated to destination
        """
        try:
            # Check if we can reuse cached Federation token
            if self.federation_auth and self.federation_auth.is_token_valid():
                console.print("[green]♻️  Reusing cached Federation token[/green]")
                console_url = self.federation_auth.get_cached_console_url(destination_url)
                if console_url:
                    console.print(f"[cyan]🌐 Navigating to: {destination_url}[/cyan]")
                    self.driver.get(console_url)
                    time.sleep(3)
                    
                    # Verify we reached the destination
                    current_url = self.driver.current_url
                    if 'console.aws.amazon.com' in current_url:
                        console.print(f"[green]✅ Reached AWS Console via Federation![/green]")
                        return True
            
            # Need fresh authentication
            console.print(f"[bold cyan]🎫 AWS Federation Authentication (NO SAML BUTTON!)[/bold cyan]")
            
            # Step 1: Navigate to Duo SSO
            if not duo_url:
                duo_url = "https://sso-dbbfec7f.sso.duosecurity.com/saml2/sp/DIRGUUDMLYKC10GOCNOR/sso"
            
            console.print(f"[cyan]🔗 Navigating to Duo SSO...[/cyan]")
            if account_name:
                console.print(f"[dim]Target account: {account_name}[/dim]")
            
            self.driver.get(duo_url)
            time.sleep(3)
            
            # Step 2: Wait for user to complete Duo authentication
            console.print(f"[yellow]⏳ Complete Duo authentication (up to {wait_timeout//60} min)...[/yellow]")
            console.print("[yellow]   1. Approve Duo push on your phone[/yellow]")
            console.print("[green]   2. ⭐ CHECK 'Trust this browser' ⭐[/green]")
            console.print("[yellow]   3. Federation will auto-extract credentials![/yellow]")
            
            # Step 3: Use Federation to get direct console URL
            if not self.federation_auth:
                console.print("[red]❌ Federation auth not initialized[/red]")
                return False
            
            console_url = self.federation_auth.authenticate_and_get_console_url(
                destination=destination_url,
                account_name=account_name,
                wait_timeout=wait_timeout
            )
            
            if not console_url:
                console.print("[red]❌ Federation authentication failed[/red]")
                return False
            
            # Step 4: Navigate directly to destination (bypasses SAML page!)
            console.print(f"[bold green]🚀 Federation successful! Navigating directly to console...[/bold green]")
            console.print(f"[cyan]🌐 Destination: {destination_url}[/cyan]")
            
            self.driver.get(console_url)
            time.sleep(3)
            
            # Verify we reached AWS Console
            current_url = self.driver.current_url
            if 'console.aws.amazon.com' in current_url:
                console.print(f"[green]✅ SUCCESS! Reached AWS Console via Federation![/green]")
                console.print(f"[green]✅ No SAML button clicking needed![/green]")
                return True
            else:
                console.print(f"[yellow]⚠️  Navigation incomplete, current URL: {current_url}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Federation authentication failed: {e}[/red]")
            return False
    
    # ==================== AWS DUO SSO AUTHENTICATION (OLD BUTTON-CLICKING APPROACH) ====================
    def authenticate_aws_duo_sso(self, duo_url: str = None, wait_timeout: int = 300, account_name: str = None, role_name: str = None) -> bool:
        """Navigate to Duo SSO and wait for authentication to complete.
        
        Args:
            duo_url: The Duo SSO URL. If None, uses default CTR Duo URL.
            wait_timeout: Max seconds to wait for authentication (default 5 min)
            account_name: AWS account to auto-select (e.g., 'ctr-prod', 'ctr-int'). If None, manual selection required.
            role_name: Desired AWS role name (e.g., 'ROAdmin'). Used as preference when multiple roles exist.
            
        Returns:
            True if successfully authenticated and reached console, False otherwise
        """
        try:
            # Safety check: Ensure browser is connected
            if not self.driver:
                console.print(f"[red]❌ Browser not initialized. Call connect() first.[/red]")
                return False
            
            # ROBUST CHECK: Skip SSO navigation if already authenticated!
            try:
                current_url = self.driver.current_url
                
                # Case 1: Already on AWS Console - Perfect! Skip everything
                if current_url and 'console.aws.amazon.com' in current_url:
                    console.print(f"[green]✅ Already on AWS Console! (Session active)[/green]")
                    return True
                
                # Case 2: On session selector / Choose session page - Click the session and VERIFY!
                # Handles both classic selector URL and newer oauth-based "Choose your AWS session" screen
                page_source = None
                try:
                    page_source = self.driver.page_source
                except Exception:
                    if self.debug:
                        console.print("[dim]   Unable to read page source for session detection[/dim]")

                if self._is_session_selector_page(current_url, page_source):
                    console.print(
                        f"[yellow]⚠️  AWS session selector detected - auto-clicking session...[/yellow]"
                    )

                    clicked = False
                    
                    # Strategy 1: Playwright (get CURRENT page, not stale!)
                    if account_name:
                        try:
                            page = self._get_current_playwright_page()
                            if page:
                                console.print(f"[dim]   Strategy 1: Playwright with multiple selectors...[/dim]")
                                
                                # Try multiple ways to find the session link
                                session_selectors = [
                                    f'a:has-text("{account_name}")',  # Exact text match
                                    f'a[href*="console"]:has-text("{account_name}")',  # Link to console with account name
                                    f'awsui-card:has-text("{account_name}")',  # New OAuth card layout
                                    f'[data-testid*="session"]:has-text("{account_name}")',
                                    'a[href*="console"]',  # Any console link (first one)
                                    'awsui-card',
                                ]
                                
                                skip_phrases = [
                                    "sign into new session",
                                    "sign in to new session",
                                    "start new session",
                                    "new session",
                                    "different user",
                                    "different account",
                                ]

                                for selector in session_selectors:
                                    try:
                                        console.print(f"[dim]      Trying: {selector}[/dim]")
                                        session_locator = page.locator(selector).first
                                        if not session_locator.is_visible(timeout=2000):
                                            continue

                                        locator_text = ""
                                        try:
                                            locator_text = session_locator.inner_text(timeout=1000) or ""
                                        except Exception:
                                            try:
                                                locator_text = session_locator.text_content(timeout=1000) or ""
                                            except Exception:
                                                locator_text = ""

                                        lowered_text = locator_text.lower()
                                        if any(phrase in lowered_text for phrase in skip_phrases):
                                            preview = locator_text.strip().replace("\n", " ")[:60]
                                            console.print(
                                                f"[dim]      Skipping selector (looks like new session option): {preview}[/dim]"
                                            )
                                            continue

                                        session_locator.click(force=True, timeout=3000)
                                        console.print(f"[green]   ✅ Clicked session (Playwright: {selector})![/green]")
                                        clicked = True
                                        break
                                    except Exception as sel_e:
                                        console.print(f"[dim]      {selector[:30]} failed: {str(sel_e)[:30]}[/dim]")
                                        continue
                        except Exception as e:
                            console.print(f"[yellow]   Playwright error: {str(e)[:60]}[/yellow]")
                    
                    # Strategy 2: JavaScript click (fallback)
                    if not clicked:
                        try:
                            console.print(f"[dim]   Strategy 2: JavaScript with smart search...[/dim]")
                            # Click the session link (prefer account name match)
                            clicked_js = self.driver.execute_script(r"""
                                var accountName = (arguments[0] || '').toLowerCase();
                                console.log('Looking for session link, account:', accountName);

                                function normalize(text) {
                                    return (text || '').replace(/\s+/g, ' ').trim().toLowerCase();
                                }

                                // First try: Find link with account name
                                if (accountName) {
                                    var allLinks = document.querySelectorAll('a');
                                    for (var i = 0; i < allLinks.length; i++) {
                                        var link = allLinks[i];
                                        var text = normalize(link.textContent);
                                        if (!text) {
                                            continue;
                                        }
                                        if (text.includes('new session') || text.includes('start new session') || text.includes('different user') || text.includes('different account')) {
                                            continue;
                                        }
                                        if (text.includes(accountName) && link.href.includes('console')) {
                                            console.log('Found account link:', link.textContent);
                                            link.click();
                                            return 'account-link';
                                        }
                                    }
                                }

                                // Fallback 1: Click first console link (skip new session/different user)
                                var consoleLinks = document.querySelectorAll('a[href*="console"]');
                                console.log('Found', consoleLinks.length, 'console links');
                                if (consoleLinks.length > 0) {
                                    for (var c = 0; c < consoleLinks.length; c++) {
                                        var consoleLink = consoleLinks[c];
                                        var consoleText = normalize(consoleLink.textContent);
                                        if (consoleText && (consoleText.includes('new session') || consoleText.includes('start new session') || consoleText.includes('different user') || consoleText.includes('different account'))) {
                                            console.log('Skipping console link (new/different session):', consoleText);
                                            continue;
                                        }
                                        console.log('Clicking console link candidate');
                                        consoleLink.click();
                                        return 'console-link';
                                    }
                                }

                                // Fallback 2: Click session tiles/buttons (new oauth UI) - prefer existing session
                                var sessionButtons = document.querySelectorAll('[data-testid*="session"], [data-testid*="account-card"], button.awsui-card, a.awsui-card, awsui-card, awsui-card a, awsui-card button, awsui-table-row, awsui-table-row a, awsui-table-row button');
                                console.log('Found', sessionButtons.length, 'session buttons/cards');
                                if (sessionButtons.length > 0) {
                                    var preferredSessionButton = null;
                                    var genericSessionButton = null;

                                    for (var s = 0; s < sessionButtons.length; s++) {
                                        var button = sessionButtons[s];
                                        if (!button) {
                                            continue;
                                        }
                                        var buttonText = normalize(button.textContent);
                                        if (buttonText) {
                                            if (buttonText.includes('new session') || buttonText.includes('start new session') || buttonText.includes('different user') || buttonText.includes('different account')) {
                                                console.log('Skipping session option (new/different):', buttonText);
                                                continue;
                                            }
                                            if (accountName && buttonText.includes(accountName)) {
                                                preferredSessionButton = button;
                                                break;
                                            }
                                            if (!preferredSessionButton && (buttonText.includes('use this session') || buttonText.includes('use existing session') || buttonText.includes('continue with this session') || buttonText.includes('existing session'))) {
                                                preferredSessionButton = button;
                                            }
                                            if (!genericSessionButton) {
                                                genericSessionButton = button;
                                            }
                                        } else if (!genericSessionButton) {
                                            genericSessionButton = button;
                                        }
                                    }

                                    var buttonToClick = preferredSessionButton || genericSessionButton;
                                    if (buttonToClick) {
                                        console.log('Clicking filtered session button/card');
                                        if (typeof buttonToClick.click === 'function') {
                                            buttonToClick.click();
                                            return 'session-tile';
                                        }
                                        var inner = buttonToClick.querySelector('button, a');
                                        if (inner && typeof inner.click === 'function') {
                                            inner.click();
                                            return 'session-tile';
                                        }
                                        var event = new MouseEvent('click', { bubbles: true, cancelable: true, view: window });
                                        buttonToClick.dispatchEvent(event);
                                        return 'session-tile';
                                    }
                                }

                                // Fallback 3: Handle awsui-button shadow DOM ("Sign into new session" layout)
                                var awsuiButtons = document.querySelectorAll('awsui-button');
                                console.log('Found', awsuiButtons.length, 'awsui-button elements');
                                var newSessionCandidate = null;
                                var genericSessionCandidate = null;
                                for (var k = 0; k < awsuiButtons.length; k++) {
                                    var awsui = awsuiButtons[k];
                                    try {
                                        var shadow = awsui.shadowRoot;
                                        var shadowButton = shadow ? shadow.querySelector('button') : null;
                                        if (!shadowButton) {
                                            shadowButton = awsui.querySelector('button');
                                        }
                                        if (!shadowButton) {
                                            continue;
                                        }
                                        var shadowText = normalize(shadowButton.textContent || awsui.textContent || '');
                                        if (shadowText.includes('use this session') || shadowText.includes('use existing session') || shadowText.includes('continue with this session') || shadowText.includes('existing session')) {
                                            console.log('Clicking awsui-button existing session via shadow DOM:', shadowText);
                                            shadowButton.click();
                                            return 'existing-session-button';
                                        }
                                        if (shadowText.includes('sign into new session') || shadowText.includes('start new session')) {
                                            if (!newSessionCandidate) {
                                                newSessionCandidate = shadowButton;
                                                console.log('Captured new session awsui-button candidate:', shadowText);
                                            }
                                            continue;
                                        }
                                        if (!genericSessionCandidate && (shadowText.includes('sign in') || shadowText.includes('continue'))) {
                                            genericSessionCandidate = shadowButton;
                                            console.log('Captured generic awsui-button candidate:', shadowText);
                                        }
                                    } catch (err) {
                                        console.log('awsui-button handling failed:', err);
                                    }
                                }

                                if (genericSessionCandidate) {
                                    console.log('Clicking awsui-button generic session candidate');
                                    genericSessionCandidate.click();
                                    return 'session-button';
                                }
                                if (newSessionCandidate) {
                                    console.log('Clicking awsui-button new session candidate');
                                    newSessionCandidate.click();
                                    return 'new-session-button';
                                }

                                // Fallback 4: Click first primary button with helpful text (prioritize existing session)
                                var primaryButtons = document.querySelectorAll('button, a');
                                var existingPrimary = null;
                                var genericPrimary = null;
                                var newPrimary = null;
                                for (var j = 0; j < primaryButtons.length; j++) {
                                    var btn = primaryButtons[j];
                                    var btnText = normalize(btn.textContent);
                                    if (btnText.includes('different user') || btnText.includes('different account')) {
                                        continue;
                                    }
                                    if (btnText.includes('use this session') || btnText.includes('use existing session') || btnText.includes('continue with this session') || btnText.includes('existing session')) {
                                        existingPrimary = btn;
                                        break;
                                    }
                                    if (btnText.includes('sign into new session') || btnText.includes('start new session')) {
                                        if (!newPrimary) {
                                            newPrimary = btn;
                                        }
                                        continue;
                                    }
                                    if (!genericPrimary && (btnText.includes('sign in') || btnText.includes('continue') || btnText.includes('start session'))) {
                                        genericPrimary = btn;
                                    }
                                }

                                function clickAndReturn(button, label) {
                                    if (button && typeof button.click === 'function') {
                                        console.log('Clicking fallback primary button:', label);
                                        button.click();
                                        return label;
                                    }
                                    return false;
                                }

                                var clickedLabel = null;
                                if (existingPrimary) {
                                    clickedLabel = clickAndReturn(existingPrimary, 'primary-existing-button');
                                    if (clickedLabel) {
                                        return clickedLabel;
                                    }
                                }
                                if (genericPrimary) {
                                    clickedLabel = clickAndReturn(genericPrimary, 'primary-generic-button');
                                    if (clickedLabel) {
                                        return clickedLabel;
                                    }
                                }
                                if (newPrimary) {
                                    clickedLabel = clickAndReturn(newPrimary, 'primary-new-button');
                                    if (clickedLabel) {
                                        return clickedLabel;
                                    }
                                }

                                return false;
                            """, account_name)
                            if clicked_js:
                                clicked = True
                                label_map = {
                                    'account-link': 'account link',
                                    'console-link': 'first console link',
                                    'session-tile': 'session tile/card',
                                    'existing-session-button': 'existing session button',
                                    'session-button': 'session button',
                                    'new-session-button': 'new session button',
                                    'primary-existing-button': 'primary existing session button',
                                    'primary-generic-button': 'primary button',
                                    'primary-new-button': 'primary new session button',
                                }
                                if isinstance(clicked_js, str):
                                    label = label_map.get(clicked_js, clicked_js)
                                    console.print(f"[green]   ✅ Clicked session ({label})![/green]")
                                else:
                                    console.print(f"[green]   ✅ Clicked session (JavaScript)![/green]")
                        except Exception as e:
                            console.print(f"[yellow]   JavaScript failed: {str(e)[:60]}[/yellow]")
                    
                    if clicked:
                        # VERIFY: Wait for console to load (up to 15 seconds)
                        console.print(f"[dim]   Waiting for console to load...[/dim]")
                        for i in range(15):
                            time.sleep(1)
                            try:
                                check_url = self.driver.current_url
                                if 'console.aws.amazon.com' in check_url:
                                    console.print(f"[green]✅ Successfully reached AWS Console![/green]")
                                    return True
                            except:
                                pass
                        
                        # After 15 seconds, check final URL
                        final_url = self.driver.current_url
                        if 'console.aws.amazon.com' in final_url:
                            console.print(f"[green]✅ Reached AWS Console![/green]")
                            return True
                        else:
                            console.print(f"[yellow]⚠️  Clicked session but still on: {final_url}[/yellow]")
                            return False
                    else:
                        console.print(f"[red]❌ Could not auto-click session[/red]")
                        console.print(f"[yellow]⚠️  Please manually click on '{account_name}' session[/yellow]")
                
                # Case 3: On SAML role selection page - DON'T NAVIGATE AWAY!
                # Match with or without region prefix
                if current_url and '/saml' in current_url and 'aws.amazon.com' in current_url:
                    console.print(f"[yellow]🎯 On SAML role selection page - clicking Sign in...[/yellow]")
                    # Try to click the sign-in button (don't navigate away!)
                    if self._click_management_console_button(account_name, requested_role_name=role_name):
                        console.print(f"[green]✅ Successfully signed in![/green]")
                        return True
                    else:
                        console.print(f"[red]❌ Sign in failed - please click manually[/red]")
                        return False
                
                # Case 4: On any other AWS page - don't navigate to SSO!
                if current_url and ('aws.amazon.com' in current_url or 'awsapps.com' in current_url):
                    console.print(f"[yellow]⚠️  Already on AWS page, skipping SSO navigation[/yellow]")
                    # Wait for console to load
                    time.sleep(5)
                    # Check if we reached console
                    final_url = self.driver.current_url
                    if 'console.aws.amazon.com' in final_url:
                        console.print(f"[green]✅ Reached AWS Console![/green]")
                        return True
                    else:
                        console.print(f"[yellow]⚠️  Still on: {final_url}[/yellow]")
                        return False
                        
            except:
                pass
            
            # ONLY navigate to SSO if NOT already on any AWS page
            if not duo_url:
                duo_url = "https://sso-dbbfec7f.sso.duosecurity.com/saml2/sp/DIRGUUDMLYKC10GOCNOR/sso"
            
            console.print(f"[cyan]🔗 Navigating to AWS Duo SSO (fresh auth needed)...[/cyan]")
            if account_name:
                console.print(f"[dim]Target account: {account_name}[/dim]")
            self.driver.get(duo_url)
            time.sleep(3)
            
            current_url = self.driver.current_url
            console.print(f"[dim]Current URL: {current_url}[/dim]")
            
            # Check if authentication needed
            if 'duosecurity.com' in current_url or 'sso' in current_url or 'signin.aws' in current_url:
                console.print("[yellow]⏳ Waiting for Duo authentication (5 min)...[/yellow]")
                console.print("[yellow]   1. Approve Duo push on your phone[/yellow]")
                console.print("[green]   2. ⭐ CHECK 'Trust this browser' ⭐[/green]")
                if account_name:
                    console.print(f"[yellow]   3. Agent will auto-select '{account_name}' account[/yellow]")
                else:
                    console.print("[yellow]   3. Click on AWS account when list appears[/yellow]")
                
                # Wait for AWS console or account selection page
                start_time = time.time()
                account_selected = False
                role_selection_failed = False  # Track if we've already tried and failed
                
                while time.time() - start_time < wait_timeout:
                    try:
                        current_url = self.driver.current_url if self.driver else None
                        
                        if not current_url:
                            console.print("[yellow]⚠️  URL is None, waiting...[/yellow]")
                            time.sleep(2)
                            continue
                    except Exception as e:
                        console.print(f"[yellow]⚠️  Error getting URL: {e}[/yellow]")
                        time.sleep(2)
                        continue
                    
                    # Success - reached AWS Console!
                    if 'console.aws.amazon.com' in current_url:
                        console.print("[green]✅ AWS Console reached![/green]")
                        return True
                    
                    # Account/role selection page detected
                    if ('awsapps.com' in current_url or 'portal.sso' in current_url or 'signin.aws' in current_url) and not account_selected:
                        
                        # Check if this is AWS SAML role selection page (roles already visible)
                        if 'signin.aws' in current_url and 'saml' in current_url:
                            if account_name and not account_selected and not role_selection_failed:
                                # IMPORTANT: On SAML page, roles are already visible
                                # DON'T click account name (it will collapse roles!)
                                # Go DIRECTLY to role selection
                                if self._click_management_console_button(account_name=account_name, requested_role_name=role_name):
                                    account_selected = True
                                    time.sleep(3)
                                else:
                                    # Failed once - don't spam console
                                    console.print("[yellow]⚠️  Role selection failed, please select manually[/yellow]")
                                    role_selection_failed = True  # Mark as failed to prevent retries
                        else:
                            # This is AWS SSO portal page (need to click account to expand)
                            # Try automatic account selection if account_name provided
                            if account_name and not account_selected:
                                if self._select_aws_account(account_name):
                                    account_selected = True
                                    time.sleep(5)  # Wait for role selection page to load
                                    
                                    # After selecting account, look for role selection
                                    if self._click_management_console_button(account_name=account_name, requested_role_name=role_name):
                                        time.sleep(3)
                                    else:
                                        time.sleep(3)
                                else:
                                    console.print(f"[yellow]⚠️  Could not auto-select '{account_name}', please click manually[/yellow]")
                            else:
                                console.print("[yellow]🖱️  Please click on your AWS account![/yellow]")
                    
                    time.sleep(2)
                
                console.print("[red]❌ Duo authentication timeout[/red]")
                return False
            
            # Already authenticated
            if 'console.aws.amazon.com' in current_url:
                console.print("[green]✅ Already authenticated[/green]")
                return True
            
            return False
            
        except Exception as e:
            console.print(f"[red]❌ Duo SSO authentication failed: {e}[/red]")
            return False
    
    def _select_aws_account(self, account_name: str) -> bool:
        """Automatically click on the specified AWS account from the selection page"""
        try:
            # Wait for account selection elements to load
            time.sleep(2)
            
            # Try multiple selectors for AWS account selection
            selectors_to_try = [
                # Look for account name in portal-instance (AWS SSO standard)
                f"//div[contains(@class, 'portal-instance')]//div[contains(text(), '{account_name}')]",
                f"//div[contains(@class, 'saml-account')]//span[contains(text(), '{account_name}')]",
                # Look in any clickable element with account name
                f"//a[contains(text(), '{account_name}')]",
                f"//button[contains(text(), '{account_name}')]",
                f"//div[@role='button'][contains(., '{account_name}')]",
                # Try case-insensitive
                f"//*[contains(translate(text(), 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{account_name.lower()}')]",
            ]
            
            for selector in selectors_to_try:
                try:
                    if self.debug:
                        console.print(f"[dim]Trying selector: {selector[:80]}...[/dim]")
                    element = WebDriverWait(self.driver, 3).until(
                        EC.element_to_be_clickable((By.XPATH, selector))
                    )
                    console.print(f"[green]✓ Found account element[/green]")
                    
                    # Click the element
                    element.click()
                    console.print(f"[green]✓ Clicked on '{account_name}'[/green]")
                    return True
                except Exception as e:
                    if self.debug:
                        console.print(f"[dim]Selector failed: {str(e)[:50]}[/dim]")
                    continue
            
            # If direct click didn't work, try finding the parent clickable element
            try:
                console.print(f"[dim]Looking for account '{account_name}' in page source...[/dim]")
                # Find any element containing the account name
                element = self.driver.find_element(By.XPATH, f"//*[contains(text(), '{account_name}')]")
                # Try to find clickable parent
                parent = element.find_element(By.XPATH, "./ancestor::a | ./ancestor::button | ./ancestor::div[@role='button']")
                parent.click()
                console.print(f"[green]✓ Clicked parent of '{account_name}'[/green]")
                return True
            except:
                pass
            
            console.print(f"[yellow]⚠️  Could not find clickable element for '{account_name}'[/yellow]")
            return False
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Account selection failed: {e}[/yellow]")
            return False

    def _collect_account_roles(self, account_name: Optional[str] = None) -> List[Dict[str, str]]:
        """Gather available roles for the specified account on the SAML page."""
        try:
            target = (account_name or "").lower()
            roles = self.driver.execute_script(
                """
                const accountFilter = arguments[0];
                const radios = Array.from(document.querySelectorAll('input[type="radio"][name="roleIndex"]'));
                const matches = [];
                radios.forEach((radio) => {
                    let container = radio.parentElement;
                    let guard = 0;
                    let accountText = '';
                    while (container && guard < 15) {
                        const text = (container.textContent || '').trim();
                        if (text.includes('Account:')) {
                            accountText = text.replace(/\\s+/g, ' ').trim();
                            break;
                        }
                        container = container.parentElement;
                        guard += 1;
                    }
                    if (!accountText) {
                        return;
                    }
                    const accountLower = accountText.toLowerCase();
                    if (accountFilter && accountLower.indexOf(accountFilter) === -1) {
                        return;
                    }
                    let roleName = '';
                    const label = document.querySelector('label[for=\"' + radio.id + '\"]');
                    if (label) {
                        roleName = label.textContent.trim();
                    } else if (radio.parentElement) {
                        roleName = (radio.parentElement.textContent || '').trim().split('\\n')[0];
                    }
                    matches.push({
                        radioId: radio.id || '',
                        roleName: roleName || '',
                        accountText: accountText
                    });
                });
                return matches;
                """,
                target
            )
            return roles or []
        except Exception as exc:
            console.print(f"[yellow]⚠️  Unable to collect roles: {exc}[/yellow]")
            return []

    def _prompt_for_role_choice(
        self,
        account_name: str,
        roles: List[Dict[str, str]],
        suggested_index: int
    ) -> Dict[str, str]:
        """Prompt the user to choose a role when multiple options exist."""
        if not roles:
            return {}
        
        console.print(f"\n[bold yellow]🔐 Multiple roles available for '{account_name}'[/bold yellow]")
        for idx, entry in enumerate(roles, start=1):
            label = entry.get("roleName") or f"Role {idx}"
            marker = "📖 [SUGGESTED]" if idx - 1 == suggested_index else ""
            console.print(f"  {idx}. {label} {marker}")
        
        default_desc = roles[suggested_index].get("roleName") or f"Role {suggested_index + 1}"
        console.print(f"\n[cyan]💡 Default: {suggested_index + 1} ({default_desc})[/cyan]")
        
        while True:
            from rich.prompt import Prompt
            choice = Prompt.ask(
                f"\n[bold]Which role should I use for {account_name}?[/bold] (1-{len(roles)} or press Enter for default)",
                default=str(suggested_index + 1)
            ).strip()
            
            if not choice:
                selected = roles[suggested_index]
                console.print(f"[green]✅ Using default role: {selected.get('roleName')}[/green]")
                return selected
            
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(roles):
                    selected = roles[idx]
                    console.print(f"[green]✅ Selected role: {selected.get('roleName')}[/green]")
                    return selected
            else:
                # Partial name match
                lowered = choice.lower()
                for entry in roles:
                    name = (entry.get("roleName") or "").lower()
                    if lowered and lowered in name:
                        console.print(f"[green]✅ Matched role: {entry.get('roleName')}[/green]")
                        return entry
            
            console.print("[yellow]⚠️  Invalid selection. Please enter a number (1-{len(roles)}) or part of the role name.[/yellow]")

    def _choose_role_entry(
        self,
        account_name: str,
        roles: List[Dict[str, str]],
        requested_role_name: Optional[str] = None
    ) -> Optional[Dict[str, str]]:
        """Determine which role entry to use, preferring requested/read-only roles."""
        if not roles:
            console.print("[red]❌ No roles available for selection[/red]")
            return None
        
        # Single role available - use it immediately
        if len(roles) == 1:
            only_role = roles[0].get("roleName") or "Role"
            console.print(f"[cyan]🎯 Single role available: '{only_role}' - selecting automatically[/cyan]")
            return roles[0]
        
        def find_match(name: Optional[str]) -> Optional[Dict[str, str]]:
            if not name:
                return None
            target = name.lower()
            for entry in roles:
                role_name = (entry.get("roleName") or "").lower()
                if target in role_name:
                    return entry
            return None
        
        if requested_role_name:
            match = find_match(requested_role_name)
            if match:
                console.print(f"[cyan]🎯 Using requested role '{match.get('roleName')}'[/cyan]")
                return match
            console.print(
                f"[yellow]⚠️  Requested role '{requested_role_name}' not found for {account_name}. Showing options...[/yellow]"
            )
        
        # Multiple roles - detect read-only and prompt user
        read_only_keywords = ("read", "view", "ro", "readonly", "read-only", "read_only")
        suggested_index = 0
        for idx, entry in enumerate(roles):
            role_lower = (entry.get("roleName") or "").lower()
            # Check if role name contains read-only indicators
            if any(keyword in role_lower for keyword in read_only_keywords):
                suggested_index = idx
                console.print(f"[cyan]📖 Detected read-only role: '{entry.get('roleName')}' - suggesting as default[/cyan]")
                break
        
        # Always prompt when multiple roles exist
        return self._prompt_for_role_choice(account_name, roles, suggested_index)

    def _select_role_entry(self, role_entry: Dict[str, str]) -> bool:
        """Click the radio button associated with the chosen role."""
        radio_id = role_entry.get("radioId")
        role_label = role_entry.get("roleName") or "selected role"
        
        console.print(f"[cyan]🎯 Selecting role: {role_label}[/cyan]")
        
        # Strategy 1: Click by radio ID
        if radio_id:
            try:
                radio_elem = self.driver.find_element(By.ID, radio_id)
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", radio_elem)
                time.sleep(0.3)
                radio_elem.click()
                time.sleep(0.5)
                
                # Verify it's checked
                if radio_elem.is_selected():
                    console.print(f"[green]✅ Role radio button selected: {role_label}[/green]")
                    return True
                else:
                    console.print(f"[yellow]⚠️  Radio not checked after click, trying label...[/yellow]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Radio click by ID failed: {str(e)[:60]}[/yellow]")
        
        # Strategy 2: Click via label
        try:
            label = self.driver.find_element(
                By.XPATH,
                f"//label[contains(normalize-space(.), '{role_label}')]"
            )
            self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", label)
            time.sleep(0.3)
            label.click()
            time.sleep(0.5)
            console.print(f"[green]✅ Role selected via label: {role_label}[/green]")
            return True
        except Exception as e:
            console.print(f"[yellow]⚠️  Label click failed: {str(e)[:60]}[/yellow]")
        
        # Strategy 3: JavaScript force-click
        if radio_id:
            try:
                clicked = self.driver.execute_script("""
                    const radio = document.getElementById(arguments[0]);
                    if (radio) {
                        radio.checked = true;
                        radio.click();
                        const event = new Event('change', { bubbles: true });
                        radio.dispatchEvent(event);
                        return radio.checked;
                    }
                    return false;
                """, radio_id)
                
                if clicked:
                    console.print(f"[green]✅ Role selected via JavaScript: {role_label}[/green]")
                    return True
            except Exception as e:
                console.print(f"[yellow]⚠️  JavaScript force-click failed: {str(e)[:60]}[/yellow]")
        
        console.print(f"[red]❌ Could not select role '{role_label}' - all strategies failed[/red]")
        return False
    
    def _click_management_console_button(
        self,
        account_name: str = None,
        requested_role_name: Optional[str] = None
    ) -> bool:
        """After account selection, click on role radio button and submit for AWS SAML signin"""
        try:
            # Safety check: Ensure driver and URL exist
            if not self.driver:
                console.print("[red]❌ Driver not initialized[/red]")
                return False
            
            current_url = self.driver.current_url
            
            # Safety check: Ensure current_url is not None
            if not current_url:
                console.print("[yellow]⚠️  Current URL is None, waiting for page load...[/yellow]")
                time.sleep(2)
                current_url = self.driver.current_url
                if not current_url:
                    console.print("[red]❌ Could not get current URL[/red]")
                    return False
            
            # Check if we're on AWS SAML role selection page (signin.aws.amazon.com/saml)
            if 'signin.aws' in current_url and 'saml' in current_url:
                roles = self._collect_account_roles(account_name)
                if not roles:
                    console.print("[red]❌ No radio buttons detected on the SAML role selection page[/red]")
                    return False
                
                chosen_entry = self._choose_role_entry(
                    account_name or "selected account",
                    roles,
                    requested_role_name=requested_role_name
                )
                if not chosen_entry:
                    console.print("[red]❌ Role selection aborted[/red]")
                    return False
                
                if not self._select_role_entry(chosen_entry):
                    return False
                
                self.last_role_selected = chosen_entry.get("roleName")
                role_name = chosen_entry.get("roleName", "Unknown")
                radio_id = chosen_entry.get("radioId", "")
                result = {"success": True, "role": role_name, "radioId": radio_id, "account": account_name}

                # CRITICAL: Verify radio is actually checked using Python
                time.sleep(1)
                try:
                    if radio_id:
                        radio_elem = self.driver.find_element(By.ID, radio_id)
                        if not radio_elem.is_selected():
                            radio_elem.click()
                            time.sleep(0.5)
                            if not radio_elem.is_selected():
                                try:
                                    label = self.driver.find_element(By.XPATH, f"//label[@for='{radio_id}']")
                                    label.click()
                                    time.sleep(0.5)
                                except Exception:
                                    pass
                except Exception:
                    pass
                
                time.sleep(1)
                
                console.print("[bold cyan]Clicking Sign in button...[/bold cyan]")
                
                # STRATEGY 0: Wait for page to fully load AND prepare page
                try:
                    console.print("[dim]⏳ Waiting for page to fully load...[/dim]")
                    
                    # Wait for Sign in button to appear (up to 10 seconds)
                    button_found = False
                    for i in range(10):
                        button_count = self.driver.execute_script("""
                            var buttons = document.querySelectorAll('button, input[type="submit"]');
                            return buttons.length;
                        """)
                        if button_count > 0:
                            console.print(f"[dim]   ✅ Found {button_count} buttons on page[/dim]")
                            button_found = True
                            break
                        time.sleep(1)
                    
                    if not button_found:
                        console.print("[yellow]   ⚠️  No buttons found, but continuing anyway...[/yellow]")
                    
                    # Now prepare the page
                    console.print("[dim]🧹 Preparing page (removing overlays, enabling buttons)...[/dim]")
                    self.driver.execute_script("""
                        // Remove ALL overlays and modals
                        var overlays = document.querySelectorAll('[class*="overlay"], [class*="modal"], [class*="backdrop"]');
                        overlays.forEach(el => el.remove());
                        
                        // Force enable ALL buttons
                        var buttons = document.querySelectorAll('button, input[type="submit"]');
                        console.log('Preparing', buttons.length, 'buttons');
                        buttons.forEach(btn => {
                            btn.disabled = false;
                            btn.removeAttribute('disabled');
                            btn.style.pointerEvents = 'auto';
                            btn.style.opacity = '1';
                        });
                        
                        // Scroll to bottom
                        window.scrollTo({top: document.body.scrollHeight, behavior: 'smooth'});
                        
                        console.log('Page prepared for sign-in button click');
                    """)
                    time.sleep(2)  # Give time for scroll animation
                except Exception as e:
                    console.print(f"[dim]   Page prep skipped: {str(e)[:40]}[/dim]")
                
                # Strategy 0.5: Directly submit the AWS SAML form before other fallbacks
                if self._force_saml_sign_in_direct():
                    # Wait for navigation to AWS Console
                    console.print("[dim]⏳ Waiting for AWS Console to load...[/dim]")
                    for wait_attempt in range(15):  # 15 seconds max
                        time.sleep(1)
                        try:
                            current_url = self.driver.current_url
                            if 'console.aws.amazon.com' in current_url:
                                console.print("[green]✅ AWS Console reached![/green]")
                                return True
                        except:
                            pass
                    console.print("[yellow]⚠️  Console didn't load after sign-in, continuing...[/yellow]")
                    return True
                
                # Strategy 1: PLAYWRIGHT click with WAIT (get CURRENT page!)
                page = self._get_current_playwright_page()
                if page:
                    try:
                        console.print("[dim]🎭 Strategy 1: Playwright with wait states...[/dim]")
                        
                        # Scroll with Playwright
                        try:
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(0.8)
                        except:
                            pass
                        
                        # Most specific selectors first (AWS SAML page)
                        sign_in_selectors = [
                            # AWS specific
                            'button[type="submit"]:has-text("Sign in")',
                            'button:has-text("Sign in"):visible',
                            'input[type="submit"][value="Sign in"]',
                            
                            # Generic submit buttons
                            'button[type="submit"]:visible',
                            'input[type="submit"]:visible',
                            'button:has-text("Sign"):visible',
                            
                            # By ID/class
                            '#signin_button',
                            'button[id*="signin"]',
                            'button[name*="signin"]',
                            '.awsui-button-variant-primary:visible'
                        ]
                        
                        for selector in sign_in_selectors:
                            try:
                                console.print(f"[dim]   Trying: {selector}[/dim]")
                                locator = page.locator(selector).first
                                
                                # Wait for it to be attached and visible
                                locator.wait_for(state="attached", timeout=3000)
                                
                                if locator.is_visible(timeout=2000):
                                    # Scroll into view
                                    locator.scroll_into_view_if_needed(timeout=2000)
                                    time.sleep(0.3)
                                    
                                    # Click with force
                                    console.print(f"[dim]   Clicking: {selector}[/dim]")
                                    locator.click(timeout=5000, force=True, no_wait_after=False)
                                    
                                    console.print(f"[green]✅ SIGNED IN! (Playwright: {selector})[/green]")
                                    time.sleep(3)
                                    
                                    # Verify navigation
                                    final_url = page.url
                                    if 'console.aws.amazon.com' in final_url:
                                        console.print(f"[green]✅ Verified: Reached AWS Console![/green]")
                                    return True
                            except Exception as e:
                                console.print(f"[dim]   {selector[:40]} → {str(e)[:40]}[/dim]")
                                continue
                        
                        console.print("[yellow]   Playwright: All selectors failed[/yellow]")
                    except Exception as e:
                        console.print(f"[yellow]   Playwright error: {str(e)[:60]}[/yellow]")
                else:
                    console.print("[yellow]   Playwright: No active page available[/yellow]")
                
                # Strategy 2: AGGRESSIVE JavaScript (will find ANY button!)
                console.print("[dim]🔥 Strategy 2: Aggressive JavaScript...[/dim]")
                
                submit_result = self.driver.execute_script("""
                    console.log('=== AGGRESSIVE JAVASCRIPT SIGN-IN FINDER ===');
                    
                    // Find ALL buttons
                    var allButtons = document.querySelectorAll('button, input[type="submit"], input[type="button"], a[role="button"]');
                    console.log('Total buttons found:', allButtons.length);
                    
                    // Try each button
                    for (var i = 0; i < allButtons.length; i++) {
                        var btn = allButtons[i];
                        var text = (btn.textContent || btn.value || btn.innerText || '').toLowerCase().trim();
                        var id = (btn.id || '').toLowerCase();
                        var className = (btn.className || '').toLowerCase();
                        
                        console.log('Button', i, ':', text, 'id:', id, 'class:', className);
                        
                        // Check if it's a sign-in button
                        if (text.includes('sign') || id.includes('sign') || className.includes('submit') || 
                            btn.type === 'submit' || text === 'sign in') {
                            
                            console.log('>>> FOUND SIGN-IN BUTTON:', text);
                            
                            // Force enable
                            btn.disabled = false;
                            btn.removeAttribute('disabled');
                            btn.style.pointerEvents = 'auto';
                            
                            // Scroll into view
                            btn.scrollIntoView({behavior: 'instant', block: 'center'});
                            
                            // Try multiple click strategies
                            try {
                                btn.click();
                                console.log('>>> SUCCESS: Direct click worked!');
                                return {success: true, method: 'direct_click', button: text};
                            } catch(e1) {
                                console.log('Direct click failed:', e1.message);
                            }
                            
                            try {
                                var evt = new MouseEvent('click', {bubbles: true, cancelable: true, view: window});
                                btn.dispatchEvent(evt);
                                console.log('>>> SUCCESS: MouseEvent worked!');
                                return {success: true, method: 'mouseevent', button: text};
                            } catch(e2) {
                                console.log('MouseEvent failed:', e2.message);
                            }
                            
                            try {
                                var form = btn.closest('form');
                                if (form) {
                                    form.submit();
                                    console.log('>>> SUCCESS: Form submit worked!');
                                    return {success: true, method: 'form_submit', button: text};
                                }
                            } catch(e3) {
                                console.log('Form submit failed:', e3.message);
                            }
                        }
                    }
                    
                    console.log('ERROR: No sign-in button could be clicked');
                    return {success: false, checked: allButtons.length};
                """)
                
                if submit_result and submit_result.get('success'):
                    method = submit_result.get('method', 'unknown')
                    console.print(f"[green]✅ Signed in (JavaScript {method})![/green]")
                    time.sleep(3)
                    return True
                else:
                    checked = submit_result.get('checked', 0) if submit_result else 0
                    console.print(f"[yellow]   JavaScript: Checked {checked} buttons, none worked[/yellow]")
                
                # Strategy 3: Selenium WebDriverWait
                console.print("[dim]🔧 Strategy 3: Selenium WebDriverWait...[/dim]")
                
                selectors = [
                    (By.XPATH, "//button[contains(translate(text(), 'SIGN', 'sign'), 'sign')]"),
                    (By.XPATH, "//input[@type='submit' and contains(@value, 'Sign')]"),
                    (By.XPATH, "//button[@type='submit']"),
                    (By.XPATH, "//input[@type='submit']"),
                    (By.CSS_SELECTOR, "button[type='submit']"),
                    (By.CSS_SELECTOR, "input[type='submit']"),
                ]
                
                for by, selector in selectors:
                    try:
                        submit_btn = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((by, selector))
                        )
                        # Scroll into view
                        self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", submit_btn)
                        time.sleep(0.5)
                        # Force click with JavaScript
                        self.driver.execute_script("arguments[0].click();", submit_btn)
                        console.print(f"[green]✅ Signed in (Selenium: {selector})![/green]")
                        time.sleep(3)
                        return True
                    except:
                        continue
                
                console.print("[red]❌ ALL STRATEGIES FAILED! Could not click Sign in button[/red]")
                console.print("[yellow]⚠️  Please click Sign in button manually[/yellow]")
                return False
            
            # If not SAML page, try original logic for portal-style pages
            # AWS SSO portal style (not SAML)
            button_texts = [
                "Management console",
                "Console",
                "management-console",
                "Access portal",
            ]
            
            for button_text in button_texts:
                selectors = [
                    f"//div[contains(@class, 'portal-instance')]//a[contains(text(), '{button_text}')]",
                    f"//a[contains(text(), '{button_text}')]",
                ]
                
                for selector in selectors:
                    try:
                        element = WebDriverWait(self.driver, 2).until(
                            EC.element_to_be_clickable((By.XPATH, selector))
                        )
                        element.click()
                        console.print(f"[green]✓ Clicked {button_text}[/green]")
                        return True
                    except:
                        continue
            
            return False
        
        except Exception as e:
            # Silently fail - error will be shown once by caller
            return False

    def _force_saml_sign_in_direct(self) -> bool:
        """Force-click or submit the AWS SAML Sign in button when Selenium struggles."""
        if not self.driver:
            return False
        
        try:
            current_url = self.driver.current_url or ""
        except Exception:
            current_url = ""
        
        if "signin.aws" not in current_url:
            return False
        
        try:
            result = self.driver.execute_script("""
                return (function () {
                    const response = {success: false, method: null, reason: null};
                    const forms = Array.from(document.querySelectorAll('form'));
                    const formCandidates = [
                        document.querySelector('#saml_form'),
                        document.querySelector('form[action*="saml"]'),
                        document.querySelector('form[action*="signin"]')
                    ].filter(Boolean);
                    if (forms.length) {
                        formCandidates.push(forms.find(f => {
                            const id = (f.id || '').toLowerCase();
                            return id.includes('saml');
                        }));
                    }
                    const targetForm = formCandidates.find(Boolean) || forms[0] || null;
                    
                    if (!targetForm) {
                        response.reason = 'no-form';
                        return response;
                    }
                    
                    const selectors = [
                        '#signin_button',
                        'form#saml_form button[type="submit"]',
                        'form#saml_form input[type="submit"]',
                        'button.awsui-button-variant-primary',
                        'button[type="submit"]',
                        'input[type="submit"]'
                    ];
                    
                    for (const selector of selectors) {
                        const btn = targetForm.querySelector(selector) || document.querySelector(selector);
                        if (!btn) continue;
                        
                        btn.disabled = false;
                        btn.removeAttribute('disabled');
                        btn.style.pointerEvents = 'auto';
                        btn.style.opacity = '1';
                        
                        try { btn.scrollIntoView({behavior: 'instant', block: 'center'}); } catch (err) {}
                        
                        try {
                            btn.click();
                            response.success = true;
                            response.method = 'click:' + selector;
                            return response;
                        } catch (err) {
                            try {
                                const evt = new MouseEvent('click', {view: window, bubbles: true, cancelable: true});
                                btn.dispatchEvent(evt);
                                response.success = true;
                                response.method = 'dispatch:' + selector;
                                return response;
                            } catch (err2) {
                                continue;
                            }
                        }
                    }
                    
                    try {
                        targetForm.submit();
                        response.success = true;
                        response.method = 'form.submit';
                        return response;
                    } catch (err3) {
                        response.reason = err3.message || 'form-submit-failed';
                        return response;
                    }
                })();
            """)
            
            if result and result.get("success"):
                console.print(f"[green]   ✅ Triggered Sign in via {result.get('method')}[/green]")
                return True
            else:
                detail = result.get("reason") if result else "no-result"
                console.print(f"[dim]   Direct SAML submit failed ({detail})[/dim]")
        except Exception as e:
            console.print(f"[dim]   Direct SAML submit error: {str(e)[:60]}[/dim]")
        
        # Selenium fallbacks (ActionChains + keyboard)
        sign_in_locators = [
            (By.ID, "signin_button"),
            (By.CSS_SELECTOR, "form#saml_form button[type='submit']"),
            (By.CSS_SELECTOR, "form#saml_form input[type='submit']"),
            (By.CSS_SELECTOR, "button.awsui-button-variant-primary"),
            (By.XPATH, "//button[contains(translate(., 'SIGNIN', 'signin'), 'sign in')]"),
            (By.XPATH, "//input[@type='submit' and contains(translate(@value, 'SIGNIN', 'signin'), 'sign in')]"),
        ]
        
        for by, locator in sign_in_locators:
            try:
                btn = self.driver.find_element(by, locator)
            except Exception:
                continue
            
            try:
                self.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", btn)
            except Exception:
                pass
            time.sleep(0.2)
            
            for strategy in ("direct", "actions", "keyboard"):
                try:
                    if strategy == "direct":
                        btn.click()
                    elif strategy == "actions":
                        ActionChains(self.driver).move_to_element(btn).pause(0.1).click(btn).perform()
                    else:
                        btn.send_keys(Keys.SPACE)
                        time.sleep(0.1)
                        btn.send_keys(Keys.ENTER)
                    console.print(f"[green]   ✅ Sign in triggered ({locator} | {strategy})[/green]")
                    return True
                except Exception:
                    continue
        
        # Final fallback: send ENTER to body
        try:
            body = self.driver.find_element(By.TAG_NAME, "body")
            body.send_keys(Keys.END)
            time.sleep(0.1)
            body.send_keys(Keys.ENTER)
            console.print("[green]   ✅ Sign in triggered via ENTER key[/green]")
            return True
        except Exception:
            return False
    
    # ==================== AWS SSO / PROFILE HANDLING ====================
    def ensure_aws_profile(self, account_identifier: str = None, role_name: str = None, max_steps: int = 2) -> bool:
        """Ensure we are inside an AWS console session for the desired account / role.

        Tries to automatically select the correct AWS SSO account + role tiles on the start
        portal if we are still at the AWS SSO page (portal.awsapps.com) or the account chooser.

        Heuristics only (no credentials). Safe to call repeatedly; it will no-op once a
        console URL (console.aws.amazon.com) is detected.
        """
        try:
            if not self.driver:
                return False
            current = self.driver.current_url or ""
            if any(host in current for host in ["console.aws.amazon.com", "signin.aws.amazon.com"]):
                # Already in console or classic signin (can't automate creds)
                return True
            if not any(host in current for host in ["awsapps.com", "portal.aws"]):
                return True  # Not on SSO start page

            console.print("[cyan]🔐 AWS SSO portal detected – attempting automatic account/role selection...[/cyan]")

            # Helper JS to collect clickable tiles (accounts / roles / console launch buttons)
            js_collect = """
                const results = [];
                const clickable = document.querySelectorAll('a,button,div[role="button"],div[data-testid],span');
                for (const el of clickable) {
                    const txt = (el.innerText||'').trim();
                    if (!txt) continue;
                    if (txt.length > 200) continue;
                    results.push({text: txt, tag: el.tagName, classes: el.className});
                }
                return results.slice(0,400);
            """
            tiles = self.driver.execute_script(js_collect) or []
            acct_lower = (account_identifier or "").lower()
            role_lower = (role_name or "").lower()

            def find_match(predicates):
                for t in tiles:
                    text_l = t['text'].lower()
                    if all(p(text_l) for p in predicates):
                        return t['text']
                return None

            target_text = None
            # Prefer combined account + role line
            if account_identifier and role_name:
                target_text = find_match([
                    lambda s: acct_lower in s,
                    lambda s: role_lower in s
                ])
            if not target_text and account_identifier:
                target_text = find_match([lambda s: acct_lower in s])
            if not target_text and role_name:
                target_text = find_match([lambda s: role_lower in s])

            if target_text:
                console.print(f"[cyan]🧭 Selecting tile containing: '{target_text[:60]}'[/cyan]")
                # Click via XPath contains to avoid dynamic IDs
                try:
                    self.click_element(f"//*[contains(normalize-space(.), '{target_text[:60]}')][1]", ClickStrategy.JAVASCRIPT, description="AWS SSO tile", wait_before=False)
                    time.sleep(2)
                except Exception as e:
                    console.print(f"[yellow]⚠️  Failed initial tile click: {e}" )

            # Look for Management console / Console link
            launch_selectors = [
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'management console')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'management console')]",
                "//a[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'console')]",
                "//button[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'),'console')]",
            ]
            for sel in launch_selectors:
                try:
                    if self.click_element(sel, ClickStrategy.JAVASCRIPT, description="Launch console", wait_before=False):
                        time.sleep(4)
                        break
                except:
                    pass

            # Wait for console domain
            for _ in range(10):
                if "console.aws.amazon.com" in (self.driver.current_url or ""):
                    console.print("[green]✅ AWS console session established[/green]")
                    return True
                time.sleep(1)

            console.print("[yellow]⚠️  Could not confirm console session (may already be authenticated or manual step needed)" )
            return False
        except Exception as e:
            console.print(f"[yellow]⚠️  AWS profile selection heuristic failed: {e}")
            return False

    # ==================== WAIT STRATEGIES ====================
    
    def wait_for(self, condition: WaitCondition, **kwargs) -> bool:
        """
        Wait for various conditions with intelligent timeouts
        
        Args:
            condition: Type of condition to wait for
            **kwargs: Condition-specific parameters (selector, text, url, etc.)
        """
        try:
            if condition == WaitCondition.PRESENCE:
                selector = kwargs.get('selector')
                by = self._parse_selector_type(selector)
                console.print(f"[cyan]⏳ Waiting for element presence: {selector}[/cyan]")
                self.wait.until(EC.presence_of_element_located((by, selector)))
                console.print(f"[green]✅ Element found[/green]")
                return True
            
            elif condition == WaitCondition.VISIBILITY:
                selector = kwargs.get('selector')
                by = self._parse_selector_type(selector)
                console.print(f"[cyan]⏳ Waiting for visibility: {selector}[/cyan]")
                self.wait.until(EC.visibility_of_element_located((by, selector)))
                console.print(f"[green]✅ Element visible[/green]")
                return True
            
            elif condition == WaitCondition.CLICKABILITY:
                selector = kwargs.get('selector')
                by = self._parse_selector_type(selector)
                console.print(f"[cyan]⏳ Waiting for clickability: {selector}[/cyan]")
                self.wait.until(EC.element_to_be_clickable((by, selector)))
                console.print(f"[green]✅ Element clickable[/green]")
                return True
            
            elif condition == WaitCondition.TEXT:
                text = kwargs.get('text')
                console.print(f"[cyan]⏳ Waiting for text: '{text}'[/cyan]")
                self.wait.until(EC.presence_of_element_located((
                    By.XPATH, f"//*[contains(text(), '{text}')]"
                )))
                console.print(f"[green]✅ Text found[/green]")
                return True
            
            elif condition == WaitCondition.URL_CONTAINS:
                url_part = kwargs.get('url_part')
                console.print(f"[cyan]⏳ Waiting for URL containing: {url_part}[/cyan]")
                self.wait.until(EC.url_contains(url_part))
                console.print(f"[green]✅ URL contains target[/green]")
                return True
            
            elif condition == WaitCondition.URL_CHANGES:
                old_url = kwargs.get('old_url', self.driver.current_url)
                console.print(f"[cyan]⏳ Waiting for URL change...[/cyan]")
                self.wait.until(EC.url_changes(old_url))
                console.print(f"[green]✅ URL changed[/green]")
                return True
            
            elif condition == WaitCondition.ELEMENT_GONE:
                selector = kwargs.get('selector')
                by = self._parse_selector_type(selector)
                console.print(f"[cyan]⏳ Waiting for element to disappear: {selector}[/cyan]")
                self.wait.until(EC.invisibility_of_element_located((by, selector)))
                console.print(f"[green]✅ Element disappeared[/green]")
                return True
            
            return False
            
        except TimeoutException:
            console.print(f"[yellow]⚠️  Timeout waiting for {condition.value}[/yellow]")
            return False
        except Exception as e:
            console.print(f"[yellow]⚠️  Wait failed: {e}[/yellow]")
            return False
    
    # ==================== CLICK STRATEGIES ====================
    
    def click_element(self, selector: str, strategy: ClickStrategy = ClickStrategy.DIRECT,
                     description: str = "element", wait_before: bool = True) -> bool:
        """
        Click element using multiple strategies
        Falls back through strategies if one fails
        """
        strategies = [strategy]  # Primary strategy
        
        # Add fallback strategies
        if strategy != ClickStrategy.JAVASCRIPT:
            strategies.append(ClickStrategy.JAVASCRIPT)
        if strategy != ClickStrategy.ACTION_CHAIN:
            strategies.append(ClickStrategy.ACTION_CHAIN)
        if strategy != ClickStrategy.FOCUS_AND_ENTER:
            strategies.append(ClickStrategy.FOCUS_AND_ENTER)
        
        for strat in strategies:
            if self._click_with_strategy(selector, strat, description, wait_before):
                self.click_history.append({
                    'selector': selector,
                    'strategy': strat.value,
                    'timestamp': datetime.now().isoformat()
                })
                return True
        
        console.print(f"[red]❌ All click strategies failed for: {description}[/red]")
        return False
    
    def _click_with_strategy(self, selector: str, strategy: ClickStrategy, 
                           description: str, wait_before: bool) -> bool:
        """Execute click with specific strategy"""
        try:
            by = self._parse_selector_type(selector)
            
            # Wait for element if requested
            if wait_before:
                try:
                    element = self.wait.until(EC.presence_of_element_located((by, selector)))
                except TimeoutException:
                    console.print(f"[yellow]   ⚠️  Element not found: {description}[/yellow]")
                    return False
            else:
                try:
                    element = self.driver.find_element(by, selector)
                except NoSuchElementException:
                    console.print(f"[yellow]   ⚠️  Element not found: {description}[/yellow]")
                    return False
            
            # Scroll into view
            self.driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.3)
            
            if strategy == ClickStrategy.DIRECT:
                console.print(f"[cyan]   🖱️  Clicking {description} (direct)...[/cyan]")
                element.click()
                
            elif strategy == ClickStrategy.JAVASCRIPT:
                console.print(f"[cyan]   🖱️  Clicking {description} (JavaScript)...[/cyan]")
                self.driver.execute_script("arguments[0].click();", element)
                
            elif strategy == ClickStrategy.ACTION_CHAIN:
                console.print(f"[cyan]   🖱️  Clicking {description} (ActionChains)...[/cyan]")
                ActionChains(self.driver).move_to_element(element).click().perform()
                
            elif strategy == ClickStrategy.FOCUS_AND_ENTER:
                console.print(f"[cyan]   🖱️  Clicking {description} (Focus+Enter)...[/cyan]")
                self.driver.execute_script("arguments[0].focus();", element)
                element.send_keys(Keys.ENTER)
                
            elif strategy == ClickStrategy.JAVASCRIPT_DOUBLE_CLICK:
                console.print(f"[cyan]   🖱️  Double-clicking {description} (JavaScript)...[/cyan]")
                self.driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('dblclick'));", element)
            
            time.sleep(0.5)
            console.print(f"[green]   ✅ Clicked {description}[/green]")
            return True
            
        except StaleElementReferenceException:
            console.print(f"[yellow]   ⚠️  Element became stale: {description}[/yellow]")
            return False
        except ElementClickInterceptedException:
            console.print(f"[yellow]   ⚠️  Element click intercepted: {description}[/yellow]")
            return False
        except Exception as e:
            console.print(f"[yellow]   ⚠️  Click failed with {strategy.value}: {e}[/yellow]")
            return False
    
    # ==================== FIND & SEARCH STRATEGIES ====================
    
    def find_element_intelligent(self, text_to_find: str, 
                                element_types: List[str] = None) -> Optional[Tuple[By, str]]:
        """
        Intelligently find element by text using multiple strategies
        Returns (By, selector) tuple if found, None otherwise
        """
        if element_types is None:
            element_types = ['a', 'button', 'div', 'span', 'li', 'tr', 'td', 'h1', 'h2', 'h3']
        
        console.print(f"[cyan]🔍 Searching for: '{text_to_find}'[/cyan]")
        
        # Strategy 1: Exact text match on various elements
        for elem_type in element_types:
            selector = f"//{elem_type}[text()='{text_to_find}']"
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    console.print(f"[green]✅ Found (exact match in <{elem_type}>)[/green]")
                    return (By.XPATH, selector)
            except:
                pass
        
        # Strategy 2: Contains text (case-insensitive)
        for elem_type in element_types:
            selector = f"//{elem_type}[contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{text_to_find.lower()}')]"
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    console.print(f"[green]✅ Found (case-insensitive in <{elem_type}>)[/green]")
                    return (By.XPATH, selector)
            except:
                pass
        
        # Strategy 3: Parent element contains text
        selector = f"//*[contains(text(), '{text_to_find}')]"
        try:
            element = self.driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                console.print(f"[green]✅ Found (parent contains text)[/green]")
                return (By.XPATH, selector)
        except:
            pass
        
        # Strategy 4: Table row contains text
        selector = f"//tr[contains(., '{text_to_find}')]"
        try:
            element = self.driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                console.print(f"[green]✅ Found (table row)[/green]")
                return (By.XPATH, selector)
        except:
            pass
        
        # Strategy 5: Data attributes
        selector = f"//*[contains(@data-id, '{text_to_find}') or contains(@id, '{text_to_find}') or contains(@name, '{text_to_find}')]"
        try:
            element = self.driver.find_element(By.XPATH, selector)
            if element.is_displayed():
                console.print(f"[green]✅ Found (data attribute)[/green]")
                return (By.XPATH, selector)
        except:
            pass
        
        console.print(f"[yellow]⚠️  Could not find: '{text_to_find}'[/yellow]")
        return None
    
    def find_table_row_by_text(self, text_to_find: str) -> Optional[Tuple[By, str]]:
        """Find and return selector for table row containing text"""
        console.print(f"[cyan]🔍 Searching table for: '{text_to_find}'[/cyan]")
        
        # Use JavaScript for more efficient search
        javascript = f"""
        var rows = document.querySelectorAll('tbody tr, tr[role="row"], [role="row"]');
        for (let row of rows) {{
            if (row.textContent.includes('{text_to_find}')) {{
                return 'found';
            }}
        }}
        return 'not_found';
        """
        
        result = self.driver.execute_script(javascript)
        if result == 'found':
            console.print(f"[green]✅ Found table row[/green]")
            return (By.XPATH, f"//tr[contains(., '{text_to_find}')]")
        
        console.print(f"[yellow]⚠️  Table row not found[/yellow]")
        return None
    
    def find_clickable_element_with_text(self, text_to_find: str) -> Optional[Tuple[By, str]]:
        """Find clickable element (link, button) with specific text"""
        selectors = [
            f"//a[contains(text(), '{text_to_find}')]",
            f"//button[contains(text(), '{text_to_find}')]",
            f"//div[@role='button'][contains(text(), '{text_to_find}')]",
            f"//li[contains(text(), '{text_to_find}')]",
            f"//span[contains(@class, 'clickable')][contains(text(), '{text_to_find}')]",
        ]
        
        for selector in selectors:
            try:
                element = self.driver.find_element(By.XPATH, selector)
                if element.is_displayed():
                    console.print(f"[green]✅ Found clickable element[/green]")
                    return (By.XPATH, selector)
            except:
                pass
        
        return None
    
    # ==================== NAVIGATION HELPERS ====================
    
    def navigate_to_url(self, url: str, wait_for_load: bool = True) -> bool:
        """Navigate to URL with intelligent loading detection"""
        try:
            console.print(f"[cyan]🔗 Navigating to: {url}[/cyan]")
            self.driver.get(url)
            
            if wait_for_load:
                # Wait for page to load
                time.sleep(2)
                try:
                    self.wait.until(lambda d: d.execute_script('return document.readyState') == 'complete')
                    console.print(f"[green]✅ Page loaded[/green]")
                except:
                    console.print(f"[yellow]⚠️  Page load timeout (continuing anyway)[/yellow]")
            
            self.navigation_history.append({
                'url': url,
                'timestamp': datetime.now().isoformat()
            })
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Navigation failed: {e}[/red]")
            return False
    
    def search_and_navigate(self, search_text: str, search_selector: str = None) -> bool:
        """Search for text in search box and navigate"""
        try:
            console.print(f"[cyan]🔍 Searching for: '{search_text}'[/cyan]")
            
            # Find search input
            if search_selector:
                search_input = self.driver.find_element(By.XPATH, search_selector)
            else:
                # Try common search selectors
                search_selectors = [
                    "//input[@type='search']",
                    "//input[@placeholder*='Search']",
                    "//input[@aria-label*='Search']",
                    "//input[@class*='search']",
                ]
                
                search_input = None
                for selector in search_selectors:
                    try:
                        search_input = self.driver.find_element(By.XPATH, selector)
                        break
                    except:
                        pass
                
                if not search_input:
                    console.print(f"[yellow]⚠️  Could not find search input[/yellow]")
                    return False
            
            # Type search text
            search_input.clear()
            search_input.send_keys(search_text)
            time.sleep(1)
            search_input.send_keys(Keys.RETURN)
            time.sleep(3)
            
            console.print(f"[green]✅ Searched and navigated[/green]")
            return True
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Search failed: {e}[/yellow]")
            return False
    
    # ==================== SCREENSHOT CAPTURE ====================
    
    def capture_screenshot(self, name: str, wait_time: int = 2,
                         scroll_before: bool = True, ensure_watermark: bool = True,
                         full_page: bool = True) -> Optional[str]:
        """
        Capture screenshot with optional scrolling
        
        Args:
            name: Screenshot name/identifier
            wait_time: Seconds to wait before capturing
            scroll_before: Whether to scroll to load dynamic content
            ensure_watermark: Whether to stamp the capture with the evidence label & timestamp
            full_page: Attempt Chrome DevTools full-page capture (falls back to viewport)
        
        Returns:
            Path to saved screenshot or None if failed
        """
        try:
            # Verify driver is still alive before attempting screenshot
            if not self.driver:
                console.print("[red]❌ Browser driver is None - cannot capture screenshot[/red]")
                return None
            
            try:
                # Quick health check
                _ = self.driver.current_url
            except Exception as health_err:
                console.print(f"[red]❌ Browser window closed or crashed: {health_err}[/red]")
                return None
            
            # Wait for dynamic content
            time.sleep(wait_time)
            
            # Scroll to load content (with error handling for each scroll)
            if scroll_before:
                console.print("[cyan]📜 Scrolling to load content...[/cyan]")
                try:
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/3);")
                    time.sleep(0.5)
                    self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight/2);")
                    time.sleep(0.5)
                    self.driver.execute_script("window.scrollTo(0, 0);")
                    time.sleep(0.5)
                except Exception as scroll_err:
                    console.print(f"[yellow]⚠️ Scroll failed (window may be closed): {scroll_err}[/yellow]")
                    return None
            
            console.print("[cyan]📸 Capturing screenshot...[/cyan]")

            screenshot_bytes = None

            if full_page and hasattr(self.driver, "execute_cdp_cmd"):
                try:
                    total_width = self.driver.execute_script(
                        "return Math.max(document.body.scrollWidth, document.documentElement.scrollWidth, window.innerWidth);"
                    )
                    total_height = self.driver.execute_script(
                        "return Math.max(document.body.scrollHeight, document.documentElement.scrollHeight, window.innerHeight);"
                    )

                    # Chrome fails above ~16k px - clamp to safe limits
                    max_dimension = 16384
                    total_width = max(1, min(int(total_width or 1920), max_dimension))
                    total_height = max(1, min(int(total_height or 1080), max_dimension))

                    self.driver.execute_cdp_cmd("Page.enable", {})
                    self.driver.execute_cdp_cmd("Emulation.setDeviceMetricsOverride", {
                        "mobile": False,
                        "width": total_width,
                        "height": total_height,
                        "deviceScaleFactor": 1,
                        "screenOrientation": {"type": "landscapePrimary", "angle": 0}
                    })

                    capture_result = self.driver.execute_cdp_cmd("Page.captureScreenshot", {
                        "format": "png",
                        "fromSurface": True,
                        "captureBeyondViewport": True
                    })
                    if capture_result and capture_result.get("data"):
                        screenshot_bytes = base64.b64decode(capture_result["data"])
                        if self.debug:
                            console.print(
                                f"[dim]   📏 Full-page capture via CDP ({total_width}x{total_height})[/dim]"
                            )
                except Exception as full_page_error:
                    screenshot_bytes = None
                    console.print(f"[yellow]⚠️  Full-page capture fallback: {full_page_error}")
                finally:
                    try:
                        self.driver.execute_cdp_cmd("Emulation.clearDeviceMetricsOverride", {})
                    except Exception:
                        pass

            if screenshot_bytes is None:
                screenshot_bytes = self.driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(screenshot_bytes))
            if ensure_watermark:
                img = self._add_timestamp(img, name)
            
            # Save
            timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
            filename = f"evidence_{name}_{timestamp}.png"
            
            # Create screenshots directory
            screenshot_dir = Path('/Users/krishna/Documents/audit-ai-agent/screenshots')
            screenshot_dir.mkdir(parents=True, exist_ok=True)
            filepath = screenshot_dir / filename
            
            img.save(str(filepath), 'PNG')
            console.print(f"[green]✅ Screenshot saved: {filepath}[/green]")
            
            return str(filepath)
            
        except Exception as e:
            console.print(f"[red]❌ Screenshot failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return None
    
    def _add_timestamp(self, img: Image.Image, label: str = "") -> Image.Image:
        """Add timestamp watermark (UTC ISO 8601) & label bottom-right with LARGE VISIBLE font.

        Ensures auditors can verify capture time embedded in the image itself.
        Uses larger font for better visibility per user request.
        """
        try:
            draw = ImageDraw.Draw(img)
            utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
            timestamp = utc_now.strftime("%Y-%m-%dT%H:%M:%SZ")
            base_label = label if label else "EVIDENCE"
            text = f"{base_label} | {timestamp}"[:120]
            
            # Use BIGGER font for better visibility (36pt instead of 20pt)
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            except:
                try:
                    # Try bold variant for even better visibility
                    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
                except:
                    font = ImageFont.load_default()
            
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Position in bottom-right corner with more padding
            x = img.width - text_width - 30
            y = img.height - text_height - 30
            
            padding = 15  # Increased padding for bigger font
            
            # Draw prominent semi-transparent dark background
            try:
                # Create RGBA overlay with more opacity for better contrast
                overlay = Image.new("RGBA", (text_width + padding*2, text_height + padding*2), (0,0,0,180))
                img.paste(overlay, (x - padding, y - padding), overlay)
            except Exception:
                # Fallback: solid dark rectangle
                draw.rectangle(
                    [x - padding, y - padding, x + text_width + padding, y + text_height + padding],
                    fill=(0, 0, 0, 220)
                )
            
            # Draw bright white text with shadow for maximum visibility
            # First draw shadow (slight offset)
            shadow_offset = 2
            draw.text((x + shadow_offset, y + shadow_offset), text, fill=(0, 0, 0), font=font)
            # Then draw main text in bright white
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
            
            return img
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not add timestamp: {e}[/yellow]")
            return img

    def add_watermark_to_file(self, file_path: str, label: str = "") -> bool:
        """Post-process existing screenshot file to ensure watermark present.

        Used for legacy or fallback capture paths that may not embed timestamp.
        Returns True on success, False otherwise.
        """
        try:
            if not os.path.exists(file_path):
                return False
            img = Image.open(file_path)
            img = self._add_timestamp(img, label)
            img.save(file_path, 'PNG')
            return True
        except Exception as e:
            console.print(f"[yellow]⚠️  Watermark post-process failed: {e}")
            return False
    
    def capture_full_page_with_scrolls(self, name: str, max_scrolls: int = 10) -> List[str]:
        """Capture multiple screenshots while scrolling for long pages"""
        console.print(f"[cyan]📸 Capturing full page with scrolling ({name})...[/cyan]")
        screenshots = []
        
        try:
            scroll_position = 0
            screenshot_num = 1
            
            for scroll_num in range(max_scrolls):
                # Capture current view
                screenshot_path = self.capture_screenshot(
                    f"{name}_scroll{screenshot_num}",
                    wait_time=1,
                    scroll_before=False,
                    ensure_watermark=True,
                    full_page=False
                )
                if screenshot_path:
                    screenshots.append(screenshot_path)
                
                # Check if we're at bottom
                new_scroll_position = self.driver.execute_script("return window.pageYOffset;")
                if new_scroll_position == scroll_position:
                    console.print(f"[green]✅ Reached bottom of page[/green]")
                    break
                
                scroll_position = new_scroll_position
                
                # Scroll down
                self.driver.execute_script("window.scrollBy(0, window.innerHeight);")
                time.sleep(1)
                screenshot_num += 1
            
            console.print(f"[green]✅ Captured {len(screenshots)} screenshots[/green]")
            return screenshots
            
        except Exception as e:
            console.print(f"[red]❌ Scroll capture failed: {e}[/red]")
            return screenshots
    
    # ==================== UTILITIES ====================
    
    def _parse_selector_type(self, selector: str) -> By:
        """Determine selector type (xpath, css, id, etc.)"""
        if selector.startswith('//') or selector.startswith('xpath:'):
            return By.XPATH
        elif selector.startswith('#'):
            return By.ID
        elif selector.startswith('.') or selector.startswith('css:'):
            return By.CSS_SELECTOR
        else:
            return By.XPATH  # Default to XPath
    
    def get_current_url(self) -> str:
        """Get current URL"""
        return self.driver.current_url if self.driver else None
    
    def get_page_title(self) -> str:
        """Get page title"""
        return self.driver.title if self.driver else None
    
    def execute_javascript(self, script: str, *args) -> any:
        """Execute arbitrary JavaScript"""
        return self.driver.execute_script(script, *args) if self.driver else None
    
    def wait_for_url_change(self, timeout: int = 10) -> bool:
        """Wait for URL to change"""
        old_url = self.driver.current_url
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            if self.driver.current_url != old_url:
                console.print(f"[green]✅ URL changed[/green]")
                return True
            time.sleep(0.5)
        
        console.print(f"[yellow]⚠️  URL did not change[/yellow]")
        return False
    
    def close(self):
        """Close browser and clean up AWS sessions"""
        try:
            if self.driver:
                # Clear AWS session cookies before closing
                try:
                    console.print("[dim]🧹 Clearing AWS session cookies...[/dim]")
                    # self.driver.delete_all_cookies()  # TEMPORARILY COMMENTED OUT FOR TESTING
                    
                    # Close all extra windows/tabs
                    if len(self.driver.window_handles) > 1:
                        for handle in self.driver.window_handles[1:]:
                            self.driver.switch_to.window(handle)
                            self.driver.close()
                        self.driver.switch_to.window(self.driver.window_handles[0])
                except Exception as e:
                    if self.debug:
                        console.print(f"[dim]Cookie cleanup: {str(e)[:60]}[/dim]")
                
                # Close Playwright if connected
                try:
                    if self.page:
                        self.page.close()
                    if self.browser_pw:
                        self.browser_pw.close()
                    if self.playwright:
                        self.playwright.stop()
                except Exception as e:
                    if self.debug:
                        console.print(f"[dim]Playwright cleanup: {str(e)[:60]}[/dim]")
                
                # Finally close the browser
                self.driver.quit()
                console.print("[green]🔒 Browser closed[/green]")
                
                # CRITICAL: Clear AWS cookies from disk (user data directory)
                # The persistent user data dir saves cookies to disk, which get reloaded on next launch
                if self.user_data_dir:  # Only if using persistent profile
                    # self._clear_aws_cookies_from_disk()  # TEMPORARILY COMMENTED OUT FOR TESTING
                    console.print("[dim]🔄 Cookie cleanup disabled - session will persist[/dim]")
                else:
                    console.print("[dim]   Temporary profile used - no disk cleanup needed[/dim]")
                
        except Exception as e:
            console.print(f"[yellow]⚠️  Error closing browser: {str(e)[:80]}[/yellow]")

    def _is_session_selector_page(self, url: Optional[str], page_source: Optional[str] = None) -> bool:
        """Return True if the current URL/page appears to be the AWS session chooser."""
        if not url:
            return False

        parsed = urlparse(url)
        host = parsed.netloc.lower()
        path = parsed.path.lower()
        query = parsed.query.lower()

        if 'sessions/selector' in path and 'aws.amazon.com' in host:
            return True

        if 'signin.aws.amazon.com' in host:
            if '/console/oauth' in path or '/oauth' in path:
                return True
            if 'client_id=arn:aws:signin:::console' in query:
                return True

        if page_source:
            lowered = page_source.lower()
            keywords = (
                'choose your aws session',
                'choose your aws account',
                'select your aws account',
                'select your aws role',
                'use this session',
            )
            if any(keyword in lowered for keyword in keywords):
                return True

        return False

    def _clear_aws_cookies_from_disk(self):
        """Clear AWS-related cookies from the persistent user data directory"""
        try:
            import shutil
            import glob
            
            console.print("[dim]🧹 Clearing AWS cookies from disk...[/dim]")
            
            # Find and delete AWS cookie files in user data directory
            cookie_paths = [
                os.path.join(self.user_data_dir, "Default", "Cookies"),
                os.path.join(self.user_data_dir, "Default", "Cookies-journal"),
                os.path.join(self.user_data_dir, "Default", "Network", "Cookies"),
                os.path.join(self.user_data_dir, "Default", "Session Storage"),
                os.path.join(self.user_data_dir, "Default", "Local Storage"),
            ]
            
            deleted_count = 0
            for cookie_path in cookie_paths:
                if os.path.exists(cookie_path):
                    try:
                        if os.path.isfile(cookie_path):
                            os.remove(cookie_path)
                            deleted_count += 1
                        elif os.path.isdir(cookie_path):
                            # Clear AWS-related files only
                            for root, dirs, files in os.walk(cookie_path):
                                for file in files:
                                    if any(aws_domain in file.lower() for aws_domain in ['aws', 'amazon', 'duo', 'signin']):
                                        os.remove(os.path.join(root, file))
                                        deleted_count += 1
                    except Exception as e:
                        if self.debug:
                            console.print(f"[dim]   Skip {cookie_path}: {str(e)[:40]}[/dim]")
            
            if deleted_count > 0:
                console.print(f"[green]✅ Cleared {deleted_count} cookie/storage files from disk[/green]")
            else:
                console.print("[dim]   No cookie files found to clear[/dim]")
                
        except Exception as e:
            console.print(f"[dim]   Disk cleanup: {str(e)[:60]}[/dim]")
    
    def __del__(self):
        """Destructor to ensure browser is closed"""
        try:
            self.close()
        except:
            pass
    
    def print_diagnostics(self):
        """Print diagnostic information"""
        console.print(Panel("[cyan]📊 Navigation & Click History[/cyan]", expand=False))
        
        if self.navigation_history:
            console.print("\n[bold cyan]Navigation History:[/bold cyan]")
            table = Table(show_header=True)
            table.add_column("URL", style="dim")
            table.add_column("Time", style="green")
            
            for nav in self.navigation_history:
                table.add_row(nav['url'][-60:], nav['timestamp'].split('T')[1][:8])
            
            console.print(table)
        
        if self.click_history:
            console.print("\n[bold cyan]Click History:[/bold cyan]")
            table = Table(show_header=True)
            table.add_column("Selector", style="dim")
            table.add_column("Strategy", style="green")
            table.add_column("Time", style="dim")
            
            for click in self.click_history[-10:]:  # Last 10 clicks
                table.add_row(click['selector'][-40:], click['strategy'], click['timestamp'].split('T')[1][:8])
            
            console.print(table)


if __name__ == "__main__":
    # Example usage
    console.print("[cyan]🧪 Universal Screenshot Tool - Testing[/cyan]\n")
    
    tool = UniversalScreenshotEnhanced(headless=False, timeout=20)
    
    if tool.connect():
        console.print("[green]✅ Connected![/green]")
        # Add your navigation code here
        tool.print_diagnostics()
        tool.close()
