# RADXOID - Immediate Action Items (TODO)

This file tracks immediate, actionable tasks that can be done right now without hardware access.

---

## 🚀 Quick Wins (Can Do Immediately)

These tasks require only code changes and can be tested with incremental builds.

### 1. Zram Compression Algorithm
**Status**: ⬜ Not Started  
**Priority**: P1 (High ROI)  
**Effort**: 15 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`  

**Task**: Change Zram compression from default to LZ4
```bash
# Add to BoardConfig.mk
BOARD_ZRAM_COMPRESSION := lz4
# or
BOARD_ZRAM_COMPRESSION := zstd
```

**Expected Impact**:
- LZ4: Faster compression/decompression, slightly larger size
- ZSTD: Better compression ratio, slightly slower
- **Recommendation**: Start with LZ4

**Verification**:
```bash
# After boot, check:
cat /proc/sys/vm/zram_compression
```

---

### 2. Expand Speed-Profile Apps
**Status**: ⬜ Not Started  
**Priority**: P1 (High ROI)  
**Effort**: 20 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk`  

**Task**: Add emulator apps to dexpreopt speed-profile
```bash
# Current apps:
# SystemUI, Settings, Launcher3QuickStep, LatinIME, PackageInstaller

# Add:
PRODUCT_DEXPREOPT_SPEED_APPS += \
    com.retroarch \
    org.ppsspp.ppsspp \
    com.dsemulator.drastic \
    org.dolphinemu.dolphinemu \
    com.duckstation \
    org.citra.citra_emu
```

**Expected Impact**:
- Faster emulator launch (20-40% improvement)
- Smoother first-time setup

**Note**: These apps need to be installed for the optimization to take effect.

---

### 3. TCP Congestion Control (BBR)
**Status**: ⬜ Not Started  
**Priority**: P1 (High ROI)  
**Effort**: 10 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`  

**Task**: Change TCP congestion control from cubic to BBR
```bash
# Add to BoardConfig.mk
BOARD_TCP_CONGESTION_CONTROL := bbr
```

**Expected Impact**:
- Better online gaming performance
- Lower latency for network operations
- Better throughput

**Verification**:
```bash
# After boot, check:
cat /proc/sys/net/ipv4/tcp_congestion_control
```

---

### 4. ART JIT Optimizations
**Status**: ⬜ Not Started  
**Priority**: P1 (Medium ROI)  
**Effort**: 10 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`  

**Task**: Increase JIT inline depth and code cache size
```bash
# Add to BoardConfig.mk
BOARD_DALVIK_VM_JIT_INLINE_DEPTH := 6
BOARD_DALVIK_VM_JIT_CODE_CACHE_SIZE := 4m
```

**Expected Impact**:
- Better JIT compilation performance
- More methods inlined
- Larger code cache for complex apps

---

### 5. Read-Ahead Size
**Status**: ⬜ Not Started  
**Priority**: P2 (Medium ROI)  
**Effort**: 10 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`  

**Task**: Increase read-ahead size for better sequential reads
```bash
# Add to BoardConfig.mk
BOARD_READ_AHEAD_KB := 512
```

**Expected Impact**:
- Better sequential read performance
- Improved app launch times
- Better for eMMC/SSD

---

### 6. CPU Frequency Limits
**Status**: ⬜ Not Started  
**Priority**: P1 (High ROI)  
**Effort**: 30 min  
**File**: `kernel/configs/rockchip/rock_3a.config`  

**Task**: Set conservative CPU frequency limits for thermal management
```bash
# Add to kernel config:
CONFIG_CPUFREQ_DT=y
CONFIG_CPUFREQ_STATS=y

# Or set via sysfs in BoardConfig.mk:
BOARD_CPU_MAX_FREQ := 1800000  # 1.8GHz max
BOARD_CPU_MIN_FREQ := 408000  # 408MHz min
```

**Expected Impact**:
- Prevents thermal throttling
- Better sustained performance
- Lower power consumption

**Note**: RK3568 has 4x Cortex-A55 @ 2.0GHz max. Conservative limit prevents overheating.

---

### 7. LMK (Low Memory Killer) Tuning
**Status**: ⬜ Not Started  
**Priority**: P1 (High ROI)  
**Effort**: 20 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`  

**Task**: Adjust LMK thresholds for gaming workload
```bash
# Add to BoardConfig.mk
BOARD_LMK_CRITICAL_THRESHOLD := 150
BOARD_LMK_LOW_THRESHOLD := 300
BOARD_LMK_MEDIUM_THRESHOLD := 600
BOARD_LMK_HIGH_THRESHOLD := 1024
```

**Expected Impact**:
- Prevents OOM kills during emulation
- Better memory management
- More aggressive killing of background apps

