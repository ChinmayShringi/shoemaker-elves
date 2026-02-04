#!/usr/bin/env python3
"""
GPT Agent Orchestrator - Legacy Entry Point
============================================

This is a backward-compatibility shim for the old CLI interface.
For new installations, use `gpt-orch` instead.

Usage:
  python3 orchestrator.py <project_dir> [options]

This script imports and runs the main CLI from the gpt_agent_orchestrator package.
"""

import sys

try:
    from gpt_agent_orchestrator.cli import main
except ImportError:
    print("Error: gpt_agent_orchestrator package not found.")
    print("Install it with: pip install -e .")
    sys.exit(1)

if __name__ == "__main__":
    main()
