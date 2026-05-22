"""
Ultra Vibe - Ultrawork Mode for Mistral Vibe

This package extends Mistral Vibe with Ultrawork Mode capabilities,
providing multi-agent orchestration and autonomous task execution.

The plugin automatically installs itself when imported.
"""

__version__ = "0.1.0"

# Import plugin components
from ultra_vibe.core.plugin.ultrawork_plugin import (
    UltraworkPlugin,
    ultrawork_plugin,
    install_ultrawork,
    uninstall_ultrawork,
    is_ultrawork_installed,
)

# Import core components
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
from ultra_vibe.core.ultrawork.agents import AGENT_DEFINITIONS, get_agent_definition

# Auto-install the plugin when ultra_vibe is imported
# This ensures ultrawork mode is available when vibe starts
try:
    install_ultrawork()
except Exception:
    # Silently fail if vibe is not available during import
    # This is fine - the plugin will be installed when vibe loads it
    pass

__all__ = [
    "__version__",
    # Plugin
    "UltraworkPlugin",
    "ultrawork_plugin",
    "install_ultrawork",
    "uninstall_ultrawork",
    "is_ultrawork_installed",
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
    # Agents
    "AGENT_DEFINITIONS",
    "get_agent_definition",
]
