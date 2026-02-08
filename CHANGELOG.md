# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Release automation with PyPI trusted publishing and npm releases
- Version synchronization script between Python and npm packages
- CHANGELOG.md for tracking project changes

## [0.1.0] - Initial Release

### Added
- Package-ready repository structure with proper Python packaging
- Robust configuration system with interactive `init` command
- Provider-agnostic planner adapter interface
- Multi-provider support: OpenAI, Anthropic (Claude), Azure OpenAI, DeepSeek
- Plugin system for custom planner providers
- High-quality task planning templates with atomic tasks and acceptance criteria
- Rich logging and progress indicators (optional dependency)
- State hardening with cross-platform file locking and crash safety
- Comprehensive test suite with 48+ tests and CI pipeline
- Standalone binary builds via PyInstaller for macOS, Linux, and Windows
- npm wrapper package for easy distribution

### Changed
- Refactored GPT mode to use adapter architecture
- Improved budgeting and error recovery in task execution

### Documentation
- Configuration system guide
- Planner adapter interface documentation
- Provider-specific adapter guides (OpenAI, Anthropic, Azure, DeepSeek)
- Plugin development guide
- Task planning templates documentation
- Rich logging UX documentation
- State hardening and crash safety documentation
- Test suite and CI documentation
- PyInstaller binary build documentation

[Unreleased]: https://github.com/ChinmayShringi/shoemaker-elves/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/ChinmayShringi/shoemaker-elves/releases/tag/v0.1.0
