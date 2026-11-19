# RADXOID - Roadmap & Future Optimizations

This document outlines the planned optimizations, features, and improvements for the RADXOID project, organized by priority and ROI (Return on Investment).

---

## 🎯 Priority Matrix

| Priority | ROI | Effort | Description |
|----------|-----|--------|-------------|
| **P0** | High | Low | Critical fixes, build reliability |
| **P1** | High | Medium | High-impact optimizations, hardware validation |
| **P2** | Medium | Medium | Nice-to-have improvements |
| **P3** | Low | High | Experimental, research, low-impact |

---

## 🚀 P0 - Critical (Must Do)

### Hardware Validation
- [ ] **Test on actual ROCK 3A hardware**
  - Flash `update.img` using `./scripts/flash-rock3a.sh`
  - Verify boot and basic functionality
  - Check ADB connectivity
  - **ROI**: High - Validates entire build process
  - **Effort**: Medium (requires physical device)

- [ ] **GPU Verification**
  - Run `./scripts/verify-gpu.sh`
  - Verify Mali-G52 driver is loaded
  - Test GPU rendering (GLMark2, etc.)
  - **ROI**: High - Critical for gaming/emulation
  - **Effort**: Low

- [ ] **Basic Performance Metrics**
  - Measure boot time
  - Measure memory usage
  - Test app launch times
  - **ROI**: High - Establishes baseline
  - **Effort**: Low

---

## 🎮 P1 - High Priority (High ROI)

### Kernel Optimizations

#### CPU Frequency & Thermal
- [ ] **CPU Frequency Limits**
  - Set max frequency based on thermal thresholds
  - Implement dynamic frequency scaling
  - **Config**: `kernel/configs/rockchip/rock_3a.config`
  - **ROI**: High - Prevents thermal throttling
  - **Effort**: Medium
  - **Files**: `device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk`

- [ ] **GPU Frequency Scaling**
  - Enable GPU frequency scaling if available
  - Set conservative limits for thermal management
  - **Config**: Mali-G52 driver parameters
  - **ROI**: High - Better GPU performance
  - **Effort**: Medium
  - **Note**: May require proprietary driver modifications

- [ ] **Thermal Engine Tuning**
  - Adjust thermal thresholds (currently CPU 60°C, GPU 55°C)
  - Implement gradual throttling instead of hard limits
  - **ROI**: High - Better sustained performance
  - **Effort**: Medium

#### CPU Governor Advanced
- [ ] **SCHEDUTIL Fine-Tuning**
  - Adjust `up_rate_limit_us` and `down_rate_limit_us`
  - Tune `hispeed_freq` and `hispeed_load`
  - **ROI**: Medium - Better responsiveness
  - **Effort**: Low
  - **Config**: Kernel command line or sysfs

- [ ] **CPU Affinity**
  - Set CPU affinity for foreground apps
  - Reserve big cores for gaming/emulation
  - **ROI**: Medium - Better performance for critical tasks
  - **Effort**: Medium

### Memory Optimizations

- [ ] **Zram Compression Algorithm**
  - Switch from default to **LZ4** or **ZSTD**
  - **ROI**: High - Better compression ratio/speed tradeoff
  - **Effort**: Low
  - **Config**: `ro.config.zram_compression` or kernel parameter
  - **Current**: Default (likely LZO)
  - **Target**: LZ4 (faster) or ZSTD (better ratio)

- [ ] **Zram Streams**
  - Increase from default (2) to 4-8
  - **ROI**: Medium - Better parallel compression
  - **Effort**: Low
  - **Config**: `num_streams` parameter

- [ ] **Zram Max Compression Size**
  - Adjust based on workload
  - **ROI**: Low - Fine-tuning
  - **Effort**: Low

- [ ] **Low Memory Killer (LMK) Tuning**
  - Adjust minfree values for gaming workload
  - Prevent OOM kills during emulation
  - **ROI**: High - Prevents crashes
  - **Effort**: Medium
  - **Config**: `ro.lmk.*` properties

### ART & Dexpreopt

- [ ] **Expand Speed-Profile Apps**
  - Add more frequently used apps:
    - RetroArch
    - PPSSPP
    - Drastic
    - Dolphin
    - DuckStation
    - Citra
  - **ROI**: High - Faster emulator launch
  - **Effort**: Low
  - **File**: `device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk`

- [ ] **Profile-Guided Optimization (PGO)**
  - Collect profiles from actual usage
  - Apply PGO to more apps
  - **ROI**: Medium - Better performance
  - **Effort**: High (requires usage data)

- [ ] **ART JIT Optimizations**
  - Increase `jit.inline_depth` from 4 to 6-8
  - Increase `jit.code_cache_size` from 2MB to 4MB
  - **ROI**: Medium - Better JIT performance
  - **Effort**: Low
  - **Config**: `dalvik.vm.jit.*` properties

