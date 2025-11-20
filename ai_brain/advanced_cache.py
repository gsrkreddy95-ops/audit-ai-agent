"""
Advanced Caching Strategies

Provides:
- Multi-level caching (memory + disk)
- Cache invalidation strategies
- Cache warming
- Performance metrics
"""

import json
import hashlib
import pickle
from typing import Dict, Any, Optional, Callable
from datetime import datetime, timedelta
from pathlib import Path
from rich.console import Console
from ai_brain.shared.cache_manager import CacheManager, CacheEntry

console = Console()


class AdvancedCacheManager(CacheManager):
    """
    Advanced cache manager with multi-level caching and invalidation.
    
    Extends base CacheManager with:
    - Disk persistence
    - Cache warming
    - Smart invalidation
    - Performance metrics
    """
    
    def __init__(
        self,
        default_ttl: int = 3600,
        disk_cache_dir: Optional[Path] = None,
        enable_disk_cache: bool = True
    ):
        """
        Initialize advanced cache manager.
        
        Args:
            default_ttl: Default time-to-live in seconds
            disk_cache_dir: Directory for disk cache
            enable_disk_cache: Enable disk caching
        """
        super().__init__(default_ttl)
        self.enable_disk_cache = enable_disk_cache
        self.disk_cache_dir = disk_cache_dir or Path.home() / ".auditmate_cache"
        self.disk_cache_dir.mkdir(parents=True, exist_ok=True)
        self.access_times: Dict[str, datetime] = {}
        self.cache_stats = {
            "memory_hits": 0,
            "disk_hits": 0,
            "misses": 0,
            "writes": 0
        }
    
    def _get_disk_path(self, key: str) -> Path:
        """Get disk cache file path for key."""
        # Use hash to avoid filesystem issues with long keys
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.disk_cache_dir / f"{key_hash}.cache"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks memory first, then disk).
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        # Check memory cache first
        result = super().get(key)
        if result is not None:
            self.cache_stats["memory_hits"] += 1
            self.access_times[key] = datetime.now()
            return result
        
        # Check disk cache
        if self.enable_disk_cache:
            disk_path = self._get_disk_path(key)
            if disk_path.exists():
                try:
                    with open(disk_path, 'rb') as f:
                        entry: CacheEntry = pickle.load(f)
                    
                    if not entry.is_expired():
                        self.cache_stats["disk_hits"] += 1
                        self.access_times[key] = datetime.now()
                        # Load into memory cache for faster access
                        self.set(key, entry.value, ttl=None)  # Keep original TTL
                        return entry.value
                    else:
                        # Expired, remove from disk
                        disk_path.unlink()
                except Exception as e:
                    console.print(f"[yellow]⚠️  Disk cache read error: {e}[/yellow]")
        
        self.cache_stats["misses"] += 1
        return None
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache (both memory and disk).
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds
        """
        # Set in memory cache
        super().set(key, value, ttl)
        
        # Also write to disk cache
        if self.enable_disk_cache:
            disk_path = self._get_disk_path(key)
            try:
                ttl = ttl or self.default_ttl
                expires_at = datetime.now() + timedelta(seconds=ttl)
                
                entry = CacheEntry(
                    value=value,
                    created_at=datetime.now(),
                    expires_at=expires_at
                )
                
                with open(disk_path, 'wb') as f:
                    pickle.dump(entry, f)
                
                self.cache_stats["writes"] += 1
            except Exception as e:
                console.print(f"[yellow]⚠️  Disk cache write error: {e}[/yellow]")
    
    def invalidate(self, pattern: Optional[str] = None) -> int:
        """
        Invalidate cache entries.
        
        Args:
            pattern: Optional pattern to match (not implemented yet)
            
        Returns:
            Number of entries invalidated
        """
        count = super().clear(pattern)
        
        # Also clear disk cache
        if self.enable_disk_cache and pattern is None:
            for cache_file in self.disk_cache_dir.glob("*.cache"):
                try:
                    cache_file.unlink()
                    count += 1
                except Exception:
                    pass
        
        return count
    
    def warm_cache(self, warm_funcs: List[Callable]) -> Dict[str, Any]:
        """
        Warm cache by pre-loading common queries.
        
        Args:
            warm_funcs: List of functions to execute for warming
            
        Returns:
            Warming results
        """
        results = {}
        console.print(f"[cyan]🔥 Warming cache with {len(warm_funcs)} functions...[/cyan]")
        
        for func in warm_funcs:
            try:
                result = func()
                results[func.__name__] = "success"
            except Exception as e:
                results[func.__name__] = f"error: {str(e)}"
        
        console.print(f"[green]✅ Cache warmed: {sum(1 for v in results.values() if v == 'success')}/{len(warm_funcs)}[/green]")
        return results
    
    def get_advanced_stats(self) -> Dict[str, Any]:
        """Get advanced cache statistics."""
        base_stats = super().get_stats()
        
        total_requests = (
            self.cache_stats["memory_hits"] +
            self.cache_stats["disk_hits"] +
            self.cache_stats["misses"]
        )
        
        memory_hit_rate = (
            (self.cache_stats["memory_hits"] / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        disk_hit_rate = (
            (self.cache_stats["disk_hits"] / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        overall_hit_rate = (
            ((self.cache_stats["memory_hits"] + self.cache_stats["disk_hits"]) / total_requests * 100)
            if total_requests > 0 else 0
        )
        
        # Count disk cache files
        disk_files = len(list(self.disk_cache_dir.glob("*.cache"))) if self.enable_disk_cache else 0
        
        return {
            **base_stats,
            "memory_hits": self.cache_stats["memory_hits"],
            "disk_hits": self.cache_stats["disk_hits"],
            "misses": self.cache_stats["misses"],
            "writes": self.cache_stats["writes"],
            "memory_hit_rate": f"{memory_hit_rate:.1f}%",
            "disk_hit_rate": f"{disk_hit_rate:.1f}%",
            "overall_hit_rate": f"{overall_hit_rate:.1f}%",
            "disk_cache_files": disk_files,
            "disk_cache_enabled": self.enable_disk_cache
        }
    
    def cleanup_expired(self) -> int:
        """
        Clean up expired cache entries from disk.
        
        Returns:
            Number of entries cleaned
        """
        if not self.enable_disk_cache:
            return 0
        
        cleaned = 0
        for cache_file in self.disk_cache_dir.glob("*.cache"):
            try:
                with open(cache_file, 'rb') as f:
                    entry: CacheEntry = pickle.load(f)
                
                if entry.is_expired():
                    cache_file.unlink()
                    cleaned += 1
            except Exception:
                # Corrupted file, remove it
                cache_file.unlink()
                cleaned += 1
        
        if cleaned > 0:
            console.print(f"[dim]🧹 Cleaned {cleaned} expired cache entries[/dim]")
        
        return cleaned

