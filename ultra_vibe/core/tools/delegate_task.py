"""
Delegate Task Tool for Ultrawork Mode.

This tool allows agents to delegate work to sub-agents.
It would be registered with Vibe's tool system.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ultra_vibe.core.tools.base import BaseTool, InvokeContext

logger = logging.getLogger(__name__)


class DelegateTaskTool:
    """
    Vibe tool for delegating tasks to sub-agents.
    
    This tool:
    - Validates delegation requests
    - Spawns sub-agents for parallel execution
    - Returns task_id for tracking
    - Supports synchronous and asynchronous execution
    
    Usage in Vibe:
        delegate_task(agent="hephaestus", task="implement feature X", sync=False)
    """
    
    def __init__(self):
        self.name = "delegate_task"
        self.description = "Delegate a task to a sub-agent for parallel execution"
        self.enabled = True
        
    def get_schema(self) -> Dict[str, Any]:
        """Get the JSON schema for this tool."""
        return {
            "type": "object",
            "properties": {
                "agent": {
                    "type": "string",
                    "description": "Name of the agent to delegate to (sisyphus, hephaestus, oracle, librarian, explore, plan)",
                    "enum": ["sisyphus", "hephaestus", "oracle", "librarian", "explore", "plan"],
                },
                "task": {
                    "type": "string",
                    "description": "Description of the task to delegate",
                },
                "task_id": {
                    "type": "string",
                    "description": "Optional task ID for continuity (generated if not provided)",
                },
                "subagent_type": {
                    "type": "string",
                    "description": "Optional sub-agent type (explore, oracle, etc.)",
                    "enum": ["explore", "oracle", "implement", "review", "document", None],
                },
                "priority": {
                    "type": "string",
                    "description": "Priority level",
                    "enum": ["high", "medium", "low"],
                    "default": "medium",
                },
                "sync": {
                    "type": "boolean",
                    "description": "If True, wait for task completion (blocking)",
                    "default": False,
                },
                "timeout": {
                    "type": "number",
                    "description": "Timeout in seconds for the task",
                    "default": 300.0,
                },
            },
            "required": ["agent", "task"],
        }
    
    async def invoke(
        self,
        context: "InvokeContext",
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """
        Invoke the delegate_task tool.
        
        Args:
            context: Vibe invoke context
            **kwargs: Tool arguments
            
        Returns:
            Result dictionary with task_id and status
        """
        from ultra_vibe.core.delegation.task_manager import (
            get_task_manager,
            TaskStatus,
            AgentType,
        )
        from ultra_vibe.core.hooks.model_override import resolve_ultrawork_override
        from ultra_vibe.core.ultrawork.agents import get_agent_definition
        from ultra_vibe.core.delegation.subagent import spawn_subagent, wait_for_subagent
        
        # Extract arguments
        agent = kwargs.get('agent', '').lower()
        task = kwargs.get('task', '')
        task_id = kwargs.get('task_id')
        subagent_type = kwargs.get('subagent_type')
        priority = kwargs.get('priority', 'medium')
        sync = kwargs.get('sync', False)
        timeout = kwargs.get('timeout', 300.0)
        
        # Validate agent
        valid_agents = ['sisyphus', 'hephaestus', 'oracle', 'librarian', 'explore', 'plan']
        if agent not in valid_agents:
            return {
                'status': 'error',
                'error': f'Invalid agent: {agent}. Must be one of {valid_agents}',
            }
        
        # Get agent definition
        agent_def = get_agent_definition(agent)
        if not agent_def:
            return {
                'status': 'error',
                'error': f'Agent {agent} not found',
            }
        
        # Generate task_id if not provided
        task_manager = get_task_manager()
        if not task_id:
            task_id = task_manager.generate_task_id()
        
        # Map agent to AgentType
        agent_type_map = {
            'sisyphus': AgentType.SISYPHUS,
            'hephaestus': AgentType.HEPHAESTUS,
            'oracle': AgentType.ORACLE,
            'librarian': AgentType.LIBRARIAN,
            'explore': AgentType.EXPLORE,
            'plan': AgentType.PLAN,
        }
        agent_type = agent_type_map.get(agent, AgentType.HEPHAESTUS)
        
        # Get model/variant for this agent in ultrawork mode
        model, variant = resolve_ultrawork_override(
            current_model=agent_def.default_model or "",
            current_variant=agent_def.default_variant or "",
        )
        
        # Create task in task manager
        task_manager.create_task(
            description=task,
            agent_type=agent_type,
            metadata={
                'delegated_by': context.get('agent_name', 'unknown'),
                'priority': priority,
                'subagent_type': subagent_type,
                'sync': sync,
            }
        )
        
        # Spawn sub-agent
        try:
            await spawn_subagent(
                agent_name=agent,
                task_id=task_id,
                task_description=task,
                model=model,
                variant=variant,
                timeout=timeout,
            )
        except Exception as e:
            logger.error(f"Failed to spawn sub-agent: {e}")
            task_manager.update_task_status(
                task_id=task_id,
                status=TaskStatus.FAILED,
            )
            return {
                'status': 'error',
                'error': str(e),
                'task_id': task_id,
            }
        
        # If sync, wait for completion
        if sync:
            from ultra_vibe.core.delegation.subagent import wait_for_subagent
            result = await wait_for_subagent(task_id)
            
            if result:
                task_manager.update_task_status(
                    task_id=task_id,
                    status=TaskStatus.COMPLETED if result.success else TaskStatus.FAILED,
                )
                task_manager.add_result(
                    task_id=task_id,
                    agent_name=agent,
                    agent_type=agent_type,
                    content=result.content,
                    success=result.success,
                    error=result.error,
                )
                
                return {
                    'status': 'completed' if result.success else 'failed',
                    'task_id': task_id,
                    'content': result.content,
                    'error': result.error,
                    'duration': result.duration,
                }
        
        # Async - return immediately
        return {
            'status': 'delegated',
            'task_id': task_id,
            'message': f'Task delegated to {agent}',
            'agent': agent,
        }
    
    async def list_tasks(self, context: "InvokeContext") -> Dict[str, Any]:
        """List all active tasks."""
        from ultra_vibe.core.delegation.task_manager import get_task_manager
        
        task_manager = get_task_manager()
        tasks = task_manager.get_all_tasks()
        
        return {
            'tasks': [
                {
                    'task_id': t.task_id,
                    'description': t.description,
                    'agent': t.agent_name,
                    'status': t.status.value,
                    'created_at': t.created_at.isoformat(),
                    'subtasks': len(t.subtasks),
                    'results': len(t.results),
                }
                for t in tasks
            ],
            'count': len(tasks),
        }
    
    async def get_task_status(self, context: "InvokeContext", task_id: str) -> Dict[str, Any]:
        """Get status of a specific task."""
        from ultra_vibe.core.delegation.task_manager import get_task_manager
        
        task_manager = get_task_manager()
        task = task_manager.get_task(task_id)
        
        if not task:
            return {'status': 'error', 'error': f'Task {task_id} not found'}
        
        return {
            'task_id': task.task_id,
            'description': task.description,
            'agent': task.agent_name,
            'status': task.status.value,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat(),
            'subtasks': [
                {
                    'task_id': stid,
                    'status': task_manager.get_task(stid).status.value if task_manager.get_task(stid) else 'unknown',
                }
                for stid in task.subtasks
            ],
            'results': [
                {
                    'agent': r.agent_name,
                    'content': r.content[:200] + '...' if len(r.content) > 200 else r.content,
                    'success': r.success,
                    'timestamp': r.timestamp.isoformat(),
                }
                for r in task.results
            ],
        }
    
    async def wait_for_task(self, context: "InvokeContext", task_id: str) -> Dict[str, Any]:
        """Wait for a task to complete."""
        from ultra_vibe.core.delegation.subagent import wait_for_subagent
        
        result = await wait_for_subagent(task_id)
        
        if not result:
            return {'status': 'error', 'error': f'Task {task_id} not found'}
        
        return {
            'status': 'completed' if result.success else 'failed',
            'task_id': task_id,
            'content': result.content,
            'error': result.error,
            'duration': result.duration,
            'retries': result.retries,
        }


# Singleton instance
delegate_task_tool = DelegateTaskTool()
