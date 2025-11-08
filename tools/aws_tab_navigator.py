"""
AWS Tab Navigator - Intelligent tab clicking for AWS Console

This module provides HUMAN-LIKE navigation of AWS Console tabs.
Instead of using fragile URL hash fragments, it:
1. Finds tabs by visible text (like a human would)
2. Clicks them using multiple strategies
3. Waits for content to load
4. Verifies navigation succeeded

This is FAR MORE RELIABLE than URL manipulation!
"""

import time
from typing import Optional, List
from rich.console import Console

console = Console()


class AWSTabNavigator:
    """
    Intelligent tab navigation for AWS Console.
    
    Uses CLICKING instead of URL manipulation for reliability.
    """
    
    def __init__(self, driver):
        """
        Initialize navigator with Selenium driver.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.last_clicked_tab = None
    
    def find_and_click_tab(self, tab_name: str, wait_time: int = 3) -> bool:
        """
        Find and click a tab by its visible text (HUMAN-LIKE!).
        
        This is MUCH MORE RELIABLE than URL hash fragments because:
        - Finds tabs by what humans see (text)
        - Works even if AWS changes URLs
        - Adapts to UI changes
        - Uses multiple fallback strategies
        
        Args:
            tab_name: Tab name to click (e.g., "Configuration", "Maintenance & backups")
            wait_time: Seconds to wait after clicking
        
        Returns:
            True if tab was found and clicked
        
        Examples:
            >>> navigator.find_and_click_tab("Configuration")
            >>> navigator.find_and_click_tab("Maintenance & backups")
            >>> navigator.find_and_click_tab("Monitoring")
        """
        console.print(f"[cyan]🔍 Looking for tab: '{tab_name}'...[/cyan]")
        
        # Strategy 1: Use JavaScript to find and click tab (MOST RELIABLE!)
        result = self.driver.execute_script("""
            var tabName = arguments[0];
            console.log('=== AWS Tab Navigation ===');
            console.log('Looking for tab:', tabName);
            
            // Find all possible tab elements
            // AWS Console uses various selectors for tabs
            var tabSelectors = [
                'button[role="tab"]',
                'a[role="tab"]',
                '[data-testid*="tab"]',
                '.awsui-tabs-tab',
                'button[class*="tab"]',
                'a[class*="tab"]'
            ];
            
            var allTabs = [];
            for (var selector of tabSelectors) {
                var tabs = document.querySelectorAll(selector);
                allTabs = allTabs.concat(Array.from(tabs));
            }
            
            console.log('Found', allTabs.length, 'potential tab elements');
            
            // Search for tab by text (case-insensitive, fuzzy matching)
            for (var i = 0; i < allTabs.length; i++) {
                var tab = allTabs[i];
                var tabText = (tab.textContent || tab.innerText || '').trim().toLowerCase();
                var searchText = tabName.toLowerCase();
                
                // Fuzzy matching: allows for variations
                // "Maintenance & backups" matches "maintenance and backups", "Maintenance & Backups", etc.
                var normalizedTabText = tabText.replace(/[^a-z0-9]/g, '');
                var normalizedSearchText = searchText.replace(/[^a-z0-9]/g, '');
                
                if (normalizedTabText.includes(normalizedSearchText) || 
                    normalizedSearchText.includes(normalizedTabText) ||
                    tabText === searchText) {
                    
                    console.log('Found matching tab:', tabText);
                    
                    // Check if tab is already selected
                    var isSelected = tab.getAttribute('aria-selected') === 'true' ||
                                   tab.classList.contains('selected') ||
                                   tab.classList.contains('active') ||
                                   tab.getAttribute('data-active') === 'true';
                    
                    if (isSelected) {
                        console.log('Tab already selected');
                        return {success: true, alreadySelected: true, tabText: tabText};
                    }
                    
                    // Click the tab (multiple strategies)
                    try {
                        // Strategy 1: Direct click
                        tab.click();
                        console.log('Clicked tab via direct click');
                        return {success: true, alreadySelected: false, tabText: tabText};
                    } catch (e) {
                        console.log('Direct click failed, trying dispatch...');
                        
                        // Strategy 2: Dispatch mouse event
                        try {
                            var clickEvent = new MouseEvent('click', {
                                bubbles: true,
                                cancelable: true,
                                view: window
                            });
                            tab.dispatchEvent(clickEvent);
                            console.log('Clicked tab via event dispatch');
                            return {success: true, alreadySelected: false, tabText: tabText};
                        } catch (e2) {
                            console.log('Event dispatch failed:', e2);
                        }
                    }
                }
            }
            
            console.log('Tab not found:', tabName);
            console.log('Available tabs:', allTabs.map(t => t.textContent.trim()).filter(t => t));
            
            return {
                success: false, 
                error: 'Tab not found',
                availableTabs: allTabs.map(t => t.textContent.trim()).filter(t => t).slice(0, 20)
            };
        """, tab_name)
        
        if result and result.get('success'):
            if result.get('alreadySelected'):
                console.print(f"[green]✓ Tab '{tab_name}' already selected[/green]")
            else:
                console.print(f"[green]✅ Clicked tab: '{result.get('tabText')}'[/green]")
                time.sleep(wait_time)  # Wait for content to load
            
            self.last_clicked_tab = tab_name
            return True
        else:
            console.print(f"[red]❌ Tab '{tab_name}' not found[/red]")
            if result and result.get('availableTabs'):
                console.print(f"[yellow]Available tabs:[/yellow]")
                for tab in result.get('availableTabs', [])[:10]:
                    console.print(f"  - {tab}")
            return False
    
    def click_multiple_tabs(self, tab_names: List[str], screenshot_callback=None) -> dict:
        """
        Click multiple tabs and optionally take screenshots of each.
        
        This is perfect for collecting evidence across multiple tabs!
        
        Args:
            tab_names: List of tab names to click
            screenshot_callback: Optional function to call after each tab click
                                Takes (tab_name) as argument
        
        Returns:
            Dict with results for each tab
        
        Example:
            >>> def take_screenshot(tab_name):
            >>>     driver.save_screenshot(f"{tab_name}.png")
            >>> 
            >>> navigator.click_multiple_tabs(
            >>>     ["Configuration", "Maintenance & backups", "Monitoring"],
            >>>     screenshot_callback=take_screenshot
            >>> )
        """
        results = {}
        
        for tab_name in tab_names:
            console.print(f"\n[bold cyan]📑 Processing tab: {tab_name}[/bold cyan]")
            
            success = self.find_and_click_tab(tab_name)
            
            if success:
                # Take screenshot if callback provided
                if screenshot_callback:
                    try:
                        screenshot_path = screenshot_callback(tab_name)
                        results[tab_name] = {
                            "success": True,
                            "screenshot": screenshot_path
                        }
                        console.print(f"[green]✅ Screenshot captured for '{tab_name}'[/green]")
                    except Exception as e:
                        results[tab_name] = {
                            "success": True,
                            "screenshot": None,
                            "error": str(e)
                        }
                        console.print(f"[red]❌ Screenshot failed for '{tab_name}': {e}[/red]")
                else:
                    results[tab_name] = {"success": True}
            else:
                results[tab_name] = {
                    "success": False,
                    "error": "Tab not found"
                }
        
        return results
    
    def explore_all_tabs(self, screenshot_callback=None) -> dict:
        """
        Automatically discover and click ALL tabs on the page.
        
        Perfect for comprehensive evidence collection!
        
        Args:
            screenshot_callback: Optional function to call after each tab
        
        Returns:
            Dict with results for each tab found
        """
        console.print("[bold cyan]🔍 Discovering all tabs...[/bold cyan]")
        
        # Use JavaScript to find all tabs
        tabs = self.driver.execute_script("""
            var tabSelectors = [
                'button[role="tab"]',
                'a[role="tab"]',
                '[data-testid*="tab"]',
                '.awsui-tabs-tab'
            ];
            
            var allTabs = [];
            var seenTexts = new Set();
            
            for (var selector of tabSelectors) {
                var tabs = document.querySelectorAll(selector);
                for (var tab of tabs) {
                    var text = (tab.textContent || tab.innerText || '').trim();
                    if (text && !seenTexts.has(text)) {
                        allTabs.push(text);
                        seenTexts.add(text);
                    }
                }
            }
            
            return allTabs;
        """)
        
        if not tabs:
            console.print("[yellow]⚠️  No tabs found on page[/yellow]")
            return {}
        
        console.print(f"[green]✓ Found {len(tabs)} tabs:[/green]")
        for tab in tabs:
            console.print(f"  - {tab}")
        
        # Click each tab
        return self.click_multiple_tabs(tabs, screenshot_callback)
    
    def verify_tab_content_loaded(self, expected_text: Optional[str] = None, timeout: int = 5) -> bool:
        """
        Verify that tab content has loaded.
        
        Args:
            expected_text: Optional text to look for in content
            timeout: Max seconds to wait
        
        Returns:
            True if content loaded
        """
        start_time = time.time()
        
        while time.time() - start_time < timeout:
            # Check if page has content (not just loading spinner)
            result = self.driver.execute_script("""
                var expectedText = arguments[0];
                
                // Check for loading indicators
                var loadingIndicators = document.querySelectorAll('[data-testid="loading"]');
                if (loadingIndicators.length > 0) {
                    return {loading: true};
                }
                
                // Check for content
                var contentAreas = document.querySelectorAll('[role="main"], .awsui-table, .awsui-cards');
                if (contentAreas.length > 0) {
                    var hasContent = false;
                    for (var area of contentAreas) {
                        if (area.textContent.trim().length > 50) {
                            hasContent = true;
                            break;
                        }
                    }
                    
                    if (hasContent) {
                        // If expected text provided, check for it
                        if (expectedText) {
                            var pageText = document.body.textContent;
                            if (pageText.includes(expectedText)) {
                                return {loaded: true, foundExpectedText: true};
                            } else {
                                return {loaded: true, foundExpectedText: false};
                            }
                        } else {
                            return {loaded: true};
                        }
                    }
                }
                
                return {loading: false, loaded: false};
            """, expected_text)
            
            if result.get('loaded'):
                if expected_text:
                    if result.get('foundExpectedText'):
                        console.print(f"[green]✓ Content loaded (found '{expected_text}')[/green]")
                    else:
                        console.print(f"[yellow]⚠️  Content loaded but '{expected_text}' not found[/yellow]")
                else:
                    console.print("[green]✓ Content loaded[/green]")
                return True
            
            time.sleep(0.5)
        
        console.print("[yellow]⚠️  Content load verification timed out[/yellow]")
        return False


# Convenience function for quick tab navigation
def navigate_aws_tabs(driver, tab_names: List[str], screenshot_func=None) -> dict:
    """
    Convenience function to navigate multiple AWS Console tabs.
    
    Args:
        driver: Selenium WebDriver
        tab_names: List of tab names to click
        screenshot_func: Optional screenshot function
    
    Returns:
        Results dict
    
    Example:
        >>> from selenium import webdriver
        >>> driver = webdriver.Chrome()
        >>> driver.get("https://console.aws.amazon.com/rds/...")
        >>> 
        >>> results = navigate_aws_tabs(
        >>>     driver,
        >>>     ["Configuration", "Maintenance & backups", "Monitoring"]
        >>> )
    """
    navigator = AWSTabNavigator(driver)
    return navigator.click_multiple_tabs(tab_names, screenshot_func)

