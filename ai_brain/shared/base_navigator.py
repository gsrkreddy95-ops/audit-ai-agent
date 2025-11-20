"""
Base Navigator - Common navigation patterns for AWS console.

Provides:
- Standardized navigation methods
- Common wait strategies
- Element finding patterns
- Error recovery
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from rich.console import Console

console = Console()


class BaseNavigator(ABC):
    """Abstract base class for AWS console navigators."""
    
    def __init__(self, driver, region: str = "us-east-1"):
        """
        Initialize base navigator.
        
        Args:
            driver: Selenium/Playwright driver
            region: AWS region
        """
        self.driver = driver
        self.region = region
    
    @abstractmethod
    def navigate_to_service(self, service: str, **kwargs) -> bool:
        """
        Navigate to AWS service.
        
        Args:
            service: Service name
            **kwargs: Additional options
            
        Returns:
            True if successful
        """
        pass
    
    def wait_for_element(
        self,
        selector: str,
        timeout: int = 10,
        by: str = "css"
    ) -> Optional[Any]:
        """
        Wait for element to appear.
        
        Args:
            selector: Element selector
            timeout: Timeout in seconds
            by: Selector type ('css', 'xpath', 'id', 'name')
            
        Returns:
            Element if found, None otherwise
        """
        # Implementation depends on driver type (Selenium vs Playwright)
        # This is a placeholder - subclasses should implement
        pass
    
    def find_element_safe(
        self,
        selector: str,
        by: str = "css",
        timeout: int = 5
    ) -> Optional[Any]:
        """
        Safely find element with timeout.
        
        Args:
            selector: Element selector
            by: Selector type
            timeout: Timeout in seconds
            
        Returns:
            Element if found, None otherwise
        """
        try:
            return self.wait_for_element(selector, timeout, by)
        except Exception as e:
            console.print(f"[yellow]⚠️  Element not found: {selector} ({e})[/yellow]")
            return None
    
    def click_safe(self, element: Any, description: str = "element") -> bool:
        """
        Safely click element with error handling.
        
        Args:
            element: Element to click
            description: Description for logging
            
        Returns:
            True if successful
        """
        if element is None:
            console.print(f"[red]❌ Cannot click {description}: element is None[/red]")
            return False
        
        try:
            element.click()
            return True
        except Exception as e:
            console.print(f"[red]❌ Failed to click {description}: {e}[/red]")
            return False
    
    def get_current_url(self) -> str:
        """Get current page URL."""
        return self.driver.current_url if hasattr(self.driver, 'current_url') else ""
    
    def wait_for_page_load(self, timeout: int = 30) -> bool:
        """
        Wait for page to load.
        
        Args:
            timeout: Timeout in seconds
            
        Returns:
            True if page loaded successfully
        """
        # Implementation depends on driver type
        # This is a placeholder - subclasses should implement
        return True

