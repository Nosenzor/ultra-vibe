"""
CLI for Ultra Vibe.

Provides command-line interface for managing Ultrawork Mode.
"""

import argparse
import logging
import sys
from pathlib import Path

from ultra_vibe import __version__

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False):
    """Configure logging."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )


def install_agents(agents_dir: Path, output_dir: Path) -> int:
    """
    Install agent configurations to Vibe's agents directory.
    
    Args:
        agents_dir: Directory containing agent TOML files
        output_dir: Vibe's agents directory
        
    Returns:
        Number of agents installed
    """
    from shutil import copy2
    
    output_dir.mkdir(parents=True, exist_ok=True)
    installed = 0
    
    for agent_file in agents_dir.glob("*.toml"):
        target = output_dir / agent_file.name
        copy2(agent_file, target)
        logger.info(f"Installed agent: {agent_file.name}")
        installed += 1
    
    return installed


def list_agents() -> None:
    """List available specialist agents."""
    from ultra_vibe import AGENT_DEFINITIONS
    
    print("\nAvailable Specialist Agents:")
    print("=" * 50)
    
    for name, agent in AGENT_DEFINITIONS.items():
        print(f"\n{name.upper()}")
        print(f"  Description: {agent.description}")
        print(f"  Role: {agent.role}")
        print(f"  Specialty: {agent.specialty}")
        print(f"  Default Model: {agent.default_model or 'N/A'}")
        print(f"  Default Variant: {agent.default_variant}")
    
    print(f"\nTotal: {len(AGENT_DEFINITIONS)} agents")


def show_agent(name: str) -> None:
    """Show details for a specific agent."""
    from ultra_vibe import get_agent_definition
    
    agent = get_agent_definition(name)
    if not agent:
        print(f"Agent '{name}' not found.")
        sys.exit(1)
    
    print(f"\n{agent.name.upper()}")
    print("=" * 50)
    print(f"Description: {agent.description}")
    print(f"Role: {agent.role}")
    print(f"Specialty: {agent.specialty}")
    print(f"Default Model: {agent.default_model or 'N/A'}")
    print(f"Default Variant: {agent.default_variant}")
    print(f"\nEnabled Tools: {', '.join(agent.enabled_tools) if agent.enabled_tools else 'All'}")
    print(f"Disabled Tools: {', '.join(agent.disabled_tools) if agent.disabled_tools else 'None'}")
    print(f"\nCapabilities:")
    for cap in agent.capabilities:
        print(f"  - {cap}")


def test_keyword_detection() -> None:
    """Test keyword detection."""
    from ultra_vibe import detect_ultrawork
    
    test_cases = [
        ("use ultrawork mode", True),
        ("ulw please", True),
        ("hpp ulw", True),
        ("normal prompt", False),
        ("what is the weather", False),
    ]
    
    print("\nKeyword Detection Tests:")
    print("=" * 50)
    
    all_passed = True
    for message, expected in test_cases:
        result = detect_ultrawork(message)
        status = "✓" if result == expected else "✗"
        print(f"{status} '{message}' -> {result} (expected {expected})")
        if result != expected:
            all_passed = False
    
    if all_passed:
        print("\nAll tests passed!")
    else:
        print("\nSome tests failed!")
        sys.exit(1)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        prog="ultra-vibe",
        description="Ultrawork Mode for Mistral Vibe",
    )
    parser.add_argument(
        "--version",
        "-v",
        action="version",
        version=f"ultra-vibe {__version__}",
    )
    parser.add_argument(
        "--verbose",
        "-V",
        action="store_true",
        help="Enable verbose logging",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Install command
    install_parser = subparsers.add_parser(
        "install",
        help="Install Ultrawork Mode",
    )
    install_parser.add_argument(
        "--agents-dir",
        type=Path,
        default=Path(__file__).parent.parent / "agents",
        help="Directory containing agent TOML files",
    )
    install_parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home() / ".vibe" / "agents",
        help="Vibe's agents directory",
    )
    
    # List agents command
    subparsers.add_parser(
        "list-agents",
        help="List available specialist agents",
    )
    
    # Show agent command
    show_parser = subparsers.add_parser(
        "show-agent",
        help="Show details for a specific agent",
    )
    show_parser.add_argument(
        "name",
        help="Agent name (sisyphus, hephaestus, oracle, librarian, explore)",
    )
    
    # Test command
    subparsers.add_parser(
        "test",
        help="Run tests",
    )
    subparsers.add_parser(
        "test-keyword-detection",
        help="Test keyword detection",
    )
    
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose)
    
    if args.command is None:
        parser.print_help()
        return
    
    if args.command == "install":
        count = install_agents(args.agents_dir, args.output_dir)
        print(f"\nInstalled {count} agent configurations to {args.output_dir}")
    
    elif args.command == "list-agents":
        list_agents()
    
    elif args.command == "show-agent":
        show_agent(args.name)
    
    elif args.command == "test":
        import pytest
        sys.exit(pytest.main(["-v", "tests"]))
    
    elif args.command == "test-keyword-detection":
        test_keyword_detection()
    
    else:
        parser.print_help()


def ultraworks_main():
    """
    Entry point for ultraworks command.
    
    This function is called when users run 'ultraworks' command.
    It enables Ultrawork Mode and runs Vibe programmatically.
    """
    import sys
    import os
    
    # Set environment variable so Vibe knows ultrawork is enabled
    os.environ['VIBE_ULTRAWORK'] = '1'
    
    # Enable ultrawork mode - this patches Vibe's internals
    try:
        from ultra_vibe.core.vibe_integration import enable_ultrawork
        enable_ultrawork()
    except Exception as e:
        # If patching fails, just continue - ultrawork will be enabled via env var
        pass
    
    # Import and run Vibe's entrypoint
    try:
        from vibe.cli.entrypoint import main as vibe_main
        
        # Modify sys.argv to replace 'ultraworks' with 'vibe'
        if len(sys.argv) > 1:
            sys.argv = ['vibe'] + sys.argv[1:]
        else:
            sys.argv = ['vibe', '--help']
        
        vibe_main()
        
    except ImportError as e:
        print("Error: Mistral Vibe is not installed.")
        print("Please install it first: pip install mistral-vibe")
        sys.exit(1)
    except Exception as e:
        print(f"Error running ultraworks: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
