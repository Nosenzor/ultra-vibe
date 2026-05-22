"""
Model Override Hook for Ultrawork Mode.

Automatically escalates models to high-precision variants when
ultrawork mode is active.

Features:
- Model mapping (e.g., mistral-medium -> mistral-large)
- Variant validation (ensure model supports requested variant)
- Configuration-based overrides
- Database persistence
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ultra_vibe.core.hooks.base import Hook, HookContext, HookType, register_hook

logger = logging.getLogger(__name__)


# Default model upgrades for ultrawork mode
ULTRAWORK_MODEL_MAP: Dict[str, str] = {
    # Mistral models
    'mistral-medium-3.5': 'mistral-large-2407',
    'mistral-medium-2402': 'mistral-large-2407',
    'mistral-small-2402': 'mistral-large-2407',
    'devstral': 'mistral-large-2407',
    'devstral-small': 'mistral-medium-3.5',
    
    # Anthropic models
    'anthropic/claude-3-haiku': 'anthropic/claude-3-sonnet',
    'anthropic/claude-3-sonnet': 'anthropic/claude-3-5-sonnet',
    
    # OpenAI models
    'gpt-4o-mini': 'gpt-4o',
    'gpt-4o': 'gpt-4-turbo',
    'gpt-3.5-turbo': 'gpt-4-turbo',
}

# Default variant for models in ultrawork mode
ULTRAWORK_VARIANT_MAP: Dict[str, str] = {
    # Mistral models
    'mistral-large-2407': 'max',
    'mistral-large-2402': 'max',
    'mistral-medium-3.5': 'max',
    'mistral-medium-2402': 'max',
    'mistral-small-2402': 'max',
    
    # Anthropic models
    'anthropic/claude-3-5-sonnet': 'max',
    'anthropic/claude-3-sonnet': 'high',
    'anthropic/claude-3-haiku': 'high',
    
    # OpenAI models
    'gpt-4-turbo': 'max',
    'gpt-4o': 'max',
    'gpt-4': 'max',
}

# Supported variants per model
SUPPORTED_VARIANTS: Dict[str, list] = {
    # Mistral models
    'mistral-large-2407': ['max', 'high', 'medium', 'low'],
    'mistral-large-2402': ['max', 'high', 'medium', 'low'],
    'mistral-medium-3.5': ['max', 'high', 'medium', 'low'],
    'mistral-medium-2402': ['max', 'high', 'medium'],
    'mistral-small-2402': ['medium', 'low'],
    
    # Anthropic models
    'anthropic/claude-3-5-sonnet': ['max', 'high'],
    'anthropic/claude-3-sonnet': ['high', 'medium'],
    'anthropic/claude-3-haiku': ['high', 'low'],
    
    # OpenAI models
    'gpt-4-turbo': ['max', 'high'],
    'gpt-4o': ['max', 'high'],
    'gpt-4': ['max', 'high'],
}


@dataclass
class ModelOverride:
    """Represents a model/variant override."""
    model: str
    variant: str
    source: str  # 'config', 'default', 'explicit'


class ModelOverrideHook(Hook[Tuple[str, str]]):
    """
    Hook that overrides model and variant selection for ultrawork mode.
    
    This hook:
    1. Checks if ultrawork mode is enabled
    2. Resolves the appropriate model and variant
    3. Validates variant support
    4. Persists the override to the database
    
    Priority: 20 (runs after keyword detection)
    Hook Type: MODEL_SELECTION
    """
    
    def __init__(self):
        super().__init__(
            name="model_override",
            hook_type=HookType.MODEL_SELECTION,
            priority=20,
            enabled=True,
        )
    
    def resolve_override(
        self,
        current_model: str,
        current_variant: str,
        config: Optional[Dict[str, Any]] = None,
        agent_name: str = "",
    ) -> Tuple[str, str]:
        """
        Resolve the model and variant override for ultrawork mode.
        
        Args:
            current_model: Currently selected model
            current_variant: Currently selected variant
            config: Vibe configuration dictionary
            agent_name: Name of the current agent
            
        Returns:
            Tuple of (model, variant) to use
        """
        # Check if we have agent-specific config
        if config:
            agent_config = config.get('agents', {}).get(agent_name, {})
            ultrawork_config = agent_config.get('ultrawork', {})
            
            if ultrawork_config.get('enabled', True):
                # Use configured model if specified
                if ultrawork_config.get('model'):
                    model = ultrawork_config['model']
                else:
                    model = ULTRAWORK_MODEL_MAP.get(current_model, current_model)
                
                # Use configured variant if specified
                if ultrawork_config.get('variant'):
                    variant = ultrawork_config['variant']
                else:
                    variant = ULTRAWORK_VARIANT_MAP.get(model, 'max')
                
                # Validate variant support
                variant = validate_variant_support(model, variant, is_ultrawork=True)
                
                return model, variant
        
        # Default behavior without config
        model = ULTRAWORK_MODEL_MAP.get(current_model, current_model)
        variant = ULTRAWORK_VARIANT_MAP.get(model, 'max')
        variant = validate_variant_support(model, variant, is_ultrawork=True)
        
        return model, variant
    
    def __call__(
        self,
        context: HookContext,
        data: Tuple[str, str],
    ) -> Tuple[str, str]:
        """
        Execute the model override hook.
        
        Args:
            context: Hook context containing ultrawork state
            data: Tuple of (current_model, current_variant)
            
        Returns:
            Tuple of (model, variant) - possibly overridden
        """
        current_model, current_variant = data
        
        # Only override if ultrawork is enabled
        if not context.metadata.get('ultrawork_enabled', False):
            return data
        
        # Get config from context if available
        config = context.metadata.get('config', {})
        
        # Resolve the override
        model, variant = self.resolve_override(
            current_model=current_model,
            current_variant=current_variant,
            config=config,
            agent_name=context.agent_name,
        )
        
        # Log the override
        if model != current_model or variant != current_variant:
            logger.info(
                f"Ultrawork model override: {current_model}/{current_variant} -> {model}/{variant}"
            )
            
            # Update context metadata
            context.metadata['ultrawork_model'] = model
            context.metadata['ultrawork_variant'] = variant
            
            # Persist to database (if session is available)
            if context.session_id:
                persist_model_override(
                    session_id=context.session_id,
                    model=model,
                    variant=variant,
                )
        
        return model, variant


def resolve_ultrawork_override(
    current_model: str,
    current_variant: str,
    config: Optional[Dict[str, Any]] = None,
    agent_name: str = "",
) -> Tuple[str, str]:
    """
    Convenience function to resolve ultrawork model override.
    
    This is the main entry point for external code to get the
    overridden model/variant for ultrawork mode.
    
    Args:
        current_model: Currently selected model
        current_variant: Currently selected variant
        config: Optional Vibe configuration
        agent_name: Optional agent name for per-agent config
        
    Returns:
        Tuple of (model, variant)
    """
    hook = ModelOverrideHook()
    return hook.resolve_override(
        current_model=current_model,
        current_variant=current_variant,
        config=config,
        agent_name=agent_name,
    )


def validate_variant_support(model: str, variant: str, is_ultrawork: bool = False) -> str:
    """
    Validate if a model supports the requested reasoning variant.
    
    Falls back to the first supported variant (usually 'medium') if
    the requested variant is not supported.
    In ultrawork mode, defaults to 'max' for unknown models.
    
    Args:
        model: Model name to check
        variant: Requested variant
        is_ultrawork: Whether this is an ultrawork override (default: False)
        
    Returns:
        Validated variant (or fallback)
    """
    supported = SUPPORTED_VARIANTS.get(model, ['max', 'high', 'medium', 'low'] if is_ultrawork else ['medium', 'low'])
    
    if variant in supported:
        return variant
    
    # Fall back to first supported variant
    fallback = supported[0] if supported else ('max' if is_ultrawork else 'medium')
    logger.warning(
        f"Model {model} does not support variant {variant}. Falling back to {fallback}"
    )
    return fallback


def persist_model_override(
    session_id: str,
    model: str,
    variant: str,
) -> bool:
    """
    Persist model override to the session database.
    
    This allows the override to survive session resumes and be
    applied consistently across the session.
    
    Args:
        session_id: Current session ID
        model: Model to persist
        variant: Variant to persist
        
    Returns:
        True if persistence succeeded, False otherwise
    """
    try:
        # In the actual Vibe integration, this would use Vibe's database
        # For now, we just log it
        logger.debug(
            f"Persisting model override for session {session_id}: {model}/{variant}"
        )
        
        # TODO: Implement actual database persistence
        # This would use Vibe's SQLite database similar to opencode.db
        # Example:
        # from ultra_vibe.core.session.database import SessionDB
        # db = SessionDB()
        # db.execute(
        #     "INSERT OR REPLACE INTO session_metadata (session_id, key, value) "
        #     "VALUES (?, 'ultrawork_model', ?), (?, 'ultrawork_variant', ?)",
        #     (session_id, model, session_id, variant)
        # )
        
        return True
    except Exception as e:
        logger.error(f"Failed to persist model override: {e}")
        return False


def get_persisted_override(session_id: str) -> Optional[Tuple[str, str]]:
    """
    Get persisted model override for a session.
    
    Args:
        session_id: Session ID to look up
        
    Returns:
        Tuple of (model, variant) if found, None otherwise
    """
    # TODO: Implement actual database lookup
    # For now, return None
    return None


# Register the hook
model_override_hook = ModelOverrideHook()
register_hook(model_override_hook)
