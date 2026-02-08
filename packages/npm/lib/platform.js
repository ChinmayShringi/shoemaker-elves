#!/usr/bin/env node
/**
 * Platform detection and binary name resolution
 */

const os = require('os');

/**
 * Get the current platform identifier
 * @returns {string} Platform name (darwin, linux, win32)
 */
function getPlatform() {
  const platform = os.platform();

  // Validate supported platforms
  const supportedPlatforms = ['darwin', 'linux', 'win32'];
  if (!supportedPlatforms.includes(platform)) {
    throw new Error(
      `Unsupported platform: ${platform}. ` +
      `Supported platforms: ${supportedPlatforms.join(', ')}`
    );
  }

  return platform;
}

/**
 * Get the current architecture identifier
 * @returns {string} Architecture name (x64, arm64)
 */
function getArch() {
  const arch = os.arch();

  // Map Node.js arch names to our binary naming convention
  const archMap = {
    'x64': 'x64',
    'arm64': 'arm64',
    'aarch64': 'arm64',
  };

  const mappedArch = archMap[arch];
  if (!mappedArch) {
    throw new Error(
      `Unsupported architecture: ${arch}. ` +
      `Supported architectures: ${Object.keys(archMap).join(', ')}`
    );
  }

  return mappedArch;
}

/**
 * Get the binary filename for the current platform
 * @param {string} version - Version string (e.g., "0.1.0")
 * @returns {string} Binary filename
 */
function getBinaryName(version) {
  const platform = getPlatform();
  const arch = getArch();
  const ext = platform === 'win32' ? '.exe' : '';

  return `gpt-orch-${platform}-${arch}${ext}`;
}

/**
 * Get the download URL for the current platform
 * @param {string} version - Version string (e.g., "0.1.0")
 * @returns {string} Download URL
 */
function getDownloadUrl(version) {
  const binaryName = getBinaryName(version);
  const repo = 'ChinmayShringi/Chainsmith';
  const tag = `v${version}`;

  return `https://github.com/${repo}/releases/download/${tag}/${binaryName}`;
}

/**
 * Get the checksums file URL
 * @param {string} version - Version string (e.g., "0.1.0")
 * @returns {string} Checksums file URL
 */
function getChecksumsUrl(version) {
  const repo = 'ChinmayShringi/Chainsmith';
  const tag = `v${version}`;

  return `https://github.com/${repo}/releases/download/${tag}/checksums.txt`;
}

module.exports = {
  getPlatform,
  getArch,
  getBinaryName,
  getDownloadUrl,
  getChecksumsUrl,
};
