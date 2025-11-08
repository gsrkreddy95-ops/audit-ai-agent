"""
SharePoint Browser Integration
Uses Playwright to access SharePoint with existing browser session (no app registration needed)
"""

import os
import json
import time
from typing import List, Dict, Optional
from pathlib import Path
from datetime import datetime
from playwright.sync_api import sync_playwright, Browser, Page
from rich.console import Console
from dotenv import load_dotenv
from .browser_intelligence import BrowserIntelligence

console = Console()

# Load environment variables
load_dotenv()


class SharePointBrowserAccess:
    """
    Access SharePoint using browser automation with existing user session
    No app registration or client secrets needed!
    """
    
    def __init__(self, headless: bool = False, llm=None):
        self.headless = headless
        self.playwright = None
        self.browser = None
        self.page = None
        self.llm = llm
        self.intelligence = None  # Will be initialized after page is ready
        
        # SharePoint config from env
        self.site_url = os.getenv('SHAREPOINT_SITE_URL')
        self.doc_library = os.getenv('SHAREPOINT_DOC_LIBRARY', 'Shared Documents')
        self.base_path = os.getenv('SHAREPOINT_BASE_PATH')
        
        # Browser selection (firefox avoids Chrome update prompts)
        self.browser_type = os.getenv('SHAREPOINT_BROWSER', 'firefox')  # 'firefox' or 'chromium'
        
        # Browser user data directory for persistent session
        self.user_data_dir = os.path.expanduser('~/.audit-agent-browser')
    
    def connect(self, use_existing_session: bool = True) -> bool:
        """
        Launch browser and navigate to SharePoint
        
        Args:
            use_existing_session: Use persistent profile (stays logged in between sessions)
        
        Returns:
            True if connected successfully
        """
        try:
            console.print("[cyan]🌐 Launching browser for SharePoint access...[/cyan]")
            
            self.playwright = sync_playwright().start()
            
            # Select browser engine
            if self.browser_type == 'firefox':
                browser_engine = self.playwright.firefox
                console.print("[cyan]🦊 Using Firefox browser (no update prompts!)[/cyan]")
            else:
                browser_engine = self.playwright.chromium
                console.print("[cyan]🌐 Using Chromium browser[/cyan]")
            
            if use_existing_session:
                # Use persistent profile (stays logged in between sessions)
                console.print("[cyan]📱 Using audit agent browser profile...[/cyan]")
                console.print("[yellow]💡 If you see a login page, log in once - your session will be saved[/yellow]\n")
                
                # Launch browser with persistent context
                if self.browser_type == 'firefox':
                    # Firefox persistent context
                    self.browser = browser_engine.launch_persistent_context(
                        user_data_dir=self.user_data_dir,
                        headless=self.headless,
                        firefox_user_prefs={
                            # Download settings
                            "browser.download.folderList": 2,
                            "browser.helperApps.neverAsk.saveToDisk": "application/octet-stream",
                            # Disable all Firefox updates
                            "app.update.enabled": False,
                            "app.update.auto": False,
                            "app.update.checkInstallTime": False,
                            "app.update.disabledForTesting": True,
                            # Disable update notifications
                            "app.update.silent": True,
                            "app.update.doorhanger": False,
                            # Disable background update checks
                            "app.update.background.enabled": False,
                            "browser.startup.homepage_override.mstone": "ignore"
                        }
                    )
                else:
                    # Chromium persistent context
                    self.browser = browser_engine.launch_persistent_context(
                        user_data_dir=self.user_data_dir,
                        headless=self.headless,
                        args=['--disable-blink-features=AutomationControlled']
                    )
                
                self.page = self.browser.pages[0] if self.browser.pages else self.browser.new_page()
            else:
                # New browser session (will require login every time)
                self.browser = browser_engine.launch(headless=self.headless)
                self.page = self.browser.new_page()
            
            # Listen to console messages from the browser for debugging
            self.page.on("console", lambda msg: console.print(f"[dim cyan]🔍 Browser: {msg.text}[/dim cyan]"))
            
            # Navigate to SharePoint
            console.print(f"[cyan]🔗 Navigating to: {self.site_url}[/cyan]")
            
            try:
                self.page.goto(self.site_url, timeout=60000)
            except Exception as e:
                console.print(f"[red]❌ Navigation failed: {e}[/red]")
                return False
            
            # Wait for SharePoint to load
            time.sleep(3)
            
            # Check if we're on SharePoint (not login page)
            current_url = self.page.url
            console.print(f"[dim]Current URL: {current_url}[/dim]")
            
            if 'login.microsoftonline.com' in current_url or 'cisco.okta.com' in current_url or 'sso.cisco.com' in current_url or 'login' in current_url:
                console.print("[yellow]⚠️  Login required. Please log in manually in the browser...[/yellow]")
                console.print("[yellow]💡 Complete Cisco SSO/Okta authentication[/yellow]")
                console.print("[yellow]⏳ Waiting for login to complete (120 seconds)...[/yellow]")
                console.print(f"[dim]💡 Tip: If session expired, you may need to re-authenticate[/dim]")
                
                # Wait for user to log in
                try:
                    self.page.wait_for_url(lambda url: 'sharepoint.com' in url and 'login' not in url, timeout=120000)
                    console.print("[green]✅ Login successful![/green]")
                    time.sleep(2)  # Give SharePoint time to fully load
                except Exception as e:
                    console.print(f"[yellow]⚠️  Login timeout or still on login page[/yellow]")
                    console.print(f"[yellow]Current URL: {self.page.url}[/yellow]")
                    console.print(f"[yellow]💡 Try running: ./clear_browser_cache.sh[/yellow]")
            
            # Verify we're on SharePoint
            current_url = self.page.url
            if 'sharepoint.com' in current_url:
                console.print("[green]✅ Connected to SharePoint![/green]")
                
                # Initialize browser intelligence if LLM is available
                if self.llm and self.page:
                    console.print("[cyan]🧠 Initializing browser intelligence layer...[/cyan]")
                    try:
                        self.intelligence = BrowserIntelligence(self.llm, self.page)
                        console.print("[green]✓ Browser intelligence active - agent can now think and adapt![/green]")
                    except Exception as intel_err:
                        console.print(f"[yellow]⚠️  Intelligence layer init failed: {intel_err}[/yellow]")
                
                return True
            else:
                console.print(f"[yellow]⚠️  Not on SharePoint yet: {current_url}[/yellow]")
                console.print(f"[yellow]💡 If you see a login page, please complete authentication[/yellow]")
                # Give user a chance to authenticate if browser is visible
                if not self.headless:
                    console.print(f"[yellow]⏳ Waiting 30 more seconds for manual authentication...[/yellow]")
                    time.sleep(30)
                    current_url = self.page.url
                    if 'sharepoint.com' in current_url:
                        console.print("[green]✅ Now connected to SharePoint![/green]")
                        return True
                    else:
                        console.print(f"[red]❌ Still not on SharePoint: {current_url}[/red]")
                        console.print(f"[yellow]💡 Session may have expired. Run: ./clear_browser_cache.sh[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Failed to connect: {e}[/red]")
            return False
    
    def navigate_to_path(self, relative_path: str) -> bool:
        """
        Navigate to specific folder path in SharePoint

        Args:
            relative_path: Path like "TD&R Evidence Collection/FY2024"

        Returns:
            True if navigation successful
        """
        try:
            # Construct full SharePoint URL
            base_url = self.site_url.rstrip('/')
            
            # Encode doc library and relative path
            import urllib.parse
            
            # Split the relative path into components
            path_components = [self.doc_library] + relative_path.split('/')
            
            # Encode each component separately
            encoded_components = [urllib.parse.quote(component) for component in path_components]
            
            # Join the encoded components
            encoded_path = '/'.join(encoded_components)
            
            folder_url = f"{base_url}/{encoded_path}"

            console.print(f"[cyan]📁 Navigating to: {relative_path}...[/cyan]")
            console.print(f"[dim]🔗 Full URL: {folder_url}[/dim]")

            try:
                self.page.goto(folder_url, timeout=30000)
            except Exception as e:
                console.print(f"[red]❌ Failed to navigate to folder: {e}[/red]")
                console.print(f"[yellow]💡 This could be a network issue or authentication problem[/yellow]")
                return False
            
            time.sleep(2)

            # Check current URL
            current_url = self.page.url
            console.print(f"[dim]📍 Actual URL after navigation: {current_url}[/dim]")
            
            # Check if we got redirected to login (highest priority check)
            if 'login.microsoftonline.com' in current_url or 'cisco.okta.com' in current_url or 'sso.cisco.com' in current_url or 'login' in current_url:
                console.print(f"[yellow]⚠️  Session expired! Authentication required for folder access[/yellow]")
                console.print(f"[yellow]💡 Please complete Cisco SSO/Okta authentication in the browser[/yellow]")
                console.print(f"[yellow]⏳ Waiting for login (120 seconds)...[/yellow]")
                console.print(f"[dim]💡 If this keeps happening, run: ./clear_browser_cache.sh[/dim]")
                
                try:
                    self.page.wait_for_url(lambda url: 'sharepoint.com' in url and 'login' not in url, timeout=120000)
                    console.print("[green]✅ Authentication complete! Trying navigation again...[/green]")
                    
                    # Try navigation again after authentication
                    self.page.goto(folder_url, timeout=30000)
                    time.sleep(2)
                    current_url = self.page.url
                    console.print(f"[dim]📍 URL after re-authentication: {current_url}[/dim]")
                except Exception as e:
                    console.print(f"[red]❌ Authentication failed or timed out: {e}[/red]")
                    console.print(f"[yellow]💡 Try: ./clear_browser_cache.sh and restart agent[/yellow]")
                    return False
            
            # Check if we're on an error page (URL-based check)
            if 'error' in current_url.lower() or 'accessdenied' in current_url.lower():
                console.print(f"[yellow]⚠️  Cannot access folder: {relative_path}[/yellow]")
                console.print(f"[yellow]💡 You may not have permissions or the folder doesn't exist[/yellow]")
                return False

            # SUCCESS CHECK: Check if we're on a valid SharePoint folder page (URL-based, most reliable)
            # SharePoint redirects to Forms/AllItems.aspx with folder ID in query params when folder exists
            import urllib.parse
            decoded_url = urllib.parse.unquote(current_url)
            
            # Extract the last part of the relative path (e.g., "BCR-06.01" from "FY2025/XDR Platform/BCR-06.01")
            path_parts = relative_path.split('/')
            folder_name = path_parts[-1] if path_parts else ''
            
            if 'sharepoint.com' in current_url:
                # Check multiple SharePoint URL patterns
                if 'Forms/AllItems.aspx' in current_url or '/Forms/' in current_url or folder_name in decoded_url:
                    # If the folder name appears in the decoded URL, we're definitely on the right page
                    if folder_name and folder_name in decoded_url:
                        console.print("[green]✅ Navigation successful![/green]")
                        console.print(f"[dim]✅ Confirmed: Folder '{folder_name}' found in URL[/dim]")
                        return True
                    else:
                        # We're on a SharePoint document library view
                        console.print("[green]✅ Navigation to SharePoint folder view successful[/green]")
                        console.print(f"[dim]💡 On document library view - folder may be empty or at parent level[/dim]")
                        return True
            
            # FALLBACK: Only check page content if URL checks were inconclusive
            try:
                page_content = self.page.content().lower()
            except Exception as e:
                console.print(f"[yellow]⚠️  Could not read page content: {e}[/yellow]")
                page_content = ""
            
            # Check for explicit 404 or error pages (page content check as last resort)
            if '404' in page_content or 'file not found' in page_content:
                console.print(f"[yellow]⚠️  Folder not found: {relative_path}[/yellow]")
                console.print(f"[yellow]💡 This RFI may not exist in the previous year, or the path structure is different[/yellow]")
                return False
            
            # If we get here, we're on SharePoint but not sure if it's the right place
            console.print(f"[yellow]⚠️  Unexpected navigation result[/yellow]")
            console.print(f"[yellow]Current URL: {current_url}[/yellow]")
            console.print(f"[yellow]💡 Folder may not exist or path may be incorrect[/yellow]")
            return False

        except Exception as e:
            console.print(f"[yellow]⚠️  Navigation failed: {e}[/yellow]")
            console.print(f"[yellow]💡 Folder likely doesn't exist: {relative_path}[/yellow]")
            return False
    
    def list_folder_contents(self, folder_path: Optional[str] = None) -> List[Dict]:
        """
        List files and folders in current SharePoint location
        
        Args:
            folder_path: Optional path to navigate to first
        
        Returns:
            List of dicts with {name, type, modified, url}
        """
        try:
            if folder_path:
                if not self.navigate_to_path(folder_path):
                    return []
            
            console.print("[cyan]📂 Reading folder contents...[/cyan]")
            
            # Wait for SharePoint list to load
            try:
                self.page.wait_for_selector('[role="row"]', timeout=10000)
                time.sleep(3)  # Increased delay for content to render
                
                # Additional wait for actual content (not just structure)
                self.page.wait_for_selector('[role="gridcell"]', timeout=5000)
                time.sleep(2)  # Extra time for dynamic content
                
                console.print("[dim]SharePoint list loaded, extracting files...[/dim]")
            except:
                console.print("[yellow]⚠️  List not loaded yet, waiting longer...[/yellow]")
                time.sleep(5)
            
            # New robust extraction using anchor hrefs and filtering out internal row-selection markers
            items = []
            rows = self.page.query_selector_all('[role="row"]')
            console.print(f"[dim]Found {len(rows)} rows to process...[/dim]\n[dim]🔍 Extracting file & folder entries...[/dim]")

            # Use a raw triple-quoted string to avoid Python escape sequence warnings (e.g., \.)
            items_js = self.page.evaluate(r"""
                () => {
                    const EXT_REGEX = /\.(pdf|png|jpg|jpeg|xlsx|xls|csv|docx|pptx|ppt|txt|json|zip|tar|log|gif|bmp|mp4|avi|mov)$/i;
                    const SKIP_REGEX = /^row-selection(-header)?$|^row-selection-\d+$/i;
                    const HEADER_NAMES = ['Name','Modified','Modified By','Sharing','File Type','Size','Type'];
                    const results = [];
                    const seen = new Set();
                    const rows = document.querySelectorAll('[role="row"]');
                    const params = new URLSearchParams(window.location.search || '');
                    const folderIdRaw = params.get('id') || '';
                    
                    // Build proper base URL from current page location
                    // The 'id' parameter contains the server-relative path, e.g.:
                    // /sites/SPRSecurityTeam/Shared Documents/TD&R Documentation Train 5/TD&R Evidence Collection/FY2025/XDR Platform/BCR-06.01
                    let baseDownloadUrl = '';
                    if (folderIdRaw) {
                        // Simply combine origin with the server-relative folder path
                        const origin = window.location.origin;  // https://cisco.sharepoint.com
                        // Ensure folder path starts with /
                        const folderPath = folderIdRaw.startsWith('/') ? folderIdRaw : '/' + folderIdRaw;
                        baseDownloadUrl = origin + folderPath;
                        console.log('[SharePoint Extraction] Base download URL: ' + baseDownloadUrl.substring(0, 120));
                    } else {
                        console.log('[SharePoint Extraction] WARNING: No folder ID found in URL params');
                    }

                    console.log('[SharePoint Extraction] Found ' + rows.length + ' rows');

                    rows.forEach((row, idx) => {
                        try {
                            if (idx < 3) {
                                try {
                                    const attrSummary = Array.from(row.attributes || []).map(a => `${a.name}=${a.value}`).join('; ');
                                    console.log(`[SharePoint Extraction] Row ${idx} attributes: ${attrSummary}`);
                                    console.log(`[SharePoint Extraction] Row ${idx} dataset: ${JSON.stringify(row.dataset || {})}`);
                                } catch (attrErr) {
                                    console.log(`[SharePoint Extraction] Failed to log attributes for row ${idx}: ${attrErr}`);
                                }
                            }
                            // Try multiple cell selector strategies
                            let cells = row.querySelectorAll('[role="gridcell"]');
                            if (cells.length === 0) {
                                cells = row.querySelectorAll('[role="cell"]');
                            }
                            if (cells.length === 0) {
                                cells = row.querySelectorAll('td');
                            }
                            if (cells.length === 0) {
                                console.log('[SharePoint Extraction] Row ' + idx + ' has no cells, skipping');
                                return;
                            }

                            console.log('[SharePoint Extraction] Processing row ' + idx + ', cells found: ' + cells.length);

                            // SharePoint structure: Cell 0 = checkbox, Cell 1 = icon, Cell 2 = file name, Cell 3+ = metadata
                            // We need to look at cell index 2 for the actual file name
                            let nameCell = null;
                            
                            // If first cell is checkbox, try cell 2 (icon is cell 1)
                            if (cells[0].querySelector('input[type="checkbox"][data-automationid="selection-checkbox"]')) {
                                if (cells.length > 2) {
                                    nameCell = cells[2];
                                } else if (cells.length > 1) {
                                    nameCell = cells[1];
                                } else {
                                    console.log('[SharePoint Extraction] Row ' + idx + ' only has checkbox cell, skipping');
                                    return;
                                }
                            } else {
                                // No checkbox, try cell 1 or 0
                                nameCell = cells.length > 1 ? cells[1] : cells[0];
                            }

                            // DEBUG: Log name cell HTML to see structure
                            console.log('[SharePoint Extraction] Name cell (index=' + Array.from(cells).indexOf(nameCell) + ') HTML preview: ' + nameCell.innerHTML.substring(0, 400));

                            // Strategy 1: Look for button with data-automationid="FieldRenderer-name" (SharePoint specific)
                            let nameButton = nameCell.querySelector('[data-automationid="FieldRenderer-name"]');
                            let link = nameCell.querySelector('a[href]');
                            let name = '';
                            let href = '';

                            console.log('[SharePoint Extraction] nameButton exists: ' + !!nameButton + ', link exists: ' + !!link);

                            // Strategy 1: Look for span with role="button" containing file name (SharePoint modern lists)
                            const fileNameSpan = nameCell.querySelector('span[role="button"][data-id="heroField"]');
                            if (fileNameSpan) {
                                name = (fileNameSpan.innerText || fileNameSpan.textContent || '').trim();
                                console.log('[SharePoint Extraction] Found name from heroField span: "' + name + '"');
                                
                                // Try to find link in same cell or parent row for URL
                                const cellLink = nameCell.querySelector('a[href]');
                                if (cellLink) {
                                    href = cellLink.getAttribute('href') || '';
                                    console.log('[SharePoint Extraction] Found link in cell: ' + href.substring(0, 80));
                                } else {
                                    // Try parent row
                                    const rowLink = row.querySelector('a[href*="' + encodeURIComponent(name) + '"]');
                                    if (rowLink) {
                                        href = rowLink.getAttribute('href') || '';
                                        console.log('[SharePoint Extraction] Found link in row: ' + href.substring(0, 80));
                                    }
                                }
                            }

                            // Strategy 2: Traditional button/link extraction
                            if (!name && nameButton) {
                                name = (nameButton.innerText || nameButton.textContent || '').trim();
                                console.log('[SharePoint Extraction] Found name from button: "' + name + '"');
                            }
                            
                            if (!name && link) {
                                href = link.getAttribute('href') || '';
                                name = (link.innerText || link.textContent || '').trim();
                                console.log('[SharePoint Extraction] Found name from link: "' + name + '" (href: ' + href.substring(0, 80) + ')');
                                
                                // Extract name from URL if text is empty
                                if (!name && href) {
                                    const parts = href.split('/');
                                    name = decodeURIComponent(parts[parts.length - 1].split('?')[0]);
                                    console.log('[SharePoint Extraction] Extracted name from URL: "' + name + '"');
                                }
                            }
                            
                            // Get href if not found yet
                            if (!href) {
                                const anyLink = row.querySelector('a[href]');
                                if (anyLink) {
                                    href = anyLink.getAttribute('href') || '';
                                    console.log('[SharePoint Extraction] Found fallback link: ' + href.substring(0, 80));
                                }
                            }

                            // Strategy 3: Get first significant span text (avoid "More Actions" buttons)
                            if (!name) {
                                const spans = nameCell.querySelectorAll('span[role="button"]');
                                for (let i = 0; i < spans.length; i++) {
                                    const spanText = (spans[i].innerText || spans[i].textContent || '').trim();
                                    if (spanText && spanText !== 'More Actions' && spanText.length > 2) {
                                        name = spanText;
                                        console.log('[SharePoint Extraction] Found name from span[' + i + ']: "' + name + '"');
                                        break;
                                    }
                                }
                            }
                            
                            // Last resort: cell text (filtered)
                            if (!name) {
                                const cellText = (nameCell.innerText || nameCell.textContent || '').trim();
                                // Remove "More Actions" if it appears
                                const cleanText = cellText.replace(/More Actions/g, '').trim();
                                console.log('[SharePoint Extraction] Cell text after cleaning: "' + cleanText.substring(0, 100) + '"');
                                name = cleanText;
                            }

                            // Clean up name
                            name = name.replace(/\n/g, ' ').trim();

                            // Skip if no name or is header
                            if (!name) {
                                console.log('[SharePoint Extraction] Row ' + idx + ' has no name, skipping');
                                return;
                            }
                            if (HEADER_NAMES.includes(name)) {
                                console.log('[SharePoint Extraction] Row ' + idx + ' is header: ' + name);
                                return;
                            }
                            if (SKIP_REGEX.test(name)) {
                                console.log('[SharePoint Extraction] Row ' + idx + ' matches skip pattern: ' + name);
                                return;
                            }

                            // Determine if folder
                            const hasFileExt = EXT_REGEX.test(name) || EXT_REGEX.test(href);
                            const hasFolderIcon = !!row.querySelector('[data-icon-name*="Folder"]') || 
                                                  !!row.querySelector('[class*="folder"]') ||
                                                  !!row.querySelector('i[class*="Folder"]');
                            const isFolder = hasFolderIcon || !hasFileExt;

                            // Build direct download URL if still missing and looks like a file
                            if (!href && !isFolder && name && baseDownloadUrl) {
                                try {
                                    const encodedName = encodeURIComponent(name);
                                    // Build SharePoint file URL: base folder URL + filename
                                    href = baseDownloadUrl + '/' + encodedName;
                                    console.log('[SharePoint Extraction] Built fallback href: ' + href);
                                } catch (buildErr) {
                                    console.log('[SharePoint Extraction] Failed to build fallback href: ' + buildErr);
                                }
                            }
                            
                            // If still no href and we have the file name, try to find it via SharePoint's direct link pattern
                            if (!href && !isFolder && name) {
                                try {
                                    // Try to construct from current location
                                    const siteMatch = window.location.href.match(/(https:\/\/[^\/]+\/sites\/[^\/]+)/);
                                    if (siteMatch && folderIdRaw) {
                                        const encodedName = encodeURIComponent(name);
                                        // Format: https://SITE/sites/SITENAME/FOLDERPATH/FILENAME
                                        href = siteMatch[1] + folderIdRaw + '/' + encodedName;
                                        console.log('[SharePoint Extraction] Built site-based href: ' + href);
                                    }
                                } catch (siteErr) {
                                    console.log('[SharePoint Extraction] Failed to build site href: ' + siteErr);
                                }
                            }

                            // Modified date (cell 3 or 4, after checkbox/icon/name)
                            let modified = 'Unknown';
                            if (cells.length > 3) {
                                const modText = (cells[3].innerText || cells[3].textContent || '').trim();
                                if (modText && !HEADER_NAMES.includes(modText)) modified = modText;
                            }

                            // Avoid duplicates
                            const key = name.toLowerCase() + '|' + href;
                            if (seen.has(key)) {
                                console.log('[SharePoint Extraction] Duplicate detected: ' + name);
                                return;
                            }
                            seen.add(key);

                            console.log('[SharePoint Extraction] ✅ Adding item: ' + name + ' (type: ' + (isFolder ? 'folder' : 'file') + ')');
                            results.push({
                                name: name,
                                type: isFolder ? 'folder' : 'file',
                                modified: modified,
                                url: href || ''
                            });
                        } catch (e) {
                            // swallow errors per row
                        }
                    });
                    return results;
                }
            """)

            if items_js and len(items_js) > 0:
                items = items_js
                console.print(f"[green]✅ Extracted {len(items)} items (filtered)[/green]")
            else:
                console.print("[yellow]⚠️  Extraction returned no usable items[/yellow]")

            # Post-filter: remove any row-selection artifacts if still present
            cleaned = []
            import re
            skip_pat = re.compile(r'^row-selection(-header)?$|^row-selection-\d+$', re.I)
            for it in items:
                if skip_pat.match(it.get('name','')):
                    continue
                cleaned.append(it)
            items = cleaned
            console.print(f"[green]✅ Final items after cleanup: {len(items)}[/green]")
            
            # Debug: If no items found, take screenshot
            if len(items) == 0 and len(rows) > 0:
                try:
                    debug_path = os.path.expanduser('~/Desktop/sharepoint_debug.png')
                    self.page.screenshot(path=debug_path)
                    console.print(f"[yellow]📸 Debug screenshot saved to: {debug_path}[/yellow]")
                    console.print(f"[yellow]💡 This will help diagnose why files aren't showing[/yellow]")
                except:
                    pass
            
            # Print summary
            for item in items:
                icon = "📁" if item['type'] == 'folder' else "📄"
                url_info = item.get('url') or ''
                url_hint = f" (url: {url_info[:60]}...)" if url_info else ""
                console.print(f"  {icon} {item['name']}{url_hint}")
            
            return items
            
        except Exception as e:
            console.print(f"[red]❌ Failed to list contents: {e}[/red]")
            return []
    
    def download_all_files(
        self,
        save_dir: str,
        folder_path: Optional[str] = None,
        recursive: bool = False,
        max_depth: int = 5,
        current_depth: int = 0
    ) -> List[Dict]:
        """
        Download all files from current SharePoint folder
        
        Args:
            save_dir: Local directory to save files
            folder_path: Optional SharePoint folder path to navigate to first
        
        Returns:
            List of dicts with {name, local_path, type, success}
        """
        try:
            # Get file list
            files = self.list_folder_contents(folder_path)
            
            if not files:
                return []
            
            # Create save directory
            os.makedirs(save_dir, exist_ok=True)
            
            downloaded = []
            file_items = [f for f in files if f['type'] == 'file']
            folder_items = [f for f in files if f['type'] == 'folder']
            
            console.print(f"[cyan]📥 Downloading {len(file_items)} files (depth {current_depth})...[/cyan]")
            
            for file_item in file_items:
                file_name = file_item['name']
                file_url = file_item.get('url','')
                local_path = os.path.join(save_dir, file_name)
                
                try:
                    success = self.download_file(file_name, local_path, file_url=file_url)
                    downloaded.append({
                        'name': file_name,
                        'local_path': local_path if success else None,
                        'type': file_item['type'],
                        'success': success
                    })
                    if success:
                        console.print(f"  ✅ {file_name}")
                    else:
                        console.print(f"  ⚠️  Failed: {file_name}")
                except Exception as e:
                    console.print(f"  ❌ Error downloading {file_name}: {e}")
                    downloaded.append({
                        'name': file_name,
                        'local_path': None,
                        'type': file_item['type'],
                        'success': False
                    })
            
            successful = sum(1 for d in downloaded if d['success'])
            console.print(f"[green]✅ Downloaded {successful}/{len(file_items)} files at depth {current_depth}[/green]")

            # Recurse into subfolders if requested
            if recursive and current_depth < max_depth and folder_items:
                console.print(f"[cyan]🔁 Recursing into {len(folder_items)} subfolder(s) (next depth {current_depth+1})...[/cyan]")
                for folder in folder_items:
                    sub_name = folder['name']
                    # Build new relative path
                    new_relative = f"{folder_path.rstrip('/')}/{sub_name}" if folder_path else sub_name
                    sub_save_dir = os.path.join(save_dir, sub_name)
                    try:
                        sub_results = self.download_all_files(
                            save_dir=sub_save_dir,
                            folder_path=new_relative,
                            recursive=True,
                            max_depth=max_depth,
                            current_depth=current_depth + 1
                        )
                        downloaded.extend(sub_results)
                    except Exception as sub_err:
                        console.print(f"[yellow]⚠️  Failed to recurse into '{sub_name}': {sub_err}")
            
            return downloaded
            
        except Exception as e:
            console.print(f"[red]❌ Failed to download files: {e}[/red]")
            return []
    
    def download_file(self, file_name: str, save_path: str, folder_path: Optional[str] = None, file_url: Optional[str] = None) -> bool:
        """
        Download a file from SharePoint
        
        Args:
            file_name: Name of file to download
            save_path: Local path to save file
            folder_path: Optional SharePoint folder path
        
        Returns:
            True if download successful
        """
        try:
            if folder_path:
                if not self.navigate_to_path(folder_path):
                    return False
            
            console.print(f"[cyan]⬇️  Downloading: {file_name}...[/cyan]")

            # Primary method: locate file in DOM and interact with it
            # This is more reliable than URL navigation for SharePoint
            console.print(f"[dim]🔍 Searching for file in DOM...[/dim]")
            
            # Try multiple selectors to find the file
            file_element = None
            
            # Strategy 1: Look for heroField span with exact name
            file_element = self.page.query_selector(f'span[role="button"][data-id="heroField"]:has-text("{file_name}")')
            
            # Strategy 2: Look for link with file name
            if not file_element:
                file_links = self.page.query_selector_all(f'[role="gridcell"] a:has-text("{file_name}")')
                if file_links:
                    file_element = file_links[0]
            
            # Strategy 3: Try partial match (some SharePoint trims display names)
            if not file_element:
                short_name = file_name.split('.')[0]
                file_element = self.page.query_selector(f'span[role="button"][data-id="heroField"]:has-text("{short_name}")')
                if not file_element:
                    file_links = self.page.query_selector_all(f'[role="gridcell"] a:has-text("{short_name}")')
                    if file_links:
                        file_element = file_links[0]
            
            if not file_element:
                console.print(f"[red]❌ File not found in DOM: {file_name}[/red]")
                console.print(f"[yellow]💡 The file may have been moved or permissions may have changed[/yellow]")
                return False

            console.print(f"[dim]✓ Found file element in DOM[/dim]")

            # Helper: close any preview / modal overlay that might block interactions
            def _close_preview_overlay():
                try:
                    # Use intelligent modal handler if available
                    if self.intelligence:
                        if self.intelligence.auto_handle_modals():
                            return
                    
                    # Fallback to manual selectors
                    selectors = [
                        'button[aria-label="Close"]',
                        'button[title="Close"]',
                        '[data-automationid="close"]',
                        'button.ms-Dialog-buttonClose',
                        'div[role="dialog"] button[aria-label="Close"]'
                    ]
                    closed = False
                    for sel in selectors:
                        btn = self.page.query_selector(sel)
                        if btn and btn.is_visible():
                            btn.click()
                            time.sleep(0.5)
                            closed = True
                    # Escape key as final attempt
                    if not closed:
                        self.page.keyboard.press('Escape')
                    if closed:
                        console.print('[dim]🧹 Closed preview overlay[/dim]')
                except Exception as e:
                    console.print(f'[dim]⚠️  Modal close attempt: {e}[/dim]')

            # Method 1: Context menu download (fastest and most reliable)
            # Note: Checkbox selection was causing 30s timeouts, context menu works immediately
            try:
                _close_preview_overlay()
                console.print('[dim]📋 Right-clicking file...[/dim]')
                file_element.click(button='right', timeout=3000)
                time.sleep(0.5)
                download_option = self.page.query_selector('[role="menuitem"]:has-text("Download"), button:has-text("Download")')
                if download_option and download_option.is_visible():
                    console.print('[dim]📥 Clicking Download...[/dim]')
                    try:
                        with self.page.expect_download(timeout=30000) as download_info:
                            download_option.click()
                        download = download_info.value
                        download.save_as(save_path)
                        console.print(f"[green]✅ {file_name}[/green]")
                        _close_preview_overlay()
                        return True
                    except Exception as cm_err:
                        console.print(f"[yellow]⚠️  Download click failed: {cm_err}[/yellow]")
                else:
                    console.print('[yellow]⚠️  Download option not found in menu')
            except Exception as ctx_err:
                console.print(f"[yellow]⚠️  Context menu failed: {ctx_err}")

            # Method 2: Toolbar download (checkbox + toolbar button)
            try:
                parent_row_handle = file_element.evaluate_handle('el => el.closest("[role=row]")')
                checkbox = None
                try:
                    checkbox = parent_row_handle.as_element().query_selector('input[type="checkbox"], div[role="checkbox"]') if parent_row_handle else None
                except Exception:
                    checkbox = None
                if checkbox:
                    console.print('[dim]☑ Trying checkbox selection...[/dim]')
                    checkbox.click(timeout=3000)  # Reduced timeout
                    time.sleep(0.5)
                    _close_preview_overlay()
                    download_button = self.page.query_selector('[data-automationid="downloadCommand"]')
                    if download_button and download_button.is_visible():
                        with self.page.expect_download(timeout=30000) as download_info:
                            download_button.click()
                        download = download_info.value
                        download.save_as(save_path)
                        console.print(f"[green]✅ {file_name}[/green]")
                        _close_preview_overlay()
                        return True
            except Exception as toolbar_err:
                console.print(f"[yellow]⚠️  Toolbar method failed: {toolbar_err}[/yellow]")

            # Method 3: Keyboard fallback
            try:
                console.print('[dim]⌨️ Trying keyboard method...[/dim]')
                file_element.focus(timeout=3000)
                self.page.keyboard.press('Enter')
                time.sleep(0.8)
                _close_preview_overlay()
                download_button = self.page.query_selector('[data-automationid="downloadCommand"]')
                if download_button and download_button.is_visible():
                    with self.page.expect_download(timeout=30000) as download_info:
                        download_button.click()
                    download = download_info.value
                    download.save_as(save_path)
                    console.print(f"[green]✅ {file_name}[/green]")
                    _close_preview_overlay()
                    return True
            except Exception as kb_err:
                console.print(f"[yellow]⚠️  Keyboard method failed: {kb_err}[/yellow]")

            # Final fallback: Try to get href from the element and navigate directly
            try:
                href = None
                if hasattr(file_element, 'get_attribute'):
                    href = file_element.get_attribute('href')
                
                # If file_element doesn't have href, look for a child link
                if not href:
                    parent_row = file_element.evaluate('el => el.closest("[role=row]")')
                    if parent_row:
                        link_in_row = self.page.evaluate('row => row.querySelector("a[href]")?.getAttribute("href")', parent_row)
                        if link_in_row:
                            href = link_in_row
            except Exception as href_err:
                console.print(f"[yellow]⚠️  Could not extract href: {href_err}[/yellow]")
                href = None
            
            if href:
                try:
                    dl_url = href
                    if 'download=1' not in dl_url:
                        sep = '&' if '?' in dl_url else '?'
                        dl_url = f"{dl_url}{sep}download=1"
                    with self.page.expect_download() as download_info:
                        self.page.goto(dl_url)
                    download = download_info.value
                    download.save_as(save_path)
                    console.print(f"[green]✅ Fallback href download succeeded: {file_name}")
                    return True
                except Exception as href_err:
                    console.print(f"[red]❌ Fallback href download failed: {href_err}")
                    return False

            console.print("[red]❌ No download method succeeded")
            return False
                    
        except Exception as e:
            console.print(f"[red]❌ Download failed: {e}[/red]")
            return False
    
    def upload_file(self, local_file_path: str, sharepoint_folder: str) -> bool:
        """
        Upload a file to SharePoint
        
        Args:
            local_file_path: Path to local file
            sharepoint_folder: SharePoint folder path to upload to
        
        Returns:
            True if upload successful
        """
        try:
            if not os.path.exists(local_file_path):
                console.print(f"[red]❌ Local file not found: {local_file_path}[/red]")
                return False
            
            # Navigate to target folder
            if not self.navigate_to_path(sharepoint_folder):
                return False
            
            console.print(f"[cyan]⬆️  Uploading: {os.path.basename(local_file_path)}...[/cyan]")
            
            # Click Upload button
            upload_button = self.page.query_selector('[data-automationid="uploadCommand"]')
            
            if not upload_button:
                console.print("[red]❌ Upload button not found[/red]")
                return False
            
            upload_button.click()
            time.sleep(1)
            
            # Click "Files" option
            files_option = self.page.query_selector('button:has-text("Files")')
            if files_option:
                files_option.click()
                time.sleep(1)
            
            # Set file input
            file_input = self.page.query_selector('input[type="file"]')
            
            if file_input:
                file_input.set_input_files(local_file_path)
                
                # Wait for upload to complete
                console.print("[cyan]⏳ Waiting for upload to complete...[/cyan]")
                time.sleep(5)
                
                # Check if file appears in list
                file_name = os.path.basename(local_file_path)
                uploaded = self.page.query_selector(f'[role="gridcell"]:has-text("{file_name}")')
                
                if uploaded:
                    console.print(f"[green]✅ Upload successful: {file_name}[/green]")
                    return True
                else:
                    console.print("[yellow]⚠️  Upload may have succeeded (file not immediately visible)[/yellow]")
                    return True
            else:
                console.print("[red]❌ File input not found[/red]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Upload failed: {e}[/red]")
            return False
    
    def get_file_metadata(self, file_name: str, folder_path: Optional[str] = None) -> Optional[Dict]:
        """
        Get metadata for a specific file (without downloading it)
        
        Args:
            file_name: Name of the file
            folder_path: Optional folder path
        
        Returns:
            Dict with file metadata {name, size, modified, type, url}
        """
        try:
            items = self.list_folder_contents(folder_path)
            
            for item in items:
                if item['name'] == file_name:
                    return item
            
            console.print(f"[yellow]⚠️  File not found: {file_name}[/yellow]")
            return None
            
        except Exception as e:
            console.print(f"[red]❌ Failed to get metadata: {e}[/red]")
            return None
    
    def close(self):
        """Close browser connection"""
        try:
            if self.page:
                self.page.close()
            if self.browser:
                self.browser.close()
            if self.playwright:
                self.playwright.stop()
            
            console.print("[cyan]🔒 Browser closed[/cyan]")
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Error closing browser: {e}[/yellow]")
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()


# Quick test function
def test_sharepoint_access():
    """Test SharePoint browser access"""
    console.print("\n[bold cyan]🧪 Testing SharePoint Browser Access[/bold cyan]\n")
    
    with SharePointBrowserAccess(headless=False) as sp:
        # Test 1: Navigate to TD&R Evidence Collection
        base_path = "TD&R Documentation Train 5/TD&R Evidence Collection"
        
        if sp.navigate_to_path(base_path):
            console.print("\n[green]✅ Successfully navigated to evidence collection[/green]")
            
            # Test 2: List folders (FY2023, FY2024, FY2025)
            items = sp.list_folder_contents()
            
            # Test 3: Navigate to FY2024
            fy2024_path = f"{base_path}/FY2024"
            if sp.navigate_to_path(fy2024_path):
                console.print("\n[green]✅ Successfully accessed FY2024[/green]")
                
                # List contents
                fy2024_contents = sp.list_folder_contents()
                console.print(f"\n[cyan]📊 FY2024 contains {len(fy2024_contents)} items[/cyan]")
        
        console.print("\n[green]🎉 SharePoint access test complete![/green]")


if __name__ == "__main__":
    test_sharepoint_access()

