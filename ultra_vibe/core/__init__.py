"""
Core module for Ultra Vibe.

This package extends Mistral Vibe with Ultrawork Mode capabilities.

Main integration point:
    from ultra_vibe.core.vibe_integration import enable_ultrawork
    enable_ultrawork()

Or use environment variable:
    export VIBE_ULTRAWORK=1
"""

from ultra_vibe.core.vibe_integration import (
    enable_ultrawork,
    disable_ultrawork,
    is_ultrawork_enabled,
    install_agent_configs,
    UltraworkCLI,
)

# Re-export from submodules
from ultra_vibe.core.hooks import (
    Hook,
    HookContext,
    HookType,
    HookRegistry,
    register_hook,
    get_hook,
    get_hooks_by_type,
)
from ultra_vibe.core.hooks.keyword_detector import (
    detect_ultrawork,
    ULTRAWORK_PATTERNS,
    HYPERPLAN_ULTRAWORK_PATTERNS,
)
from ultra_vibe.core.hooks.model_override import (
    resolve_ultrawork_override,
    validate_variant_support,
    persist_model_override,
    get_persisted_override,
)
from ultra_vibe.core.hooks.ultrawork import get_ultrawork_system_prompt
from ultra_vibe.core.ultrawork import (
    ULWLoop,
    LoopState,
    VERIFICATION_PROMPT,
    ULTRAWORK_SYSTEM_PROMPT,
    HYPERPLAN_ULTRAWORK_SYSTEM_PROMPT,
)
from ultra_vibe.core.ultrawork.agents import (
    AgentDefinition,
    AGENT_DEFINITIONS,
    get_agent_definition,
    get_agent_system_prompt,
    SISYPHUS_DEFINITION,
    HEPHAESTUS_DEFINITION,
    ORACLE_DEFINITION,
    LIBRARIAN_DEFINITION,
    EXPLORE_DEFINITION,
)
from ultra_vibe.core.delegation import (
    TaskManager,
    DelegatedTask,
    TaskResult,
    TaskStatus,
    AgentType,
    get_task_manager,
    create_task,
    delegate_task,
    SubAgentPool,
    SubAgentConfig,
    SubAgentResult,
    get_subagent_pool,
    spawn_subagent,
    wait_for_subagent,
    DelegationTool,
)
from ultra_vibe.core.background import (
    BackgroundTaskQueue,
    BackgroundTask,
    TaskPriority,
    get_background_queue,
    enqueue_task,
    wait_for_task,
)
from ultra_vibe.core.middleware.ultrawork import (
    UltraworkMiddleware,
    UltraworkModelMiddleware,
    TaskDelegationMiddleware,
)

__all__ = [
    # Integration
    "enable_ultrawork",
    "disable_ultrawork",
    "is_ultrawork_enabled",
    "install_agent_configs",
    "UltraworkCLI",
    # Hooks
    "Hook",
    "HookContext",
    "HookType",
    "HookRegistry",
    "register_hook",
    "get_hook",
    "get_hooks_by_type",
    # Keyword detection
    "detect_ultrawork",
    "ULTRAWORK_PATTERNS",
    "HYPERPLAN_ULTRAWORK_PATTERNS",
    # Model override
    "resolve_ultrawork_override",
    "validate_variant_support",
    "persist_model_override",
    "get_persisted_override",
    # Protocol
    "get_ultrawork_system_prompt",
    "ULTRAWORK_SYSTEM_PROMPT",
    "HYPERPLAN_ULTRAWORK_SYSTEM_PROMPT",
    # ULW Loop
    "ULWLoop",
    "LoopState",
    "VERIFICATION_PROMPT",
    # Agents
    "AgentDefinition",
    "AGENT_DEFINITIONS",
    "get_agent_definition",
    "get_agent_system_prompt",
    "SISYPHUS_DEFINITION",
    "HEPHAESTUS_DEFINITION",
    "ORACLE_DEFINITION",
    "LIBRARIAN_DEFINITION",
    "EXPLORE_DEFINITION",
    # Delegation
    "TaskManager",
    "DelegatedTask",
    "TaskResult",
    "TaskStatus",
    "AgentType",
    "get_task_manager",
    "create_task",
    "delegate_task",
    "SubAgentPool",
    "SubAgentConfig",
    "SubAgentResult",
    "get_subagent_pool",
    "spawn_subagent",
    "wait_for_subagent",
    "DelegationTool",
    # Background
    "BackgroundTaskQueue",
    "BackgroundTask",
    "TaskPriority",
    "get_background_queue",
    "enqueue_task",
    "wait_for_task",
    # Middleware
    "UltraworkMiddleware",
    "UltraworkModelMiddleware",
    "TaskDelegationMiddleware",
]
