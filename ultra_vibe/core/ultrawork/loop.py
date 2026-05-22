"""
ULW Loop for persistent iteration and verification.

Implements the Ralph/ULW Loop mechanism from oh-my-openagent,
allowing for iterative task refinement with verification enforcement.
"""

from __future__ import annotations

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


# Verification prompt for oracle tasks during ULW Loop
VERIFICATION_PROMPT: str = """
You are in **VERIFICATION MODE**. Be extremely skeptical and thorough:

1. **Review ALL changes line by line** - No exceptions
2. **Identify potential issues**:
   - Bugs (logical errors, edge cases)
   - Security vulnerabilities
   - Performance problems
   - Anti-patterns
   - Missing validations
3. **Check for edge cases**:
   - Null/undefined values
   - Empty inputs
   - Maximum/minimum values
   - Concurrent access
   - Error conditions
4. **Verify implementation matches specification exactly**
5. **Provide specific references**: file:line for every issue found

**CRITICAL**: If you find ANY issues (even minor ones), return them as a structured list.
Do NOT approve unless you are 100% certain the implementation is correct, complete, and production-ready.

Your response should be in this format:
```
VERIFICATION RESULT: [PASS/FAIL]

If FAIL:
ISSUES FOUND:
1. [Issue description] at [file:line]
2. [Issue description] at [file:line]
...

If PASS:
All verifications passed. Implementation is correct and complete.
```
"""


@dataclass
class LoopState:
    """State of an active ULW Loop."""
    
    loop_id: str
    task_id: str
    initial_task: str
    iterations: int = 0
    status: str = "running"  # running, paused, completed, failed
    created_at: datetime = field(default_factory=datetime.now)
    last_iteration_at: Optional[datetime] = None
    verification_pending: bool = False
    verification_results: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'loop_id': self.loop_id,
            'task_id': self.task_id,
            'initial_task': self.initial_task,
            'iterations': self.iterations,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_iteration_at': self.last_iteration_at.isoformat() if self.last_iteration_at else None,
            'verification_pending': self.verification_pending,
            'verification_results': self.verification_results,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LoopState':
        """Create from dictionary."""
        return cls(
            loop_id=data.get('loop_id', ''),
            task_id=data.get('task_id', ''),
            initial_task=data.get('initial_task', ''),
            iterations=data.get('iterations', 0),
            status=data.get('status', 'running'),
            created_at=datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now(),
            last_iteration_at=datetime.fromisoformat(data['last_iteration_at']) if data.get('last_iteration_at') else None,
            verification_pending=data.get('verification_pending', False),
            verification_results=data.get('verification_results', []),
        )