**Note**: Values in MB. Adjust based on device RAM (ROCK 3A has 4GB/8GB variants).

---

### 8. Zram Streams
**Status**: ⬜ Not Started  
**Priority**: P2 (Medium ROI)  
**Effort**: 10 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`  

**Task**: Increase Zram streams for better parallel compression
```bash
# Add to BoardConfig.mk
BOARD_ZRAM_STREAMS := 4
```

**Expected Impact**:
- Better parallel compression performance
- Improved multi-core utilization

---

### 9. SurfaceFlinger Vsync Test
**Status**: ⬜ Not Started  
**Priority**: P2 (Medium ROI)  
**Effort**: 15 min  
**File**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`  

**Task**: Test vsync enabled vs disabled
```bash
# Current: vsync disabled (experimental)
# Try enabling it:
# Remove or comment out:
# BOARD_SURFACEFLINGER_VSYNC := false

# Or test both and compare
```

**Expected Impact**:
- Vsync enabled: Smoother rendering, potential input lag
- Vsync disabled: Lower latency, potential tearing
- **Recommendation**: Test both and choose based on use case

---

### 10. Build System Optimization
**Status**: ⬜ Not Started  
**Priority**: P2 (Medium ROI)  
**Effort**: 30 min  
**File**: `scripts/build.sh`  

**Task**: Increase parallel jobs for faster builds
```bash
# In build.sh, find the make command and add:
-j$(nproc --all) \
```

**Expected Impact**:
- Faster incremental builds
- Better CPU utilization

**Note**: USB HDD may be bottleneck. Monitor I/O wait.

---

## 📋 Implementation Checklist

### For Each Task:
- [ ] Read relevant documentation
- [ ] Identify exact file and line to change
- [ ] Make minimal, targeted change
- [ ] Test with incremental build
- [ ] Verify change is applied
- [ ] Commit with descriptive message
- [ ] Update documentation

---

## 🔄 Incremental Build Workflow

For testing these changes:

```bash
# 1. Make your changes to the appropriate files
nano device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk

# 2. Run incremental build
./scripts/build-incremental.sh

# Or for lean flavor:
ROCK3A_ENV=lean ./scripts/build-incremental.sh

# 3. Check build status
# If BUILD_EXIT=0, build succeeded

# 4. Flash and test (when hardware available)
./scripts/flash-rock3a.sh
./scripts/verify-gpu.sh
```

---

## 🎯 Recommended Order

Based on ROI and effort, implement in this order:

1. **Zram LZ4** (15 min, High ROI)
2. **Speed-Profile Apps** (20 min, High ROI)
3. **TCP BBR** (10 min, High ROI)
4. **CPU Frequency Limits** (30 min, High ROI)
5. **LMK Tuning** (20 min, High ROI)
6. **ART JIT** (10 min, Medium ROI)
7. **Read-Ahead** (10 min, Medium ROI)
8. **Zram Streams** (10 min, Medium ROI)
9. **SurfaceFlinger Vsync** (15 min, Medium ROI)
10. **Build Parallel Jobs** (30 min, Medium ROI)

**Total Estimated Time**: ~3 hours (can be done incrementally)

---

## 📊 Expected Results

| Optimization | Boot Time | App Launch | Memory | CPU Jitter | Network |
|--------------|-----------|------------|--------|------------|---------|
| Zram LZ4 | - | + | + | - | - |
| Speed-Profile | + | ++ | - | - | - |
| TCP BBR | - | - | - | - | ++ |
| CPU Freq Limits | - | - | - | ++ | - |
| LMK Tuning | - | - | ++ | - | - |
| ART JIT | - | + | - | - | - |
| Read-Ahead | + | + | - | - | - |

**Legend**: `--` = No impact, `-` = Small improvement, `+` = Medium improvement, `++` = Large improvement

---

## 💡 Tips

1. **Test one change at a time** - Easier to identify impact
2. **Document results** - Record before/after metrics
3. **Use git branches** - Keep changes isolated
4. **Small commits** - One optimization per commit
5. **Update documentation** - Keep docs in sync with code

---

## 📝 Change Log

Use this format to track completed tasks:

```
### [Date] - Task Name
- **Status**: ✅ Completed
- **Changes**: Description of changes
- **Files**: List of modified files
- **Results**: Measured impact
- **Commit**: commit-hash
```

---

## 🎉 Next Steps After These Tasks

Once these quick wins are implemented:

1. **Hardware Testing** - Flash and test on actual ROCK 3A
2. **Performance Benchmarking** - Measure actual impact
3. **P1 Optimizations** - Move to higher-effort, high-ROI tasks
4. **Documentation** - Update docs with results

---

*Last updated: 2026-11-19*
*Status: Ready for implementation*
