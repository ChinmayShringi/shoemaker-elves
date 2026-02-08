# Release Guide

This guide explains how to create a new release of gpt-agent-orchestrator.

## Overview

The release process is automated via GitHub Actions and publishes to:
- **PyPI** (Python package)
- **npm** (npm wrapper package)
- **GitHub Releases** (with binaries and checksums)

## Prerequisites

### One-time Setup

1. **PyPI Trusted Publishing**
   - Go to https://pypi.org/manage/account/publishing/
   - Add a new publisher:
     - Owner: `ChinmayShringi`
     - Repository: `Chainsmith`
     - Workflow: `release.yml`
     - Environment: `pypi`
   - No API token needed with trusted publishing!

2. **npm Token**
   - Generate an npm automation token: https://www.npmjs.com/settings/~/tokens
   - Add to GitHub Secrets as `NPM_TOKEN`:
     - Go to repository Settings → Secrets and variables → Actions
     - Create new secret: `NPM_TOKEN`

3. **GitHub Token**
   - Automatically provided by GitHub Actions (no setup needed)

## Release Process

### Step 1: Prepare the Release

1. **Update the version** in `pyproject.toml`:
   ```toml
   [project]
   version = "1.2.3"  # Update to your new version
   ```

2. **Sync npm package version**:
   ```bash
   python scripts/sync_version.py --sync
   ```

   This ensures `packages/npm/package.json` matches `pyproject.toml`.

3. **Update CHANGELOG.md**:
   - Add a new section for your version
   - Follow the [Keep a Changelog](https://keepachangelog.com/) format
   - Include all notable changes since the last release

   Example:
   ```markdown
   ## [1.2.3] - 2026-02-04

   ### Added
   - New feature X
   - Support for Y

   ### Fixed
   - Bug in Z

   ### Changed
   - Improved performance of W
   ```

4. **Verify version consistency**:
   ```bash
   python scripts/sync_version.py --check
   ```

   This must pass before proceeding.

### Step 2: Commit and Tag

1. **Commit your changes**:
   ```bash
   git add pyproject.toml packages/npm/package.json CHANGELOG.md
   git commit -m "Release v1.2.3"
   ```

2. **Create and push the tag**:
   ```bash
   git tag v1.2.3
   git push origin main --tags
   ```

   **Important**: The tag MUST match the version in `pyproject.toml` (with `v` prefix).

### Step 3: Automated Release

Once the tag is pushed, GitHub Actions automatically:

1. **Validates** version consistency across files
2. **Builds** Python package (sdist + wheel)
3. **Publishes** to PyPI
4. **Builds** binaries for all platforms:
   - macOS (Intel + Apple Silicon)
   - Linux (x64)
   - Windows (x64)
5. **Generates** SHA256 checksums for all binaries
6. **Creates** GitHub Release with:
   - Changelog excerpt for this version
   - All binaries and checksums
   - Auto-generated release notes
7. **Publishes** npm package

### Step 4: Verify the Release

After the workflow completes, verify:

1. **PyPI**: https://pypi.org/project/gpt-agent-orchestrator/
   ```bash
   pip install gpt-agent-orchestrator==1.2.3
   chainsmith --version
   ```

2. **npm**: https://www.npmjs.com/package/gpt-agent-orchestrator
   ```bash
   npm install -g gpt-agent-orchestrator@1.2.3
   chainsmith --version
   ```

3. **GitHub Release**: https://github.com/ChinmayShringi/shoemaker-elves/releases
   - Download and test a binary
   - Verify checksums match

## Dry Run Testing

Before a real release, test the workflow without publishing:

1. Go to **Actions** → **Release** → **Run workflow**
2. Set `dry_run` to `true`
3. Click **Run workflow**

This will:
- Run all validation checks
- Build all packages and binaries
- Show what would be published
- **NOT** actually publish anything

## Troubleshooting

### Version Mismatch Error

**Error**: "Tag version doesn't match pyproject.toml version"

**Solution**:
1. Ensure `pyproject.toml` version matches your tag (minus the `v` prefix)
2. Run `python scripts/sync_version.py --sync` to update package.json
3. Run `python scripts/sync_version.py --check` to verify

### PyPI Publishing Failed

**Error**: PyPI trusted publishing authentication failed

**Solution**:
1. Verify PyPI trusted publishing is configured correctly
2. Check repository name, workflow name, and environment name match exactly
3. Ensure the workflow is running from a tagged commit

### npm Publishing Failed

**Error**: npm authentication failed

**Solution**:
1. Verify `NPM_TOKEN` secret is set in repository settings
2. Ensure the token has publish permissions
3. Check token hasn't expired

### Binary Build Failed

**Error**: Binary build failed for a specific platform

**Solution**:
1. Check the build logs for specific errors
2. Verify all dependencies are installable on that platform
3. Test locally with the build scripts:
   ```bash
   # macOS/Linux
   bash scripts/build_binaries.sh

   # Windows
   powershell scripts/build_binaries.ps1
   ```

## Version Sync Script

The `scripts/sync_version.py` script ensures version consistency:

```bash
# Show current versions
python scripts/sync_version.py --show

# Check if versions match (exits 1 if not)
python scripts/sync_version.py --check

# Sync package.json to match pyproject.toml
python scripts/sync_version.py --sync
```

This script is used by:
- CI workflow (checks on every PR)
- Release workflow (validates before publishing)
- Manual release process (sync before committing)

## Release Checklist

- [ ] Version updated in `pyproject.toml`
- [ ] `python scripts/sync_version.py --sync` executed
- [ ] `CHANGELOG.md` updated with new version section
- [ ] `python scripts/sync_version.py --check` passes
- [ ] Changes committed to main branch
- [ ] Tag created and pushed (`v1.2.3` format)
- [ ] GitHub Actions workflow completes successfully
- [ ] PyPI package published and installable
- [ ] npm package published and installable
- [ ] GitHub Release created with binaries
- [ ] Binaries downloadable and executable
- [ ] Checksums verified

## Rolling Back a Release

If a release has critical issues:

1. **PyPI**: You cannot delete releases, but you can yank them:
   ```bash
   # Using twine
   twine yank gpt-agent-orchestrator 1.2.3
   ```

2. **npm**: You can unpublish within 72 hours:
   ```bash
   npm unpublish gpt-agent-orchestrator@1.2.3
   ```

3. **GitHub Release**: Delete the release and tag:
   - Go to Releases → Delete release
   - Delete the tag: `git push --delete origin v1.2.3`

4. **Fix and Re-release**: Create a new version (e.g., 1.2.4) with the fix.

## Support

For issues with the release process:
- Check workflow logs in GitHub Actions
- Review this guide for common issues
- Open an issue: https://github.com/ChinmayShringi/shoemaker-elves/issues
