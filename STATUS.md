# RADXOID - Current Status & Quick Reference

## 🎯 Project State: READY FOR HARDWARE TESTING

---

## ✅ COMPLETED

### Build System
- [x] **Source Tree**: Prepared at `/run/media/lich/EdgeBKP/radxoid/source` (150GB)
- [x] **Build Scripts**: `build.sh`, `build-incremental.sh`, `validate.sh`
- [x] **Docker Image**: `radxoid-builder:u20.04`
- [x] **Configuration**: `rock3a.env`, `rock3a-lean.env`
- [x] **Last Build**: 2026-11-19 12:34-12:51, `BUILD_EXIT=0`

### Optimizations Applied
- [x] **CPU Governor**: SCHEDUTIL (replaces INTERACTIVE)
- [x] **ART/Dexpreopt**: 5 apps (SystemUI, Settings, Launcher3QuickStep, LatinIME, PackageInstaller)
- [x] **ART JIT**: inline=4, codeCacheSize=2MB
- [x] **Zram**: 75% RAM, writeback enabled, swappiness=100
- [x] **I/O Scheduler**: DEADLINE (replaces CFQ)
- [x] **SurfaceFlinger**: Triple buffer, phase offsets disabled, vsync disabled
- [x] **Display**: 60Hz locked, adaptive refresh disabled
- [x] **Network**: Buffer sizes increased, TCP keepalive optimized
- [x] **Audio**: Flinger boost, deep buffer disabled, offload buffer 128KB
- [x] **CPU Boost**: Enabled, duration=1000ms
- [x] **Thermal**: CPU 60°C, GPU 55°C thresholds
- [x] **Kernel CPU**: BIG_LITTLE, CPPC, DT, STATS enabled

### Debloat
- [x] **~70 packages removed** (GMS, telephony, TV, print, carrier, wallpapers, media apps, email, browser, system apps, dev tools, accessibility)
- [x] **Impact**: ~300-400MB system image reduction

### Fixups
- [x] **LOCAL_TIDY**: Disabled (prevents clang-tidy failures)
- [x] **Recovery Partition**: 134217728 (8KiB headroom)

### Documentation
- [x] **README.md**: Complete project documentation
- [x] **OPTIMIZATIONS.md**: All applied optimizations documented
- [x] **SUMMARY.md**: Executive summary with metrics
- [x] **CHANGELOG.md**: Project history
- [x] **ROADMAP.md**: Future optimizations
- [x] **TODO.md**: Immediate action items
- [x] **docs/ARCH_HOST.md**: Arch Linux host setup
- [x] **docs/GPU_DRIVER_OVERRIDE.md**: GPU driver override

### GitHub Repository
- [x] **URL**: https://github.com/rufl/RADXOID
- [x] **Branch**: main
- [x] **Commits**: 18 commits (58d9bf4..1719435)
- [x] **Latest**: 1719435 docs: add ROADMAP.md and TODO.md for future optimizations

---

## 📊 Build Artifacts (2026-11-19)

| File | Size | SHA256 | Location |
|------|------|--------|----------|
| `update.img` | 1.8 GB | `eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5` | `source/rockdev/Image-rk356x_rock_3a_r/` |
| `super.img` | 1.6 GB | - | `source/rockdev/Image-rk356x_rock_3a_r/` |
| `rkupdate.img` | 1.7 GB | - | `source/rockdev/Image-rk356x_rock_3a_r/` |
| `gpt.img` | 4.1 GB | - | `source/rockdev/Image-rk356x_rock_3a_r/` |
| `recovery.img` | 110 MB | - | `source/IMAGE/RK356X_ROCK_3A_R_USERDEBUG_*/` |
| `boot.img` | 35 MB | - | `source/IMAGE/RK356X_ROCK_3A_R_USERDEBUG_*/` |
| `dtbo.img` | 607 B | - | `source/IMAGE/RK356X_ROCK_3A_R_USERDEBUG_*/` |

---

## 🚀 QUICK START

### Build Commands
```bash
# Full build (first time)
./scripts/build.sh

# Incremental build (reuses out/)
./scripts/build-incremental.sh

# Lean build (with debloat)
ROCK3A_ENV=lean ./scripts/build-incremental.sh

# Docker build
docker run --rm -v "$PWD":/work -v /run/media/lich/EdgeBKP:/run/media/lich/EdgeBKP \
  radxoid-builder:u20.04 -lc 'cd /work && ROCK3A_ENV=lean ./scripts/build-incremental.sh'
```

