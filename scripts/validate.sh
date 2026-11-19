#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)

ENV_FILE="${ROCK3A_ENV:-rock3a}"
case "${ENV_FILE}" in
  rock3a) ENV_FILE="${ROOT_DIR}/config/rock3a.env" ;;
  lean)   ENV_FILE="${ROOT_DIR}/config/rock3a-lean.env" ;;
  *) ENV_FILE="${ENV_FILE}" ;;
esac
# shellcheck source=../config/rock3a.env
source "${ENV_FILE}"

required=(
  ANDROID_VERSION MANIFEST_URL MANIFEST_BRANCH MANIFEST_REVISION MANIFEST_NAME
  PRODUCT_NAME PRODUCT_UBOOT_CONFIG PRODUCT_KERNEL_CONFIG PRODUCT_KERNEL_DTS TARGET_BUILD_VARIANT
)
for key in "${required[@]}"; do
  [[ -n "${!key:-}" ]] || { echo "missing ${key}" >&2; exit 1; }
done

[[ "${ANDROID_VERSION}" == 11 ]] || { echo "ROCK 3A target must remain Android 11 until a newer Radxa board target exists" >&2; exit 1; }
[[ "${PRODUCT_NAME}" == rk356x_rock_3a_r ]] || { echo "unexpected product: ${PRODUCT_NAME}" >&2; exit 1; }
[[ "${PRODUCT_KERNEL_DTS}" == rk3568-rock-3a ]] || { echo "unexpected DTS: ${PRODUCT_KERNEL_DTS}" >&2; exit 1; }
[[ "${TARGET_BUILD_VARIANT}" == userdebug ]] || { echo "target must be userdebug for first bring-up" >&2; exit 1; }
[[ "${MANIFEST_REVISION}" =~ ^[0-9a-f]{40}$ ]] || { echo "manifest revision is not a full git SHA" >&2; exit 1; }

# Validate optional artifact directory when it exists (post-build check).
case "${SOURCE_DIR:-}" in
  "") ;;
  *)
    RD="${SOURCE_DIR}/rockdev/Image-${PRODUCT_NAME}"
    if [[ -d "${RD}" ]]; then
      for f in update.img boot.img recovery.img; do
        [[ -s "${RD}/${f}" ]] || { echo "artifact missing/empty: ${RD}/${f}" >&2; exit 1; }
      done
      echo "artifacts OK: $(du -sh "${RD}/update.img" | cut -f1) update.img"
    fi
    ;;
esac

printf 'rock3a configuration OK: Android %s, %s, manifest %s\n' \
  "${ANDROID_VERSION}" "${PRODUCT_NAME}-${TARGET_BUILD_VARIANT}" "${MANIFEST_REVISION}"