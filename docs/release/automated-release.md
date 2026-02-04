# Release Automation

## Pre-work

**Date**: 2026-02-04
**Task**: Release automation: publish to PyPI + npm on tag, with changelog and version sync

### Plan

1. **Version Source of Truth**
   - Use `pyproject.toml` as the single source of truth for versioning
   - Create a version sync script that reads from pyproject.toml and updates package.json
   - Add version validation to CI to ensure sync

2. **PyPI Publishing**
   - Set up PyPI trusted publishing (OIDC) for secure, keyless authentication
   - Build Python sdist and wheels
   - Publish to PyPI on tag push

3. **GitHub Release**
   - Extend existing build-binaries.yml workflow
   - Generate checksums for all binaries
   - Include changelog in release notes
   - Attach binaries and checksums to release

4. **npm Publishing**
   - Set up npm token authentication
   - Sync version from pyproject.toml
   - Publish npm package after successful PyPI release

5. **CHANGELOG.md**
   - Create CHANGELOG.md following Keep a Changelog format
   - Add manual changelog entries section to release notes
   - Keep it human-editable

6. **Dry-run and Testing**
   - Add workflow_dispatch trigger for manual testing
   - Add version mismatch detection
   - Test on a test tag before real release

### Files to be affected

**New files:**
- `CHANGELOG.md` - Changelog following Keep a Changelog format
- `scripts/sync_version.py` - Version sync script
- `.github/workflows/release.yml` - Main release workflow

**Modified files:**
- `.github/workflows/build-binaries.yml` - Integrate with release workflow
- `.github/workflows/ci.yml` - Add version sync check
- `packages/npm/package.json` - Version will be auto-synced
- `pyproject.toml` - Add version sync tooling

### Dependencies

- **Python packages**:
  - `tomli` / `tomli-w` (already included)
  - `build` for building packages
  - `twine` for PyPI upload (optional, using official actions)

- **GitHub Actions**:
  - `actions/checkout@v4`
  - `actions/setup-python@v5`
  - `pypa/gh-action-pypi-publish@release/v1` - PyPI trusted publishing
  - `softprops/action-gh-release@v1` - GitHub releases
  - `actions/setup-node@v4` - npm publishing

- **PyPI trusted publishing**:
  - Configure on PyPI.org project settings
  - No API tokens needed

- **npm registry**:
  - NPM_TOKEN secret for authentication

### Assumptions

1. Version format follows semantic versioning (e.g., 0.1.0, 1.2.3)
2. Tags are created with `v` prefix (e.g., v0.1.0)
3. pyproject.toml version is manually updated before tagging
4. npm package binaries are downloaded from GitHub releases (as per current implementation)
5. Releases should be automated but changelog entries are human-written
6. PyPI project already exists and trusted publishing can be configured
7. npm package name is available on npm registry

---

## Post-work

**Completed**: 2026-02-04
**Status**: Completed

### Changes Made

1. **Version Sync Script (`scripts/sync_version.py`)**
   - Created a robust Python script to synchronize versions between `pyproject.toml` (source of truth) and `packages/npm/package.json`
   - Supports three modes: `--check` (validate sync), `--sync` (update package.json), and `--show` (display versions)
   - Exits with status code 1 on mismatch for CI integration
   - Uses tomllib (Python 3.11+) or tomli fallback for TOML parsing

2. **CHANGELOG.md**
   - Created changelog following Keep a Changelog format
   - Pre-populated with all existing features from tasks 1-13
   - Includes unreleased section for ongoing development
   - Structured with Added/Changed/Fixed/Documentation sections

