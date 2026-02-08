#!/bin/bash
# Test script to simulate local installation

set -e

echo "Testing npm package local installation..."
echo ""

# Create a temporary directory
TEST_DIR=$(mktemp -d)
echo "Created test directory: $TEST_DIR"

# Clean up on exit
cleanup() {
  echo ""
  echo "Cleaning up test directory..."
  rm -rf "$TEST_DIR"
}
trap cleanup EXIT

# Pack the package
echo ""
echo "Packing npm package..."
PACKAGE_FILE=$(npm pack 2>&1 | grep -o 'shoemaker-elves.*\.tgz' | head -n1)

if [ -z "$PACKAGE_FILE" ]; then
  echo "Error: Failed to create package file"
  exit 1
fi

echo "Created package: $PACKAGE_FILE"

# Move package to test directory
mv "$PACKAGE_FILE" "$TEST_DIR/"

# Install in test directory
cd "$TEST_DIR"
echo ""
echo "Installing package in test directory..."
npm install "./$PACKAGE_FILE"

echo ""
echo "✓ Package installed successfully!"
echo ""
echo "Note: Binary download will only work if:"
echo "  1. A matching release exists on GitHub"
echo "  2. The version in package.json matches a release tag"
echo ""
echo "To test the wrapper after binary is available:"
echo "  npx shoemaker-elves --help"
echo ""

# Show what was installed
echo "Installed files:"
ls -la node_modules/shoemaker-elves/

echo ""
echo "Binary directory contents:"
ls -la node_modules/shoemaker-elves/bin/ || echo "bin directory not found"

echo ""
echo "Test complete!"
