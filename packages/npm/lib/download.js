#!/usr/bin/env node
/**
 * Binary download and verification utilities
 */

const https = require('https');
const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

/**
 * Download a file from a URL
 * @param {string} url - URL to download from
 * @param {string} dest - Destination file path
 * @returns {Promise<void>}
 */
function downloadFile(url, dest) {
  return new Promise((resolve, reject) => {
    const file = fs.createWriteStream(dest);
    let redirectCount = 0;
    const maxRedirects = 5;

    function handleResponse(response) {
      // Handle redirects
      if (response.statusCode === 301 || response.statusCode === 302) {
        redirectCount++;
        if (redirectCount > maxRedirects) {
          file.close();
          fs.unlinkSync(dest);
          reject(new Error(`Too many redirects (${maxRedirects})`));
          return;
        }

        const redirectUrl = response.headers.location;
        if (!redirectUrl) {
          file.close();
          fs.unlinkSync(dest);
          reject(new Error('Redirect location not provided'));
          return;
        }

        https.get(redirectUrl, handleResponse).on('error', (err) => {
          file.close();
          fs.unlinkSync(dest);
          reject(err);
        });
        return;
      }

      // Handle error responses
      if (response.statusCode !== 200) {
        file.close();
        fs.unlinkSync(dest);
        reject(new Error(`Download failed with status code: ${response.statusCode}`));
        return;
      }

      // Pipe the response to the file
      response.pipe(file);

      file.on('finish', () => {
        file.close();
        resolve();
      });
    }

    https.get(url, handleResponse).on('error', (err) => {
      file.close();
      fs.unlinkSync(dest);
      reject(err);
    });

    file.on('error', (err) => {
      file.close();
      fs.unlinkSync(dest);
      reject(err);
    });
  });
}

/**
 * Calculate SHA256 checksum of a file
 * @param {string} filePath - Path to the file
 * @returns {Promise<string>} Hex-encoded checksum
 */
function calculateChecksum(filePath) {
  return new Promise((resolve, reject) => {
    const hash = crypto.createHash('sha256');
    const stream = fs.createReadStream(filePath);

    stream.on('data', (data) => hash.update(data));
    stream.on('end', () => resolve(hash.digest('hex')));
    stream.on('error', reject);
  });
}

/**
 * Download and parse checksums file
 * @param {string} url - URL to checksums file
 * @returns {Promise<Map<string, string>>} Map of filename to checksum
 */
async function downloadChecksums(url) {
  return new Promise((resolve, reject) => {
    https.get(url, (response) => {
      if (response.statusCode === 404) {
        // Checksums file not found - this is acceptable, we'll skip verification
        console.warn('Warning: checksums.txt not found, skipping verification');
        resolve(new Map());
        return;
      }

      if (response.statusCode !== 200) {
        reject(new Error(`Failed to download checksums: ${response.statusCode}`));
        return;
      }

      let data = '';
      response.on('data', (chunk) => data += chunk);
      response.on('end', () => {
        const checksums = new Map();
        const lines = data.split('\n').filter(line => line.trim());

        for (const line of lines) {
          // Format: <checksum>  <filename> or <checksum> *<filename>
          const match = line.match(/^([a-f0-9]{64})\s+\*?(.+)$/);
          if (match) {
            checksums.set(match[2].trim(), match[1].trim());
          }
        }

        resolve(checksums);
      });
    }).on('error', (err) => {
      console.warn(`Warning: Failed to download checksums: ${err.message}`);
      resolve(new Map());
    });
  });
}

/**
 * Verify file checksum
 * @param {string} filePath - Path to the file
 * @param {string} expectedChecksum - Expected checksum
 * @returns {Promise<boolean>} True if checksum matches
 */
async function verifyChecksum(filePath, expectedChecksum) {
  const actualChecksum = await calculateChecksum(filePath);
  return actualChecksum.toLowerCase() === expectedChecksum.toLowerCase();
}

/**
 * Make file executable (Unix-like systems)
 * @param {string} filePath - Path to the file
 */
function makeExecutable(filePath) {
  if (process.platform !== 'win32') {
    fs.chmodSync(filePath, 0o755);
  }
}

/**
 * Download binary with checksum verification
 * @param {string} binaryUrl - URL to the binary
 * @param {string} checksumsUrl - URL to the checksums file
 * @param {string} binaryName - Name of the binary file
 * @param {string} destPath - Destination path for the binary
 * @returns {Promise<void>}
 */
async function downloadAndVerifyBinary(binaryUrl, checksumsUrl, binaryName, destPath) {
  console.log(`Downloading ${binaryName}...`);
  console.log(`From: ${binaryUrl}`);

  // Download the binary
  await downloadFile(binaryUrl, destPath);
  console.log('Download complete.');

  // Download and verify checksums
  console.log('Verifying checksum...');
  const checksums = await downloadChecksums(checksumsUrl);

  if (checksums.size > 0 && checksums.has(binaryName)) {
    const expectedChecksum = checksums.get(binaryName);
    const isValid = await verifyChecksum(destPath, expectedChecksum);

    if (!isValid) {
      fs.unlinkSync(destPath);
      throw new Error('Checksum verification failed! The downloaded file may be corrupted.');
    }

    console.log('Checksum verified successfully.');
  } else {
    console.warn('Warning: Skipping checksum verification (checksums.txt not available)');
  }

  // Make executable
  makeExecutable(destPath);
  console.log('Binary installed successfully.');
}

module.exports = {
  downloadFile,
  calculateChecksum,
  downloadChecksums,
  verifyChecksum,
  makeExecutable,
  downloadAndVerifyBinary,
};
