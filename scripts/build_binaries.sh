#!/usr/bin/env bash
# Build standalone binary using PyInstaller for POSIX systems (macOS/Linux)

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Get project root directory (one level up from scripts/)
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo -e "${GREEN}Building shoemaker-elves standalone binary${NC}"
echo "Project root: $PROJECT_ROOT"

# Detect platform and architecture (allow override from TARGET_ARCH env var)
PLATFORM="$(uname -s | tr '[:upper:]' '[:lower:]')"
if [ -n "${TARGET_ARCH:-}" ]; then
    ARCH="$TARGET_ARCH"
else
    ARCH="$(uname -m)"
fi

# Normalize architecture names (skip if already normalized from TARGET_ARCH)
case "$ARCH" in
    x64|arm64)
        # Already normalized
        ;;
    x86_64|amd64)
        ARCH="x64"
        ;;
    aarch64)
        ARCH="arm64"
        ;;
    *)
        echo -e "${YELLOW}Warning: Unknown architecture $ARCH, using as-is${NC}"
        ;;
esac

echo "Platform: $PLATFORM"
echo "Architecture: $ARCH"

# Check if PyInstaller is available
if ! command -v pyinstaller &> /dev/null; then
    echo -e "${RED}Error: PyInstaller not found${NC}"
    echo "Please install it with: pip install pyinstaller>=6.0.0"
    echo "Or install dev dependencies: pip install -e '.[dev,all]'"
    exit 1
fi

# Check if all dependencies are installed
echo -e "\n${GREEN}Checking dependencies...${NC}"
python -c "import openai, anthropic, rich, tomli, tomli_w, filelock" 2>/dev/null || {
    echo -e "${YELLOW}Warning: Some optional dependencies not found${NC}"
    echo "Installing all dependencies..."
    pip install -e ".[all]"
}

# Clean previous builds
echo -e "\n${GREEN}Cleaning previous builds...${NC}"
rm -rf build/ dist/

# Build with PyInstaller
echo -e "\n${GREEN}Building binary with PyInstaller...${NC}"
pyinstaller \
    --clean \
    --noconfirm \
    packaging/pyinstaller/shoemaker-elves.spec

# Check if build succeeded
if [ ! -f "dist/shoemaker-elves" ]; then
    echo -e "${RED}Error: Build failed - binary not found${NC}"
    exit 1
fi

# Rename binary with platform and architecture
BINARY_NAME="shoemaker-elves-${PLATFORM}-${ARCH}"
echo -e "\n${GREEN}Renaming binary to ${BINARY_NAME}${NC}"
mv dist/shoemaker-elves "dist/${BINARY_NAME}"

# Make binary executable (should already be, but just in case)
chmod +x "dist/${BINARY_NAME}"

# Get binary size
BINARY_SIZE=$(du -h "dist/${BINARY_NAME}" | cut -f1)

echo -e "\n${GREEN}✓ Build successful!${NC}"
echo "Binary: dist/${BINARY_NAME}"
echo "Size: ${BINARY_SIZE}"

# Test the binary
echo -e "\n${GREEN}Testing binary...${NC}"
if "./dist/${BINARY_NAME}" --help > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Binary test passed${NC}"
else
    echo -e "${RED}✗ Binary test failed${NC}"
    exit 1
fi

echo -e "\n${GREEN}Build complete!${NC}"
echo "To test the binary, run: ./dist/${BINARY_NAME} --help"