class ULWLoop:
    """
    Ultrawork Loop manager for iterative task refinement.
    
    Manages multiple concurrent loops, enforces verification,
    and maintains state across iterations.
    """
    
    def __init__(self):
        self.active_loops: Dict[str, LoopState] = {}
        self.verification_pending: Dict[str, bool] = {}  # task_id -> bool
        self.verification_promises: Dict[str, Any] = {}  # For async verification
    
    def generate_loop_id(self) -> str:
        """Generate a unique loop ID."""
        return f"ulw-loop-{uuid.uuid4().hex[:12]}"
    
    def generate_task_id(self) -> str:
        """Generate a unique task ID."""
        return f"task-{uuid.uuid4().hex[:12]}"
    
    def start_loop(self, task_id: str, initial_task: str) -> str:
        """
        Start a new ULW Loop.
        
        Args:
            task_id: The task ID this loop is for
            initial_task: Description of the initial task
            
        Returns:
            The new loop ID
        """
        loop_id = self.generate_loop_id()
        
        self.active_loops[loop_id] = LoopState(
            loop_id=loop_id,
            task_id=task_id,
            initial_task=initial_task,
            iterations=0,
            status='running',
        )
        
        logger.info(f"Started ULW Loop {loop_id} for task {task_id}")
        return loop_id
    
    def stop_loop(self, loop_id: str, status: str = "completed") -> bool:
        """
        Stop an active ULW Loop.
        
        Args:
            loop_id: The loop ID to stop
            status: Final status (completed, failed, etc.)
            
        Returns:
            True if loop was found and stopped
        """
        if loop_id not in self.active_loops:
            return False
        
        self.active_loops[loop_id].status = status
        logger.info(f"Stopped ULW Loop {loop_id} with status: {status}")
        return True
    
    def get_loop(self, loop_id: str) -> Optional[LoopState]:
        """Get a loop by ID."""
        return self.active_loops.get(loop_id)
    
    def get_loop_by_task(self, task_id: str) -> Optional[LoopState]:
        """Get a loop by associated task ID."""
        for loop in self.active_loops.values():
            if loop.task_id == task_id:
                return loop
        return None
    
    def verification_required(self, task_id: str) -> bool:
        """
        Check if verification is pending for a task.
        
        Args:
            task_id: Task ID to check
            
        Returns:
            True if verification is pending
        """
        return self.verification_pending.get(task_id, False)
    
    def set_verification_pending(self, task_id: str, pending: bool) -> None:
        """
        Set verification pending state for a task.
        
        Args:
            task_id: Task ID
            pending: Whether verification is pending
        """
        self.verification_pending[task_id] = pending
        logger.debug(f"Verification pending for task {task_id}: {pending}")
    
    def add_verification_result(
        self,
        task_id: str,
        result: Dict[str, Any],
    ) -> None:
        """
        Add a verification result for a task.
        
        Args:
            task_id: Task ID
            result: Verification result dictionary
        """
        loop = self.get_loop_by_task(task_id)
        if loop:
            loop.verification_results.append(result)
            logger.debug(f"Added verification result for task {task_id}")
    
    def increment_iteration(self, loop_id: str) -> int:
        """
        Increment the iteration count for a loop.
        
        Args:
            loop_id: Loop ID
            
        Returns:
            New iteration count
        """
        loop = self.active_loops.get(loop_id)
        if loop:
            loop.iterations += 1
            loop.last_iteration_at = datetime.now()
            logger.debug(f"Loop {loop_id} iteration {loop.iterations}")
            return loop.iterations
        return 0
    
    def enforce_verification(
        self,
        tool_call: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enforce verification for oracle tasks during ULW Loop.
        
        Intercepts delegate_task calls with subagent_type="oracle" and
        injects the verification prompt, forcing synchronous execution.
        
        Args:
            tool_call: The tool call dictionary to potentially modify
            
        Returns:
            Modified tool call with verification enforcement if applicable
        """
        if tool_call.get('tool') != 'delegate_task':
            return tool_call
        
        args = tool_call.get('arguments', {})
        task_type = args.get('subagent_type', '')
        task_id = args.get('task_id', '')
        
        # Check if this is an oracle task with verification pending
        if task_type.lower() == 'oracle' and self.verification_required(task_id):
            logger.debug(f"Enforcing verification for oracle task {task_id}")
            
            # Inject verification prompt
            args['system_prompt_addendum'] = VERIFICATION_PROMPT
            
            # Force synchronous execution to block until verification complete
            args['sync'] = True
            
            # Mark that verification is in progress
            self.set_verification_pending(task_id, True)
            
            tool_call['arguments'] = args
        
        return tool_call
    
    def is_in_loop(self, task_id: str) -> bool:
        """Check if a task is in an active ULW Loop."""
        return self.get_loop_by_task(task_id) is not None
    
    def get_active_loops(self) -> List[LoopState]:
        """Get all active loops."""
        return list(self.active_loops.values())
    
    def cleanup(self, max_age_hours: int = 24) -> int:
        """
        Clean up old completed loops.
        
        Args:
            max_age_hours: Maximum age in hours for kept loops
            
        Returns:
            Number of loops cleaned up
        """
        from datetime import timedelta
        
        cutoff = datetime.now() - timedelta(hours=max_age_hours)
        cleaned = 0
        
        loop_ids_to_remove = []
        for loop_id, loop in self.active_loops.items():
            if loop.status in ('completed', 'failed') and loop.last_iteration_at:
                if loop.last_iteration_at < cutoff:
                    loop_ids_to_remove.append(loop_id)
        
        for loop_id in loop_ids_to_remove:
            del self.active_loops[loop_id]
            cleaned += 1
        
        logger.debug(f"Cleaned up {cleaned} old loops")
        return cleaned


# Global ULW Loop instance
ulw_loop = ULWLoop()