### Flash & Verify
```bash
# Flash to device
./scripts/flash-rock3a.sh [adb-serial]

# Verify GPU
./scripts/verify-gpu.sh [adb-serial]
```

---

## 🎮 NEXT STEPS (Immediate)

### 1. Hardware Testing (P0 - Critical)
- [ ] Flash `update.img` to ROCK 3A
- [ ] Verify boot and ADB connectivity
- [ ] Run `verify-gpu.sh` to check Mali-G52
- [ ] Test basic functionality

### 2. Quick Wins (P1 - High ROI, Can Do Now)
| Task | File | Effort | Impact |
|------|------|--------|--------|
| Zram LZ4 | BoardConfig.mk | 15 min | High |
| Speed-Profile Apps | rk356x_rock_3a_r.mk | 20 min | High |
| TCP BBR | BoardConfig.mk | 10 min | High |
| CPU Freq Limits | kernel config | 30 min | High |
| LMK Tuning | BoardConfig.mk | 20 min | High |
| ART JIT | BoardConfig.mk | 10 min | Medium |
| Read-Ahead | BoardConfig.mk | 10 min | Medium |

**See TODO.md for detailed instructions**

### 3. Performance Validation
- [ ] Measure boot time
- [ ] Measure memory usage
- [ ] Test emulator FPS (RetroArch, PPSSPP, etc.)
- [ ] Check thermal throttling
- [ ] Validate input latency

---

## 📈 Expected Performance Improvements

| Metric | Baseline | Target | Improvement |
|--------|----------|--------|-------------|
| Boot Time | ~45s | ~35-40s | 15-20% faster |
| System Image | ~2.1GB | ~1.8GB | 15% smaller |
| Memory Usage | ~1.2GB | ~1.0GB | 15% lower |
| CPU Jitter | Variable | Lower | Better for emulation |
| App Launch | ~500ms | ~300-400ms | 20-40% faster |
| Emulator FPS | TBD | TBD | TBD |

---

## 🔧 Repository Structure

```
RADXOID/
├── config/                    # Configuration files
│   ├── rock3a.env             # Default config
│   ├── rock3a-lean.env        # Lean config (debloat)
│   └── gpu-drivers.env        # GPU driver config
├── scripts/                   # Build & utility scripts
│   ├── build.sh               # Main build script
│   ├── build-incremental.sh   # Incremental build
│   ├── debloat.sh             # Package removal
│   ├── tune-performance.sh    # Performance tuning
│   ├── validate.sh            # Validation
│   ├── flash-rock3a.sh        # Flash to device
│   ├── verify-gpu.sh          # GPU verification
│   └── ... (10 more scripts)
├── overlay/                   # Overlay files
│   └── radxoid-gpu/           # GPU overlay
├── docs/                      # Documentation
│   ├── ARCH_HOST.md           # Arch Linux setup
│   └── GPU_DRIVER_OVERRIDE.md # GPU driver override
├── .dockerignore              # Docker ignore
├── .gitignore                 # Git ignore
├── Dockerfile                 # Docker builder
├── README.md                  # Main documentation
├── OPTIMIZATIONS.md            # Optimization guide
├── SUMMARY.md                 # Executive summary
├── CHANGELOG.md               # Project history
├── ROADMAP.md                 # Future optimizations
├── TODO.md                    # Immediate tasks
└── STATUS.md                  # This file
```

---

## 📚 Documentation Index

| File | Purpose |
|------|---------|
| **README.md** | Main documentation, build instructions, results |
| **OPTIMIZATIONS.md** | Complete list of all applied optimizations |
| **SUMMARY.md** | Executive summary, metrics, future work |
| **CHANGELOG.md** | Project history, commit details |
| **ROADMAP.md** | Future optimizations, priority matrix |
| **TODO.md** | Immediate action items, quick wins |
| **STATUS.md** | This file - current state reference |
| **docs/ARCH_HOST.md** | Arch Linux host setup |
| **docs/GPU_DRIVER_OVERRIDE.md** | GPU driver override guide |

---

## 🎯 Optimization Categories Summary

