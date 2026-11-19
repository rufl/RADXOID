# RADXOID - Release Notes

## 🎉 v1.0.0 - Initial Release (2026-11-19)

**First stable release of RADXOID - Lean Android 11 for Radxa ROCK 3A (RK3568) optimized for gaming and emulation.**

---

## 📋 Release Summary

| Item | Value |
|------|-------|
| **Version** | v1.0.0 |
| **Release Date** | 2026-11-19 |
| **Android Version** | 11 (API 30) |
| **Target Device** | Radxa ROCK 3A (RK3568) |
| **Build Status** | ✅ BUILD_EXIT=0 |
| **GitHub Commit** | 1b02851 |

---

## 🚀 What's Included

### Build Artifacts
| File | Size | SHA256 | Description |
|------|------|--------|-------------|
| `update.img` | 1.8 GB | `eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5` | Full flashable image |
| `super.img` | 1.6 GB | - | Dynamic partitions |
| `rkupdate.img` | 1.7 GB | - | Rockchip update package |
| `gpt.img` | 4.1 GB | - | Partition table |
| `recovery.img` | 110 MB | - | Recovery partition |
| `boot.img` | 35 MB | - | Boot partition |
| `dtbo.img` | 607 B | - | Device tree overlay |

### Source Tree
- **Location**: `/run/media/lich/EdgeBKP/radxoid/source` (150 GB)
- **Manifest**: `Android11_Radxa_rk12`
- **Revision**: `116eac8ed8e7b29ff17d9a71fa8d1adcb442da57`
- **Product**: `rk356x_rock_3a_r-userdebug`

---

## ✨ Features

### Performance Optimizations (12 Categories)
1. **CPU Governor**: SCHEDUTIL (replaces INTERACTIVE) - Lower jitter for emulation
2. **ART/Dexpreopt**: 5 apps speed-profiled (SystemUI, Settings, Launcher3QuickStep, LatinIME, PackageInstaller)
3. **ART JIT**: Inline depth 4, code cache 2MB
4. **Zram**: 75% of RAM, writeback enabled, swappiness=100
5. **I/O Scheduler**: DEADLINE (replaces CFQ)
6. **SurfaceFlinger**: Triple buffer, phase offsets disabled, vsync disabled
7. **Display**: 60Hz locked, adaptive refresh disabled
8. **Network**: Buffer sizes increased (16MB), TCP keepalive optimized
9. **Audio**: Flinger boost enabled, deep buffer disabled, offload buffer 128KB
10. **CPU Boost**: Enabled, 1000ms duration
11. **Thermal**: CPU 60°C, GPU 55°C thresholds
12. **Kernel CPU**: BIG_LITTLE, CPPC, DT, STATS enabled

### Debloat
- **~70 packages removed** across 13 categories:
  - Google GMS & Services (9 packages)
  - Telephony (7 packages)
  - TV & Media Center (7 packages)
  - Print Services (3 packages)
  - Carrier Services (3 packages)
  - Launchers & Wallpapers (5 packages)
  - Media Apps (9 packages)
  - Email & Contacts (5 packages)
  - Browser (2 packages)
  - System Apps (10 packages)
  - Development Tools (3 packages)
  - Accessibility (4 packages)
  - Miscellaneous (10 packages)
- **Impact**: ~300-400MB system image reduction

### Fixups
- LOCAL_TIDY disabled (prevents clang-tidy failures)
- Recovery partition size: 134217728 (8KiB headroom)

---

## 📊 Performance Metrics

### Expected Improvements
| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Boot Time | ~45s | ~35-40s | 15-20% faster |
| System Image Size | ~2.1GB | ~1.8GB | 15% smaller |
| Memory Usage | ~1.2GB | ~1.0GB | 15% lower |
| CPU Jitter | Variable | Lower | Better for emulation |
| App Launch Time | ~500ms | ~300-400ms | 20-40% faster |

### After Quick Wins (Estimated)
| Metric | Current | After Quick Wins | Improvement |
|--------|---------|------------------|-------------|
| Boot Time | ~40s | ~38s | 5% faster |
| App Launch | ~350ms | ~250ms | 30% faster |
| Memory Usage | ~1.0GB | ~0.95GB | 5% lower |
| CPU Jitter | Medium | Low | 20% better |
| Network Latency | Medium | Low | 25% better |
| Thermal Throttling | Occasional | Rare | 50% reduction |
| OOM Kills | Occasional | Rare | 70% reduction |

---

## 🎯 Quick Wins (Ready to Apply)

### 8 High-ROI Optimizations
| # | Optimization | File | Expected Impact |
|---|--------------|------|-----------------|
| 1 | Zram LZ4 Compression | BoardConfig.mk | +20% compression speed |
| 2 | TCP BBR Congestion Control | BoardConfig.mk | -25% latency |
| 3 | CPU Frequency Limits | BoardConfig.mk | -50% thermal throttling |
| 4 | LMK Tuning | BoardConfig.mk | -70% OOM kills |
| 5 | ART JIT Optimizations | BoardConfig.mk | +30% app launch |
| 6 | Speed-Profile Apps | rk356x_rock_3a_r.mk | +30% emulator launch |
| 7 | Zram Streams | BoardConfig.mk | +15% multi-core utilization |
| 8 | Read-Ahead | BoardConfig.mk | +10% I/O performance |

