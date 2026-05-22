"""
Ultrawork Middleware for Vibe.

Implements Ultrawork Mode as Vibe middleware, intercepting
conversations to enable multi-agent orchestration.
"""

from __future__ import annotations

import logging
from typing import Any, Optional



logger = logging.getLogger(__name__)


# Runtime imports - try to import from Vibe
try:
    from ultra_vibe.core.middleware import (
        ConversationContext as VibeConversationContext,
        ConversationMiddleware as VibeConversationMiddleware,
        MiddlewareAction as VibeMiddlewareAction,
        MiddlewareResult as VibeMiddlewareResult,
    )
    from ultra_vibe.core.config import VibeConfig as VibeVibeConfig
    
    ConversationContext = VibeConversationContext
    ConversationMiddleware = VibeConversationMiddleware
    MiddlewareAction = VibeMiddlewareAction
    MiddlewareResult = VibeMiddlewareResult
    VibeConfig = VibeVibeConfig
except ImportError:
    # Vibe not installed - define minimal stubs for testing
    from dataclasses import dataclass
    from typing import Any, Optional, Protocol, runtime_checkable
    
    @runtime_checkable
    class ConversationMiddleware(Protocol):
        def reset(self, reset_reason: str = "STOP") -> None: ...
        async def before_turn(self, context: "ConversationContext") -> "MiddlewareResult": ...
    
    @dataclass
    class ConversationContext:
        messages: list[dict[str, Any]]
        config: Any = None
        stats: Any = None
    
    @dataclass
    class MiddlewareResult:
        action: Optional[str] = None
        message: str = ""
        metadata: dict[str, Any] = None
        
        def __post_init__(self):
            if self.metadata is None:
                self.metadata = {}
    
    class MiddlewareAction:
        INJECT_MESSAGE = "INJECT_MESSAGE"
        CONTINUE = "CONTINUE"
        STOP = "STOP"
        COMPACT = "COMPACT"
    
    class VibeConfig:
        pass


class UltraworkMiddleware(ConversationMiddleware):
    """
    Middleware that enables Ultrawork Mode detection and protocol injection.
    
    This middleware:
    1. Detects ultrawork mode keywords in user messages
    2. Injects ultrawork protocol into system prompts
    3. Manages ultrawork state across turns
    """
    
    def __init__(self, config: VibeConfig):
        self.config = config
        self.ultrawork_enabled: bool = False
        self.hyperplan_enabled: bool = False
        self.task_id: Optional[str] = None
        self.loop_id: Optional[str] = None
        
    def reset(self, reset_reason: str = "STOP") -> None:
        """Reset ultrawork state."""
        self.ultrawork_enabled = False
        self.hyperplan_enabled = False
        self.task_id = None
        self.loop_id = None
        logger.debug("Ultrawork middleware reset")
    
    def _detect_ultrawork(self, message: str) -> tuple[bool, bool]:
        """
        Detect if message triggers ultrawork or hyperplan ultrawork.
        
        Returns:
            Tuple of (ultrawork_detected, hyperplan_detected)
        """
        from ultra_vibe.core.hooks.keyword_detector import detect_ultrawork
        
        # Check for hyperplan combo first
        import re
        hyperplan_patterns = [
            r'\bhpp\s+ulw\b',
            r'\bulw\s+hyperplan\b',
            r'\bhyperplan\s+ulw\b',
        ]
        for pattern in hyperplan_patterns:
            if re.search(pattern, message, re.IGNORECASE):
                return True, True
        
        # Check for regular ultrawork
        if detect_ultrawork(message):
            return True, False
        
        return False, False
    
    def _get_ultrawork_protocol(self, hyperplan: bool = False) -> str:
        """Get the ultrawork protocol to inject."""
        from ultra_vibe.core.ultrawork.protocol import get_ultrawork_system_prompt
        return get_ultrawork_system_prompt(hyperplan=hyperplan)
    
    async def before_turn(self, context: ConversationContext) -> MiddlewareResult:
        """
        Intercept conversation before each turn.
        
        Detects ultrawork keywords and manages state.
        """
        # Get the latest user message
        messages = context.messages
        if not messages:
            return MiddlewareResult()
        
        # Check the most recent message for ultrawork triggers
        latest_message = messages[-1]
        content = latest_message.get('content', '') if isinstance(latest_message, dict) else str(latest_message)
        
        # Detect ultrawork mode
        is_ultrawork, is_hyperplan = self._detect_ultrawork(content)
        
        # If already in ultrawork mode, maintain it
        if self.ultrawork_enabled:
            # But check if we should also enable hyperplan
            if is_hyperplan:
                self.hyperplan_enabled = True
            return MiddlewareResult()
        
        # If we detected ultrawork, enable it
        if is_ultrawork:
            self.ultrawork_enabled = True
            self.hyperplan_enabled = is_hyperplan
            logger.info(f"Ultrawork mode enabled (hyperplan: {is_hyperplan})")
            
            # Generate task_id if this is the start
            if not self.task_id:
                import uuid
                self.task_id = f"ulw-task-{uuid.uuid4().hex[:12]}"
                logger.debug(f"Generated task_id: {self.task_id}")
            
            # Inject protocol into context
            return MiddlewareResult(
                action=MiddlewareAction.INJECT_MESSAGE,
                message=self._get_ultrawork_protocol(is_hyperplan),
                metadata={
                    'ultrawork_enabled': True,
                    'hyperplan_enabled': is_hyperplan,
                    'task_id': self.task_id,
                }
            )
        
        return MiddlewareResult()


