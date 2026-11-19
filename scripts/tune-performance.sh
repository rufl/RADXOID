#!/usr/bin/env bash
set -euo pipefail

# Performance tuning for ROCK 3A Android 11 lean image.
# Applies kernel config, build props, and device.mk tweaks for gaming/emulation.
# Idempotent: re-running leaves one marker block.

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
# shellcheck source=../config/rock3a.env
source "${ROOT_DIR}/config/rock3a.env"

: "${SOURCE_DIR:=${ROOT_DIR}/source}"
case "${SOURCE_DIR}" in
  /*) ;;
  *) SOURCE_DIR="${ROOT_DIR}/${SOURCE_DIR}" ;;
esac

cd "${SOURCE_DIR}"

# ============================================================
# 1. Kernel: CPU Governor and Frequency Scaling
# ============================================================
kcfg="${SOURCE_DIR}/kernel/configs/rockchip/rock_3a.config"
if [[ -f "${kcfg}" ]]; then
  # SCHEDUTIL governor - better for sustained load, lower jitter
  if ! grep -q '^CONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y$' "${kcfg}"; then
    printf '\nCONFIG_SCHED_SCHEDUTIL=y\nCONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y\n' >> "${kcfg}"
    echo "tune: kernel governor -> SCHEDUTIL"
  fi
  # Enable CPU frequency scaling drivers
  if ! grep -q '^CONFIG_CPUFREQ_DT=y$' "${kcfg}"; then
    echo "CONFIG_CPUFREQ_DT=y" >> "${kcfg}"
    echo "tune: CPUFREQ_DT enabled"
  fi
  # Enable CPU freq stats for debugging
  if ! grep -q '^CONFIG_CPUFREQ_STATS=y$' "${kcfg}"; then
    echo "CONFIG_CPUFREQ_STATS=y" >> "${kcfg}"
    echo "tune: CPUFREQ_STATS enabled"
  fi
  # Enable CPU frequency scaling for all CPUs
  if ! grep -q '^CONFIG_GENERIC_CPUFREQ_CPU0=y$' "${kcfg}"; then
    echo "CONFIG_GENERIC_CPUFREQ_CPU0=y" >> "${kcfg}"
    echo "tune: GENERIC_CPUFREQ_CPU0 enabled"
  fi
  # Enable CPU frequency scaling stats in sysfs
  if ! grep -q '^CONFIG_CPUFREQ_STATS=y$' "${kcfg}"; then
    echo "CONFIG_CPUFREQ_STATS=y" >> "${kcfg}"
    echo "tune: CPUFREQ_STATS already enabled"
  fi
  # Enable CPU frequency scaling for big.LITTLE (RK3568 has 4x Cortex-A55)
  if ! grep -q '^CONFIG_ARM_BIG_LITTLE_CPUFREQ=y$' "${kcfg}"; then
    echo "CONFIG_ARM_BIG_LITTLE_CPUFREQ=y" >> "${kcfg}"
    echo "tune: ARM_BIG_LITTLE_CPUFREQ enabled"
  fi
  # Enable CPU frequency scaling for ARM64
  if ! grep -q '^CONFIG_ARM64_CPUFREQ_CPPC=y$' "${kcfg}"; then
    echo "CONFIG_ARM64_CPUFREQ_CPPC=y" >> "${kcfg}"
    echo "tune: ARM64_CPUFREQ_CPPC enabled"
  fi
fi

# ============================================================
# 2. ART/dexpreopt: speed-profile for boot-critical + common apps
# ============================================================
dmk="${SOURCE_DIR}/device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk"
if [[ -f "${dmk}" ]]; then
  if ! grep -q '^PRODUCT_DEXPREOPT_SPEED_APPS' "${dmk}"; then
    printf '\nPRODUCT_DEXPREOPT_SPEED_APPS += \\\n    SystemUI \\\n    Settings \\\n    Launcher3QuickStep \\\n    LatinIME \\\n    PackageInstaller\n' >> "${dmk}"
    echo "tune: dexpreopt speed-profile applied (5 apps)"
  fi
  # Enable profile-guided optimization for speed apps
  if ! grep -q '^PRODUCT_DEXPREOPT_PROFILE_GUIDED_OPTIMIZATION' "${dmk}"; then
    echo "PRODUCT_DEXPREOPT_PROFILE_GUIDED_OPTIMIZATION := true" >> "${dmk}"
    echo "tune: PGO enabled for dexpreopt"
  fi
  # Use speed profile for all speed apps (faster launch)
  if ! grep -q '^PRODUCT_DEXPREOPT_SPEED_APPS_FILTER' "${dmk}"; then
    echo "PRODUCT_DEXPREOPT_SPEED_APPS_FILTER := speed-profile" >> "${dmk}"
    echo "tune: speed-profile filter applied"
  fi
  # Enable dexpreopt for all apps (not just speed)
  if ! grep -q '^WITH_DEXPREOPT' "${dmk}"; then
    echo "WITH_DEXPREOPT := true" >> "${dmk}"
    echo "tune: dexpreopt enabled for all apps"
  fi
fi

# ============================================================
# 3. Build props: zram, swappiness, I/O scheduler
# ============================================================
bcfg="${SOURCE_DIR}/device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk"
if [[ -f "${bcfg}" ]]; then
  # Zram is already enabled by default in Rockchip device.mk
  # Ensure swappiness is set for better memory management
  if ! grep -q 'ro.config.swappiness' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.config.swappiness=100" >> "${bcfg}"
    echo "tune: swappiness=100"
  fi
  # I/O scheduler: deadline for eMMC/SSD
  if ! grep -q 'ro.iostat.scheduler' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.iostat.scheduler=deadline" >> "${bcfg}"
    echo "tune: I/O scheduler -> deadline"
  fi
  # Zram: increase size for better compression (default is 50% of RAM)
  if ! grep -q 'ro.config.zram_size' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.config.zram_size=75" >> "${bcfg}"
    echo "tune: zram size -> 75% of RAM"
  fi
  # Zram: mark idle delay (already set in common device.mk, but ensure)
  if ! grep -q 'ro.zram.mark_idle_delay_mins' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.zram.mark_idle_delay_mins=60" >> "${bcfg}"
    echo "tune: zram mark idle delay = 60min"
  fi
  # Zram: enable writeback for better performance
  if ! grep -q 'ro.config.zram_writeback' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.config.zram_writeback=1" >> "${bcfg}"
    echo "tune: zram writeback enabled"
  fi
fi

# ============================================================
# 4. SurfaceFlinger: triple buffer + phase offsets
# ============================================================
if [[ -f "${bcfg}" ]]; then
  if ! grep -q 'ro.sys.sf.use_triple_buffer' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.sys.sf.use_triple_buffer=1" >> "${bcfg}"
    echo "tune: SurfaceFlinger triple buffer enabled"
  fi
  if ! grep -q 'ro.sys.sf.use_phase_offsets' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.sys.sf.use_phase_offsets=0" >> "${bcfg}"
    echo "tune: SurfaceFlinger phase offsets disabled"
  fi
  # Disable vsync for lower latency (experimental)
  if ! grep -q 'ro.sys.sf.vsync' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.sys.sf.vsync=0" >> "${bcfg}"
    echo "tune: SurfaceFlinger vsync disabled (experimental)"
  fi
fi

# ============================================================
# 5. ART runtime: ISA variants for RK3568 (Cortex-A55)
# ============================================================
if [[ -f "${bcfg}" ]]; then
  if ! grep -q 'dalvik.vm.isa.arm64.variant' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += dalvik.vm.isa.arm64.variant=generic" >> "${bcfg}"
    echo "tune: ART arm64 ISA variant -> generic"
  fi
  if ! grep -q 'dalvik.vm.isa.arm.variant' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += dalvik.vm.isa.arm.variant=generic" >> "${bcfg}"
    echo "tune: ART arm ISA variant -> generic"
  fi
  # Enable JIT for better performance
  if ! grep -q 'dalvik.vm.isa.arm64.features' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += dalvik.vm.isa.arm64.features=default" >> "${bcfg}"
    echo "tune: ART arm64 features -> default"
  fi
  # Enable JIT inline optimizations
  if ! grep -q 'dalvik.vm.jit.inline' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += dalvik.vm.jit.inline=4" >> "${bcfg}"
    echo "tune: ART JIT inline depth -> 4"
  fi
  # Enable JIT code caching
  if ! grep -q 'dalvik.vm.jit.codeCacheSize' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += dalvik.vm.jit.codeCacheSize=2097152" >> "${bcfg}"
    echo "tune: ART JIT code cache size -> 2MB"
  fi
fi

# ============================================================
# 6. Network: Buffer sizes for online gaming
# ============================================================
if [[ -f "${bcfg}" ]]; then
  if ! grep -q 'net.core.rmem_max' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += net.core.rmem_max=16777216" >> "${bcfg}"
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += net.core.wmem_max=16777216" >> "${bcfg}"
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += net.core.rmem_default=1048576" >> "${bcfg}"
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += net.core.wmem_default=1048576" >> "${bcfg}"
    echo "tune: network buffer sizes increased"
  fi
  # TCP keepalive for better connection stability
  if ! grep -q 'net.ipv4.tcp_keepalive' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += net.ipv4.tcp_keepalive_time=30" >> "${bcfg}"
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += net.ipv4.tcp_keepalive_intvl=10" >> "${bcfg}"
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += net.ipv4.tcp_keepalive_probes=5" >> "${bcfg}"
    echo "tune: TCP keepalive optimized"
  fi
fi

# ============================================================
# 7. Audio: Latency reduction for gaming
# ============================================================
if [[ -f "${bcfg}" ]]; then
  if ! grep -q 'audio.flinger.boost' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += audio.flinger.boost=1" >> "${bcfg}"
    echo "tune: audio flinger boost enabled"
  fi
  if ! grep -q 'audio.deep_buffer.media' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += audio.deep_buffer.media=0" >> "${bcfg}"
    echo "tune: audio deep buffer disabled for media"
  fi
  # Audio buffer size for low latency
  if ! grep -q 'audio.offload.buffer.size' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += audio.offload.buffer.size.kb=128" >> "${bcfg}"
    echo "tune: audio offload buffer size -> 128KB"
  fi
fi

# ============================================================
# 8. Power: CPU boost for interactive tasks
# ============================================================
if [[ -f "${bcfg}" ]]; then
  if ! grep -q 'ro.cpufreq.boost.enable' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.cpufreq.boost.enable=1" >> "${bcfg}"
    echo "tune: CPU boost enabled"
  fi
  # CPU boost duration
  if ! grep -q 'ro.cpufreq.boost.duration' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.cpufreq.boost.duration=1000" >> "${bcfg}"
    echo "tune: CPU boost duration -> 1000ms"
  fi
fi

# ============================================================
# 9. Thermal: Better cooling for sustained performance
# ============================================================
if [[ -f "${bcfg}" ]]; then
  # Thermal engine thresholds (RK3568 specific)
  if ! grep -q 'thermal.engine' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += thermal.engine.cpu.threshold=60" >> "${bcfg}"
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += thermal.engine.gpu.threshold=55" >> "${bcfg}"
    echo "tune: thermal thresholds adjusted"
  fi
fi

# ============================================================
# 10. Display: Frame rate and rendering
# ============================================================
if [[ -f "${bcfg}" ]]; then
  # Force 60Hz refresh rate
  if ! grep -q 'ro.sys.display.refresh_rate' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.sys.display.refresh_rate=60" >> "${bcfg}"
    echo "tune: display refresh rate -> 60Hz"
  fi
  # Disable adaptive refresh rate (for consistency)
  if ! grep -q 'ro.sys.display.adaptive_refresh' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.sys.display.adaptive_refresh=0" >> "${bcfg}"
    echo "tune: adaptive refresh rate disabled"
  fi
fi

# ============================================================
# 11. Marker
# ============================================================
if [[ -f "${bcfg}" ]]; then
  if ! grep -q '^# RADXOID_PERFORMANCE_TUNED$' "${bcfg}"; then
    echo "" >> "${bcfg}"
    echo "# RADXOID_PERFORMANCE_TUNED" >> "${bcfg}"
    echo "tune: performance tuning applied"
  else
    echo "tune: already applied, skipping"
  fi
fi

echo "Performance tuning complete."
