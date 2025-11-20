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
        'codepipeline': 'https://{region}.console.aws.amazon.com/codesuite/codepipeline/pipelines?region={region}',
        'codebuild': 'https://{region}.console.aws.amazon.com/codesuite/codebuild/projects?region={region}',
        'codecommit': 'https://{region}.console.aws.amazon.com/codesuite/codecommit/repositories?region={region}',
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
        """
        STRICT validation: Only reuse if ACTUALLY on the service console page.
        NOT if just seeing service name in "Recently Viewed" or on homepage!
        """
        current_url = self._safe_current_url()
        if not current_url or 'console.aws.amazon.com' not in current_url:
            return False
        # CRITICAL: If on AWS homepage (/console/home), NEVER reuse!
        # Homepage shows "Recently Viewed" which contains service names but is NOT the service page
        if '/console/home' in current_url:
            console.print(f"[dim]   On AWS homepage, need to navigate to {service_name}...[/dim]")
            return False
        
        # STRICT: Check if URL actually contains the service path
        # e.g., apigateway URL must have '/apigateway/' in path
        # Not just seeing "API Gateway" text somewhere on page!
        service_path_patterns = {
            'apigateway': ['/apigateway/', '/apigateway/main', '/apigateway/home'],
            'api-gateway': ['/apigateway/', '/apigateway/main', '/apigateway/home'],
            'rds': ['/rds/', '/rds/home', '/rds#'],
            'ec2': ['/ec2/', '/ec2/v2', '/ec2/home'],
            'lambda': ['/lambda/', '/lambda/home'],
            's3': ['s3.console.aws.amazon.com', '/s3/'],
            'vpc': ['/vpc/', '/vpc/home'],
            'iam': ['/iam/', '/iamv2/'],
            'cloudtrail': ['/cloudtrail/', '/cloudtrail/home'],
            'cloudwatch': ['/cloudwatch/', '/cloudwatch/home'],
            'kms': ['/kms/', '/kms/home'],
            'secretsmanager': ['/secretsmanager/', '/secretsmanager/home'],
            'secrets-manager': ['/secretsmanager/', '/secretsmanager/home'],
            'codepipeline': ['/codesuite/codepipeline/', '/codepipeline/'],
            'codebuild': ['/codesuite/codebuild/', '/codebuild/'],
            'codecommit': ['/codesuite/codecommit/', '/codecommit/'],
            'systems-manager': ['/systems-manager/', '/systems-manager/home'],
            'ssm': ['/systems-manager/', '/systems-manager/home'],
            'backup': ['/backup/', '/backup/home'],
            'bedrock': ['/bedrock/', '/bedrock/home'],
            'dynamodb': ['/dynamodb/', '/dynamodbv2/'],
            'sns': ['/sns/', '/sns/v3/'],
            'sqs': ['/sqs/', '/sqs/v2/'],
            'elb': ['/ec2/v2/home', '/ec2/home#LoadBalancers'],
            'elasticloadbalancing': ['/ec2/v2/home', '/ec2/home#LoadBalancers'],
        }
        
        # Check if current URL contains the actual service path
        if service_key in service_path_patterns:
            patterns = service_path_patterns[service_key]
            url_lower = current_url.lower()
            
            for pattern in patterns:
                if pattern.lower() in url_lower:
                    console.print(
                        f"[bold green]🔁 Reusing active {service_name} console (verified at: {pattern})[/bold green]"
                    )
                    self._record_service_visit(service_key, service_name, url=current_url, mode="reuse")
                    try:
                        self.driver.execute_script("window.scrollTo(0, 0);")
                    except Exception:
                        pass
                    return True
            
            # URL doesn't contain service path - must navigate!
            console.print(f"[dim]   Current page not {service_name} console, will navigate...[/dim]")
            return False
        
        # For unknown services, do strict URL matching
        matched = self._url_matches_service(service_key, url=current_url, service_name=service_name)
        
        if matched:
            # Double-check: URL must contain service key, not just text on page
            if service_key.lower() in current_url.lower():
                console.print(
                    f"[bold green]🔁 Reusing active {service_name} view[/bold green]"
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
   
    def navigate_to_section(
        self,
        section_name: str,
        click_first_resource: bool = False,
        resource_name: Optional[str] = None,
        resource_index: int = 0
    ) -> bool:
        """
        Navigate to a specific section within the current AWS service.
        
        Examples:
            - "Custom Domain Names" in API Gateway
            - "Databases" in RDS
            - "Load Balancers" in EC2
            - "Functions" in Lambda
            
        Args:
            section_name: The section/page to navigate to (e.g., "Custom Domain Names")
            click_first_resource: If True, clicks the first resource in the list
            resource_name: If provided, clicks the resource with this name
            resource_index: If click_first_resource=True, clicks this index (default: 0)
        
        Returns:
            bool: True if navigation successful
        """
        try:
            console.print(f"[cyan]🧭 Navigating to section: '{section_name}'...[/cyan]")
            
            # STRATEGY 1: Look for sidebar/navigation menu links
            result = self.driver.execute_script("""
                var sectionName = arguments[0];
                var sectionLower = sectionName.toLowerCase();
                console.log('=== Section Navigation ===');
                console.log('Looking for:', sectionName);
                
                // Look for navigation links (sidebar, menu, etc.)
                var selectors = [
                    'a[href*="#"]',  // Hash links (common in AWS)
                    'nav a',          // Navigation links
                    'aside a',        // Sidebar links
                    '[role="navigation"] a',
                    '.awsui-side-navigation a',
                    '[data-testid*="nav"] a',
                    'ul li a',        // List links
                    '.awsui-table a'  // Table links
                ];
                
                for (var s = 0; s < selectors.length; s++) {
                    var links = document.querySelectorAll(selectors[s]);
                    console.log('Checking', links.length, 'links with selector:', selectors[s]);
                    
                    for (var i = 0; i < links.length; i++) {
                        var link = links[i];
                        var linkText = (link.textContent || link.innerText || '').trim().toLowerCase();
                        
                        if (linkText === sectionLower || 
                            linkText.includes(sectionLower) ||
                            sectionLower.includes(linkText)) {
                            console.log('✅ Found matching link:', linkText);
                            link.scrollIntoView({behavior: 'smooth', block: 'center'});
                            link.click();
                            return {success: true, method: 'link-click', text: linkText};
                        }
                    }
                }
                
                // STRATEGY 2: Look for buttons
                var buttons = document.querySelectorAll('button, [role="button"]');
                console.log('Checking', buttons.length, 'buttons');
                
                for (var i = 0; i < buttons.length; i++) {
                    var btn = buttons[i];
                    var btnText = (btn.textContent || btn.innerText || '').trim().toLowerCase();
                    
                    if (btnText.includes(sectionLower)) {
                        console.log('✅ Found matching button:', btnText);
                        btn.scrollIntoView({behavior: 'smooth', block: 'center'});
                        btn.click();
                        return {success: true, method: 'button-click', text: btnText};
                    }
                }
                
                return {success: false, error: 'No matching navigation element found'};
            """, section_name)
            
            if result and result.get('success'):
                console.print(f"[green]✅ Navigated to '{section_name}' via {result.get('method')}[/green]")
                time.sleep(2)  # Wait for page load
                
                # Handle resource selection if requested
                if click_first_resource or resource_name:
                    return self._select_resource(resource_name, resource_index)
                
                return True
            else:
                console.print(f"[yellow]⚠️  Could not find section '{section_name}'[/yellow]")
                return False
        
        except Exception as e:
            console.print(f"[red]❌ Section navigation failed: {e}[/red]")
            return False
    
    def _select_resource(
        self,
        resource_name: Optional[str] = None,
        resource_index: int = 0
    ) -> bool:
        """
        Select a resource from the current list/table.
        
        Args:
            resource_name: If provided, clicks the resource with this name
            resource_index: If resource_name not provided, clicks this index (default: 0 = first)
        
        Returns:
            bool: True if resource selected successfully
        """
        try:
            if resource_name:
                console.print(f"[cyan]🎯 Selecting resource: '{resource_name}'...[/cyan]")
            else:
                console.print(f"[cyan]🎯 Selecting resource at index {resource_index}...[/cyan]")
            
            result = self.driver.execute_script("""
                var resourceName = arguments[0];
                var resourceIndex = arguments[1];
                console.log('=== Resource Selection ===');
                
                // Look for table rows or list items
                var selectors = [
                    '.awsui-table tbody tr',
                    'table tbody tr',
                    '[role="row"]',
                    'ul li',
                    '.resource-list li',
                    '[data-testid*="resource"]',
                    '[data-testid*="item"]'
                ];
                
                for (var s = 0; s < selectors.length; s++) {
                    var items = document.querySelectorAll(selectors[s]);
                    
                    if (items.length === 0) continue;
                    
                    console.log('Found', items.length, 'resources with selector:', selectors[s]);
                    
                    if (resourceName) {
                        // Search by name
                        var nameLower = resourceName.toLowerCase();
                        for (var i = 0; i < items.length; i++) {
                            var item = items[i];
                            var itemText = (item.textContent || item.innerText || '').toLowerCase();
                            
                            if (itemText.includes(nameLower)) {
                                console.log('✅ Found resource:', resourceName);
                                
                                // Try to find clickable link within item
                                var link = item.querySelector('a');
                                if (link) {
                                    link.scrollIntoView({behavior: 'smooth', block: 'center'});
                                    link.click();
                                    return {success: true, method: 'name-match'};
                                }
                                
                                // Fallback: click the item itself
                                item.scrollIntoView({behavior: 'smooth', block: 'center'});
                                item.click();
                                return {success: true, method: 'name-match-direct'};
                            }
                        }
                    } else {
                        // Select by index
                        if (resourceIndex >= 0 && resourceIndex < items.length) {
                            var item = items[resourceIndex];
                            console.log('✅ Selecting resource at index', resourceIndex);
                            
                            // Try to find clickable link within item
                            var link = item.querySelector('a');
                            if (link) {
                                link.scrollIntoView({behavior: 'smooth', block: 'center'});
                                link.click();
                                return {success: true, method: 'index-select'};
                            }
                            
                            // Fallback: click the item itself
                            item.scrollIntoView({behavior: 'smooth', block: 'center'});
                            item.click();
                            return {success: true, method: 'index-select-direct'};
                        }
                    }
                }
                
                return {success: false, error: 'No matching resource found'};
            """, resource_name, resource_index)
            
            if result and result.get('success'):
                console.print(f"[green]✅ Resource selected via {result.get('method')}[/green]")
                time.sleep(2)  # Wait for page load
                return True
            else:
                console.print(f"[yellow]⚠️  Could not select resource[/yellow]")
                return False
        
        except Exception as e:
            console.print(f"[red]❌ Resource selection failed: {e}[/red]")
            return False
    
    def _navigate_via_search(self, service_name: str, service_key: Optional[str] = None) -> bool:
        """
        UNIVERSAL AWS Console Search - Works for ANY service!
        Uses AWS Console's built-in search (most reliable method)
        """
        try:
            console.print(f"[cyan]🔍 Universal AWS search for '{service_name}'...[/cyan]")

            result = self.driver.execute_script("""
                var serviceName = arguments[0];
                console.log('=== Universal AWS Console Search ===');
                console.log('Searching for:', serviceName);
                
                // STEP 1: Find and click search button (multiple selectors for robustness)
                var searchButton = document.querySelector('[data-testid="awsc-nav-search-button"]') ||
                                 document.querySelector('[aria-label="Search"]') ||
                                 document.querySelector('button[aria-label*="Search"]') ||
                                 document.querySelector('#awsc-nav-search-button') ||
                                 document.querySelector('[data-testid="awsc-header-search-button"]') ||
                                 document.querySelector('button[class*="search"]');
                
                if (!searchButton) {
                    console.log('ERROR: Search button not found');
                    return {success: false, error: 'Search button not found'};
                }
                
                searchButton.click();
                console.log('✅ Clicked search button');
                
                // STEP 2: Wait for search input and type
                setTimeout(function() {
                    var searchInput = document.querySelector('input[type="search"]') ||
                                    document.querySelector('[data-testid="search-input"]') ||
                                    document.querySelector('[data-testid="awsc-header-search-input"]') ||
                                    document.querySelector('input[placeholder*="Search"]') ||
                                    document.querySelector('input[placeholder*="search"]') ||
                                    document.querySelector('#awsc-nav-search-field') ||
                                    document.querySelector('input[aria-label*="Search"]');
                    
                    if (!searchInput) {
                        console.log('ERROR: Search input not found');
                        return;
                    }
                    
                    console.log('✅ Found search input, typing:', serviceName);
                    searchInput.focus();
                    searchInput.value = serviceName;
                    
                    // Trigger all possible events for search
                    searchInput.dispatchEvent(new Event('input', { bubbles: true }));
                    searchInput.dispatchEvent(new Event('change', { bubbles: true }));
                    searchInput.dispatchEvent(new KeyboardEvent('keydown', { bubbles: true, key: 'Enter' }));
                    searchInput.dispatchEvent(new KeyboardEvent('keyup', { bubbles: true, key: 'Enter' }));
                    
                    console.log('✅ Search query sent');
                    
                    // STEP 3: Wait for results and click first service result
                    setTimeout(function() {
                        console.log('Looking for search results...');
                        
                        // Try multiple result selectors (AWS changes UI frequently)
                        var results = document.querySelectorAll('[data-testid="search-result"]') ||
                                    document.querySelectorAll('[data-testid="awsc-nav-service-menu-item"]') ||
                                    document.querySelectorAll('a[href*="console.aws"]') ||
                                    document.querySelectorAll('.awsui-table-row a') ||
                                    document.querySelectorAll('[class*="search-result"]') ||
                                    document.querySelectorAll('[role="option"]') ||
                                    document.querySelectorAll('li[role="option"] a');
                        
                        console.log('Found', results.length, 'search results');
                        
                        if (results.length > 0) {
                            // Filter results to prefer exact service matches
                            var serviceNameLower = serviceName.toLowerCase();
                            var bestResult = null;
                            
                            for (var i = 0; i < results.length; i++) {
                                var result = results[i];
                                var resultText = (result.textContent || result.innerText || '').toLowerCase();
                                
                                console.log('Result', i, ':', resultText.substring(0, 50));
                                
                                // Skip "Recently Viewed" or "Recent" sections
                                if (resultText.includes('recent') && resultText.includes('viewed')) {
                                    console.log('  → Skipping (Recently Viewed section)');
                                    continue;
                                }
                                
                                // Prefer exact matches or service links
                                var href = result.href || '';
                                if (href.includes('console.aws.amazon.com') && !href.includes('/home?')) {
                                    bestResult = result;
                                    console.log('  → Found console link!');
                                    break;
                                }
                                
                                // Fallback: use first non-recent result
                                if (!bestResult && resultText.includes(serviceNameLower)) {
                                    bestResult = result;
                                }
                            }
                            
                            if (bestResult) {
                                console.log('✅ Clicking best result:', (bestResult.textContent || '').substring(0, 50));
                                bestResult.click();
                            } else if (results.length > 0) {
                                console.log('⚠️  No perfect match, clicking first result');
                                results[0].click();
                            }
                        } else {
                            console.log('ERROR: No search results found');
                        }
                    }, 1000); // Increased wait time for results
                }, 500);
                
                return {success: true};
            """, service_name)
            
            time.sleep(5)  # Wait for navigation to complete
            
            current_url = self.driver.current_url
            console.print(f"[dim]   After search, at: {current_url}[/dim]")
            
            # STRICT validation: Must NOT be on homepage
            if '/console/home' in current_url:
                console.print(f"[yellow]⚠️  Search landed on homepage, not actual service[/yellow]")
                return False
            
            # Validate we're on a service console
            if 'console.aws.amazon.com' in current_url and current_url != self.driver.current_url:
                console.print(f"[green]✅ Search navigation successful![/green]")
                return True
            
            # Check if service key in URL
            if service_key and service_key.lower() in current_url.lower():
                console.print(f"[green]✅ Search found {service_name} service![/green]")
                return True
            
            console.print(f"[yellow]⚠️  Search completed but service validation unclear[/yellow]")
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
    
    def handle_pagination(self, screenshot_callback: Optional[Callable] = None, max_pages: int = 50) -> Dict:
        """
        🔄 UNIVERSAL PAGINATION HANDLER - Works for ALL AWS Services!
        
        Automatically detects and navigates through all pages in paginated AWS Console views.
        
        Handles multiple pagination patterns:
        1. Standard AWS pagination (1, 2, 3, ... Next)
        2. "Load more" buttons
        3. Infinite scroll
        4. Dropdown page selectors
        5. "Next" only buttons
        
        Args:
            screenshot_callback: Optional function to call for each page (receives page_number)
            max_pages: Safety limit (default: 50 pages)
        
        Returns:
            Dict with results:
            {
                "total_pages": 8,
                "screenshots": ["page1.png", "page2.png", ...],
                "items_captured": 120,
                "pagination_type": "standard"
            }
        
        Example:
            # Capture all pages of KMS keys
            navigator.navigate_to_service("KMS")
            results = navigator.handle_pagination(
                screenshot_callback=lambda page: f"kms_page_{page}.png"
            )
        """
        console.print("\n[bold cyan]" + "="*60 + "[/bold cyan]")
        console.print("[bold cyan]🔄 PAGINATION HANDLER ACTIVATED[/bold cyan]")
        console.print("[bold cyan]" + "="*60 + "[/bold cyan]\n")
        
        results = {
            "total_pages": 0,
            "screenshots": [],
            "items_captured": 0,
            "pagination_type": "unknown",
            "error": None
        }
        
        current_page = 1
        screenshots = []
        
        try:
            while current_page <= max_pages:
                console.print(f"\n[bold yellow]📄 Page {current_page}[/bold yellow]")
                
                # Wait for page content to load
                time.sleep(2)
                
                # Count items on current page
                items_on_page = self._count_items_on_page()
                results["items_captured"] += items_on_page
                console.print(f"[cyan]   Items on this page: {items_on_page}[/cyan]")
                
                # Take screenshot if callback provided
                if screenshot_callback:
                    try:
                        screenshot_path = screenshot_callback(current_page)
                        screenshots.append(screenshot_path)
                        console.print(f"[green]   ✅ Screenshot saved: {screenshot_path}[/green]")
                    except Exception as e:
                        console.print(f"[yellow]   ⚠️  Screenshot failed: {e}[/yellow]")
                
                # Try to find and click "Next" button
                next_clicked = self._click_next_page()
                
                if not next_clicked:
                    # No more pages
                    console.print(f"[green]✅ Reached end of pagination (Page {current_page})[/green]")
                    break
                
                current_page += 1
                
                # Safety check
                if current_page > max_pages:
                    console.print(f"[yellow]⚠️  Reached max page limit ({max_pages})[/yellow]")
                    break
            
            results["total_pages"] = current_page
            results["screenshots"] = screenshots
            results["pagination_type"] = self._detect_pagination_type()
            
            # Summary
            console.print("\n[bold green]" + "="*60 + "[/bold green]")
            console.print("[bold green]✅ PAGINATION COMPLETE[/bold green]")
            console.print(f"[bold green]   Total Pages: {results['total_pages']}[/bold green]")
            console.print(f"[bold green]   Items Captured: {results['items_captured']}[/bold green]")
            console.print(f"[bold green]   Screenshots: {len(screenshots)}[/bold green]")
            console.print("[bold green]" + "="*60 + "[/bold green]\n")
            
        except Exception as e:
            results["error"] = str(e)
            console.print(f"[red]❌ Pagination error: {e}[/red]")
        
        return results
    
    def _count_items_on_page(self) -> int:
        """Count items/rows on current page"""
        try:
            # Try multiple selectors for different AWS services
            count_script = """
                // Try table rows (most common)
                let rows = document.querySelectorAll('table tbody tr');
                if (rows.length > 0) return rows.length;
                
                // Try cards/tiles
                let cards = document.querySelectorAll('[data-testid*="card"], .awsui-cards-card-container > div');
                if (cards.length > 0) return cards.length;
                
                // Try list items
                let items = document.querySelectorAll('ul[role="list"] > li, ol[role="list"] > li');
                if (items.length > 0) return items.length;
                
                // Try awsui-table rows
                let awsuiRows = document.querySelectorAll('awsui-table tbody tr, [role="row"]');
                if (awsuiRows.length > 1) return awsuiRows.length - 1; // Subtract header
                
                return 0;
            """
            
            count = self.driver.execute_script(count_script)
            return count if count else 0
            
        except Exception as e:
            console.print(f"[dim]   Could not count items: {e}[/dim]")
            return 0
    
    def _click_next_page(self) -> bool:
        """
        Universal "Next Page" clicker - tries multiple strategies
        
        Returns:
            True if successfully clicked next, False if no more pages
        """
        # Strategy 1: Look for "Next" button
        strategies = [
            # AWS Pagination - "Next" button
            {
                "name": "AWS Next Button",
                "script": """
                    let nextBtn = document.querySelector('button[data-testid="pagination-button-next"]') ||
                                  document.querySelector('button:not([disabled])[aria-label*="Next"]') ||
                                  document.querySelector('button:not([disabled])[aria-label*="next"]') ||
                                  document.querySelector('a[aria-label*="Next"]');
                    
                    if (nextBtn && !nextBtn.disabled && !nextBtn.hasAttribute('aria-disabled')) {
                        nextBtn.click();
                        return true;
                    }
                    return false;
                """
            },
            # Numbered pagination - click next number
            {
                "name": "Numbered Pages",
                "script": """
                    let pages = document.querySelectorAll('button[data-testid^="pagination-button-"]:not([aria-current])');
                    let currentPage = document.querySelector('button[data-testid^="pagination-button-"][aria-current="true"]');
                    
                    if (currentPage && pages.length > 0) {
                        // Find the next page number
                        for (let page of pages) {
                            let pageNum = parseInt(page.textContent);
                            let currentNum = parseInt(currentPage.textContent);
                            if (pageNum === currentNum + 1) {
                                page.click();
                                return true;
                            }
                        }
                    }
                    return false;
                """
            },
            # "Load more" button
            {
                "name": "Load More Button",
                "script": """
                    let loadMore = document.querySelector('button:not([disabled])')
                    if (loadMore && loadMore.textContent.match(/load more|show more/i)) {
                        loadMore.click();
                        return true;
                    }
                    return false;
                """
            },
            # Right arrow / chevron
            {
                "name": "Right Arrow Icon",
                "script": """
                    let rightArrow = document.querySelector('button[aria-label*="forward"]') ||
                                     document.querySelector('button svg[data-icon="angle-right"]') ||
                                     document.querySelector('a[rel="next"]');
                    
                    if (rightArrow && !rightArrow.disabled) {
                        rightArrow.click();
                        return true;
                    }
                    return false;
                """
            }
        ]
        
        for strategy in strategies:
            try:
                result = self.driver.execute_script(strategy["script"])
                if result:
                    console.print(f"[dim]   🎯 {strategy['name']} clicked[/dim]")
                    time.sleep(1)  # Wait for page load
                    return True
            except Exception as e:
                continue
        
        # No strategy worked - assume we're at the end
        return False
    
    def _detect_pagination_type(self) -> str:
        """Detect what type of pagination this page uses"""
        try:
            detection_script = """
                if (document.querySelector('button[data-testid="pagination-button-next"]')) {
                    return 'standard-aws';
                }
                if (document.querySelector('button')) {
                    return 'load-more';
                }
                if (document.querySelector('a[rel="next"]')) {
                    return 'link-based';
                }
                return 'unknown';
            """
            
            return self.driver.execute_script(detection_script)
        except:
            return 'unknown'
    
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