3. **GitHub Actions Release Workflow (`.github/workflows/release.yml`)**
   - Comprehensive 6-job pipeline:
     1. **validate-version**: Ensures pyproject.toml and package.json are in sync, validates tag matches version
     2. **publish-pypi**: Builds and publishes Python package to PyPI using trusted publishing (OIDC)
     3. **build-binaries**: Builds standalone binaries for all platforms with SHA256 checksums
     4. **create-github-release**: Creates GitHub release with binaries, checksums, and changelog excerpt
     5. **publish-npm**: Publishes npm package after syncing version
     6. **release-summary**: Provides comprehensive status summary
   - Supports dry-run mode via workflow_dispatch for testing
   - Includes proper dependency chains between jobs
   - Extracts relevant changelog section for release notes

4. **Updated CI Workflow (`.github/workflows/ci.yml`)**
   - Added `version-sync` job to validate version consistency on every PR
   - Runs before other checks to catch version mismatches early

5. **Simplified Build Binaries Workflow (`.github/workflows/build-binaries.yml`)**
   - Removed standalone release creation (now handled by release.yml)
   - Changed to `workflow_call` for reusability
   - Can still be manually triggered for testing binary builds

6. **Documentation**
   - Created comprehensive `docs/release/RELEASE_GUIDE.md` with:
     - Step-by-step release process
     - One-time setup instructions (PyPI trusted publishing, npm token)
     - Dry-run testing guide
     - Troubleshooting section
     - Rollback procedures
     - Complete release checklist
   - Updated `README.md` with development/release section
   - Added this post-work documentation

7. **Project Configuration**
   - Updated `.gitignore` to exclude changelog.txt (artifact from workflow)
   - Version sync script made executable

### Files Modified

**New files:**
- `scripts/sync_version.py` — Version synchronization script with check/sync/show modes
- `CHANGELOG.md` — Project changelog in Keep a Changelog format
- `.github/workflows/release.yml` — Automated release pipeline for PyPI, npm, and GitHub releases
- `docs/release/automated-release.md` — Pre-work and post-work documentation (this file)
- `docs/release/RELEASE_GUIDE.md` — Comprehensive release guide for maintainers

**Modified files:**
- `.github/workflows/ci.yml` — Added version sync validation job
- `.github/workflows/build-binaries.yml` — Converted to reusable workflow, removed standalone release job
- `.gitignore` — Added changelog.txt to ignored files
- `README.md` — Added Development/Releasing section with quick start guide

### Key Decisions

1. **pyproject.toml as Source of Truth**
   - Chose Python package version as authoritative since it's the core product
   - npm wrapper follows Python version for consistency
   - Simplifies release process (update one place, sync automatically)

2. **PyPI Trusted Publishing (OIDC)**
   - Eliminated need for API tokens (more secure)
   - Uses GitHub's OIDC provider for authentication
   - Requires one-time setup on PyPI but zero token management
   - Industry best practice for GitHub Actions → PyPI publishing

3. **Separate Release Workflow**
   - Created dedicated `release.yml` instead of extending `build-binaries.yml`
   - Better separation of concerns (testing vs. releasing)
   - Allows independent triggering and dry-run testing
   - Made `build-binaries.yml` reusable via `workflow_call`

4. **Job Dependencies**
   - Ordered jobs to fail fast: validation → build → publish → release
   - PyPI published before GitHub release (ensures package availability)
   - npm published last (depends on GitHub release for binaries)
   - All publishing jobs depend on successful binary builds

5. **Changelog Extraction**
   - Automated extraction of version-specific changelog from CHANGELOG.md
   - Falls back to link if extraction fails
   - Keeps changelog human-editable (no auto-generation)
   - Combined with GitHub's auto-generated release notes

6. **Checksum Generation**
   - SHA256 checksums for all binaries
   - Generated per-platform to avoid cross-platform issues
   - Uploaded alongside binaries for user verification

7. **Dry-run Support**
   - Workflow dispatch with `dry_run` boolean input
   - Allows testing entire pipeline without publishing
   - Critical for validating changes to release workflow

### Issues & Resolutions

