"""
Task Delegation System for Ultrawork Mode.

Provides functionality for spawning sub-agents and managing
task execution across multiple agents.

Main Components:
- task_manager: Task lifecycle management
- subagent: Sub-agent spawning and execution
"""

from ultra_vibe.core.delegation.task_manager import (
    TaskManager,
    DelegatedTask,
    TaskResult,
    TaskStatus,
    AgentType,
    get_task_manager,
    create_task,
    delegate_task,
)
from ultra_vibe.core.delegation.subagent import (
    SubAgentPool,
    SubAgentConfig,
    SubAgentResult,
    get_subagent_pool,
    spawn_subagent,
    wait_for_subagent,
    DelegationTool,
)

__all__ = [
    # Task Manager
    "TaskManager",
    "DelegatedTask",
    "TaskResult",
    "TaskStatus",
    "AgentType",
    "get_task_manager",
    "create_task",
    "delegate_task",
    # Sub-Agent
    "SubAgentPool",
    "SubAgentConfig",
    "SubAgentResult",
    "get_subagent_pool",
    "spawn_subagent",
    "wait_for_subagent",
    "DelegationTool",
]
