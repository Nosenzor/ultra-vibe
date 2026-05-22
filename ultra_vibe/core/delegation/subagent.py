"""
Sub-Agent Execution for Ultrawork Mode.

Handles spawning and managing sub-agents for parallel task execution.
"""

from __future__ import annotations

import asyncio
import logging
import subprocess
import tempfile
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable, AsyncGenerator

logger = logging.getLogger(__name__)


@dataclass
class SubAgentConfig:
    """Configuration for spawning a sub-agent."""
    agent_name: str
    task_id: str
    task_description: str
    model: Optional[str] = None
    variant: Optional[str] = None
    workdir: Optional[Path] = None
    timeout: float = 300.0  # 5 minutes default
    tools: List[str] = field(default_factory=list)
    env: Dict[str, str] = field(default_factory=dict)
    
    def to_vibe_args(self) -> List[str]:
        """Convert to Vibe CLI arguments."""
        args = ["vibe", "--agent", self.agent_name]
        
        if self.model:
            # Model would need to be configured in Vibe's config
            pass
        
        if self.variant:
            # Variant would need to be configured
            pass
        
        if self.workdir:
            args.extend(["--workdir", str(self.workdir)])
        
        # Add task context as prompt
        prompt = f"Task ID: {self.task_id}\n\n{self.task_description}"
        args.append(prompt)
        
        return args


