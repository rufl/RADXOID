#!/usr/bin/env bash
set -euo pipefail

# Incremental build for ROCK 3A — avoids the full `./build.sh` (which
# triggers a kati --regen over the 150 GB tree on USB HDD). Only rebuilds
# targets affected by the last device.mk change.
# Usage: ./scripts/build-incremental.sh [extra args]

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

# AOSP envsetup.sh references $ZSH_VERSION unguarded; incompatible with `set -u`.
# Keep `set +u` for the entire envsetup + lunch sequence (vendor envsetup
# internally accesses TOP and other vars that would trip `set -u`).
set +u
source build/envsetup.sh
lunch "${PRODUCT_NAME}-${TARGET_BUILD_VARIANT}"

# Re-apply the same fixups that build.sh does (idempotent; no-op if already applied).
tidy_mk="${SOURCE_DIR}/external/usb_modeswitch/usb_dongle/Android.mk"
if [[ -f "${tidy_mk}" ]] && grep -q '^LOCAL_TIDY := true$' "${tidy_mk}"; then
  sed -i 's/^LOCAL_TIDY := true$/LOCAL_TIDY := false/' "${tidy_mk}"
  echo "fixup: LOCAL_TIDY disabled for usb_dongle"
fi
rcfg="${SOURCE_DIR}/device/rockchip/rk356x/rk356x_rock_3a_r/BoardConfig.mk"
if [[ -f "${rcfg}" ]] && grep -q '^BOARD_RECOVERYIMAGE_PARTITION_SIZE := 114552832$' "${rcfg}"; then
  sed -i 's/^BOARD_RECOVERYIMAGE_PARTITION_SIZE := 114552832$/BOARD_RECOVERYIMAGE_PARTITION_SIZE := 134217728/' "${rcfg}"
  echo "fixup: recovery partition 114552832 -> 134217728 (8KiB headroom)"
fi
if [[ "${ROCK3A_ENV:-rock3a}" == "lean" ]]; then
  "${ROOT_DIR}/scripts/debloat.sh"
fi

# Incremental build: use `m` if defined (from envsetup.sh), else `make -j$(nproc)`
if declare -f m >/dev/null 2>&1; then
  m "$@"
elif command -v make >/dev/null 2>&1; then
  make -j"$(nproc)" "$@"
else
  echo "no m/make target available" >&2
  exit 1
fi