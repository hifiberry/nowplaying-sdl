#!/bin/bash
set -e

# Build Debian package for nowplaying-sdl
# Version is taken from debian/changelog

cd "$(dirname "$0")"

echo "Building nowplaying-sdl Debian package..."
echo "==========================================="

# Check if required build tools are installed
if ! command -v dpkg-buildpackage &> /dev/null; then
    echo "Error: dpkg-buildpackage not found. Please install build-essential and debhelper:"
    echo "  sudo apt-get install build-essential debhelper dh-python python3-all python3-setuptools"
    exit 1
fi

# Check if python3-sdl2 is installed (needed for build)
if ! dpkg -l python3-sdl2 &> /dev/null; then
    echo "Warning: python3-sdl2 not installed. Installing build dependency..."
    sudo apt-get install -y python3-sdl2
fi

# Extract version from debian/changelog
VERSION=$(dpkg-parsechangelog -S Version)
echo "Package version: $VERSION"
echo ""

# Clean previous build artifacts
echo "Cleaning previous build artifacts..."
debian/rules clean || true
rm -f ../nowplaying-sdl_*.deb ../nowplaying-sdl_*.buildinfo ../nowplaying-sdl_*.changes 2>/dev/null || true
echo ""

# Build the package
echo "Building package..."
dpkg-buildpackage -us -uc -b

echo ""
echo "==========================================="
echo "Build complete!"
echo ""
echo "Package created: ../nowplaying-sdl_${VERSION}_all.deb"
echo ""
echo "To install:"
echo "  sudo dpkg -i ../nowplaying-sdl_${VERSION}_all.deb"
echo ""
echo "To install dependencies if needed:"
echo "  sudo apt-get install -f"
