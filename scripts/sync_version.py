#!/usr/bin/env python3
"""
Version synchronization script for shoemaker-elves.

This script ensures version consistency between pyproject.toml (source of truth)
and package.json (npm wrapper). It can:
- Check if versions are in sync (--check)
- Update package.json to match pyproject.toml (--sync)
- Display current versions (--show)

Usage:
    python scripts/sync_version.py --check  # Exit 1 if mismatch
    python scripts/sync_version.py --sync   # Update package.json
    python scripts/sync_version.py --show   # Display versions
"""

import json
import sys
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # type: ignore

try:
    import tomli_w
except ImportError:
    tomli_w = None  # type: ignore


def get_project_root() -> Path:
    """Get the project root directory."""
    script_path = Path(__file__).resolve()
    return script_path.parent.parent


def read_pyproject_version() -> str:
    """Read version from pyproject.toml."""
    pyproject_path = get_project_root() / "pyproject.toml"

    if not pyproject_path.exists():
        print(f"Error: pyproject.toml not found at {pyproject_path}", file=sys.stderr)
        sys.exit(1)

    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)

    version = data.get("project", {}).get("version")
    if not version:
        print("Error: version not found in pyproject.toml", file=sys.stderr)
        sys.exit(1)

    return version


def read_package_json_version() -> str:
    """Read version from package.json."""
    package_json_path = get_project_root() / "packages" / "npm" / "package.json"

    if not package_json_path.exists():
        print(f"Error: package.json not found at {package_json_path}", file=sys.stderr)
        sys.exit(1)

    with open(package_json_path, encoding="utf-8") as f:
        data = json.load(f)

    version = data.get("version")
    if not version:
        print("Error: version not found in package.json", file=sys.stderr)
        sys.exit(1)

    return version


def update_package_json_version(new_version: str) -> None:
    """Update version in package.json."""
    package_json_path = get_project_root() / "packages" / "npm" / "package.json"

    with open(package_json_path, encoding="utf-8") as f:
        data = json.load(f)

    old_version = data.get("version", "unknown")
    data["version"] = new_version

    # Write with pretty formatting (2 spaces, newline at end)
    with open(package_json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write("\n")  # Ensure newline at end of file

    print(f"✓ Updated package.json: {old_version} → {new_version}")


def check_versions() -> bool:
    """Check if versions are in sync. Returns True if synced, False otherwise."""
    pyproject_version = read_pyproject_version()
    package_json_version = read_package_json_version()

    if pyproject_version == package_json_version:
        print(f"✓ Versions are in sync: {pyproject_version}")
        return True
    else:
        print("✗ Version mismatch detected:", file=sys.stderr)
        print(f"  pyproject.toml:  {pyproject_version}", file=sys.stderr)
        print(f"  package.json:    {package_json_version}", file=sys.stderr)
        return False


def show_versions() -> None:
    """Display current versions."""
    pyproject_version = read_pyproject_version()
    package_json_version = read_package_json_version()

    print("Current versions:")
    print(f"  pyproject.toml:  {pyproject_version}")
    print(f"  package.json:    {package_json_version}")

    if pyproject_version != package_json_version:
        print("\n⚠️  Versions are out of sync!")


def sync_versions() -> None:
    """Sync package.json version to match pyproject.toml."""
    pyproject_version = read_pyproject_version()
    package_json_version = read_package_json_version()

    if pyproject_version == package_json_version:
        print(f"✓ Already in sync: {pyproject_version}")
        return

    print(f"Syncing versions: {package_json_version} → {pyproject_version}")
    update_package_json_version(pyproject_version)


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Synchronize version between pyproject.toml and package.json"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Check if versions are in sync (exit 1 if not)",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Update package.json to match pyproject.toml",
    )
    parser.add_argument(
        "--show",
        action="store_true",
        help="Show current versions",
    )

    args = parser.parse_args()

    # Default to --show if no arguments provided
    if not any([args.check, args.sync, args.show]):
        args.show = True

    try:
        if args.check:
            if not check_versions():
                sys.exit(1)
        elif args.sync:
            sync_versions()
        elif args.show:
            show_versions()
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
