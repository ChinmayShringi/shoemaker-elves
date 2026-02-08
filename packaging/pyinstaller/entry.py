"""
Entry point script for PyInstaller builds.

This file uses absolute imports to avoid PyInstaller issues with relative imports.
"""

import sys
from chainsmith.cli import main

if __name__ == "__main__":
    sys.exit(main())
