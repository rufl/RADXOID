#!/bin/bash
# RADXOID - Prepare Distribution Package
# This script prepares the complete distribution package with split volumes
# Usage: ./prepare_distribution.sh [output_dir]

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="/run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r"
OUTPUT_DIR="${1:-$SCRIPT_DIR/RADXOID-v1.0.0}"
VOLUME_SIZE_MB=1900  # Slightly less than 2GB

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  RADXOID - Preparing Distribution Package v1.0.0                 ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if source directory exists
if [ ! -d "$SOURCE_DIR" ]; then
    echo -e "${RED}❌ Error: Source directory not found at $SOURCE_DIR${NC}"
    echo "   Please mount the USB HDD or check the path."
    exit 1
fi

echo -e "${YELLOW}🔹 Source directory: $SOURCE_DIR${NC}"
echo -e "${YELLOW}🔹 Output directory: $OUTPUT_DIR${NC}"
echo -e "${YELLOW}🔹 Volume size: ${VOLUME_SIZE_MB}MB${NC}"
echo ""

# Create output directory
mkdir -p "$OUTPUT_DIR"
echo -e "${GREEN}✅ Created output directory: $OUTPUT_DIR${NC}"
echo ""

# Create subdirectories
mkdir -p "$OUTPUT_DIR/volumes"
mkdir -p "$OUTPUT_DIR/installer/windows"
mkdir -p "$OUTPUT_DIR/installer/linux"
mkdir -p "$OUTPUT_DIR/installer/common"
echo -e "${GREEN}✅ Created subdirectories${NC}"
echo ""

# Copy installer files
echo -e "${YELLOW}🔹 Copying installer files...${NC}"
cp "$SCRIPT_DIR/installer/radxoid_installer.py" "$OUTPUT_DIR/installer/common/"
cp "$SCRIPT_DIR/installer/README.md" "$OUTPUT_DIR/installer/"
cp "$SCRIPT_DIR/installer/build_windows.bat" "$OUTPUT_DIR/installer/windows/"
cp "$SCRIPT_DIR/installer/build_linux.sh" "$OUTPUT_DIR/installer/linux/"
cp "$SCRIPT_DIR/split_volumes.py" "$OUTPUT_DIR/installer/common/"
cp "$SCRIPT_DIR/join_volumes.py" "$OUTPUT_DIR/installer/common/"
echo "   ✅ Installer files copied"
echo ""

# Split large files into volumes
echo -e "${YELLOW}🔹 Splitting files into volumes...${NC}"
cd "$SCRIPT_DIR"
python3 split_volumes.py "$SOURCE_DIR" "$OUTPUT_DIR/volumes" "$VOLUME_SIZE_MB"
echo ""

# Generate checksums
echo -e "${YELLOW}🔹 Generating checksums...${NC}"
cd "$OUTPUT_DIR/volumes"
sha256sum * > SHA256SUMS.txt
cat SHA256SUMS.txt
echo ""

# Copy README and LICENSE
echo -e "${YELLOW}🔹 Copying documentation...${NC}"
cp "$SCRIPT_DIR/README.md" "$OUTPUT_DIR/"
cp "$SCRIPT_DIR/../LICENSE" "$OUTPUT_DIR/" 2>/dev/null || echo "   ⚠️  LICENSE not found"
echo "   ✅ Documentation copied"
echo ""

# Create version info
echo -e "${YELLOW}🔹 Creating version info...${NC}"
cat > "$OUTPUT_DIR/VERSION.txt" << EOF
RADXOID Version: v1.0.0
Release Date: $(date +%Y-%m-%d)
Android Version: 11 (API 30)
Target Device: Radxa ROCK 3A (RK3568)
Build Status: BUILD_EXIT=0
GitHub: https://github.com/rufl/RADXOID
EOF
cat "$OUTPUT_DIR/VERSION.txt"
echo ""

# Create package info
echo -e "${YELLOW}🔹 Creating package info...${NC}"
cat > "$OUTPUT_DIR/PACKAGE_INFO.txt" << EOF
Package: RADXOID v1.0.0
Description: Lean Android 11 for Radxa ROCK 3A optimized for gaming and emulation

Contents:
- installer/ - Cross-platform GUI installer
- volumes/ - Split volume files
- README.md - Installation instructions
- LICENSE - License information
- VERSION.txt - Version information
- SHA256SUMS.txt - Checksums

Files Split into Volumes:
- update.img (1.8 GB) - 1 volume
- super.img (1.6 GB) - 1 volume
- gpt.img (4.1 GB) - 3 volumes (1900MB each)
- boot.img (35 MB) - 1 volume
- recovery.img (110 MB) - 1 volume
- dtbo.img (607 B) - 1 volume

Total Volumes: $(ls $OUTPUT_DIR/volumes/*.* | wc -l)
Total Size: $(du -sh $OUTPUT_DIR/volumes | cut -f1)

Installation:
1. Download all files from the release
2. Run the installer for your platform:
   - Windows: installer/windows/RADXOID-Installer.exe
   - Linux: installer/linux/RADXOID-Installer
3. Follow the GUI instructions

For more information, see: https://github.com/rufl/RADXOID
EOF
echo "   ✅ Package info created"
echo ""

# List all files in the distribution
echo -e "${YELLOW}🔹 Distribution contents:${NC}"
find "$OUTPUT_DIR" -type f | sort | sed "s|$OUTPUT_DIR/|  |"
echo ""

# Calculate total size
echo -e "${YELLOW}🔹 Distribution size:${NC}"
du -sh "$OUTPUT_DIR"
echo ""

# Create tar.gz for Linux distribution
echo -e "${YELLOW}🔹 Creating Linux distribution package...${NC}"
cd "$SCRIPT_DIR"
tar -czvf "$OUTPUT_DIR/../RADXOID-v1.0.0-linux.tar.gz" -C "$OUTPUT_DIR" .
echo "   ✅ Created: $OUTPUT_DIR/../RADXOID-v1.0.0-linux.tar.gz"
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ DISTRIBUTION PACKAGE PREPARED SUCCESSFULLY!                        ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Distribution Package Location: $OUTPUT_DIR"
echo ""
echo "Next Steps:"
echo "  1. Build Windows installer: cd $OUTPUT_DIR/installer/windows && build_windows.bat"
echo "  2. Build Linux installer: cd $OUTPUT_DIR/installer/linux && ./build_linux.sh"
echo "  3. Upload to GitHub release v1.0.0"
echo ""
echo "For GitHub release:"
echo "  - Upload all files from $OUTPUT_DIR"
echo "  - Use RELEASE_NOTES.md as the release description"
echo "  - Tag: v1.0.0"
echo ""
echo "✨ Distribution package is ready for publishing! ✨"
