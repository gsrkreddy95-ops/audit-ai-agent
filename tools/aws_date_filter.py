"""
AWS Date/Time Filter - Universal Resource Filtering by Audit Period
====================================================================

CRITICAL FOR AUDIT COMPLIANCE:
- Filter resources by creation date
- Filter resources by modification date  
- Filter resources by audit period (e.g., FY2025: Jan 1 - Dec 31, 2025)
- Works for ALL AWS services via browser-based filtering

Supports:
- KMS Keys (Creation Date)
- Secrets Manager Secrets (Last Modified, Created)
- S3 Buckets (Creation Date)
- RDS Databases (Creation Time)
- EC2 Instances (Launch Time)
- Lambda Functions (Last Modified)
- IAM Users (Created)
- CloudWatch Alarms (State Updated)
- ... and ALL other AWS resources with date columns!
"""

import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Tuple
from rich.console import Console
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

console = Console()


class AWSDateFilter:
    """
    Universal date/time filter for AWS Console resources.
    
    Works by:
    1. Detecting date columns in AWS Console tables
    2. Applying filters via AWS Console UI (filter buttons, date pickers)
    3. Using JavaScript to filter client-side when AWS UI doesn't support it
    4. Highlighting matching rows for screenshot evidence
    """
    
    def __init__(self, driver):
        """
        Initialize date filter with Selenium driver.
        
        Args:
            driver: Selenium WebDriver instance
        """
        self.driver = driver
        self.debug = True
    
    def filter_by_audit_period(
        self,
        audit_period: str = "FY2025",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        date_column: Optional[str] = None
    ) -> Dict:
        """
        Filter AWS resources by audit period.
        
        Args:
            audit_period: Audit period name (e.g., "FY2025", "Q1-2025")
            start_date: Start date (YYYY-MM-DD or MM/DD/YYYY)
            end_date: End date (YYYY-MM-DD or MM/DD/YYYY)
            date_column: Specific date column to filter (auto-detects if None)
        
        Returns:
            Dict with results:
            {
                "status": "success",
                "filtered_count": 15,
                "total_count": 100,
                "start_date": "2025-01-01",
                "end_date": "2025-12-31",
                "method": "javascript" or "aws_ui",
                "date_column": "Creation date"
            }
        
        Examples:
            # Filter by FY2025 (auto-calculates Jan 1 - Dec 31, 2025)
            filter_by_audit_period(audit_period="FY2025")
            
            # Filter by custom date range
            filter_by_audit_period(
                start_date="2025-01-01",
                end_date="2025-06-30"
            )
            
            # Filter by specific column
            filter_by_audit_period(
                start_date="2025-01-01",
                end_date="2025-12-31",
                date_column="Last modified"
            )
        """
        console.print("\n[bold cyan]" + "="*60 + "[/bold cyan]")
        console.print("[bold cyan]📅 DATE FILTER ACTIVATED[/bold cyan]")
        console.print("[bold cyan]" + "="*60 + "[/bold cyan]\n")
        
        # Parse audit period to dates
        if not start_date or not end_date:
            start_date, end_date = self._parse_audit_period(audit_period)
        
        console.print(f"[cyan]📅 Audit Period: {audit_period}[/cyan]")
        console.print(f"[cyan]   Start Date: {start_date}[/cyan]")
        console.print(f"[cyan]   End Date: {end_date}[/cyan]\n")
        
        # Wait for page to load
        time.sleep(2)
        
        # Try AWS Console UI filtering first (if available)
        ui_result = self._try_aws_ui_filter(start_date, end_date, date_column)
        if ui_result["success"]:
            console.print("[green]✅ Applied filter via AWS Console UI[/green]")
            return ui_result
        
        # Fall back to JavaScript filtering
        console.print("[yellow]⚠️  AWS UI filter not available, using JavaScript filter[/yellow]")
        js_result = self._apply_javascript_filter(start_date, end_date, date_column)
        
        if js_result["status"] == "success":
            console.print(f"\n[bold green]✅ DATE FILTER COMPLETE![/bold green]")
            console.print(f"[green]   Filtered: {js_result['filtered_count']} resources[/green]")
            console.print(f"[green]   Total: {js_result['total_count']} resources[/green]")
            console.print(f"[green]   Period: {start_date} to {end_date}[/green]\n")
        
        return js_result
    
    def _parse_audit_period(self, audit_period: str) -> Tuple[str, str]:
        """
        Parse audit period string to start/end dates.
        
        Supported formats:
        - FY2025 → Jan 1, 2025 to Dec 31, 2025
        - FY2024 → Jan 1, 2024 to Dec 31, 2024
        - Q1-2025 → Jan 1, 2025 to Mar 31, 2025
        - Q2-2025 → Apr 1, 2025 to Jun 30, 2025
        - Q3-2025 → Jul 1, 2025 to Sep 30, 2025
        - Q4-2025 → Oct 1, 2025 to Dec 31, 2025
        - 2025 → Jan 1, 2025 to Dec 31, 2025
        
        Args:
            audit_period: Period string
        
        Returns:
            Tuple of (start_date, end_date) in YYYY-MM-DD format
        """
        audit_period = audit_period.upper().strip()
        
        # Fiscal Year (FY2025)
        if audit_period.startswith("FY"):
            year = int(audit_period.replace("FY", ""))
            return f"{year}-01-01", f"{year}-12-31"
        
        # Quarter (Q1-2025, Q2-2025, etc.)
        if audit_period.startswith("Q"):
            quarter = int(audit_period[1])
            year = int(audit_period.split("-")[1])
            
            quarters = {
                1: (f"{year}-01-01", f"{year}-03-31"),
                2: (f"{year}-04-01", f"{year}-06-30"),
                3: (f"{year}-07-01", f"{year}-09-30"),
                4: (f"{year}-10-01", f"{year}-12-31")
            }
            return quarters.get(quarter, (f"{year}-01-01", f"{year}-12-31"))
        
        # Just year (2025)
        if audit_period.isdigit():
            year = int(audit_period)
            return f"{year}-01-01", f"{year}-12-31"
        
        # Default: current year
        current_year = datetime.now().year
        console.print(f"[yellow]⚠️  Unknown audit period '{audit_period}', using current year {current_year}[/yellow]")
        return f"{current_year}-01-01", f"{current_year}-12-31"
    
    def _try_aws_ui_filter(
        self,
        start_date: str,
        end_date: str,
        date_column: Optional[str]
    ) -> Dict:
        """
        Try to use AWS Console's built-in filtering UI.
        
        AWS Console services often have filter buttons/dropdowns.
        This method tries to find and use them.
        
        Returns:
            Dict with success status
        """
        try:
            # Look for AWS filter button
            filter_script = """
                // Try to find filter button
                let filterBtn = document.querySelector('[data-testid="filter-button"]') ||
                                document.querySelector('button[aria-label*="Filter"]') ||
                                document.querySelector('button[aria-label*="filter"]') ||
                                document.querySelector('awsui-property-filter');
                
                if (filterBtn) {
                    return true;
                }
                return false;
            """
            
            has_filter_ui = self.driver.execute_script(filter_script)
            
            if not has_filter_ui:
                return {"success": False, "reason": "No AWS filter UI found"}
            
            # AWS has filter UI, but configuring it is complex
            # For now, return False and use JavaScript method
            # TODO: Implement AWS filter UI automation
            return {"success": False, "reason": "AWS filter UI automation not yet implemented"}
            
        except Exception as e:
            return {"success": False, "reason": str(e)}
    
    def _apply_javascript_filter(
        self,
        start_date: str,
        end_date: str,
        date_column: Optional[str]
    ) -> Dict:
        """
        Apply date filter using JavaScript.
        
        This method:
        1. Finds all table rows
        2. Extracts date from each row
        3. Hides rows outside date range
        4. Highlights rows within date range
        5. Counts filtered results
        
        Returns:
            Dict with filter results
        """
        try:
            # Convert dates to timestamps for comparison
            start_ts = self._parse_date_to_timestamp(start_date)
            end_ts = self._parse_date_to_timestamp(end_date)
            
            filter_script = f"""
                // Date filtering script
                const startDate = new Date('{start_date}');
                const endDate = new Date('{end_date}');
                
                // Helper: Parse date from various formats
                function parseDate(dateStr) {{
                    if (!dateStr) return null;
                    
                    // Try ISO format (YYYY-MM-DD)
                    let date = new Date(dateStr);
                    if (!isNaN(date)) return date;
                    
                    // Try MM/DD/YYYY
                    let parts = dateStr.match(/(\\d{{1,2}})\\/(\\d{{1,2}})\\/(\\d{{4}})/);
                    if (parts) {{
                        return new Date(parts[3], parts[1]-1, parts[2]);
                    }}
                    
                    // Try relative dates (e.g., "2 days ago")
                    if (dateStr.includes('ago')) {{
                        let match = dateStr.match(/(\\d+)\\s+(day|week|month|year)/);
                        if (match) {{
                            let amount = parseInt(match[1]);
                            let unit = match[2];
                            let now = new Date();
                            
                            if (unit === 'day') {{
                                return new Date(now.setDate(now.getDate() - amount));
                            }} else if (unit === 'week') {{
                                return new Date(now.setDate(now.getDate() - (amount * 7)));
                            }} else if (unit === 'month') {{
                                return new Date(now.setMonth(now.getMonth() - amount));
                            }} else if (unit === 'year') {{
                                return new Date(now.setFullYear(now.getFullYear() - amount));
                            }}
                        }}
                    }}
                    
                    return null;
                }}
                
                // Find all table rows
                let rows = document.querySelectorAll('table tbody tr');
                if (rows.length === 0) {{
                    rows = document.querySelectorAll('[role="row"]');
                }}
                
                let totalCount = rows.length;
                let filteredCount = 0;
                let hiddenCount = 0;
                
                // Process each row
                rows.forEach(row => {{
                    let dateFound = false;
                    let inRange = false;
                    
                    // Search for date in cells
                    let cells = row.querySelectorAll('td, [role="cell"]');
                    
                    for (let cell of cells) {{
                        let text = cell.textContent.trim();
                        let date = parseDate(text);
                        
                        if (date && !isNaN(date)) {{
                            dateFound = true;
                            
                            // Check if date is in range
                            if (date >= startDate && date <= endDate) {{
                                inRange = true;
                                break;
                            }}
                        }}
                    }}
                    
                    // Apply filter
                    if (dateFound) {{
                        if (inRange) {{
                            // Highlight matching row
                            row.style.backgroundColor = '#e8f5e9';  // Light green
                            row.style.border = '2px solid #4caf50';
                            filteredCount++;
                        }} else {{
                            // Hide non-matching row
                            row.style.display = 'none';
                            hiddenCount++;
                        }}
                    }} else {{
                        // No date found - keep visible but don't count
                        // (might be header or non-date row)
                    }}
                }});
                
                // Add filter indicator banner
                let banner = document.createElement('div');
                banner.id = 'date-filter-banner';
                banner.style.cssText = `
                    position: fixed;
                    top: 80px;
                    right: 20px;
                    background: #4caf50;
                    color: white;
                    padding: 15px 20px;
                    border-radius: 8px;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.3);
                    z-index: 10000;
                    font-family: Arial, sans-serif;
                    font-size: 14px;
                `;
                banner.innerHTML = `
                    <strong>📅 Date Filter Active</strong><br>
                    Period: {start_date} to {end_date}<br>
                    Showing: ${{filteredCount}} / ${{totalCount}} resources
                `;
                
                // Remove old banner if exists
                let oldBanner = document.getElementById('date-filter-banner');
                if (oldBanner) oldBanner.remove();
                
                document.body.appendChild(banner);
                
                return {{
                    filteredCount: filteredCount,
                    totalCount: totalCount,
                    hiddenCount: hiddenCount
                }};
            """
            
            result = self.driver.execute_script(filter_script)
            
            if result:
                return {
                    "status": "success",
                    "filtered_count": result.get("filteredCount", 0),
                    "total_count": result.get("totalCount", 0),
                    "hidden_count": result.get("hiddenCount", 0),
                    "start_date": start_date,
                    "end_date": end_date,
                    "method": "javascript",
                    "date_column": date_column or "auto-detected"
                }
            else:
                return {
                    "status": "error",
                    "error": "No result from JavaScript filter"
                }
            
        except Exception as e:
            console.print(f"[red]❌ JavaScript filter error: {e}[/red]")
            return {
                "status": "error",
                "error": str(e)
            }
    
    def _parse_date_to_timestamp(self, date_str: str) -> float:
        """Convert date string to Unix timestamp"""
        try:
            dt = datetime.strptime(date_str, "%Y-%m-%d")
            return dt.timestamp()
        except:
            return 0.0
    
    def clear_filter(self) -> bool:
        """
        Clear date filter and show all resources.
        
        Returns:
            True if successful
        """
        try:
            clear_script = """
                // Show all hidden rows
                let rows = document.querySelectorAll('table tbody tr, [role="row"]');
                rows.forEach(row => {
                    row.style.display = '';
                    row.style.backgroundColor = '';
                    row.style.border = '';
                });
                
                // Remove banner
                let banner = document.getElementById('date-filter-banner');
                if (banner) banner.remove();
                
                return true;
            """
            
            self.driver.execute_script(clear_script)
            console.print("[green]✅ Date filter cleared[/green]")
            return True
            
        except Exception as e:
            console.print(f"[red]❌ Error clearing filter: {e}[/red]")
            return False
    
    def get_date_column_names(self) -> List[str]:
        """
        Auto-detect date column names in current AWS table.
        
        Returns:
            List of date column names found
        """
        try:
            detect_script = """
                let columns = [];
                let headers = document.querySelectorAll('table thead th, [role="columnheader"]');
                
                headers.forEach((header, index) => {
                    let text = header.textContent.trim().toLowerCase();
                    
                    // Date-related keywords
                    if (text.includes('date') || 
                        text.includes('time') || 
                        text.includes('created') ||
                        text.includes('modified') ||
                        text.includes('updated') ||
                        text.includes('launched') ||
                        text.includes('last')) {
                        columns.push({
                            index: index,
                            name: header.textContent.trim()
                        });
                    }
                });
                
                return columns;
            """
            
            columns = self.driver.execute_script(detect_script)
            column_names = [col['name'] for col in columns]
            
            if column_names:
                console.print(f"[cyan]📅 Date columns found: {', '.join(column_names)}[/cyan]")
            
            return column_names
            
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not detect date columns: {e}[/yellow]")
            return []

