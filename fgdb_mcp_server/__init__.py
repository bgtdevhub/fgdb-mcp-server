"""FGDB MCP Server package."""

# Import main function from the root-level module for script entry point
import sys
from pathlib import Path

# Add parent directory to path to import fgdb_toolserver
parent_dir = Path(__file__).parent.parent
if str(parent_dir) not in sys.path:
    sys.path.insert(0, str(parent_dir))

from fgdb_toolserver import main

__all__ = ['main']

