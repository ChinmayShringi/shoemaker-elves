#!/usr/bin/env node
/**
 * Wrapper script that executes the platform-specific binary
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');

// Determine binary path
const binDir = __dirname;
const isWindows = process.platform === 'win32';
const binaryName = isWindows ? 'gpt-orch-win-x64.exe' : `gpt-orch-${process.platform}-${process.arch}`;
const binaryPath = path.join(binDir, binaryName);

// Check if binary exists
if (!fs.existsSync(binaryPath)) {
  console.error('Error: gpt-orch binary not found.');
  console.error('');
  console.error('The binary may not have been downloaded during installation.');
  console.error('Please try reinstalling the package:');
  console.error('');
  console.error('  npm install gpt-agent-orchestrator');
  console.error('');
  console.error('Or manually download the binary from:');
  console.error('https://github.com/ChinmayShringi/Chainsmith/releases');
  console.error('');
  console.error(`Expected binary location: ${binaryPath}`);
  process.exit(1);
}

// Spawn the binary with all arguments and environment variables
const child = spawn(binaryPath, process.argv.slice(2), {
  stdio: 'inherit',
  env: process.env,
});

// Handle process signals
process.on('SIGINT', () => {
  child.kill('SIGINT');
});

process.on('SIGTERM', () => {
  child.kill('SIGTERM');
});

// Exit with the same code as the child process
child.on('exit', (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code || 0);
  }
});

child.on('error', (err) => {
  console.error('Failed to execute binary:', err.message);
  process.exit(1);
});
