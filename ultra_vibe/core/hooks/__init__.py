"""
Hook System for Ultra Vibe.

Provides a plugin-like system for intercepting and modifying Vibe's behavior
at various points in the request/response lifecycle.

Hook Types:
- Pre-prompt hooks: Modify system prompt before LLM call
- Post-response hooks: Process LLM response
- Tool execution hooks: Intercept and modify tool calls
- Model selection hooks: Override model/variant selection
"""

from ultra_vibe.core.hooks.base import (
    Hook,
    HookType,
    HookRegistry,
    HookContext,
    register_hook,
    get_hook,
    get_hooks_by_type,
    execute_hooks,
)

__all__ = [
    "Hook",
    "HookType",
    "HookRegistry",
    "HookContext",
    "register_hook",
    "get_hook",
    "get_hooks_by_type",
    "execute_hooks",
]
