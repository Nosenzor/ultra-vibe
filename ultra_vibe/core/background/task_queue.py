"""
Background Task Queue for Ultrawork Mode.

Provides async task execution with priority queues and result collection.
"""

from __future__ import annotations

import asyncio
import heapq
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar('T')


class TaskPriority(Enum):
    """Priority levels for background tasks."""
    HIGH = 0
    MEDIUM = 1
    LOW = 2


@dataclass
class BackgroundTask:
    """A task to be executed in the background."""
    task_id: str
    name: str
    func: Callable[[], T]
    priority: TaskPriority = TaskPriority.MEDIUM
    max_retries: int = 3
    retry_delay: float = 1.0
    timeout: Optional[float] = None
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    # For heapq ordering (lower number = higher priority)
    def __lt__(self, other: BackgroundTask) -> bool:
        return self.priority.value < other.priority.value


@dataclass
class TaskResult:
    """Result of a background task."""
    task_id: str
    success: bool
    result: Optional[T] = None
    error: Optional[str] = None
    duration: float = 0.0
    retries: int = 0
    completed_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'success': self.success,
            'result': self.result,
            'error': self.error,
            'duration': self.duration,
            'retries': self.retries,
            'completed_at': self.completed_at,
        }


class BackgroundTaskQueue:
    """
    Priority queue for background task execution.
    
    Features:
    - Priority-based execution (HIGH > MEDIUM > LOW)
    - Concurrent execution with configurable limits
    - Retry with exponential backoff
    - Timeout support
    - Result collection and error handling
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        queue_size: int = 100,
    ):
        self.max_concurrent = max_concurrent
        self.queue_size = queue_size
        
        self._queue: List[BackgroundTask] = []
        self._running: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, TaskResult] = {}
        self._waiters: Dict[str, asyncio.Event] = {}
        
        self._lock = asyncio.Lock()
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._running_event = asyncio.Event()
        self._shutdown = False
        
    def _priority_key(self, task: BackgroundTask) -> Tuple[int, float]:
        """Get priority key for ordering (lower = higher priority)."""
        return (task.priority.value, task.created_at)
    
    async def enqueue(
        self,
        task_id: str,
        name: str,
        func: Callable[[], T],
        priority: TaskPriority = TaskPriority.MEDIUM,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        timeout: Optional[float] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Enqueue a new background task.
        
        Args:
            task_id: Unique task ID
            name: Human-readable task name
            func: Callable to execute (must be async or return coroutine)
            priority: Task priority
            max_retries: Maximum retry attempts
            retry_delay: Initial delay between retries (doubles each retry)
            timeout: Optional timeout in seconds
            metadata: Additional metadata
            
        Returns:
            True if task was enqueued, False if queue is full
        """
        async with self._lock:
            if len(self._queue) >= self.queue_size:
                logger.warning(f"Task queue full, rejecting task {task_id}")
                return False
            
            if task_id in self._running or task_id in self._results:
                logger.warning(f"Task {task_id} already exists")
                return False
            
            task = BackgroundTask(
                task_id=task_id,
                name=name,
                func=func,
                priority=priority,
                max_retries=max_retries,
                retry_delay=retry_delay,
                timeout=timeout,
                metadata=metadata or {},
            )
            
            heapq.heappush(self._queue, task)
            logger.debug(f"Enqueued task {task_id} with priority {priority.name}")
        
        # Signal that there's work to do
        self._running_event.set()
        
        return True
    
    async def _execute_task(self, task: BackgroundTask) -> TaskResult:
        """Execute a single task with retry logic."""
        start_time = time.time()
        last_error: Optional[Exception] = None
        
        for attempt in range(task.max_retries + 1):
            try:
                # Check timeout
                elapsed = time.time() - start_time
                if task.timeout and elapsed >= task.timeout:
                    return TaskResult(
                        task_id=task.task_id,
                        success=False,
                        error=f"Timeout after {task.timeout}s",
                        duration=elapsed,
                        retries=attempt,
                    )
                
                # Execute the function
                if asyncio.iscoroutinefunction(task.func):
                    result = await asyncio.wait_for(
                        task.func(),
                        timeout=(task.timeout - elapsed) if task.timeout else None,
                    )
                else:
                    result = await asyncio.to_thread(
                        task.func,
                        timeout=(task.timeout - elapsed) if task.timeout else None,
                    )
                
                duration = time.time() - start_time
                return TaskResult(
                    task_id=task.task_id,
                    success=True,
                    result=result,
                    duration=duration,
                    retries=attempt,
                )
                
            except asyncio.TimeoutError:
                return TaskResult(
                    task_id=task.task_id,
                    success=False,
                    error=f"Timeout after {task.timeout}s",
                    duration=time.time() - start_time,
                    retries=attempt,
                )
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Task {task.task_id} failed (attempt {attempt + 1}/{task.max_retries + 1}): {e}"
                )
                
                # Wait before retry with exponential backoff
                if attempt < task.max_retries:
                    delay = task.retry_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
        
        # All retries exhausted
        duration = time.time() - start_time
        return TaskResult(
            task_id=task.task_id,
            success=False,
            error=str(last_error) if last_error else "Unknown error",
            duration=duration,
            retries=task.max_retries,
        )
    
    async def _worker(self) -> None:
        """Worker that processes tasks from the queue."""
        while not self._shutdown:
            # Wait for tasks
            try:
                await asyncio.wait_for(
                    self._running_event.wait(),
                    timeout=1.0,
                )
            except asyncio.TimeoutError:
                continue
            
            # Check if there are tasks
            async with self._lock:
                if not self._queue:
                    self._running_event.clear()
                    continue
                
                task = heapq.heappop(self._queue)
            
            # Acquire semaphore (wait if at max concurrency)
            await self._semaphore.acquire()
            
            async with self._lock:
                self._running[task.task_id] = asyncio.current_task()
            
            try:
                # Execute the task
                result = await self._execute_task(task)
                
                # Store result
                async with self._lock:
                    self._results[task.task_id] = result
                    
                    # Signal any waiters
                    if task.task_id in self._waiters:
                        self._waiters[task.task_id].set()
                        del self._waiters[task.task_id]
                
                logger.debug(
                    f"Completed task {task.task_id} "
                    f"({'success' if result.success else 'failed'}) "
                    f"in {result.duration:.2f}s"
                )
                
            finally:
                async with self._lock:
                    if task.task_id in self._running:
                        del self._running[task.task_id]
                self._semaphore.release()
    
    async def start(self) -> None:
        """Start the background worker."""
        self._worker_task = asyncio.create_task(self._worker())
        logger.info("Background task queue started")
    
    async def stop(self) -> None:
        """Stop the background worker."""
        self._shutdown = True
        if hasattr(self, '_worker_task'):
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass
        logger.info("Background task queue stopped")
    
    async def wait_for_task(self, task_id: str) -> Optional[TaskResult]:
        """
        Wait for a specific task to complete.
        
        Args:
            task_id: Task ID to wait for
            
        Returns:
            Task result or None if task doesn't exist
        """
        async with self._lock:
            if task_id in self._results:
                return self._results[task_id]
            
            if task_id not in self._running and task_id not in [t.task_id for t in self._queue]:
                return None
        
        # Create waiter event
        event = asyncio.Event()
        async with self._lock:
            self._waiters[task_id] = event
        
        try:
            await event.wait()
            return self._results.get(task_id)
        finally:
            async with self._lock:
                self._waiters.pop(task_id, None)
    
    async def wait_all(self) -> Dict[str, TaskResult]:
        """Wait for all enqueued tasks to complete."""
        async with self._lock:
            all_task_ids = {
                t.task_id for t in self._queue
            } | set(self._running.keys())
        
        if not all_task_ids:
            return dict(self._results)
        
        # Wait for each task
        results = {}
        for task_id in all_task_ids:
            result = await self.wait_for_task(task_id)
            if result:
                results[task_id] = result
        
        return results
    
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get result for a task (non-blocking)."""
        return self._results.get(task_id)
    
    def get_all_results(self) -> Dict[str, TaskResult]:
        """Get all results."""
        return dict(self._results)
    
    def get_queue_size(self) -> int:
        """Get number of queued tasks."""
        return len(self._queue)
    
    def get_running_count(self) -> int:
        """Get number of currently running tasks."""
        return len(self._running)
    
    def is_running(self, task_id: str) -> bool:
        """Check if a task is currently running."""
        return task_id in self._running
    
    def is_queued(self, task_id: str) -> bool:
        """Check if a task is queued."""
        return any(t.task_id == task_id for t in self._queue)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running or queued task."""
        async with self._lock:
            # Check if running
            if task_id in self._running:
                task = self._running[task_id]
                task.cancel()
                del self._running[task_id]
                return True
            
            # Check if queued
            for i, t in enumerate(self._queue):
                if t.task_id == task_id:
                    # Remove from heap
                    # Note: This is O(n) but queue should be small
                    self._queue.pop(i)
                    heapq.heapify(self._queue)
                    return True
        
        return False
    
    async def cancel_all(self) -> int:
        """Cancel all tasks."""
        count = 0
        
        async with self._lock:
            # Cancel running tasks
            for task in self._running.values():
                task.cancel()
                count += 1
            self._running.clear()
            
            # Clear queue
            count += len(self._queue)
            self._queue.clear()
        
        return count
    
    def clear(self) -> None:
        """Clear all tasks and results."""
        self._queue.clear()
        self._running.clear()
        self._results.clear()
        self._waiters.clear()


# Global background task queue
_background_queue = BackgroundTaskQueue()


def get_background_queue() -> BackgroundTaskQueue:
    """Get the global background task queue."""
    return _background_queue


async def enqueue_task(
    task_id: str,
    name: str,
    func: Callable[[], T],
    priority: TaskPriority = TaskPriority.MEDIUM,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout: Optional[float] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> bool:
    """Enqueue a background task (convenience function)."""
    return await _background_queue.enqueue(
        task_id=task_id,
        name=name,
        func=func,
        priority=priority,
        max_retries=max_retries,
        retry_delay=retry_delay,
        timeout=timeout,
        metadata=metadata,
    )


async def wait_for_task(task_id: str) -> Optional[TaskResult]:
    """Wait for a task (convenience function)."""
    return await _background_queue.wait_for_task(task_id)
