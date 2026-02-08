"""
GPT Agent Orchestrator
======================

A standalone CLI tool that uses GPT as an orchestrator to break down large
projects into tasks, then runs each task through an AI coding agent
automatically using a hook-driven chain.
"""

__version__ = "0.1.0"

from .cli import main
from .state import State

__all__ = ["main", "State", "__version__"]
