# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for building chainsmith standalone binary.

This creates a one-file executable that includes all dependencies.
"""

import sys
import os
from pathlib import Path

# Get the project root directory
# When PyInstaller runs, SPECPATH is the directory containing this spec file
spec_dir = Path(SPECPATH)
project_root = spec_dir.parent.parent
src_path = project_root / "src"

block_cipher = None

# Analysis: collect all Python files and dependencies
a = Analysis(
    [str(spec_dir / "entry.py")],  # Use our custom entry point
    pathex=[str(src_path)],
    binaries=[],
    datas=[
        # Include README if needed for --help or similar
        (str(project_root / "README.md"), "."),
    ],
    hiddenimports=[
        # Explicitly include all optional dependencies
        "openai",
        "anthropic",
        "rich",
        "tomli",
        "tomli_w",
        "filelock",
        # Include all planner adapters
        "chainsmith.planners.openai_adapter",
        "chainsmith.planners.anthropic_adapter",
        "chainsmith.planners.azure_openai_adapter",
        # Standard library modules that might not be auto-detected
        "argparse",
        "json",
        "subprocess",
        "pathlib",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Exclude test and dev dependencies to reduce size
        "pytest",
        "pytest_cov",
        "pytest_asyncio",
        "ruff",
        "mypy",
        "unittest",
        "test",
        "tests",
        # Exclude unnecessary standard library modules
        "tkinter",
        "matplotlib",
        "numpy",
        "pandas",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

# PYZ: create a compressed archive of pure Python modules
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

# EXE: create the executable
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="chainsmith",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # CLI application
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Set icon if available (optional)
    # icon='icon.ico',
)
