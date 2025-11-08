"""
RDS-Specific Enhanced Navigator
Handles all RDS navigation including clusters, instances, tabs, and configurations
"""

import os
import time
import re
from typing import Optional, Tuple, Dict
from datetime import datetime

try:
    from selenium.webdriver.common.by import By
    from selenium.webdriver.common.keys import Keys
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, NoSuchElementException
except ImportError:
    pass

from rich.console import Console
from tools.universal_screenshot_enhanced import UniversalScreenshotEnhanced, ClickStrategy, WaitCondition

# INTELLIGENT: Import AWS SDK helper for smart cluster discovery
try:
    from tools.aws_rds_helper import AWSRDSHelper
    AWS_SDK_AVAILABLE = True
except ImportError:
    console.print("[yellow]⚠️  AWS SDK (boto3) not available, will use browser-only navigation[/yellow]")
    AWS_SDK_AVAILABLE = False

console = Console()


class RDSNavigatorEnhanced:
    """Enhanced RDS navigation with multiple strategies"""
    
    def __init__(self, screenshot_tool: UniversalScreenshotEnhanced, aws_profile: str = None):
        self.tool = screenshot_tool
        self.region = 'us-east-1'
        self.current_cluster = None
        self.current_tab = None
        self.aws_profile = aws_profile
        
        # Initialize AWS SDK helper for intelligent cluster discovery
        self.aws_helper = None
        if AWS_SDK_AVAILABLE:
            try:
                self.aws_helper = AWSRDSHelper(region=self.region, profile=aws_profile)
                console.print("[green]🧠 AWS SDK enabled - Agent will use intelligent cluster discovery![/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  AWS SDK init failed: {e}[/yellow]")
                console.print("[dim]   Will fall back to browser-only navigation[/dim]")
    
    def set_region(self, region: str):
        """Set AWS region"""
        self.region = region
        console.print(f"[cyan]🌍 Region set to: {region}[/cyan]")
    
    def navigate_to_cluster_direct(self, cluster_id: str, tab: str = None, is_cluster: bool = True) -> bool:
        """
        Navigate to RDS cluster using HYBRID approach:
        1. URL for cluster (fast)
        2. CLICKING for tabs (reliable!)
        
        This is MUCH MORE RELIABLE than URL hash fragments for tabs!
        
        Args:
            cluster_id: The cluster identifier
            tab: Optional tab name (e.g., 'Configuration', 'Maintenance & backups')
            is_cluster: True for clusters, False for instances
        
        Returns:
            True if navigation successful
        """
        try:
            # Build URL to cluster (WITHOUT tab - we'll click it!)
            hash_fragment = f"#database:id={cluster_id}"
            if is_cluster:
                hash_fragment += ";is-cluster=true"
            
            url = f"https://{self.region}.console.aws.amazon.com/rds/home?region={self.region}{hash_fragment}"
            
            console.print(f"[cyan]🗄️  Navigating to RDS cluster: {cluster_id}[/cyan]")
            if tab:
                console.print(f"[cyan]📑 Will click tab: {tab}[/cyan]")
            
            if not self.tool.navigate_to_url(url):
                console.print("[red]❌ Failed to navigate to cluster[/red]")
                return False
            
            # Wait for cluster page to load
            console.print("[dim]⏳ Waiting for cluster page to load...[/dim]")
            time.sleep(5)
            
            # Store current state
            self.current_cluster = cluster_id
            self.current_tab = tab if tab else None
            
            # If tab specified, CLICK IT (don't use URL!)
            if tab:
                from tools.aws_tab_navigator import AWSTabNavigator
                
                console.print(f"[bold cyan]🖱️  Clicking tab '{tab}' (HUMAN-LIKE navigation!)[/bold cyan]")
                tab_navigator = AWSTabNavigator(self.tool.driver)
                
                if tab_navigator.find_and_click_tab(tab):
                    # Verify content loaded
                    tab_navigator.verify_tab_content_loaded()
                    console.print(f"[green]✅ Successfully navigated to '{tab}' tab[/green]")
                else:
                    console.print(f"[yellow]⚠️  Failed to click tab '{tab}', trying URL fallback...[/yellow]")
                    # Fallback: Try URL-based navigation
                    return self._navigate_to_tab_via_url(cluster_id, tab, is_cluster)
            
            # Use JavaScript to verify page loaded and tab selected
            console.print("[cyan]🔍 Verifying page loaded with JavaScript...[/cyan]")
            verification_result = self.tool.driver.execute_script("""
                var clusterId = arguments[0];
                var tabName = arguments[1];
                
                console.log('=== RDS Page Verification ===');
                console.log('Target cluster:', clusterId);
                console.log('Target tab:', tabName);
                
                // Check 1: Verify cluster ID appears on page
                var pageText = document.body.innerText;
                if (pageText.indexOf(clusterId) === -1) {
                    console.log('ERROR: Cluster ID not found on page');
                    return {success: false, reason: 'Cluster ID not on page', clusterId: clusterId};
                }
                console.log('✓ Cluster ID found on page');
                
                // Check 2: Verify we're on RDS page (look for common RDS terms)
                var isRDSPage = pageText.indexOf('RDS') !== -1 || 
                               pageText.indexOf('Aurora') !== -1 || 
                               pageText.indexOf('Database') !== -1 ||
                               pageText.indexOf('Cluster') !== -1;
                if (!isRDSPage) {
                    console.log('WARNING: May not be on RDS page');
                }
                console.log('✓ On RDS page');
                
                // Check 3: If tab specified, find and click it if not already selected
                if (tabName) {
                    console.log('Looking for tab:', tabName);
                    
                    // Find all tab elements (AWS Console uses various selectors)
                    var tabSelectors = [
                        '[role="tab"]',
                        'button[class*="tab"]',
                        'a[class*="tab"]',
                        '.awsui-tabs-tab',
                        '[data-testid*="tab"]'
                    ];
                    
                    var allTabs = [];
                    for (var selector of tabSelectors) {
                        var tabs = document.querySelectorAll(selector);
                        allTabs = allTabs.concat(Array.from(tabs));
                    }
                    
                    console.log('Found', allTabs.length, 'potential tab elements');
                    
                    var tabFound = false;
                    var tabSelected = false;
                    
                    for (var i = 0; i < allTabs.length; i++) {
                        var tab = allTabs[i];
                        var text = (tab.textContent || tab.innerText || '').toLowerCase().trim();
                        
                        // Check if this tab matches our target
                        if (text === tabName.toLowerCase() || 
                            text.indexOf(tabName.toLowerCase()) !== -1 ||
                            tabName.toLowerCase().indexOf(text) !== -1) {
                            
                            tabFound = true;
                            console.log('Found matching tab:', text);
                            
                            // Check if tab is already selected
                            var isSelected = tab.getAttribute('aria-selected') === 'true' ||
                                           tab.classList.contains('selected') ||
                                           tab.classList.contains('active') ||
                                           tab.getAttribute('data-active') === 'true';
                            
                            if (isSelected) {
                                console.log('✓ Tab already selected');
                                tabSelected = true;
                            } else {
                                console.log('Tab not selected, clicking it...');
                                try {
                                    tab.click();
                                    tabSelected = true;
                                    console.log('✓ Clicked tab successfully');
                                } catch (e) {
                                    console.log('Failed to click tab:', e);
                                }
                            }
                            break;
                        }
                    }
                    
                    if (!tabFound) {
                        console.log('WARNING: Tab not found on page (may still be loading)');
                        return {success: false, reason: 'Tab not found', needsRetry: true, tabName: tabName};
                    }
                    
                    if (!tabSelected) {
                        console.log('WARNING: Tab found but not selected');
                        return {success: false, reason: 'Tab not selected', needsRetry: true, tabName: tabName};
                    }
                }
                
                console.log('=== Verification Complete ===');
                return {success: true, clusterId: clusterId, tabName: tabName};
            """, cluster_id, tab_normalized)
            
            # Check verification result
            if verification_result and verification_result.get('success'):
                console.print(f"[green]✅ Page verified: {cluster_id}[/green]")
                if tab:
                    console.print(f"[green]✅ Tab verified: {tab_normalized}[/green]")
                return True
            
            # If verification failed but needs retry, wait and try once more
            if verification_result and verification_result.get('needsRetry'):
                console.print(f"[yellow]⚠️  {verification_result.get('reason')}, waiting and retrying...[/yellow]")
                time.sleep(5)
                
                # Retry verification/click
                retry_result = self.tool.driver.execute_script("""
                    var tabName = arguments[0];
                    
                    // Try to find and click the tab again
                    var allElements = document.querySelectorAll('[role="tab"], button, a');
                    for (var i = 0; i < allElements.length; i++) {
                        var elem = allElements[i];
                        var text = (elem.textContent || elem.innerText || '').toLowerCase().trim();
                        if (text.indexOf(tabName.toLowerCase()) !== -1) {
                            elem.click();
                            return {success: true, clicked: text};
                        }
                    }
                    return {success: false};
                """, tab_normalized)
                
                if retry_result and retry_result.get('success'):
                    console.print(f"[green]✅ Tab clicked on retry: {retry_result.get('clicked')}[/green]")
                    return True
                else:
                    console.print("[yellow]⚠️  Tab not found on retry, proceeding anyway[/yellow]")
                    return True
            
            # Even if verification had issues, return True as URL navigation succeeded
            console.print("[yellow]⚠️  Page verification incomplete, but URL navigation succeeded[/yellow]")
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Direct navigation failed: {e}[/red]")
            return False
    
    def navigate_to_clusters_list(self) -> bool:
        """Navigate to RDS clusters list using direct URL"""
        try:
            # First, verify browser is still alive
            try:
                current_url = self.tool.driver.current_url
                if not current_url:
                    console.print("[red]❌ Browser session is dead (no URL)[/red]")
                    console.print("[yellow]💡 Browser window may have been closed. Please restart the agent.[/yellow]")
                    return False
            except Exception as e:
                error_msg = str(e)
                if 'no such window' in error_msg or 'target window already closed' in error_msg or 'web view not found' in error_msg:
                    console.print("[red]❌ Browser window was closed![/red]")
                    console.print("[yellow]💡 Please restart the agent to open a new browser session.[/yellow]")
                    return False
                else:
                    console.print(f"[yellow]⚠️  Browser health check warning: {error_msg[:80]}[/yellow]")
            
            console.print("[cyan]📋 Navigating to RDS databases list...[/cyan]")
            
            # Use exact AWS RDS URL pattern: #databases:
            url = f"https://{self.region}.console.aws.amazon.com/rds/home?region={self.region}#databases:"
            console.print(f"[dim]URL: {url}[/dim]")
            
            if not self.tool.navigate_to_url(url):
                console.print("[red]❌ Failed to navigate to RDS console[/red]")
                return False
            
            # Wait for page to load
            time.sleep(5)
            
            # Verify we're on RDS databases page
            page_source = self.tool.driver.page_source.lower()
            if 'rds' in page_source or 'database' in page_source or 'cluster' in page_source:
                console.print("[green]✅ RDS databases list loaded[/green]")
                return True
            else:
                console.print("[yellow]⚠️  Page may not be RDS console[/yellow]")
                return False
        
        except Exception as e:
            console.print(f"[red]❌ Navigation failed: {e}[/red]")
            return False
    
    def find_cluster_by_name(self, cluster_name: str, partial_match: bool = True) -> Optional[Dict]:
        """
        Find cluster in list by name (supports PARTIAL name matching!).
        
        Args:
            cluster_name: Full or partial cluster name (e.g., "conure" for "prod-conure-aurora-cluster")
            partial_match: If True, finds clusters containing the name (default: True)
        
        Returns:
            Dict with cluster info: {'full_name': str, 'element': WebElement, 'selector': str}
            or None if not found
        """
        try:
            console.print(f"[cyan]🔍 Searching for cluster with name containing: '{cluster_name}'[/cyan]")
            
            # Use JavaScript to find ALL clusters and match by partial name
            result = self.tool.driver.execute_script("""
                var searchName = arguments[0];
                var partialMatch = arguments[1];
                
                console.log('=== RDS Cluster Search ===');
                console.log('Searching for:', searchName);
                console.log('Partial match:', partialMatch);
                
                // Find all cluster names and their clickable elements
                var clusters = [];
                
                // Strategy 1: Look in table rows
                var rows = document.querySelectorAll('tbody tr, tr[role="row"], [data-testid*="row"]');
                console.log('Found rows:', rows.length);
                
                for (var i = 0; i < rows.length; i++) {
                    var row = rows[i];
                    var text = row.textContent || row.innerText || '';
                    
                    // Look for cluster identifiers (usually in first cell or as a link)
                    var links = row.querySelectorAll('a[href*="database"]');
                    if (links.length > 0) {
                        var clusterName = links[0].textContent.trim();
                        
                        // Check if this matches our search
                        var matches = false;
                        if (partialMatch) {
                            matches = clusterName.toLowerCase().indexOf(searchName.toLowerCase()) !== -1;
                        } else {
                            matches = clusterName.toLowerCase() === searchName.toLowerCase();
                        }
                        
                        if (matches) {
                            console.log('FOUND MATCH:', clusterName);
                            clusters.push({
                                full_name: clusterName,
                                element_index: i,
                                link_href: links[0].href
                            });
                        }
                    }
                }
                
                // Strategy 2: Look for cluster cards (alternative UI)
                if (clusters.length === 0) {
                    var cards = document.querySelectorAll('[data-testid*="database"], [data-testid*="cluster"]');
                    console.log('Found cards:', cards.length);
                    
                    for (var i = 0; i < cards.length; i++) {
                        var card = cards[i];
                        var text = card.textContent || card.innerText || '';
                        
                        if (partialMatch) {
                            if (text.toLowerCase().indexOf(searchName.toLowerCase()) !== -1) {
                                clusters.push({
                                    full_name: text.trim().split('\\n')[0],
                                    element_index: i,
                                    is_card: true
                                });
                            }
                        }
                    }
                }
                
                console.log('Total matches found:', clusters.length);
                
                if (clusters.length > 0) {
                    return {success: true, clusters: clusters};
                } else {
                    return {success: false, message: 'No matching clusters found'};
                }
            """, cluster_name, partial_match)
            
            if result and result.get('success'):
                clusters = result.get('clusters', [])
                if clusters:
                    # Return first match
                    first_match = clusters[0]
                    full_name = first_match.get('full_name', cluster_name)
                    
                    console.print(f"[green]✅ Found cluster: '{full_name}'[/green]")
                    if len(clusters) > 1:
                        console.print(f"[dim]   (Found {len(clusters)} matches, using first one)[/dim]")
                    
                    # Find the element using MULTIPLE strategies (more robust!)
                    link_href = first_match.get('link_href')
                    element = None
                    
                    if link_href:
                        # Strategy 1: Try exact href match
                        try:
                            element = self.tool.driver.find_element(By.XPATH, f"//a[@href='{link_href}']")
                            console.print(f"[dim]Found element by exact href[/dim]")
                        except:
                            pass
                        
                        # Strategy 2: Try text content match
                        if not element:
                            try:
                                element = self.tool.driver.find_element(By.XPATH, f"//a[contains(text(), '{full_name}')]")
                                console.print(f"[dim]Found element by text content[/dim]")
                            except:
                                pass
                        
                        # Strategy 3: Try partial href match
                        if not element:
                            try:
                                cluster_id = full_name  # Use full name as ID
                                element = self.tool.driver.find_element(By.XPATH, f"//a[contains(@href, '{cluster_id}')]")
                                console.print(f"[dim]Found element by partial href[/dim]")
                            except:
                                pass
                        
                        # Strategy 4: Use JavaScript to find the element
                        if not element:
                            try:
                                console.print(f"[dim]Trying JavaScript element finder...[/dim]")
                                element = self.tool.driver.execute_script("""
                                    var clusterName = arguments[0];
                                    var allLinks = document.querySelectorAll('a');
                                    
                                    for (var i = 0; i < allLinks.length; i++) {
                                        var link = allLinks[i];
                                        var text = link.textContent || link.innerText || '';
                                        var href = link.href || '';
                                        
                                        if (text.indexOf(clusterName) !== -1 || href.indexOf(clusterName) !== -1) {
                                            return link;
                                        }
                                    }
                                    return null;
                                """, full_name)
                                
                                if element:
                                    console.print(f"[dim]Found element using JavaScript[/dim]")
                            except:
                                pass
                        
                        if element:
                            return {
                                'full_name': full_name,
                                'element': element,
                                'selector': f"Found by multiple strategies",
                                'href': link_href
                            }
                    
                    console.print(f"[yellow]⚠️  Found cluster in list but couldn't locate clickable element[/yellow]")
                    return None
            
            console.print(f"[yellow]⚠️  No cluster found matching '{cluster_name}'[/yellow]")
            return None
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Search failed: {e}[/yellow]")
            import traceback
            traceback.print_exc()
            return None
    
    def click_cluster(self, cluster_name: str, partial_match: bool = True) -> bool:
        """
        Click on cluster to open details (UI-based navigation).
        
        Supports PARTIAL name matching! E.g., "conure" will find "prod-conure-aurora-cluster"
        
        Args:
            cluster_name: Full or partial cluster name
            partial_match: If True, matches clusters containing this name
        
        Returns:
            True if successful
        """
        try:
            console.print(f"[cyan]🖱️  Looking for cluster to click: '{cluster_name}'[/cyan]")
            
            # Find cluster (supports partial names!)
            cluster_info = self.find_cluster_by_name(cluster_name, partial_match=partial_match)
            
            if not cluster_info:
                console.print(f"[yellow]⚠️  Could not find cluster in UI[/yellow]")
                return False
            
            full_name = cluster_info.get('full_name', cluster_name)
            element = cluster_info.get('element')
            
            console.print(f"[green]✓ Found cluster: '{full_name}'[/green]")
            console.print(f"[cyan]🖱️  Clicking to open cluster details...[/cyan]")
            
            # Click the cluster link with MULTIPLE strategies (more robust!)
            click_success = False
            
            # Strategy 1: Regular click
            try:
                element.click()
                click_success = True
                console.print(f"[dim]Clicked using regular click[/dim]")
            except Exception as e1:
                console.print(f"[dim]Regular click failed: {e1}[/dim]")
                
                # Strategy 2: JavaScript click
                try:
                    self.tool.driver.execute_script("arguments[0].click();", element)
                    click_success = True
                    console.print(f"[dim]Clicked using JavaScript[/dim]")
                except Exception as e2:
                    console.print(f"[dim]JavaScript click failed: {e2}[/dim]")
                    
                    # Strategy 3: Scroll into view then click
                    try:
                        self.tool.driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
                        time.sleep(1)
                        element.click()
                        click_success = True
                        console.print(f"[dim]Clicked after scrolling into view[/dim]")
                    except Exception as e3:
                        console.print(f"[dim]Scroll+click failed: {e3}[/dim]")
                        
                        # Strategy 4: Navigate via href
                        try:
                            href = cluster_info.get('href')
                            if href:
                                self.tool.driver.get(href)
                                click_success = True
                                console.print(f"[dim]Navigated using href[/dim]")
                        except Exception as e4:
                            console.print(f"[dim]Navigate via href failed: {e4}[/dim]")
            
            if not click_success:
                console.print(f"[red]❌ All click strategies failed[/red]")
                return False
            
            time.sleep(3)
            self.current_cluster = full_name
            console.print(f"[green]✅ Cluster clicked, details page should be loading...[/green]")
            
            # Wait a bit more for page to fully load
            time.sleep(2)
            
            # Verify we're on cluster details page
            current_url = self.tool.driver.current_url
            if 'database' in current_url or full_name.lower() in self.tool.driver.page_source.lower():
                console.print(f"[green]✅ Cluster details page loaded![/green]")
                return True
            else:
                console.print(f"[yellow]⚠️  Cluster details may not have fully loaded, but proceeding...[/yellow]")
                return True
        
        except Exception as e:
            console.print(f"[red]❌ Click operation failed: {e}[/red]")
            import traceback
            traceback.print_exc()
            return False
    
    def navigate_to_cluster_smart(self, cluster_name: str, tab: Optional[str] = None, prefer_url: bool = True) -> bool:
        """
        Smart navigation: tries URL first (fast), falls back to UI clicking (intelligent)
        
        Args:
            cluster_name: Cluster identifier
            tab: Optional tab name
            prefer_url: If True, tries URL first then UI. If False, tries UI first then URL.
        
        Returns:
            True if navigation successful
        """
        try:
            if prefer_url:
                # Strategy 1: Direct URL (fast, reliable)
                console.print(f"[cyan]🎯 Smart navigation: Trying direct URL first...[/cyan]")
                if self.navigate_to_cluster_direct(cluster_id=cluster_name, tab=tab, is_cluster=True):
                    console.print(f"[green]✅ URL navigation successful[/green]")
                    return True
                
                # Strategy 2: UI clicking fallback
                console.print(f"[yellow]⚠️  URL navigation failed, trying UI clicking...[/yellow]")
                if self.navigate_to_clusters_list():
                    if self.click_cluster(cluster_name):
                        if tab:
                            return self.navigate_to_tab(tab)
                        return True
                
                console.print(f"[red]❌ Both URL and UI navigation failed[/red]")
                return False
            else:
                # Strategy 1: UI clicking (intelligent, handles dynamic content)
                console.print(f"[cyan]🎯 Smart navigation: Trying UI clicking first...[/cyan]")
                if self.navigate_to_clusters_list():
                    if self.click_cluster(cluster_name):
                        if tab:
                            if self.navigate_to_tab(tab):
                                console.print(f"[green]✅ UI navigation successful[/green]")
                                return True
                        else:
                            console.print(f"[green]✅ UI navigation successful[/green]")
                            return True
                
                # Strategy 2: Direct URL fallback
                console.print(f"[yellow]⚠️  UI navigation failed, trying direct URL...[/yellow]")
                if self.navigate_to_cluster_direct(cluster_id=cluster_name, tab=tab, is_cluster=True):
                    console.print(f"[green]✅ URL fallback successful[/green]")
                    return True
                
                console.print(f"[red]❌ Both UI and URL navigation failed[/red]")
                return False
        
        except Exception as e:
            console.print(f"[red]❌ Smart navigation failed: {e}[/red]")
            return False
    
    def list_available_clusters(self) -> list:
        """List all available clusters on current page"""
        try:
            console.print("[cyan]📋 Listing available clusters...[/cyan]")
            
            # Use JavaScript to extract cluster names
            javascript = """
            var clusters = [];
            var rows = document.querySelectorAll('tbody tr, tr[role="row"]');
            
            for (let row of rows) {
                var text = row.textContent.trim();
                if (text && text.length > 0) {
                    // Get first cell (usually cluster name)
                    var cells = row.querySelectorAll('td, [role="gridcell"]');
                    if (cells.length > 0) {
                        var clusterName = cells[0].textContent.trim();
                        if (clusterName && clusterName.length > 0) {
                            clusters.push(clusterName);
                        }
                    }
                }
            }
            return clusters.slice(0, 20);  // Return first 20
            """
            
            clusters = self.tool.driver.execute_script(javascript)
            
            if clusters:
                console.print(f"[green]✅ Found {len(clusters)} clusters[/green]")
                for i, cluster in enumerate(clusters, 1):
                    console.print(f"   {i}. {cluster}")
                return clusters
            else:
                console.print("[yellow]⚠️  No clusters found in table[/yellow]")
                return []
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to list clusters: {e}[/yellow]")
            return []
    
    def navigate_to_tab(self, tab_name: str) -> bool:
        """Navigate to cluster tab (Configuration, Backups, Monitoring, etc.)"""
        try:
            console.print(f"[cyan]📑 Navigating to '{tab_name}' tab[/cyan]")
            
            # Content anchors - text that should appear when tab loads successfully
            content_anchors = {
                'Configuration': ['Parameter group', 'Resource ID', 'Engine version', 'DB cluster parameter group'],
                'Connectivity & security': ['Endpoint', 'Security group', 'VPC', 'Subnet group'],
                'Monitoring': ['CloudWatch', 'Metrics', 'Performance Insights'],
                'Logs & events': ['Recent events', 'Logs', 'Event subscriptions'],
                'Maintenance & backups': ['Backup retention', 'Auto minor version upgrade', 'Maintenance window', 'Backup', 'Snapshot']
            }
            
            # Common tab selectors
            tab_selectors = [
                f"//div[@role='tab'][contains(text(), '{tab_name}')]",
                f"//button[@role='tab'][contains(text(), '{tab_name}')]",
                f"//a[contains(text(), '{tab_name}')]",
                f"//div[contains(text(), '{tab_name}')][contains(@class, 'tab')]",
                f"//span[contains(text(), '{tab_name}')][ancestor::*[contains(@class, 'tab')]]",
                # Case-insensitive variants
                f"//div[@role='tab'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{tab_name.lower()}')]",
                f"//button[@role='tab'][contains(translate(., 'ABCDEFGHIJKLMNOPQRSTUVWXYZ', 'abcdefghijklmnopqrstuvwxyz'), '{tab_name.lower()}')]",
            ]
            
            for selector in tab_selectors:
                if self.tool.click_element(selector, ClickStrategy.JAVASCRIPT, f"tab '{tab_name}'", wait_before=False):
                    console.print(f"[cyan]⏳ Waiting for tab content to load...[/cyan]")
                    time.sleep(2)
                    
                    # Wait for content anchors to confirm tab loaded
                    anchors = content_anchors.get(tab_name, [])
                    if anchors:
                        content_found = False
                        for anchor in anchors:
                            try:
                                # Check if anchor text appears in page
                                if anchor.lower() in self.tool.driver.page_source.lower():
                                    console.print(f"[green]✅ Tab content verified (found: {anchor})[/green]")
                                    content_found = True
                                    break
                            except:
                                pass
                        
                        if not content_found:
                            console.print(f"[yellow]⚠️  Tab clicked but content not loaded yet, waiting...[/yellow]")
                            time.sleep(5)  # Give more time for slow AWS console
                    
                    self.current_tab = tab_name
                    console.print(f"[green]✅ Tab '{tab_name}' navigation complete[/green]")
                    return True
            
            console.print(f"[yellow]⚠️  Could not find or click tab '{tab_name}'[/yellow]")
            return False
        
        except Exception as e:
            console.print(f"[red]❌ Tab navigation failed: {e}[/red]")
            return False
    
    def list_available_tabs(self) -> list:
        """List all available tabs on current page"""
        try:
            console.print("[cyan]📋 Listing available tabs...[/cyan]")
            
            javascript = """
            var tabs = [];
            var tabElements = document.querySelectorAll('[role="tab"], .tab, [class*="Tab"]');
            
            for (let elem of tabElements) {
                var text = elem.textContent.trim();
                if (text && text.length > 0 && text.length < 50) {
                    if (!tabs.includes(text)) {
                        tabs.push(text);
                    }
                }
            }
            return tabs;
            """
            
            tabs = self.tool.driver.execute_script(javascript)
            
            if tabs:
                console.print(f"[green]✅ Found {len(tabs)} tabs[/green]")
                for i, tab in enumerate(tabs, 1):
                    console.print(f"   {i}. {tab}")
                return tabs
            else:
                console.print("[yellow]⚠️  No tabs found[/yellow]")
                return []
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to list tabs: {e}[/yellow]")
            return []
    
    def get_cluster_details(self) -> dict:
        """Extract cluster details from page"""
        try:
            console.print("[cyan]📊 Extracting cluster details...[/cyan]")
            
            javascript = """
            var details = {
                cluster_name: null,
                status: null,
                engine: null,
                instances: null,
                region: null,
                availability_zones: null,
                backup_retention: null,
                encryption: null,
            };
            
            // Try to extract from various page elements
            var pageText = document.body.innerText;
            
            // Status
            var statusMatch = pageText.match(/Status[:\\s]+(Available|Creating|Deleting|Failed|Modifying|Rebooting|Restoring)/i);
            if (statusMatch) details.status = statusMatch[1];
            
            // Engine
            var engineMatch = pageText.match(/Engine[:\\s]+(aurora|aurora-mysql|aurora-postgresql|mysql|postgresql|mariadb|oracle|sqlserver)/i);
            if (engineMatch) details.engine = engineMatch[1];
            
            // Backup retention
            var backupMatch = pageText.match(/Backup retention period[:\\s]+(\d+)\s*days?/i);
            if (backupMatch) details.backup_retention = backupMatch[1] + " days";
            
            // Encryption
            if (pageText.includes('Encryption') && pageText.includes('Enabled')) {
                details.encryption = "Enabled";
            }
            
            return details;
            """
            
            details = self.tool.driver.execute_script(javascript)
            
            console.print("[green]✅ Details extracted[/green]")
            
            # Print extracted details
            for key, value in details.items():
                if value:
                    console.print(f"   {key}: {value}")
            
            return details
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Failed to extract details: {e}[/yellow]")
            return {}
    
    def capture_cluster_screenshot(self, cluster_name: str, tab: Optional[str] = None, use_smart_navigation: bool = True, **kwargs) -> Optional[str]:
        """Capture screenshot of cluster (optionally with tab)

        Supports PARTIAL cluster names! E.g., "conure" will find "prod-conure-aurora-cluster"
        
        Uses HUMAN-LIKE browsing:
        1. Navigate to databases list
        2. Find cluster by partial name
        3. Click on cluster
        4. Click tab
        5. Take screenshot
        
        Args:
            cluster_name: Full or PARTIAL cluster name (e.g., "conure", "prod", etc.)
            tab: Optional tab name (e.g., 'Configuration', 'Maintenance & backups')
            use_smart_navigation: If True, uses browsing-first approach. If False, tries direct URL.

        Extended to accept and ignore legacy kwargs (output_dir, custom_filename) so that
        callers passing these do not raise TypeError. The UniversalScreenshotEnhanced tool
        already embeds timestamp/label; evidence manager assigns final filename.
        """
        try:
            console.print(f"[bold cyan]📸 Capturing cluster screenshot (INTELLIGENT approach!)[/bold cyan]")
            console.print(f"[cyan]   Searching for cluster: '{cluster_name}'[/cyan]")
            if tab:
                console.print(f"[cyan]   Tab: {tab}[/cyan]")

            # STEP 0: Use AWS SDK to find full cluster name (INTELLIGENT!)
            full_cluster_name = cluster_name
            if self.aws_helper:
                console.print(f"[bold green]🧠 Using AWS SDK for intelligent cluster discovery...[/bold green]")
                cluster_info = self.aws_helper.find_cluster_by_partial_name(cluster_name)
                if cluster_info:
                    full_cluster_name = cluster_info['cluster_id']
                    console.print(f"[green]✅ AWS SDK found cluster: '{full_cluster_name}'[/green]")
                    console.print(f"[dim]   Engine: {cluster_info.get('engine')}, Status: {cluster_info.get('status')}[/dim]")
                else:
                    console.print(f"[yellow]⚠️  AWS SDK couldn't find cluster, will try browser search...[/yellow]")
            else:
                console.print(f"[dim]AWS SDK not available, using browser search only...[/dim]")

            # STEP 0.5: Reuse existing cluster view when already on the desired page
            reuse_existing_view = False
            normalized_target = (full_cluster_name or cluster_name or "").lower()

            if self.tool and self.tool.driver:
                try:
                    current_url = (self.tool.driver.current_url or "").lower()
                    if "console.aws.amazon.com/rds/home" in current_url and "#database:id=" in current_url:
                        if normalized_target and normalized_target in current_url:
                            reuse_existing_view = True
                        else:
                            try:
                                page_source_lower = (self.tool.driver.page_source or "").lower()
                            except Exception:
                                page_source_lower = ""
                            if normalized_target and normalized_target in page_source_lower:
                                reuse_existing_view = True
                            elif not normalized_target and cluster_name and cluster_name.lower() in page_source_lower:
                                reuse_existing_view = True

                    if not reuse_existing_view and self.current_cluster:
                        current_known = (self.current_cluster or "").lower()
                        if normalized_target and (normalized_target in current_known or current_known in normalized_target):
                            reuse_existing_view = True
                except Exception as reuse_error:
                    console.print(f"[yellow]⚠️  Reuse detection warning: {reuse_error}")

            if reuse_existing_view:
                console.print("[bold green]🔁 Reusing active RDS cluster view within existing browser session[/bold green]")
                if full_cluster_name:
                    self.current_cluster = full_cluster_name
                elif self.current_cluster:
                    full_cluster_name = self.current_cluster
                else:
                    self.current_cluster = cluster_name

                if not full_cluster_name or not full_cluster_name.strip():
                    try:
                        header_text = self.tool.driver.execute_script("""
                            return (function(){
                                const header = document.querySelector("[data-testid='database-header']") ||
                                                document.querySelector('h1, h2');
                                if (!header) { return ''; }
                                return (header.innerText || header.textContent || '').split('\n')[0].trim();
                            })();
                        """) or ""
                        if header_text:
                            full_cluster_name = header_text
                            self.current_cluster = header_text
                    except Exception:
                        pass

                # Make sure we're back at the top before switching tabs or capturing
                try:
                    self.tool.driver.execute_script("window.scrollTo(0, 0);")
                except Exception:
                    pass

                if tab:
                    desired_tab_lower = tab.lower()
                    if self.current_tab and self.current_tab.lower() == desired_tab_lower:
                        console.print(f"[green]✅ Already on tab '{tab}'[/green]")
                        time.sleep(1)
                    else:
                        from tools.aws_tab_navigator import AWSTabNavigator

                        tab_navigator = AWSTabNavigator(self.tool.driver)
                        if tab_navigator.find_and_click_tab(tab):
                            self.current_tab = tab
                            console.print(f"[green]✅ Successfully clicked tab '{tab}'[/green]")
                            time.sleep(2)
                        else:
                            console.print(f"[yellow]⚠️  Tab '{tab}' not found, capturing current view[/yellow]")
                else:
                    console.print("[dim]No tab requested; capturing the current view as-is.[/dim]")
            else:
                # STEP 1: Navigate to databases list
                console.print("[cyan]Step 1: Navigating to RDS databases list...[/cyan]")
                if not self.navigate_to_clusters_list():
                    console.print("[red]❌ Failed to navigate to databases list[/red]")
                    return None

                # Wait for list to load
                time.sleep(3)

                # STEP 2: Find and click cluster (now using FULL name if SDK found it!)
                console.print(f"[cyan]Step 2: Finding and clicking cluster '{full_cluster_name}'...[/cyan]")
                if not self.click_cluster(full_cluster_name, partial_match=True):
                    console.print(f"[red]❌ Could not find or click cluster '{full_cluster_name}'[/red]")
                    return None

                # Wait for cluster details to load
                time.sleep(3)

                # Step 3: Click tab if specified
                if tab:
                    console.print(f"[cyan]Step 3: Clicking tab '{tab}' (HUMAN-LIKE!)[/cyan]")
                    from tools.aws_tab_navigator import AWSTabNavigator

                    tab_navigator = AWSTabNavigator(self.tool.driver)
                    if tab_navigator.find_and_click_tab(tab):
                        self.current_tab = tab
                        console.print(f"[green]✅ Successfully clicked tab '{tab}'[/green]")
                        time.sleep(2)  # Wait for tab content to load
                    else:
                        console.print(f"[yellow]⚠️  Tab '{tab}' not found, capturing current view[/yellow]")

            # Step 4: Capture screenshot
            console.print("[cyan]Step 4: Capturing screenshot...[/cyan]")
            label_base = (full_cluster_name or cluster_name or "RDS")
            label = f"RDS_{label_base}_{tab}" if tab else f"RDS_{label_base}"
            screenshot_path = self.tool.capture_screenshot(label)
            
            if screenshot_path:
                console.print(f"[green]✅ Screenshot saved: {screenshot_path}[/green]")
                return screenshot_path
            else:
                console.print("[red]❌ Screenshot capture failed[/red]")
                return None
        
        except Exception as e:
            console.print(f"[red]❌ Screenshot capture failed: {e}[/red]")
            return False

    # Backwards compatibility shim (accept legacy keyword args)
    def capture_cluster_screenshot_compat(self, *args, **kwargs):  # pragma: no cover
        return self.capture_cluster_screenshot(*args, **{k: v for k, v in kwargs.items() if k in ('cluster_name','tab')})
    
    def get_status(self) -> dict:
        """Get current navigation status"""
        return {
            'current_cluster': self.current_cluster,
            'current_tab': self.current_tab,
            'region': self.region,
            'current_url': self.tool.get_current_url(),
        }
    
    def _navigate_to_tab_via_url(self, cluster_id: str, tab: str, is_cluster: bool = True) -> bool:
        """
        Fallback method: Navigate to tab using URL hash fragment.
        
        Only used if clicking fails. URL method is less reliable but can work as fallback.
        
        Args:
            cluster_id: Cluster identifier
            tab: Tab name
            is_cluster: True for clusters
        
        Returns:
            True if successful
        """
        console.print(f"[yellow]🔄 Using URL fallback for tab '{tab}'...[/yellow]")
        
        # Normalize tab name to AWS URL format
        tab_mapping = {
            'configuration': 'configuration',
            'config': 'configuration',
            'maintenance & backups': 'maintenance-and-backups',
            'maintenance and backups': 'maintenance-and-backups',
            'maintenance': 'maintenance-and-backups',
            'backup': 'maintenance-and-backups',
            'backups': 'maintenance-and-backups',
            'monitoring': 'monitoring',
            'logs & events': 'logs-and-events',
            'logs and events': 'logs-and-events',
            'logs': 'logs-and-events',
            'connectivity & security': 'connectivity-and-security',
            'connectivity and security': 'connectivity-and-security',
            'connectivity': 'connectivity-and-security',
            'security': 'connectivity-and-security',
        }
        
        tab_normalized = tab_mapping.get(tab.lower(), tab.lower().replace(' ', '-').replace('&', 'and'))
        
        hash_fragment = f"#database:id={cluster_id}"
        if is_cluster:
            hash_fragment += ";is-cluster=true"
        hash_fragment += f";tab={tab_normalized}"
        
        url = f"https://{self.region}.console.aws.amazon.com/rds/home?region={self.region}{hash_fragment}"
        
        console.print(f"[dim]Fallback URL: {url}[/dim]")
        return self.tool.navigate_to_url(url)


# Convenience function
def create_rds_navigator(screenshot_tool: UniversalScreenshotEnhanced) -> RDSNavigatorEnhanced:
    """Create and return RDS navigator"""
    return RDSNavigatorEnhanced(screenshot_tool)


if __name__ == "__main__":
    # Example usage
    from tools.universal_screenshot_enhanced import UniversalScreenshotEnhanced
    
    console.print("[cyan]Testing RDS Navigator...[/cyan]")
    
    tool = UniversalScreenshotEnhanced(headless=False)
    
    if tool.connect():
        navigator = RDSNavigatorEnhanced(tool)
        
        # Will need to authenticate to AWS first
        if navigator.navigate_to_clusters_list():
            clusters = navigator.list_available_clusters()
            
            if clusters:
                # Try to navigate to first cluster
                first_cluster = clusters[0]
                if navigator.navigate_to_cluster_direct(first_cluster):
                    tabs = navigator.list_available_tabs()
                    details = navigator.get_cluster_details()
                    navigator.capture_cluster_screenshot(first_cluster)
        
        tool.close()