@dataclass
class SubAgentResult:
    """Result from a sub-agent execution."""
    task_id: str
    agent_name: str
    content: str
    success: bool = True
    error: Optional[str] = None
    stdout: str = ""
    stderr: str = ""
    exit_code: int = 0
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class SubAgentPool:
    """
    Pool for managing concurrent sub-agent execution.
    
    This class:
    - Spawns sub-agents as subprocesses
    - Manages concurrency limits
    - Collects results
    - Handles timeouts
    """
    
    def __init__(
        self,
        max_concurrent: int = 5,
        default_timeout: float = 300.0,
    ):
        self.max_concurrent = max_concurrent
        self.default_timeout = default_timeout
        self._running: Dict[str, asyncio.Task] = {}
        self._results: Dict[str, SubAgentResult] = {}
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._lock = asyncio.Lock()
        
    async def spawn(
        self,
        config: SubAgentConfig,
    ) -> str:
        """
        Spawn a sub-agent.
        
        Args:
            config: Sub-agent configuration
            
        Returns:
            Task ID
        """
        async with self._lock:
            if config.task_id in self._running:
                raise ValueError(f"Task {config.task_id} already running")
        
        # Acquire semaphore (wait if at max concurrency)
        await self._semaphore.acquire()
        
        # Start the task
        task = asyncio.create_task(
            self._run_subagent(config)
        )
        
        async with self._lock:
            self._running[config.task_id] = task
        
        logger.info(f"Spawned sub-agent {config.agent_name} for task {config.task_id}")
        return config.task_id
    
    async def _run_subagent(self, config: SubAgentConfig) -> SubAgentResult:
        """Run a sub-agent and collect results."""
        import time
        
        start_time = time.time()
        result = SubAgentResult(
            task_id=config.task_id,
            agent_name=config.agent_name,
            content="",
            success=True,
        )
        
        try:
            # Build the command
            # For now, we'll use vibe directly
            # In production, we might use Vibe's programmatic API
            
            # Create a temporary directory for the sub-agent
            with tempfile.TemporaryDirectory() as tmpdir:
                workdir = Path(tmpdir)
                
                # Write task context to a file
                context_file = workdir / "task_context.json"
                context_file.write_text(json.dumps({
                    'task_id': config.task_id,
                    'agent_name': config.agent_name,
                    'description': config.task_description,
                    'model': config.model,
                    'variant': config.variant,
                }))
                
                # Build command
                # Note: This assumes vibe is in PATH
                cmd = [
                    "vibe",
                    "--agent", config.agent_name,
                    "--workdir", str(workdir),
                    "--trust",  # Trust the temp directory
                    f"Task: {config.task_description}",
                ]
                
                logger.debug(f"Running: {' '.join(cmd)}")
                
                # Run the subprocess
                proc = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=str(workdir),
                    env={**dict(subprocess.os.environ), **config.env},
                )
                
                # Wait for completion with timeout
                try:
                    stdout, stderr = await asyncio.wait_for(
                        proc.communicate(),
                        timeout=config.timeout,
                    )
                except asyncio.TimeoutError:
                    proc.kill()
                    await proc.wait()
                    result.success = False
                    result.error = f"Timeout after {config.timeout}s"
                    result.exit_code = -1
                    return result
                
                result.exit_code = proc.returncode or 0
                result.stdout = stdout.decode('utf-8', errors='replace')
                result.stderr = stderr.decode('utf-8', errors='replace')
                result.content = result.stdout
                
                # Check for errors
                if result.exit_code != 0:
                    result.success = False
                    result.error = f"Subprocess failed with code {result.exit_code}"
                    if result.stderr:
                        result.error += f": {result.stderr[:500]}"
                
        except Exception as e:
            result.success = False
            result.error = str(e)
            logger.error(f"Sub-agent {config.task_id} error: {e}")
        
        finally:
            result.duration = time.time() - start_time
            self._semaphore.release()
        
        # Store result
        async with self._lock:
            self._results[config.task_id] = result
            if config.task_id in self._running:
                del self._running[config.task_id]
        
        logger.info(f"Completed sub-agent {config.agent_name} for task {config.task_id} in {result.duration:.1f}s")
        return result
    
    async def wait_for_task(self, task_id: str) -> Optional[SubAgentResult]:
        """Wait for a specific task to complete."""
        async with self._lock:
            if task_id not in self._running:
                return self._results.get(task_id)
        
        # Wait for the task to complete
        task = self._running[task_id]
        try:
            await task
        except Exception as e:
            logger.error(f"Task {task_id} failed: {e}")
            return None
        
        return self._results.get(task_id)
    
    async def wait_all(self) -> Dict[str, SubAgentResult]:
        """Wait for all running sub-agents to complete."""
        async with self._lock:
            tasks = list(self._running.values())
        
        if not tasks:
            return dict(self._results)
        
        # Wait for all tasks
        await asyncio.gather(*tasks, return_exceptions=True)
        
        async with self._lock:
            return dict(self._results)
    
    async def get_result(self, task_id: str) -> Optional[SubAgentResult]:
        """Get result for a task (non-blocking)."""
        async with self._lock:
            return self._results.get(task_id)
    
    def get_all_results(self) -> Dict[str, SubAgentResult]:
        """Get all results."""
        return dict(self._results)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a running task."""
        async with self._lock:
            if task_id not in self._running:
                return False
            
            task = self._running[task_id]
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
            
            del self._running[task_id]
            return True
    
    async def cancel_all(self) -> int:
        """Cancel all running tasks."""
        async with self._lock:
            tasks_to_cancel = list(self._running.values())
        
        cancelled = 0
        for task in tasks_to_cancel:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                cancelled += 1
        
        async with self._lock:
            self._running.clear()
        
        return cancelled
    
    def get_running_tasks(self) -> List[str]:
        """Get list of running task IDs."""
        return list(self._running.keys())
    
    def is_running(self, task_id: str) -> bool:
        """Check if a task is running."""
        return task_id in self._running
    
    def clear(self) -> None:
        """Clear all state."""
        self._running.clear()
        self._results.clear()


# Global sub-agent pool
_subagent_pool = SubAgentPool()


def get_subagent_pool() -> SubAgentPool:
    """Get the global sub-agent pool."""
    return _subagent_pool


async def spawn_subagent(
    agent_name: str,
    task_id: str,
    task_description: str,
    model: Optional[str] = None,
    variant: Optional[str] = None,
    timeout: float = 300.0,
) -> str:
    """
    Spawn a sub-agent (convenience function).
    
    Args:
        agent_name: Name of the agent to use
        task_id: Task ID
        task_description: Description of the task
        model: Model to use (optional)
        variant: Reasoning variant (optional)
        timeout: Timeout in seconds
        
    Returns:
        Task ID
    """
    config = SubAgentConfig(
        agent_name=agent_name,
        task_id=task_id,
        task_description=task_description,
        model=model,
        variant=variant,
        timeout=timeout,
    )
    
    return await _subagent_pool.spawn(config)


async def wait_for_subagent(task_id: str) -> Optional[SubAgentResult]:
    """Wait for a sub-agent result (convenience function)."""
    return await _subagent_pool.wait_for_task(task_id)


class DelegationTool:
    """
    Tool that agents can use to delegate tasks to sub-agents.
    
    This would be registered as a Vibe tool that agents can call.
    """
    
    def __init__(self):
        self.pool = _subagent_pool
        
    async def delegate_task(
        self,
        agent: str,
        task: str,
        task_id: Optional[str] = None,
        subagent_type: Optional[str] = None,
        priority: str = "medium",
        sync: bool = False,
    ) -> Dict[str, Any]:
        """
        Delegate a task to a sub-agent.
        
        Args:
            agent: Agent name to delegate to
            task: Task description
            task_id: Optional task ID (generated if not provided)
            subagent_type: Type of sub-agent (explore, oracle, etc.)
            priority: Priority level
            sync: If True, wait for completion (blocking)
            
        Returns:
            Result dictionary with task_id and status
        """
        from ultra_vibe.core.delegation.task_manager import get_task_manager, TaskStatus
        from ultra_vibe.core.ultrawork.agents import get_agent_definition
        
        # Generate task_id if not provided
        if not task_id:
            task_id = get_task_manager().generate_task_id()
        
        # Get agent definition to validate
        agent_def = get_agent_definition(agent)
        if not agent_def:
            return {
                'status': 'error',
                'error': f'Agent {agent} not found',
                'task_id': task_id,
            }
        
        # Get model/variant for this agent in ultrawork mode
        from ultra_vibe.core.hooks.model_override import resolve_ultrawork_override
        model, variant = resolve_ultrawork_override(
            current_model=agent_def.default_model or "",
            current_variant=agent_def.default_variant or "",
        )
        
        # Create task in task manager
        from ultra_vibe.core.delegation.task_manager import AgentType, get_task_manager
        
        # Map agent name to AgentType
        agent_type_map = {
            'sisyphus': AgentType.SISYPHUS,
            'hephaestus': AgentType.HEPHAESTUS,
            'oracle': AgentType.ORACLE,
            'librarian': AgentType.LIBRARIAN,
            'explore': AgentType.EXPLORE,
            'plan': AgentType.PLAN,
        }
        agent_type = agent_type_map.get(agent.lower(), AgentType.HEPHAESTUS)
        
        task_manager = get_task_manager()
        task_manager.create_task(
            description=task,
            agent_type=agent_type,
            metadata={
                'delegated_by': 'user',
                'priority': priority,
                'subagent_type': subagent_type,
            }
        )
        
        # Spawn sub-agent
        subagent_task_id = await self.pool.spawn(
            SubAgentConfig(
                agent_name=agent,
                task_id=task_id,
                task_description=task,
                model=model,
                variant=variant,
            )
        )
        
        # If sync, wait for completion
        if sync:
            result = await self.pool.wait_for_task(subagent_task_id)
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
                }
        
        # Async - return immediately
        return {
            'status': 'delegated',
            'task_id': task_id,
            'message': f'Task delegated to {agent}',
        }
