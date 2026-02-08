#!/usr/bin/env python3
"""
Shoemaker Elves - Legacy Entry Point
============================================

This is a backward-compatibility shim for the old CLI interface.
For new installations, use `shoemaker-elves` instead.

Usage:
  python3 orchestrator.py <project_dir> [options]

This script imports and runs the main CLI from the shoemaker-elves package.
"""

import sys

try:
    from shoemaker_elves.cli import main
except ImportError:
    print("Error: shoemaker-elves package not found.")
    print("Install it with: pip install -e .")
    sys.exit(1)

if __name__ == "__main__":
    main()
