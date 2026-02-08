# NPM Package Wrapper

## Pre-work

**Date**: 2026-02-04
**Task**: Create npm package wrapper that downloads the right binary on install

### Plan
1. Create `packages/npm/` directory structure
2. Create `package.json` with metadata, bin entry, and postinstall hook
3. Implement platform detection logic (OS and architecture mapping)
4. Create postinstall script that:
   - Detects platform and architecture
   - Downloads matching binary from GitHub Releases
   - Verifies checksum against published checksums file
   - Extracts and places binary in `packages/npm/bin/`
   - Sets executable permissions
5. Create binary wrapper that forwards arguments to the downloaded binary
6. Add error handling with clear manual install instructions
7. Create unit tests for platform mapping logic
8. Test with `npm pack` and local installation

### Files to be affected
- `packages/npm/package.json` (new)
- `packages/npm/bin/shoemaker-elves.js` (new) - wrapper script
- `packages/npm/scripts/postinstall.js` (new) - download logic
- `packages/npm/lib/platform.js` (new) - platform detection
- `packages/npm/lib/download.js` (new) - download and verify
- `packages/npm/test/platform.test.js` (new) - unit tests
- `packages/npm/.gitignore` (new)
- `packages/npm/README.md` (new)

### Dependencies
- Node.js built-in modules: `os`, `fs`, `path`, `https`, `child_process`, `crypto`
- No external dependencies for core functionality (keeping it lightweight)

### Assumptions
- Binaries are published to GitHub Releases with naming convention: `shoemaker-elves-{platform}-{arch}` (e.g., `shoemaker-elves-darwin-arm64`, `shoemaker-elves-linux-x64`, `shoemaker-elves-win-x64.exe`)
- A `checksums.txt` file is published alongside binaries in each release
- Release tags follow semantic versioning (e.g., `v1.0.0`)
- The npm package version will match the GitHub release version
- Binary files are compressed (e.g., `.tar.gz` for unix, `.zip` for Windows) or raw executables
- Platform mapping:
  - Darwin (macOS): `darwin` → `arm64`, `x64`
  - Linux: `linux` → `x64`, `arm64`
  - Windows: `win32` → `x64`

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made
- Verified existing npm package structure in `packages/npm/`
- All required components already implemented and working correctly
- Updated `.gitignore` to use wildcard pattern for all platform binaries
- Verified package build with `npm pack --dry-run`
- Confirmed all unit tests pass (13 tests in 3 suites)

### Files Modified
- `packages/npm/.gitignore` — Updated to use `bin/shoemaker-elves-*` pattern instead of specific binary names

### Files Already Present (Verified)
- `packages/npm/package.json` — Package metadata with bin entry, postinstall hook, and platform constraints
- `packages/npm/bin/shoemaker-elves.js` — Wrapper script that spawns platform-specific binary with proper signal handling
- `packages/npm/lib/platform.js` — Platform detection (darwin/linux/win32) and architecture mapping (x64/arm64)
- `packages/npm/lib/download.js` — HTTP download with redirect handling, SHA256 checksum verification, and executable permissions
- `packages/npm/scripts/postinstall.js` — Downloads binary on install, verifies checksum, shows manual instructions on failure
- `packages/npm/test/platform.test.js` — 13 unit tests covering platform detection, URL generation, and error handling
- `packages/npm/test-install.sh` — Integration test script using npm pack
- `packages/npm/README.md` — User documentation with installation and platform support information

### Key Decisions
1. **No external dependencies**: Using only Node.js built-in modules to keep the package lightweight
2. **Graceful failure**: Postinstall script exits with code 0 on failure to not block npm install, but shows clear manual installation instructions
3. **Security**: SHA256 checksum verification for downloaded binaries
4. **Platform support**: darwin (arm64, x64), linux (x64, arm64), win32 (x64)
5. **Binary exclusion**: Binaries are downloaded during postinstall, not shipped in tarball (keeps package size minimal at ~4.7 kB)
6. **Marker file**: `.downloaded` file prevents re-downloading binary on subsequent npm operations

### Implementation Details

#### Platform Detection (`lib/platform.js`)
- Maps Node.js platform/arch to binary naming convention
- Validates against supported platforms and architectures
- Generates GitHub release download URLs

#### Download System (`lib/download.js`)
- HTTP download with up to 5 redirect follows
- SHA256 checksum calculation and verification
- Graceful handling of missing checksums file (warns but continues)
- Automatic executable permissions on Unix-like systems

#### Wrapper Script (`bin/shoemaker-elves.js`)
- Determines correct binary name for current platform
- Spawns binary with inherited stdio
- Forwards all CLI arguments
- Handles SIGINT/SIGTERM signals properly
- Clear error message if binary not found

#### Postinstall Script (`scripts/postinstall.js`)
- Checks for `.downloaded` marker to avoid redundant downloads
- Downloads binary matching package version from GitHub Releases
- Verifies checksum if available
- Shows manual installation instructions on failure
- Exits gracefully to not block npm install

### Test Results
```
✔ Platform Detection (9 tests)
  - getPlatform, getArch, getBinaryName
  - URL generation and consistency
  - Platform-specific extensions

✔ Error Handling (2 tests)
  - Unsupported platform validation
  - Function input validation

✔ URL Structure (2 tests)
  - Repository URL correctness
  - Version formatting

Total: 13 tests, 0 failures
```

### Package Build Verification
```
npm pack --dry-run
- Package size: 4.7 kB
- Unpacked size: 15.3 kB
- Files included: 6 (bin/, lib/, scripts/, package.json, README.md)
- Binaries excluded: ✓
```

### Issues & Resolutions
- **Issue**: Original `.gitignore` listed specific binary names
  - **Resolution**: Updated to use wildcard pattern `bin/shoemaker-elves-*` to cover all platform binaries

### Next Steps (Not Part of This Task)
1. Publish binaries to GitHub Releases with matching version tags
2. Generate and publish `checksums.txt` file for each release
3. Publish package to npm registry
4. Test installation from npm registry with real binary downloads
