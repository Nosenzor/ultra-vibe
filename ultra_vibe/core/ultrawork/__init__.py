"""
Ultrawork-specific components for Vibe.

This module contains the core Ultrawork Mode functionality:
- ULW Loop for persistent iteration
- Protocol definitions
- Agent definitions
- Task management
"""

from ultra_vibe.core.ultrawork.loop import ULWLoop, LoopState, VERIFICATION_PROMPT
from ultra_vibe.core.ultrawork.protocol import (
    get_ultrawork_system_prompt,
    ULTRAWORK_SYSTEM_PROMPT,
    HYPERPLAN_ULTRAWORK_SYSTEM_PROMPT,
)
from ultra_vibe.core.ultrawork.agents import (
    AGENT_DEFINITIONS,
    get_agent_definition,
    SISYPHUS_DEFINITION,
    HEPHAESTUS_DEFINITION,
    ORACLE_DEFINITION,
    LIBRARIAN_DEFINITION,
    EXPLORE_DEFINITION,
)

__all__ = [
    # Loop
    "ULWLoop",
    "LoopState",
    "VERIFICATION_PROMPT",
    # Protocol
    "get_ultrawork_system_prompt",
    "ULTRAWORK_SYSTEM_PROMPT",
    "HYPERPLAN_ULTRAWORK_SYSTEM_PROMPT",
    # Agents
    "AGENT_DEFINITIONS",
    "get_agent_definition",
    "SISYPHUS_DEFINITION",
    "HEPHAESTUS_DEFINITION",
    "ORACLE_DEFINITION",
    "LIBRARIAN_DEFINITION",
    "EXPLORE_DEFINITION",
]
