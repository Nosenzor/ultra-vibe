"""
Background Task Execution for Ultrawork Mode.

Provides async task execution with priority queues and result collection.
"""

from ultra_vibe.core.background.task_queue import (
    BackgroundTaskQueue,
    BackgroundTask,
    TaskPriority,
    TaskResult,
    get_background_queue,
    enqueue_task,
    wait_for_task,
)

__all__ = [
    "BackgroundTaskQueue",
    "BackgroundTask",
    "TaskPriority",
    "TaskResult",
    "get_background_queue",
    "enqueue_task",
    "wait_for_task",
]
