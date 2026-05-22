"""
Base classes and utilities for the hook system.

This module provides the foundation for Vibe's hook system, allowing
interception and modification of behavior at key points in the
request/response lifecycle.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar, Generic

logger = logging.getLogger(__name__)


class HookType(Enum):
    """Types of hooks that can be registered."""
    
    # Before LLM call
    PRE_PROMPT = "pre_prompt"
    # After LLM response
    POST_RESPONSE = "post_response"
    # Before tool execution
    PRE_TOOL = "pre_tool"
    # After tool execution
    POST_TOOL = "post_tool"
    # Model/variant selection
    MODEL_SELECTION = "model_selection"
    # Session creation
    SESSION_CREATED = "session_created"
    # Session initialization
    SESSION_INIT = "session_init"


@dataclass
class HookContext:
    """
    Context passed to hook functions.
    
    Contains information about the current state that hooks can use
    to make decisions.
    """
    # Session information
    session_id: str
    session: Any = None
    
    # Message information
    message: str = ""
    messages: List[Dict[str, Any]] = field(default_factory=list)
    
    # Agent information
    agent_name: str = ""
    agent_config: Dict[str, Any] = field(default_factory=dict)
    
    # Model information
    current_model: str = ""
    current_variant: str = ""
    
    # Tool information (for tool hooks)
    tool_name: str = ""
    tool_args: Dict[str, Any] = field(default_factory=dict)
    
    # Ultrawork state
    ultrawork_enabled: bool = False
    task_id: Optional[str] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


T = TypeVar('T')


class Hook(Generic[T]):
    """
    Base class for hooks.
    
    Hooks are callable objects that can intercept and modify
    Vibe's behavior at specific points.
    
    Attributes:
        name: Unique identifier for the hook
        hook_type: Type of hook (pre_prompt, post_response, etc.)
        priority: Execution order (lower = earlier)
        enabled: Whether the hook is active
    """
    
    def __init__(
        self,
        name: str,
        hook_type: HookType,
        priority: int = 50,
        enabled: bool = True,
    ):
        self.name = name
        self.hook_type = hook_type
        self.priority = priority
        self.enabled = enabled
    
    def __call__(self, context: HookContext, data: T) -> T:
        """
        Execute the hook.
        
        Args:
            context: Hook context with current state
            data: Input data to potentially modify
            
        Returns:
            Modified data (or original if no modification)
        """
        return data
    
    def __repr__(self) -> str:
        return f"Hook(name={self.name!r}, type={self.hook_type.value}, priority={self.priority})"


class HookRegistry:
    """
    Registry for managing hooks.
    
    Provides methods to register, retrieve, and execute hooks.
    Hooks are organized by type and executed in priority order.
    """
    
    def __init__(self):
        self._hooks: Dict[HookType, List[Hook]] = {t: [] for t in HookType}
        self._registered_hooks: Dict[str, Hook] = {}
    
    def register(self, hook: Hook) -> None:
        """Register a hook."""
        if hook.name in self._registered_hooks:
            logger.warning(f"Hook {hook.name} already registered, replacing")
        
        self._registered_hooks[hook.name] = hook
        self._hooks[hook.hook_type].append(hook)
        # Sort by priority
        self._hooks[hook.hook_type].sort(key=lambda h: h.priority)
        logger.debug(f"Registered hook: {hook}")
    
    def unregister(self, name: str) -> bool:
        """Unregister a hook by name."""
        if name not in self._registered_hooks:
            return False
        
        hook = self._registered_hooks.pop(name)
        if hook in self._hooks[hook.hook_type]:
            self._hooks[hook.hook_type].remove(hook)
        
        logger.debug(f"Unregistered hook: {hook.name}")
        return True
    
    def get(self, name: str) -> Optional[Hook]:
        """Get a hook by name."""
        return self._registered_hooks.get(name)
    
    def get_all(self, hook_type: Optional[HookType] = None) -> List[Hook]:
        """Get all hooks, optionally filtered by type."""
        if hook_type is not None:
            return list(self._hooks[hook_type])
        
        all_hooks = []
        for hooks in self._hooks.values():
            all_hooks.extend(hooks)
        return all_hooks
    
    def execute(
        self,
        hook_type: HookType,
        context: HookContext,
        data: T,
    ) -> T:
        """
        Execute all hooks of a given type.
        
        Hooks are executed in priority order (lowest first).
        Each hook can modify the data, and the result is passed to the next.
        """
        hooks = self._hooks[hook_type]
        
        for hook in hooks:
            if not hook.enabled:
                continue
            
            try:
                logger.debug(f"Executing hook: {hook.name}")
                data = hook(context, data)
            except Exception as e:
                logger.error(f"Hook {hook.name} failed: {e}")
                # Continue with original data on error
                
        return data
    
    def clear(self) -> None:
        """Clear all registered hooks."""
        self._hooks = {t: [] for t in HookType}
        self._registered_hooks.clear()


# Global hook registry instance
_hook_registry = HookRegistry()


def register_hook(hook: Hook) -> Hook:
    """
    Decorator to register a hook.
    
    Usage:
        @register_hook
        class MyHook(Hook):
            ...
    
    Or:
        hook = MyHook(...)
        register_hook(hook)
    """
    _hook_registry.register(hook)
    return hook


def get_hook(name: str) -> Optional[Hook]:
    """Get a registered hook by name."""
    return _hook_registry.get(name)


def get_hooks_by_type(hook_type: HookType) -> List[Hook]:
    """Get all hooks of a specific type."""
    return _hook_registry.get_all(hook_type)


def execute_hooks(hook_type: HookType, context: HookContext, data: T) -> T:
    """Execute all hooks of a given type."""
    return _hook_registry.execute(hook_type, context, data)
