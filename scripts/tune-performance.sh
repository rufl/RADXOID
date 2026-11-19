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
# 1. Kernel: SCHEDUTIL (already applied by build.sh fixup)
# ============================================================
kcfg="${SOURCE_DIR}/kernel/configs/rockchip/rock_3a.config"
if [[ -f "${kcfg}" ]]; then
  # SCHEDUTIL already applied by build.sh; ensure it's present
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
fi

# ============================================================
# 2. ART/dexpreopt: speed-profile for boot-critical apps
# ============================================================
dmk="${SOURCE_DIR}/device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk"
if [[ -f "${dmk}" ]]; then
  if ! grep -q '^PRODUCT_DEXPREOPT_SPEED_APPS' "${dmk}"; then
    printf '\nPRODUCT_DEXPREOPT_SPEED_APPS += \\\n    SystemUI \\\n    Settings \\\n    Launcher3QuickStep\n' >> "${dmk}"
    echo "tune: dexpreopt speed-profile applied"
  fi
  # Enable profile-guided optimization for speed apps
  if ! grep -q '^PRODUCT_DEXPREOPT_PROFILE_GUIDED_OPTIMIZATION' "${dmk}"; then
    echo "PRODUCT_DEXPREOPT_PROFILE_GUIDED_OPTIMIZATION := true" >> "${dmk}"
    echo "tune: PGO enabled for dexpreopt"
  fi
fi

# ============================================================
# 3. Build props: zram, swappiness, I/O scheduler
# ============================================================
# These are applied via BoardConfig.mk or device.mk
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
fi

# ============================================================
# 4. SurfaceFlinger: triple buffer for smoother rendering
# ============================================================
if [[ -f "${bcfg}" ]]; then
  if ! grep -q 'ro.sys.sf.use_triple_buffer' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.sys.sf.use_triple_buffer=1" >> "${bcfg}"
    echo "tune: SurfaceFlinger triple buffer enabled"
  fi
  # Disable phase offsets for lower latency
  if ! grep -q 'ro.sys.sf.use_phase_offsets' "${bcfg}"; then
    echo "TARGET_GLOBAL_PROPERTY_OVERRIDES += ro.sys.sf.use_phase_offsets=0" >> "${bcfg}"
    echo "tune: SurfaceFlinger phase offsets disabled"
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
fi

# ============================================================
# 6. Marker
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
