"""
Shared utilities and base classes for the audit-ai-agent.

This module provides:
- BaseTool: Abstract base class for all tools
- BaseNavigator: Common navigation patterns
- ErrorHandler: Standardized error handling
- CacheManager: LLM response caching
- ConnectionPool: AWS client pooling
"""

from .base_tool import BaseTool
from .base_navigator import BaseNavigator
from .error_handler import ErrorHandler, RetryConfig
from .cache_manager import CacheManager
from .connection_pool import ConnectionPool

__all__ = [
    'BaseTool',
    'BaseNavigator',
    'ErrorHandler',
    'RetryConfig',
    'CacheManager',
    'ConnectionPool',
]