### I/O Optimizations

- [ ] **I/O Scheduler Fine-Tuning**
  - Test **FIOPS** vs DEADLINE vs CFQ
  - Adjust scheduler parameters
  - **ROI**: Medium - Better I/O performance
  - **Effort**: Medium

- [ ] **Read-Ahead Size**
  - Increase from default (128KB) to 512KB-1MB
  - **ROI**: Medium - Better sequential reads
  - **Effort**: Low
  - **Config**: `/sys/block/*/queue/read_ahead_kb`

- [ ] **I/O Priority**
  - Set higher priority for foreground apps
  - **ROI**: Medium - Better responsiveness
  - **Effort**: Medium

### Graphics Optimizations

- [ ] **SurfaceFlinger Optimizations**
  - Test **vsync enabled** vs disabled
  - Adjust frame buffer count
  - **ROI**: Medium - Better rendering
  - **Effort**: Medium

- [ ] **GPU Renderer**
  - Test **Skia** vs **OpenGL** vs **Vulkan**
  - **ROI**: Medium - Better graphics performance
  - **Effort**: High

- [ ] **Hardware Acceleration**
  - Ensure all codecs are hardware-accelerated
  - **ROI**: Medium - Better video playback
  - **Effort**: Medium

### Network Optimizations

- [ ] **TCP Congestion Control**
  - Switch from **cubic** to **BBR**
  - **ROI**: Medium - Better online gaming
  - **Effort**: Low
  - **Config**: `net.ipv4.tcp_congestion_control`

- [ ] **Buffer Sizes**
  - Fine-tune `rmem_max`, `wmem_max`
  - **ROI**: Low - Fine-tuning
  - **Effort**: Low

### Emulator-Specific Optimizations

- [ ] **RetroArch**
  - Pre-configure for RK3568
  - Set optimal core configurations
  - **ROI**: High - Better emulation performance
  - **Effort**: Medium

- [ ] **PPSSPP**
  - Configure for Mali-G52
  - Set optimal resolution scaling
  - **ROI**: High - Better PSP emulation
  - **Effort**: Medium

- [ ] **Drastic**
  - Configure for RK3568
  - **ROI**: Medium - Better DS emulation
  - **Effort**: Low

---

## 🎨 P2 - Medium Priority (Medium ROI)

### System Optimizations

- [ ] **Init.d Scripts**
  - Add performance scripts to `/system/etc/init.d/`
  - Apply tuning on boot
  - **ROI**: Medium - Persistent tuning
  - **Effort**: Medium

- [ ] **Build.prop Tweaks**
  - Add performance-related properties
  - **ROI**: Medium - System-wide improvements
  - **Effort**: Low

- [ ] **SELinux Permissive**
  - Set to permissive mode for debugging
  - **ROI**: Low - Debugging only
  - **Effort**: Low
  - **Warning**: Security implications

### Audio Optimizations

- [ ] **Audio Buffer Size**
  - Reduce from 128KB to 64KB
  - **ROI**: Medium - Lower audio latency
  - **Effort**: Low

- [ ] **Sample Rate**
  - Force 48KHz for consistency
  - **ROI**: Low - Better compatibility
  - **Effort**: Low

### Display Optimizations

- [ ] **Color Mode**
  - Set to **Natural** or **Vivid**
  - **ROI**: Low - Visual preference
  - **Effort**: Low

- [ ] **Refresh Rate**
  - Test 30Hz vs 60Hz for battery life
  - **ROI**: Low - Battery optimization
  - **Effort**: Low

### Build System Optimizations

- [ ] **CCACHE Optimization**
  - Increase cache size
  - Configure for better hit rate
  - **ROI**: Medium - Faster rebuilds
  - **Effort**: Low

- [ ] **Parallel Jobs**
  - Increase `-j` parameter
  - **ROI**: Medium - Faster builds
  - **Effort**: Low

- [ ] **Distributed Building**
  - Set up build farm
  - **ROI**: Low - Faster builds (high effort)
  - **Effort**: High

### Documentation

- [ ] **Hardware Testing Guide**
  - Document testing procedures
  - **ROI**: Medium - Better reproducibility
  - **Effort**: Medium

- [ ] **Performance Benchmarking**
  - Document benchmark results
  - **ROI**: Medium - Better understanding
  - **Effort**: Medium

- [ ] **Troubleshooting Guide**
  - Document common issues and solutions
  - **ROI**: Medium - Better support
  - **Effort**: Medium

---

## 🔬 P3 - Low Priority (Experimental)

### Kernel Experiments

- [ ] **Custom Kernel**
  - Build custom kernel with additional optimizations
  - **ROI**: Low - High effort, uncertain benefits
  - **Effort**: High

