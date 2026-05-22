"""
Ultrawork Hook for protocol injection and management.

This hook injects the Ultrawork protocol into the system prompt
when ultrawork mode is enabled.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ultra_vibe.core.hooks.base import Hook, HookContext, HookType, register_hook

logger = logging.getLogger(__name__)


# Ultrawork protocol system prompt
ULTRAWORK_SYSTEM_PROMPT = """
You are in **ULTRAWORK MODE**. Follow these rules **strictly**:

## RULE 1: MANDATORY CERTAINTY (100%)
You MUST achieve 100% certainty before implementing any code or making any changes.

- Use `subagent_type="explore"` to gather codebase context and understand the full scope
- Use `subagent_type="oracle"` for architectural review and validation
- Never guess, assume, or make changes without complete understanding
- If you are unsure about ANYTHING, delegate to a specialist agent for verification

## RULE 2: MANDATORY PLANNING
For **any task involving 2 or more steps**, you MUST call the `plan` agent.

- Use: `delegate_task(agent="plan", task=<detailed_task_description>)`
- The plan agent will generate a structured task graph
- Use the returned `task_id` for all follow-up questions to save tokens and maintain state
- This is NOT optional - you MUST plan before executing

## RULE 3: AGGRESSIVE DELEGATION
You are an **orchestrator**, not an implementer. Delegate work to specialist agents:

- **Hephaestus**: Deep implementation tasks, complex coding, refactoring, optimization
- **Librarian**: Documentation generation, research, knowledge lookup, context gathering
- **Oracle**: Architecture review, code review, security analysis, best practices
- **Explore**: Codebase exploration, repository analysis, context building

You should delegate at least 80% of implementation work. Only do minimal work yourself.

## RULE 4: MODEL OPTIMIZATION
Your model and reasoning capabilities are **automatically upgraded** to the highest precision.
- You are using maximum reasoning effort
- Take your time to think thoroughly
- Do not rush - quality over speed

## ADDITIONAL RULES
- Always use `task_id` for continuity across session resumes
- Maintain complete task state and context
- Be thorough, methodical, and precise
- Verify everything multiple times before finalizing

Remember: **Delegate, Verify, Plan, Execute** - in that order.
"""

# Hyperplan + Ultrawork combo protocol
HYPERPLAN_ULTRAWORK_SYSTEM_PROMPT = """
You are in **HYPERPLAN + ULTRAWORK MODE** - the most powerful combination.

Follow the Ultrawork rules (see below) PLUS:

## ADVERSARIAL PLANNING WORKFLOW

1. **Load the hyperplan skill**: Use `load_skill_from_pathAsync` or similar
2. **Independent Analysis**: Each specialist agent must analyze the task independently
3. **Cross-Attacks**: Agents must challenge each other's findings and assumptions
4. **Synthesis**: Combine all analyses into a comprehensive plan
5. **Execution**: Only after adversarial review, proceed with implementation

## HYPERPLAN SPECIFIC RULES
- Minimum 3 agents must participate in planning
- Each agent must provide at least 5 potential issues/risks
- All conflicts must be resolved before execution
- The final plan must be approved by Oracle (architecture review)

---

""" + ULTRAWORK_SYSTEM_PROMPT


class UltraworkHook(Hook[str]):
    """
    Hook that injects the Ultrawork protocol into system prompts.
    
    This hook:
    1. Checks if ultrawork mode is enabled in the context
    2. Injects the appropriate protocol (standard or hyperplan combo)
    3. Ensures the protocol is prepended to the existing system prompt
    
    Priority: 30 (runs after keyword detection and model override)
    Hook Type: PRE_PROMPT
    """
    
    def __init__(self):
        super().__init__(
            name="ultrawork_protocol",
            hook_type=HookType.PRE_PROMPT,
            priority=30,
            enabled=True,
        )
    
    def get_protocol(self, context: HookContext) -> str:
        """
        Get the appropriate ultrawork protocol for the context.
        
        Args:
            context: Hook context containing ultrawork state
            
        Returns:
            Protocol string to inject
        """
        if context.metadata.get('hyperplan_ultrawork_enabled', False):
            return HYPERPLAN_ULTRAWORK_SYSTEM_PROMPT
        return ULTRAWORK_SYSTEM_PROMPT
    
    def __call__(self, context: HookContext, data: str) -> str:
        """
        Execute the ultrawork hook.
        
        Injects the ultrawork protocol into the system prompt when enabled.
        
        Args:
            context: Hook context
            data: Current system prompt
            
        Returns:
            Modified system prompt with ultrawork protocol prepended
        """
        # Only inject if ultrawork is enabled
        if not context.metadata.get('ultrawork_enabled', False):
            return data
        
        # Get the appropriate protocol
        protocol = self.get_protocol(context)
        
        # Prepend protocol to existing system prompt
        if data:
            # Check if protocol is already injected (avoid duplication)
            if protocol.strip() in data:
                return data
            new_prompt = f"{protocol}\n\n{data}"
        else:
            new_prompt = protocol
        
        logger.debug("Ultrawork protocol injected into system prompt")
        
        return new_prompt


def get_ultrawork_system_prompt(hyperplan: bool = False) -> str:
    """
    Get the ultrawork system prompt.
    
    This is the main entry point for external code to get the
    ultrawork protocol string.
    
    Args:
        hyperplan: If True, return the hyperplan + ultrawork combo protocol
        
    Returns:
        Ultrawork system prompt string
    """
    if hyperplan:
        return HYPERPLAN_ULTRAWORK_SYSTEM_PROMPT
    return ULTRAWORK_SYSTEM_PROMPT


# Register the hook
ultrawork_hook = UltraworkHook()
register_hook(ultrawork_hook)
