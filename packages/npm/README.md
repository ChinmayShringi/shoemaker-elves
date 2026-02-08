# shoemaker-elves

A CLI tool that uses GPT as an orchestrator to break down large projects into tasks, then runs each task through an AI coding agent automatically using a hook-driven chain.

## Installation

```bash
npm install -g shoemaker-elves
```

Or use with npx (no installation required):

```bash
npx shoemaker-elves --help
```

## Usage

```bash
shoemaker-elves --help
shoemaker-elves init
shoemaker-elves plan "Build a web application"
shoemaker-elves run
```

## Platform Support

This package automatically downloads the appropriate binary for your platform during installation:

- **macOS**: darwin-arm64 (Apple Silicon), darwin-x64 (Intel)
- **Linux**: linux-x64, linux-arm64
- **Windows**: win-x64

## Requirements

- Node.js 16.0.0 or later

## Manual Installation

If automatic installation fails, you can manually install the binary:

1. Download the binary for your platform from the [releases page](https://github.com/ChinmayShringi/shoemaker-elves/releases)
2. Place it in `node_modules/shoemaker-elves/bin/`
3. Make it executable (Unix/Mac): `chmod +x <binary-path>`

## Security

Binary downloads are verified using SHA256 checksums published with each release.

## License

MIT

## Repository

[https://github.com/ChinmayShringi/shoemaker-elves](https://github.com/ChinmayShringi/shoemaker-elves)
