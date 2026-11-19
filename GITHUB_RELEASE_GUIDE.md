# RADXOID - GitHub Release Publishing Guide

## 🎉 How to Publish v1.0.0 Release on GitHub

This guide provides step-by-step instructions to publish the RADXOID v1.0.0 release on GitHub.

---

## 📋 Prerequisites

### 1. GitHub Repository
- **Repository**: https://github.com/rufl/RADXOID
- **Branch**: main
- **Commits**: 24 commits (latest: 01471f8)
- **Access**: You need push permissions to the repository

### 2. Build Artifacts
The build artifacts are located at:
```
/run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/
```

Required files:
- `update.img` (1.8 GB) - SHA256: `eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5`
- `super.img` (1.6 GB)
- `rkupdate.img` (1.7 GB)
- `gpt.img` (4.1 GB)

### 3. Documentation
All documentation is already in the repository:
- `RELEASE_NOTES.md` - Complete release notes
- `README.md` - Main documentation
- `OPTIMIZATIONS.md` - All optimizations
- `SUMMARY.md` - Executive summary
- And 8 more documentation files

---

## 🚀 Publishing Methods

### Method 1: Using GitHub Web Interface (Recommended)

#### Step 1: Create Release Tag
1. Go to: https://github.com/rufl/RADXOID/releases/new
2. Click "Choose a tag" and type: **v1.0.0**
3. Click "+ Create new tag: v1.0.0 on publish"
4. Click "Create tag"

#### Step 2: Fill Release Information
1. **Release title**: `RADXOID v1.0.0 - Lean Android 11 for Radxa ROCK 3A`
2. **Description**: Copy the content from `RELEASE_NOTES.md`
3. **Tag**: v1.0.0
4. **Target**: main

#### Step 3: Upload Artifacts
Drag and drop these files from `/run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/`:
- `update.img`
- `super.img`
- `rkupdate.img`
- `gpt.img`

#### Step 4: Add Checksums
Create a `SHA256SUMS.txt` file with:
```
eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5  update.img
[add other checksums here]
```

Upload `SHA256SUMS.txt` as well.

#### Step 5: Publish Release
Click "Publish release"

---

### Method 2: Using GitHub CLI (gh)

If you have the GitHub CLI installed:

```bash
# Install gh CLI (if not installed)
# Ubuntu: sudo apt install gh
# Arch: sudo pacman -S github-cli

# Authenticate
gh auth login

# Create release
cd /home/lich/lichforge/code/monorepo/RADXOID

# Create tag
git tag -a v1.0.0 -m "Release v1.0.0: Lean Android 11 for Radxa ROCK 3A"
git push origin v1.0.0

# Create release with artifacts
gh release create v1.0.0 \
    --title "RADXOID v1.0.0 - Lean Android 11 for Radxa ROCK 3A" \
    --notes "$(cat RELEASE_NOTES.md)" \
    --repo rufl/RADXOID \
    /run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/update.img \
    /run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/super.img \
    /run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/rkupdate.img \
    /run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/gpt.img
```

---

### Method 3: Using the Publish Script

Run the provided script:

```bash
cd /home/lich/lichforge/code/monorepo/RADXOID
./scripts/publish-release.sh v1.0.0
```

This script will:
1. Create a release directory with symbolic links to artifacts
2. Generate SHA256 checksums
3. Create Git tag v1.0.0
4. Push tag to GitHub
5. Attempt to create GitHub release (using gh CLI if available)
6. Commit release notes

---

## 📝 Release Information

### Release Details
- **Version**: v1.0.0
- **Name**: RADXOID v1.0.0 - Lean Android 11 for Radxa ROCK 3A
- **Published**: 2026-11-19
- **Tag**: v1.0.0
- **Target**: main
- **Commit**: 01471f8

### Release Notes
Use the content from `RELEASE_NOTES.md`:

