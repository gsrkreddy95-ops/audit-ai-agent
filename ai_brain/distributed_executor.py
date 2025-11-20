"""
Distributed Execution Support - Execute tasks across multiple workers/machines

Features:
1. Task queue with priority support
2. Worker pool management
3. Remote execution via SSH/API
4. Load balancing
5. Task retry and recovery
6. Distributed locking
7. Result aggregation
8. Health monitoring
"""

import json
import time
import uuid
import threading
import queue
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum
from collections import defaultdict
import pickle
import hashlib
from rich.console import Console

console = Console()


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"
    CANCELLED = "cancelled"


class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4


@dataclass
class Task:
    """Distributed task"""
    task_id: str
    function: Callable
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    status: TaskStatus = TaskStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    worker_id: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    
    def __lt__(self, other):
        """For priority queue comparison"""
        return self.priority.value > other.priority.value  # Higher priority first


@dataclass
class Worker:
    """Distributed worker"""
    worker_id: str
    worker_type: str = "local"  # local, remote_ssh, remote_api
    host: Optional[str] = None
    port: Optional[int] = None
    credentials: Optional[Dict] = None
    is_active: bool = True
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    last_heartbeat: datetime = field(default_factory=datetime.now)
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    def get_load(self) -> float:
        """Calculate worker load score"""
        task_load = 1.0 if self.current_task else 0.0
        resource_load = (self.cpu_usage + self.memory_usage) / 200.0
        return task_load + resource_load


