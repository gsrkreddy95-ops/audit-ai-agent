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
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable
from rich.console import Console
from tools.aws_tab_navigator import AWSTabNavigator

console = Console()


@dataclass
class ServiceContext:
    """Track navigation context for a specific AWS service."""

    service_name: str
    normalized_key: str
    last_url: Optional[str] = None
    last_tab: Optional[str] = None
    last_mode: str = ""
    last_visited: float = field(default_factory=time.time)
    available_tabs: List[str] = field(default_factory=list)
    history: List[str] = field(default_factory=list)

    def log_event(self, event: str):
        timestamp = time.strftime("%H:%M:%S")
        self.history.append(f"{timestamp} {event}")
        if len(self.history) > 25:
            del self.history[:-25]

    def to_dict(self) -> Dict:
        return {
            "service_name": self.service_name,
            "normalized_key": self.normalized_key,
            "last_url": self.last_url,
            "last_tab": self.last_tab,
            "last_mode": self.last_mode,
            "last_visited": self.last_visited,
            "available_tabs": list(self.available_tabs),
            "history": list(self.history),
        }


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
        self.service_contexts: Dict[str, ServiceContext] = {}

        console.print(f"[bold green]🌐 AWS Universal Navigator Ready![/bold green]")
        console.print(f"[dim]Region: {region}[/dim]")

    # ==================== Internal helpers ====================

    def _normalize_service_key(self, service_name: Optional[str]) -> Optional[str]:
        if not service_name:
            return None
        return service_name.strip().lower().replace(" ", "-").replace("_", "-")

    def _safe_current_url(self) -> str:
        try:
            return self.driver.current_url or ""
        except Exception:
            return ""

    def _normalized_url_variants(self, url: Optional[str]) -> List[str]:
        if not url:
            return []

        cleaned = url.lower().replace("https://", "").replace("http://", "")
        if cleaned.startswith("www."):
            cleaned = cleaned[4:]

        variants = []
        for candidate in [cleaned, cleaned.split("#")[0], cleaned.split("?")[0], cleaned.split("#")[0].split("?")[0]]:
            if candidate and candidate not in variants:
                variants.append(candidate)
        return variants

    def _url_matches_service(self, service_key: Optional[str], url: Optional[str] = None, service_name: Optional[str] = None) -> bool:
        """Return True when the supplied URL clearly points at the target service."""

        if not url:
            url = self._safe_current_url()

        if not url or not service_key:
            # Fall back to simple service-name heuristic only when nothing else available
            if service_name:
                sanitized_name = service_name.strip().lower().replace(" ", "-")
                return sanitized_name and sanitized_name in (url or "").lower()
            return False

        variants = self._normalized_url_variants(url)
        if not variants:
            return False

        fragments = self._get_service_url_fragments(service_key)
        normalized_key = service_key.replace("-", "")

        for variant in variants:
            if not variant:
                continue

            # Direct fragment match (covers explicit service console paths)
            if any(fragment and fragment in variant for fragment in fragments):
                return True

            # Fallback: ensure the service key appears in the path portion
            path_bits = variant.split("/", 1)[-1]
            if normalized_key and normalized_key in path_bits.replace("-", ""):
                return True

        return False

    def _get_service_url_fragments(self, service_key: str) -> List[str]:
        fragments: List[str] = []
        template = self.SERVICE_URLS.get(service_key)

        if not template:
            return fragments

        potential_urls = set()
        try:
            potential_urls.add(template.format(region=self.region))
        except Exception:
            potential_urls.add(template)

        # Additional fallbacks for templates with placeholders
        potential_urls.add(template.replace("{region}.", ""))
        potential_urls.add(template.replace("{region}", self.region))
        potential_urls.add(template.replace("{region}", ""))

        for candidate in potential_urls:
            fragments.extend(self._normalized_url_variants(candidate))

        # Deduplicate while preserving order
        unique_fragments: List[str] = []
        seen = set()
        for fragment in fragments:
            if fragment and fragment not in seen:
                seen.add(fragment)
                unique_fragments.append(fragment)

        return unique_fragments

    def _ensure_context(self, service_key: str, service_name: Optional[str]) -> ServiceContext:
        if service_key not in self.service_contexts:
            context = ServiceContext(service_name=service_name or service_key, normalized_key=service_key)
            self.service_contexts[service_key] = context
        else:
            context = self.service_contexts[service_key]
            if service_name and context.service_name != service_name:
                context.service_name = service_name
        return context

    def _update_navigation_history(self, service_name: str):
        if not self.navigation_history or self.navigation_history[-1] != service_name:
            self.navigation_history.append(service_name)

    def _record_service_visit(
        self,
        service_key: str,
        service_name: str,
        url: Optional[str] = None,
        mode: str = "visit",
    ) -> ServiceContext:
        context = self._ensure_context(service_key, service_name)
        context.last_url = url or self._safe_current_url()
        context.last_mode = mode
        context.last_visited = time.time()
        context.log_event(f"{mode}: {context.last_url or 'current page'}")

        self.current_service = service_name
        self._update_navigation_history(service_name)
        return context

    def _page_contains_text(self, text: str) -> bool:
        try:
            page_source = (self.driver.page_source or "").lower()
            return text.lower() in page_source
        except Exception:
            return False

    def _reuse_existing_service_view(self, service_key: str, service_name: str) -> bool:
        current_url = self._safe_current_url()
        if not current_url:
            return False

        current_variants = self._normalized_url_variants(current_url)
        fragments = self._get_service_url_fragments(service_key)

        matched = self._url_matches_service(service_key, url=current_url, service_name=service_name)

        context = self.service_contexts.get(service_key)
        if not matched and context and context.last_url:
            matched = self._url_matches_service(service_key, url=context.last_url, service_name=service_name)

        if not matched and service_name and len(service_name) > 1:
            matched = self._page_contains_text(service_name)

        if matched:
            console.print(
                f"[bold green]🔁 Reusing active {service_name} view within the existing AWS Console session[/bold green]"
            )
            self._record_service_visit(service_key, service_name, url=current_url, mode="reuse")
            try:
                self.driver.execute_script("window.scrollTo(0, 0);")
            except Exception:
                pass
            return True

        return False

    def _update_current_service_tab(self, tab_name: str, event: str = "tab:click"):
        if not tab_name or not self.current_service:
            return

        service_key = self._normalize_service_key(self.current_service)
        if not service_key:
            return

        context = self._ensure_context(service_key, self.current_service)
        context.last_tab = tab_name
        context.log_event(f"{event}: {tab_name}")

    def _record_available_tabs(self, service_key: Optional[str], tabs: List[str]):
        if not service_key:
            return

        context = self._ensure_context(service_key, self.current_service or service_key)
        context.available_tabs = list(tabs)
        context.log_event(f"tabs-discovered: {len(tabs)}")

    def _navigate_to_url(
        self,
        url: str,
        *,
        service_key: Optional[str] = None,
        service_name: Optional[str] = None,
        wait_seconds: int = 3,
    ) -> bool:
        try:
            console.print(f"[cyan]🔗 Navigating via URL: {url[:80]}...[/cyan]")
            self.driver.get(url)
            time.sleep(wait_seconds)

            if service_key:
                if self._url_matches_service(service_key, service_name=service_name):
                    return True
                console.print(
                    f"[yellow]⚠️  URL navigation reached unexpected page: {self._safe_current_url()}[/yellow]"
                )
                return False

            return True
        except Exception as e:
            console.print(f"[red]❌ URL navigation failed: {e}[/red]")
            return False

    # ==================== Public API ====================

    def navigate_to_service(
        self,
        service_name: str,
        use_search: bool = True,
        tab: Optional[str] = None,
        reuse_existing: bool = True,
    ) -> bool:
        """
        Navigate to any AWS service.

        Args:
            service_name: Service name (e.g., 'RDS', 'EC2', 'Lambda')
            use_search: If True, uses AWS Console search (faster, more human-like)
            tab: Optional tab to select after navigation
            reuse_existing: If True, reuses active service tab when already open

        Returns:
            True if navigation successful
        """
        service_key = self._normalize_service_key(service_name)

        console.print(f"[bold cyan]🚀 Navigating to {service_name}...[/bold cyan]")

        if reuse_existing and service_key and self._reuse_existing_service_view(service_key, service_name):
            if tab:
                self.click_tab(tab)
            return True

        navigation_mode = None
        success = False
        search_attempted = False

        if use_search:
            search_attempted = True
            if self._navigate_via_search(service_name, service_key=service_key):
                success = True
                navigation_mode = "search"

        if not success and service_key in self.SERVICE_URLS:
            url = self.SERVICE_URLS[service_key].format(region=self.region)
            if self._navigate_to_url(url, service_key=service_key, service_name=service_name):
                console.print(f"[green]✅ Navigated to {service_name} via direct URL[/green]")
                success = True
                navigation_mode = "direct"

        if not success:
            if not search_attempted:
                console.print(
                    f"[yellow]⚠️  Service '{service_name}' not in known list, falling back to console search...[/yellow]"
                )
                if self._navigate_via_search(service_name, service_key=service_key):
                    success = True
                    navigation_mode = "search"
            elif service_key not in self.SERVICE_URLS:
                console.print(
                    f"[yellow]⚠️  No direct URL for '{service_name}', retrying console search...[/yellow]"
                )
                if self._navigate_via_search(service_name, service_key=service_key):
                    success = True
                    navigation_mode = "search"

        if not success:
            console.print(f"[red]❌ Failed to navigate to {service_name}[/red]")
            return False

        # Record visit + optional tab navigation
        visit_mode = f"navigate:{navigation_mode or 'unknown'}"
        context_key = service_key or self._normalize_service_key(service_name) or service_name.lower()
        self._record_service_visit(context_key, service_name, mode=visit_mode)

        if tab:
            self.click_tab(tab)

        return True
    
    def _navigate_via_search(self, service_name: str, service_key: Optional[str] = None) -> bool:
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
            if self._url_matches_service(service_key, url=current_url, service_name=service_name):
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
        success = self.tab_navigator.find_and_click_tab(tab_name)
        if success:
            resolved_tab = self.tab_navigator.last_clicked_tab or tab_name
            self._update_current_service_tab(resolved_tab)
        return success
    
    def explore_all_tabs(self, screenshot_callback: Optional[Callable] = None) -> Dict:
        """
        Discover and navigate ALL tabs on current page.
        
        Perfect for comprehensive evidence collection!
        
        Args:
            screenshot_callback: Optional function to call for each tab
        
        Returns:
            Dict with results for each tab
        """
        results = self.tab_navigator.explore_all_tabs(screenshot_callback)

        if isinstance(results, dict) and results:
            service_key = self._normalize_service_key(self.current_service)
            if service_key:
                self._record_available_tabs(service_key, list(results.keys()))
                for tab_name, outcome in results.items():
                    if isinstance(outcome, dict) and outcome.get("success"):
                        self._update_current_service_tab(tab_name, event="tab:batch")

        return results
    
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
        service_key = self._normalize_service_key(self.current_service)

        if tabs:
            # Specific tabs provided
            tab_results = self.tab_navigator.click_multiple_tabs(tabs, screenshot_callback)
            if isinstance(tab_results, dict):
                if service_key:
                    self._record_available_tabs(service_key, list(tab_results.keys()))
                for tab_name, outcome in tab_results.items():
                    if isinstance(outcome, dict) and outcome.get("success"):
                        self._update_current_service_tab(tab_name, event="tab:batch")
            results["tabs"] = tab_results
        else:
            # Auto-discover all tabs
            console.print("[cyan]🔍 Auto-discovering tabs...[/cyan]")
            results["tabs"] = self.explore_all_tabs(screenshot_callback)

        # Summary
        total_tabs = len(results["tabs"]) if isinstance(results["tabs"], dict) else 0
        successful_tabs = (
            sum(1 for t in results["tabs"].values() if isinstance(t, dict) and t.get("success"))
            if isinstance(results["tabs"], dict)
            else 0
        )
        
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
        current_context = None
        if self.current_service:
            service_key = self._normalize_service_key(self.current_service)
            if service_key and service_key in self.service_contexts:
                current_context = self.service_contexts[service_key].to_dict()

        return {
            "current_service": self.current_service,
            "region": self.region,
            "navigation_history": list(self.navigation_history),
            "current_url": self._safe_current_url(),
            "cached_services": {key: ctx.to_dict() for key, ctx in self.service_contexts.items()},
            "current_context": current_context,
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

