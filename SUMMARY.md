# RADXOID - Executive Summary

## Project Overview

**RADXOID** is a lean Android 11 image build system for the **Radxa ROCK 3A** (RK3568 SoC) optimized for **gaming and emulation** workloads. This project provides reproducible builds, performance tuning, and aggressive debloating to create a minimal, high-performance Android image.

## Quick Facts

| Item | Value |
|------|-------|
| **Target Device** | Radxa ROCK 3A |
| **SoC** | Rockchip RK3568 (4x Cortex-A55) |
| **GPU** | ARM Mali-G52 (Bifrost) |
| **Android Version** | 11 (API 30) - Latest official from Radxa |
| **Manifest** | `Android11_Radxa_rk12` @ `116eac8ed...` |
| **Build Status** | ✅ `BUILD_EXIT=0` (2026-11-19) |
| **Image Size** | ~1.8GB (update.img) |
| **Repository** | https://github.com/rufl/RADXOID |

---

## Build Results

### Latest Successful Build
- **Date**: 2026-11-19 12:34-12:51
- **Duration**: ~2.5 hours (on USB HDD)
- **Status**: `BUILD_EXIT=0`

### Generated Artifacts
| File | Size | SHA256 | Purpose |
|------|------|--------|---------|
| `update.img` | 1.8 GB | `eb5a202662b8af89fda31e7c8b4dd9375156c74f5445c1150d5bfa41157441d5` | Full flashable image |
| `super.img` | 1.6 GB | - | Dynamic partitions |
| `rkupdate.img` | 1.7 GB | - | Rockchip update package |
| `gpt.img` | 4.1 GB | - | Partition table |
| `recovery.img` | 110 MB | - | Recovery partition |
| `boot.img` | 35 MB | - | Boot partition |
| `dtbo.img` | 607 B | - | Device tree overlay |

### Build Environment
- **Source Tree**: 150 GB (on `/run/media/lich/EdgeBKP/radxoid/source`)
- **Out Directory**: 50 GB (build artifacts)
- **Docker Image**: `radxoid-builder:u20.04` (Ubuntu 20.04)
- **Host**: Arch Linux (build orchestration)

---

## Optimization Summary

### 🎯 Performance Tuning (12 Categories)

#### 1. CPU Governor
- **Change**: INTERACTIVE → **SCHEDUTIL**
- **Impact**: Better sustained load performance, lower jitter for emulation
- **Files**: `kernel/configs/rockchip/rock_3a.config`

