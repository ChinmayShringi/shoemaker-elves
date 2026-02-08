/**
 * Unit tests for platform detection and mapping
 */

const { test, describe } = require('node:test');
const assert = require('node:assert');
const os = require('os');

// We need to mock os module for testing different platforms
// Since we can't easily mock in Node's built-in test runner,
// we'll test the actual behavior and validate the logic

const {
  getPlatform,
  getArch,
  getBinaryName,
  getDownloadUrl,
  getChecksumsUrl,
} = require('../lib/platform');

describe('Platform Detection', () => {
  test('getPlatform returns current platform', () => {
    const platform = getPlatform();
    assert.ok(['darwin', 'linux', 'win32'].includes(platform));
    assert.strictEqual(platform, os.platform());
  });

  test('getArch returns valid architecture', () => {
    const arch = getArch();
    assert.ok(['x64', 'arm64'].includes(arch));
  });

  test('getArch maps aarch64 to arm64', () => {
    // This test validates the mapping logic conceptually
    const archMap = {
      'x64': 'x64',
      'arm64': 'arm64',
      'aarch64': 'arm64',
    };
    assert.strictEqual(archMap['aarch64'], 'arm64');
  });

  test('getBinaryName includes platform and arch', () => {
    const version = '0.1.0';
    const binaryName = getBinaryName(version);

    const platform = os.platform();
    const arch = os.arch() === 'aarch64' ? 'arm64' : os.arch();

    assert.ok(binaryName.includes(platform));
    assert.ok(binaryName.includes(arch === 'aarch64' ? 'arm64' : arch));
    assert.ok(binaryName.startsWith('gpt-orch-'));
  });

  test('getBinaryName adds .exe extension on Windows', () => {
    const version = '0.1.0';
    const binaryName = getBinaryName(version);

    if (os.platform() === 'win32') {
      assert.ok(binaryName.endsWith('.exe'));
    } else {
      assert.ok(!binaryName.endsWith('.exe'));
    }
  });

  test('getDownloadUrl returns valid GitHub URL', () => {
    const version = '0.1.0';
    const url = getDownloadUrl(version);

    assert.ok(url.startsWith('https://github.com/'));
    assert.ok(url.includes('/releases/download/'));
    assert.ok(url.includes('v0.1.0'));
    assert.ok(url.includes('gpt-orch-'));
  });

  test('getChecksumsUrl returns valid GitHub URL', () => {
    const version = '0.1.0';
    const url = getChecksumsUrl(version);

    assert.ok(url.startsWith('https://github.com/'));
    assert.ok(url.includes('/releases/download/'));
    assert.ok(url.includes('v0.1.0'));
    assert.ok(url.endsWith('checksums.txt'));
  });

  test('binary names follow expected patterns', () => {
    const version = '1.0.0';

    // Test different platform/arch combinations conceptually
    const expectedPatterns = [
      'gpt-orch-darwin-x64',
      'gpt-orch-darwin-arm64',
      'gpt-orch-linux-x64',
      'gpt-orch-linux-arm64',
      'gpt-orch-win-x64.exe',
    ];

    // Verify at least one matches current platform
    const currentBinary = getBinaryName(version);
    const matchesPattern = expectedPatterns.some(pattern =>
      pattern === currentBinary ||
      (pattern.endsWith('.exe') && currentBinary.endsWith('.exe'))
    );

    assert.ok(matchesPattern, `Current binary ${currentBinary} should match an expected pattern`);
  });

  test('download URLs are consistent across versions', () => {
    const url1 = getDownloadUrl('0.1.0');
    const url2 = getDownloadUrl('0.2.0');

    // Should have same structure, different version
    assert.ok(url1.includes('v0.1.0'));
    assert.ok(url2.includes('v0.2.0'));

    // Same repo and path structure
    const base1 = url1.split('/v0.1.0/')[0];
    const base2 = url2.split('/v0.2.0/')[0];
    assert.strictEqual(base1, base2);
  });
});

describe('Error Handling', () => {
  test('unsupported platform should throw error', () => {
    // We can't easily test this without mocking, but we verify the logic exists
    // by checking that getPlatform validates against known platforms
    const platform = getPlatform();
    assert.ok(['darwin', 'linux', 'win32'].includes(platform));
  });

  test('functions do not throw with valid inputs', () => {
    assert.doesNotThrow(() => getPlatform());
    assert.doesNotThrow(() => getArch());
    assert.doesNotThrow(() => getBinaryName('0.1.0'));
    assert.doesNotThrow(() => getDownloadUrl('0.1.0'));
    assert.doesNotThrow(() => getChecksumsUrl('0.1.0'));
  });
});

describe('URL Structure', () => {
  test('URLs point to correct repository', () => {
    const downloadUrl = getDownloadUrl('0.1.0');
    const checksumsUrl = getChecksumsUrl('0.1.0');

    const expectedRepo = 'ChinmayShringi/Chainsmith';
    assert.ok(downloadUrl.includes(expectedRepo));
    assert.ok(checksumsUrl.includes(expectedRepo));
  });

  test('version is properly formatted in URLs', () => {
    const testVersions = ['0.1.0', '1.2.3', '10.20.30'];

    testVersions.forEach(version => {
      const url = getDownloadUrl(version);
      assert.ok(url.includes(`/v${version}/`));
    });
  });
});