class UltraworkModelMiddleware(ConversationMiddleware):
    """
    Middleware that handles model overrides for Ultrawork Mode.
    
    This middleware:
    1. Checks if ultrawork mode is active
    2. Overrides model and variant to high-precision versions
    """
    
    def __init__(self, config: VibeConfig):
        self.config = config
        self.original_model: Optional[str] = None
        self.original_variant: Optional[str] = None
        
    def reset(self, reset_reason: str = "STOP") -> None:
        """Reset model override state."""
        self.original_model = None
        self.original_variant = None
        
    async def before_turn(self, context: ConversationContext) -> MiddlewareResult:
        """
        Override model selection for ultrawork mode.
        """
        # Check if ultrawork is enabled by detecting keywords in messages
        messages = context.messages
        if not messages:
            return MiddlewareResult()
        
        # Check the most recent message for ultrawork triggers
        latest_message = messages[-1]
        content = latest_message.get('content', '') if isinstance(latest_message, dict) else str(latest_message)
        
        # Detect ultrawork mode
        from ultra_vibe.core.hooks.keyword_detector import detect_ultrawork
        if not detect_ultrawork(content):
            return MiddlewareResult()
        
        # Get current model config
        current_model = context.config.get_active_model()
        
        # Resolve ultrawork override
        from ultra_vibe.core.hooks.model_override import resolve_ultrawork_override
        
        model_name = current_model.name if hasattr(current_model, 'name') else str(current_model)
        variant = getattr(current_model, 'variant', 'medium')
        
        overridden_model, overridden_variant = resolve_ultrawork_override(
            current_model=model_name,
            current_variant=variant,
            config=self.config.model_dump() if hasattr(self.config, 'model_dump') else {},
        )
        
        # If we need to override
        if model_name != overridden_model or variant != overridden_variant:
            logger.info(f"Ultrawork model override: {model_name}/{variant} -> {overridden_model}/{overridden_variant}")
            
            # Store original for restoration
            if self.original_model is None:
                self.original_model = model_name
                self.original_variant = variant
            
            # Return override instruction
            return MiddlewareResult(
                action=MiddlewareAction.CONTINUE,
                metadata={
                    'model_override': overridden_model,
                    'variant_override': overridden_variant,
                }
            )
        
        return MiddlewareResult()


class TaskDelegationMiddleware(ConversationMiddleware):
    """
    Middleware for handling task delegation in Ultrawork Mode.
    
    This middleware:
    1. Detects delegate_task calls from the agent
    2. Spawns sub-agents for parallel execution
    3. Aggregates results
    """
    
    def __init__(self, config: VibeConfig):
        self.config = config
        self.pending_delegations: dict[str, Any] = {}
        self.completed_delegations: dict[str, Any] = {}
        
    def reset(self, reset_reason: str = "STOP") -> None:
        """Reset delegation state."""
        self.pending_delegations.clear()
        self.completed_delegations.clear()
        
    async def before_turn(self, context: ConversationContext) -> MiddlewareResult:
        """
        Handle task delegation.
        """
        # Check for delegation in the latest message
        messages = context.messages
        if not messages:
            return MiddlewareResult()
        
        latest = messages[-1]
        content = latest.get('content', '') if isinstance(latest, dict) else str(latest)
        
        # Check if this is a delegation request
        if 'delegate_task' in content.lower():
            # Parse delegation (simplified - would use LLM parsing in reality)
            # For now, just detect and acknowledge
            logger.debug("Delegation request detected")
            return MiddlewareResult(
                action=MiddlewareAction.INJECT_MESSAGE,
                message="Delegation received. Spawning sub-agents...",
                metadata={'delegation_detected': True}
            )
        
        return MiddlewareResult()
