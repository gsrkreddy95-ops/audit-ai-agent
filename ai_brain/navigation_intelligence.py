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
    
    def learn_navigation_path(self, service=None, resource_type=None, url=None, **kwargs):
        """
        Store/retrieve navigation path with flexible signature.
        
        Supports both:
        - learn_navigation_path(service, resource_type, url)
        - learn_navigation_path(platform="aws", service="iam", target="identity_provider", ...)
        
        Returns:
            Learned URL if available, or instructions dict
        """
        # Extract from kwargs if not provided as positional
        service = service or kwargs.get('service')
        resource_type = resource_type or kwargs.get('resource_type') or kwargs.get('target')
        url = url or kwargs.get('url') or kwargs.get('current_url')
        
        # If being called to GET learned path (no url provided)
        if service and resource_type and not url:
            learned_url = self.get_learned_navigation(service, resource_type)
            if learned_url:
                return {"url": learned_url, "learned": True}
            return None
        
        # If being called to STORE a path
        if service and resource_type and url:
            if service not in self.learned_paths:
                self.learned_paths[service] = {}
            
            self.learned_paths[service][resource_type] = url
            console.print(f"[dim]📍 Learned navigation: {service}/{resource_type}[/dim]")
            return {"success": True}
        
        return None
    
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
