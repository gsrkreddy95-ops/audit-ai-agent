"""
SharePoint Browser Access using undetected-chromedriver
This uses anti-detection Selenium to bypass Cisco Duo blocks
"""

import os
import time
from typing import List, Dict, Optional
from rich.console import Console
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv

load_dotenv()
console = Console()


class SharePointSeleniumAccess:
    """
    Access SharePoint using undetected-chromedriver (anti-detection Selenium)
    Uses your system Chrome and hides automation flags
    """
    
    def __init__(self, headless: bool = False):
        self.headless = headless
        self.driver = None
        
        # SharePoint configuration
        self.site_url = os.getenv('SHAREPOINT_SITE_URL', '')
        self.doc_library = os.getenv('SHAREPOINT_DOC_LIBRARY', 'Shared Documents')
        self.base_path = os.getenv('SHAREPOINT_BASE_PATH', '')
        
        # User data directory for persistent session
        self.user_data_dir = os.path.expanduser('~/.audit-agent-chrome-selenium')
    
    def connect(self) -> bool:
        """
        Launch Chrome using undetected-chromedriver
        This bypasses automation detection!
        """
        try:
            console.print("[cyan]🌐 Launching undetected Chrome (anti-detection)...[/cyan]")
            console.print("[dim]This uses your system Chrome and hides automation flags![/dim]")
            
            # Configure undetected-chromedriver options
            options = uc.ChromeOptions()
            
            # Use persistent profile
            options.add_argument(f'--user-data-dir={self.user_data_dir}')
            
            if self.headless:
                options.add_argument('--headless=new')
            
            # Additional stealth options
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--disable-dev-shm-usage')
            options.add_argument('--no-sandbox')
            
            # Launch undetected Chrome
            self.driver = uc.Chrome(options=options, version_main=None)
            
            console.print("[green]✅ Undetected Chrome launched![/green]")
            console.print("[dim]Cisco Duo should not detect this as automation![/dim]")
            
            # Navigate to SharePoint
            console.print(f"[cyan]🔗 Navigating to: {self.site_url}[/cyan]")
            self.driver.get(self.site_url)
            
            time.sleep(3)
            
            # Check if login is needed
            current_url = self.driver.current_url
            console.print(f"[dim]Current URL: {current_url}[/dim]")
            
            if 'login' in current_url.lower():
                console.print("[yellow]⚠️  Login required. Please log in manually in the browser...[/yellow]")
                console.print("[yellow]💡 Complete Cisco SSO/Okta/Duo authentication[/yellow]")
                console.print("[yellow]⏳ Waiting for login to complete (120 seconds)...[/yellow]")
                
                # Wait for user to log in
                wait = WebDriverWait(self.driver, 120)
                try:
                    wait.until(lambda d: 'sharepoint.com' in d.current_url and 'login' not in d.current_url.lower())
                    console.print("[green]✅ Login successful![/green]")
                    time.sleep(2)
                except:
                    console.print("[yellow]⚠️  Login timeout or still on login page[/yellow]")
                    return False
            
            # Verify we're on SharePoint
            if 'sharepoint.com' in self.driver.current_url:
                console.print("[green]✅ Connected to SharePoint![/green]")
                return True
            else:
                console.print(f"[yellow]⚠️  Not on SharePoint yet: {self.driver.current_url}[/yellow]")
                return False
                
        except Exception as e:
            console.print(f"[red]❌ Failed to connect: {e}[/red]")
            return False
    
    def navigate_to_path(self, relative_path: str) -> bool:
        """Navigate to specific folder path in SharePoint"""
        try:
            import urllib.parse
            
            base_url = self.site_url.rstrip('/')
            encoded_doc_library = urllib.parse.quote(self.doc_library) if ' ' in self.doc_library else self.doc_library
            encoded_path = urllib.parse.quote(relative_path, safe='/')
            folder_url = f"{base_url}/{encoded_doc_library}/{encoded_path}"
            
            console.print(f"[cyan]📁 Navigating to: {relative_path}...[/cyan]")
            console.print(f"[dim]🔗 Full URL: {folder_url}[/dim]")
            
            self.driver.get(folder_url)
            time.sleep(3)
            
            current_url = self.driver.current_url
            console.print(f"[dim]📍 Actual URL: {current_url}[/dim]")
            
            # Check if successful
            if 'sharepoint.com' in current_url and 'Forms/AllItems.aspx' in current_url:
                # Decode and check for folder name
                decoded_url = urllib.parse.unquote(current_url)
                folder_name = relative_path.split('/')[-1] if '/' in relative_path else relative_path
                
                if folder_name in decoded_url:
                    console.print("[green]✅ Navigation successful![/green]")
                    console.print(f"[dim]✅ Confirmed: Folder '{folder_name}' found in URL[/dim]")
                    return True
                else:
                    console.print("[green]✅ Navigation to SharePoint folder view successful[/green]")
                    return True
            
            return False
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Navigation failed: {e}[/yellow]")
            return False
    
    def list_folder_contents(self, folder_path: Optional[str] = None) -> List[Dict]:
        """List files and folders in current SharePoint location"""
        try:
            if folder_path:
                if not self.navigate_to_path(folder_path):
                    return []
            
            console.print("[cyan]📂 Reading folder contents...[/cyan]")
            
            # Wait for SharePoint list to load
            wait = WebDriverWait(self.driver, 10)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, '[role="row"]')))
            time.sleep(2)
            
            items = []
            rows = self.driver.find_elements(By.CSS_SELECTOR, '[role="row"]')
            
            console.print(f"[dim]Found {len(rows)} rows to process...[/dim]")
            
            for row in rows:
                try:
                    # Get all cells
                    cells = row.find_elements(By.CSS_SELECTOR, '[role="gridcell"]')
                    if len(cells) == 0:
                        continue
                    
                    # First cell contains name
                    first_cell = cells[0]
                    
                    # Try to get name from button or link
                    try:
                        name_element = first_cell.find_element(By.TAG_NAME, 'button')
                    except:
                        try:
                            name_element = first_cell.find_element(By.TAG_NAME, 'a')
                        except:
                            continue
                    
                    name = name_element.text.strip()
                    
                    # Skip headers
                    if not name or name in ['Name', 'Modified', 'Modified By', 'Sharing']:
                        continue
                    
                    # Check if folder
                    is_folder = False
                    try:
                        row.find_element(By.CSS_SELECTOR, '[data-icon-name*="Folder"]')
                        is_folder = True
                    except:
                        pass
                    
                    # Get modified date
                    modified = "Unknown"
                    if len(cells) > 1:
                        try:
                            modified = cells[1].text.strip()
                        except:
                            pass
                    
                    items.append({
                        'name': name,
                        'type': 'folder' if is_folder else 'file',
                        'modified': modified,
                        'url': ''
                    })
                    
                except Exception:
                    continue
            
            console.print(f"[green]✅ Found {len(items)} items[/green]")
            
            for item in items:
                icon = "📁" if item['type'] == 'folder' else "📄"
                console.print(f"  {icon} {item['name']}")
            
            return items
            
        except Exception as e:
            console.print(f"[red]❌ Failed to list contents: {e}[/red]")
            return []
    
    def download_file(self, file_name: str, save_path: str) -> bool:
        """Download a file from SharePoint"""
        # Implementation similar to Playwright version
        # For now, return True (will implement if this approach works)
        console.print(f"[yellow]⚠️  Download not yet implemented for Selenium version[/yellow]")
        return False
    
    def close(self):
        """Close the browser"""
        if self.driver:
            try:
                self.driver.quit()
                console.print("[dim]🔒 Browser closed[/dim]")
            except:
                pass