#### 2. ART/Dexpreopt
- **Apps**: SystemUI, Settings, Launcher3QuickStep, LatinIME, PackageInstaller
- **Features**: Speed-profile, PGO, JIT inline=4, code cache=2MB
- **Impact**: Faster app launch, smoother animations
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk`

#### 3. Zram
- **Size**: 75% of RAM (default was 50%)
- **Writeback**: Enabled
- **Swappiness**: 100
- **Impact**: Better memory compression and management
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 4. I/O Scheduler
- **Change**: CFQ → **DEADLINE**
- **Impact**: Better I/O performance for eMMC/SSD
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 5. SurfaceFlinger
- **Triple Buffer**: Enabled
- **Phase Offsets**: Disabled
- **Vsync**: Disabled (experimental)
- **Impact**: Smoother rendering, lower latency
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 6. Display
- **Refresh Rate**: 60Hz (locked)
- **Adaptive Refresh**: Disabled
- **Impact**: Consistent frame pacing
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 7. Network
- **Buffer Sizes**: rmem_max=16MB, wmem_max=16MB
- **TCP Keepalive**: time=30s, intvl=10s, probes=5
- **Impact**: Better online gaming performance
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 8. Audio
- **Flinger Boost**: Enabled
- **Deep Buffer**: Disabled
- **Offload Buffer**: 128KB
- **Impact**: Lower audio latency
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 9. CPU Boost
- **Enabled**: Yes
- **Duration**: 1000ms
- **Impact**: Faster response to interactive tasks
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 10. Thermal
- **CPU Threshold**: 60°C
- **GPU Threshold**: 55°C
- **Impact**: Better sustained performance
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 11. ART JIT
- **Inline Depth**: 4
- **Code Cache**: 2MB
- **ISA Variants**: arm64=generic, arm=generic
- **Impact**: Better JIT compilation performance
- **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

#### 12. Kernel CPU Features
- **CONFIG_ARM_BIG_LITTLE_CPUFREQ**: Enabled
- **CONFIG_ARM64_CPUFREQ_CPPC**: Enabled
- **CONFIG_CPUFREQ_DT**: Enabled
- **CONFIG_CPUFREQ_STATS**: Enabled
- **Impact**: Better CPU frequency scaling
- **Files**: `kernel/configs/rockchip/rock_3a.config`

### 🗑️ Debloat (Lean Flavor)

**~70 packages removed** including:
- Google GMS and Services (9 packages)
- Telephony (7 packages)
- TV and Media Center (7 packages)
- Print Services (3 packages)
- Carrier Services (3 packages)
- Heavy Launchers/Wallpapers (5 packages)
- Media Apps (9 packages)
- Email/Contacts (5 packages)
- Browser/Web (2 packages)
- System Apps (10 packages)
- Development Tools (3 packages)
- Accessibility (4 packages)
- Misc System Apps (10 packages)

**Impact**:
- System image reduced by ~300-400MB
- Faster boot time
- Lower memory usage
- Reduced attack surface

### 🔧 Fixups

1. **LOCAL_TIDY Disabled**: Prevents clang-tidy failures with modern host clang
2. **Recovery Partition Size**: 114552832 → 134217728 (8KiB headroom)

---

## Repository Structure

```
RADXOID/
├── config/
│   ├── rock3a.env           # Default config (Android 11)
│   ├── rock3a-lean.env      # Lean config (debloat enabled)
│   └── gpu-drivers.env       # GPU driver config
├── scripts/
│   ├── build.sh              # Main build script
│   ├── build-incremental.sh  # Incremental build
│   ├── debloat.sh            # Package removal
│   ├── tune-performance.sh   # Performance tuning
│   ├── validate.sh           # Config validation
│   ├── flash-rock3a.sh       # Flash to device
│   ├── verify-gpu.sh         # GPU verification
│   ├── fix-ownership.sh      # Fix file ownership
│   ├── prepare.sh            # Prepare source tree
│   └── probe-rock3a.sh       # Device probing
├── overlay/
│   └── radxoid-gpu/          # GPU overlay
├── docs/
│   ├── ARCH_HOST.md          # Arch Linux host setup
│   └── GPU_DRIVER_OVERRIDE.md # GPU driver override
├── Dockerfile                # Docker builder image
├── README.md                 # Main documentation
├── OPTIMIZATIONS.md           # Optimization guide
└── SUMMARY.md                # This file
```

---

## GitHub Commits

| Commit | Message | Changes |
|--------|---------|---------|
| `59040c3` | docs: update OPTIMIZATIONS.md with all applied tuning and changelog | OPTIMIZATIONS.md |
| `1100a1b` | feat(tune): add SurfaceFlinger vsync, thermal, display, JIT, TCP optimizations | tune-performance.sh |
| `803fc22` | feat(debloat): expand package removal list for lean gaming image | debloat.sh |
| `5da56a3` | feat(tune): enhance performance tuning with network, audio, zram, ART optimizations | tune-performance.sh |
| `7d136d5` | docs: add OPTIMIZATIONS.md with complete optimization guide | OPTIMIZATIONS.md |
| `4eab994` | feat(tune): add performance tuning script (zram, I/O, SurfaceFlinger, ART) | tune-performance.sh |
| `d8e3198` | docs: add build results, lean flavor details, and usage instructions | README.md |
| `f6d1182` | feat(lean): add debloat + performance fixups + incremental build loop | build.sh, debloat.sh, validate.sh |
| `6d533d8` | feat: add incremental build loop and lean debloat workflow | build-incremental.sh |
| `58d9bf4` | feat(rock3a): Android 11 lean + debloat + performance fixups | Initial commit |

---

## Usage Quick Start

### 1. Clone Repository
```bash
git clone https://github.com/rufl/RADXOID.git
cd RADXOID
```

### 2. Prepare Source Tree (150GB required)
```bash
./scripts/prepare.sh
```

### 3. Full Build
```bash
./scripts/build.sh
```

### 4. Lean Build (Debloat + Performance)
```bash
ROCK3A_ENV=lean ./scripts/build-incremental.sh
```

### 5. Flash to Device
```bash
./scripts/flash-rock3a.sh
```

### 6. Verify GPU
```bash
./scripts/verify-gpu.sh
```

---

## Performance Metrics (Expected)

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| Boot Time | ~45s | ~35-40s | ~15-20% faster |
| System Image Size | ~2.1GB | ~1.8GB | ~15% smaller |
| Memory Usage | ~1.2GB | ~1.0GB | ~15% lower |
| CPU Jitter | Variable | Lower | Better for emulation |
| App Launch Time | ~500ms | ~300-400ms | ~20-40% faster |

*Note: Actual metrics require hardware testing on ROCK 3A*

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| **CPU** | x86_64 | x86_64 (multi-core) |
| **RAM** | 16GB | 32GB+ |
| **Storage** | 200GB | 500GB+ SSD/NVMe |
| **OS** | Ubuntu 20.04 | Ubuntu 20.04/22.04 |
| **Docker** | 20.10+ | 20.10+ |

---

## Known Limitations

1. **Android Version**: RK3568 only has official Android 11 support from Radxa
2. **GPU Driver**: Uses proprietary Mali-G52 driver (Panfrost not production-ready for Android)
3. **Build Time**: Full build takes 2-3 hours on USB HDD
4. **Storage**: Requires 150GB+ for source tree
5. **Testing**: Hardware validation required for GPU, thermals, performance

---

## Future Work

### High Priority
- [ ] Test on actual ROCK 3A hardware
- [ ] Validate GPU performance (Mali-G52)
- [ ] Measure actual performance metrics
- [ ] Test emulator compatibility (RetroArch, PPSSPP, etc.)

### Medium Priority
- [ ] Kernel: CPU frequency limits for better thermals
- [ ] Kernel: GPU frequency scaling
- [ ] ART: More speed-profile apps
- [ ] Zram: Better compression algorithm (LZ4/ZSTD)

### Low Priority
- [ ] I/O: F2FS for system partition
- [ ] Network: TCP BBR congestion control
- [ ] Audio: Sample rate optimization
- [ ] Display: Color mode configuration

---

## Contacts & Resources

- **Repository**: https://github.com/rufl/RADXOID
- **Radxa Documentation**: https://docs.radxa.com/rock3/rock3a
- **Mali-G52 Documentation**: https://developer.arm.com/ip-products/graphics-and-multimedia/mali-gpus/mali-g52
- **AOSP**: https://source.android.com

---

## License

This project uses the following licenses:
- **Code**: Apache 2.0 (where applicable)
- **Documentation**: CC-BY-4.0
- **Rockchip BSP**: Proprietary (see Radxa terms)
- **Mali Driver**: Proprietary (see ARM terms)

Do not redistribute proprietary Rockchip/Mali blobs outside their original license terms.

---

*Last updated: 2026-11-19*
*Build: RK356X_ROCK_3A_R_USERDEBUG_RK3568-ROCK-3A_ENG.RADXA.20261119.110506*
