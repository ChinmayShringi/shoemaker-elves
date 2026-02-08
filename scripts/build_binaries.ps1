# Build standalone binary using PyInstaller for Windows
# PowerShell script for Windows systems

#Requires -Version 5.1

$ErrorActionPreference = "Stop"

# Colors for output
function Write-ColorOutput {
    param(
        [string]$Message,
        [string]$Color = "White"
    )
    Write-Host $Message -ForegroundColor $Color
}

# Get project root directory (one level up from scripts/)
$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

Write-ColorOutput "Building shoemaker-elves standalone binary" -Color Green
Write-Host "Project root: $ProjectRoot"

# Detect architecture (allow override from TARGET_ARCH env var)
if ($env:TARGET_ARCH) {
    $Arch = $env:TARGET_ARCH
} elseif ([Environment]::Is64BitOperatingSystem) {
    $Arch = "x64"
} else {
    $Arch = "x86"
}
$Platform = "windows"

Write-Host "Platform: $Platform"
Write-Host "Architecture: $Arch"

# Check if PyInstaller is available
try {
    $null = Get-Command pyinstaller -ErrorAction Stop
} catch {
    Write-ColorOutput "Error: PyInstaller not found" -Color Red
    Write-Host "Please install it with: pip install pyinstaller>=6.0.0"
    Write-Host "Or install dev dependencies: pip install -e .[dev,all]"
    exit 1
}

# Check if all dependencies are installed
Write-Host ""
Write-ColorOutput "Checking dependencies..." -Color Green
$checkCmd = "import openai, anthropic, rich, tomli, tomli_w, filelock"
$ErrorActionPreference = "Continue"
python -c $checkCmd 2>$null
$depCheck = $LASTEXITCODE
$ErrorActionPreference = "Stop"
if ($depCheck -ne 0) {
    Write-ColorOutput "Warning: Some optional dependencies not found" -Color Yellow
    Write-Host "Installing all dependencies..."
    pip install -e ".[all]"
}

# Clean previous builds
Write-Host ""
Write-ColorOutput "Cleaning previous builds..." -Color Green
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }

# Build with PyInstaller
Write-Host ""
Write-ColorOutput "Building binary with PyInstaller..." -Color Green
pyinstaller --clean --noconfirm packaging/pyinstaller/shoemaker-elves.spec

# Check if build succeeded
$BinaryPath = "dist/shoemaker-elves.exe"
if (-not (Test-Path $BinaryPath)) {
    Write-ColorOutput "Error: Build failed - binary not found" -Color Red
    exit 1
}

# Rename binary with platform and architecture
$BinaryName = "shoemaker-elves-$Platform-$Arch.exe"
Write-Host ""
Write-ColorOutput "Renaming binary to $BinaryName" -Color Green
Move-Item -Path $BinaryPath -Destination "dist/$BinaryName" -Force

# Get binary size
$BinarySize = (Get-Item "dist/$BinaryName").Length
$BinarySizeMB = [math]::Round($BinarySize / 1MB, 2)

Write-Host ""
Write-ColorOutput "Build successful!" -Color Green
Write-Host "Binary: dist/$BinaryName"
Write-Host "Size: ${BinarySizeMB} MB"

# Test the binary
Write-Host ""
Write-ColorOutput "Testing binary..." -Color Green
try {
    $null = & "dist/$BinaryName" --help 2>&1
    Write-ColorOutput "Binary test passed" -Color Green
} catch {
    Write-ColorOutput "Binary test failed" -Color Red
    Write-Host $_.Exception.Message
    exit 1
}

Write-Host ""
Write-ColorOutput "Build complete!" -Color Green
Write-Host "To test the binary, run: .\dist\$BinaryName --help"