```markdown
## 🎉 v1.0.0 - Initial Release (2026-11-19)

**First stable release of RADXOID - Lean Android 11 for Radxa ROCK 3A (RK3568) optimized for gaming and emulation.**

### What's Included
- Build artifacts (update.img, super.img, rkupdate.img, gpt.img)
- 12 performance optimizations applied
- ~70 packages debloated
- Complete documentation

### Features
- CPU Governor: SCHEDUTIL (lower jitter)
- ART/Dexpreopt: 5 apps speed-profiled
- Zram: 75% RAM, writeback enabled
- I/O Scheduler: DEADLINE
- SurfaceFlinger: Triple buffer, vsync disabled
- And 7 more optimizations...

### Performance
- Boot Time: ~35-40s (15-20% faster)
- System Image: ~1.8GB (15% smaller)
- Memory Usage: ~1.0GB (15% lower)

### Quick Wins Ready
8 high-ROI optimizations ready to apply:
1. Zram LZ4 Compression
2. TCP BBR Congestion Control
3. CPU Frequency Limits
4. LMK Tuning
5. ART JIT Optimizations
6. Speed-Profile Apps
7. Zram Streams
8. Read-Ahead

See NEXT_OPTIMIZATIONS.md for details.

### Installation
```bash
git clone https://github.com/rufl/RADXOID.git
cd RADXOID
./scripts/flash-rock3a.sh [serial]
```

### Known Limitations
- Android 11 only (RK3568 has no official Android 12+ support)
- Proprietary Mali-G52 driver
- Requires 150GB for source tree
- Hardware testing required

### License
Apache 2.0 (code), CC-BY-4.0 (docs)
Do not redistribute proprietary Rockchip/Mali blobs.
```

---

## 📦 Artifact Information

### Files to Upload
| File | Size | SHA256 | Description |
|------|------|--------|-------------|
| `update.img` | 1.8 GB | `eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5` | Full flashable image |
| `super.img` | 1.6 GB | - | Dynamic partitions |
| `rkupdate.img` | 1.7 GB | - | Rockchip update package |
| `gpt.img` | 4.1 GB | - | Partition table |

### File Locations
```
Source: /run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/
```

### SHA256 Checksums
```
eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5  update.img
[generate others with: sha256sum *.img]
```

---

## 🎯 Post-Release Checklist

### After Publishing
- [ ] Verify release is visible at: https://github.com/rufl/RADXOID/releases
- [ ] Test download links
- [ ] Verify checksums
- [ ] Update README.md with release link
- [ ] Announce release (optional)

### Verification Commands
```bash
# Verify checksums
cd /path/to/downloads
sha256sum -c SHA256SUMS.txt

# Flash to device
./scripts/flash-rock3a.sh

# Verify GPU
./scripts/verify-gpu.sh
```

---

## 📚 Additional Documentation

### Repository Files
- `README.md` - Main documentation
- `RELEASE_NOTES.md` - Full release notes
- `OPTIMIZATIONS.md` - All applied optimizations
- `SUMMARY.md` - Executive summary
- `CHANGELOG.md` - Project history
- `ROADMAP.md` - Future optimizations
- `TODO.md` - Immediate action items
- `STATUS.md` - Current state
- `FINAL_SUMMARY.md` - Complete overview
- `RESUME.md` - Visual summary

### Scripts
- `scripts/build.sh` - Main build script
- `scripts/build-incremental.sh` - Incremental build
- `scripts/flash-rock3a.sh` - Flash to device
- `scripts/verify-gpu.sh` - Verify GPU
- `scripts/apply-quick-wins.sh` - Apply quick wins
- `scripts/apply-quick-wins-manual.sh` - Manual quick wins guide
- `scripts/verify-quick-wins.sh` - Verify quick wins
- `scripts/publish-release.sh` - Publish release

---

## 💡 Tips for Successful Release

### 1. Test Before Publishing
- Verify all artifacts exist and are accessible
- Test flashing on actual hardware (if possible)
- Verify checksums

### 2. Use Clear Naming
- Tag: `v1.0.0` (semantic versioning)
- Title: Include version and key features
- Description: Clear, concise, informative

### 3. Include All Necessary Files
- All build artifacts
- Checksums
- Release notes
- Installation instructions

### 4. Document Known Issues
- Be transparent about limitations
- Provide workarounds if available
- Set expectations

### 5. Provide Support Channels
- GitHub Issues for bug reports
- Clear contribution guidelines
- License information

---

## 🎉 Release Published!

Once published, your release will be available at:
```
https://github.com/rufl/RADXOID/releases/tag/v1.0.0
```

Users can:
1. Download the artifacts
2. Flash to their ROCK 3A
3. Apply Quick Wins (optional)
4. Test and provide feedback

---

## 📞 Support

For issues with the release:
- Open an issue: https://github.com/rufl/RADXOID/issues
- Check documentation: https://github.com/rufl/RADXOID#readme
- Review release notes: https://github.com/rufl/RADXOID/releases

---

*Last updated: 2026-11-19*
*Release: v1.0.0*
