#!/bin/bash
# RADXOID Installer - Build for Linux
# This script creates a standalone AppImage for Linux

set -e

echo "RADXOID Installer - Linux Build"
echo "================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    echo "Please install Python 3.8+ from your distribution"
    exit 1
fi

# Check if PyInstaller is installed
if ! python3 -m PyInstaller --version &> /dev/null; then
    echo "Installing PyInstaller..."
    python3 -m pip install PyInstaller --user
fi

# Create output directory
mkdir -p build/linux

# Build the installer
echo "Building RADXOID Installer for Linux..."
python3 -m PyInstaller \
    --onefile \
    --windowed \
    --name RADXOID-Installer \
    --add-data "../README.md:." \
    --add-data "../LICENSE:." \
    --distpath build/linux \
    --workpath build/linux/temp \
    radxoid_installer.py

if [ $? -ne 0 ]; then
    echo "Error: Build failed"
    exit 1
fi

echo ""
echo "✅ Build successful!"
echo "The installer is at: build/linux/RADXOID-Installer"

# Make executable
chmod +x build/linux/RADXOID-Installer

# Copy additional files
cp radxoid_installer.py build/linux/
cp ../README.md build/linux/
cp ../LICENSE build/linux/

echo ""
echo "To create the distribution package:"
echo "1. Run: python3 split_volumes.py /path/to/artifacts dist/volumes"
echo "2. Copy all files to: build/linux/volumes/"
echo "3. Create AppImage (optional):"
echo "   linuxdeploy-x86_64.AppImage build/linux/RADXOID-Installer -o build/linux/"
echo ""
echo "Or create a tar.gz:"
echo "   tar -czvf RADXOID-v1.0.0-linux.tar.gz -C build/linux ."
