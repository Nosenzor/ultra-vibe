"""
Task Manager for Ultrawork Mode.

Manages task lifecycle, sub-agent spawning, and result aggregation.
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Status of a task."""
    CREATED = "created"
    PLANNING = "planning"
    DELEGATED = "delegated"
    IN_PROGRESS = "in_progress"
    VERIFICATION_PENDING = "verification_pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AgentType(Enum):
    """Types of specialist agents."""
    SISYPHUS = "sisyphus"      # Orchestrator
    HEPHAESTUS = "hephaestus"  # Implementer
    ORACLE = "oracle"          # Reviewer
    LIBRARIAN = "librarian"    # Researcher
    EXPLORE = "explore"        # Explorer
    PLAN = "plan"              # Planner


@dataclass
class TaskResult:
    """Result from a delegated task."""
    task_id: str
    agent_name: str
    agent_type: AgentType
    content: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    success: bool = True
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'agent_name': self.agent_name,
            'agent_type': self.agent_type.value,
            'content': self.content,
            'metadata': self.metadata,
            'timestamp': self.timestamp.isoformat(),
            'success': self.success,
            'error': self.error,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'TaskResult':
        """Create from dictionary."""
        return cls(
            task_id=data['task_id'],
            agent_name=data['agent_name'],
            agent_type=AgentType(data['agent_type']),
            content=data['content'],
            metadata=data.get('metadata', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            success=data.get('success', True),
            error=data.get('error'),
        )


@dataclass
class DelegatedTask:
    """A task that has been delegated to a sub-agent."""
    task_id: str
    parent_task_id: Optional[str]
    description: str
    agent_name: str
    agent_type: AgentType
    priority: str = "medium"  # high, medium, low
    status: TaskStatus = TaskStatus.CREATED
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    results: List[TaskResult] = field(default_factory=list)
    subtasks: List[str] = field(default_factory=list)  # task_ids of subtasks
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'task_id': self.task_id,
            'parent_task_id': self.parent_task_id,
            'description': self.description,
            'agent_name': self.agent_name,
            'agent_type': self.agent_type.value,
            'priority': self.priority,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'results': [r.to_dict() for r in self.results],
            'subtasks': self.subtasks,
            'metadata': self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DelegatedTask':
        """Create from dictionary."""
        return cls(
            task_id=data['task_id'],
            parent_task_id=data.get('parent_task_id'),
            description=data['description'],
            agent_name=data['agent_name'],
            agent_type=AgentType(data['agent_type']),
            priority=data.get('priority', 'medium'),
            status=TaskStatus(data.get('status', 'created')),
            created_at=datetime.fromisoformat(data['created_at']),
            updated_at=datetime.fromisoformat(data['updated_at']),
            results=[TaskResult.from_dict(r) for r in data.get('results', [])],
            subtasks=data.get('subtasks', []),
            metadata=data.get('metadata', {}),
        )


class TaskManager:
    """
    Manages tasks and sub-agent delegation for Ultrawork Mode.
    
    This is the core of the Ultrawork Mode implementation, handling:
    - Task creation and tracking
    - Sub-agent spawning
    - Result aggregation
    - Task continuity
    """
    
    def __init__(self):
        self.tasks: Dict[str, DelegatedTask] = {}
        self.active_task_id: Optional[str] = None
        self.task_counter: int = 0
        self._lock = asyncio.Lock()
        
    def generate_task_id(self) -> str:
        """Generate a unique task ID."""
        self.task_counter += 1
        return f"ulw-{self.task_counter:04d}-{uuid.uuid4().hex[:8]}"
    
    def create_task(
        self,
        description: str,
        agent_type: AgentType = AgentType.SISYPHUS,
        parent_task_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Create a new task.
        
        Args:
            description: Task description
            agent_type: Type of agent to use
            parent_task_id: Parent task ID if this is a subtask
            metadata: Additional metadata
            
        Returns:
            New task ID
        """
        task_id = self.generate_task_id()
        
        # Map agent type to agent name
        agent_name = agent_type.value
        
        task = DelegatedTask(
            task_id=task_id,
            parent_task_id=parent_task_id,
            description=description,
            agent_name=agent_name,
            agent_type=agent_type,
            status=TaskStatus.CREATED,
            metadata=metadata or {},
        )
        
        self.tasks[task_id] = task
        self.active_task_id = task_id
        
        logger.info(f"Created task {task_id}: {description[:50]}...")
        return task_id
    
    def get_task(self, task_id: str) -> Optional[DelegatedTask]:
        """Get a task by ID."""
        return self.tasks.get(task_id)
    
    def get_active_task(self) -> Optional[DelegatedTask]:
        """Get the currently active task."""
        if self.active_task_id:
            return self.tasks.get(self.active_task_id)
        return None
    
    def set_active_task(self, task_id: str) -> bool:
        """Set the active task."""
        if task_id in self.tasks:
            self.active_task_id = task_id
            return True
        return False
    
    def update_task_status(
        self,
        task_id: str,
        status: TaskStatus,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update task status."""
        task = self.tasks.get(task_id)
        if task:
            task.status = status
            task.updated_at = datetime.now()
            if metadata:
                task.metadata.update(metadata)
            logger.debug(f"Updated task {task_id} status to {status.value}")
            return True
        return False
    
    def add_result(
        self,
        task_id: str,
        agent_name: str,
        agent_type: AgentType,
        content: str,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Add a result to a task."""
        task = self.tasks.get(task_id)
        if task:
            result = TaskResult(
                task_id=task_id,
                agent_name=agent_name,
                agent_type=agent_type,
                content=content,
                success=success,
                error=error,
                metadata=metadata or {},
            )
            task.results.append(result)
            task.updated_at = datetime.now()
            logger.debug(f"Added result to task {task_id} from {agent_name}")
            return True
        return False
    
    def add_subtask(self, parent_task_id: str, subtask_id: str) -> bool:
        """Add a subtask to a parent task."""
        task = self.tasks.get(parent_task_id)
        if task and subtask_id in self.tasks:
            task.subtasks.append(subtask_id)
            task.updated_at = datetime.now()
            return True
        return False
    
    def delegate_task(
        self,
        task_id: str,
        agent_type: AgentType,
        description: str,
        priority: str = "medium",
    ) -> str:
        """
        Delegate a subtask from an existing task.
        
        Args:
            task_id: Parent task ID
            agent_type: Type of agent to delegate to
            description: Subtask description
            priority: Priority level
            
        Returns:
            New subtask ID
        """
        parent_task = self.tasks.get(task_id)
        if not parent_task:
            raise ValueError(f"Parent task {task_id} not found")
        
        subtask_id = self.create_task(
            description=description,
            agent_type=agent_type,
            parent_task_id=task_id,
            metadata={'delegated_by': parent_task.agent_name, 'priority': priority},
        )
        
        # Add subtask to parent
        parent_task.subtasks.append(subtask_id)
        parent_task.updated_at = datetime.now()
        
        logger.info(f"Delegated subtask {subtask_id} from task {task_id} to {agent_type.value}")
        return subtask_id
    
    async def execute_task(
        self,
        task_id: str,
        execute_fn: Callable[[str, AgentType, str], Any],
    ) -> Optional[Any]:
        """
        Execute a task by running its agent.
        
        Args:
            task_id: Task ID to execute
            execute_fn: Function to call with (task_id, agent_type, description)
            
        Returns:
            Result from execution
        """
        task = self.tasks.get(task_id)
        if not task:
            return None
        
        async with self._lock:
            task.status = TaskStatus.IN_PROGRESS
            task.updated_at = datetime.now()
        
        try:
            result = await execute_fn(
                task.task_id,
                task.agent_type,
                task.description,
            )
            task.status = TaskStatus.COMPLETED
            return result
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.metadata['error'] = str(e)
            logger.error(f"Task {task_id} failed: {e}")
            return None
    
    def get_task_context(self, task_id: str) -> str:
        """
        Get formatted context for a task.
        
        Returns a summary of the task state that can be included
        in prompts to agents.
        """
        task = self.tasks.get(task_id)
        if not task:
            return f"Task {task_id} not found"
        
        lines = [
            f"Task ID: {task.task_id}",
            f"Description: {task.description}",
            f"Agent: {task.agent_name} ({task.agent_type.value})",
            f"Status: {task.status.value}",
            f"Created: {task.created_at}",
        ]
        
        if task.subtasks:
            lines.append(f"Subtasks: {len(task.subtasks)}")
            for subtask_id in task.subtasks:
                subtask = self.tasks.get(subtask_id)
                if subtask:
                    lines.append(f"  - {subtask_id}: {subtask.description} ({subtask.status.value})")
        
        if task.results:
            lines.append(f"\nResults ({len(task.results)}):")
            for result in task.results:
                lines.append(f"  - [{result.agent_name}] {result.content[:100]}...")
        
        return "\n".join(lines)
    
    def get_all_tasks(self) -> List[DelegatedTask]:
        """Get all tasks."""
        return list(self.tasks.values())
    
    def get_tasks_by_status(self, status: TaskStatus) -> List[DelegatedTask]:
        """Get tasks by status."""
        return [t for t in self.tasks.values() if t.status == status]
    
    def cleanup_completed(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed tasks.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            Number of tasks cleaned up
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        to_remove = [
            tid for tid, task in self.tasks.items()
            if task.status in (TaskStatus.COMPLETED, TaskStatus.FAILED)
            and task.updated_at < cutoff
        ]
        
        for tid in to_remove:
            del self.tasks[tid]
        
        logger.debug(f"Cleaned up {len(to_remove)} old tasks")
        return len(to_remove)
    
    def clear(self) -> None:
        """Clear all tasks."""
        self.tasks.clear()
        self.active_task_id = None
        self.task_counter = 0


# Global task manager instance
_task_manager = TaskManager()


def get_task_manager() -> TaskManager:
    """Get the global task manager instance."""
    return _task_manager


def create_task(
    description: str,
    agent_type: AgentType = AgentType.SISYPHUS,
    parent_task_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Create a new task (convenience function)."""
    return _task_manager.create_task(
        description=description,
        agent_type=agent_type,
        parent_task_id=parent_task_id,
        metadata=metadata,
    )


def delegate_task(
    task_id: str,
    agent_type: AgentType,
    description: str,
    priority: str = "medium",
) -> str:
    """Delegate a subtask (convenience function)."""
    return _task_manager.delegate_task(
        task_id=task_id,
        agent_type=agent_type,
        description=description,
        priority=priority,
    )
