"""
Connection Pool - AWS client connection pooling.

Reuses AWS clients to reduce overhead and improve performance.
"""

from typing import Dict, Optional, Any
from threading import Lock
import boto3
from rich.console import Console

console = Console()


class ConnectionPool:
    """Manages pool of AWS service clients."""
    
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        """Singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize connection pool."""
        if self._initialized:
            return
        
        self._clients: Dict[str, Any] = {}
        self._sessions: Dict[str, boto3.Session] = {}
        self._lock = Lock()
        self._initialized = True
    
    def get_client(
        self,
        service: str,
        region: str = "us-east-1",
        profile: Optional[str] = None,
        **kwargs
    ) -> Any:
        """
        Get or create AWS service client.
        
        Args:
            service: AWS service name (e.g., 's3', 'ec2')
            region: AWS region
            profile: AWS profile name
            **kwargs: Additional client arguments
            
        Returns:
            AWS service client
        """
        # Generate cache key
        key = f"{service}:{region}:{profile or 'default'}"
        
        with self._lock:
            if key not in self._clients:
                # Get or create session
                session_key = f"{profile or 'default'}:{region}"
                if session_key not in self._sessions:
                    if profile:
                        session = boto3.Session(profile_name=profile, region_name=region)
                    else:
                        session = boto3.Session(region_name=region)
                    self._sessions[session_key] = session
                else:
                    session = self._sessions[session_key]
                
                # Create client
                client = session.client(service, region_name=region, **kwargs)
                self._clients[key] = client
                console.print(f"[dim]🔌 Created new {service} client for {region}[/dim]")
            
            return self._clients[key]
    
    def clear(self, service: Optional[str] = None, region: Optional[str] = None):
        """
        Clear cached clients.
        
        Args:
            service: Optional service name to clear (all if None)
            region: Optional region to clear (all if None)
        """
        with self._lock:
            if service is None and region is None:
                self._clients.clear()
                self._sessions.clear()
                console.print("[dim]🧹 Cleared all connection pool entries[/dim]")
            else:
                keys_to_remove = [
                    key for key in self._clients.keys()
                    if (service is None or key.startswith(f"{service}:"))
                    and (region is None or f":{region}:" in key or key.endswith(f":{region}"))
                ]
                for key in keys_to_remove:
                    del self._clients[key]
    
    def get_stats(self) -> Dict[str, int]:
        """
        Get connection pool statistics.
        
        Returns:
            Dict with stats
        """
        return {
            "clients": len(self._clients),
            "sessions": len(self._sessions)
        }