- [ ] **Overclocking**
  - Test CPU/GPU overclocking
  - **ROI**: Low - Thermal issues likely
  - **Effort**: High
  - **Warning**: May cause instability

- [ ] **Undervolting**
  - Test CPU/GPU undervolting
  - **ROI**: Low - Power savings, potential instability
  - **Effort**: High

### Alternative GPU Drivers

- [ ] **Panfrost (Open Source)**
  - Test open-source Mali driver
  - **ROI**: Low - Experimental, may not work well
  - **Effort**: High
  - **Note**: Not production-ready for Android

- [ ] **Mesa**
  - Test Mesa for OpenGL/Vulkan
  - **ROI**: Low - Experimental
  - **Effort**: High

### Alternative Android Versions

- [ ] **Android 12+ Port**
  - Attempt to port to newer Android version
  - **ROI**: Low - No official support, high effort
  - **Effort**: Very High
  - **Note**: RK3568 has no official Android 12+ support

- [ ] **LineageOS**
  - Test LineageOS for RK3568
  - **ROI**: Low - May not have GPU drivers
  - **Effort**: High

### Advanced Features

- [ ] **Root Access**
  - Enable root access for advanced tuning
  - **ROI**: Low - Security implications
  - **Effort**: Medium

- [ ] **Custom Recovery**
  - Build custom recovery (TWRP)
  - **ROI**: Low - Nice to have
  - **Effort**: High

- [ ] **OTA Updates**
  - Set up OTA update system
  - **ROI**: Low - Nice to have
  - **Effort**: High

---

## 📊 Implementation Timeline

### Phase 1: Hardware Validation (Week 1)
- [ ] Test on ROCK 3A hardware
- [ ] Verify GPU
- [ ] Measure baseline performance
- [ ] Document results

### Phase 2: High-ROI Optimizations (Week 2-3)
- [ ] CPU frequency limits
- [ ] GPU frequency scaling
- [ ] Zram LZ4/ZSTD
- [ ] Expand speed-profile apps
- [ ] LMK tuning

### Phase 3: Medium-ROI Optimizations (Week 4-6)
- [ ] SCHEDUTIL fine-tuning
- [ ] TCP BBR
- [ ] Init.d scripts
- [ ] Build.prop tweaks
- [ ] Emulator configurations

### Phase 4: Documentation & Polish (Week 7-8)
- [ ] Hardware testing guide
- [ ] Performance benchmarking
- [ ] Troubleshooting guide
- [ ] Final validation

---

## 🎯 Quick Wins (Can Do Now)

These optimizations can be implemented immediately with minimal effort:

1. **Zram LZ4**: Change compression algorithm in BoardConfig.mk
2. **Speed-Profile Apps**: Add emulator apps to dexpreopt list
3. **TCP BBR**: Change congestion control in BoardConfig.mk
4. **ART JIT**: Increase inline_depth and code_cache_size
5. **Read-Ahead**: Increase read_ahead_kb in BoardConfig.mk

---

## 📝 Implementation Notes

### Testing Methodology
1. **Before**: Measure baseline performance
2. **After**: Measure performance with optimization
3. **Compare**: Verify improvement
4. **Document**: Record results

### Validation Checklist
- [ ] Build succeeds (`BUILD_EXIT=0`)
- [ ] Device boots
- [ ] ADB works
- [ ] GPU detected
- [ ] Performance improved
- [ ] No regressions

### Rollback Plan
- Keep git history clean
- Use feature branches
- Test before merging to main
- Document breaking changes

---

## 💡 Optimization Ideas (Brainstorm)

### Power Management
- Dynamic CPU/GPU frequency based on workload
- Aggressive power saving when idle
- Performance mode when gaming

### Thermal Management
- Predictive thermal throttling
- Workload-based thermal limits
- Fan control (if available)

### Storage Optimization
- F2FS for system partition
- Compression for system apps
- Deduplication

### Network
- QoS for gaming traffic
- DNS caching
- Connection pooling

### Security
- SELinux hardening
- App sandboxing
- Permission management

---

## 📚 Resources

- [Android Performance Patterns](https://developer.android.com/topic/performance/patterns)
- [Kernel Documentation](https://www.kernel.org/doc/html/latest/)
- [Rockchip Documentation](https://docs.radxa.com/)
- [Mali GPU Documentation](https://developer.arm.com/ip-products/graphics-and-multimedia/mali-gpus)

---

## 🤝 Contributing

If you want to contribute to any of these optimizations:

1. **Pick an item** from the roadmap
2. **Create a branch** for your changes
3. **Implement** the optimization
4. **Test** thoroughly
5. **Document** your changes
6. **Open a PR** with:
   - Description of changes
   - Performance impact
   - Testing results
   - Any limitations

---

*Last updated: 2026-11-19*
*Status: Ready for hardware testing and P1 optimizations*