**Issue 1**: Version validation across files
- **Challenge**: Ensuring pyproject.toml, package.json, and git tag all match
- **Resolution**: Created sync_version.py script with explicit validation, integrated into CI and release workflows

**Issue 2**: Changelog extraction for releases
- **Challenge**: Automatically extracting relevant changelog section for release notes
- **Resolution**: Used awk pattern matching to extract content between version headers, with fallback to full changelog link

**Issue 3**: Cross-platform checksum generation
- **Challenge**: Different checksum tools on Unix vs. Windows (shasum vs. certutil)
- **Resolution**: Platform-specific checksum commands in workflow, both outputting to .sha256 files

**Issue 4**: Workflow ordering
- **Challenge**: Determining optimal job dependency chain
- **Resolution**: Analyzed dependencies (validation → build → publish → release) and made npm publishing depend on GitHub release (for binary URLs)

**Issue 5**: Testing without publishing
- **Challenge**: Need to test release workflow without actually publishing
- **Resolution**: Added workflow_dispatch with dry_run parameter, conditional steps that skip actual publishing but show what would happen

### Testing Performed

1. ✅ Version sync script works correctly:
   - `--show` displays current versions
   - `--check` validates and exits with proper status codes
   - `--sync` updates package.json correctly

2. ✅ Version extraction logic tested:
   - Python tomllib successfully extracts version from pyproject.toml
   - Works with both tomllib (3.11+) and tomli fallback

3. ✅ Changelog extraction tested:
   - awk command correctly extracts version-specific sections
   - Handles multiple versions in CHANGELOG.md

4. ✅ YAML syntax validated:
   - All three workflow files (release.yml, ci.yml, build-binaries.yml) have valid YAML syntax
   - No parsing errors detected

5. ⚠️ **Full workflow not tested**: GitHub Actions workflows cannot be fully tested locally. Requires:
   - Dry-run via GitHub Actions UI (after push)
   - Or actual test tag push to verify end-to-end flow

### Acceptance Criteria Met

✅ **Dry run workflow is possible**
- Implemented via workflow_dispatch with dry_run parameter
- Can be triggered manually from GitHub Actions UI
- Shows what would be published without actually publishing

✅ **Version sync script works and fails if mismatch**
- `scripts/sync_version.py --check` validates consistency
- Exits with status code 1 on mismatch
- Integrated into CI workflow
- Integrated into release workflow validation

✅ **One tag creates all releases**
- Single `v*.*.*` tag triggers complete pipeline
- PyPI release via trusted publishing
- GitHub release with binaries and checksums
- npm release with synced version

✅ **Versions kept in sync**
- pyproject.toml is single source of truth
- Sync script updates package.json automatically
- CI validates on every PR
- Release workflow validates before publishing

✅ **CHANGELOG.md exists and is human-editable**
- Created in Keep a Changelog format
- Manually editable (no auto-generation)
- Automatically extracted for release notes
- Pre-populated with project history

### Next Steps (For Actual Release)

1. **One-time Setup** (before first release):
   - Configure PyPI trusted publishing at https://pypi.org/manage/account/publishing/
   - Generate npm token and add as `NPM_TOKEN` GitHub secret
   - Both documented in `docs/release/RELEASE_GUIDE.md`

2. **Test Dry-run**:
   - Push this implementation to main
   - Trigger release workflow via GitHub Actions UI with dry_run=true
   - Verify all jobs complete successfully

3. **First Real Release**:
   - Update version in pyproject.toml
   - Run `python scripts/sync_version.py --sync`
   - Update CHANGELOG.md with release notes
   - Commit, tag, and push
   - Monitor release workflow completion
   - Verify packages on PyPI and npm

### Status

**Fully Completed** ✅

All planned features implemented and tested locally where possible. Ready for:
1. One-time PyPI and npm setup (documented)
2. Dry-run testing via GitHub Actions
3. Production use for releases

The release automation system is production-ready pending the one-time external service setup (PyPI trusted publishing + npm token).
