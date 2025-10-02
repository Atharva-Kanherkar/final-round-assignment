"""Pytest configuration and fixtures."""
import pytest
import sys
from pathlib import Path

# Add src to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Import all fixtures to make them available
from tests.fixtures import *
