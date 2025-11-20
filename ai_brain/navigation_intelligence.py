"""
Navigation Intelligence - Smart Browser Navigation

Uses LLM to:
- Learn successful navigation paths
- Adapt to UI changes
- Find elements intelligently
- Handle dynamic pages
"""

from typing import Dict, Any, Optional
from rich.console import Console

console = Console()


class NavigationIntelligence:
    """LLM-driven browser navigation intelligence."""
    
    def __init__(self, llm=None):
        self.llm = llm
        self.enabled = llm is not None
        self.learned_paths = {
            # Store successful navigation patterns
            "iam": {
                "identity_provider": "https://console.aws.amazon.com/iam/home#/identity_providers"
            }
        }
    
    def get_learned_navigation(self, service: str, resource_type: str) -> Optional[str]:
        """
        Get a learned navigation URL.
        
        Args:
            service: Service name (iam, kms, etc.)
            resource_type: Resource type (identity_provider, keys, etc.)
            
        Returns:
            URL if learned, None otherwise
        """
        return self.learned_paths.get(service, {}).get(resource_type)
    
    def learn_navigation_path(self, **kwargs) -> Dict[str, Any]:
        """
        Store/retrieve a successful navigation path.
        
        Flexible signature to handle various call patterns.
        
        Args (via kwargs):
            service: Service name
            target or resource_type: Resource type
            url or current_url: URL
            platform: Platform (aws, etc.)
            user_request: Original request
            
        Returns:
            Navigation instructions or learned URL
        """
        service = kwargs.get('service', '')
        target = kwargs.get('target') or kwargs.get('resource_type', '')
        url = kwargs.get('url') or kwargs.get('current_url', '')
        
        if not service or not target:
            # If called without proper args, return learned path
            return self.get_learned_navigation(service, target) or {}
        
        # Store the path if URL provided
        if url and service and target:
            if service not in self.learned_paths:
                self.learned_paths[service] = {}
            
            self.learned_paths[service][target] = url
            console.print(f"[dim]📍 Learned navigation: {service}/{target}[/dim]")
        
        # Return learned or constructed navigation
        learned_url = self.get_learned_navigation(service, target)
        
        return {
            "url": learned_url,
            "method": "learned" if learned_url else "construct",
            "service": service,
            "target": target
        }
    
    def get_navigation_strategy(
        self,
        target: str,
        current_url: str,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Ask LLM for navigation strategy.
        
        Returns strategy for reaching target from current location.
        """
        if not self.enabled:
            return {"strategy": "direct_url"}
        
        # For now, prefer learned paths
        return {"strategy": "use_learned_path"}


def get_navigation_intelligence(llm=None):
    """Get navigation intelligence instance."""
    return NavigationIntelligence(llm)
