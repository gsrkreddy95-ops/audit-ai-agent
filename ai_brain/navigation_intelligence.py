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
    
    def learn_navigation_path(self, service: str, resource_type: str, url: str) -> None:
        """
        Store a successful navigation path.
        
        Args:
            service: Service name
            resource_type: Resource type  
            url: Successful URL
        """
        if service not in self.learned_paths:
            self.learned_paths[service] = {}
        
        self.learned_paths[service][resource_type] = url
        console.print(f"[dim]📍 Learned navigation: {service}/{resource_type}[/dim]")
    
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
