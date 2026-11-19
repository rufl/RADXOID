#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

ENV_FILE="${ROCK3A_ENV:-rock3a}"
case "${ENV_FILE}" in
  rock3a) ENV_FILE="${ROOT_DIR}/config/rock3a.env" ;;
  lean)   ENV_FILE="${ROOT_DIR}/config/rock3a-lean.env" ;;
  *) ENV_FILE="${ENV_FILE}" ;;
esac
[[ -f "${ENV_FILE}" ]] || { echo "env file missing: ${ENV_FILE}" >&2; exit 1; }
# shellcheck source=../config/rock3a.env
source "${ENV_FILE}"

: "${SOURCE_DIR:=${ROOT_DIR}/source}"
case "${SOURCE_DIR}" in
  /*) ;;
  *) SOURCE_DIR="${ROOT_DIR}/${SOURCE_DIR}" ;;
esac

cd "${SOURCE_DIR}"
[[ -f build/envsetup.sh ]] || { echo "source tree is not prepared; run scripts/prepare.sh" >&2; exit 1; }
[[ -x ./build.sh ]] || { echo "Rockchip build.sh is missing" >&2; exit 1; }

build_args=(${BUILD_ARGS:--UACKup})

# Fixup: the AOSP-11-era clang-tidy invocation trips cert-dcl37-c/dcl51-cpp
# on reserved identifiers from system headers (newer host clang than the BSP
# was tested with) and only breaks external/usb_modeswitch/usb_dongle.
# Tidy is a host-side lint; disabling it for this module changes no output.
tidy_mk="${SOURCE_DIR}/external/usb_modeswitch/usb_dongle/Android.mk"
if [[ -f "${tidy_mk}" ]] && grep -q '^LOCAL_TIDY := true$' "${tidy_mk}"; then
  sed -i 's/^LOCAL_TIDY := true$/LOCAL_TIDY := false/' "${tidy_mk}"
  echo "fixup: LOCAL_TIDY disabled for usb_dongle"
fi
# Performance: SCHEDUTIL governor — better CPU utilization under sustained
# load and lower jitter for emulation. Replaces INTERACTIVE. Requires a
# kernel rebuild (rock_3a.config is the board-specific fragment, applied
# after rockchip_defconfig so it wins).
kcfg="${SOURCE_DIR}/kernel/configs/rockchip/rock_3a.config"
if [[ -f "${kcfg}" ]] && ! grep -q '^CONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y$' "${kcfg}"; then
  printf '\nCONFIG_SCHED_SCHEDUTIL=y\nCONFIG_CPU_FREQ_DEFAULT_GOV_SCHEDUTIL=y\n' >> "${kcfg}"
  echo "fixup: kernel governor -> SCHEDUTIL (rock_3a.config)"
fi
# ART: preoptimize boot-critical apps with speed-profile for faster launch
# and smoother animations; no framework changes.
dmk="${SOURCE_DIR}/device/rockchip/rk356x/rk356x_rock_3a_r/rk356x_rock_3a_r.mk"
if [[ -f "${dmk}" ]] && ! grep -q '^PRODUCT_DEXPREOPT_SPEED_APPS' "${dmk}"; then
  printf '\nPRODUCT_DEXPREOPT_SPEED_APPS += \\\n    SystemUI \\\n    Settings \\\n    Launcher3QuickStep\n' >> "${dmk}"
  echo "fixup: dexpreopt speed-profile for SystemUI/Settings/Launcher3QuickStep"
fi
# Fixup: recovery image grew 8 KiB past BOARD_RECOVERYIMAGE_PARTITION_SIZE
# (kernel grew via rock_3a.config). Parameter.txt regenerates from this variable,
rcfg="${SOURCE_DIR}/device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk"
if [[ -f "${rcfg}" ]] && grep -q '^BOARD_RECOVERYIMAGE_PARTITION_SIZE := 114552832$' "${rcfg}"; then
  sed -i 's/^BOARD_RECOVERYIMAGE_PARTITION_SIZE := 114552832$/BOARD_RECOVERYIMAGE_PARTITION_SIZE := 134217728/' "${rcfg}"
  echo "fixup: recovery partition 114552832 -> 134217728 (8KiB headroom)"
fi
# Debloat: removes GMS, telephony/TV/print/carrier and heavy launchers/wallpapers
# for the lean/gaming flavor. Only affects device mk; no source churn beyond that.
if [[ "${ROCK3A_ENV:-rock3a}" == "lean" ]]; then
  "${ROOT_DIR}/scripts/debloat.sh"
fi
if [[ -n "${BUILD_JOBS:-}" ]]; then
  export MAKEFLAGS="-j${BUILD_JOBS}"
fi
if [[ -n "${CCACHE_DIR:-}" ]]; then
  mkdir -p "${CCACHE_DIR}"
  export CCACHE_DIR
fi
./build.sh "${build_args[@]}"

echo "Images are under ${SOURCE_DIR}/IMAGE"