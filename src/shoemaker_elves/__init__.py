"""
Shoemaker Elves
======================

A standalone CLI tool that breaks down large projects into atomic tasks
and runs each task through an AI coding agent automatically using a
hook-driven chain.
"""

__version__ = "0.1.0"

from .cli import main
from .state import State

__all__ = ["main", "State", "__version__"]
