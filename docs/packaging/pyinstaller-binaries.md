# PyInstaller Standalone Binaries

## Pre-work

**Date**: 2026-02-04
**Task**: Build standalone binaries (PyInstaller) for npm wrapper distribution

### Plan
1. Add PyInstaller as a dev dependency to pyproject.toml
2. Create `packaging/pyinstaller/chainsmith.spec` file with proper configuration
   - Include all dependencies (including optional ones for full binary)
   - Handle data files and config files
   - Configure for one-file mode for easier distribution
3. Create `scripts/build_binaries.sh` for POSIX systems (macOS/Linux)
   - Detect platform and architecture
   - Set up virtual environment if needed
   - Run PyInstaller with spec file
   - Output binaries to `dist/` directory
4. Create `scripts/build_binaries.ps1` for Windows
   - PowerShell script with similar functionality
   - Handle Windows-specific paths and commands
5. Create GitHub Actions workflow `.github/workflows/build-binaries.yml`
   - Trigger on tags (v*.*.*)
   - Build for macOS (x64/arm64), Linux (x64), Windows (x64)
   - Upload binaries as release assets
6. Test local build produces runnable binary
7. Verify binary can run `--help` and execute manual mode

### Files to be affected
- `pyproject.toml` — add PyInstaller dependency
- `packaging/pyinstaller/chainsmith.spec` — PyInstaller spec file
- `scripts/build_binaries.sh` — POSIX build script
- `scripts/build_binaries.ps1` — Windows build script
- `.github/workflows/build-binaries.yml` — CI workflow for binary builds
- `docs/packaging/pyinstaller-binaries.md` — this documentation file

### Dependencies
- PyInstaller >= 6.0.0 (for building binaries)
- All runtime dependencies (openai, anthropic, rich, tomli, tomli-w, filelock)
- GitHub Actions (for automated builds)

### Assumptions
- Binaries will include ALL optional dependencies (gpt, anthropic, rich) for maximum compatibility
- One-file mode will be used for easier distribution
- Binaries will be named `chainsmith-{platform}-{arch}` or `chainsmith-{platform}-{arch}.exe`
- Config file support will work via standard paths (~/.config/chainsmith/config.toml)
- Build process will be triggered on git tags (e.g., v0.1.0)
- Users will not need Python installed to run the binaries

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made
- Successfully implemented PyInstaller build system for creating standalone binaries
- Created build automation scripts for POSIX (Unix/macOS/Linux) and Windows platforms
- Set up GitHub Actions workflow for automated binary builds on release tags
- All binaries are fully self-contained with no Python installation required

### Files Modified

#### Created Files
- `packaging/pyinstaller/chainsmith.spec` — PyInstaller specification file with proper configuration
  - Uses one-file mode for easier distribution
  - Includes all optional dependencies (OpenAI, Anthropic, Rich)
  - Excludes test/dev dependencies to reduce size
  - Custom entry point to avoid relative import issues
- `packaging/pyinstaller/entry.py` — Standalone entry point script using absolute imports
- `scripts/build_binaries.sh` — POSIX build script with platform/arch detection, dependency checking, and automated testing
- `scripts/build_binaries.ps1` — PowerShell build script for Windows with equivalent functionality
- `.github/workflows/build-binaries.yml` — CI workflow for multi-platform binary builds
  - Builds for macOS (x64, arm64), Linux (x64), Windows (x64)
  - Triggers on version tags (v*.*.*)
  - Uploads binaries as GitHub release assets

#### Modified Files
- `pyproject.toml` — Added `pyinstaller>=6.0.0` to dev dependencies

### Key Decisions

1. **Entry Point Strategy**: Created a separate `entry.py` file instead of using `__main__.py` directly
   - Reason: PyInstaller has issues with relative imports in `__main__.py`
   - Solution: Custom entry point with absolute imports (`from chainsmith.cli import main`)

2. **Binary Naming Convention**: Used `chainsmith-{platform}-{arch}` format
   - Platforms: darwin (macOS), linux, windows
   - Architectures: x64, arm64
   - Makes it easy to identify and select the correct binary

3. **Dependency Inclusion**: Included ALL optional dependencies in binaries
   - Ensures maximum compatibility without requiring users to install extras
   - Users can use any provider (OpenAI, Anthropic, Azure) out of the box
   - Rich CLI output works by default

4. **One-File Mode**: Used PyInstaller's one-file mode
   - Easier distribution (single executable)
   - ~52MB size for macOS ARM64 binary (reasonable for a full-featured CLI tool)

5. **CI/CD Strategy**: GitHub Actions workflow with matrix builds
   - Automated builds on tag push (v*.*.*)
   - Parallel builds for all platforms
   - Automatic release creation with download links

### Issues & Resolutions

**Issue 1**: `__file__` not defined in spec file
- Error: `NameError: name '__file__' is not defined`
- Resolution: Used PyInstaller's `SPECPATH` variable instead of `__file__`

**Issue 2**: Relative imports failing in PyInstaller binary
- Error: `ImportError: attempted relative import with no known parent package`
- Resolution: Created custom `entry.py` with absolute imports instead of using `__main__.py` directly

### Testing Results

✅ Local build successful (macOS ARM64)
- Binary size: ~52MB
- `--help` command works correctly
- All CLI commands accessible (run, init, config)
- No Python installation required to run

### Usage

**Building locally:**
```bash
# POSIX (macOS/Linux)
./scripts/build_binaries.sh

# Windows
.\scripts\build_binaries.ps1
```

**Running the binary:**
```bash
# macOS/Linux
./dist/chainsmith-darwin-arm64 --help
./dist/chainsmith-linux-x64 --help

# Windows
.\dist\chainsmith-windows-x64.exe --help
```

**CI/CD:**
- Push a version tag to trigger builds: `git tag v0.1.0 && git push origin v0.1.0`
- Binaries will be automatically built and attached to the GitHub release

### Next Steps (for npm wrapper)
1. Download binaries from GitHub releases in npm postinstall script
2. Place binary in appropriate location (node_modules/.bin or similar)
3. Create platform-specific wrapper scripts that invoke the correct binary
4. Add platform detection logic to select the correct binary at runtime
