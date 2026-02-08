#!/usr/bin/env node
/**
 * Post-install script to download the appropriate binary
 */

const fs = require('fs');
const path = require('path');
const { getBinaryName, getDownloadUrl, getChecksumsUrl, getPlatform, getArch } = require('../lib/platform');
const { downloadAndVerifyBinary } = require('../lib/download');

const PACKAGE_JSON = require('../package.json');

// Marker file to track if binary has been downloaded
const MARKER_FILE = path.join(__dirname, '..', 'bin', '.downloaded');

function showManualInstallInstructions() {
  console.error('\n===========================================');
  console.error('Manual Installation Instructions');
  console.error('===========================================\n');
  console.error('To manually install shoemaker-elves:');
  console.error('');
  console.error('1. Download the binary for your platform from:');
  console.error(`   https://github.com/ChinmayShringi/shoemaker-elves/releases/tag/v${PACKAGE_JSON.version}`);
  console.error('');
  console.error('2. Place the binary in:');
  console.error(`   ${path.join(__dirname, '..', 'bin', 'shoemaker-elves' + (process.platform === 'win32' ? '.exe' : ''))}`);
  console.error('');
  console.error('3. Make it executable (Unix/Mac):');
  console.error('   chmod +x <path-to-binary>');
  console.error('');
  console.error('===========================================\n');
}

async function main() {
  try {
    // Check if binary already downloaded
    if (fs.existsSync(MARKER_FILE)) {
      console.log('Binary already downloaded, skipping installation.');
      return;
    }

    // Detect platform
    const platform = getPlatform();
    const arch = getArch();
    console.log(`Detected platform: ${platform}-${arch}`);

    // Get URLs and paths
    const version = PACKAGE_JSON.version;
    const binaryName = getBinaryName(version);
    const binaryUrl = getDownloadUrl(version);
    const checksumsUrl = getChecksumsUrl(version);

    const binDir = path.join(__dirname, '..', 'bin');
    if (!fs.existsSync(binDir)) {
      fs.mkdirSync(binDir, { recursive: true });
    }

    const destPath = path.join(binDir, path.basename(binaryName));

    // Download and verify
    await downloadAndVerifyBinary(binaryUrl, checksumsUrl, binaryName, destPath);

    // Create marker file
    fs.writeFileSync(MARKER_FILE, new Date().toISOString());

    console.log('\n✓ shoemaker-elves installed successfully!');
    console.log(`Run 'npx shoemaker-elves --help' to get started.\n`);

  } catch (error) {
    console.error('\n✗ Failed to install shoemaker-elves binary:');
    console.error(error.message);
    console.error('');

    showManualInstallInstructions();

    // Exit with success code to not block npm install
    // Users can still manually install the binary
    process.exit(0);
  }
}

// Only run if this is the main module
if (require.main === module) {
  main().catch(err => {
    console.error('Unexpected error:', err);
    process.exit(0); // Exit gracefully
  });
}

module.exports = { main };
