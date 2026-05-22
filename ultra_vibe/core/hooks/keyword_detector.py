"""
Keyword Detection Hook for Ultrawork Mode.

Detects ultrawork mode triggers in user messages and enables
ultrawork functionality accordingly.

Triggers:
- Explicit commands: /ultrawork, /ulw
- Natural language: "ultrawork", "ulw" (word boundaries)
- Combo modes: "hpp ulw", "ulw hyperplan"
- Session state: If ultrawork was previously enabled
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from ultra_vibe.core.hooks.base import Hook, HookContext, HookType, register_hook


# Ultrawork trigger patterns
ULTRAWORK_PATTERNS: List[str] = [
    r'\bultrawork\b',
    r'\bulw\b',
    r'/ultrawork',
    r'/ulw',
]

# Hyperplan + Ultrawork combo patterns
HYPERPLAN_ULTRAWORK_PATTERNS: List[str] = [
    r'\bhpp\s+ulw\b',
    r'\bulw\s+hyperplan\b',
    r'\bhyperplan\s+ulw\b',
    r'/hpp\s+/ulw',
    r'/ulw\s+/hpp',
]

# Compiled patterns for efficiency
_COMPILED_ULTRAWORK = [re.compile(p, re.IGNORECASE) for p in ULTRAWORK_PATTERNS]
_COMPILED_HYPERPLAN_ULTRAWORK = [
    re.compile(p, re.IGNORECASE) for p in HYPERPLAN_ULTRAWORK_PATTERNS
]

# Agents that should not trigger ultrawork mode (to prevent recursion)
NON_ULTRAWORK_AGENTS: set = {
    'plan',
    'prometheus',
    'sisyphus',
    'hephaestus',
    'oracle',
    'librarian',
    'explore',
}

# Planner agents that should filter out ultrawork keywords
PLANNER_AGENTS: set = {
    'plan',
    'prometheus',
}


class KeywordDetectorHook(Hook[str]):
    """
    Hook that detects ultrawork mode keywords in user messages.
    
    This hook:
    1. Checks if the current message contains ultrawork triggers
    2. Checks if we're in a sub-agent session (avoid recursion)
    3. Checks if the current agent is a planner (filter out keywords)
    4. Injects ultrawork state into the context
    
    Priority: 10 (high priority - detect mode early)
    Hook Type: PRE_PROMPT (modifies system prompt)
    """
    
    def __init__(self):
        super().__init__(
            name="keyword_detector",
            hook_type=HookType.PRE_PROMPT,
            priority=10,
            enabled=True,
        )
    
    def _is_planner_agent(self, agent_name: str) -> bool:
        """Check if the current agent is a planner type."""
        return agent_name.lower() in PLANNER_AGENTS
    
    def _is_non_ultrawork_agent(self, agent_name: str) -> bool:
        """Check if the current agent should skip ultrawork detection."""
        return agent_name.lower() in NON_ULTRAWORK_AGENTS
    
    def _matches_pattern(self, message: str, patterns: List[re.Pattern]) -> bool:
        """Check if message matches any of the compiled patterns."""
        for pattern in patterns:
            if pattern.search(message):
                return True
        return False
    
    def detect_from_message(self, message: str) -> bool:
        """
        Detect if a message triggers ultrawork mode.
        
        Args:
            message: The user message to check
            
        Returns:
            True if ultrawork should be enabled
        """
        return self._matches_pattern(message, _COMPILED_ULTRAWORK)
    
    def detect_hyperplan_ultrawork(self, message: str) -> bool:
        """
        Detect if a message triggers hyperplan + ultrawork combo mode.
        
        Args:
            message: The user message to check
            
        Returns:
            True if hyperplan ultrawork combo should be enabled
        """
        return self._matches_pattern(message, _COMPILED_HYPERPLAN_ULTRAWORK)
    
    def __call__(self, context: HookContext, data: str) -> str:
        """
        Execute the keyword detection hook.
        
        This modifies the system prompt or context to enable ultrawork mode
        when keywords are detected.
        
        Args:
            context: Hook context containing session state
            data: The current system prompt (not used directly)
            
        Returns:
            Modified system prompt with ultrawork protocol if enabled
        """
        # Safety check: Don't trigger in planner agents
        if self._is_planner_agent(context.agent_name):
            # Filter out ultrawork keywords from the message to prevent recursion
            # This is done elsewhere in the pipeline
            return data
        
        # Check if we're in a sub-agent session (avoid recursive delegation)
        # This would be checked via session metadata in actual implementation
        if context.metadata.get('is_subagent_session', False):
            # Allow ultrawork to propagate in main session only
            if not context.metadata.get('is_main_session', True):
                return data
        
        # Check for ultrawork keywords in the current message
        is_ultrawork = self.detect_from_message(context.message)
        is_hyperplan_ultrawork = self.detect_hyperplan_ultrawork(context.message)
        
        # Also check if ultrawork is already enabled in this session
        already_enabled = context.ultrawork_enabled
        
        # Update context metadata with detection results
        context.metadata['ultrawork_detected'] = is_ultrawork
        context.metadata['hyperplan_ultrawork_detected'] = is_hyperplan_ultrawork
        
        # If we should enable ultrawork, inject the protocol
        if is_ultrawork or is_hyperplan_ultrawork or already_enabled:
            # Mark as ultrawork enabled in metadata
            context.metadata['ultrawork_enabled'] = True
            
            # If hyperplan combo, mark that too
            if is_hyperplan_ultrawork:
                context.metadata['hyperplan_ultrawork_enabled'] = True
            
            # The actual protocol injection happens in the ultrawork hook
            # which has lower priority (runs after this)
        
        return data


# Pattern exports for external use
ULTRAWORK_PATTERNS_REGEX = [re.compile(p, re.IGNORECASE) for p in ULTRAWORK_PATTERNS]
HYPERPLAN_ULTRAWORK_PATTERNS_REGEX = [
    re.compile(p, re.IGNORECASE) for p in HYPERPLAN_ULTRAWORK_PATTERNS
]


def detect_ultrawork(message: str, agent_name: str = "", session_metadata: Optional[Dict[str, Any]] = None) -> bool:
    """
    Convenience function to detect ultrawork mode from a message.
    
    This is the main entry point for external code to check if ultrawork
    should be enabled.
    
    Args:
        message: The user message to check
        agent_name: Current agent name (to check exclusions)
        session_metadata: Optional session metadata (for sub-agent check)
        
    Returns:
        True if ultrawork mode should be enabled
    """
    # Check for keywords in message
    for pattern in _COMPILED_ULTRAWORK + _COMPILED_HYPERPLAN_ULTRAWORK:
        if pattern.search(message):
            # Exclude planner agents
            if agent_name.lower() in PLANNER_AGENTS:
                return False
            # Exclude non-ultrawork agents (optional, based on config)
            # Allow in main session or if explicitly configured
            return True
    
    # Check session metadata
    if session_metadata:
        if session_metadata.get('ultrawork_enabled', False):
            return True
    
    return False


# Register the hook
keyword_detector_hook = KeywordDetectorHook()
register_hook(keyword_detector_hook)
