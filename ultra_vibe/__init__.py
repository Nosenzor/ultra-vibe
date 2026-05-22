"""
Ultra Vibe - Ultrawork Mode for Mistral Vibe

This package extends Mistral Vibe with Ultrawork Mode capabilities,
providing multi-agent orchestration and autonomous task execution.
"""

__version__ = "0.1.0"

from ultra_vibe.core.hooks import (
    HookRegistry,
    register_hook,
    get_hook,
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
)
from ultra_vibe.core.ultrawork.protocol import get_ultrawork_system_prompt

__all__ = [
    "__version__",
    # Hook system
    "HookRegistry",
    "register_hook",
    "get_hook",
    # Keyword detection
    "detect_ultrawork",
    "ULTRAWORK_PATTERNS",
    "HYPERPLAN_ULTRAWORK_PATTERNS",
    # Model override
    "resolve_ultrawork_override",
    "validate_variant_support",
    "persist_model_override",
    # Protocol
    "get_ultrawork_system_prompt",
]