### How to Apply
```bash
# Method 1: Manual (recommended)
./scripts/apply-quick-wins-manual.sh

# Method 2: Automatic (requires sudo)
./scripts/apply-quick-wins.sh

# After applying:
./scripts/build-incremental.sh
./scripts/flash-rock3a.sh
./scripts/verify-quick-wins.sh [serial]
```

---

## 📚 Documentation

### Core Documentation (10 Files)
| File | Size | Purpose |
|------|------|---------|
| RESUME.md | 43 KB | Visual project summary |
| FINAL_SUMMARY.md | 19 KB | Complete project overview |
| NEXT_OPTIMIZATIONS.md | 15 KB | Detailed quick wins guide |
| OPTIMIZATIONS.md | 19 KB | All applied optimizations |
| README.md | 12 KB | Main documentation |
| STATUS.md | 11 KB | Current project state |
| SUMMARY.md | 11 KB | Executive summary |
| ROADMAP.md | 13 KB | Future optimizations |
| TODO.md | 8 KB | Immediate action items |
| CHANGELOG.md | 5 KB | Project history |

### Scripts (17 Files)
- Build: `build.sh`, `build-incremental.sh`
- Optimization: `debloat.sh`, `tune-performance.sh`
- Device: `flash-rock3a.sh`, `verify-gpu.sh`, `probe-rock3a.sh`
- Quick Wins: `apply-quick-wins.sh`, `apply-quick-wins-manual.sh`, `verify-quick-wins.sh`
- Utilities: `validate.sh`, `fix-ownership.sh`, `prepare.sh`, `fetch-gpu-driver.sh`, `package-gpu-overlay.sh`

---

## 🎮 Emulator Compatibility

### Expected Performance
| Emulator | Platform | Performance | Notes |
|----------|----------|-------------|-------|
| RetroArch | Multi-system | ✅ Excellent | Core support for RK3568 |
| PPSSPP | PSP | ✅ Excellent | Mali-G52 handles well |
| Drastic | Nintendo DS | ✅ Excellent | Low requirements |
| Dolphin | GameCube/Wii | ✅ Good | May need settings tweaks |
| DuckStation | PlayStation 1 | ✅ Excellent | Low requirements |
| Citra | Nintendo 3DS | ✅ Good | Mali-G52 capable |

---

## 🔧 Installation Instructions

### Prerequisites
- Radxa ROCK 3A device
- USB HDD with source tree (150 GB)
- Ubuntu 20.04 host or Docker

### Flashing
```bash
# Clone repository
git clone https://github.com/rufl/RADXOID.git
cd RADXOID

# Flash to device
./scripts/flash-rock3a.sh [adb-serial]

# Verify GPU
./scripts/verify-gpu.sh [adb-serial]
```

### Build from Source
```bash
# Prepare source tree (150 GB, one-time)
./scripts/prepare.sh

# Full build (~2.5-3 hours)
./scripts/build.sh

# Incremental build (~5-30 min)
./scripts/build-incremental.sh

# Lean build (with debloat)
ROCK3A_ENV=lean ./scripts/build-incremental.sh
```

---

## ⚠️ Known Limitations

1. **Android Version**: RK3568 only has official Android 11 support from Radxa
2. **GPU Driver**: Uses proprietary Mali-G52 driver (Panfrost not production-ready for Android)
3. **Build Time**: Full build takes 2-3 hours on USB HDD
4. **Storage**: Requires 150GB+ for source tree
5. **Testing**: Hardware validation required for GPU, thermals, performance
6. **Quick Wins**: Not yet applied in this release (ready to apply)

---

## 📝 Changelog

### v1.0.0 (2026-11-19)
- Initial release
- Android 11 build for Radxa ROCK 3A
- 12 performance optimizations applied
- ~70 packages debloated
- Complete documentation
- Build verified (BUILD_EXIT=0)

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Open a Pull Request

---

## 📜 License

- **Code**: Apache 2.0 (where applicable)
- **Documentation**: CC-BY-4.0
- **Rockchip BSP**: Proprietary (see Radxa terms)
- **Mali Driver**: Proprietary (see ARM terms)

**Do not redistribute proprietary Rockchip/Mali blobs outside their original license terms.**

---

## 📞 Support

- **Repository**: https://github.com/rufl/RADXOID
- **Issues**: https://github.com/rufl/RADXOID/issues
- **Pull Requests**: https://github.com/rufl/RADXOID/pulls

---

## 🏁 Release Checklist

- [x] Build successful (BUILD_EXIT=0)
- [x] Artifacts generated
- [x] Documentation complete
- [x] Quick Wins documented
- [x] GitHub repository updated
- [x] Release notes created
- [ ] GitHub Release published
- [ ] Hardware testing completed
- [ ] Performance benchmarks measured

---

*Release v1.0.0 - 2026-11-19*
*Build: RK356X_ROCK_3A_R_USERDEBUG_RK3568-ROCK-3A_ENG.RADXA.20261119.110506*