### Applied (12 categories)
1. ✅ CPU Governor (SCHEDUTIL)
2. ✅ ART/Dexpreopt (5 apps)
3. ✅ ART JIT (inline=4, codeCache=2MB)
4. ✅ Zram (75% RAM, writeback, swappiness=100)
5. ✅ I/O Scheduler (DEADLINE)
6. ✅ SurfaceFlinger (triple buffer, vsync disabled)
7. ✅ Display (60Hz locked)
8. ✅ Network (buffer sizes, TCP keepalive)
9. ✅ Audio (flinger boost, offload buffer)
10. ✅ CPU Boost (1000ms)
11. ✅ Thermal (CPU 60°C, GPU 55°C)
12. ✅ Kernel CPU (BIG_LITTLE, CPPC, DT, STATS)

### Pending (High ROI)
1. ⬜ Zram LZ4 compression
2. ⬜ Speed-profile for emulator apps
3. ⬜ TCP BBR congestion control
4. ⬜ CPU frequency limits
5. ⬜ LMK tuning
6. ⬜ ART JIT (inline=6, codeCache=4MB)
7. ⬜ Read-ahead size (512KB)
8. ⬜ Zram streams (4)
9. ⬜ SurfaceFlinger vsync test
10. ⬜ GPU frequency scaling

---

## 💡 Common Commands

### Build
```bash
# Full build
./scripts/build.sh

# Incremental
./scripts/build-incremental.sh

# Lean (debloat + tuning)
ROCK3A_ENV=lean ./scripts/build-incremental.sh
```

### Flash
```bash
./scripts/flash-rock3a.sh
```

### Verify
```bash
./scripts/verify-gpu.sh
```

### Debug
```bash
# Check build status
cat source/build-run.log

# Check artifacts
du -sh source/rockdev/Image-rk356x_rock_3a_r/*

# Check out directory size
du -sh source/out
```

---

## ⚠️ Known Issues & Limitations

1. **Android Version**: RK3568 only has official Android 11 support
2. **GPU Driver**: Uses proprietary Mali-G52 driver (Panfrost not production-ready)
3. **Build Time**: Full build takes 2-3 hours on USB HDD
4. **Storage**: Requires 150GB+ for source tree
5. **Testing**: Hardware validation required for GPU, thermals, performance
6. **Zram**: Currently using default compression (LZO), can be optimized to LZ4/ZSTD
7. **Speed-Profile**: Only 5 apps, can be expanded to include emulators

---

## 🤝 Contributing

1. **Pick a task** from TODO.md or ROADMAP.md
2. **Create a branch**: `git checkout -b feat/your-feature`
3. **Make changes**
4. **Test**: Run incremental build, verify changes
5. **Commit**: `git commit -m "feat: description of changes"`
6. **Push**: `git push origin feat/your-feature`
7. **PR**: Open Pull Request with:
   - Description of changes
   - Performance impact
   - Testing results
   - Files modified

---

## 📞 Quick Reference

| Need | Command/File |
|------|--------------|
| Build | `./scripts/build.sh` |
| Incremental Build | `./scripts/build-incremental.sh` |
| Lean Build | `ROCK3A_ENV=lean ./scripts/build-incremental.sh` |
| Flash | `./scripts/flash-rock3a.sh` |
| Verify GPU | `./scripts/verify-gpu.sh` |
| Source Tree | `/run/media/lich/EdgeBKP/radxoid/source` |
| Out Directory | `/run/media/lich/EdgeBKP/radxoid/source/out` |
| Artifacts | `/run/media/lich/EdgeBKP/radxoid/source/rockdev/Image-rk356x_rock_3a_r/` |
| GitHub | https://github.com/rufl/RADXOID |
| Latest Build | 2026-11-19, BUILD_EXIT=0 |
| Latest Commit | 1719435 |

---

## 🎉 Current Status

**🟢 BUILD: SUCCESSFUL**  
**🟢 OPTIMIZATIONS: 12/12 APPLIED**  
**🟢 DEBLOAT: ~70 PACKAGES REMOVED**  
**🟢 DOCUMENTATION: COMPLETE**  
**🟡 HARDWARE TESTING: PENDING**  
**🟡 PERFORMANCE VALIDATION: PENDING**  

---

*Last updated: 2026-11-19*
*Build: RK356X_ROCK_3A_R_USERDEBUG_RK3568-ROCK-3A_ENG.RADXA.20261119.110506*
*Status: Ready for hardware testing and P1 optimizations*
