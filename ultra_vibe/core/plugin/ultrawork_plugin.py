"""
Ultrawork Plugin for Mistral Vibe.

This is the main integration point that:
1. Registers Ultrawork middleware with Vibe
2. Registers Ultrawork agents
3. Registers Ultrawork tools
4. Adds CLI flags

Usage:
    from ultra_vibe.core.plugin.ultrawork_plugin import UltraworkPlugin
    plugin = UltraworkPlugin()
    plugin.install()
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from ultra_vibe.core.middleware import MiddlewarePipeline
    from ultra_vibe.core.agents.manager import AgentManager
    from ultra_vibe.core.config import VibeConfig

logger = logging.getLogger(__name__)


class UltraworkPlugin:
    """
    Plugin that integrates Ultrawork Mode with Mistral Vibe.
    
    This plugin:
    - Adds Ultrawork middleware to the pipeline
    - Registers specialist agents
    - Registers delegation tools
    - Enables ultrawork CLI flags
    """
    
    def __init__(self):
        self._installed = False
        self._middleware_added = False
        self._agents_registered = False
        self._tools_registered = False
        
    def install(
        self,
        middleware_pipeline: Optional["MiddlewarePipeline"] = None,
        agent_manager: Optional["AgentManager"] = None,
        tool_manager: Optional[Any] = None,
        config: Optional["VibeConfig"] = None,
    ) -> None:
        """
        Install the Ultrawork plugin.
        
        Args:
            middleware_pipeline: Vibe's middleware pipeline
            agent_manager: Vibe's agent manager
            tool_manager: Vibe's tool manager
            config: Vibe configuration
        """
        if self._installed:
            logger.debug("Ultrawork plugin already installed")
            return
        
        logger.info("Installing Ultrawork Mode plugin...")
        
        # Install components
        self._install_middleware(middleware_pipeline, config)
        self._install_agents(agent_manager, config)
        self._install_tools(tool_manager, config)
        
        self._installed = True
        logger.info("Ultrawork Mode plugin installed successfully")
    
    def _install_middleware(
        self,
        pipeline: Optional["MiddlewarePipeline"],
        config: Optional["VibeConfig"],
    ) -> None:
        """Install Ultrawork middleware."""
        if pipeline is None:
            logger.debug("No middleware pipeline provided, skipping middleware installation")
            return
        
        from ultra_vibe.core.middleware.ultrawork import (
            UltraworkMiddleware,
            UltraworkModelMiddleware,
            TaskDelegationMiddleware,
        )
        
        # Create middleware instances
        ultrawork_middleware = UltraworkMiddleware(config or VibeConfig())
        model_middleware = UltraworkModelMiddleware(config or VibeConfig())
        delegation_middleware = TaskDelegationMiddleware(config or VibeConfig())
        
        # Add to pipeline
        pipeline.add(ultrawork_middleware)
        pipeline.add(model_middleware)
        pipeline.add(delegation_middleware)
        
        self._middleware_added = True
        logger.info("Ultrawork middleware installed")
    
    def _install_agents(
        self,
        agent_manager: Optional["AgentManager"],
        config: Optional["VibeConfig"],
    ) -> None:
        """Register Ultrawork specialist agents."""
        if agent_manager is None:
            logger.debug("No agent manager provided, skipping agent registration")
            return
        
        from ultra_vibe.core.ultrawork.agents import (
            SISYPHUS_DEFINITION,
            HEPHAESTUS_DEFINITION,
            ORACLE_DEFINITION,
            LIBRARIAN_DEFINITION,
            EXPLORE_DEFINITION,
        )
        from ultra_vibe.core.agents.models import AgentProfile, AgentType, AgentSafety
        
        # Convert our AgentDefinition to Vibe's AgentProfile
        def create_agent_profile(definition) -> AgentProfile:
            return AgentProfile(
                name=definition.name,
                display_name=definition.name.title(),
                description=definition.description,
                safety=AgentSafety.NEUTRAL,  # Ultrawork agents are safe
                agent_type=AgentType.AGENT,
                overrides={
                    'system_prompt': definition.system_prompt,
                    'model': definition.default_model,
                    'variant': definition.default_variant,
                    'enabled_tools': definition.enabled_tools,
                    'disabled_tools': definition.disabled_tools,
                },
                install_required=False,
            )
        
        # Register each specialist agent
        agents_to_register = [
            SISYPHUS_DEFINITION,
            HEPHAESTUS_DEFINITION,
            ORACLE_DEFINITION,
            LIBRARIAN_DEFINITION,
            EXPLORE_DEFINITION,
        ]
        
        for definition in agents_to_register:
            profile = create_agent_profile(definition)
            try:
                agent_manager.register_agent(profile)
                logger.info(f"Registered Ultrawork agent: {definition.name}")
            except Exception as e:
                logger.warning(f"Failed to register agent {definition.name}: {e}")
        
        self._agents_registered = True
    
    def _install_tools(
        self,
        tool_manager: Optional[Any],
        config: Optional["VibeConfig"],
    ) -> None:
        """Register Ultrawork tools."""
        if tool_manager is None:
            logger.debug("No tool manager provided, skipping tool registration")
            return
        
        from ultra_vibe.core.tools.delegate_task import DelegateTaskTool
        
        # Create delegation tool
        delegate_tool = DelegateTaskTool()
        
        try:
            # Register with tool manager
            # The exact method depends on Vibe's tool manager API
            # This is a placeholder - actual implementation would use Vibe's API
            if hasattr(tool_manager, 'register_tool'):
                tool_manager.register_tool(delegate_tool)
            elif hasattr(tool_manager, 'add_tool'):
                tool_manager.add_tool(delegate_tool)
            
            logger.info("Registered delegate_task tool")
            self._tools_registered = True
        except Exception as e:
            logger.warning(f"Failed to register delegate_task tool: {e}")
    
    def uninstall(self) -> None:
        """Uninstall the Ultrawork plugin."""
        if not self._installed:
            return
        
        logger.info("Uninstalling Ultrawork Mode plugin...")
        
        # Note: Cleanup would require references to the components
        # For now, just mark as uninstalled
        self._installed = False
        self._middleware_added = False
        self._agents_registered = False
        self._tools_registered = False
        
        logger.info("Ultrawork Mode plugin uninstalled")
    
    @property
    def is_installed(self) -> bool:
        """Check if plugin is installed."""
        return self._installed
    
    @property
    def middleware_added(self) -> bool:
        """Check if middleware was added."""
        return self._middleware_added
    
    @property
    def agents_registered(self) -> bool:
        """Check if agents were registered."""
        return self._agents_registered
    
    @property
    def tools_registered(self) -> bool:
        """Check if tools were registered."""
        return self._tools_registered


# Singleton instance
ultrawork_plugin = UltraworkPlugin()


# Convenience functions
def install_ultrawork() -> None:
    """Install Ultrawork Mode (convenience function)."""
    ultrawork_plugin.install()


def uninstall_ultrawork() -> None:
    """Uninstall Ultrawork Mode (convenience function)."""
    ultrawork_plugin.uninstall()


def is_ultrawork_installed() -> bool:
    """Check if Ultrawork Mode is installed."""
    return ultrawork_plugin.is_installed
