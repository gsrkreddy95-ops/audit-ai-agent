"""
Optimized Browser Session Manager - Enhanced with advanced features

New features added in this optimization:
1. Session idle timeout management
2. Session health monitoring with metrics
3. Memory management and cleanup
4. Session pool optimization
5. Automatic session recovery
6. Session statistics and telemetry
7. Session lifecycle hooks
"""

import time
import psutil
import threading
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable
from dataclasses import dataclass, field
from collections import defaultdict
from rich.console import Console

console = Console()


@dataclass
class SessionMetrics:
    """Metrics for a browser session"""
    account: str
    created_at: datetime
    last_used: datetime
    request_count: int = 0
    error_count: int = 0
    memory_usage_mb: float = 0.0
    is_healthy: bool = True
    health_check_failures: int = 0


class SessionPool:
    """Manages a pool of browser sessions with optimizations"""
    
    def __init__(self, 
                 max_sessions: int = 3,
                 session_idle_timeout: int = 600,  # 10 minutes
                 health_check_interval: int = 60,   # 1 minute
                 memory_threshold_mb: float = 500.0):
        """
        Initialize session pool
        
        Args:
            max_sessions: Maximum concurrent browser sessions
            session_idle_timeout: Seconds before idle session is closed
            health_check_interval: Seconds between health checks
            memory_threshold_mb: MB threshold for memory warnings
        """
        self.max_sessions = max_sessions
        self.session_idle_timeout = session_idle_timeout
        self.health_check_interval = health_check_interval
        self.memory_threshold_mb = memory_threshold_mb
        
        self._sessions: Dict[str, any] = {}
        self._metrics: Dict[str, SessionMetrics] = {}
        self._lock = threading.Lock()
        self._cleanup_thread = None
        self._running = False
        
        # Lifecycle hooks
        self._on_session_created: List[Callable] = []
        self._on_session_closed: List[Callable] = []
        self._on_session_error: List[Callable] = []
        
        # Start background monitoring
        self._start_monitoring()
    
    def _start_monitoring(self):
        """Start background monitoring thread"""
        if self._cleanup_thread and self._cleanup_thread.is_alive():
            return
        
        self._running = True
        self._cleanup_thread = threading.Thread(target=self._monitor_sessions, daemon=True)
        self._cleanup_thread.start()
        console.print("[dim]🔍 Browser session monitoring started[/dim]")
    
    def _monitor_sessions(self):
        """Background thread to monitor and cleanup sessions"""
        while self._running:
            try:
                time.sleep(self.health_check_interval)
                self._perform_health_checks()
                self._cleanup_idle_sessions()
                self._check_memory_usage()
            except Exception as e:
                console.print(f"[yellow]⚠️  Session monitoring error: {e}[/yellow]")
    
    def _perform_health_checks(self):
        """Check health of all active sessions"""
        with self._lock:
            for account, browser in list(self._sessions.items()):
                metrics = self._metrics.get(account)
                if not metrics:
                    continue
                
                driver = getattr(browser, 'driver', None)
                if not driver:
                    metrics.is_healthy = False
                    metrics.health_check_failures += 1
                    continue
                
                try:
                    # Quick health check
                    driver.execute_script("return 1")
                    metrics.is_healthy = True
                    metrics.health_check_failures = 0
                except:
                    metrics.is_healthy = False
                    metrics.health_check_failures += 1
                    
                    # Close session if too many failures
                    if metrics.health_check_failures >= 3:
                        console.print(f"[yellow]⚠️  Session {account} failed health checks, closing...[/yellow]")
                        self._close_session(account)
    
    def _cleanup_idle_sessions(self):
        """Close sessions that have been idle too long"""
        current_time = datetime.now()
        
        with self._lock:
            for account, metrics in list(self._metrics.items()):
                idle_seconds = (current_time - metrics.last_used).total_seconds()
                
                if idle_seconds > self.session_idle_timeout:
                    console.print(f"[yellow]⏰ Session {account} idle for {int(idle_seconds)}s, closing...[/yellow]")
                    self._close_session(account)
    
    def _check_memory_usage(self):
        """Monitor memory usage of browser sessions"""
        try:
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            
            with self._lock:
                for account, metrics in self._metrics.items():
                    # Estimate per-session memory
                    metrics.memory_usage_mb = memory_mb / max(len(self._sessions), 1)
                    
                    if metrics.memory_usage_mb > self.memory_threshold_mb:
                        console.print(f"[yellow]⚠️  Session {account} using {metrics.memory_usage_mb:.1f}MB (high memory!)[/yellow]")
        except:
            pass
    
    def get_session(self, account: str, force_new: bool = False) -> Optional[any]:
        """
        Get or create a browser session
        
        Args:
            account: Account identifier
            force_new: Force create new session
            
        Returns:
            Browser instance or None
        """
        with self._lock:
            # Update last used time
            if account in self._metrics:
                self._metrics[account].last_used = datetime.now()
                self._metrics[account].request_count += 1
            
            # Check if session exists and is valid
            if not force_new and account in self._sessions:
                browser = self._sessions[account]
                metrics = self._metrics.get(account)
                
                if metrics and metrics.is_healthy:
                    console.print(f"[dim]♻️  Reusing healthy session for {account}[/dim]")
                    return browser
                else:
                    console.print(f"[yellow]⚠️  Session {account} unhealthy, recreating...[/yellow]")
                    self._close_session(account)
            
            # Check session limit
            if len(self._sessions) >= self.max_sessions:
                # Close least recently used session
                oldest_account = min(
                    self._metrics.items(),
                    key=lambda x: x[1].last_used
                )[0]
                console.print(f"[yellow]⚠️  Max sessions reached, closing {oldest_account}[/yellow]")
                self._close_session(oldest_account)
            
            # Create new session
            browser = self._create_browser_instance(account)
            
            if browser:
                self._sessions[account] = browser
                self._metrics[account] = SessionMetrics(
                    account=account,
                    created_at=datetime.now(),
                    last_used=datetime.now()
                )
                
                # Trigger lifecycle hook
                for callback in self._on_session_created:
                    try:
                        callback(account, browser)
                    except:
                        pass
                
                console.print(f"[green]✅ Created new session for {account}[/green]")
                return browser
            
            return None
    
    def _create_browser_instance(self, account: str):
        """Create a new browser instance"""
        try:
            from tools.universal_screenshot_enhanced import UniversalScreenshotEnhanced
            import os
            
            profile_base = os.path.expanduser("~/.audit-agent-browsers")
            os.makedirs(profile_base, exist_ok=True)
            account_profile = os.path.join(profile_base, f"profile-{account}")
            
            browser = UniversalScreenshotEnhanced(
                headless=False,
                timeout=180,
                debug=True,
                persistent_profile=True,
                profile_dir=account_profile
            )
            
            if browser.connect():
                return browser
            
            return None
        except Exception as e:
            console.print(f"[red]❌ Failed to create browser for {account}: {e}[/red]")
            
            # Trigger error hook
            for callback in self._on_session_error:
                try:
                    callback(account, e)
                except:
                    pass
            
            return None
    
    def _close_session(self, account: str):
        """Close a specific session"""
        if account not in self._sessions:
            return
        
        browser = self._sessions[account]
        
        try:
            browser.close()
        except:
            pass
        
        del self._sessions[account]
        
        # Trigger lifecycle hook
        for callback in self._on_session_closed:
            try:
                callback(account)
            except:
                pass
        
        if account in self._metrics:
            console.print(f"[dim]📊 Session {account} stats: {self._metrics[account].request_count} requests, {self._metrics[account].error_count} errors[/dim]")
            del self._metrics[account]
    
    def record_error(self, account: str):
        """Record an error for a session"""
        with self._lock:
            if account in self._metrics:
                self._metrics[account].error_count += 1
    
    def get_stats(self) -> Dict:
        """Get session pool statistics"""
        with self._lock:
            return {
                "active_sessions": len(self._sessions),
                "max_sessions": self.max_sessions,
                "total_requests": sum(m.request_count for m in self._metrics.values()),
                "total_errors": sum(m.error_count for m in self._metrics.values()),
                "sessions": {
                    account: {
                        "created_at": m.created_at.isoformat(),
                        "last_used": m.last_used.isoformat(),
                        "idle_seconds": (datetime.now() - m.last_used).total_seconds(),
                        "requests": m.request_count,
                        "errors": m.error_count,
                        "memory_mb": m.memory_usage_mb,
                        "healthy": m.is_healthy
                    }
                    for account, m in self._metrics.items()
                }
            }
    
    def register_hook(self, event: str, callback: Callable):
        """Register lifecycle hook"""
        if event == "session_created":
            self._on_session_created.append(callback)
        elif event == "session_closed":
            self._on_session_closed.append(callback)
        elif event == "session_error":
            self._on_session_error.append(callback)
    
    def shutdown(self):
        """Shutdown the session pool"""
        console.print("[yellow]🔒 Shutting down session pool...[/yellow]")
        self._running = False
        
        if self._cleanup_thread:
            self._cleanup_thread.join(timeout=2)
        
        with self._lock:
            for account in list(self._sessions.keys()):
                self._close_session(account)
        
        console.print("[green]✅ Session pool shutdown complete[/green]")


# Global session pool instance
_session_pool = SessionPool(
    max_sessions=3,
    session_idle_timeout=600,  # 10 minutes
    health_check_interval=60,  # 1 minute
    memory_threshold_mb=500.0
)


def get_optimized_session_pool() -> SessionPool:
    """Get the global optimized session pool"""
    return _session_pool

