#!/bin/bash
# RADXOID - Publish GitHub Release
# This script creates a GitHub release with the build artifacts
# Usage: ./scripts/publish-release.sh [version]
# Example: ./scripts/publish-release.sh v1.0.0

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
SOURCE_DIR="/run/media/lich/EdgeBKP/radxoid/source"
ARTIFACT_DIR="$SOURCE_DIR/rockdev/Image-rk356x_rock_3a_r"
RELEASE_DIR="$PROJECT_DIR/releases"

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Default version
VERSION="${1:-v1.0.0}"

echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  RADXOID - Publishing GitHub Release $VERSION                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -d "$PROJECT_DIR/.git" ]; then
    echo -e "${RED}❌ Error: Not in RADXOID project directory${NC}"
    exit 1
fi

# Create release directory
mkdir -p "$RELEASE_DIR"
echo -e "${YELLOW}🔹 Created release directory: $RELEASE_DIR${NC}"

# Check if artifacts exist
ARTIFACTS=("update.img" "super.img" "rkupdate.img" "gpt.img")
MISSING=()

for artifact in "${ARTIFACTS[@]}"; do
    if [ ! -f "$ARTIFACT_DIR/$artifact" ]; then
        MISSING+=("$artifact")
    fi
done

if [ ${#MISSING[@]} -gt 0 ]; then
    echo -e "${RED}❌ Error: Missing artifacts:${NC}"
    for artifact in "${MISSING[@]}"; do
        echo "   - $artifact"
    done
    echo ""
    echo "   Expected location: $ARTIFACT_DIR/"
    exit 1
fi

echo -e "${GREEN}✅ All artifacts found in $ARTIFACT_DIR/${NC}"
echo ""

# Copy artifacts to release directory (symbolic links to save space)
echo -e "${YELLOW}🔹 Creating symbolic links to artifacts...${NC}"
for artifact in "${ARTIFACTS[@]}"; do
    ln -sf "$ARTIFACT_DIR/$artifact" "$RELEASE_DIR/$artifact"
    echo "   Linked: $artifact"
done
echo ""

# Create checksums
echo -e "${YELLOW}🔹 Creating checksums...${NC}"
cd "$RELEASE_DIR"
sha256sum ${ARTIFACTS[@]} > "$RELEASE_DIR/SHA256SUMS.txt"
cat "$RELEASE_DIR/SHA256SUMS.txt"
echo ""

# Create release tag
echo -e "${YELLOW}🔹 Creating Git tag $VERSION...${NC}"
git tag -a "$VERSION" -m "Release $VERSION: Lean Android 11 for Radxa ROCK 3A"
echo "   Tag created: $VERSION"
echo ""

# Push tag to GitHub
echo -e "${YELLOW}🔹 Pushing tag to GitHub...${NC}"
git push origin "$VERSION"
echo "   Tag pushed to origin"
echo ""

# Create GitHub Release using GitHub CLI
echo -e "${YELLOW}🔹 Creating GitHub Release...${NC}"

# Check if gh CLI is available
if command -v gh &> /dev/null; then
    # Create release
    gh release create "$VERSION" \
        --title "RADXOID $VERSION - Lean Android 11 for Radxa ROCK 3A" \
        --notes "$(cat "$PROJECT_DIR/RELEASE_NOTES.md")" \
        --repo rufl/RADXOID
    
    echo -e "${GREEN}✅ GitHub Release created using gh CLI${NC}"
else
    echo -e "${YELLOW}⚠️  GitHub CLI (gh) not found. Manual release creation required.${NC}"
    echo ""
    echo "To create the release manually:"
    echo "1. Go to: https://github.com/rufl/RADXOID/releases/new"
    echo "2. Tag version: $VERSION"
    echo "3. Release title: RADXOID $VERSION - Lean Android 11 for Radxa ROCK 3A"
    echo "4. Copy release notes from: $PROJECT_DIR/RELEASE_NOTES.md"
    echo "5. Upload artifacts from: $RELEASE_DIR/"
    echo ""
fi

# Commit release notes
echo -e "${YELLOW}🔹 Committing release notes...${NC}"
cd "$PROJECT_DIR"
git add RELEASE_NOTES.md
git commit -m "docs: add RELEASE_NOTES.md for $VERSION"
git push origin main
echo "   Release notes committed"
echo ""

# Summary
echo -e "${GREEN}╔════════════════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  ✅ RELEASE $VERSION PUBLISHED SUCCESSFULLY!                              ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Release Summary:"
echo "  Version: $VERSION"
echo "  Tag: $VERSION"
echo "  Artifacts: ${ARTIFACTS[*]}"
echo "  Checksums: SHA256SUMS.txt"
echo "  Release Notes: RELEASE_NOTES.md"
echo ""
echo "GitHub Release URL:"
echo "  https://github.com/rufl/RADXOID/releases/tag/$VERSION"
echo ""
echo "Local Release Directory:"
echo "  $RELEASE_DIR/"
echo ""
echo "Next Steps:"
echo "  1. Download artifacts from GitHub release"
echo "  2. Flash to ROCK 3A: ./scripts/flash-rock3a.sh"
echo "  3. Apply Quick Wins (optional)"
echo "  4. Test and validate"
echo ""

exit 0
