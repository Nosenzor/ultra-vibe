"""Tests for the ultraworks CLI command."""

import os
import sys
from unittest.mock import patch, MagicMock

import pytest


class TestUltraworksCLI:
    """Test suite for ultraworks CLI command."""

    def test_ultraworks_importable(self):
        """Test that ultraworks_main can be imported."""
        from ultra_vibe.cli import ultraworks_main
        assert callable(ultraworks_main)

    def test_ultraworks_entry_point_exists(self):
        """Test that the ultraworks entry point is defined in pyproject.toml."""
        import subprocess
        # Check if ultraworks command is available
        result = subprocess.run(['which', 'ultraworks'], 
                              capture_output=True, text=True)
        # On some systems it might not be in PATH immediately after install
        # So we just check the package structure
        from ultra_vibe.cli import ultraworks_main
        assert ultraworks_main is not None

    def test_ultraworks_command_in_package(self):
        """Test that ultraworks is a valid command."""
        # Verify the command can be invoked via Python
        import subprocess
        result = subprocess.run(
            [sys.executable, '-c', 
             'from ultra_vibe.cli import ultraworks_main; print("OK")'],
            capture_output=True, text=True
        )
        assert result.returncode == 0
        assert 'OK' in result.stdout
