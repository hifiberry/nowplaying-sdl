#!/bin/bash

# Clean up Debian package build artifacts for nowplaying-sdl

cd "$(dirname "$0")"

echo "Cleaning Debian package build artifacts..."
echo "==========================================="

# Clean build directory
if [ -f debian/rules ]; then
    echo "Running debian/rules clean..."
    debian/rules clean || true
fi

# Remove build artifacts from parent directory
echo "Removing .deb, .buildinfo, .changes files..."
rm -f ../nowplaying-sdl_*.deb
rm -f ../nowplaying-sdl_*.buildinfo
rm -f ../nowplaying-sdl_*.changes
rm -f ../nowplaying-sdl_*.build

# Remove pybuild directory
echo "Removing .pybuild directory..."
rm -rf .pybuild

# Remove Python build artifacts
echo "Removing Python build artifacts..."
rm -rf build/
rm -rf dist/
rm -rf *.egg-info
rm -rf nowplaying_sdl.egg-info
find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true

# Remove Debian package build artifacts
echo "Removing debian build artifacts..."
rm -rf debian/nowplaying-sdl/
rm -rf debian/.debhelper/
rm -f debian/debhelper-build-stamp
rm -f debian/files
rm -f debian/*.log
rm -f debian/*.substvars

echo ""
echo "==========================================="
echo "Cleanup complete!"
