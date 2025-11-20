"""
Tool Registry - Lazy Loading and Tool Management

Provides:
- Lazy loading of tools (load only when needed)
- Tool registration and discovery
- Tool metadata and documentation
- Performance optimization through deferred imports
"""

from typing import Dict, Any, Optional, Callable, Type
from functools import lru_cache
from rich.console import Console

console = Console()


class ToolRegistry:
    """
    Central registry for all tools with lazy loading support.
    
    Tools are registered but not imported until actually needed.
    This significantly reduces startup time and memory usage.
    """
    
    _instance = None
    _tools: Dict[str, Dict[str, Any]] = {}
    _loaded_tools: Dict[str, Any] = {}
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize tool registry."""
        if self._initialized:
            return
        
        self._register_all_tools()
        self._initialized = True
    
    def _register_all_tools(self):
        """Register all available tools (without importing them)."""
        # AWS Tools
        self.register(
            name="aws_export_data",
            module="tools.aws_universal_export",
            function="export_aws_data",
            description="Export AWS resources to CSV/JSON",
            category="aws"
        )
        
        self.register(
            name="aws_take_screenshot",
            module="ai_brain.tool_executor",
            method="_execute_aws_screenshot",
            description="Capture AWS console screenshots",
            category="aws"
        )
        
        self.register(
            name="aws_console_action",
            module="ai_brain.tool_executor",
            method="_execute_aws_console_action",
            description="Universal AWS console actions",
            category="aws"
        )
        
        self.register(
            name="list_aws_resources",
            module="ai_brain.tool_executor",
            method="_execute_list_aws",
            description="List AWS resources",
            category="aws"
        )
        
        # SharePoint Tools
        self.register(
            name="upload_to_sharepoint",
            module="ai_brain.tool_executor",
            method="_execute_upload",
            description="Upload files to SharePoint",
            category="sharepoint"
        )
        
        self.register(
            name="show_local_evidence",
            module="ai_brain.tool_executor",
            method="_execute_show_evidence",
            description="Show local evidence files",
            category="evidence"
        )
        
        # Self-healing Tools
        self.register(
            name="read_tool_source",
            module="ai_brain.tool_executor",
            method="_execute_read_tool_source",
            description="Read tool source code",
            category="self_healing"
        )
        
        self.register(
            name="fix_tool_code",
            module="ai_brain.tool_executor",
            method="_execute_fix_tool_code",
            description="Fix tool code automatically",
            category="self_healing"
        )
        
        # Web Search
        self.register(
            name="web_search",
            module="ai_brain.tool_executor",
            method="_execute_web_search",
            description="Search the web for real-time information",
            category="knowledge"
        )
        
        console.print(f"[dim]📦 Registered {len(self._tools)} tools (lazy loading enabled)[/dim]")
    
    def register(
        self,
        name: str,
        module: str,
        function: Optional[str] = None,
        method: Optional[str] = None,
        class_name: Optional[str] = None,
        description: str = "",
        category: str = "general"
    ):
        """
        Register a tool without importing it.
        
        Args:
            name: Tool name
            module: Module path (e.g., "tools.aws_export")
            function: Function name (if standalone function)
            method: Method name (if class method)
            class_name: Class name (if method)
            description: Tool description
            category: Tool category
        """
        self._tools[name] = {
            "module": module,
            "function": function,
            "method": method,
            "class_name": class_name,
            "description": description,
            "category": category,
            "loaded": False
        }
    
    def get_tool(self, name: str, executor_instance: Optional[Any] = None) -> Optional[Callable]:
        """
        Get tool function/method (lazy loads if not already loaded).
        
        Args:
            name: Tool name
            executor_instance: ToolExecutor instance (for methods)
            
        Returns:
            Callable tool function/method or None
        """
        if name not in self._tools:
            console.print(f"[yellow]⚠️  Tool '{name}' not registered[/yellow]")
            return None
        
        tool_info = self._tools[name]
        
        # Return cached if already loaded
        if name in self._loaded_tools:
            tool = self._loaded_tools[name]
            if tool_info.get("method") and executor_instance:
                return getattr(executor_instance, tool_info["method"], None)
            return tool
        
        # Lazy load the tool
        try:
            module_path = tool_info["module"]
            module = __import__(module_path, fromlist=[module_path.split('.')[-1]])
            
            if tool_info.get("function"):
                # Standalone function
                tool = getattr(module, tool_info["function"])
                self._loaded_tools[name] = tool
                console.print(f"[dim]📦 Loaded tool: {name}[/dim]")
                return tool
            
            elif tool_info.get("method") and executor_instance:
                # Class method (already available on executor)
                method = getattr(executor_instance, tool_info["method"], None)
                if method:
                    console.print(f"[dim]📦 Using tool method: {name}[/dim]")
                    return method
            
            elif tool_info.get("class_name"):
                # Class instance
                cls = getattr(module, tool_info["class_name"])
                tool = cls()
                self._loaded_tools[name] = tool
                console.print(f"[dim]📦 Loaded tool class: {name}[/dim]")
                return tool
            
        except ImportError as e:
            console.print(f"[red]❌ Failed to load tool '{name}': {e}[/red]")
            return None
        except AttributeError as e:
            console.print(f"[red]❌ Tool '{name}' not found in module: {e}[/red]")
            return None
        
        return None
    
    def list_tools(self, category: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        List all registered tools.
        
        Args:
            category: Optional category filter
            
        Returns:
            Dict of tool names to tool info
        """
        if category:
            return {
                name: info
                for name, info in self._tools.items()
                if info.get("category") == category
            }
        return self._tools.copy()
    
    def get_tool_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get tool metadata."""
        return self._tools.get(name)
    
    def clear_cache(self):
        """Clear loaded tools cache (for testing/reloading)."""
        self._loaded_tools.clear()
        console.print("[dim]🧹 Cleared tool cache[/dim]")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get registry statistics."""
        return {
            "total_tools": len(self._tools),
            "loaded_tools": len(self._loaded_tools),
            "load_percentage": f"{(len(self._loaded_tools) / len(self._tools) * 100):.1f}%" if self._tools else "0%"
        }


# Global registry instance
_registry = None


def get_tool_registry() -> ToolRegistry:
    """Get global tool registry instance."""
    global _registry
    if _registry is None:
        _registry = ToolRegistry()
    return _registry

