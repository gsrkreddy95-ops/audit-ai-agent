"""
Universal AWS Service Navigator - Works for ALL AWS Services!

Supports EVERY AWS service with human-like navigation:
- Tab clicking
- Scrolling
- Forward/backward navigation  
- Recently visited services
- Search bar usage
- Resource exploration

Designed to work like a HUMAN navigating AWS Console!
"""

import time
from typing import List, Dict, Optional, Callable
from rich.console import Console
from tools.aws_tab_navigator import AWSTabNavigator

console = Console()


class AWSUniversalServiceNavigator:
    """
    Navigate ANY AWS service with human-like behavior.
    
    Supports ALL AWS services from your screenshot:
    - Aurora and RDS
    - API Gateway
    - EC2
    - AWS Global View
    - Billing and Cost Management
    - Systems Manager
    - Secrets Manager
    - IAM
    - S3
    - Key Management Service (KMS)
    - CloudTrail
    - AWS Backup
    - VPC
    - Amazon Bedrock
    - Lambda
    - And MORE!
    """
    
    # AWS Service URL patterns
    SERVICE_URLS = {
        'rds': 'https://{region}.console.aws.amazon.com/rds/home?region={region}',
        'aurora': 'https://{region}.console.aws.amazon.com/rds/home?region={region}#databases:',
        'ec2': 'https://{region}.console.aws.amazon.com/ec2/home?region={region}',
        's3': 'https://s3.console.aws.amazon.com/s3/home?region={region}',
        'lambda': 'https://{region}.console.aws.amazon.com/lambda/home?region={region}#/functions',
        'apigateway': 'https://{region}.console.aws.amazon.com/apigateway/home?region={region}',
        'api-gateway': 'https://{region}.console.aws.amazon.com/apigateway/home?region={region}',
        'vpc': 'https://{region}.console.aws.amazon.com/vpc/home?region={region}',
        'cloudtrail': 'https://{region}.console.aws.amazon.com/cloudtrail/home?region={region}',
        'cloudwatch': 'https://{region}.console.aws.amazon.com/cloudwatch/home?region={region}',
        'iam': 'https://console.aws.amazon.com/iam/home',
        'billing': 'https://console.aws.amazon.com/billing/home',
        'cost-management': 'https://console.aws.amazon.com/cost-management/home',
        'kms': 'https://{region}.console.aws.amazon.com/kms/home?region={region}',
        'secretsmanager': 'https://{region}.console.aws.amazon.com/secretsmanager/home?region={region}',
        'secrets-manager': 'https://{region}.console.aws.amazon.com/secretsmanager/home?region={region}',
        'systems-manager': 'https://{region}.console.aws.amazon.com/systems-manager/home?region={region}',
        'ssm': 'https://{region}.console.aws.amazon.com/systems-manager/home?region={region}',
        'backup': 'https://{region}.console.aws.amazon.com/backup/home?region={region}',
        'bedrock': 'https://{region}.console.aws.amazon.com/bedrock/home?region={region}',
        'dynamodb': 'https://{region}.console.aws.amazon.com/dynamodbv2/home?region={region}',
        'sns': 'https://{region}.console.aws.amazon.com/sns/home?region={region}',
        'sqs': 'https://{region}.console.aws.amazon.com/sqs/home?region={region}',
        'elasticache': 'https://{region}.console.aws.amazon.com/elasticache/home?region={region}',
        'ecs': 'https://{region}.console.aws.amazon.com/ecs/home?region={region}',
        'eks': 'https://{region}.console.aws.amazon.com/eks/home?region={region}',
        'elb': 'https://{region}.console.aws.amazon.com/ec2/home?region={region}#LoadBalancers:',
        'route53': 'https://console.aws.amazon.com/route53/home',
        'cloudfront': 'https://console.aws.amazon.com/cloudfront/home',
        'waf': 'https://{region}.console.aws.amazon.com/wafv2/home?region={region}',
    }
    
    def __init__(self, driver, region: str = "us-east-1"):
        """
        Initialize universal navigator.
        
        Args:
            driver: Selenium WebDriver instance
            region: AWS region (default us-east-1)
        """
        self.driver = driver
        self.region = region
        self.tab_navigator = AWSTabNavigator(driver)
        self.navigation_history = []
        self.current_service = None
        
        console.print(f"[bold green]🌐 AWS Universal Navigator Ready![/bold green]")
        console.print(f"[dim]Region: {region}[/dim]")
    
    def navigate_to_service(self, service_name: str, use_search: bool = True) -> bool:
        """
        Navigate to any AWS service.
        
        Args:
            service_name: Service name (e.g., 'RDS', 'EC2', 'Lambda')
            use_search: If True, uses AWS Console search (faster, more human-like)
        
        Returns:
            True if navigation successful
        """
        service_lower = service_name.lower().replace(' ', '-')
        
        console.print(f"[bold cyan]🚀 Navigating to {service_name}...[/bold cyan]")
        
        if use_search:
            # Try AWS Console search first (FASTEST, most human-like!)
            if self._navigate_via_search(service_name):
                self.current_service = service_name
                self.navigation_history.append(service_name)
                return True
        
        # Fallback to direct URL
        if service_lower in self.SERVICE_URLS:
            url = self.SERVICE_URLS[service_lower].format(region=self.region)
            console.print(f"[cyan]🔗 Navigating via URL: {url[:80]}...[/cyan]")
            self.driver.get(url)
            time.sleep(3)
            
            self.current_service = service_name
            self.navigation_history.append(service_name)
            console.print(f"[green]✅ Navigated to {service_name}[/green]")
            return True
        else:
            console.print(f"[yellow]⚠️  Service '{service_name}' not in known services, trying search...[/yellow]")
            return self._navigate_via_search(service_name)
    
    def _navigate_via_search(self, service_name: str) -> bool:
        """Navigate using AWS Console search (HUMAN-LIKE!)"""
        try:
            console.print(f"[cyan]🔍 Using AWS Console search for '{service_name}'...[/cyan]")
            
            result = self.driver.execute_script("""
                var serviceName = arguments[0];
                console.log('=== AWS Console Search ===');
                console.log('Searching for:', serviceName);
                
                // Find search button
                var searchButton = document.querySelector('[data-testid="awsc-nav-search-button"]') ||
                                 document.querySelector('[aria-label="Search"]') ||
                                 document.querySelector('button[aria-label*="Search"]') ||
                                 document.querySelector('#awsc-nav-search-button');
                
                if (!searchButton) {
                    console.log('ERROR: Search button not found');
                    return {success: false, error: 'Search button not found'};
                }
                
                // Click search button
                searchButton.click();
                console.log('Clicked search button');
                
                // Wait for search input to appear
                setTimeout(function() {
                    var searchInput = document.querySelector('input[type="search"]') ||
                                    document.querySelector('[data-testid="search-input"]') ||
                                    document.querySelector('input[placeholder*="Search"]') ||
                                    document.querySelector('#awsc-nav-search-field');
                    
                    if (!searchInput) {
                        console.log('ERROR: Search input not found');
                        return;
                    }
                    
                    console.log('Found search input, typing...');
                    searchInput.value = serviceName;
                    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                    searchInput.dispatchEvent(new Event('change', { bubbles: true }));
                    
                    // Wait for results and click first one
                    setTimeout(function() {
                        var results = document.querySelectorAll('[data-testid="search-result"]') ||
                                    document.querySelectorAll('a[href*="console.aws"]') ||
                                    document.querySelectorAll('.search-result');
                        
                        console.log('Found', results.length, 'search results');
                        
                        if (results.length > 0) {
                            console.log('Clicking first result...');
                            results[0].click();
                        }
                    }, 800);
                }, 500);
                
                return {success: true};
            """, service_name)
            
            time.sleep(4)  # Wait for navigation
            
            current_url = self.driver.current_url
            if service_name.lower() in current_url.lower() or 'console.aws.amazon.com' in current_url:
                console.print(f"[green]✅ Search navigation successful![/green]")
                return True
            else:
                console.print(f"[yellow]⚠️  Search may not have worked[/yellow]")
                return False
        
        except Exception as e:
            console.print(f"[red]❌ Search navigation failed: {e}[/red]")
            return False
    
    def go_back(self) -> bool:
        """Navigate back (like clicking browser back button)"""
        console.print("[cyan]⬅️  Going back...[/cyan]")
        self.driver.back()
        time.sleep(2)
        console.print("[green]✓ Navigated back[/green]")
        return True
    
    def go_forward(self) -> bool:
        """Navigate forward (like clicking browser forward button)"""
        console.print("[cyan]➡️  Going forward...[/cyan]")
        self.driver.forward()
        time.sleep(2)
        console.print("[green]✓ Navigated forward[/green]")
        return True
    
    def scroll_down(self, pixels: int = 500) -> bool:
        """Scroll down on the page"""
        console.print(f"[cyan]📜 Scrolling down {pixels}px...[/cyan]")
        self.driver.execute_script(f"window.scrollBy(0, {pixels});")
        time.sleep(0.5)
        return True
    
    def scroll_up(self, pixels: int = 500) -> bool:
        """Scroll up on the page"""
        console.print(f"[cyan]📜 Scrolling up {pixels}px...[/cyan]")
        self.driver.execute_script(f"window.scrollBy(0, -{pixels});")
        time.sleep(0.5)
        return True
    
    def scroll_to_bottom(self) -> bool:
        """Scroll to bottom of page"""
        console.print("[cyan]📜 Scrolling to bottom...[/cyan]")
        self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(1)
        return True
    
    def scroll_to_top(self) -> bool:
        """Scroll to top of page"""
        console.print("[cyan]📜 Scrolling to top...[/cyan]")
        self.driver.execute_script("window.scrollTo(0, 0);")
        time.sleep(1)
        return True
    
    def click_tab(self, tab_name: str) -> bool:
        """
        Click a tab on current page.
        
        Works for ANY AWS service that has tabs!
        
        Args:
            tab_name: Tab name (e.g., "Configuration", "Monitoring")
        
        Returns:
            True if successful
        """
        return self.tab_navigator.find_and_click_tab(tab_name)
    
    def explore_all_tabs(self, screenshot_callback: Optional[Callable] = None) -> Dict:
        """
        Discover and navigate ALL tabs on current page.
        
        Perfect for comprehensive evidence collection!
        
        Args:
            screenshot_callback: Optional function to call for each tab
        
        Returns:
            Dict with results for each tab
        """
        return self.tab_navigator.explore_all_tabs(screenshot_callback)
    
    def navigate_multiple_services(self, services: List[str], screenshot_callback: Optional[Callable] = None) -> Dict:
        """
        Navigate to multiple AWS services and optionally screenshot each.
        
        Args:
            services: List of service names (e.g., ['RDS', 'EC2', 'S3'])
            screenshot_callback: Optional function to call for each service
        
        Returns:
            Dict with results for each service
        """
        results = {}
        
        for service in services:
            console.print(f"\n[bold cyan]{'='*50}[/bold cyan]")
            console.print(f"[bold cyan]📍 Service: {service}[/bold cyan]")
            console.print(f"[bold cyan]{'='*50}[/bold cyan]\n")
            
            if self.navigate_to_service(service):
                if screenshot_callback:
                    try:
                        screenshot_path = screenshot_callback(service)
                        results[service] = {"success": True, "screenshot": screenshot_path}
                        console.print(f"[green]✅ {service} completed[/green]")
                    except Exception as e:
                        results[service] = {"success": True, "screenshot": None, "error": str(e)}
                        console.print(f"[yellow]⚠️  {service} screenshot failed: {e}[/yellow]")
                else:
                    results[service] = {"success": True}
            else:
                results[service] = {"success": False, "error": "Navigation failed"}
                console.print(f"[red]❌ {service} navigation failed[/red]")
        
        return results
    
    def comprehensive_evidence_collection(
        self,
        service: str,
        tabs: Optional[List[str]] = None,
        screenshot_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Complete evidence collection for a service:
        1. Navigate to service
        2. Take overview screenshot
        3. Click and screenshot each specified tab
        4. OR auto-discover all tabs
        
        Args:
            service: Service name (e.g., 'RDS')
            tabs: Optional list of tabs to screenshot. If None, auto-discovers all tabs.
            screenshot_callback: Function to call for screenshots
        
        Returns:
            Dict with all results
        """
        console.print(f"\n[bold green]{'='*60}[/bold green]")
        console.print(f"[bold green]📋 COMPREHENSIVE EVIDENCE COLLECTION[/bold green]")
        console.print(f"[bold green]Service: {service}[/bold green]")
        console.print(f"[bold green]{'='*60}[/bold green]\n")
        
        results = {
            "service": service,
            "overview": None,
            "tabs": {}
        }
        
        # Step 1: Navigate to service
        if not self.navigate_to_service(service):
            results["error"] = "Navigation failed"
            return results
        
        # Step 2: Take overview screenshot
        if screenshot_callback:
            try:
                overview_path = screenshot_callback(f"{service}_overview")
                results["overview"] = overview_path
                console.print(f"[green]✅ Overview screenshot captured[/green]")
            except Exception as e:
                console.print(f"[yellow]⚠️  Overview screenshot failed: {e}[/yellow]")
        
        # Step 3: Navigate tabs
        if tabs:
            # Specific tabs provided
            results["tabs"] = self.tab_navigator.click_multiple_tabs(tabs, screenshot_callback)
        else:
            # Auto-discover all tabs
            console.print("[cyan]🔍 Auto-discovering tabs...[/cyan]")
            results["tabs"] = self.tab_navigator.explore_all_tabs(screenshot_callback)
        
        # Summary
        total_tabs = len(results["tabs"])
        successful_tabs = sum(1 for t in results["tabs"].values() if t.get("success"))
        
        console.print(f"\n[bold green]{'='*60}[/bold green]")
        console.print(f"[bold green]✅ EVIDENCE COLLECTION COMPLETE[/bold green]")
        console.print(f"[bold green]Total tabs: {total_tabs} | Successful: {successful_tabs}[/bold green]")
        console.print(f"[bold green]{'='*60}[/bold green]\n")
        
        return results
    
    def get_recently_visited_services(self) -> List[str]:
        """Get list of recently visited services from AWS Console"""
        try:
            services = self.driver.execute_script("""
                var recentlyVisited = [];
                
                // Look for "Recently visited" section
                var recentSection = document.querySelector('[data-testid="recently-visited"]') ||
                                  document.querySelector('h2:contains("Recently visited")') ||
                                  document.querySelectorAll('h2, h3');
                
                // Find service links
                var serviceLinks = document.querySelectorAll('a[href*="console.aws"]');
                
                for (var link of serviceLinks) {
                    var text = link.textContent.trim();
                    if (text && text.length > 0 && text.length < 50) {
                        recentlyVisited.push(text);
                    }
                }
                
                return recentlyVisited;
            """)
            
            if services:
                console.print(f"[cyan]📋 Recently visited services: {', '.join(services[:5])}[/cyan]")
                return services
            else:
                return []
        
        except Exception as e:
            console.print(f"[yellow]⚠️  Could not get recently visited services: {e}[/yellow]")
            return []
    
    def change_region(self, new_region: str) -> bool:
        """
        Change AWS region using the region selector.
        
        Args:
            new_region: Region code (e.g., 'us-west-2', 'eu-west-1')
        
        Returns:
            True if successful
        """
        console.print(f"[cyan]🌍 Changing region to {new_region}...[/cyan]")
        
        try:
            result = self.driver.execute_script("""
                var targetRegion = arguments[0];
                console.log('=== Region Change ===');
                console.log('Target region:', targetRegion);
                
                // Find region selector button
                var regionButton = document.querySelector('[data-testid="awsc-nav-region-menu-button"]') ||
                                 document.querySelector('button[aria-label*="region"]') ||
                                 document.querySelector('#regionMenuButton');
                
                if (!regionButton) {
                    console.log('ERROR: Region selector not found');
                    return {success: false, error: 'Region selector not found'};
                }
                
                // Click region selector
                regionButton.click();
                console.log('Clicked region selector');
                
                // Wait for menu to open
                setTimeout(function() {
                    // Find target region option
                    var regionOptions = document.querySelectorAll('[data-region]') ||
                                      document.querySelectorAll('button[aria-label*="' + targetRegion + '"]');
                    
                    for (var option of regionOptions) {
                        var dataRegion = option.getAttribute('data-region');
                        var text = option.textContent || '';
                        
                        if (dataRegion === targetRegion || text.includes(targetRegion)) {
                            console.log('Found region option, clicking...');
                            option.click();
                            return;
                        }
                    }
                    
                    console.log('ERROR: Region option not found');
                }, 500);
                
                return {success: true};
            """, new_region)
            
            time.sleep(3)
            self.region = new_region
            console.print(f"[green]✅ Changed to region {new_region}[/green]")
            return True
        
        except Exception as e:
            console.print(f"[red]❌ Region change failed: {e}[/red]")
            return False
    
    def get_status(self) -> Dict:
        """Get current navigation status"""
        return {
            "current_service": self.current_service,
            "region": self.region,
            "navigation_history": self.navigation_history,
            "current_url": self.driver.current_url
        }


# Convenience function for quick service navigation
def navigate_aws_services(
    driver,
    services: List[str],
    region: str = "us-east-1",
    screenshot_func: Optional[Callable] = None
) -> Dict:
    """
    Quick function to navigate multiple AWS services.
    
    Args:
        driver: Selenium WebDriver
        services: List of service names
        region: AWS region
        screenshot_func: Optional screenshot function
    
    Returns:
        Dict with results
    
    Example:
        >>> from selenium import webdriver
        >>> driver = webdriver.Chrome()
        >>> # Authenticate to AWS first...
        >>> 
        >>> results = navigate_aws_services(
        >>>     driver,
        >>>     ['RDS', 'EC2', 'Lambda', 'API Gateway'],
        >>>     region='us-east-1'
        >>> )
    """
    navigator = AWSUniversalServiceNavigator(driver, region)
    return navigator.navigate_multiple_services(services, screenshot_func)

