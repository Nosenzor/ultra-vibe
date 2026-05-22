"""
Integration with Mistral Vibe.

This module provides the main integration point for Ultrawork Mode
with Mistral Vibe. It patches Vibe's initialization to add Ultrawork
middleware and register Ultrawork agents.

Usage:
    # In your code before starting Vibe
    import vibe.core.vibe_integration
    vibe.core.vibe_integration.enable_ultrawork()
    
    # Then run vibe as normal
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    try:
        from vibe.core.agent_loop import AgentLoop
        from vibe.core.middleware import MiddlewarePipeline
    except ImportError:
        # Vibe not installed, use dummy types
        class AgentLoop:
            _setup_middleware: Any = None
            middleware_pipeline: Any = None
            config: Any = None
        class MiddlewarePipeline:
            pass

logger = logging.getLogger(__name__)

# Track if ultrawork is enabled
_ultrawork_enabled: bool = False
_original_setup_middleware: Optional[Any] = None


def enable_ultrawork() -> None:
    """
    Enable Ultrawork Mode in Vibe.
    
    This patches Vibe's AgentLoop._setup_middleware to add Ultrawork middleware.
    It also installs the Ultrawork agent definitions.
    
    Call this before creating any AgentLoop instances.
    """
    global _ultrawork_enabled, _original_setup_middleware
    
    if _ultrawork_enabled:
        logger.debug("Ultrawork already enabled")
        return
    
    logger.info("Enabling Ultrawork Mode...")
    
    # Patch AgentLoop._setup_middleware
    try:
        from vibe.core.agent_loop import AgentLoop
        
        if _original_setup_middleware is None:
            _original_setup_middleware = AgentLoop._setup_middleware
        
        def patched_setup_middleware(self: AgentLoop) -> None:
            """Patched _setup_middleware that adds Ultrawork middleware."""
            # Call original
            _original_setup_middleware(self)
            
            # Add Ultrawork middleware
            _add_ultrawork_middleware(self.middleware_pipeline, self.config)
        
        AgentLoop._setup_middleware = patched_setup_middleware
        logger.info("Patched AgentLoop._setup_middleware for Ultrawork")
        
    except ImportError as e:
        logger.warning(f"Could not patch AgentLoop: {e}")
    except Exception as e:
        logger.error(f"Failed to patch AgentLoop: {e}")
        raise
    
    # Install Ultrawork agents (if they exist)
    _install_ultrawork_agents()
    
    _ultrawork_enabled = True
    logger.info("Ultrawork Mode enabled")


def disable_ultrawork() -> None:
    """
    Disable Ultrawork Mode.
    
    Restores the original _setup_middleware method.
    """
    global _ultrawork_enabled, _original_setup_middleware
    
    if not _ultrawork_enabled:
        return
    
    try:
        from vibe.core.agent_loop import AgentLoop
        
        if _original_setup_middleware is not None:
            AgentLoop._setup_middleware = _original_setup_middleware
            logger.info("Restored original _setup_middleware")
    except ImportError:
        pass
    
    _ultrawork_enabled = False
    logger.info("Ultrawork Mode disabled")


def is_ultrawork_enabled() -> bool:
    """Check if Ultrawork Mode is enabled."""
    return _ultrawork_enabled


def _add_ultrawork_middleware(
    pipeline: "MiddlewarePipeline",
    config: Any,
) -> None:
    """Add Ultrawork middleware to the pipeline."""
    from ultra_vibe.core.middleware.ultrawork import (
        UltraworkMiddleware,
        UltraworkModelMiddleware,
        TaskDelegationMiddleware,
    )
    
    # Create and add middleware
    ultrawork_mw = UltraworkMiddleware(config)
    model_mw = UltraworkModelMiddleware(config)
    delegation_mw = TaskDelegationMiddleware(config)
    
    pipeline.add(ultrawork_mw)
    pipeline.add(model_mw)
    pipeline.add(delegation_mw)
    
    logger.info("Added Ultrawork middleware to pipeline")


def _install_ultrawork_agents() -> int:
    """
    Install Ultrawork agent definitions to Vibe's agents directory.
    
    Copies agent TOML files from our package to ~/.vibe/agents/
    
    Returns:
        Number of agents installed
    """
    import shutil
    from pathlib import Path
    
    # Get our agents directory
    our_agents_dir = Path(__file__).parent.parent.parent / "agents"
    if not our_agents_dir.exists():
        logger.warning(f"Ultrawork agents directory not found: {our_agents_dir}")
        return 0
    
    # Get Vibe's agents directory
    vibe_agents_dir = Path.home() / ".vibe" / "agents"
    vibe_agents_dir.mkdir(parents=True, exist_ok=True)
    
    # Copy agent files
    installed = 0
    for agent_file in our_agents_dir.glob("*.toml"):
        target = vibe_agents_dir / agent_file.name
        
        # Skip if already exists and is different
        if target.exists():
            # Check if it's our version
            our_content = agent_file.read_text()
            their_content = target.read_text()
            if "Ultra Vibe" in our_content and "Ultra Vibe" not in their_content:
                # Backup existing
                backup = target.with_suffix('.toml.bak')
                shutil.copy2(target, backup)
                logger.info(f"Backed up existing agent: {target.name}")
            else:
                continue
        
        shutil.copy2(agent_file, target)
        logger.info(f"Installed Ultrawork agent: {agent_file.name}")
        installed += 1
    
    return installed


def install_agent_configs() -> int:
    """
    Manually install agent configurations.
    
    Use this if automatic installation doesn't work.
    
    Returns:
        Number of agents installed
    """
    return _install_ultrawork_agents()


class UltraworkCLI:
    """
    CLI integration for Ultrawork Mode.
    
    Provides command-line flags for enabling Ultrawork Mode.
    """
    
    @staticmethod
    def add_arguments(parser: Any) -> None:
        """Add Ultrawork arguments to a parser."""
        parser.add_argument(
            '--ultrawork',
            '-U',
            action='store_true',
            help='Enable Ultrawork Mode for autonomous multi-agent execution',
        )
        parser.add_argument(
            '--ulw',
            action='store_true',
            dest='ultrawork',
            help='Alias for --ultrawork',
        )
        parser.add_argument(
            '--install-ultrawork-agents',
            action='store_true',
            help='Install Ultrawork agent configurations and exit',
        )
    
    @staticmethod
    def handle_args(args: Any) -> bool:
        """
        Handle Ultrawork CLI arguments.
        
        Args:
            args: Parsed arguments
            
        Returns:
            True if Vibe should continue, False if it should exit
        """
        if getattr(args, 'install_ultrawork_agents', False):
            count = install_agent_configs()
            print(f"Installed {count} Ultrawork agent configurations")
            return False
        
        if getattr(args, 'ultrawork', False) or getattr(args, 'ulw', False):
            enable_ultrawork()
        
        return True


# Auto-enable if VIBE_ULTRAWORK environment variable is set
import os
if os.environ.get('VIBE_ULTRAWORK', '').lower() in ('1', 'true', 'yes'):
    enable_ultrawork()


# Convenience exports
__all__ = [
    "enable_ultrawork",
    "disable_ultrawork",
    "is_ultrawork_enabled",
    "install_agent_configs",
    "UltraworkCLI",
    "cli_main",
]


def cli_main():
    """
    CLI entry point for ultra-vibe command.
    
    This handles both Ultra Vibe CLI commands and passing arguments to Vibe.
    """
    import argparse
    import os
    import sys
    from pathlib import Path
    
    # Create parser
    parser = argparse.ArgumentParser(
        prog="ultra-vibe",
        description="Ultrawork Mode for Mistral Vibe",
    )
    
    # Add Ultrawork-specific arguments
    parser.add_argument(
        '--ultrawork',
        '-U',
        action='store_true',
        help='Enable Ultrawork Mode for autonomous multi-agent execution',
    )
    parser.add_argument(
        '--ulw',
        action='store_true',
        dest='ultrawork',
        help='Alias for --ultrawork',
    )
    parser.add_argument(
        '--install-agents',
        action='store_true',
        help='Install Ultrawork agent configurations and exit',
    )
    parser.add_argument(
        '--version',
        '-v',
        action='version',
        version=f"ultra-vibe 0.1.0",
    )
    parser.add_argument(
        '--verbose',
        '-V',
        action='store_true',
        help='Enable verbose logging',
    )
    
    # Use parse_known_args to handle both our flags and Vibe arguments
    args, remaining_args = parser.parse_known_args()
    
    # Handle install-agents flag
    if args.install_agents:
        count = install_agent_configs()
        print(f"Installed {count} Ultrawork agent configurations to ~/.vibe/agents/")
        sys.exit(0)
    
    # Enable Ultrawork if requested
    ultrawork_was_enabled = False
    if args.ultrawork:
        enable_ultrawork()
        print("Ultrawork Mode enabled ✓")
        os.environ['VIBE_ULTRAWORK'] = '1'
        ultrawork_was_enabled = True
    
    # Check if remaining args look like a Vibe command or an Ultra Vibe CLI command
    if remaining_args:
        # Check if first arg is an Ultra Vibe CLI command
        cli_commands = ['install', 'list-agents', 'show-agent', 'test', 'test-keyword-detection']
        if remaining_args[0] in cli_commands:
            # Import and run the CLI command
            from ultra_vibe.cli import main as ultra_vibe_cli_main
            sys.argv = ['ultra-vibe'] + remaining_args
            ultra_vibe_cli_main()
            return
        
        # Check if prompt contains ultrawork keywords
        prompt = ' '.join(remaining_args)
        from ultra_vibe.core.hooks.keyword_detector import detect_ultrawork
        if detect_ultrawork(prompt):
            if not ultrawork_was_enabled:
                enable_ultrawork()
                print("Ultrawork Mode auto-enabled (keyword detected) ✓")
                os.environ['VIBE_ULTRAWORK'] = '1'
                ultrawork_was_enabled = True
    
    # Check if Vibe is available
    try:
        import vibe
    except ImportError:
        print("Error: Mistral Vibe is not installed or not in PATH")
        print("Please install Vibe first: pip install mistral-vibe")
        sys.exit(1)
    
    # Launch Vibe with remaining arguments
    from vibe.cli.entrypoint import main as vibe_main
    
    sys.argv = ['vibe'] + remaining_args
    
    try:
        vibe_main()
    except SystemExit as e:
        sys.exit(e.code)