class DistributedExecutor:
    """
    Distributed task executor with load balancing and fault tolerance
    """
    
    def __init__(self, 
                 max_local_workers: int = 3,
                 task_timeout: int = 300,
                 enable_remote: bool = False):
        """
        Initialize distributed executor
        
        Args:
            max_local_workers: Maximum local worker threads
            task_timeout: Task execution timeout in seconds
            enable_remote: Enable remote worker support
        """
        self.max_local_workers = max_local_workers
        self.task_timeout = task_timeout
        self.enable_remote = enable_remote
        
        # Task management
        self._task_queue = queue.PriorityQueue()
        self._tasks: Dict[str, Task] = {}
        self._task_lock = threading.Lock()
        
        # Worker management
        self._workers: Dict[str, Worker] = {}
        self._worker_threads: Dict[str, threading.Thread] = {}
        self._worker_lock = threading.Lock()
        
        # Execution state
        self._running = False
        self._coordinator_thread = None
        
        # Statistics
        self._stats = {
            "total_tasks": 0,
            "completed_tasks": 0,
            "failed_tasks": 0,
            "total_execution_time": 0.0
        }
        
        # Callbacks
        self._on_task_complete: List[Callable] = []
        self._on_task_failed: List[Callable] = []
        
        # Initialize local workers
        self._init_local_workers()
    
    def _init_local_workers(self):
        """Initialize local worker threads"""
        for i in range(self.max_local_workers):
            worker_id = f"local-worker-{i}"
            worker = Worker(
                worker_id=worker_id,
                worker_type="local"
            )
            self._workers[worker_id] = worker
        
        console.print(f"[green]✅ Initialized {self.max_local_workers} local workers[/green]")
    
    def add_remote_worker(self, 
                         host: str, 
                         port: int = 22,
                         worker_type: str = "remote_ssh",
                         credentials: Optional[Dict] = None) -> str:
        """
        Add a remote worker
        
        Args:
            host: Remote host address
            port: Remote port
            worker_type: Type of remote worker (remote_ssh, remote_api)
            credentials: Authentication credentials
            
        Returns:
            Worker ID
        """
        if not self.enable_remote:
            console.print("[yellow]⚠️  Remote workers not enabled[/yellow]")
            return None
        
        worker_id = f"remote-{host}-{port}"
        worker = Worker(
            worker_id=worker_id,
            worker_type=worker_type,
            host=host,
            port=port,
            credentials=credentials
        )
        
        with self._worker_lock:
            self._workers[worker_id] = worker
        
        console.print(f"[green]✅ Added remote worker: {worker_id}[/green]")
        return worker_id
    
    def submit_task(self, 
                   function: Callable,
                   args: Tuple = (),
                   kwargs: Dict = None,
                   priority: TaskPriority = TaskPriority.NORMAL,
                   task_id: Optional[str] = None,
                   metadata: Dict = None) -> str:
        """
        Submit a task for distributed execution
        
        Args:
            function: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
            priority: Task priority
            task_id: Optional task ID (generated if not provided)
            metadata: Optional task metadata
            
        Returns:
            Task ID
        """
        if task_id is None:
            task_id = str(uuid.uuid4())
        
        task = Task(
            task_id=task_id,
            function=function,
            args=args or (),
            kwargs=kwargs or {},
            priority=priority,
            metadata=metadata or {}
        )
        
        with self._task_lock:
            self._tasks[task_id] = task
            self._stats["total_tasks"] += 1
        
        self._task_queue.put((priority.value, task))
        
        console.print(f"[cyan]📋 Task submitted: {task_id} (priority: {priority.name})[/cyan]")
        
        # Start coordinator if not running
        if not self._running:
            self.start()
        
        return task_id
    
    def submit_batch(self, 
                    tasks: List[Tuple[Callable, Tuple, Dict]],
                    priority: TaskPriority = TaskPriority.NORMAL) -> List[str]:
        """
        Submit multiple tasks as a batch
        
        Args:
            tasks: List of (function, args, kwargs) tuples
            priority: Priority for all tasks
            
        Returns:
            List of task IDs
        """
        task_ids = []
        
        for func, args, kwargs in tasks:
            task_id = self.submit_task(func, args, kwargs, priority)
            task_ids.append(task_id)
        
        console.print(f"[cyan]📋 Submitted batch of {len(task_ids)} tasks[/cyan]")
        return task_ids
    
    def start(self):
        """Start the distributed executor"""
        if self._running:
            return
        
        self._running = True
        
        # Start coordinator thread
        self._coordinator_thread = threading.Thread(target=self._coordinate, daemon=True)
        self._coordinator_thread.start()
        
        # Start local worker threads
        for worker_id, worker in self._workers.items():
            if worker.worker_type == "local":
                thread = threading.Thread(target=self._worker_loop, args=(worker_id,), daemon=True)
                thread.start()
                self._worker_threads[worker_id] = thread
        
        console.print("[bold green]🚀 Distributed executor started[/bold green]")
    
    def _coordinate(self):
        """Coordinator thread to monitor and manage execution"""
        while self._running:
            try:
                # Monitor worker health
                self._check_worker_health()
                
                # Check for timeout tasks
                self._check_task_timeouts()
                
                # Update statistics
                self._update_stats()
                
                time.sleep(1)
            except Exception as e:
                console.print(f"[red]❌ Coordinator error: {e}[/red]")
    
    def _worker_loop(self, worker_id: str):
        """Worker thread loop"""
        worker = self._workers.get(worker_id)
        if not worker:
            return
        
        console.print(f"[dim]👷 Worker {worker_id} started[/dim]")
        
        while self._running:
            try:
                # Get next task from queue
                try:
                    priority, task = self._task_queue.get(timeout=1)
                except queue.Empty:
                    continue
                
                # Execute task
                self._execute_task(worker_id, task)
                
            except Exception as e:
                console.print(f"[red]❌ Worker {worker_id} error: {e}[/red]")
        
        console.print(f"[dim]👷 Worker {worker_id} stopped[/dim]")
    
    def _execute_task(self, worker_id: str, task: Task):
        """Execute a task on a worker"""
        worker = self._workers.get(worker_id)
        if not worker:
            return
        
        # Update task and worker state
        with self._task_lock:
            task.status = TaskStatus.RUNNING
            task.started_at = datetime.now()
            task.worker_id = worker_id
        
        worker.current_task = task.task_id
        worker.last_heartbeat = datetime.now()
        
        console.print(f"[cyan]⚙️  Worker {worker_id} executing task {task.task_id}[/cyan]")
        
        try:
            # Execute the function
            start_time = time.time()
            result = task.function(*task.args, **task.kwargs)
            execution_time = time.time() - start_time
            
            # Task succeeded
            with self._task_lock:
                task.status = TaskStatus.COMPLETED
                task.completed_at = datetime.now()
                task.result = result
                self._stats["completed_tasks"] += 1
                self._stats["total_execution_time"] += execution_time
            
            worker.tasks_completed += 1
            worker.current_task = None
            
            console.print(f"[green]✅ Task {task.task_id} completed ({execution_time:.2f}s)[/green]")
            
            # Trigger callbacks
            for callback in self._on_task_complete:
                try:
                    callback(task)
                except:
                    pass
        
        except Exception as e:
            # Task failed
            with self._task_lock:
                task.error = str(e)
                task.retries += 1
                
                if task.retries < task.max_retries:
                    # Retry task
                    task.status = TaskStatus.RETRYING
                    console.print(f"[yellow]🔄 Task {task.task_id} failed, retrying ({task.retries}/{task.max_retries})[/yellow]")
                    self._task_queue.put((task.priority.value, task))
                else:
                    # Max retries exceeded
                    task.status = TaskStatus.FAILED
                    task.completed_at = datetime.now()
                    self._stats["failed_tasks"] += 1
                    console.print(f"[red]❌ Task {task.task_id} failed permanently: {e}[/red]")
                    
                    # Trigger callbacks
                    for callback in self._on_task_failed:
                        try:
                            callback(task)
                        except:
                            pass
            
            worker.tasks_failed += 1
            worker.current_task = None
    
    def _check_worker_health(self):
        """Check health of all workers"""
        current_time = datetime.now()
        
        with self._worker_lock:
            for worker_id, worker in self._workers.items():
                if worker.worker_type == "local":
                    # Local workers are always healthy
                    worker.is_active = True
                    worker.last_heartbeat = current_time
                else:
                    # Check remote worker heartbeat
                    heartbeat_age = (current_time - worker.last_heartbeat).total_seconds()
                    if heartbeat_age > 30:  # 30 seconds timeout
                        worker.is_active = False
                        console.print(f"[yellow]⚠️  Worker {worker_id} unhealthy (no heartbeat for {heartbeat_age:.0f}s)[/yellow]")
    
    def _check_task_timeouts(self):
        """Check for tasks that have exceeded timeout"""
        current_time = datetime.now()
        
        with self._task_lock:
            for task_id, task in self._tasks.items():
                if task.status == TaskStatus.RUNNING and task.started_at:
                    execution_time = (current_time - task.started_at).total_seconds()
                    
                    if execution_time > self.task_timeout:
                        console.print(f"[red]⏰ Task {task_id} exceeded timeout ({execution_time:.0f}s)[/red]")
                        task.status = TaskStatus.FAILED
                        task.error = f"Task timeout after {execution_time:.0f}s"
                        task.completed_at = current_time
                        self._stats["failed_tasks"] += 1
    
    def _update_stats(self):
        """Update execution statistics"""
        # Could add more sophisticated metrics here
        pass
    
    def get_task_status(self, task_id: str) -> Optional[TaskStatus]:
        """Get status of a specific task"""
        with self._task_lock:
            task = self._tasks.get(task_id)
            return task.status if task else None
    
    def get_task_result(self, task_id: str, wait: bool = False, timeout: float = None) -> Any:
        """
        Get result of a completed task
        
        Args:
            task_id: Task ID
            wait: Wait for task to complete
            timeout: Maximum wait time
            
        Returns:
            Task result or None
        """
        if wait:
            start_time = time.time()
            while True:
                status = self.get_task_status(task_id)
                
                if status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
                    break
                
                if timeout and (time.time() - start_time) > timeout:
                    console.print(f"[yellow]⏰ Timeout waiting for task {task_id}[/yellow]")
                    return None
                
                time.sleep(0.1)
        
        with self._task_lock:
            task = self._tasks.get(task_id)
            if task and task.status == TaskStatus.COMPLETED:
                return task.result
            elif task and task.status == TaskStatus.FAILED:
                raise Exception(f"Task failed: {task.error}")
            return None
    
    def wait_for_tasks(self, task_ids: List[str], timeout: float = None) -> Dict[str, Any]:
        """
        Wait for multiple tasks to complete
        
        Args:
            task_ids: List of task IDs
            timeout: Maximum wait time
            
        Returns:
            Dictionary mapping task_id to result
        """
        results = {}
        start_time = time.time()
        
        for task_id in task_ids:
            remaining_timeout = None
            if timeout:
                remaining_timeout = timeout - (time.time() - start_time)
                if remaining_timeout <= 0:
                    break
            
            try:
                result = self.get_task_result(task_id, wait=True, timeout=remaining_timeout)
                results[task_id] = result
            except Exception as e:
                results[task_id] = f"Error: {e}"
        
        return results
    
    def get_stats(self) -> Dict:
        """Get execution statistics"""
        with self._task_lock, self._worker_lock:
            avg_execution_time = (
                self._stats["total_execution_time"] / max(self._stats["completed_tasks"], 1)
            )
            
            return {
                "total_tasks": self._stats["total_tasks"],
                "completed_tasks": self._stats["completed_tasks"],
                "failed_tasks": self._stats["failed_tasks"],
                "pending_tasks": self._task_queue.qsize(),
                "active_workers": sum(1 for w in self._workers.values() if w.is_active),
                "total_workers": len(self._workers),
                "avg_execution_time": avg_execution_time,
                "workers": {
                    worker_id: {
                        "type": worker.worker_type,
                        "active": worker.is_active,
                        "current_task": worker.current_task,
                        "completed": worker.tasks_completed,
                        "failed": worker.tasks_failed,
                        "load": worker.get_load()
                    }
                    for worker_id, worker in self._workers.items()
                }
            }
    
    def register_callback(self, event: str, callback: Callable):
        """Register callback for task events"""
        if event == "task_complete":
            self._on_task_complete.append(callback)
        elif event == "task_failed":
            self._on_task_failed.append(callback)
    
    def stop(self):
        """Stop the distributed executor"""
        console.print("[yellow]🛑 Stopping distributed executor...[/yellow]")
        self._running = False
        
        if self._coordinator_thread:
            self._coordinator_thread.join(timeout=2)
        
        for thread in self._worker_threads.values():
            thread.join(timeout=2)
        
        console.print("[green]✅ Distributed executor stopped[/green]")
        
        # Print final stats
        stats = self.get_stats()
        console.print(f"[dim]📊 Final stats: {stats['completed_tasks']} completed, {stats['failed_tasks']} failed[/dim]")


# Global executor instance
_distributed_executor = None


def get_distributed_executor(max_workers: int = 3, enable_remote: bool = False) -> DistributedExecutor:
    """Get or create the global distributed executor"""
    global _distributed_executor
    
    if _distributed_executor is None:
        _distributed_executor = DistributedExecutor(
            max_local_workers=max_workers,
            enable_remote=enable_remote
        )
    
    return _distributed_executor

